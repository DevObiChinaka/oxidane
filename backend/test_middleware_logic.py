#!/usr/bin/env python
"""
Test the SubscriptionValidationMiddleware logic with derachinaka@gmail.com

This script simulates what the middleware will do:
1. Find user's active subscriptions
2. Check if any have end_date < now
3. Mark them as expired
4. Queue Telegram removal
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

print('=' * 70)
print('TESTING MIDDLEWARE LOGIC WITH derachinaka@gmail.com')
print('=' * 70)

email = 'derachinaka@gmail.com'

try:
    user = User.objects.get(email=email)
    print(f'\n✅ Found user: {user.email}')
    print(f'   User ID: {user.id}')
    print(f'   Current status: {user.subscription_status}')
    
    # Get active subscriptions (what middleware will check)
    active_subscriptions = Subscription.objects.filter(
        billing_profile__user=user,
        status='active'
    ).select_related('plan', 'billing_profile__user')
    
    print(f'\n📋 Active subscriptions: {active_subscriptions.count()}')
    
    now = timezone.now()
    print(f'\n⏰ Current time: {now}')
    
    expired_found = False
    
    for subscription in active_subscriptions:
        print(f'\n🔍 Checking subscription {subscription.id}:')
        print(f'   Plan: {subscription.plan.name if subscription.plan else "N/A"}')
        print(f'   Status: {subscription.status}')
        print(f'   End date: {subscription.end_date}')
        print(f'   Next billing: {subscription.next_billing_date}')
        print(f'   Auto-renew: {subscription.auto_renew}')
        
        # Check if expired
        if subscription.end_date < now:
            print(f'\n   ⚠️  EXPIRED! End date was {(now - subscription.end_date).days} days ago')
            print(f'   📝 Middleware WOULD mark this as expired')
            expired_found = True
        else:
            time_remaining = subscription.end_date - now
            days = time_remaining.days
            hours = time_remaining.seconds // 3600
            print(f'\n   ✅ ACTIVE - Expires in {days} days, {hours} hours')
            print(f'   📝 Middleware would NOT touch this')
    
    print('\n' + '=' * 70)
    if expired_found:
        print('❌ MIDDLEWARE WOULD EXPIRE SUBSCRIPTIONS')
        print('=' * 70)
        print('\nActions middleware would take:')
        print('  1. Set subscription.status = "expired"')
        print('  2. Set user.subscription_status = "expired"')
        print('  3. Queue remove_user_from_telegram_groups task')
        print('  4. Log warning about missed Celery Beat expiration')
        print('\nThis is the FAILSAFE mechanism working correctly!')
    else:
        print('✅ NO EXPIRED SUBSCRIPTIONS FOUND')
        print('=' * 70)
        print('\nMiddleware would take NO action.')
        print('User has valid active subscription(s).')
        print('\nTo test expiration detection:')
        print('  1. Use test_expiration.py to set end_date to yesterday')
        print('  2. Make any authenticated request as this user')
        print('  3. Middleware will catch and expire the subscription')
    
    print('\n' + '=' * 70)
    print('TEST COMPLETE')
    print('=' * 70)
    
except User.DoesNotExist:
    print(f'\n❌ User not found: {email}')
    sys.exit(1)
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
