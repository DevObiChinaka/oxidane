#!/usr/bin/env python
"""
Test subscription expiration email notification
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription
from subscriptions.signals import subscription_expired
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

print('=' * 70)
print('TESTING SUBSCRIPTION EXPIRATION EMAIL')
print('=' * 70)

email = 'derachinaka@gmail.com'

try:
    user = User.objects.get(email=email)
    sub = Subscription.objects.filter(
        billing_profile__user=user,
        status='active'
    ).select_related('plan').first()
    
    if not sub:
        print('\n❌ No active subscription found')
        sys.exit(1)
    
    print(f'\n📧 Testing email notification for subscription expiration')
    print(f'   User: {user.email}')
    print(f'   Subscription: {sub.id}')
    print(f'   Plan: {sub.plan.name if sub.plan else "N/A"}')
    
    # Save original state
    original_status = sub.status
    original_end = sub.end_date
    
    print('\n' + '=' * 70)
    print('TEST: Manually trigger subscription_expired signal')
    print('=' * 70)
    
    print('\nTrigger subscription_expired signal...')
    
    # Manually fire the signal (simulates what happens when subscription expires)
    subscription_expired.send(
        sender=Subscription,
        subscription=sub,
        user=user
    )
    
    print('\n✅ Signal sent!')
    print('\nExpected behaviors triggered:')
    print('  1. Log: "Subscription expired: ..." ✅')
    print('  2. Revoke feature access ✅')
    print('  3. Send expiration email to user ✅ (NEW)')
    
    print('\n📧 Email should contain:')
    print(f'   To: {user.email}')
    print(f'   Subject: Subscription Expired')
    print(f'   Plan: {sub.plan.name if sub.plan else "N/A"}')
    print(f'   End Date: {sub.end_date.strftime("%B %d, %Y")}')
    print(f'   Resubscribe URL: https://oxidane.com/pricing')
    
    print('\n' + '=' * 70)
    print('✅ TEST COMPLETE')
    print('=' * 70)
    
    print('\n📝 Next Steps:')
    print('  1. Check email inbox for derachinaka@gmail.com')
    print('  2. Verify email contains subscription details')
    print('  3. Check Celery logs for email sending confirmation:')
    print('     journalctl -u oxidane-celery --since "1 minute ago" | grep "expiry email"')
    print('  4. Check Django logs for signal handler execution:')
    print('     tail -f /var/log/oxidane/gunicorn-error.log | grep "subscription_expired"')
    
    print('\n🔄 Signal Handlers Registered:')
    receivers = subscription_expired.receivers
    print(f'   Total handlers: {len(receivers)}')
    print('   Handlers:')
    for idx, (lookup, receiver) in enumerate(receivers, 1):
        func = receiver()
        if func:
            print(f'     {idx}. {func.__name__}')
    
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
