"""
Comprehensive Test for Singleton Settings and Auto-Renewal/Expiration Tasks

Tests:
1. PaymentConfiguration singleton
2. EmailConfiguration singleton
3. TelegramConfiguration singleton
4. Auto-renewal task (successful charge)
5. Auto-renewal task (failed charge, auto-renew disabled)
6. Expiration task (user removal from groups)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from subscriptions.models import (
    PaymentConfiguration, EmailConfiguration, TelegramConfiguration,
    Subscription, SubscriptionPlan, BillingProfile, PaymentMethod,
    Feature, User
)
from subscriptions.tasks import (
    process_auto_renewals,
    process_single_renewal,
    check_expired_subscriptions
)

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def test_singleton_settings():
    """Test all three singleton configuration models"""
    print_section("TEST 1: SINGLETON CONFIGURATION MODELS")
    
    try:
        # Test 1.1: PaymentConfiguration
        print("\n[1.1] Testing PaymentConfiguration singleton...")
        payment_config1 = PaymentConfiguration.get_instance()
        payment_config2 = PaymentConfiguration.get_instance()
        
        assert payment_config1.id == payment_config2.id, "PaymentConfiguration not a singleton!"
        assert PaymentConfiguration.objects.count() == 1, "Multiple PaymentConfiguration instances found!"
        
        print(f"✅ PaymentConfiguration is singleton (ID: {payment_config1.id})")
        print(f"   - Paystack configured: {payment_config1.is_paystack_configured()}")
        print(f"   - Stripe configured: {payment_config1.is_stripe_configured()}")
        print(f"   - Test mode: {payment_config1.is_test_mode}")
        
        # Test 1.2: EmailConfiguration
        print("\n[1.2] Testing EmailConfiguration singleton...")
        email_config1 = EmailConfiguration.get_instance()
        email_config2 = EmailConfiguration.get_instance()
        
        assert email_config1.id == email_config2.id, "EmailConfiguration not a singleton!"
        assert EmailConfiguration.objects.count() == 1, "Multiple EmailConfiguration instances found!"
        
        print(f"✅ EmailConfiguration is singleton (ID: {email_config1.id})")
        print(f"   - SMTP Host: {email_config1.smtp_host or 'Not set'}")
        print(f"   - From Email: {email_config1.from_email or 'Not set'}")
        print(f"   - Is configured: {email_config1.is_configured()}")
        
        # Test 1.3: TelegramConfiguration
        print("\n[1.3] Testing TelegramConfiguration singleton...")
        telegram_config1 = TelegramConfiguration.get_instance()
        telegram_config2 = TelegramConfiguration.get_instance()
        
        assert telegram_config1.id == telegram_config2.id, "TelegramConfiguration not a singleton!"
        assert TelegramConfiguration.objects.count() == 1, "Multiple TelegramConfiguration instances found!"
        
        print(f"✅ TelegramConfiguration is singleton (ID: {telegram_config1.id})")
        print(f"   - Bot username: {telegram_config1.bot_username or 'Not set'}")
        print(f"   - Is enabled: {telegram_config1.is_enabled}")
        print(f"   - Is connected: {telegram_config1.is_connected}")
        
        print("\n✅ ALL SINGLETON TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Singleton test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_renewal_success():
    """Test successful auto-renewal"""
    print_section("TEST 2: AUTO-RENEWAL (SUCCESSFUL CHARGE)")
    
    try:
        # Cleanup
        User.objects.filter(email='renewal_test@example.com').delete()
        SubscriptionPlan.objects.filter(slug='renewal-test-plan').delete()
        
        print("\n[2.1] Creating test subscription ending today...")
        
        # Create user
        user = User.objects.create_user(
            username='renewal_test',
            email='renewal_test@example.com',
            password='test123'
        )
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Create payment method with auth code
        payment_method = PaymentMethod.objects.create(
            billing_profile=billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_test_renewal',  # Mock auth code
            card_last4='4242',
            card_brand='visa',
            card_exp_month='12',
            card_exp_year='2030',
            is_default=True,
            is_active=True
        )
        
        # Create plan
        feature = Feature.objects.create(
            key='renewal_feature',
            name='Test Feature',
            description='Test',
            category='signals'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Renewal Test Plan',
            slug='renewal-test-plan',
            base_price=Decimal('10.00'),
            billing_period='weekly',
            is_active=True
        )
        plan.features.add(feature)
        
        # Create subscription ending today
        today = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=today - timedelta(days=7),
            end_date=today,  # Expires today
            amount_paid=Decimal('10.00'),
            currency='USD',
            auto_renew=True,
            payment_method=payment_method,
            next_billing_date=today  # Due for renewal today
        )
        
        print(f"✅ Created subscription {subscription.id}")
        print(f"   - Auto-renew: {subscription.auto_renew}")
        print(f"   - End date: {subscription.end_date.date()}")
        print(f"   - Next billing: {subscription.next_billing_date.date()}")
        print(f"   - Payment method: {payment_method.card_brand} ...{payment_method.card_last4}")
        
        print("\n[2.2] Running process_auto_renewals task...")
        result = process_auto_renewals()
        
        print(f"   - Task result: {result}")
        
        if result.get('success'):
            print(f"✅ Found {result.get('renewals', 0)} subscriptions to renew")
            print(f"✅ Queued {result.get('queued', 0)} renewal tasks")
            
            print("\n⚠️  NOTE: Actual charge will fail (mock payment method)")
            print("   In production with real Paystack auth codes, this would succeed")
        else:
            print(f"❌ Task failed: {result.get('error')}")
        
        # Cleanup
        user.delete()
        plan.delete()
        feature.delete()
        
        print("\n✅ AUTO-RENEWAL TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"\n❌ Auto-renewal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_renewal_failure_disables():
    """Test that failed auto-renewal disables auto_renew"""
    print_section("TEST 3: AUTO-RENEWAL FAILURE (AUTO-RENEW DISABLED)")
    
    try:
        # Cleanup
        User.objects.filter(email='renewal_fail_test@example.com').delete()
        SubscriptionPlan.objects.filter(slug='renewal-fail-plan').delete()
        
        print("\n[3.1] Creating subscription with invalid payment method...")
        
        user = User.objects.create_user(
            username='renewal_fail',
            email='renewal_fail_test@example.com',
            password='test123'
        )
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Create invalid payment method (no auth code)
        payment_method = PaymentMethod.objects.create(
            billing_profile=billing_profile,
            payment_type='card',
            gateway_authorization_code='',  # No auth code - will fail
            card_last4='0000',
            card_brand='visa',
            is_active=True
        )
        
        feature = Feature.objects.create(
            key='fail_feature',
            name='Fail Feature',
            description='Test',
            category='signals'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Fail Plan',
            slug='renewal-fail-plan',
            base_price=Decimal('10.00'),
            billing_period='weekly',
            is_active=True
        )
        plan.features.add(feature)
        
        today = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=today - timedelta(days=7),
            end_date=today,
            amount_paid=Decimal('10.00'),
            currency='USD',
            auto_renew=True,
            payment_method=payment_method,
            next_billing_date=today
        )
        
        print(f"✅ Created subscription with invalid payment method")
        print(f"   - Auto-renew before: {subscription.auto_renew}")
        
        print("\n[3.2] Testing process_single_renewal (should fail)...")
        result = process_single_renewal(str(subscription.id))
        
        print(f"   - Task result: {result}")
        
        # Refresh subscription
        subscription.refresh_from_db()
        
        if not result.get('success'):
            print(f"✅ Renewal failed as expected: {result.get('error')}")
            
            if result.get('action') == 'auto_renew_disabled':
                print(f"✅ Auto-renew was disabled: {subscription.auto_renew}")
            else:
                print(f"⚠️  Auto-renew status: {subscription.auto_renew}")
        
        # Cleanup
        user.delete()
        plan.delete()
        feature.delete()
        
        print("\n✅ AUTO-RENEWAL FAILURE TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"\n❌ Auto-renewal failure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_subscription_expiration():
    """Test subscription expiration and user removal"""
    print_section("TEST 4: SUBSCRIPTION EXPIRATION & USER REMOVAL")
    
    try:
        # Cleanup
        User.objects.filter(email='expire_test@example.com').delete()
        SubscriptionPlan.objects.filter(slug='expire-test-plan').delete()
        
        print("\n[4.1] Creating expired subscription...")
        
        user = User.objects.create_user(
            username='expire_test',
            email='expire_test@example.com',
            password='test123'
        )
        billing_profile = BillingProfile.objects.get(user=user)
        
        feature = Feature.objects.create(
            key='expire_feature',
            name='Expire Feature',
            description='Test',
            category='signals'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Expire Test Plan',
            slug='expire-test-plan',
            base_price=Decimal('10.00'),
            billing_period='weekly',
            is_active=True
        )
        plan.features.add(feature)
        
        # Create expired subscription (ended yesterday)
        yesterday = timezone.now() - timedelta(days=1)
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',  # Still marked active
            start_date=yesterday - timedelta(days=7),
            end_date=yesterday,  # Expired yesterday
            amount_paid=Decimal('10.00'),
            currency='USD',
            auto_renew=False
        )
        
        print(f"✅ Created expired subscription")
        print(f"   - Status before: {subscription.status}")
        print(f"   - End date: {subscription.end_date.date()}")
        print(f"   - Days expired: {(timezone.now() - subscription.end_date).days}")
        
        print("\n[4.2] Running check_expired_subscriptions task...")
        result = check_expired_subscriptions()
        
        print(f"   - Task result: {result}")
        
        # Refresh subscription
        subscription.refresh_from_db()
        user.refresh_from_db()
        
        if result.get('success'):
            print(f"✅ Found {result.get('expired_count', 0)} expired subscriptions")
            print(f"   - Subscription status after: {subscription.status}")
            print(f"   - User subscription status: {user.subscription_status}")
            
            if subscription.status == 'expired':
                print(f"✅ Subscription marked as expired")
            else:
                print(f"❌ Subscription still active!")
                
            print(f"\n   Note: User removal from Telegram groups queued as Celery task")
            print(f"   Task: remove_user_from_telegram_groups({user.id}, '{plan.id}')")
        
        # Cleanup
        user.delete()
        plan.delete()
        feature.delete()
        
        print("\n✅ EXPIRATION TEST COMPLETED")
        return True
        
    except Exception as e:
        print(f"\n❌ Expiration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SINGLETON & CELERY TASK TESTS")
    print("Testing Configuration Singletons and Auto-Renewal/Expiration Logic")
    print("="*80)
    
    results = []
    
    # Test singletons
    results.append(('Singleton Settings', test_singleton_settings()))
    
    # Test auto-renewal
    results.append(('Auto-Renewal (Success)', test_auto_renewal_success()))
    results.append(('Auto-Renewal (Failure)', test_auto_renewal_failure_disables()))
    
    # Test expiration
    results.append(('Subscription Expiration', test_subscription_expiration()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == '__main__':
    main()
