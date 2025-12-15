#!/usr/bin/env python
"""
Test Subscription Expiration & Telegram Group Removal
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
from subscriptions.tasks import check_expired_subscriptions, remove_user_from_telegram_groups

print("=" * 70)
print("SUBSCRIPTION EXPIRATION TEST UTILITY")
print("=" * 70)

def list_active_subscriptions():
    """List active subscriptions that can be expired for testing"""
    print("\n📋 Active subscriptions:\n")
    
    subs = Subscription.objects.filter(
        status='active'
    ).select_related('billing_profile__user', 'plan')
    
    if not subs.exists():
        print("❌ No active subscriptions found!")
        return []
    
    for i, sub in enumerate(subs, 1):
        user = sub.billing_profile.user
        days_left = (sub.end_date - timezone.now()).days if sub.end_date else None
        print(f"{i}. User: {user.email}")
        print(f"   Plan: {sub.plan.name}")
        print(f"   End date: {sub.end_date}")
        print(f"   Days left: {days_left}")
        print(f"   Auto-renew: {'✅' if sub.auto_renew else '❌'}")
        print(f"   Subscription ID: {sub.id}")
        print()
    
    return list(subs)

def expire_subscription(subscription_id):
    """Set a subscription's end_date to yesterday to trigger expiration"""
    try:
        sub = Subscription.objects.select_related('billing_profile__user', 'plan').get(id=subscription_id)
        yesterday = timezone.now() - timedelta(days=1)
        
        print(f"\n🔧 Expiring subscription for: {sub.billing_profile.user.email}")
        print(f"   Old end_date: {sub.end_date}")
        
        # Set end date to yesterday
        sub.end_date = yesterday
        sub.save(update_fields=['end_date'])
        
        print(f"   ✅ New end_date: {sub.end_date}")
        print(f"\n💡 Now run: check_expired_subscriptions()")
        print(f"💡 Or manually: remove_user_from_telegram_groups('{sub.billing_profile.user.id}', '{sub.plan.id}')")
        
        return True
    except Subscription.DoesNotExist:
        print(f"❌ Subscription {subscription_id} not found!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def trigger_expiration_check():
    """Run the check_expired_subscriptions task"""
    print("\n🚀 Running check_expired_subscriptions task...\n")
    
    try:
        result = check_expired_subscriptions()
        print("\n📊 Result:")
        print(result)
        return result
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def manually_remove_from_telegram(user_id, plan_id):
    """Manually trigger Telegram group removal"""
    print(f"\n🚀 Removing user {user_id} from Telegram groups for plan {plan_id}\n")
    
    try:
        from subscriptions.tasks import remove_user_from_telegram_groups
        # Queue the task
        result = remove_user_from_telegram_groups.delay(user_id, plan_id)
        print(f"✅ Task queued: {result.id}")
        print(f"💡 Check Celery worker logs to see the result")
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
        print("1. List active subscriptions")
        print("2. Set subscription end_date to YESTERDAY (expire it)")
        print("3. Trigger expiration check (check_expired_subscriptions)")
        print("4. Manually remove user from Telegram group")
        print("5. Exit")
        print("=" * 70)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            list_active_subscriptions()
        
        elif choice == '2':
            subs = list_active_subscriptions()
            if subs:
                try:
                    idx = int(input("\nEnter subscription number: ")) - 1
                    if 0 <= idx < len(subs):
                        expire_subscription(subs[idx].id)
                    else:
                        print("❌ Invalid number!")
                except ValueError:
                    print("❌ Please enter a valid number!")
        
        elif choice == '3':
            confirm = input("\n⚠️  This will expire ALL subscriptions past end_date. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                trigger_expiration_check()
        
        elif choice == '4':
            user_id = input("\nEnter user ID: ").strip()
            plan_id = input("Enter plan ID: ").strip()
            if user_id and plan_id:
                manually_remove_from_telegram(user_id, plan_id)
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")
