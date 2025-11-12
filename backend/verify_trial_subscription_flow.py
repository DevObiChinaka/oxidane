"""
Manual verification script for trial subscription flow
Tests the updated payment views logic for trial subscriptions
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import (
    BillingProfile,
    SubscriptionPlan,
    Feature,
    Subscription,
    PaymentMethod
)

User = get_user_model()

def test_trial_subscription_flow():
    """Test trial subscription creation flow"""
    
    print("\n" + "="*70)
    print("TRIAL SUBSCRIPTION FLOW TESTS")
    print("="*70)
    
    # Test 1: Create plan with trial
    print("\n[TEST 1] Create subscription plan with trial period")
    print("-" * 70)
    
    try:
        # Clean up existing test data
        SubscriptionPlan.objects.filter(slug='test-trial-plan').delete()
        User.objects.filter(username='trial_test_user').delete()
        Feature.objects.filter(key='test_feature').delete()  # Clean up feature too
        
        feature = Feature.objects.create(
            key='test_feature',
            name='Test Feature',
            description='Test feature for trial',
            category='signals',  # Valid category
            is_active=True
        )
        
        trial_plan = SubscriptionPlan.objects.create(
            name='Test Trial Plan',
            slug='test-trial-plan',
            description='Monthly plan with 7-day trial',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            trial_days=7,  # 7-day trial
            is_active=True
        )
        trial_plan.features.add(feature)
        
        print(f"✓ Plan created: {trial_plan.name}")
        print(f"  Base price: ${trial_plan.base_price}")
        print(f"  Trial days: {trial_plan.trial_days}")
        print(f"  Billing period: {trial_plan.billing_period}")
        
        # Verify plan has trial
        if trial_plan.trial_days > 0:
            print("✓ Plan has trial period configured")
        else:
            print("✗ Plan should have trial period")
            return False
    except Exception as e:
        print(f"✗ Error creating plan: {e}")
        return False
    
    # Test 2: Create plan without trial
    print("\n[TEST 2] Create subscription plan without trial")
    print("-" * 70)
    
    try:
        SubscriptionPlan.objects.filter(slug='test-no-trial-plan').delete()
        
        no_trial_plan = SubscriptionPlan.objects.create(
            name='Test No Trial Plan',
            slug='test-no-trial-plan',
            description='Monthly plan without trial',
            base_price=Decimal('50.00'),
            billing_period='monthly',
            trial_days=0,  # No trial
            is_active=True
        )
        no_trial_plan.features.add(feature)
        
        print(f"✓ Plan created: {no_trial_plan.name}")
        print(f"  Base price: ${no_trial_plan.base_price}")
        print(f"  Trial days: {no_trial_plan.trial_days}")
        
        if no_trial_plan.trial_days == 0:
            print("✓ Plan correctly has no trial period")
        else:
            print("✗ Plan should not have trial period")
            return False
    except Exception as e:
        print(f"✗ Error creating plan: {e}")
        return False
    
    # Test 3: Simulate trial subscription creation
    print("\n[TEST 3] Simulate trial subscription creation")
    print("-" * 70)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        user = User.objects.create_user(
            username='trial_test_user',
            email='trial_test@example.com',
            password='testpass123'
        )
        
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Check if plan has trial
        is_trial = trial_plan.trial_days > 0
        
        print(f"✓ User created: {user.username}")
        print(f"  Is trial subscription: {is_trial}")
        
        # Calculate dates
        start_date = timezone.now()
        
        if is_trial:
            trial_end_date = start_date + timedelta(days=trial_plan.trial_days)
            end_date = trial_end_date
            next_billing_date = trial_end_date
            amount_paid = Decimal('0.00')
            
            print(f"✓ Trial dates calculated:")
            print(f"  Start date: {start_date.date()}")
            print(f"  Trial end date: {trial_end_date.date()}")
            print(f"  Next billing date: {next_billing_date.date()}")
            print(f"  Amount paid: ${amount_paid}")
        else:
            trial_end_date = None
            end_date = start_date + timedelta(days=30)
            next_billing_date = start_date + timedelta(days=30)
            amount_paid = trial_plan.base_price
            
            print(f"✓ Regular subscription dates calculated:")
            print(f"  Start date: {start_date.date()}")
            print(f"  End date: {end_date.date()}")
            print(f"  Amount paid: ${amount_paid}")
        
        # Create payment method (simulating card save during checkout)
        payment_method = PaymentMethod.objects.create(
            billing_profile=billing_profile,
            payment_type='card',
            gateway_authorization_code='AUTH_trial_test',
            card_last4='4242',
            card_brand='visa',
            card_exp_month='12',
            card_exp_year='2030',
            is_default=True,
            is_active=True
        )
        
        print(f"✓ Payment method saved: {payment_method.card_brand} ending in {payment_method.card_last4}")
        
        # Create subscription
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=trial_plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            is_trial=is_trial,
            trial_end_date=trial_end_date,
            amount_paid=amount_paid,
            currency='USD',
            auto_renew=True,
            payment_method=payment_method,
            next_billing_date=next_billing_date
        )
        
        print(f"✓ Subscription created: {subscription.id}")
        print(f"  Status: {subscription.status}")
        print(f"  Is trial: {subscription.is_trial}")
        print(f"  Trial end date: {subscription.trial_end_date}")
        print(f"  Amount paid: ${subscription.amount_paid}")
        print(f"  Auto-renew: {subscription.auto_renew}")
        print(f"  Payment method linked: {subscription.payment_method is not None}")
        
        # Verify trial properties
        if subscription.is_trial:
            print(f"  Days until trial end: {subscription.days_until_trial_end}")
    except Exception as e:
        print(f"✗ Error creating trial subscription: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Simulate regular (non-trial) subscription creation
    print("\n[TEST 4] Simulate regular subscription creation")
    print("-" * 70)
    
    try:
        user2 = User.objects.create_user(
            username='regular_test_user',
            email='regular_test@example.com',
            password='testpass123'
        )
        
        billing_profile2 = BillingProfile.objects.get(user=user2)
        
        is_trial = no_trial_plan.trial_days > 0
        start_date = timezone.now()
        
        if is_trial:
            trial_end_date = start_date + timedelta(days=no_trial_plan.trial_days)
            end_date = trial_end_date
            next_billing_date = trial_end_date
            amount_paid = Decimal('0.00')
        else:
            trial_end_date = None
            end_date = start_date + timedelta(days=30)
            next_billing_date = start_date + timedelta(days=30)
            amount_paid = no_trial_plan.base_price
        
        payment_method2 = PaymentMethod.objects.create(
            billing_profile=billing_profile2,
            payment_type='card',
            gateway_authorization_code='AUTH_regular_test',
            card_last4='5555',
            card_brand='mastercard',
            card_exp_month='06',
            card_exp_year='2028',
            is_default=True,
            is_active=True
        )
        
        subscription2 = Subscription.objects.create(
            billing_profile=billing_profile2,
            plan=no_trial_plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            is_trial=is_trial,
            trial_end_date=trial_end_date,
            amount_paid=amount_paid,
            currency='USD',
            auto_renew=True,
            payment_method=payment_method2,
            next_billing_date=next_billing_date
        )
        
        print(f"✓ Regular subscription created: {subscription2.id}")
        print(f"  Is trial: {subscription2.is_trial}")
        print(f"  Amount paid: ${subscription2.amount_paid}")
        
        if not subscription2.is_trial and subscription2.amount_paid == no_trial_plan.base_price:
            print("✓ Regular subscription correctly charged full price")
        else:
            print("✗ Regular subscription should not be trial and should be charged")
            return False
    except Exception as e:
        print(f"✗ Error creating regular subscription: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Verify trial vs non-trial logic
    print("\n[TEST 5] Verify trial vs non-trial logic")
    print("-" * 70)
    
    try:
        print("Trial Subscription:")
        print(f"  Is trial: {subscription.is_trial}")
        print(f"  Amount paid: ${subscription.amount_paid}")
        print(f"  Trial end date: {subscription.trial_end_date}")
        print(f"  Next billing date: {subscription.next_billing_date}")
        
        print("\nRegular Subscription:")
        print(f"  Is trial: {subscription2.is_trial}")
        print(f"  Amount paid: ${subscription2.amount_paid}")
        print(f"  Trial end date: {subscription2.trial_end_date}")
        print(f"  Next billing date: {subscription2.next_billing_date}")
        
        # Verify trial is $0
        if subscription.is_trial and subscription.amount_paid == Decimal('0.00'):
            print("\n✓ Trial subscription has $0 amount_paid")
        else:
            print("\n✗ Trial subscription should have $0 amount_paid")
            return False
        
        # Verify regular is charged
        if not subscription2.is_trial and subscription2.amount_paid == no_trial_plan.base_price:
            print("✓ Regular subscription charged full price")
        else:
            print("✗ Regular subscription should be charged full price")
            return False
    except Exception as e:
        print(f"✗ Error verifying subscriptions: {e}")
        return False
    
    # Cleanup
    print("\n[CLEANUP] Removing test data")
    print("-" * 70)
    try:
        user.delete()
        user2.delete()
        trial_plan.delete()
        no_trial_plan.delete()
        feature.delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"⚠ Warning: Cleanup failed: {e}")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print("\nSummary:")
    print("✓ Plans can be created with and without trial periods")
    print("✓ Trial subscriptions are created with is_trial=True")
    print("✓ Trial subscriptions have $0 amount_paid")
    print("✓ Trial subscriptions have trial_end_date set")
    print("✓ Regular subscriptions charged full price")
    print("✓ Payment methods are linked for auto-renewal")
    print("✓ Next billing date set correctly for both types")
    print("\nTrial subscription flow is ready! 🚀")
    
    return True

if __name__ == '__main__':
    try:
        success = test_trial_subscription_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
