"""
Fix the subscription for chiderachinaka06 by setting the end date
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import SignalSubscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print("=" * 80)
print("🔧 FIXING SUBSCRIPTION FOR chiderachinaka06")
print("=" * 80)

try:
    chidera = User.objects.get(email='chiderachinaka06@gmail.com')
    print(f"\n✅ User found: {chidera.email}")
    
    # Get the subscription
    sub = SignalSubscription.objects.get(
        user=chidera,
        id='8a6769db-8267-4cf0-8fe5-fc7a147c1fd9'
    )
    
    print(f"\n📋 Current Subscription Details:")
    print(f"   ID: {sub.id}")
    print(f"   Plan: {sub.pricing_plan.name if sub.pricing_plan else 'None'}")
    print(f"   Start Date: {sub.subscription_start}")
    print(f"   End Date: {sub.subscription_end}")
    print(f"   Payment Status: {sub.payment_status}")
    
    # Fix the subscription
    if not sub.subscription_end:
        print(f"\n⚠️  End date is missing! Fixing now...")
        
        # Set end date based on plan type
        if sub.plan_type in ['signals_weekly', 'vip_weekly']:
            days_to_add = 7
        elif sub.plan_type in ['signals_monthly', 'vip_monthly', 'mentorship_basic']:
            days_to_add = 30
        elif sub.plan_type in ['signals_yearly', 'vip_yearly']:
            days_to_add = 365
        else:
            days_to_add = 30  # Default to 30 days
        
        # Calculate end date from start date
        if sub.subscription_start:
            sub.subscription_end = sub.subscription_start + timedelta(days=days_to_add)
        else:
            # If no start date either, set both to now
            sub.subscription_start = timezone.now()
            sub.subscription_end = timezone.now() + timedelta(days=days_to_add)
        
        sub.save()
        
        print(f"\n✅ Subscription fixed!")
        print(f"   New Start Date: {sub.subscription_start}")
        print(f"   New End Date: {sub.subscription_end}")
        
        # Check if now active
        is_active = (
            sub.payment_status == 'verified' and
            sub.subscription_end and
            timezone.now() <= sub.subscription_end
        )
        
        if is_active:
            days_left = (sub.subscription_end - timezone.now()).days
            print(f"   Status: ✅ ACTIVE")
            print(f"   Days Remaining: {days_left}")
        else:
            print(f"   Status: ❌ INACTIVE")
    else:
        print(f"\n✅ Subscription already has an end date")
        
        # Check if active
        is_active = (
            sub.payment_status == 'verified' and
            sub.subscription_end and
            timezone.now() <= sub.subscription_end
        )
        
        if is_active:
            days_left = (sub.subscription_end - timezone.now()).days
            print(f"   Status: ✅ ACTIVE")
            print(f"   Days Remaining: {days_left}")
        else:
            print(f"   Status: ❌ INACTIVE")

except User.DoesNotExist:
    print("\n❌ User not found!")
except SignalSubscription.DoesNotExist:
    print("\n❌ Subscription not found!")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
