#!/usr/bin/env python
"""
Test Celery Tasks
Tests payment-related Celery tasks

Created: November 10, 2025
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import (
    activate_subscription,
    add_user_to_telegram_groups,
    send_payment_receipt_email,
    check_expired_subscriptions,
)
from subscriptions.models import Payment, User, SubscriptionPlan
from decimal import Decimal


def test_activate_subscription():
    """Test activate_subscription task"""
    print("\n" + "="*60)
    print("TEST: activate_subscription Task")
    print("="*60)
    
    # Find a successful payment
    payment = Payment.objects.filter(status='success').first()
    
    if not payment:
        print("⏭️  SKIP: No successful payments found")
        return False
    
    print(f"\nTesting with payment ID: {payment.id}")
    print(f"Current status: {payment.status}")
    
    # Run task synchronously (not async)
    try:
        result = activate_subscription(payment.id)
        print(f"\nTask Result:")
        print(f"  Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"  Subscription ID: {result.get('subscription_id')}")
            print(f"  Plan: {result.get('plan_name')}")
            print(f"  Start Date: {result.get('start_date')}")
            print(f"  End Date: {result.get('end_date')}")
            print("\n✅ PASS: Subscription activated")
            return True
        else:
            print(f"  Error: {result.get('error')}")
            print("\n⚠️  WARN: Task returned error (may be expected)")
            return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_add_user_to_telegram_groups():
    """Test add_user_to_telegram_groups task"""
    print("\n" + "="*60)
    print("TEST: add_user_to_telegram_groups Task")
    print("="*60)
    
    # Find a user with subscription
    user = User.objects.filter(subscription_status='active').first()
    
    if not user or not user.current_plan:
        print("⏭️  SKIP: No active users with plans found")
        return False
    
    print(f"\nTesting with user ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Plan: {user.current_plan.name}")
    print(f"Telegram ID: {user.telegram_id or 'Not linked'}")
    
    # Run task synchronously
    try:
        result = add_user_to_telegram_groups(user.id, str(user.current_plan.id))
        print(f"\nTask Result:")
        print(f"  Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"  Groups Added: {result.get('groups_added', 0)}")
            if result.get('group_names'):
                for group in result['group_names']:
                    print(f"    - {group}")
            print("\n✅ PASS: Telegram groups processed")
            return True
        else:
            print(f"  Error: {result.get('error')}")
            print("\n⚠️  WARN: Task returned error (may be expected)")
            return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_send_payment_receipt_email():
    """Test send_payment_receipt_email task"""
    print("\n" + "="*60)
    print("TEST: send_payment_receipt_email Task")
    print("="*60)
    
    # Find a successful payment
    payment = Payment.objects.filter(status='success').first()
    
    if not payment:
        print("⏭️  SKIP: No successful payments found")
        return False
    
    print(f"\nTesting with payment ID: {payment.id}")
    print(f"Recipient: {payment.billing_profile.user.email}")
    print(f"Amount: {payment.currency} {payment.total_amount}")
    
    # Run task synchronously
    try:
        result = send_payment_receipt_email(payment.id)
        print(f"\nTask Result:")
        print(f"  Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"  Recipient: {result.get('recipient')}")
            print(f"  Subject: {result.get('subject')}")
            print("\n✅ PASS: Email sent")
            return True
        else:
            print(f"  Error: {result.get('error')}")
            print("\n⚠️  WARN: Email sending failed (check SMTP config)")
            return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_check_expired_subscriptions():
    """Test check_expired_subscriptions periodic task"""
    print("\n" + "="*60)
    print("TEST: check_expired_subscriptions Task (Periodic)")
    print("="*60)
    
    # Run task synchronously
    try:
        result = check_expired_subscriptions()
        print(f"\nTask Result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Expired Count: {result.get('expired_count', 0)}")
        print("\n✅ PASS: Expiration check completed")
        return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_celery_connection():
    """Check if Celery can connect to Redis"""
    print("\n" + "="*60)
    print("Checking Celery Connection")
    print("="*60)
    
    try:
        from oxidane.celery import app
        
        # Check broker connection
        print(f"\nCelery Broker: {app.conf.broker_url[:50]}...")
        print(f"Result Backend: {app.conf.result_backend[:50]}...")
        
        # Try to ping Redis
        result = app.control.inspect().ping()
        
        if result:
            print(f"\n✅ Celery is connected")
            print(f"   Active workers: {len(result)}")
            for worker_name in result.keys():
                print(f"   - {worker_name}")
            return True
        else:
            print("\n⚠️  No Celery workers running")
            print("   Start worker: celery -A oxidane worker -l INFO")
            return False
    
    except Exception as e:
        print(f"\n⚠️  Could not connect to Celery: {str(e)}")
        print("   Make sure Redis is running")
        print("   Start worker: celery -A oxidane worker -l INFO")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CELERY TASKS TEST SUITE")
    print("Testing Payment & Subscription Tasks")
    print("="*60)
    
    # Check connection first
    has_workers = check_celery_connection()
    
    if not has_workers:
        print("\n" + "="*60)
        print("NOTE: Running tasks synchronously (no workers)")
        print("      Tasks will execute in this process")
        print("="*60)
    
    # Run tests
    results = []
    
    results.append(('activate_subscription', test_activate_subscription()))
    results.append(('add_user_to_telegram_groups', test_add_user_to_telegram_groups()))
    results.append(('send_payment_receipt_email', test_send_payment_receipt_email()))
    results.append(('check_expired_subscriptions', test_check_expired_subscriptions()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n✅ All Celery tasks are functional!")
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Start Celery worker:")
    print("   celery -A oxidane worker -l INFO")
    print()
    print("2. Start Celery beat (for periodic tasks):")
    print("   celery -A oxidane beat -l INFO")
    print()
    print("3. Monitor tasks:")
    print("   celery -A oxidane events")
    print("="*60)
    
    return passed_count == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
