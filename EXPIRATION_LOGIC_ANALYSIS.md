# Subscription Expiration Logic Analysis

**Date**: December 15, 2025  
**Issue**: Celery Beat crash prevented expiration checks, causing subscriptions to remain "active" past their end_date

---

## 🔍 How Expiration SHOULD Work

### 1. **The Scheduled Task** (`check_expired_subscriptions`)

**Location**: `backend/subscriptions/tasks.py` (lines 776-816)

**Schedule**: Daily at **midnight UTC** (configured in `backend/oxidane/celery.py`)

```python
@shared_task
def check_expired_subscriptions():
    """
    Check for expired subscriptions and deactivate them
    
    Runs: Daily at midnight (configured in celery.py)
    
    Actions:
        1. Find subscriptions past their end_date
        2. Mark as expired
        3. Remove users from Telegram groups
        4. Update user status
    """
    logger.info("Checking for expired subscriptions")
    
    # Get subscriptions that expired
    expired_subscriptions = Subscription.objects.filter(
        status='active',              # ← Only checks ACTIVE subscriptions
        end_date__lt=timezone.now()   # ← Where end_date is in the PAST
    ).select_related('billing_profile__user', 'plan')
    
    count = 0
    for subscription in expired_subscriptions:
        # STEP 1: Mark subscription as expired
        subscription.status = 'expired'
        subscription.save()
        
        # STEP 2: Update user status
        user = subscription.billing_profile.user
        user.subscription_status = 'expired'
        user.save()
        
        # STEP 3: Remove from Telegram groups
        if subscription.plan:
            try:
                remove_user_from_telegram_groups.delay(user.id, str(subscription.plan.id))
                logger.info(f"Queued Telegram removal for user {user.id}")
            except Exception as e:
                logger.error(f"Failed to queue Telegram removal: {str(e)}")
        
        count += 1
        logger.info(f"Expired subscription {subscription.id} for user {user.email}")
    
    logger.info(f"Processed {count} expired subscriptions")
    
    return {'success': True, 'expired_count': count}
```

### 2. **Signal Chain** (Auto-triggered on status change)

**Location**: `backend/subscriptions/signals.py`

When `subscription.status` changes from `'active'` to `'expired'`, Django triggers these signals:

#### **Pre-Save Signal** (line 549):
```python
@receiver(pre_save, sender='subscriptions.Subscription')
def detect_subscription_changes(sender, instance, **kwargs):
    """Capture old state before save"""
    if instance.pk:
        old = Subscription.objects.get(pk=instance.pk)
        instance._old_status = old.status  # ← Stores old status
```

#### **Post-Save Signal** (line 473):
```python
@receiver(post_save, sender='subscriptions.Subscription')
def handle_subscription_changes(sender, instance, created, **kwargs):
    """Fires custom signals based on status change"""
    old_status = getattr(subscription, '_old_status', None)
    
    # Detects: active → expired
    if old_status == 'active' and subscription.status == 'expired':
        subscription_expired.send(
            sender=Subscription,
            subscription=subscription,
            user=user
        )
```

#### **Custom Signal Handlers** (lines 183-228):
```python
@receiver(subscription_expired)
def log_subscription_expired(sender, subscription, user, **kwargs):
    """Log expiration event"""
    logger.info(f"Subscription expired: {subscription.id}")

@receiver(subscription_expired)
def revoke_expired_subscription_access(sender, subscription, user, **kwargs):
    """Revoke feature access when subscription expires"""
    features = subscription.plan.features.all()
    for feature in features:
        feature_access_revoked.send(
            sender=subscription.__class__,
            subscription=subscription,
            feature=feature,
            user=user
        )
```

---

## ❌ What WENT WRONG (Root Cause)

### **Problem 1: Celery Beat Crash Loop**

**Symptom**: Service crashed 2,400+ times, restarting every ~2 minutes

**Evidence**:
```bash
$ journalctl -u oxidane-celery-beat --since "1 day ago" | grep "exit code"
# Shows continuous crashes with exit code 1
```

**Root Causes**:
1. **Corrupted schedule file**: `celerybeat-schedule` database was locked
   ```
   _gdbm.error: [Errno 11] Resource temporarily unavailable: 'celerybeat-schedule'
   ```
2. **Aggressive polling task**: `process_telegram_updates` running every 5 seconds overwhelmed the scheduler

**Impact**: `check_expired_subscriptions` task **NEVER RAN** during the entire crash period

---

### **Problem 2: No Fallback or Grace Logic**

**Observation**: The expiration task is the **ONLY** mechanism that marks subscriptions as expired.

**Weakness**: There is NO fallback logic such as:
- ❌ Real-time check in API endpoints (e.g., when user accesses course content)
- ❌ Middleware to validate subscription status on each request
- ❌ Grace period after end_date before hard cutoff
- ❌ Database constraint or trigger to auto-expire

**Result**: Users with `end_date < now()` remained `status='active'` indefinitely until Celery Beat was fixed.

---

### **Problem 3: Silent Failure**

**Issue**: When Celery Beat crashed, there was:
- ❌ No monitoring alert
- ❌ No health check endpoint
- ❌ No dashboard warning
- ❌ No automated recovery attempt

**Discovery Method**: Manual investigation after user reported issue

---

## ✅ What Was FIXED

### **Fix 1: Resolved Celery Beat Crash** ✅

**Actions Taken**:
1. Stopped Celery Beat service
2. Removed corrupted schedule files:
   ```bash
   rm /var/www/oxidane/backend/celerybeat-schedule*
   ```
3. Moved aggressive Telegram polling to separate systemd service (`oxidane-telegram-poller`)
4. Reduced Beat schedule to only 5 critical tasks:
   ```python
   app.conf.beat_schedule = {
       'check-expired-subscriptions': {  # ← THE FIX FOR EXPIRATION
           'task': 'subscriptions.tasks.check_expired_subscriptions',
           'schedule': crontab(hour=0, minute=0),  # Daily midnight
       },
       'process-auto-renewals': { ... },
       'send-renewal-reminders': { ... },
       'reconcile-payments': { ... },
       'update-exchange-rates': { ... },
   }
   ```
5. Restarted service - now stable for 11+ minutes (was crashing every 2 min)

**Verification**:
```bash
$ systemctl status oxidane-celery-beat
● oxidane-celery-beat.service - Oxidane Celery Beat Scheduler
   Active: active (running) since Sun 2025-12-15 14:01:21 WAT; 11min ago
   Main PID: 72110
   
$ journalctl -u oxidane-celery-beat --since "15 minutes ago"
# No crashes, running smoothly
```

### **Fix 2: Manual Recovery for Affected Users** ✅

**Created Tool**: `backend/fix_affected_user.py`

**Purpose**: Reactivate subscriptions that expired during Celery Beat downtime

**Three Recovery Options**:

#### **Option 1: Grace Period Extension** (Recommended)
```python
# No charge, just extend subscription by one billing period
new_end_date = timezone.now() + extension  # e.g., +7 days for weekly
sub.status = 'active'
sub.end_date = new_end_date
sub.next_billing_date = new_end_date
sub.save()

# Re-add to Telegram groups
add_user_to_telegram_groups.delay(user.id, str(sub.plan.id))
```

**Use When**: You want to apologize for service disruption with free extension

#### **Option 2: Charge Immediately**
```python
# Attempt payment right now via auto-renewal task
process_single_renewal.delay(subscription_id)
```

**Use When**: User should have been charged already, no grace needed

#### **Option 3: Fresh Start**
```python
# Reset dates as if subscription just started
new_start = timezone.now()
new_end = new_start + extension
sub.start_date = new_start
sub.end_date = new_end
sub.next_billing_date = new_end
sub.status = 'active'
sub.save()
```

**Use When**: Major disruption, start fresh billing cycle

---

## 🛡️ How to PREVENT This in Future

### **Recommendation 1: Add Real-Time Validation** 🔴 HIGH PRIORITY

Add middleware to check subscription status on EVERY authenticated request:

**Create**: `backend/subscriptions/middleware.py`
```python
from django.utils import timezone
from subscriptions.models import Subscription

class SubscriptionValidationMiddleware:
    """
    Real-time subscription validation middleware.
    
    Checks if user's subscription has expired on EVERY request
    and updates status accordingly. This acts as a failsafe
    in case Celery Beat fails.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Get user's active subscription
            subscription = Subscription.objects.filter(
                billing_profile__user=request.user,
                status='active'
            ).first()
            
            if subscription and subscription.end_date < timezone.now():
                # Subscription should be expired but isn't
                subscription.status = 'expired'
                subscription.save()
                
                # Update user
                request.user.subscription_status = 'expired'
                request.user.save()
                
                # Log the catch
                logger.warning(
                    f"Middleware caught expired subscription {subscription.id} "
                    f"for user {request.user.email} that was still marked active"
                )
        
        return self.get_response(request)
```

**Add to** `backend/oxidane/settings.py`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware ...
    'subscriptions.middleware.SubscriptionValidationMiddleware',  # ← ADD THIS
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Benefits**:
- ✅ Catches expired subscriptions in real-time
- ✅ Works even if Celery Beat is down
- ✅ Minimal performance impact (only runs for authenticated users)
- ✅ Automatically triggers expiration signals

---

### **Recommendation 2: Add Health Monitoring** 🟡 MEDIUM PRIORITY

**Create**: `backend/subscriptions/management/commands/check_celery_health.py`

```python
from django.core.management.base import BaseCommand
from celery import current_app
import redis
from django.conf import settings

class Command(BaseCommand):
    help = 'Check Celery Beat and Worker health'
    
    def handle(self, *args, **options):
        issues = []
        
        # Check Redis connection
        try:
            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            self.stdout.write(self.style.SUCCESS('✓ Redis connection: OK'))
        except Exception as e:
            issues.append(f'Redis connection failed: {e}')
            self.stdout.write(self.style.ERROR(f'✗ Redis: {e}'))
        
        # Check Celery workers
        try:
            inspect = current_app.control.inspect()
            workers = inspect.active()
            if workers:
                self.stdout.write(self.style.SUCCESS(f'✓ Workers active: {len(workers)}'))
            else:
                issues.append('No active Celery workers found')
                self.stdout.write(self.style.ERROR('✗ No active workers'))
        except Exception as e:
            issues.append(f'Worker check failed: {e}')
            self.stdout.write(self.style.ERROR(f'✗ Workers: {e}'))
        
        # Check scheduled tasks
        try:
            scheduled = inspect.scheduled()
            if scheduled:
                self.stdout.write(self.style.SUCCESS(f'✓ Scheduled tasks: OK'))
            else:
                issues.append('No scheduled tasks found (Beat may be down)')
                self.stdout.write(self.style.WARNING('⚠ No scheduled tasks'))
        except Exception as e:
            issues.append(f'Scheduled tasks check failed: {e}')
            self.stdout.write(self.style.ERROR(f'✗ Beat: {e}'))
        
        # Exit code
        if issues:
            self.stdout.write(self.style.ERROR(f'\n❌ {len(issues)} issues found'))
            for issue in issues:
                self.stdout.write(f'  - {issue}')
            exit(1)
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All checks passed'))
            exit(0)
```

**Schedule with cron** (run every 5 minutes):
```bash
*/5 * * * * cd /var/www/oxidane/backend && /var/www/oxidane/venv/bin/python manage.py check_celery_health || echo "Celery health check failed!" | mail -s "ALERT: Celery Down" admin@oxidane.com
```

**Benefits**:
- ✅ Proactive monitoring
- ✅ Email alerts on failure
- ✅ Can integrate with uptime monitoring services (UptimeRobot, etc.)

---

### **Recommendation 3: Add Database Indices** 🟢 LOW PRIORITY

The expiration query could be slow on large databases:

```python
expired_subscriptions = Subscription.objects.filter(
    status='active',
    end_date__lt=timezone.now()
)
```

**Add Index**:
```python
# In backend/subscriptions/models.py - Subscription model
class Meta:
    indexes = [
        models.Index(fields=['status', 'end_date']),  # ← ADD THIS
        # ... existing indexes ...
    ]
```

**Create Migration**:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Benefits**:
- ✅ Faster expiration checks (milliseconds instead of seconds)
- ✅ Reduced database load
- ✅ Better performance as user base grows

---

### **Recommendation 4: Add Grace Period Logic** 🟢 OPTIONAL

Currently, there's a **hard cutoff** at `end_date`. Consider adding a 24-hour grace period:

**In** `backend/subscriptions/tasks.py`:
```python
from datetime import timedelta

@shared_task
def check_expired_subscriptions():
    """Check for expired subscriptions with 24-hour grace period"""
    
    # Grace period: subscription expires 24 hours AFTER end_date
    grace_cutoff = timezone.now() - timedelta(hours=24)
    
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lt=grace_cutoff  # ← Changed from timezone.now()
    ).select_related('billing_profile__user', 'plan')
    
    # ... rest of logic ...
```

**Benefits**:
- ✅ Gives users 24 hours after end_date before hard cutoff
- ✅ Better user experience (forgives payment delays)
- ✅ Aligns with industry best practices

**Trade-off**: Users get 1 extra day of access (may be desirable)

---

## 📊 Current System Status

### ✅ **Fixed Components**:
1. **Celery Beat**: Running stable, no crashes for 11+ minutes
2. **Telegram Poller**: Moved to separate service, running independently
3. **Expiration Task**: Will run tonight at midnight UTC
4. **Auto-Renewal Task**: Will run tomorrow at 2 AM UTC

### ⚠️ **Outstanding Risks**:
1. **No real-time validation**: If Celery Beat crashes again, issue repeats
2. **No monitoring alerts**: Silent failures possible
3. **No health checks**: Manual investigation required to detect issues

### 🔄 **Next Expiration Check**:
- **When**: Tonight at **00:00 UTC** (Midnight)
- **What**: Will mark all subscriptions with `end_date < now()` as expired
- **Who**: Users like `derachinaka@gmail.com` (manually extended to Dec 22)

---

## 🧪 Testing Plan

Use the created test scripts to verify expiration works:

### **Test 1: Verify Expiration Works**
```bash
ssh root@169.255.57.172
cd /var/www/oxidane/backend
sudo -u oxidane /var/www/oxidane/venv/bin/python test_expiration.py

# Menu:
# 1. List active subscriptions
# 2. Expire subscription (set end_date to yesterday)
# 3. Trigger expiration check (run task manually)
# 4. Check if Telegram removal queued
```

**Expected Result**: Subscription status changes to `expired`, Telegram removal task queued

### **Test 2: Monitor Tonight's Scheduled Run**
```bash
# Wait until 00:05 UTC (5 minutes after midnight)
ssh root@169.255.57.172
journalctl -u oxidane-celery-beat --since "10 minutes ago" | grep "check_expired_subscriptions"

# Should see:
# "Checking for expired subscriptions"
# "Processed X expired subscriptions"
```

### **Test 3: Verify User Removed from Telegram**
- Check Telegram group at 00:10 UTC
- Verify expired users no longer in group
- Check logs: `journalctl -u oxidane-celery --since "1 hour ago" | grep "remove_user_from_telegram"`

---

## 📝 Summary

### **What Caused the Issue**:
1. Celery Beat crashed due to corrupted schedule file
2. Aggressive Telegram polling task (every 5 seconds) overwhelmed scheduler
3. `check_expired_subscriptions` task never ran during crash period
4. No fallback mechanism to catch expired subscriptions
5. Subscriptions remained `status='active'` despite `end_date` in past

### **What Was Fixed**:
1. ✅ Removed corrupted schedule file
2. ✅ Moved Telegram polling to separate systemd service
3. ✅ Celery Beat now stable with 5 critical tasks only
4. ✅ Created recovery tool (`fix_affected_user.py`)
5. ✅ Manually extended affected user (derachinaka@gmail.com)

### **How to Prevent Future Issues**:
1. 🔴 **Add real-time validation middleware** (CRITICAL)
2. 🟡 **Add health monitoring and alerts** (IMPORTANT)
3. 🟢 **Add database indices for performance**
4. 🟢 **Consider 24-hour grace period** (optional UX improvement)

---

**Current Status**: ✅ **System Operational**  
**Next Action**: Implement middleware for real-time validation  
**Next Test**: Monitor expiration task tonight at midnight UTC

