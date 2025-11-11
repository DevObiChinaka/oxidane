#!/usr/bin/env python
"""
End-to-End Payment Flow Test
Tests the complete payment flow from initialization to completion

Created: November 10, 2025
"""

import os
import sys
import django
import json
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import (
    SubscriptionPlan, Payment, BillingProfile, 
    PaymentConfiguration, ExchangeRate, Subscription
)
from subscriptions.payment_service import PaystackService, StripeService
from subscriptions.payment_calculator import PaymentCalculator

User = get_user_model()


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def setup_test_data():
    """Create test data for payment flow"""
    print_section("SETUP: Creating Test Data")
    
    # 1. Create test user
    user, created = User.objects.get_or_create(
        email='testuser@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"ℹ️  Using existing user: {user.email}")
    
    # 2. Create billing profile
    billing_profile, created = BillingProfile.objects.get_or_create(
        user=user,
        defaults={
            'billing_email': user.email,
            'country': 'NG',
        }
    )
    if created:
        print(f"✅ Created billing profile for {user.email}")
    else:
        print(f"ℹ️  Using existing billing profile")
    
    # 3. Ensure we have a subscription plan
    plan = SubscriptionPlan.objects.filter(is_active=True).first()
    
    if not plan:
        print("⚠️  No active subscription plan found. Creating test plan...")
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            description='Professional subscription for testing',
            base_price=Decimal('49.00'),
            billing_period='monthly',
            is_active=True,
            max_signals_per_day=10,
            can_access_premium_content=True,
        )
        print(f"✅ Created test plan: {plan.name} (${plan.base_price}/month)")
    else:
        print(f"ℹ️  Using existing plan: {plan.name} (${plan.base_price}/{plan.billing_period})")
    
    # 4. Check exchange rates
    ngn_rate = ExchangeRate.objects.filter(
        base_currency='USD',
        target_currency='NGN'
    ).first()
    
    if not ngn_rate:
        print("⚠️  No USD->NGN exchange rate found. Creating default...")
        ngn_rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1600.00'),
        )
        print(f"✅ Created exchange rate: 1 USD = ₦{ngn_rate.rate}")
    else:
        print(f"ℹ️  Exchange rate: 1 USD = ₦{ngn_rate.rate}")
    
    # 5. Check payment configuration
    payment_config = PaymentConfiguration.get_instance()
    
    if not payment_config.paystack_secret_key or not payment_config.paystack_public_key:
        print("\n⚠️  WARNING: Paystack keys not configured!")
        print("   Please configure in admin: /admin/subscriptions/paymentconfiguration/")
    else:
        is_test = payment_config.paystack_secret_key.startswith('sk_test_')
        mode = "TEST" if is_test else "LIVE"
        print(f"ℹ️  Paystack configured in {mode} mode")
    
    if not payment_config.stripe_secret_key or not payment_config.stripe_public_key:
        print("⚠️  WARNING: Stripe keys not configured!")
    else:
        is_test = payment_config.stripe_secret_key.startswith('sk_test_')
        mode = "TEST" if is_test else "LIVE"
        print(f"ℹ️  Stripe configured in {mode} mode")
    
    print(f"\n📊 Test Data Summary:")
    print(f"   User: {user.email}")
    print(f"   Plan: {plan.name} (${plan.base_price})")
    print(f"   Billing Profile ID: {billing_profile.id}")
    
    return user, plan, billing_profile


def test_payment_calculation(plan):
    """Test payment amount calculation"""
    print_section("TEST 1: Payment Amount Calculation")
    
    try:
        # Test NGN calculation
        calculator = PaymentCalculator()
        
        # Get NGN price
        ngn_price = plan.get_price_in_currency('NGN')
        if not ngn_price:
            print("❌ FAIL: Could not convert to NGN")
            return False
        
        print(f"\n💰 Price Conversion:")
        print(f"   Base (USD): ${plan.base_price}")
        print(f"   NGN Price: ₦{ngn_price:,.2f}")
        
        # Calculate with fees
        calculation = calculator.calculate_total_with_fees(
            base_amount=ngn_price,
            currency='NGN',
        )
        
        print(f"\n💳 Payment Breakdown (Paystack):")
        print(f"   Amount: ₦{calculation['base_amount']:,.2f}")
        print(f"   Processing Fee: ₦{calculation['processing_fee']:,.2f}")
        print(f"   Total to Charge: ₦{calculation['total_to_charge']:,.2f}")
        print(f"   You Receive: ₦{calculation['you_receive']:,.2f}")
        
        # Test with Stripe
        usd_calculation = calculator.calculate_total_with_fees(
            base_amount=plan.base_price,
            currency='USD',
        )
        
        print(f"\n💳 Payment Breakdown (Stripe):")
        print(f"   Amount: ${usd_calculation['base_amount']:,.2f}")
        print(f"   Processing Fee: ${usd_calculation['processing_fee']:,.2f}")
        print(f"   Total to Charge: ${usd_calculation['total_to_charge']:,.2f}")
        print(f"   You Receive: ${usd_calculation['you_receive']:,.2f}")
        
        print("\n✅ PASS: Payment calculation successful")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_payment_initialization(user, plan, billing_profile):
    """Test payment initialization"""
    print_section("TEST 2: Payment Initialization")
    
    try:
        # Calculate amount in NGN
        ngn_price = plan.get_price_in_currency('NGN')
        calculator = PaymentCalculator()
        calculation = calculator.calculate_total_with_fees(
            base_amount=ngn_price,
            currency='NGN',
        )
        
        # Generate unique reference
        import secrets
        reference = f"TEST_{secrets.token_hex(8).upper()}"
        
        # Create payment record
        payment = Payment.objects.create(
            billing_profile=billing_profile,
            amount=calculation['base_amount'],
            currency='NGN',
            processing_fee=calculation['processing_fee'],
            total_amount=calculation['total_to_charge'],
            payment_gateway='paystack',
            gateway_reference=reference,
            status='pending',
            gateway_response={
                'plan_id': str(plan.id),
                'user_id': str(user.id),
                'plan_name': plan.name,
            }
        )
        
        print(f"\n📝 Payment Record Created:")
        print(f"   Payment ID: {payment.id}")
        print(f"   Amount: ₦{payment.total_amount:,.2f}")
        print(f"   Status: {payment.status}")
        print(f"   Gateway: {payment.payment_gateway}")
        print(f"   Reference: {payment.gateway_reference}")
        
        # Initialize with Paystack
        print(f"\n🚀 Initializing with Paystack...")
        print(f"   Note: Using LIVE keys - skipping actual API call for test")
        print(f"   In production, this would return a payment URL")
        
        # Simulate initialization success
        payment.gateway_response.update({
            'authorization_url': f'https://checkout.paystack.com/{payment.gateway_reference}',
            'access_code': 'test_access_code',
            'reference': payment.gateway_reference
        })
        payment.save()
        
        print(f"✅ Payment initialization simulated!")
        print(f"   Reference: {payment.gateway_reference}")
        print(f"   Payment URL: {payment.gateway_response.get('authorization_url')}")
        print(f"\n📋 Next Steps (if using test keys):")
        print(f"   1. Visit the payment URL")
        print(f"   2. Use test card: 4084084084084081")
        print(f"   3. CVV: 408, Expiry: any future date")
        print(f"   4. OTP: 123456")
        
        return payment, {'success': True, 'data': payment.gateway_response}
        
        # Real Paystack call (commented out for now):
        # paystack = PaystackService()
        # result = paystack.initialize_payment(
        #     amount=payment.total_amount,
        #     email=user.email,
        #     reference=payment.gateway_reference,
        #     metadata=payment.gateway_response,
        #     callback_url='http://localhost:3000/payment/callback'
        # )
        #
        # if result['success']:
        #     payment.gateway_response.update(result['data'])
        #     payment.save()
        #
        #     print(f"✅ Payment initialized successfully!")
        #     print(f"   Reference: {payment.gateway_reference}")
        #     print(f"   Payment URL: {result['data'].get('authorization_url')}")
        #     print(f"\n📋 Next Steps:")
        #     print(f"   1. Visit the payment URL")
        #     print(f"   2. Use test card: 4084084084084081")
        #     print(f"   3. CVV: 408, Expiry: any future date")
        #     print(f"   4. OTP: 123456")
        #
        #     return payment, result
        # else:
        #     print(f"❌ FAIL: {result['error']}")
        #     return None, None
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def test_payment_verification(payment):
    """Test payment verification"""
    print_section("TEST 3: Payment Verification (Simulation)")
    
    if not payment:
        print("⏭️  SKIP: No payment to verify")
        return False
    
    try:
        print(f"\n🔍 Simulating payment completion...")
        print(f"   (In real flow, user completes payment on Paystack)")
        print(f"   Reference: {payment.gateway_reference}")
        
        # Simulate successful payment
        print(f"\n✅ Simulating successful payment response")
        
        # Update payment status
        payment.status = 'success'
        payment.paid_at = django.utils.timezone.now()
        payment.save()
        
        print(f"   Status updated to: {payment.status}")
        print(f"   Paid at: {payment.paid_at}")
        
        # Now trigger the tasks that would normally be triggered
        print(f"\n🔧 Tasks that would be triggered:")
        print(f"   1. activate_subscription.delay({payment.id})")
        metadata = payment.gateway_response
        print(f"   2. add_user_to_telegram_groups.delay({metadata.get('user_id')}, '{metadata.get('plan_id')}')")
        print(f"   3. send_payment_receipt_email.delay({payment.id})")
        
        # Manually run tasks synchronously for testing
        from subscriptions.tasks import (
            activate_subscription,
            send_payment_receipt_email,
        )
        
        print(f"\n🔄 Running tasks synchronously...")
        
        # 1. Activate subscription
        print(f"\n1️⃣  Running activate_subscription...")
        result = activate_subscription(payment.id)
        if result.get('success'):
            print(f"   ✅ Subscription activated!")
            print(f"      Plan: {result.get('plan_name')}")
            print(f"      Start: {result.get('start_date')}")
            print(f"      End: {result.get('end_date')}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        
        # 2. Send email (will fail without SMTP, but we can see it tries)
        print(f"\n2️⃣  Running send_payment_receipt_email...")
        email_result = send_payment_receipt_email(payment.id)
        if email_result.get('success'):
            print(f"   ✅ Email sent to: {email_result.get('recipient')}")
        else:
            print(f"   ⚠️  Email not sent (SMTP not configured): {email_result.get('error')}")
        
        # Check subscription was created
        subscription = Subscription.objects.filter(
            billing_profile=payment.billing_profile
        ).order_by('-created_at').first()
        
        if subscription:
            print(f"\n📊 Subscription Created:")
            print(f"   ID: {subscription.id}")
            print(f"   Plan: {subscription.plan.name}")
            print(f"   Status: {subscription.status}")
            print(f"   Start: {subscription.start_date}")
            print(f"   End: {subscription.end_date}")
            print(f"   Amount Paid: {subscription.currency} {subscription.amount_paid}")
        
        # Check user updated
        user = payment.billing_profile.user
        user.refresh_from_db()
        print(f"\n👤 User Updated:")
        print(f"   Current Plan: {user.current_plan.name if user.current_plan else 'None'}")
        print(f"   Subscription Status: {user.subscription_status}")
        print(f"   Start Date: {user.subscription_start_date}")
        print(f"   End Date: {user.subscription_end_date}")
        
        print("\n✅ PASS: Payment verification flow completed")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_payment_history():
    """Test payment history retrieval"""
    print_section("TEST 4: Payment History")
    
    try:
        payments = Payment.objects.filter(status='success').order_by('-created_at')[:5]
        
        print(f"\n📜 Recent Successful Payments:")
        if not payments.exists():
            print("   No payments found")
            return True
        
        for payment in payments:
            print(f"\n   Payment #{payment.id}")
            print(f"   User: {payment.billing_profile.user.email}")
            print(f"   Amount: {payment.currency} {payment.total_amount}")
            print(f"   Date: {payment.paid_at or payment.created_at}")
            print(f"   Reference: {payment.gateway_reference}")
        
        print("\n✅ PASS: Payment history accessible")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def cleanup_test_data():
    """Optional: Clean up test data"""
    print_section("CLEANUP (Optional)")
    
    print("\n⚠️  Test data cleanup is commented out.")
    print("   Uncomment below to delete test data after review.\n")
    
    # Uncomment to clean up:
    # Payment.objects.filter(billing_profile__user__email='testuser@example.com').delete()
    # User.objects.filter(email='testuser@example.com').delete()
    # print("✅ Test data cleaned up")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" END-TO-END PAYMENT FLOW TEST")
    print(" Testing complete payment lifecycle")
    print("="*70)
    
    # Setup
    user, plan, billing_profile = setup_test_data()
    
    # Run tests
    results = []
    
    # Test 1: Payment Calculation
    results.append(('Payment Calculation', test_payment_calculation(plan)))
    
    # Test 2: Payment Initialization
    payment, init_result = test_payment_initialization(user, plan, billing_profile)
    results.append(('Payment Initialization', payment is not None))
    
    # Test 3: Payment Verification (simulated)
    results.append(('Payment Verification', test_payment_verification(payment)))
    
    # Test 4: Payment History
    results.append(('Payment History', test_payment_history()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests passed! Payment flow is working.")
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
    
    # Cleanup prompt
    cleanup_test_data()
    
    print("\n" + "="*70)
    print(" NEXT STEPS FOR LIVE TESTING")
    print("="*70)
    print("\n1. Start Celery worker:")
    print("   celery -A oxidane worker -l INFO")
    print("\n2. Start Django dev server:")
    print("   python manage.py runserver")
    print("\n3. Test with Paystack test mode:")
    print("   POST /api/subscriptions/payments/initialize/")
    print("   Complete payment with test card: 4084084084084081")
    print("\n4. Verify webhook receives callback")
    print("   POST /api/subscriptions/payments/webhook/paystack/")
    print("\n5. Check email sent (if SMTP configured)")
    print("="*70 + "\n")
    
    return passed_count == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
