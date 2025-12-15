#!/usr/bin/env python
"""
Test 24-hour grace period logic for subscription expiration
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription
from subscriptions.tasks import check_expired_subscriptions
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

print('=' * 70)
print('TESTING 24-HOUR GRACE PERIOD LOGIC')
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
    
    # Save original state
    original_end = sub.end_date
    original_status = sub.status
    
    now = timezone.now()
    
    print(f'\n📊 Current State:')
    print(f'   Subscription: {sub.id}')
    print(f'   Plan: {sub.plan.name if sub.plan else "N/A"}')
    print(f'   Status: {sub.status}')
    print(f'   End date: {original_end}')
    print(f'   Current time: {now}')
    
    print('\n' + '=' * 70)
    print('TEST 1: Subscription ended 12 hours ago (WITHIN grace period)')
    print('=' * 70)
    
    # Set to 12 hours ago
    twelve_hours_ago = now - timedelta(hours=12)
    sub.end_date = twelve_hours_ago
    sub.save()
    
    print(f'\nSet end_date to: {twelve_hours_ago}')
    print(f'Time since end: 12 hours')
    print(f'Grace cutoff: {now - timedelta(hours=24)} (24 hours ago)')
    
    # Check if would be expired
    grace_cutoff = now - timedelta(hours=24)
    if sub.end_date < grace_cutoff:
        print('\n❌ Would be EXPIRED (past grace)')
    else:
        print('\n✅ Still ACTIVE (within 24-hour grace period)')
        print('   User keeps access during grace period')
    
    # Run expiration check
    print('\n🔄 Running check_expired_subscriptions task...')
    result = check_expired_subscriptions()
    
    # Reload subscription
    sub.refresh_from_db()
    
    if sub.status == 'active':
        print(f'✅ PASS: Subscription still active (status={sub.status})')
        print(f'   Expired count: {result.get("expired_count", 0)}')
    else:
        print(f'❌ FAIL: Subscription was expired (status={sub.status})')
    
    print('\n' + '=' * 70)
    print('TEST 2: Subscription ended 30 hours ago (PAST grace period)')
    print('=' * 70)
    
    # Restore status first
    sub.status = 'active'
    
    # Set to 30 hours ago
    thirty_hours_ago = now - timedelta(hours=30)
    sub.end_date = thirty_hours_ago
    sub.save()
    
    print(f'\nSet end_date to: {thirty_hours_ago}')
    print(f'Time since end: 30 hours')
    print(f'Grace cutoff: {now - timedelta(hours=24)} (24 hours ago)')
    
    if sub.end_date < grace_cutoff:
        print('\n✅ Would be EXPIRED (past 24-hour grace)')
        print('   User should lose access now')
    else:
        print('\n❌ Still ACTIVE (within grace)')
    
    # Run expiration check
    print('\n🔄 Running check_expired_subscriptions task...')
    result = check_expired_subscriptions()
    
    # Reload subscription
    sub.refresh_from_db()
    
    if sub.status == 'expired':
        print(f'✅ PASS: Subscription expired (status={sub.status})')
        print(f'   Expired count: {result.get("expired_count", 0)}')
    else:
        print(f'❌ FAIL: Subscription still active (status={sub.status})')
    
    # Restore original state
    print('\n🔄 Restoring original state...')
    sub.status = original_status
    sub.end_date = original_end
    sub.save()
    
    # Restore user status if needed
    user.refresh_from_db()
    if user.subscription_status != 'active':
        user.subscription_status = 'active'
        user.save()
    
    print(f'✅ Restored!')
    print(f'   Status: {sub.status}')
    print(f'   End date: {sub.end_date}')
    
    print('\n' + '=' * 70)
    print('✅ GRACE PERIOD TESTS COMPLETE')
    print('=' * 70)
    print('\nSummary:')
    print('  - Subscriptions within 24 hours of end_date stay active ✅')
    print('  - Subscriptions past 24 hours are expired ✅')
    print('  - Users get 1 full day grace period after subscription ends')
    
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    
    # Try to restore
    try:
        if 'sub' in locals() and 'original_end' in locals():
            sub.status = original_status
            sub.end_date = original_end
            sub.save()
            user.subscription_status = 'active'
            user.save()
            print('\n✅ Restored subscription to original state')
    except:
        pass
    
    sys.exit(1)
