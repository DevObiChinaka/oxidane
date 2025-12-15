#!/usr/bin/env python
"""
Test Auto-Renewal Flow
This script helps test the auto-renewal system without waiting for actual renewal dates
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

from subscriptions.models import Subscription, User
from subscriptions.tasks import process_auto_renewals, process_single_renewal

print("=" * 70)
print("AUTO-RENEWAL TEST UTILITY")
print("=" * 70)

def list_test_candidates():
    """List subscriptions that can be used for testing"""
    print("\n📋 Active subscriptions with auto-renew enabled:\n")
    
    subs = Subscription.objects.filter(
        status='active',
        auto_renew=True
    ).select_related('billing_profile__user', 'plan', 'payment_method')
    
    if not subs.exists():
        print("❌ No active subscriptions with auto-renew enabled found!")
        return []
    
    for i, sub in enumerate(subs, 1):
        user = sub.billing_profile.user
        has_payment = "✅" if sub.payment_method and sub.payment_method.is_active else "❌"
        print(f"{i}. User: {user.email}")
        print(f"   Plan: {sub.plan.name} ({sub.plan.billing_period})")
        print(f"   Current end date: {sub.end_date}")
        print(f"   Next billing: {sub.next_billing_date}")
        print(f"   Payment method: {has_payment}")
        print(f"   Subscription ID: {sub.id}")
        print()
    
    return list(subs)

def set_renewal_date_to_today(subscription_id):
    """Set a subscription's next_billing_date to today for testing"""
    try:
        sub = Subscription.objects.select_related('billing_profile__user').get(id=subscription_id)
        today = timezone.now().date()
        
        print(f"\n🔧 Modifying subscription for: {sub.billing_profile.user.email}")
        print(f"   Old next_billing_date: {sub.next_billing_date}")
        
        # Set next billing to today
        sub.next_billing_date = today
        sub.save(update_fields=['next_billing_date'])
        
        print(f"   ✅ New next_billing_date: {sub.next_billing_date}")
        print(f"\n💡 Now run: process_auto_renewals() or process_single_renewal('{subscription_id}')")
        
        return True
    except Subscription.DoesNotExist:
        print(f"❌ Subscription {subscription_id} not found!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def trigger_single_renewal(subscription_id):
    """Manually trigger renewal for a specific subscription"""
    print(f"\n🚀 Triggering renewal for subscription: {subscription_id}\n")
    
    try:
        result = process_single_renewal(str(subscription_id))
        print("\n📊 Result:")
        print(result)
        return result
    except Exception as e:
        print(f"\n❌ Error during renewal: {e}")
        import traceback
        traceback.print_exc()
        return None

def trigger_all_renewals():
    """Run the process_auto_renewals task"""
    print("\n🚀 Running process_auto_renewals task...\n")
    
    try:
        result = process_auto_renewals()
        print("\n📊 Result:")
        print(result)
        return result
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Interactive menu
if __name__ == '__main__':
    while True:
        print("\n" + "=" * 70)
        print("MENU:")
        print("1. List active subscriptions (with auto-renew)")
        print("2. Set subscription next_billing_date to TODAY")
        print("3. Trigger single subscription renewal")
        print("4. Trigger ALL renewals (process_auto_renewals)")
        print("5. Exit")
        print("=" * 70)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            list_test_candidates()
        
        elif choice == '2':
            subs = list_test_candidates()
            if subs:
                try:
                    idx = int(input("\nEnter subscription number: ")) - 1
                    if 0 <= idx < len(subs):
                        set_renewal_date_to_today(subs[idx].id)
                    else:
                        print("❌ Invalid number!")
                except ValueError:
                    print("❌ Please enter a valid number!")
        
        elif choice == '3':
            sub_id = input("\nEnter subscription ID: ").strip()
            if sub_id:
                trigger_single_renewal(sub_id)
        
        elif choice == '4':
            confirm = input("\n⚠️  This will process ALL subscriptions due today. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                trigger_all_renewals()
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")
