#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Coupon
from datetime import datetime

# Check all coupon codes in database
print("\n" + "="*70)
print("  EXISTING COUPONS IN DATABASE")
print("="*70 + "\n")

coupons = Coupon.objects.all()

if not coupons.exists():
    print("❌ No coupons found in database.")
    print("\nWould you like to create test coupons?\n")
else:
    print(f"Found {coupons.count()} coupon(s):")
    print()
    
    for idx, coupon in enumerate(coupons, 1):
        print(f"{idx}. CODE: {coupon.code}")
        print(f"   Type: {coupon.discount_type}")
        print(f"   Value: {coupon.discount_value}{'%' if coupon.discount_type == 'percentage' else ' USD'}")
        print(f"   Valid From: {coupon.valid_from.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Valid Until: {coupon.valid_until.strftime('%Y-%m-%d %H:%M') if coupon.valid_until else 'No expiry'}")
        print(f"   Max Uses: {coupon.max_uses if coupon.max_uses else 'Unlimited'}")
        print(f"   Current Uses: {coupon.current_uses}")
        print(f"   Active: {'✅ Yes' if coupon.is_active else '❌ No'}")
        
        # Check if valid now
        now = datetime.now(coupon.valid_from.tzinfo)
        is_valid_time = coupon.valid_from <= now and (not coupon.valid_until or coupon.valid_until >= now)
        is_valid_uses = not coupon.max_uses or coupon.current_uses < coupon.max_uses
        
        if coupon.is_active and is_valid_time and is_valid_uses:
            print(f"   Status: ✅ READY TO USE")
        else:
            reasons = []
            if not coupon.is_active:
                reasons.append("inactive")
            if not is_valid_time:
                reasons.append("expired/not started")
            if not is_valid_uses:
                reasons.append("max uses reached")
            print(f"   Status: ❌ NOT USABLE ({', '.join(reasons)})")
        
        print()

print("="*70)
print()