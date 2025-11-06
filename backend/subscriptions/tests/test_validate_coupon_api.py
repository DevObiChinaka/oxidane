"""
Comprehensive tests for Validate Coupon API (Phase 0.5 - Task 0.5.34)

Tests POST /api/v1/subscriptions/validate-coupon/validate/ endpoint:
- Valid coupon codes (percentage and fixed discounts)
- Invalid/expired/inactive coupons
- Usage limits (total and per-user)
- Plan restrictions
- Discount calculations
- Edge cases (zero discount, missing fields, etc.)
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from subscriptions.models import Coupon, SubscriptionPlan, Feature, Subscription, BillingProfile, User


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def billing_profile(user):
    """Get or create a billing profile for the test user"""
    # BillingProfile is auto-created by signal, so get_or_create instead of create
    profile, created = BillingProfile.objects.get_or_create(user=user)
    return profile


@pytest.fixture
def active_plan(db):
    """Create an active subscription plan"""
    plan = SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium-monthly',
        description='Premium features',
        base_price=Decimal('99.00'),
        billing_period='monthly',
        trial_days=7,
        is_active=True,
        is_featured=True,
        sort_order=1
    )
    return plan


@pytest.fixture
def yearly_plan(db):
    """Create a yearly subscription plan"""
    plan = SubscriptionPlan.objects.create(
        name='Yearly Plan',
        slug='yearly',
        description='Annual subscription',
        base_price=Decimal('999.00'),
        billing_period='yearly',
        is_active=True,
        sort_order=2
    )
    return plan


@pytest.fixture
def percentage_coupon(db):
    """Create a percentage discount coupon"""
    return Coupon.objects.create(
        code='SAVE20',
        discount_type='percentage',
        discount_value=Decimal('20.00'),
        is_active=True,
        max_uses=100,
        max_uses_per_user=3
    )


@pytest.fixture
def fixed_coupon(db):
    """Create a fixed amount discount coupon"""
    return Coupon.objects.create(
        code='FIXED10',
        discount_type='fixed',
        discount_value=Decimal('10.00'),
        is_active=True
    )


@pytest.fixture
def expired_coupon(db):
    """Create an expired coupon"""
    return Coupon.objects.create(
        code='EXPIRED',
        discount_type='percentage',
        discount_value=Decimal('50.00'),
        valid_from=timezone.now() - timedelta(days=30),
        valid_until=timezone.now() - timedelta(days=1),
        is_active=True
    )


@pytest.fixture
def inactive_coupon(db):
    """Create an inactive coupon"""
    return Coupon.objects.create(
        code='INACTIVE',
        discount_type='percentage',
        discount_value=Decimal('30.00'),
        is_active=False
    )


@pytest.fixture
def plan_specific_coupon(db, active_plan):
    """Create a coupon that only applies to specific plans"""
    coupon = Coupon.objects.create(
        code='PREMIUM50',
        discount_type='percentage',
        discount_value=Decimal('50.00'),
        is_active=True
    )
    coupon.plans.add(active_plan)
    return coupon


@pytest.fixture
def usage_limit_reached_coupon(db):
    """Create a coupon with usage limit reached"""
    return Coupon.objects.create(
        code='MAXEDOUT',
        discount_type='percentage',
        discount_value=Decimal('15.00'),
        is_active=True,
        max_uses=5,
        current_uses=5  # Already maxed out
    )


@pytest.fixture
def future_coupon(db):
    """Create a coupon that starts in the future"""
    return Coupon.objects.create(
        code='FUTURE',
        discount_type='percentage',
        discount_value=Decimal('25.00'),
        valid_from=timezone.now() + timedelta(days=7),
        is_active=True
    )


# ============================================================================
# Test: Valid Coupon Validation
# ============================================================================

@pytest.mark.django_db
class TestValidCouponValidation:
    """Tests for valid coupon codes"""
    
    def test_validate_percentage_coupon_without_amount(self, api_client, percentage_coupon):
        """Should validate percentage coupon without calculating discount"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'SAVE20'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['code'] == 'SAVE20'
        assert data['discount_type'] == 'percentage'
        assert data['discount_value'] == 20.0
        assert data['discount_display'] == '20% off'
        assert 'message' in data
        assert 'usage' in data
    
    def test_validate_percentage_coupon_with_amount(self, api_client, percentage_coupon):
        """Should validate coupon and calculate discount for percentage type"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['original_price'] == 99.00
        assert data['discount_amount'] == 19.80  # 20% of 99
        assert data['final_price'] == 79.20
        assert data['savings_percentage'] == 20.0
    
    def test_validate_fixed_coupon_with_amount(self, api_client, fixed_coupon):
        """Should validate coupon and calculate discount for fixed type"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'FIXED10',
            'amount': 50.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['discount_type'] == 'fixed'
        assert data['original_price'] == 50.00
        assert data['discount_amount'] == 10.00
        assert data['final_price'] == 40.00
        assert data['savings_percentage'] == 20.0
    
    def test_validate_coupon_case_insensitive(self, api_client, percentage_coupon):
        """Should validate coupon code regardless of case"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        
        # Test lowercase
        response = api_client.post(url, {'code': 'save20'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['valid'] is True
        
        # Test mixed case
        response = api_client.post(url, {'code': 'SaVe20'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['valid'] is True
    
    def test_validate_coupon_with_plan(self, api_client, percentage_coupon, active_plan):
        """Should validate coupon for a specific plan (no restrictions)"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'plan_id': str(active_plan.id),
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        # No applicable_plan info if coupon applies to all plans
    
    def test_validate_plan_specific_coupon(self, api_client, plan_specific_coupon, active_plan):
        """Should validate plan-specific coupon with correct plan"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'PREMIUM50',
            'plan_id': str(active_plan.id),
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['discount_amount'] == 49.50  # 50% of 99
        assert 'applicable_plan' in data
        assert data['applicable_plan']['name'] == 'Premium Plan'


# ============================================================================
# Test: Invalid Coupon Codes
# ============================================================================

@pytest.mark.django_db
class TestInvalidCouponCodes:
    """Tests for invalid, expired, and inactive coupons"""
    
    def test_validate_nonexistent_coupon(self, api_client):
        """Should return error for non-existent coupon code"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'DOESNOTEXIST'})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        
        assert data['valid'] is False
        assert data['code'] == 'DOESNOTEXIST'
        assert data['error_code'] == 'COUPON_NOT_FOUND'
        assert 'error' in data
    
    def test_validate_expired_coupon(self, api_client, expired_coupon):
        """Should return error for expired coupon"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'EXPIRED'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'COUPON_EXPIRED'
        assert 'expired' in data['error'].lower()
        assert 'valid_until' in data
    
    def test_validate_inactive_coupon(self, api_client, inactive_coupon):
        """Should return error for inactive coupon"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'INACTIVE'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'COUPON_INACTIVE'
        assert 'no longer active' in data['error'].lower() or 'not active' in data['error'].lower()
    
    def test_validate_future_coupon(self, api_client, future_coupon):
        """Should return error for coupon that hasn't started yet"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'FUTURE'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'COUPON_NOT_STARTED'
        assert 'not valid until' in data['error']
        assert 'valid_from' in data
    
    def test_validate_missing_code(self, api_client):
        """Should return error when coupon code is missing"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'MISSING_CODE'


# ============================================================================
# Test: Usage Limits
# ============================================================================

@pytest.mark.django_db
class TestCouponUsageLimits:
    """Tests for coupon usage limits"""
    
    def test_validate_usage_limit_reached(self, api_client, usage_limit_reached_coupon):
        """Should return error when total usage limit is reached"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'MAXEDOUT'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'USAGE_LIMIT_REACHED'
        assert 'usage limit' in data['error']
        assert data['current_uses'] == 5
        assert data['max_uses'] == 5
    
    def test_validate_user_usage_limit_reached(self, api_client, percentage_coupon, 
                                               user, billing_profile, active_plan):
        """Should return error when user has already used coupon max times"""
        # Create 3 subscriptions with this coupon for the user
        for i in range(3):
            Subscription.objects.create(
                billing_profile=billing_profile,
                plan=active_plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                amount_paid=Decimal('99.00'),
                status='active',
                metadata={'coupon_code': 'SAVE20'}
            )
        
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'user_id': str(user.id)
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'USER_LIMIT_REACHED'
        assert 'already used' in data['error']
        assert data['user_usage'] == 3
        assert data['max_uses_per_user'] == 3
    
    def test_validate_user_below_usage_limit(self, api_client, percentage_coupon, 
                                            user, billing_profile, active_plan):
        """Should validate successfully when user is below usage limit"""
        # Create 1 subscription (max is 3)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=active_plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('99.00'),
            status='active',
            metadata={'coupon_code': 'SAVE20'}
        )
        
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'user_id': str(user.id),
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
    
    def test_validate_with_invalid_user_id(self, api_client, percentage_coupon):
        """Should still validate if user_id is invalid (graceful degradation)"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'user_id': '00000000-0000-0000-0000-000000000000'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['valid'] is True


# ============================================================================
# Test: Plan Restrictions
# ============================================================================

@pytest.mark.django_db
class TestPlanRestrictions:
    """Tests for plan-specific coupon restrictions"""
    
    def test_validate_plan_specific_coupon_with_wrong_plan(self, api_client, 
                                                           plan_specific_coupon, yearly_plan):
        """Should return error when coupon doesn't apply to plan"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'PREMIUM50',
            'plan_id': str(yearly_plan.id)
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'PLAN_NOT_APPLICABLE'
        assert 'not applicable' in data['error'].lower() or 'only valid for' in data['error'].lower()
    
    def test_validate_plan_specific_coupon_without_plan_id(self, api_client, plan_specific_coupon):
        """Should return error when plan-specific coupon validated without plan_id"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'PREMIUM50'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'MISSING_PLAN_ID'
        assert 'requires a plan' in data['error']
    
    def test_validate_with_invalid_plan_id(self, api_client, percentage_coupon):
        """Should return error for invalid plan ID"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'plan_id': '00000000-0000-0000-0000-000000000000'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'INVALID_PLAN_ID'


# ============================================================================
# Test: Discount Calculations
# ============================================================================

@pytest.mark.django_db
class TestDiscountCalculations:
    """Tests for discount amount calculations"""
    
    def test_percentage_discount_calculation(self, api_client, percentage_coupon):
        """Should correctly calculate percentage discount"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        test_cases = [
            (100.00, 20.00, 80.00),
            (50.00, 10.00, 40.00),
            (99.99, 19.998, 79.992),  # Rounding edge case
        ]
        
        for original, discount, final in test_cases:
            response = api_client.post(url, {
                'code': 'SAVE20',
                'amount': original
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data['original_price'] == original
            assert abs(data['discount_amount'] - discount) < 0.01  # Allow small rounding
            assert abs(data['final_price'] - final) < 0.01
    
    def test_fixed_discount_calculation(self, api_client, fixed_coupon):
        """Should correctly calculate fixed discount"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'FIXED10',
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['original_price'] == 99.00
        assert data['discount_amount'] == 10.00
        assert data['final_price'] == 89.00
        assert abs(data['savings_percentage'] - 10.101) < 0.01  # 10/99 * 100
    
    def test_fixed_discount_larger_than_price(self, api_client, fixed_coupon):
        """Should not make price negative if discount is larger than price"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'FIXED10',
            'amount': 5.00  # Price less than discount
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['original_price'] == 5.00
        assert data['discount_amount'] == 5.00  # Capped at price
        assert data['final_price'] == 0.00
        assert data['savings_percentage'] == 100.0
    
    def test_invalid_amount_format(self, api_client, percentage_coupon):
        """Should return error for invalid amount format"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'amount': 'invalid'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data['valid'] is False
        assert data['error_code'] == 'INVALID_AMOUNT'


# ============================================================================
# Test: Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_validate_zero_price(self, api_client, percentage_coupon):
        """Should handle zero price gracefully"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'amount': 0.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['discount_amount'] == 0.00
        assert data['final_price'] == 0.00
    
    def test_validate_100_percent_discount(self, api_client, db):
        """Should handle 100% discount correctly"""
        coupon = Coupon.objects.create(
            code='FREE100',
            discount_type='percentage',
            discount_value=Decimal('100.00'),
            is_active=True
        )
        
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'FREE100',
            'amount': 99.00
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['final_price'] == 0.00
        assert data['discount_amount'] == 99.00
        assert data['savings_percentage'] == 100.0
    
    def test_validate_very_large_amount(self, api_client, percentage_coupon):
        """Should handle very large amounts"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {
            'code': 'SAVE20',
            'amount': 999999.99
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['original_price'] == 999999.99
    
    def test_usage_stats_in_response(self, api_client, percentage_coupon):
        """Should include usage statistics in response"""
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'SAVE20'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'usage' in data
        assert data['usage']['current_uses'] == 0
        assert data['usage']['max_uses'] == 100
        assert data['usage']['remaining_uses'] == 100
    
    def test_unlimited_usage_coupon(self, api_client, db):
        """Should handle unlimited usage coupons (max_uses=None)"""
        coupon = Coupon.objects.create(
            code='UNLIMITED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            is_active=True,
            max_uses=None  # Unlimited
        )
        
        url = reverse('subscriptions:v1-validate-coupon-validate')
        response = api_client.post(url, {'code': 'UNLIMITED'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['valid'] is True
        assert data['usage']['max_uses'] is None
        assert data['usage']['remaining_uses'] is None
