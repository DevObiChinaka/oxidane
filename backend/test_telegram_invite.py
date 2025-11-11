"""
Test Telegram group invitation for @only_mercedesblanche
This script tests the add_user_to_telegram_groups task
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import SubscriptionPlan, TelegramGroup, TelegramConfiguration, BillingProfile, Subscription
from subscriptions.tasks import add_user_to_telegram_groups
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_telegram_invite():
    """
    Test Telegram group invitation for @only_mercedesblanche
    """
    print("=" * 70)
    print("TELEGRAM INVITE TEST FOR @only_mercedesblanche")
    print("=" * 70)
    
    # Step 1: Check if user exists or create
    print("\n[1] Checking user @only_mercedesblanche...")
    username = "only_mercedesblanche"
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ User found: {user.email}")
    except User.DoesNotExist:
        print(f"❌ User not found. Creating user...")
        user = User.objects.create_user(
            username=username,
            email=f"{username}@telegram.user",
            telegram_username=f"@{username}",
            first_name="Mercedes",
            last_name="Blanche"
        )
        print(f"✅ User created: {user.email}")
    
    # Display user info
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Username: {user.username}")
    print(f"   - Telegram Username: {user.telegram_username or 'Not set'}")
    print(f"   - Telegram ID: {user.telegram_id or 'Not set'}")
    
    # Step 2: Update Telegram info if missing
    if not user.telegram_username:
        user.telegram_username = f"@{username}"
        user.save()
        print(f"   ℹ️  Updated Telegram username to: @{username}")
    
    # Step 3: Check Telegram Configuration
    print("\n[2] Checking Telegram Configuration...")
    try:
        telegram_config = TelegramConfiguration.get_instance()
        if telegram_config.bot_token:
            print(f"✅ Telegram bot configured")
            print(f"   - Bot Token: {telegram_config.bot_token[:10]}***")
        else:
            print("❌ Telegram bot token not configured")
            print("   ⚠️  You need to set up the bot token in admin")
    except Exception as e:
        print(f"❌ Telegram configuration error: {str(e)}")
    
    # Step 4: Check available subscription plans
    print("\n[3] Checking subscription plans...")
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    if not plans.exists():
        print("❌ No active subscription plans found")
        return
    
    print(f"✅ Found {plans.count()} active plans:")
    for plan in plans:
        telegram_groups = plan.telegram_groups.filter(is_active=True)
        print(f"   - {plan.name} (${plan.base_price})")
        print(f"     Telegram groups: {telegram_groups.count()}")
        for group in telegram_groups:
            print(f"       • {group.name} (Chat ID: {group.chat_id})")
    
    # Step 5: Select a plan (use Monthly Signals if exists, otherwise first plan)
    print("\n[4] Selecting plan for test...")
    try:
        test_plan = SubscriptionPlan.objects.get(name="Monthly Signals", is_active=True)
        print(f"✅ Using Monthly Signals plan")
    except SubscriptionPlan.DoesNotExist:
        test_plan = plans.first()
        print(f"✅ Using {test_plan.name} plan")
    
    # Check if plan has Telegram groups
    telegram_groups = test_plan.telegram_groups.filter(is_active=True)
    if not telegram_groups.exists():
        print(f"❌ Plan '{test_plan.name}' has no Telegram groups configured")
        print("   ⚠️  You need to add Telegram groups to this plan in admin")
        return
    
    print(f"   - Plan: {test_plan.name}")
    print(f"   - Price: ${test_plan.base_price}")
    print(f"   - Telegram groups: {telegram_groups.count()}")
    
    # Step 6: Create or get billing profile
    print("\n[5] Checking billing profile...")
    billing_profile, created = BillingProfile.objects.get_or_create(user=user)
    if created:
        print(f"✅ Created billing profile")
    else:
        print(f"✅ Billing profile exists")
    
    # Step 7: Create a test subscription (if not exists)
    print("\n[6] Creating test subscription...")
    subscription, created = Subscription.objects.get_or_create(
        billing_profile=billing_profile,
        plan=test_plan,
        status='active',
        defaults={
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'amount_paid': test_plan.base_price,
            'currency': 'USD'
        }
    )
    
    if created:
        print(f"✅ Created test subscription: {subscription.id}")
    else:
        print(f"✅ Subscription exists: {subscription.id}")
    
    print(f"   - Status: {subscription.status}")
    print(f"   - Start: {subscription.start_date}")
    print(f"   - End: {subscription.end_date}")
    
    # Step 8: Test the Telegram task
    print("\n[7] Testing Telegram group invitation task...")
    print(f"   Calling add_user_to_telegram_groups({user.id}, '{test_plan.id}')")
    
    try:
        # Run the task synchronously (not via Celery)
        result = add_user_to_telegram_groups(user.id, str(test_plan.id))
        
        print("\n[8] Task execution result:")
        print("=" * 70)
        if result:
            print("✅ TASK EXECUTED SUCCESSFULLY")
            print(f"\nResult: {result}")
        else:
            print("⚠️  Task completed but returned no result")
            print("   This may mean:")
            print("   - User has no Telegram ID set")
            print("   - No Telegram groups configured for this plan")
            print("   - Bot token not configured")
        
    except Exception as e:
        print(f"\n❌ TASK FAILED")
        print(f"Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
    
    # Step 9: Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"User: @{username}")
    print(f"Plan: {test_plan.name}")
    print(f"Telegram Groups: {telegram_groups.count()}")
    print(f"Telegram ID Set: {'Yes' if user.telegram_id else 'No (REQUIRED for invites)'}")
    print(f"Telegram Username: {user.telegram_username or 'Not set'}")
    
    if not user.telegram_id:
        print("\n⚠️  IMPORTANT: User needs to set Telegram ID")
        print("   The user must verify their Telegram account first")
        print("   Invite links can only be sent to verified Telegram users")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_telegram_invite()
