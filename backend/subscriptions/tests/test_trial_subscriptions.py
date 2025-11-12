"""
Tests for trial subscription functionality
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
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


class TrialSubscriptionTestCase(TestCase):
    """Test trial subscription creation and management"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create billing profile
        self.billing_profile = BillingProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            telegram_verified=True
        )
        
        # Create features
        self.feature1 = Feature.objects.create(
            key='premium_signals',
            name='Premium Signals',
            description='Access to premium trading signals'
        )
        
        # Create plan WITH trial (7 days)
        self.trial_plan = SubscriptionPlan.objects.create(
            name='Monthly Signals',
            slug='monthly-signals',
            description='Monthly subscription with trial',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            trial_days=7,  # Admin set 7-day trial
            is_active=True
        )
        self.trial_plan.features.add(self.feature1)
        
        # Create plan WITHOUT trial
        self.no_trial_plan = SubscriptionPlan.objects.create(
            name='Lifetime Mentorship',
            slug='lifetime-mentorship',
            description='One-time lifetime purchase',
            base_price=Decimal('500.00'),
            billing_period='lifetime',
            trial_days=0,  # Admin set NO trial
            is_active=True
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_test123',
            card_last4='4081',
            card_brand='visa',
            card_exp_month='12',
            card_exp_year='2025',
            is_default=True,
            is_active=True
        )
    
    def test_trial_plan_has_trial_days(self):
        """Test that trial plan has trial_days configured"""
        self.assertEqual(self.trial_plan.trial_days, 7)
        self.assertTrue(self.trial_plan.has_trial)
    
    def test_no_trial_plan_has_zero_trial_days(self):
        """Test that non-trial plan has 0 trial_days"""
        self.assertEqual(self.no_trial_plan.trial_days, 0)
        self.assertFalse(self.no_trial_plan.has_trial)
    
    def test_create_trial_subscription(self):
        """Test creating a trial subscription"""
        trial_end = timezone.now() + timedelta(days=7)
        subscription_end = trial_end + timedelta(days=30)
        
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.trial_plan,
            status='active',
            is_trial=True,
            trial_end_date=trial_end,
            start_date=timezone.now(),
            end_date=subscription_end,
            amount_paid=Decimal('0.00'),  # No charge during trial
            currency='USD',
            payment_method=self.payment_method,
            auto_renew=True,
            next_billing_date=trial_end,
            metadata={
                'trial_started': timezone.now().isoformat(),
                'trial_duration_days': 7
            }
        )
        
        # Assertions
        self.assertTrue(subscription.is_trial)
        self.assertIsNotNone(subscription.trial_end_date)
        self.assertEqual(subscription.amount_paid, Decimal('0.00'))
        self.assertTrue(subscription.auto_renew)
        self.assertEqual(subscription.payment_method, self.payment_method)
        self.assertEqual(subscription.status, 'active')
    
    def test_create_non_trial_subscription(self):
        """Test creating a subscription without trial"""
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.no_trial_plan,
            status='active',
            is_trial=False,
            trial_end_date=None,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=36500),  # Lifetime
            amount_paid=Decimal('500.00'),  # Charged immediately
            currency='USD',
            auto_renew=False,  # Lifetime doesn't renew
            metadata={
                'direct_purchase': True
            }
        )
        
        # Assertions
        self.assertFalse(subscription.is_trial)
        self.assertIsNone(subscription.trial_end_date)
        self.assertEqual(subscription.amount_paid, Decimal('500.00'))
        self.assertFalse(subscription.auto_renew)
    
    def test_days_until_trial_end_property(self):
        """Test days_until_trial_end property calculation"""
        trial_end = timezone.now() + timedelta(days=5)
        
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.trial_plan,
            status='active',
            is_trial=True,
            trial_end_date=trial_end,
            start_date=timezone.now(),
            end_date=trial_end + timedelta(days=30),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=self.payment_method,
            auto_renew=True
        )
        
        days = subscription.days_until_trial_end
        self.assertIsNotNone(days)
        self.assertEqual(days, 5)
    
    def test_days_until_trial_end_for_non_trial(self):
        """Test days_until_trial_end returns None for non-trial"""
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.no_trial_plan,
            status='active',
            is_trial=False,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365),
            amount_paid=Decimal('500.00'),
            currency='USD'
        )
        
        self.assertIsNone(subscription.days_until_trial_end)
    
    def test_trial_subscription_with_payment_method(self):
        """Test trial subscription requires payment method"""
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.trial_plan,
            status='active',
            is_trial=True,
            trial_end_date=timezone.now() + timedelta(days=7),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=37),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=self.payment_method,
            auto_renew=True
        )
        
        self.assertIsNotNone(subscription.payment_method)
        self.assertEqual(
            subscription.payment_method.gateway_authorization_code,
            'auth_test123'
        )
    
    def test_trial_metadata_storage(self):
        """Test trial information stored in metadata"""
        trial_start = timezone.now()
        
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.trial_plan,
            status='active',
            is_trial=True,
            trial_end_date=trial_start + timedelta(days=7),
            start_date=trial_start,
            end_date=trial_start + timedelta(days=37),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=self.payment_method,
            auto_renew=True,
            metadata={
                'trial_started': trial_start.isoformat(),
                'trial_duration_days': 7,
                'plan_trial_days': self.trial_plan.trial_days
            }
        )
        
        self.assertEqual(subscription.metadata['trial_duration_days'], 7)
        self.assertEqual(subscription.metadata['plan_trial_days'], 7)
        self.assertIn('trial_started', subscription.metadata)


class TrialConversionTestCase(TestCase):
    """Test converting trial subscriptions to paid"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='trialuser',
            email='trial@example.com',
            password='testpass123'
        )
        
        self.billing_profile = BillingProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            telegram_verified=True
        )
        
        self.payment_method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_valid123',
            card_last4='4081',
            card_brand='visa',
            is_default=True,
            is_active=True
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly Plan',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            trial_days=7,
            is_active=True
        )
    
    def test_convert_trial_to_paid(self):
        """Test converting a trial subscription to paid"""
        # Create trial subscription
        trial_end = timezone.now() + timedelta(days=7)
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.plan,
            status='active',
            is_trial=True,
            trial_end_date=trial_end,
            start_date=timezone.now(),
            end_date=trial_end + timedelta(days=30),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=self.payment_method,
            auto_renew=True,
            metadata={'trial_started': timezone.now().isoformat()}
        )
        
        # Simulate successful payment and conversion
        subscription.is_trial = False
        subscription.trial_end_date = None
        subscription.amount_paid = self.plan.base_price
        subscription.metadata['converted_from_trial'] = True
        subscription.metadata['conversion_date'] = timezone.now().isoformat()
        subscription.save()
        
        # Verify conversion
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_trial)
        self.assertIsNone(subscription.trial_end_date)
        self.assertEqual(subscription.amount_paid, Decimal('30.00'))
        self.assertTrue(subscription.metadata['converted_from_trial'])
    
    def test_trial_without_payment_method_cannot_convert(self):
        """Test trial without payment method should not convert"""
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.plan,
            status='active',
            is_trial=True,
            trial_end_date=timezone.now() + timedelta(days=7),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=37),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=None,  # No payment method!
            auto_renew=True
        )
        
        # Should not have payment method
        self.assertIsNone(subscription.payment_method)
        self.assertTrue(subscription.is_trial)
    
    def test_expired_trial_becomes_expired(self):
        """Test trial that expires without conversion"""
        past_date = timezone.now() - timedelta(days=1)
        
        subscription = Subscription.objects.create(
            billing_profile=self.billing_profile,
            plan=self.plan,
            status='active',
            is_trial=True,
            trial_end_date=past_date,  # Trial already ended
            start_date=timezone.now() - timedelta(days=8),
            end_date=timezone.now() + timedelta(days=22),
            amount_paid=Decimal('0.00'),
            currency='USD',
            payment_method=None,  # No payment method
            auto_renew=False  # Disabled due to no payment
        )
        
        # Simulate expiration
        subscription.is_trial = False
        subscription.status = 'expired'
        subscription.save()
        
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'expired')
        self.assertFalse(subscription.is_trial)


class PaymentMethodTestCase(TestCase):
    """Test payment method functionality for trials"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='paymentuser',
            email='payment@example.com',
            password='testpass123'
        )
        
        self.billing_profile = BillingProfile.objects.create(
            user=self.user,
            phone_number='+1234567890'
        )
    
    def test_create_payment_method_with_authorization_code(self):
        """Test creating payment method with Paystack authorization code"""
        payment_method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_abc123xyz',
            card_last4='4081',
            card_brand='visa',
            card_exp_month='12',
            card_exp_year='2025',
            bank_name='Test Bank',
            is_default=True,
            is_active=True
        )
        
        self.assertEqual(payment_method.gateway_authorization_code, 'auth_abc123xyz')
        self.assertEqual(payment_method.card_last4, '4081')
        self.assertTrue(payment_method.is_default)
        self.assertTrue(payment_method.is_active)
    
    def test_default_payment_method_only_one(self):
        """Test that only one payment method can be default"""
        # Create first default
        pm1 = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_111',
            card_last4='1111',
            card_brand='visa',
            is_default=True
        )
        
        # Create second default (should unset first)
        pm2 = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_222',
            card_last4='2222',
            card_brand='mastercard',
            is_default=True
        )
        
        # Refresh and check
        pm1.refresh_from_db()
        pm2.refresh_from_db()
        
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)
    
    def test_payment_method_string_representation(self):
        """Test payment method __str__ method"""
        payment_method = PaymentMethod.objects.create(
            billing_profile=self.billing_profile,
            payment_type='card',
            gateway_authorization_code='auth_test',
            card_last4='4081',
            card_brand='visa'
        )
        
        self.assertEqual(str(payment_method), 'visa ****4081')
