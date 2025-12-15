#!/usr/bin/env python
"""Fix derachinaka@gmail.com subscription that should be expired"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription, User
from subscriptions.tasks import add_user_to_telegram_groups
from django.utils import timezone
from datetime import timedelta

email = 'derachinaka@gmail.com'

print('=' * 70)
print(f'FIXING SUBSCRIPTION FOR: {email}')
print('=' * 70)

try:
    user = User.objects.get(email=email)
    sub = Subscription.objects.filter(
        billing_profile__user=user
    ).select_related('plan', 'payment_method').order_by('-created_at').first()
    
    if not sub:
        print('\n❌ No subscription found!')
        sys.exit(1)
    
    print(f'\n📊 Current State:')
    print(f'   Status: {sub.status}')
    print(f'   End date: {sub.end_date}')
    print(f'   Next billing: {sub.next_billing_date}')
    print(f'   Auto-renew: {sub.auto_renew}')
    print(f'   Payment method: {"✅" if sub.payment_method else "❌"}')
    
    # Check if end date has passed
    if sub.end_date < timezone.now():
        print(f'\n⚠️  ISSUE DETECTED: Subscription ended {(timezone.now() - sub.end_date).days} days ago but status is still "{sub.status}"')
        print('\nThis happened because Celery Beat was down and check_expired_subscriptions did not run.')
    
    # Calculate extension
    if sub.plan.billing_period == 'weekly':
        extension = timedelta(days=7)
    elif sub.plan.billing_period == 'monthly':
        extension = timedelta(days=30)
    elif sub.plan.billing_period == 'quarterly':
        extension = timedelta(days=90)
    elif sub.plan.billing_period == 'yearly':
        extension = timedelta(days=365)
    else:
        extension = timedelta(days=30)
    
    new_end_date = timezone.now() + extension
    new_billing_date = new_end_date
    
    print('\n' + '=' * 70)
    print('APPLYING FIX: EXTEND SUBSCRIPTION (Grace Period)')
    print('=' * 70)
    print(f'\nExtending by: {extension.days} days')
    print(f'New end date: {new_end_date}')
    print(f'Next billing: {new_billing_date}')
    
    # Update subscription
    sub.status = 'active'
    sub.end_date = new_end_date
    sub.next_billing_date = new_billing_date
    sub.save()
    
    # Update user
    user.subscription_status = 'active'
    user.current_plan = sub.plan
    user.save()
    
    print('\n✅ Subscription extended!')
    print(f'\n📊 New State:')
    print(f'   Status: {sub.status}')
    print(f'   End date: {sub.end_date}')
    print(f'   Next billing: {sub.next_billing_date}')
    
    # Re-add to Telegram groups (in case they were removed)
    if sub.plan:
        print(f'\n📱 Ensuring user is in Telegram groups...')
        add_user_to_telegram_groups.delay(user.id, str(sub.plan.id))
        print('✅ Task queued!')
    
    print('\n' + '=' * 70)
    print('✅ SUCCESS!')
    print('=' * 70)
    print(f'User given {extension.days}-day grace period.')
    print(f'Auto-renewal will charge on: {new_billing_date.date()}')
    print('\nYou can now use this user for testing:')
    print('  - Test auto-renewal (set next_billing_date to today)')
    print('  - Test expiration (set end_date to yesterday)')
    print('  - Subscription will work normally from now on')
    print('=' * 70)
        
except User.DoesNotExist:
    print(f'\n❌ User not found: {email}')
    sys.exit(1)
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
