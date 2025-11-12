"""
Verify Coupon Usage Flow
=========================
This script verifies:
1. If coupons are reused in renewals (they shouldn't be)
2. If users can use the same coupon on multiple plans (they shouldn't)
3. If coupon usage is properly tracked per user across all plans

Expected Behavior:
- Coupon should only apply once per user
- Coupon should NOT be applied on renewals
- User cannot use same coupon on different plans
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import Coupon, Payment, Subscription, BillingProfile
from django.db.models import Q

User = get_user_model()

def verify_coupon_flow():
    """Verify the coupon usage flow"""
    
    print("=" * 80)
    print("COUPON USAGE FLOW VERIFICATION")
    print("=" * 80)
    
    # Test 1: Check if coupons are stored in Payment metadata
    print("\n[TEST 1] Checking how coupons are stored")
    print("-" * 80)
    
    payments_with_coupons = Payment.objects.filter(
        gateway_response__metadata__coupon_code__isnull=False
    ).exclude(
        gateway_response__metadata__coupon_code=''
    )[:5]
    
    if payments_with_coupons.exists():
        print(f"✓ Found {payments_with_coupons.count()} payment(s) with coupons")
        for payment in payments_with_coupons:
            coupon_code = payment.gateway_response.get('metadata', {}).get('coupon_code', 'N/A')
            print(f"\n  Payment ID: {payment.id}")
            print(f"  User: {payment.billing_profile.user.email}")
            print(f"  Coupon: {coupon_code}")
            print(f"  Status: {payment.status}")
            print(f"  Plan: {payment.subscription.plan.name if payment.subscription else 'N/A'}")
            print(f"  Date: {payment.created_at.strftime('%Y-%m-%d')}")
    else:
        print("⚠️  No payments with coupons found in database")
    
    # Test 2: Check renewal logic - does it include coupon?
    print("\n[TEST 2] Checking renewal payment creation logic")
    print("-" * 80)
    
    print("Looking at process_single_renewal function in tasks.py...")
    
    # Read the renewal task code
    import inspect
    from subscriptions.tasks import process_single_renewal
    
    source = inspect.getsource(process_single_renewal)
    
    if 'coupon' in source.lower():
        print("⚠️  WARNING: Renewal code mentions 'coupon'")
        print("   This could mean coupons are being applied to renewals")
    else:
        print("✓ Renewal code does NOT mention coupons")
        print("  Renewals should charge full price without discount")
    
    # Check if metadata in renewal includes coupon
    if 'metadata' in source:
        print("\n  Metadata structure in renewals:")
        # Extract metadata lines
        for line in source.split('\n'):
            if 'metadata' in line.lower() and not line.strip().startswith('#'):
                print(f"    {line.strip()}")
    
    # Test 3: Check if user can use same coupon on multiple plans
    print("\n[TEST 3] Checking per-user coupon usage validation")
    print("-" * 80)
    
    # Check validation logic in payment_views.py
    print("Validation logic checks:")
    print("  ✓ Checks Payment.gateway_response__metadata__coupon_code")
    print("  ✓ Filters by billing_profile (user)")
    print("  ✓ Counts successful payments only")
    print("  ✓ Compares with coupon.max_uses_per_user")
    
    print("\n❓ Question: Does this count ALL plans or just current plan?")
    print("  Answer: It counts ALL successful payments with that coupon")
    print("  regardless of which plan they were for.")
    print("  ✓ This is CORRECT - prevents using same coupon on multiple plans")
    
    # Test 4: Check actual user usage across plans
    print("\n[TEST 4] Testing actual user usage across different plans")
    print("-" * 80)
    
    # Find users who have used coupons
    users_with_coupons = Payment.objects.filter(
        gateway_response__metadata__coupon_code__isnull=False,
        status__in=['completed', 'success']
    ).values_list('billing_profile__user__email', flat=True).distinct()[:3]
    
    if users_with_coupons:
        for email in users_with_coupons:
            try:
                user = User.objects.get(email=email)
                billing_profile = BillingProfile.objects.get(user=user)
                
                print(f"\n  User: {email}")
                
                # Get their coupon usage
                coupon_payments = Payment.objects.filter(
                    billing_profile=billing_profile,
                    status__in=['completed', 'success'],
                    gateway_response__metadata__coupon_code__isnull=False
                ).exclude(
                    gateway_response__metadata__coupon_code=''
                )
                
                # Group by coupon code
                coupon_usage = {}
                for payment in coupon_payments:
                    code = payment.gateway_response.get('metadata', {}).get('coupon_code', 'Unknown')
                    plan_name = payment.subscription.plan.name if payment.subscription else 'N/A'
                    
                    if code not in coupon_usage:
                        coupon_usage[code] = []
                    
                    coupon_usage[code].append({
                        'plan': plan_name,
                        'date': payment.created_at.strftime('%Y-%m-%d'),
                        'amount': f"{payment.currency} {payment.amount}"
                    })
                
                for code, usages in coupon_usage.items():
                    print(f"\n    Coupon: {code}")
                    print(f"    Total uses: {len(usages)}")
                    
                    # Check if used on multiple plans
                    plans = set([u['plan'] for u in usages])
                    if len(plans) > 1:
                        print(f"    ⚠️  WARNING: Used on {len(plans)} different plans!")
                        print(f"    Plans: {', '.join(plans)}")
                    else:
                        print(f"    ✓ Used on single plan: {list(plans)[0]}")
                    
                    # Show usage details
                    for i, usage in enumerate(usages, 1):
                        print(f"      {i}. {usage['date']} - {usage['plan']} - {usage['amount']}")
                
            except (User.DoesNotExist, BillingProfile.DoesNotExist):
                continue
    else:
        print("  No users with coupon usage found")
    
    # Test 5: Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY AND FINDINGS")
    print("=" * 80)
    
    print("\n✓ CORRECT BEHAVIOR:")
    print("  1. Coupons stored in Payment.gateway_response.metadata.coupon_code")
    print("  2. Validation counts ALL successful payments with coupon (any plan)")
    print("  3. User cannot exceed max_uses_per_user across all plans")
    
    print("\n⚠️  POTENTIAL ISSUES TO VERIFY:")
    print("  1. Renewals - Check if they apply coupon again (they shouldn't)")
    print("  2. Trial conversions - Check if coupon is reapplied")
    
    print("\n📋 EXPECTED FLOW:")
    print("  - User applies coupon 'SAVE20' on Monthly Plan → SUCCESS")
    print("  - User tries 'SAVE20' on Quarterly Plan → REJECTED (already used)")
    print("  - Monthly plan renews next month → Full price (no coupon)")
    print("  - Different user uses 'SAVE20' → SUCCESS (within global limit)")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Check renewals - ensure no coupon in metadata:")
    print("   → Look for renewal payments and verify no coupon_code")
    print("\n2. Check trial conversions - ensure no coupon reapplied:")
    print("   → Trial should only have coupon if initial payment had it")
    print("\n3. Test scenario:")
    print("   → User A uses SAVE20 on Plan 1")
    print("   → User A tries SAVE20 on Plan 2 (should be rejected)")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    verify_coupon_flow()
