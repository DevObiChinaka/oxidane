#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import CouponCode

# Check all coupon codes in database
print("=== All Coupon Codes in Database ===")
coupons = CouponCode.objects.all()

if not coupons.exists():
    print("No coupon codes found in database.")
else:
    print(f"Found {coupons.count()} coupon code(s):")
    print()
    
    for coupon in coupons:
        print(f"ID: {coupon.id}")
        print(f"Code: {coupon.code}")
        print(f"Description: {coupon.description}")
        print(f"Discount Type: {coupon.discount_type}")
        print(f"Discount Value: {coupon.discount_value}")
        print(f"Is Active: {coupon.is_active}")
        print(f"Valid From: {coupon.valid_from}")
        print(f"Valid Until: {coupon.valid_until}")
        print(f"Usage Limit: {coupon.usage_limit}")
        print(f"Usage Count: {coupon.usage_count}")
        print(f"Created At: {coupon.created_at}")
        print("-" * 50)

# Check specifically for SUMMER2025
print("\n=== Checking for SUMMER2025 ===")
try:
    summer_coupon = CouponCode.objects.get(code="SUMMER2025")
    print("Found SUMMER2025 coupon:")
    print(f"  ID: {summer_coupon.id}")
    print(f"  Active: {summer_coupon.is_active}")
    print(f"  Valid From: {summer_coupon.valid_from}")
    print(f"  Valid Until: {summer_coupon.valid_until}")
except CouponCode.DoesNotExist:
    print("SUMMER2025 coupon not found in database.")