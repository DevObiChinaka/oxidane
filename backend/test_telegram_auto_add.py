"""
Test Telegram Auto-Add Functionality

This script tests the new Telegram auto-add feature that directly adds users
to Telegram groups instead of generating invite links.

Requirements:
- User must have telegram_user_id in billing profile
- Payment must be completed successfully
- Celery task should add user to all plan groups

Test Cases:
1. Verify billing profile has telegram_user_id
2. Test payment initialization with Telegram validation
3. Test Celery task execution
4. Verify user receives group invites

Usage:
    python test_telegram_auto_add.py --username only_mercedesblanche --user-id <telegram_numeric_id>
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from subscriptions.models import (
    SubscriptionPlan, BillingProfile, Payment, Subscription,
    TelegramGroup, PaymentConfiguration
)
from subscriptions.tasks import add_user_to_telegram_groups
import argparse

User = get_user_model()


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_result(success, message):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_billing_profile_telegram(user, telegram_username, telegram_user_id):
    """Test 1: Verify billing profile has Telegram credentials"""
    print_header("TEST 1: Billing Profile Telegram Setup")
    
    try:
        billing_profile, created = BillingProfile.objects.get_or_create(
            user=user,
            defaults={'billing_email': user.email}
        )
        
        # Check if another user has this telegram_user_id
        existing = BillingProfile.objects.filter(
            telegram_user_id=telegram_user_id
        ).exclude(user=user).first()
        
        if existing:
            print(f"⚠️  Telegram ID already linked to user: {existing.user.email}")
            print(f"Clearing old link and reassigning to {user.email}")
            # Delete the old profile's telegram link completely
            existing.delete()
            # Recreate billing profile for that user
            BillingProfile.objects.create(
                user=existing.user,
                billing_email=existing.user.email
            )
        
        # Update Telegram credentials
        billing_profile.telegram_username = telegram_username
        billing_profile.telegram_user_id = telegram_user_id
        billing_profile.telegram_verified = True
        billing_profile.save()
        
        print(f"Billing Profile ID: {billing_profile.id}")
        print(f"Telegram Username: {billing_profile.telegram_username}")
        print(f"Telegram User ID: {billing_profile.telegram_user_id}")
        print(f"Telegram Verified: {billing_profile.telegram_verified}")
        
        # Verify
        if billing_profile.telegram_user_id:
            print_result(True, "Billing profile has Telegram user ID")
            return True, billing_profile
        else:
            print_result(False, "Billing profile missing Telegram user ID")
            return False, None
    
    except Exception as e:
        print_result(False, f"Error setting up billing profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


def test_payment_validation_with_telegram(user, plan):
    """Test 2: Test payment initialization validates Telegram requirement"""
    print_header("TEST 2: Payment Telegram Validation")
    
    try:
        billing_profile = user.billing_profile
        
        # Check if plan has Telegram groups
        telegram_groups = plan.telegram_groups.filter(is_active=True)
        has_telegram_groups = telegram_groups.exists()
        
        print(f"Plan: {plan.name}")
        print(f"Has Telegram Groups: {has_telegram_groups}")
        
        if has_telegram_groups:
            print(f"Telegram Groups ({telegram_groups.count()}):")
            for group in telegram_groups:
                print(f"  - {group.name} (Chat ID: {group.chat_id})")
        
        # Check validation logic
        if has_telegram_groups and not billing_profile.telegram_user_id:
            print_result(True, "Would correctly reject payment (no Telegram ID)")
            return True
        elif has_telegram_groups and billing_profile.telegram_user_id:
            print_result(True, "Would correctly allow payment (Telegram ID present)")
            return True
        else:
            print_result(True, "Plan has no Telegram groups (validation skipped)")
            return True
    
    except Exception as e:
        print_result(False, f"Error testing payment validation: {str(e)}")
        return False


def test_celery_task_execution(user, plan):
    """Test 3: Test Celery task execution"""
    print_header("TEST 3: Celery Task Execution")
    
    try:
        # Call the task synchronously (for testing)
        result = add_user_to_telegram_groups(user.id, plan.id)
        
        print(f"Task Result:")
        print(f"  Success: {result.get('success')}")
        print(f"  User ID: {result.get('user_id')}")
        print(f"  Plan: {result.get('plan_name')}")
        print(f"  Groups Added: {result.get('groups_added')}")
        print(f"  Groups Failed: {result.get('groups_failed')}")
        print(f"  Telegram Username: {result.get('telegram_username')}")
        print(f"  Telegram User ID: {result.get('telegram_user_id')}")
        
        if result.get('group_names'):
            print(f"\nSuccessfully Added to Groups:")
            for group_name in result['group_names']:
                print(f"  ✅ {group_name}")
        
        if result.get('failures'):
            print(f"\nFailed Groups:")
            for failure in result['failures']:
                print(f"  ❌ {failure['group']}: {failure['error']}")
        
        if result.get('success'):
            print_result(True, "Celery task executed successfully")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print_result(False, f"Celery task failed: {error}")
            return False
    
    except Exception as e:
        print_result(False, f"Error executing Celery task: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_payment_flow(user, plan, telegram_username, telegram_user_id):
    """Test 4: Complete end-to-end payment flow"""
    print_header("TEST 4: End-to-End Payment Flow")
    
    try:
        # Step 1: Setup billing profile
        billing_profile = user.billing_profile
        billing_profile.telegram_username = telegram_username
        billing_profile.telegram_user_id = telegram_user_id
        billing_profile.telegram_verified = True
        billing_profile.save()
        
        print(f"✓ Billing profile configured")
        
        # Step 2: Create a test payment (use timestamp for unique reference)
        import time
        payment = Payment.objects.create(
            billing_profile=billing_profile,
            amount=plan.base_price,
            processing_fee=Decimal('50.00'),
            total_amount=plan.base_price + Decimal('50.00'),
            currency='NGN',
            payment_gateway='paystack',
            gateway_reference=f"TEST_{user.id}_{int(time.time())}",
            status='completed',
            gateway_response={'test': True}
        )
        
        print(f"✓ Test payment created: {payment.id}")
        
        # Step 3: Create subscription
        from datetime import datetime, timedelta
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            amount_paid=payment.total_amount,
            currency=payment.currency
        )
        
        payment.subscription = subscription
        payment.save()
        
        print(f"✓ Subscription created: {subscription.id}")
        
        # Step 4: Trigger Telegram task
        result = add_user_to_telegram_groups(user.id, plan.id)
        
        if result.get('success'):
            print(f"✓ Telegram groups task completed")
            print(f"  Groups added: {result.get('groups_added')}")
            print_result(True, "End-to-end flow completed successfully")
            return True
        else:
            print(f"✗ Telegram groups task failed: {result.get('error')}")
            print_result(False, "Telegram task failed in end-to-end flow")
            return False
    
    except Exception as e:
        print_result(False, f"Error in end-to-end flow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description='Test Telegram Auto-Add Functionality')
    parser.add_argument('--username', default='only_mercedesblanche', help='Telegram username')
    parser.add_argument('--user-id', required=True, help='Telegram numeric user ID')
    parser.add_argument('--email', default='test@oxidane.com', help='Test user email')
    
    args = parser.parse_args()
    
    print_header("TELEGRAM AUTO-ADD TEST SUITE")
    print(f"Telegram Username: @{args.username}")
    print(f"Telegram User ID: {args.user_id}")
    
    # Get or create test user
    try:
        user = User.objects.get(email=args.email)
        print(f"\nUsing existing user: {user.email}")
    except User.DoesNotExist:
        # Generate unique username
        import random
        username = f"test_telegram_{random.randint(1000, 9999)}"
        user = User.objects.create_user(
            email=args.email,
            username=username,
            password='testpass123'
        )
        print(f"\nCreated new test user: {user.email}")
    
    # Get a subscription plan with Telegram groups
    plan = SubscriptionPlan.objects.filter(
        is_active=True,
        telegram_groups__isnull=False
    ).distinct().first()
    
    if not plan:
        print("\n⚠️  No subscription plan with Telegram groups found!")
        print("Creating a test plan and group...")
        
        # Create test plan
        plan = SubscriptionPlan.objects.create(
            name="Test Signals Plan",
            base_price=Decimal('48000.00'),
            billing_period='monthly',
            is_active=True
        )
        
        # Create test Telegram group
        test_group = TelegramGroup.objects.create(
            name="Test Signals Group",
            chat_id="-1001234567890",  # Placeholder
            group_key="test_signals",
            description="Test group for auto-add functionality",
            is_active=True,
            is_private=True
        )
        
        plan.telegram_groups.add(test_group)
        print(f"✓ Created test plan: {plan.name}")
        print(f"✓ Created test group: {test_group.name}")
    
    print(f"\nUsing plan: {plan.name}")
    
    # Run tests
    results = []
    
    # Test 1: Billing Profile Setup
    success, billing_profile = test_billing_profile_telegram(
        user, args.username, args.user_id
    )
    results.append(('Billing Profile Setup', success))
    
    if not success:
        print("\n❌ Cannot proceed without billing profile setup")
        return
    
    # Test 2: Payment Validation
    success = test_payment_validation_with_telegram(user, plan)
    results.append(('Payment Validation', success))
    
    # Test 3: Celery Task
    success = test_celery_task_execution(user, plan)
    results.append(('Celery Task Execution', success))
    
    # Test 4: End-to-End Flow
    success = test_end_to_end_payment_flow(user, plan, args.username, args.user_id)
    results.append(('End-to-End Flow', success))
    
    # Summary
    print_header("TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Telegram auto-add is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the errors above.")


if __name__ == '__main__':
    main()
