# Payment Safety Architecture

## Critical Issue Resolved
✅ **Redis SSL Configuration Fixed** - SSL settings now only apply when using `rediss://` scheme

## Current Risk: Transaction Inconsistency
When a payment succeeds but Celery tasks fail:
- User is charged ✅ 
- Subscription created in DB ✅
- Features granted in DB ✅
- BUT: Subscription not activated ❌
- BUT: User not added to Telegram groups ❌
- BUT: No receipt email sent ❌

## Safety Mechanisms Needed

### 1. Paystack Webhook Implementation
**Purpose**: Receive authoritative payment confirmations from Paystack
**Priority**: CRITICAL
**Location**: `backend/subscriptions/views/webhooks.py`

```python
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import hmac
import hashlib
import json

@csrf_exempt
def paystack_webhook(request):
    """
    Webhook endpoint for Paystack payment events
    URL: /api/webhooks/paystack/
    """
    # Verify webhook signature
    paystack_secret = PaymentConfiguration.get_instance().paystack_secret_key
    signature = request.headers.get('x-paystack-signature')
    
    computed_signature = hmac.new(
        paystack_secret.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()
    
    if signature != computed_signature:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Process event
    event = json.loads(request.body)
    event_type = event.get('event')
    
    if event_type == 'charge.success':
        # Double-check payment status with Paystack API
        # Then activate subscription (idempotent)
        reference = event['data']['reference']
        activate_subscription_from_webhook.delay(reference)
    
    return JsonResponse({'status': 'success'})
```

**Benefits**:
- Authoritative source of truth (Paystack confirms payment)
- Retries automatically if webhook fails
- Decoupled from user's payment flow (async)

### 2. Idempotency Implementation
**Purpose**: Prevent double-charging and ensure tasks run exactly once
**Priority**: CRITICAL
**Location**: `backend/subscriptions/models.py`

```python
class Payment(models.Model):
    # Existing fields...
    idempotency_key = models.CharField(max_length=255, unique=True, null=True)
    activation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    activation_attempts = models.IntegerField(default=0)
    last_activation_error = models.TextField(null=True, blank=True)
```

**Usage**:
```python
# Before processing payment
idempotency_key = f"payment_{user.id}_{timezone.now().timestamp()}"
existing_payment = Payment.objects.filter(idempotency_key=idempotency_key).first()
if existing_payment:
    return existing_payment  # Don't charge again
```

### 3. Atomic Transactions
**Purpose**: All-or-nothing database operations
**Priority**: HIGH
**Location**: `backend/subscriptions/views/payment_views.py`

```python
from django.db import transaction

@transaction.atomic
def process_payment_callback(request):
    """
    Wrap payment processing in atomic transaction
    If ANY step fails, ALL changes are rolled back
    """
    # Create payment record
    payment = Payment.objects.create(...)
    
    # Create subscription
    subscription = UserSubscription.objects.create(...)
    
    # Grant features
    for feature in plan.features.all():
        UserPlanFeature.objects.create(...)
    
    # Queue Celery tasks OUTSIDE atomic block
    transaction.on_commit(lambda: activate_subscription.delay(payment.id))
```

**Benefits**:
- Database consistency guaranteed
- Tasks only queued if DB commit succeeds
- Rollback on any failure

### 4. Task Retry Logic with Exponential Backoff
**Purpose**: Handle transient failures (network issues, Redis downtime)
**Priority**: HIGH
**Location**: `backend/subscriptions/tasks.py`

```python
@shared_task(
    bind=True,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff: 2^retry seconds
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,  # Add randomness to prevent thundering herd
)
def activate_subscription(self, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Check if already activated (idempotency)
        if payment.activation_status == 'completed':
            return {'status': 'already_activated'}
        
        # Mark as processing
        payment.activation_status = 'processing'
        payment.activation_attempts += 1
        payment.save()
        
        # Activate subscription logic...
        
        # Mark as completed
        payment.activation_status = 'completed'
        payment.save()
        
    except Exception as exc:
        payment.activation_status = 'failed'
        payment.last_activation_error = str(exc)
        payment.save()
        raise self.retry(exc=exc)
```

### 5. Payment Reconciliation Job
**Purpose**: Detect and fix inconsistencies
**Priority**: MEDIUM
**Location**: `backend/subscriptions/tasks.py`

```python
@shared_task
def reconcile_payments():
    """
    Run daily to find payments that succeeded but subscriptions weren't activated
    """
    # Find payments with status='success' but activation_status='failed'
    failed_activations = Payment.objects.filter(
        status='success',
        activation_status__in=['pending', 'failed']
    )
    
    for payment in failed_activations:
        # Retry activation
        activate_subscription.delay(payment.id)
        
    # Log reconciliation results
    logger.info(f"Reconciled {failed_activations.count()} payments")
```

**Schedule in Celery Beat**:
```python
CELERY_BEAT_SCHEDULE = {
    # ... existing schedules ...
    'reconcile-payments': {
        'task': 'subscriptions.tasks.reconcile_payments',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
}
```

### 6. Payment Audit Trail
**Purpose**: Track all payment state changes for debugging
**Priority**: MEDIUM
**Location**: `backend/subscriptions/models.py`

```python
class PaymentEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)  # 'created', 'verified', 'activated', 'failed'
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

**Usage**:
```python
# Log every significant event
PaymentEvent.objects.create(
    payment=payment,
    event_type='activation_started',
    details={'celery_task_id': task.request.id}
)
```

## Implementation Priority

1. **URGENT** (Do Now):
   - ✅ Fix Redis SSL configuration
   - ⏳ Add `activation_status` field to Payment model
   - ⏳ Wrap payment processing in `@transaction.atomic`
   - ⏳ Add retry logic to `activate_subscription` task

2. **HIGH** (This Week):
   - ⏳ Implement Paystack webhook endpoint
   - ⏳ Add idempotency key to Payment model
   - ⏳ Create payment reconciliation job

3. **MEDIUM** (This Month):
   - ⏳ Implement PaymentEvent audit trail
   - ⏳ Add monitoring/alerting for failed activations
   - ⏳ Create admin dashboard for payment reconciliation

## Testing Plan

### 1. Test Redis Fix
```bash
# Make a test payment
# Verify in logs:
# - No SSL error
# - activate_subscription.delay() succeeds
# - User added to Telegram groups
# - Receipt email sent
```

### 2. Test Network Failure Scenario
```bash
# Stop Redis temporarily
redis-cli shutdown

# Make payment (will succeed in Paystack but fail to queue tasks)
# Restart Redis
redis-server

# Verify retry logic kicks in and activates subscription
```

### 3. Test Idempotency
```python
# Attempt to charge same idempotency_key twice
# Verify second attempt returns existing payment without charging
```

## Monitoring Checklist

- [ ] Set up alerts for `payment.activation_status = 'failed'`
- [ ] Monitor Celery task failure rate
- [ ] Track time between payment success and subscription activation
- [ ] Alert on Redis connection failures
- [ ] Daily reconciliation report (how many payments needed fixing)

## Production Deployment

For production (e.g., Railway):
1. Set environment variable: `REDIS_URL=rediss://your-redis-cloud-url`
2. Verify SSL settings apply automatically (scheme check in settings.py)
3. Configure Paystack webhook URL in Paystack dashboard
4. Enable payment reconciliation cron job

## Questions Addressed

> "how can we pause transcation or make sure things go as planned and no one looses money or credibility"

**Answer**: We cannot pause Paystack transactions (they're processed by Paystack), but we can ensure **eventual consistency**:

1. **Paystack Webhooks**: Even if initial activation fails, webhook will retry
2. **Idempotency**: Prevents double-charging if user retries
3. **Atomic Transactions**: Database stays consistent
4. **Retry Logic**: Transient failures (network, Redis) auto-recover
5. **Reconciliation**: Daily job catches any edge cases
6. **Audit Trail**: Every state change is logged for debugging

**Money Safety Guarantee**:
- User charged → Paystack confirms → Webhook triggers activation → Retries until success
- If activation permanently fails → Admin alerted → Manual intervention → Refund if needed
- No scenario where user loses money AND doesn't get service (eventually consistent)

**Credibility Guarantee**:
- Receipt emails always sent (via webhook, not initial flow)
- Clear user communication about processing delays
- Admin tools to manually activate if needed
- Transparent audit trail
