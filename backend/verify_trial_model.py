"""
Quick script to verify trial subscription model functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from subscriptions.models import (
    SubscriptionPlan,
    Subscription,
    BillingProfile,
    PaymentMethod,
    Feature
)

User = get_user_model()

print("=" * 60)
print("TRIAL SUBSCRIPTION MODEL VERIFICATION")
print("=" * 60)

# Clean up any existing test data
print("\n✓ Cleanup: Removing any existing test data...")
try:
    User.objects.filter(username='trial_test_user').delete()
    SubscriptionPlan.objects.filter(slug__in=['test-monthly-trial', 'trial-test']).delete()
    print("  ✓ Cleanup complete")
except Exception as e:
    print(f"  - Cleanup note: {e}")

# Test 1: Check if trial fields exist
print("\n✓ Test 1: Checking trial fields on Subscription model...")
trial_fields = ['is_trial', 'trial_end_date']
for field in trial_fields:
    has_field = hasattr(Subscription, field)
    print(f"  - {field}: {'✓ EXISTS' if has_field else '✗ MISSING'}")

# Test 2: Check SubscriptionPlan has trial_days
print("\n✓ Test 2: Checking trial_days on SubscriptionPlan model...")
has_trial_days = hasattr(SubscriptionPlan, 'trial_days')
print(f"  - trial_days: {'✓ EXISTS' if has_trial_days else '✗ MISSING'}")

# Test 3: Create a plan with trial
print("\n✓ Test 3: Creating plan with trial...")
try:
    plan = SubscriptionPlan.objects.create(
        name='Test Monthly Plan',
        slug='test-monthly-trial',
        base_price=Decimal('30.00'),
        billing_period='monthly',
        trial_days=7,  # 7-day trial
        is_active=True
    )
    print(f"  - Plan created: {plan.name}")
    print(f"  - Trial days: {plan.trial_days}")
    print(f"  - Has trial: {plan.has_trial}")
    plan.delete()  # Clean up
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 4: Create user and billing profile
print("\n✓ Test 4: Creating user and billing profile...")
try:
    user = User.objects.create_user(
        username='trial_test_user',
        email='trial@test.com',
        password='test123'
    )
    # Billing profile is auto-created by signal
    billing_profile = user.billing_profile
    billing_profile.telegram_verified = True
    billing_profile.save()
    
    print(f"  - User created: {user.email}")
    print(f"  - Billing profile created: {billing_profile.id}")
    print("  ✓ SUCCESS")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    user = None
    billing_profile = None

# Test 5: Create trial subscription
if user and billing_profile:
    print("\n✓ Test 5: Creating trial subscription...")
    try:
        plan = SubscriptionPlan.objects.create(
            name='Trial Test Plan',
            slug='trial-test',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            trial_days=7,
            is_active=True
        )
        
        trial_end = timezone.now() + timedelta(days=7)
        subscription_end = trial_end + timedelta(days=30)
        
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            is_trial=True,
            trial_end_date=trial_end,
            start_date=timezone.now(),
            end_date=subscription_end,
            amount_paid=Decimal('0.00'),
            currency='USD',
            auto_renew=True,
            next_billing_date=trial_end,
            metadata={
                'trial_started': timezone.now().isoformat(),
                'trial_duration_days': 7
            }
        )
        
        print(f"  - Subscription created: {subscription.id}")
        print(f"  - Is trial: {subscription.is_trial}")
        print(f"  - Trial end date: {subscription.trial_end_date}")
        print(f"  - Amount paid: ${subscription.amount_paid}")
        print(f"  - Days until trial end: {subscription.days_until_trial_end}")
        print("  ✓ SUCCESS")
        
        # Clean up
        subscription.delete()
        plan.delete()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()

# Clean up
if user:
    if billing_profile:
        billing_profile.delete()
    user.delete()

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
