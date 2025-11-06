"""
Tests for Plan Upgrade/Downgrade APIs (Phase 0.5 - Task 0.5.36)

API endpoints for upgrading and downgrading subscription plans with prorated billing.

Endpoints tested:
- POST /api/v1/subscriptions/{id}/upgrade/
- POST /api/v1/subscriptions/{id}/downgrade/

Test Coverage:
- Plan upgrades (immediate with prorated credit)
- Plan downgrades (scheduled and immediate)
- Prorated billing calculations
- Validation (higher/lower tier checks)
- Edge cases (same plan, inactive subscriptions)
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from subscriptions.models import BillingProfile, Subscription, SubscriptionPlan, Feature

User = get_user_model()


@pytest.mark.django_db
class TestPlanUpgrade:
    """Test subscription plan upgrade scenarios"""
    
    def test_successful_upgrade_with_prorated_credit(self):
        """Upgrade to higher-tier plan should apply prorated credit"""
        client = APIClient()
        
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        # Get or create billing profile
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        # Create plans
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic Monthly',
            slug='basic-monthly',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium Monthly',
            slug='premium-monthly',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        # Create active subscription (15 days remaining out of 30)
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'upgrade_details' in data
        assert data['upgrade_details']['new_plan'] == 'Premium Monthly'
        assert data['upgrade_details']['old_plan'] == 'Basic Monthly'
        assert data['upgrade_details']['prorated_credit'] > 0  # Should get credit for unused days
        assert data['upgrade_details']['amount_due'] >= 0
        
        # Refresh subscription from DB
        subscription.refresh_from_db()
        assert subscription.plan.id == premium_plan.id
        assert 'upgrade_history' in subscription.metadata
    
    def test_upgrade_with_payment_reference(self):
        """Upgrade with payment reference should store it"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            base_price=Decimal('19.99'),
            billing_period='monthly',
            is_active=True
        )
        
        pro_plan = SubscriptionPlan.objects.create(
            name='Professional',
            slug='professional',
            base_price=Decimal('49.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('19.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(pro_plan.id),
            'payment_reference': 'PAY_REF_12345'
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['payment_reference'] == 'PAY_REF_12345'
        
        # Check metadata
        subscription.refresh_from_db()
        upgrade_history = subscription.metadata['upgrade_history']
        assert len(upgrade_history) == 1
        assert upgrade_history[0]['payment_reference'] == 'PAY_REF_12345'
    
    def test_upgrade_to_inactive_plan_fails(self):
        """Upgrading to inactive plan should fail"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        inactive_plan = SubscriptionPlan.objects.create(
            name='Deprecated',
            slug='deprecated',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            is_active=False
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(inactive_plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'PLAN_INACTIVE'
    
    def test_upgrade_inactive_subscription_fails(self):
        """Cannot upgrade inactive subscription"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-test',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-test',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='expired',  # Inactive
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'SUBSCRIPTION_INACTIVE'
    
    def test_upgrade_to_same_plan_fails(self):
        """Upgrading to same plan should fail"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            base_price=Decimal('49.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('49.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'SAME_PLAN'
    
    def test_upgrade_to_lower_tier_fails(self):
        """Upgrading to lower-priced plan should fail"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='testuser6',
            email='test6@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-6',
            base_price=Decimal('99.99'),
            billing_period='monthly',
            is_active=True
        )
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-6',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=premium_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('99.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(basic_plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'INVALID_UPGRADE'


@pytest.mark.django_db
class TestPlanDowngrade:
    """Test subscription plan downgrade scenarios"""
    
    def test_successful_scheduled_downgrade(self):
        """Downgrade should be scheduled for end of billing period"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='downgrade_user',
            email='downgrade@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-down',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-down',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        end_date = now + timedelta(days=20)
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=premium_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=end_date,
            amount_paid=Decimal('59.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/downgrade/', {
            'new_plan_id': str(basic_plan.id),
            'immediate': False
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['downgrade_details']['immediate'] is False
        # Check that message indicates change date (from downgrade_plan method)
        assert 'plan will change' in data['message'].lower() or 'scheduled' in data['message'].lower()
        
        # Check metadata
        subscription.refresh_from_db()
        assert 'scheduled_downgrade' in subscription.metadata
        assert subscription.metadata['scheduled_downgrade']['new_plan_name'] == 'Basic'
        assert subscription.auto_renew is False  # Should disable auto-renewal
    
    def test_successful_immediate_downgrade(self):
        """Immediate downgrade should take effect right away"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='immediate_user',
            email='immediate@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-immediate',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-immediate',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=premium_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('59.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/downgrade/', {
            'new_plan_id': str(basic_plan.id),
            'immediate': True
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['downgrade_details']['immediate'] is True
        
        # Check subscription was updated
        subscription.refresh_from_db()
        assert subscription.plan.id == basic_plan.id
        assert 'downgrade_history' in subscription.metadata
    
    def test_downgrade_to_higher_tier_fails(self):
        """Downgrading to higher-priced plan should fail"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='invalid_down_user',
            email='invalid_down@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-invalid',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-invalid',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/downgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'INVALID_DOWNGRADE'
    
    def test_downgrade_inactive_subscription_fails(self):
        """Cannot downgrade inactive subscription"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='inactive_down_user',
            email='inactive_down@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-inactive-test',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-inactive-test',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=premium_plan,
            status='cancelled',  # Inactive
            start_date=now - timedelta(days=40),
            end_date=now - timedelta(days=10),
            amount_paid=Decimal('59.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/downgrade/', {
            'new_plan_id': str(basic_plan.id)
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error_code'] == 'SUBSCRIPTION_INACTIVE'


@pytest.mark.django_db
class TestUpgradeCalculations:
    """Test prorated billing calculations for upgrades"""
    
    def test_prorated_credit_halfway_through_period(self):
        """Prorated credit should be ~50% if halfway through period"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='calc_user',
            email='calc@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-calc',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-calc',
            base_price=Decimal('60.00'),
            billing_period='monthly',
            is_active=True
        )
        
        # Create subscription halfway through period
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            amount_paid=Decimal('30.00'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Prorated credit should be around $15 (50% of $30)
        prorated_credit = data['upgrade_details']['prorated_credit']
        assert 14.0 <= prorated_credit <= 16.0  # Allow small variance
        
        # Amount due should be around $45 ($60 - $15)
        amount_due = data['upgrade_details']['amount_due']
        assert 44.0 <= amount_due <= 46.0
    
    def test_prorated_credit_near_end_of_period(self):
        """Prorated credit should be minimal near end of period"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='end_period_user',
            email='end_period@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-end',
            base_price=Decimal('30.00'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-end',
            base_price=Decimal('60.00'),
            billing_period='monthly',
            is_active=True
        )
        
        # Create subscription with only 3 days remaining out of 30
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=now - timedelta(days=27),
            end_date=now + timedelta(days=3),
            amount_paid=Decimal('30.00'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        
        # Prorated credit should be around $3 (10% of $30)
        prorated_credit = data['upgrade_details']['prorated_credit']
        assert prorated_credit < 5.0  # Should be small
        
        # Amount due should be close to full price
        amount_due = data['upgrade_details']['amount_due']
        assert amount_due > 55.0


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_upgrade_nonexistent_subscription(self):
        """Upgrading non-existent subscription should return 404"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='edge_user',
            email='edge@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        fake_id = '00000000-0000-0000-0000-000000000000'
        
        response = client.post(f'/api/v1/subscriptions/{fake_id}/upgrade/', {
            'new_plan_id': fake_id
        }, format='json')
        
        assert response.status_code == 404
        data = response.json()
        assert data['error_code'] == 'SUBSCRIPTION_NOT_FOUND'
    
    def test_upgrade_missing_plan_id(self):
        """Upgrade without plan ID should fail"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='missing_plan_user',
            email='missing_plan@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-missing',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            # No plan_id provided
        }, format='json')
        
        assert response.status_code == 400
        data = response.json()
        assert data['error_code'] == 'MISSING_PLAN_ID'
    
    def test_unauthorized_upgrade_attempt(self):
        """User cannot upgrade another user's subscription"""
        client = APIClient()
        
        # Create subscription owner
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        owner_profile, _ = BillingProfile.objects.get_or_create(user=owner)
        
        # Create different user
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=other_user)
        
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-auth',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium-auth',
            base_price=Decimal('59.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=owner_profile,
            plan=plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': str(premium_plan.id)
        }, format='json')
        
        assert response.status_code == 403
        data = response.json()
        assert data['error_code'] == 'PERMISSION_DENIED'
    
    def test_upgrade_with_invalid_plan_id_format(self):
        """Invalid plan ID format should fail gracefully"""
        client = APIClient()
        
        user = User.objects.create_user(
            username='invalid_format_user',
            email='invalid_format@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)
        
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic-invalid-format',
            base_price=Decimal('29.99'),
            billing_period='monthly',
            is_active=True
        )
        
        now = timezone.now()
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=20),
            amount_paid=Decimal('29.99'),
            currency='USD'
        )
        
        response = client.post(f'/api/v1/subscriptions/{subscription.id}/upgrade/', {
            'new_plan_id': 'not-a-uuid'
        }, format='json')
        
        assert response.status_code in [400, 404]  # Either validation or not found
