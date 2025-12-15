#!/usr/bin/env python
"""
Delete Lifetime Mentorship subscription for specific user
Keeps Weekly Signals subscription intact
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.utils import timezone
from subscriptions.models import Subscription, BillingProfile, SubscriptionPlan
from users.models import User

def delete_mentorship_subscription(email):
    """Delete only the Lifetime Mentorship subscription for user"""
    try:
        # Get user
        user = User.objects.get(email=email)
        print(f"\n✓ Found user: {user.email}")
        
        # Get billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        print(f"✓ Found billing profile: {billing_profile.id}")
        
        # Get Lifetime Mentorship plan
        mentorship_plan = SubscriptionPlan.objects.get(name='Lifetime Mentorship')
        print(f"✓ Found plan: {mentorship_plan.name}")
        
        # Get subscription for this specific plan
        subscription = Subscription.objects.filter(
            billing_profile=billing_profile,
            plan=mentorship_plan,
            status='active'
        ).first()
        
        if not subscription:
            print(f"\n❌ No active Lifetime Mentorship subscription found for {email}")
            return False
        
        # Show subscription details before deletion
        print(f"\n{'='*70}")
        print(f"📋 SUBSCRIPTION TO DELETE")
        print(f"{'='*70}")
        print(f"ID: {subscription.id}")
        print(f"Plan: {subscription.plan.name}")
        print(f"Status: {subscription.status}")
        print(f"Start: {subscription.start_date}")
        print(f"End: {subscription.end_date}")
        print(f"Auto-renew: {subscription.auto_renew}")
        print(f"{'='*70}\n")
        
        # Confirm deletion
        confirm = input("Delete this subscription? (type 'yes' to confirm): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Deletion cancelled")
            return False
        
        # Delete the subscription
        subscription.delete()
        
        print(f"\n✅ Successfully deleted Lifetime Mentorship subscription")
        print(f"✓ Subscription ID: {subscription.id}")
        print(f"✓ User still has other active subscriptions (if any)")
        
        # Check remaining subscriptions
        remaining = Subscription.objects.filter(
            billing_profile=billing_profile,
            status='active'
        )
        
        print(f"\n📊 Remaining active subscriptions: {remaining.count()}")
        for sub in remaining:
            print(f"   - {sub.plan.name} (ends: {sub.end_date})")
        
        return True
        
    except User.DoesNotExist:
        print(f"❌ User not found: {email}")
        return False
    except BillingProfile.DoesNotExist:
        print(f"❌ Billing profile not found for user: {email}")
        return False
    except SubscriptionPlan.DoesNotExist:
        print(f"❌ Lifetime Mentorship plan not found")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python delete_mentorship_sub.py <user_email>")
        print("Example: python delete_mentorship_sub.py derachinaka@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    delete_mentorship_subscription(email)
