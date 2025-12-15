#!/usr/bin/env python
"""Quick script to find and reactivate derachinaka@gmail.com"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription, User
from subscriptions.tasks import add_user_to_telegram_groups
from django.utils import timezone
from datetime import timedelta

print('=' * 70)
print('FINDING SUBSCRIPTION FOR: derachinaka@gmail.com')
print('=' * 70)

try:
    user = User.objects.get(email='derachinaka@gmail.com')
    print(f'\n✅ User found: {user.email}')
    print(f'   User ID: {user.id}')
    print(f'   Current status: {user.subscription_status}')
    
    subs = Subscription.objects.filter(
        billing_profile__user=user
    ).select_related('plan', 'payment_method').order_by('-created_at')
    
    if not subs.exists():
        print('\n❌ No subscriptions found!')
        sys.exit(1)
    
    print(f'\n📋 Found {subs.count()} subscription(s):\n')
    
    for i, sub in enumerate(subs, 1):
        days_since = (timezone.now() - sub.end_date).days if sub.end_date else None
        has_payment = '✅' if sub.payment_method and sub.payment_method.is_active else '❌'
        
        print(f'{i}. Subscription ID: {sub.id}')
        print(f'   Plan: {sub.plan.name} ({sub.plan.billing_period})')
        print(f'   Status: {sub.status.upper()}')
        print(f'   Auto-renew: {"✅" if sub.auto_renew else "❌"}')
        print(f'   End: {sub.end_date}', end='')
        if days_since is not None:
            print(f' ({days_since} days ago)')
        else:
            print()
        print(f'   Payment method: {has_payment}')
        if sub.payment_method:
            print(f'   Card: {sub.payment_method.card_last4} ({sub.payment_method.card_brand})')
        print()
    
    # Get the most recent subscription
    latest_sub = subs.first()
    
    if latest_sub.status in ['expired', 'inactive']:
        print('\n' + '=' * 70)
        print('REACTIVATING SUBSCRIPTION (OPTION 1: EXTEND)')
        print('=' * 70)
        
        # Calculate extension
        if latest_sub.plan.billing_period == 'weekly':
            extension = timedelta(days=7)
        elif latest_sub.plan.billing_period == 'monthly':
            extension = timedelta(days=30)
        elif latest_sub.plan.billing_period == 'quarterly':
            extension = timedelta(days=90)
        elif latest_sub.plan.billing_period == 'yearly':
            extension = timedelta(days=365)
        else:
            extension = timedelta(days=30)
        
        new_end_date = timezone.now() + extension
        new_billing_date = new_end_date
        
        print(f'\nExtending subscription by: {extension.days} days')
        print(f'New end date: {new_end_date}')
        print(f'Next billing: {new_billing_date}')
        
        # Update subscription
        latest_sub.status = 'active'
        latest_sub.end_date = new_end_date
        latest_sub.next_billing_date = new_billing_date
        latest_sub.save()
        
        # Update user
        user.subscription_status = 'active'
        user.current_plan = latest_sub.plan
        user.save()
        
        print('\n✅ Subscription reactivated!')
        print(f'   Status: {latest_sub.status}')
        print(f'   End date: {latest_sub.end_date}')
        print(f'   Next billing: {latest_sub.next_billing_date}')
        
        # Re-add to Telegram groups
        if latest_sub.plan:
            print(f'\n📱 Re-adding user to Telegram groups...')
            add_user_to_telegram_groups.delay(user.id, str(latest_sub.plan.id))
            print('✅ Task queued!')
        
        print('\n' + '=' * 70)
        print('SUCCESS! User has been given a grace period extension.')
        print(f'They will be auto-charged on: {new_billing_date.date()}')
        print('=' * 70)
    else:
        print(f'\n⚠️  Subscription is already {latest_sub.status}')
        print('No action needed.')
        
except User.DoesNotExist:
    print('\n❌ User not found: derachinaka@gmail.com')
    sys.exit(1)
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
