#!/usr/bin/env python
"""Check if a user used any coupons and examine coupon tracking."""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import Subscription, Coupon
from django.db import connection

User = get_user_model()

# Find user
email = 'obbinachidera123@gmail.com'
user = User.objects.filter(email=email).first()

print(f"=== Checking Coupon Usage for {email} ===\n")

if not user:
    print(f"❌ User not found: {email}")
    exit(1)

print(f"✓ User found: {user.username} (ID: {user.id})")
print()

# Check subscriptions
subs = Subscription.objects.filter(billing_profile__user=user).order_by('-created_at')
print(f"📋 Subscriptions: {subs.count()}")

for i, sub in enumerate(subs, 1):
    print(f"\n  Subscription {i}:")
    print(f"    Plan: {sub.plan.name if sub.plan else 'No plan'}")
    print(f"    Amount: {sub.amount_paid} {sub.currency}")
    print(f"    Status: {sub.status}")
    print(f"    Created: {sub.created_at}")
    
    # Check metadata for coupon info
    if sub.metadata:
        print(f"    Metadata: {sub.metadata}")

print("\n" + "="*60)

# Check Subscription table schema for coupon field
print("\n🔍 Checking Subscription table for coupon-related fields...")
cursor = connection.cursor()
# PostgreSQL query instead of PRAGMA
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'subscriptions_subscription'
    AND column_name LIKE '%coupon%'
""")
columns = cursor.fetchall()

if columns:
    print("  ✓ Coupon fields found:")
    for col in columns:
        print(f"    - {col[0]} ({col[1]})")
else:
    print("  ❌ No coupon field found in Subscription model!")
    print("  📝 Checking metadata field for coupon info...")
    
    for i, sub in enumerate(subs, 1):
        if sub.metadata and 'coupon' in str(sub.metadata).lower():
            print(f"    Subscription {i} metadata contains coupon info: {sub.metadata}")

print("\n" + "="*60)

# Check all coupons and their usage
print("\n💰 All Coupons in System:")
coupons = Coupon.objects.all().order_by('-created_at')
print(f"  Total coupons: {coupons.count()}")

for coupon in coupons:
    print(f"\n  {coupon.code}:")
    print(f"    Type: {coupon.discount_type} - {coupon.discount_value}")
    print(f"    Usage: {coupon.current_uses}/{coupon.max_uses or 'unlimited'}")
    print(f"    Active: {coupon.is_active}")

print("\n" + "="*60)
print("\n✅ Analysis complete!")
