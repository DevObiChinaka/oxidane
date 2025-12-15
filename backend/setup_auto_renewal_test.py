#!/usr/bin/env python
"""
Set derachinaka's subscription to end TODAY so auto-renewal runs tonight at 2 AM
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

print('=' * 70)
print('SETTING UP AUTO-RENEWAL TEST FOR TONIGHT')
print('=' * 70)

email = 'derachinaka@gmail.com'

try:
    user = User.objects.get(email=email)
    sub = Subscription.objects.filter(
        billing_profile__user=user,
        status='active'
    ).select_related('plan', 'payment_method').first()
    
    if not sub:
        print('\n❌ No active subscription found')
        sys.exit(1)
    
    print(f'\n📊 Current State:')
    print(f'   User: {user.email}')
    print(f'   Subscription ID: {sub.id}')
    print(f'   Plan: {sub.plan.name if sub.plan else "N/A"}')
    print(f'   Billing Period: {sub.plan.billing_period if sub.plan else "N/A"}')
    print(f'   Status: {sub.status}')
    print(f'   Current end_date: {sub.end_date}')
    print(f'   Current next_billing_date: {sub.next_billing_date}')
    print(f'   Auto-renew: {sub.auto_renew}')
    print(f'   Payment method: {"✅" if sub.payment_method else "❌"}')
    
    # Set to end TODAY (so it will be picked up by tonight's 2 AM auto-renewal)
    now = timezone.now()
    today_end = now.replace(hour=23, minute=59, second=59)  # End of today
    
    print(f'\n🔧 Setting subscription to end TODAY:')
    print(f'   Current time: {now}')
    print(f'   New end_date: {today_end}')
    print(f'   New next_billing_date: {today_end}')
    
    sub.end_date = today_end
    sub.next_billing_date = today_end
    sub.status = 'active'  # Ensure it's active
    sub.save()
    
    print(f'\n✅ Updated!')
    
    print(f'\n📅 What Will Happen:')
    print(f'   Tonight at 02:00 UTC (2 AM):')
    print(f'     - process_auto_renewals task runs')
    print(f'     - Finds subscriptions with next_billing_date == today')
    print(f'     - Charges {sub.payment_method.card_last4} ({sub.payment_method.card_type})')
    print(f'     - Extends subscription by {sub.plan.billing_period} period')
    print(f'     - Updates next_billing_date to {(today_end + timedelta(days=7)).date()} (next week)')
    
    print(f'\n   Tomorrow at 00:00 UTC (Midnight):')
    print(f'     - check_expired_subscriptions runs')
    print(f'     - Checks if end_date < (now - 24 hours)')
    print(f'     - Will NOT expire (just renewed)')
    
    print(f'\n🧪 Testing Schedule:')
    print(f'   1. Tonight 02:00 UTC - Auto-renewal should charge and extend')
    print(f'   2. Check logs tomorrow: journalctl -u oxidane-celery-beat --since "6 hours ago" | grep renewal')
    print(f'   3. Verify subscription extended to {(today_end + timedelta(days=7)).date()}')
    
    print(f'\n⚠️  Important:')
    print(f'   - Payment method valid: {"✅" if sub.payment_method else "❌"}')
    print(f'   - Auto-renew enabled: {"✅" if sub.auto_renew else "❌"}')
    print(f'   - Status active: {"✅" if sub.status == "active" else "❌"}')
    print(f'   - All conditions met for auto-renewal: {"✅" if (sub.payment_method and sub.auto_renew and sub.status == "active") else "❌"}')
    
    print('\n' + '=' * 70)
    print('✅ SUBSCRIPTION CONFIGURED FOR TONIGHT\'S AUTO-RENEWAL')
    print('=' * 70)
    
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
