#!/usr/bin/env python
"""
Handle Affected User - Subscription Didn't Auto-Renew
This script helps you fix users whose subscriptions expired during the Celery Beat downtime
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

from subscriptions.models import Subscription, User, BillingProfile
from subscriptions.tasks import process_single_renewal, add_user_to_telegram_groups

print("=" * 70)
print("FIX AFFECTED USER - MANUAL SUBSCRIPTION RECOVERY")
print("=" * 70)

def find_inactive_subscriptions():
    """Find subscriptions that expired recently (last 7 days) with auto-renew enabled"""
    print("\n🔍 Finding subscriptions that expired recently...\n")
    
    week_ago = timezone.now() - timedelta(days=7)
    
    subs = Subscription.objects.filter(
        status__in=['expired', 'inactive'],
        auto_renew=True,
        end_date__gte=week_ago
    ).select_related('billing_profile__user', 'plan', 'payment_method').order_by('-end_date')
    
    if not subs.exists():
        print("✅ No recently expired subscriptions with auto-renew found!")
        return []
    
    print(f"Found {subs.count()} subscriptions:\n")
    
    for i, sub in enumerate(subs, 1):
        user = sub.billing_profile.user
        days_since_expired = (timezone.now() - sub.end_date).days if sub.end_date else None
        has_payment = "✅" if sub.payment_method and sub.payment_method.is_active else "❌"
        
        print(f"{i}. User: {user.email}")
        print(f"   Plan: {sub.plan.name} ({sub.plan.billing_period})")
        print(f"   Status: {sub.status.upper()}")
        print(f"   Expired: {sub.end_date} ({days_since_expired} days ago)")
        print(f"   Payment method: {has_payment}")
        if sub.payment_method:
            print(f"   Card: {sub.payment_method.card_last4} ({sub.payment_method.card_brand})")
        print(f"   Subscription ID: {sub.id}")
        print()
    
    return list(subs)

def reactivate_subscription(subscription_id, option='extend'):
    """
    Reactivate a subscription using one of three methods:
    1. 'extend' - Extend the subscription without charging (manual grace period)
    2. 'charge' - Attempt to charge the payment method now
    3. 'reset' - Reset to active and set new billing dates
    """
    try:
        sub = Subscription.objects.select_related(
            'billing_profile__user', 'plan', 'payment_method'
        ).get(id=subscription_id)
        
        user = sub.billing_profile.user
        
        print(f"\n🔧 Reactivating subscription for: {user.email}")
        print(f"   Current status: {sub.status}")
        print(f"   Current end date: {sub.end_date}")
        
        if option == 'extend':
            # OPTION 1: Extend subscription by the billing period (grace period)
            print("\n📅 Option 1: Extending subscription (no charge)...")
            
            if sub.plan.billing_period == 'weekly':
                extension = timedelta(days=7)
            elif sub.plan.billing_period == 'monthly':
                extension = timedelta(days=30)
            elif sub.plan.billing_period == 'quarterly':
                extension = timedelta(days=90)
            elif sub.plan.billing_period == 'yearly':
                extension = timedelta(days=365)
            else:
                extension = timedelta(days=30)
            
            new_end_date = timezone.now() + extension
            new_billing_date = new_end_date
            
            sub.status = 'active'
            sub.end_date = new_end_date
            sub.next_billing_date = new_billing_date
            sub.save()
            
            # Update user status
            user.subscription_status = 'active'
            user.current_plan = sub.plan
            user.save()
            
            print(f"   ✅ New status: {sub.status}")
            print(f"   ✅ New end date: {sub.end_date}")
            print(f"   ✅ Next billing: {sub.next_billing_date}")
            print(f"\n💡 User has been given a grace period extension")
            print(f"💡 They will be charged on: {new_billing_date}")
            
            # Re-add to Telegram groups
            if sub.plan:
                print(f"\n📱 Re-adding user to Telegram groups...")
                add_user_to_telegram_groups.delay(user.id, str(sub.plan.id))
            
            return True
        
        elif option == 'charge':
            # OPTION 2: Attempt to charge now
            print("\n💳 Option 2: Attempting to charge payment method now...")
            
            if not sub.payment_method or not sub.payment_method.is_active:
                print("❌ No active payment method found!")
                print("💡 User needs to add/update their payment method")
                return False
            
            # First reactivate the subscription temporarily
            sub.status = 'active'
            sub.next_billing_date = timezone.now().date()
            sub.save()
            
            # Trigger renewal
            print("🚀 Triggering renewal process...")
            result = process_single_renewal(str(subscription_id))
            
            print("\n📊 Renewal result:")
            print(result)
            
            if result.get('success'):
                print("\n✅ Subscription successfully renewed and charged!")
                return True
            else:
                print(f"\n❌ Renewal failed: {result.get('error')}")
                print("💡 Consider using Option 1 (extend) or Option 3 (reset)")
                return False
        
        elif option == 'reset':
            # OPTION 3: Reset subscription as if it's brand new
            print("\n🔄 Option 3: Resetting subscription...")
            
            if sub.plan.billing_period == 'weekly':
                extension = timedelta(days=7)
            elif sub.plan.billing_period == 'monthly':
                extension = timedelta(days=30)
            elif sub.plan.billing_period == 'quarterly':
                extension = timedelta(days=90)
            elif sub.plan.billing_period == 'yearly':
                extension = timedelta(days=365)
            else:
                extension = timedelta(days=30)
            
            sub.status = 'active'
            sub.start_date = timezone.now()
            sub.end_date = timezone.now() + extension
            sub.next_billing_date = sub.end_date
            sub.save()
            
            user.subscription_status = 'active'
            user.current_plan = sub.plan
            user.save()
            
            print(f"   ✅ Status reset to: {sub.status}")
            print(f"   ✅ New start date: {sub.start_date}")
            print(f"   ✅ New end date: {sub.end_date}")
            print(f"\n💡 Subscription has been completely reset")
            
            # Re-add to Telegram groups
            if sub.plan:
                print(f"\n📱 Re-adding user to Telegram groups...")
                add_user_to_telegram_groups.delay(user.id, str(sub.plan.id))
            
            return True
        
    except Subscription.DoesNotExist:
        print(f"❌ Subscription {subscription_id} not found!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Interactive menu
if __name__ == '__main__':
    while True:
        print("\n" + "=" * 70)
        print("MENU:")
        print("1. Find recently expired subscriptions (with auto-renew)")
        print("2. Reactivate subscription - OPTION 1: Extend (grace period, no charge)")
        print("3. Reactivate subscription - OPTION 2: Charge now (attempt payment)")
        print("4. Reactivate subscription - OPTION 3: Reset (fresh start)")
        print("5. Exit")
        print("=" * 70)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            find_inactive_subscriptions()
        
        elif choice in ['2', '3', '4']:
            subs = find_inactive_subscriptions()
            if subs:
                try:
                    idx = int(input("\nEnter subscription number: ")) - 1
                    if 0 <= idx < len(subs):
                        option_map = {'2': 'extend', '3': 'charge', '4': 'reset'}
                        reactivate_subscription(subs[idx].id, option_map[choice])
                    else:
                        print("❌ Invalid number!")
                except ValueError:
                    print("❌ Please enter a valid number!")
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")
