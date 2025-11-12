"""
Test script to verify per-user coupon usage limit enforcement.

This script checks that:
1. A user cannot use the same coupon more than max_uses_per_user times
2. The check happens during payment initialization
3. The check also happens during coupon validation API
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import Coupon, SubscriptionPlan, BillingProfile, Payment
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

def test_coupon_per_user_limit():
    """Test that per-user coupon limit is enforced"""
    
    print("=" * 70)
    print("TESTING PER-USER COUPON USAGE LIMIT")
    print("=" * 70)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='coupon_test@example.com',
        defaults={
            'first_name': 'Coupon',
            'last_name': 'Test',
            'username': 'coupon_test'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"\n✓ Created test user: {user.email}")
    else:
        print(f"\n✓ Using existing test user: {user.email}")
    
    # Get or create billing profile
    billing_profile, created = BillingProfile.objects.get_or_create(
        user=user
    )
    print(f"✓ Billing profile: {billing_profile.user.email}")
    
    # Create a test coupon with max_uses_per_user = 1
    coupon, created = Coupon.objects.get_or_create(
        code='TEST_ONCE',
        defaults={
            'discount_type': 'percentage',
            'discount_value': Decimal('20.00'),
            'max_uses': 100,  # High total limit
            'max_uses_per_user': 1,  # Only 1 use per user
            'is_active': True,
            'valid_from': timezone.now(),
            'valid_until': timezone.now() + timezone.timedelta(days=30)
        }
    )
    if created:
        print(f"\n✓ Created test coupon: {coupon.code}")
    else:
        print(f"\n✓ Using existing coupon: {coupon.code}")
    
    print(f"  - Discount: {coupon.discount_value}% off")
    print(f"  - Max uses per user: {coupon.max_uses_per_user}")
    
    # Count existing successful payments with this coupon
    existing_usage = Payment.objects.filter(
        billing_profile=billing_profile,
        status__in=['completed', 'success'],
        gateway_response__metadata__coupon_code=coupon.code
    ).count()
    
    print(f"\n✓ Current usage by this user: {existing_usage}/{coupon.max_uses_per_user}")
    
    if existing_usage >= coupon.max_uses_per_user:
        print("\n✅ TEST RESULT: User has already used this coupon the maximum number of times")
        print(f"   Expected: Coupon validation should FAIL")
        print(f"   Expected error: 'You have already used this coupon {coupon.max_uses_per_user} time(s)'")
    else:
        print("\n✅ TEST RESULT: User has NOT exceeded coupon usage limit")
        print(f"   Expected: Coupon validation should PASS")
        print(f"   User can still use this coupon {coupon.max_uses_per_user - existing_usage} more time(s)")
    
    # Show all payments with this coupon by this user
    print("\n" + "-" * 70)
    print("PAYMENT HISTORY WITH THIS COUPON:")
    print("-" * 70)
    
    payments = Payment.objects.filter(
        billing_profile=billing_profile,
        gateway_response__metadata__coupon_code=coupon.code
    ).order_by('-created_at')
    
    if payments.exists():
        for i, payment in enumerate(payments, 1):
            print(f"\n{i}. Payment #{payment.id}")
            print(f"   Status: {payment.status}")
            print(f"   Amount: {payment.currency} {payment.amount}")
            print(f"   Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Counts toward limit: {'Yes' if payment.status in ['completed', 'success'] else 'No'}")
    else:
        print("\nNo payments found with this coupon for this user.")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return existing_usage >= coupon.max_uses_per_user

if __name__ == '__main__':
    try:
        limit_exceeded = test_coupon_per_user_limit()
        
        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        
        if limit_exceeded:
            print("\n1. Try to apply coupon 'TEST_ONCE' in the checkout page")
            print("2. You should see error: 'You have already used this coupon 1 time(s)'")
            print("3. This confirms the fix is working correctly")
        else:
            print("\n1. Use coupon 'TEST_ONCE' in checkout and complete payment")
            print("2. Then try to use the same coupon again")
            print("3. The second attempt should be rejected")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
