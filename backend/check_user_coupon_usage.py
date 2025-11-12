"""
Check which coupons a specific user has used and how many times.
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import Coupon, BillingProfile, Payment
from django.db.models import Q

User = get_user_model()

def check_user_coupon_usage(email=None):
    """Check coupon usage for a specific user"""
    
    print("=" * 70)
    print("USER COUPON USAGE CHECKER")
    print("=" * 70)
    
    # Get user email
    if not email:
        email = input("\nEnter user email: ").strip()
    
    # Find user
    try:
        user = User.objects.get(email=email)
        print(f"\n✓ Found user: {user.email} ({user.first_name} {user.last_name})")
    except User.DoesNotExist:
        print(f"\n❌ User with email '{email}' not found")
        return
    
    # Get billing profile
    try:
        billing_profile = BillingProfile.objects.get(user=user)
        print(f"✓ Billing profile ID: {billing_profile.id}")
    except BillingProfile.DoesNotExist:
        print("❌ No billing profile found for this user")
        return
    
    # Get all payments with coupons
    payments_with_coupons = Payment.objects.filter(
        billing_profile=billing_profile,
        gateway_response__metadata__coupon_code__isnull=False
    ).exclude(
        gateway_response__metadata__coupon_code=''
    ).order_by('-created_at')
    
    if not payments_with_coupons.exists():
        print("\n✓ This user has NOT used any coupons yet")
        print("\n" + "=" * 70)
        return
    
    print(f"\n✓ Found {payments_with_coupons.count()} payment(s) with coupons")
    print("\n" + "-" * 70)
    print("COUPON USAGE HISTORY:")
    print("-" * 70)
    
    # Group by coupon code
    coupon_usage = {}
    
    for payment in payments_with_coupons:
        try:
            coupon_code = payment.gateway_response.get('metadata', {}).get('coupon_code', 'Unknown')
            
            if coupon_code not in coupon_usage:
                coupon_usage[coupon_code] = {
                    'total': 0,
                    'successful': 0,
                    'payments': []
                }
            
            coupon_usage[coupon_code]['total'] += 1
            if payment.status in ['completed', 'success']:
                coupon_usage[coupon_code]['successful'] += 1
            
            coupon_usage[coupon_code]['payments'].append({
                'id': str(payment.id),
                'status': payment.status,
                'amount': f"{payment.currency} {payment.amount}",
                'date': payment.created_at.strftime('%Y-%m-%d %H:%M'),
                'counts': payment.status in ['completed', 'success']
            })
        except Exception as e:
            print(f"Error processing payment {payment.id}: {e}")
    
    # Display results
    for coupon_code, data in coupon_usage.items():
        print(f"\n📌 Coupon: {coupon_code}")
        print(f"   Total uses: {data['total']}")
        print(f"   Successful uses (count toward limit): {data['successful']}")
        
        # Get coupon details
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            print(f"   Max uses per user: {coupon.max_uses_per_user}")
            print(f"   Status: {'✅ Can still use' if data['successful'] < coupon.max_uses_per_user else '❌ Limit reached'}")
        except Coupon.DoesNotExist:
            print(f"   ⚠️ Coupon not found in database (may have been deleted)")
        
        print("\n   Payment Details:")
        for i, p in enumerate(data['payments'], 1):
            counts_icon = "✅" if p['counts'] else "⏳"
            print(f"   {i}. {counts_icon} {p['date']} - {p['status']} - {p['amount']}")
            print(f"      Payment ID: {p['id']}")
            print(f"      Counts toward limit: {'Yes' if p['counts'] else 'No'}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for coupon_code, data in coupon_usage.items():
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            remaining = coupon.max_uses_per_user - data['successful']
            if remaining > 0:
                print(f"\n✅ {coupon_code}: Can use {remaining} more time(s)")
            else:
                print(f"\n❌ {coupon_code}: LIMIT REACHED (used {data['successful']}/{coupon.max_uses_per_user} times)")
        except Coupon.DoesNotExist:
            print(f"\n⚠️ {coupon_code}: Coupon no longer exists")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else None
    check_user_coupon_usage(email)
