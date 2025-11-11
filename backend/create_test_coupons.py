#!/usr/bin/env python
"""Create test coupons for payment flow testing"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Coupon
from datetime import datetime, timedelta
from django.utils import timezone

print("\n" + "="*70)
print("  CREATING TEST COUPONS")
print("="*70 + "\n")

# Create test coupons
coupons_to_create = [
    {
        'code': 'SAVE10',
        'discount_type': 'percentage',
        'discount_value': 10,
        'description': '10% off any plan',
        'max_uses': 100,
        'valid_from': timezone.now(),
        'valid_until': timezone.now() + timedelta(days=30),
        'is_active': True
    },
    {
        'code': 'SAVE20',
        'discount_type': 'percentage',
        'discount_value': 20,
        'description': '20% off any plan',
        'max_uses': 50,
        'valid_from': timezone.now(),
        'valid_until': timezone.now() + timedelta(days=30),
        'is_active': True
    },
    {
        'code': 'FLAT5',
        'discount_type': 'fixed',
        'discount_value': 5,
        'description': '$5 off any plan',
        'max_uses': 200,
        'valid_from': timezone.now(),
        'valid_until': timezone.now() + timedelta(days=60),
        'is_active': True
    },
    {
        'code': 'WELCOME',
        'discount_type': 'percentage',
        'discount_value': 15,
        'description': '15% welcome discount',
        'max_uses': None,  # Unlimited
        'valid_from': timezone.now(),
        'valid_until': None,  # No expiry
        'is_active': True
    },
    {
        'code': 'EXPIRED',
        'discount_type': 'percentage',
        'discount_value': 50,
        'description': 'Expired coupon for testing',
        'max_uses': 10,
        'valid_from': timezone.now() - timedelta(days=60),
        'valid_until': timezone.now() - timedelta(days=30),
        'is_active': True
    },
]

created_count = 0
for coupon_data in coupons_to_create:
    coupon, created = Coupon.objects.get_or_create(
        code=coupon_data['code'],
        defaults=coupon_data
    )
    
    if created:
        print(f"✅ Created: {coupon.code}")
        print(f"   Type: {coupon.discount_type}")
        print(f"   Value: {coupon.discount_value}{'%' if coupon.discount_type == 'percentage' else ' USD'}")
        print(f"   Max Uses: {coupon.max_uses if coupon.max_uses else 'Unlimited'}")
        print(f"   Valid Until: {coupon.valid_until.strftime('%Y-%m-%d') if coupon.valid_until else 'No expiry'}")
        created_count += 1
    else:
        print(f"⚠️  Already exists: {coupon.code}")
    print()

print("="*70)
print(f"Created {created_count} new coupon(s)")
print("="*70)
print("\n✅ Test Coupons:")
print("   - SAVE10  : 10% off (valid 30 days)")
print("   - SAVE20  : 20% off (valid 30 days)")
print("   - FLAT5   : $5 off (valid 60 days)")
print("   - WELCOME : 15% off (unlimited, no expiry)")
print("   - EXPIRED : 50% off (expired - for error testing)")
print()
