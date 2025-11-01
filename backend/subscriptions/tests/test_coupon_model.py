"""
Comprehensive tests for Coupon model.
Tests cover creation, validation, discounts, validity checks, and usage tracking.
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Coupon, SubscriptionPlan
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCouponModel:
    """Test basic Coupon model functionality"""
    
    def test_create_percentage_coupon_success(self):
        """Test successful creation of percentage coupon"""
        coupon = Coupon.objects.create(
            code='SAVE20',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        assert coupon.id is not None
        assert coupon.code == 'SAVE20'
        assert coupon.discount_type == 'percentage'
        assert coupon.discount_value == Decimal('20.00')
        assert coupon.is_active is True
        assert coupon.current_uses == 0
        assert coupon.max_uses_per_user == 1
    
    def test_create_fixed_coupon_success(self):
        """Test successful creation of fixed amount coupon"""
        coupon = Coupon.objects.create(
            code='SAVE10USD',
            discount_type='fixed',
            discount_value=Decimal('10.00')
        )
        
        assert coupon.discount_type == 'fixed'
        assert coupon.discount_value == Decimal('10.00')
    
    def test_coupon_code_auto_uppercase(self):
        """Test that coupon codes are automatically converted to uppercase"""
        coupon = Coupon.objects.create(
            code='summer2024',
            discount_type='percentage',
            discount_value=Decimal('15.00')
        )
        
        assert coupon.code == 'SUMMER2024'
    
    def test_coupon_code_strips_whitespace(self):
        """Test that coupon codes strip whitespace"""
        coupon = Coupon.objects.create(
            code='  SAVE20  ',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        assert coupon.code == 'SAVE20'
    
    def test_coupon_code_uniqueness(self):
        """Test that coupon codes must be unique"""
        Coupon.objects.create(
            code='UNIQUE123',
            discount_type='percentage',
            discount_value=Decimal('10.00')
        )
        
        with pytest.raises(ValidationError):
            Coupon.objects.create(
                code='UNIQUE123',
                discount_type='percentage',
                discount_value=Decimal('20.00')
            )
    
    def test_coupon_code_invalid_characters(self):
        """Test that invalid characters in code raise error"""
        with pytest.raises(ValidationError) as exc_info:
            Coupon.objects.create(
                code='SAVE@20%',
                discount_type='percentage',
                discount_value=Decimal('20.00')
            )
        
        assert 'code' in str(exc_info.value)
    
    def test_coupon_string_representation(self):
        """Test __str__ method returns code with discount"""
        coupon = Coupon.objects.create(
            code='SAVE25',
            discount_type='percentage',
            discount_value=Decimal('25.00')
        )
        
        assert str(coupon) == 'SAVE25 (25% off)'
    
    def test_percentage_coupon_validation_over_100(self):
        """Test that percentage over 100 is invalid"""
        with pytest.raises(ValidationError) as exc_info:
            Coupon.objects.create(
                code='INVALID',
                discount_type='percentage',
                discount_value=Decimal('150.00')
            )
        
        assert 'discount_value' in str(exc_info.value)
    
    def test_percentage_coupon_validation_negative(self):
        """Test that negative percentage is invalid"""
        with pytest.raises(ValidationError) as exc_info:
            Coupon.objects.create(
                code='INVALID',
                discount_type='percentage',
                discount_value=Decimal('-10.00')
            )
        
        assert 'discount_value' in str(exc_info.value)
    
    def test_fixed_coupon_validation_negative(self):
        """Test that negative fixed amount is invalid"""
        with pytest.raises(ValidationError) as exc_info:
            Coupon.objects.create(
                code='INVALID',
                discount_type='fixed',
                discount_value=Decimal('-5.00')
            )
        
        assert 'discount_value' in str(exc_info.value)
    
    def test_coupon_ordering(self):
        """Test coupons are ordered by creation date (newest first)"""
        import time
        
        coupon1 = Coupon.objects.create(
            code='FIRST',
            discount_type='percentage',
            discount_value=Decimal('10.00')
        )
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        coupon2 = Coupon.objects.create(
            code='SECOND',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        coupons = list(Coupon.objects.all())
        assert coupons[0] == coupon2  # Newest first
        assert coupons[1] == coupon1


@pytest.mark.django_db
class TestCouponValidity:
    """Test coupon validity checks"""
    
    def test_coupon_valid_now(self):
        """Test coupon that is currently valid"""
        now = timezone.now()
        coupon = Coupon.objects.create(
            code='VALID',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            is_active=True
        )
        
        assert coupon.is_valid() is True
    
    def test_coupon_not_started(self):
        """Test coupon that hasn't started yet"""
        now = timezone.now()
        coupon = Coupon.objects.create(
            code='FUTURE',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=now + timedelta(days=1),
            is_active=True
        )
        
        assert coupon.is_valid() is False
    
    def test_coupon_expired(self):
        """Test coupon that has expired"""
        now = timezone.now()
        coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(days=1),
            is_active=True
        )
        
        assert coupon.is_valid() is False
    
    def test_coupon_inactive(self):
        """Test inactive coupon"""
        coupon = Coupon.objects.create(
            code='INACTIVE',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            is_active=False
        )
        
        assert coupon.is_valid() is False
    
    def test_coupon_no_expiration(self):
        """Test coupon with no expiration date"""
        coupon = Coupon.objects.create(
            code='FOREVER',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            valid_until=None
        )
        
        assert coupon.is_valid() is True
    
    def test_coupon_invalid_date_range(self):
        """Test coupon with end date before start date"""
        now = timezone.now()
        
        with pytest.raises(ValidationError) as exc_info:
            Coupon.objects.create(
                code='INVALID',
                discount_type='percentage',
                discount_value=Decimal('20.00'),
                valid_from=now,
                valid_until=now - timedelta(days=1)
            )
        
        assert 'valid_until' in str(exc_info.value)


@pytest.mark.django_db
class TestCouponUsageLimits:
    """Test coupon usage tracking and limits"""
    
    def test_coupon_usage_available_unlimited(self):
        """Test coupon with unlimited uses"""
        coupon = Coupon.objects.create(
            code='UNLIMITED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_uses=None
        )
        
        assert coupon.is_usage_available() is True
        assert coupon.get_remaining_uses() is None
    
    def test_coupon_usage_available_with_limit(self):
        """Test coupon with usage limit"""
        coupon = Coupon.objects.create(
            code='LIMITED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_uses=100,
            current_uses=50
        )
        
        assert coupon.is_usage_available() is True
        assert coupon.get_remaining_uses() == 50
    
    def test_coupon_usage_exhausted(self):
        """Test coupon that has reached usage limit"""
        coupon = Coupon.objects.create(
            code='EXHAUSTED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_uses=10,
            current_uses=10
        )
        
        assert coupon.is_usage_available() is False
        assert coupon.get_remaining_uses() == 0
    
    def test_increment_usage(self):
        """Test incrementing coupon usage"""
        coupon = Coupon.objects.create(
            code='INCREMENT',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            current_uses=5
        )
        
        coupon.increment_usage()
        coupon.refresh_from_db()
        
        assert coupon.current_uses == 6
    
    def test_can_be_used_valid_with_usage(self):
        """Test can_be_used when valid and usage available"""
        coupon = Coupon.objects.create(
            code='USABLE',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            is_active=True,
            max_uses=10,
            current_uses=5
        )
        
        assert coupon.can_be_used() is True
    
    def test_can_be_used_expired(self):
        """Test can_be_used when expired"""
        now = timezone.now()
        coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(days=1),
            max_uses=10,
            current_uses=5
        )
        
        assert coupon.can_be_used() is False
    
    def test_can_be_used_exhausted(self):
        """Test can_be_used when usage exhausted"""
        coupon = Coupon.objects.create(
            code='EXHAUSTED',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            is_active=True,
            max_uses=10,
            current_uses=10
        )
        
        assert coupon.can_be_used() is False
    
    def test_negative_usage_validation(self):
        """Test that negative usage values are invalid"""
        with pytest.raises(ValidationError):
            Coupon.objects.create(
                code='INVALID',
                discount_type='percentage',
                discount_value=Decimal('10.00'),
                current_uses=-5
            )


@pytest.mark.django_db
class TestCouponPlanRelationship:
    """Test coupon-plan relationships"""
    
    def test_coupon_applies_to_all_plans(self):
        """Test coupon with no specific plans (applies to all)"""
        plan1 = SubscriptionPlan.objects.create(
            name='Basic',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Pro',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        
        coupon = Coupon.objects.create(
            code='ALLPLANS',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        assert coupon.applies_to_plan(plan1) is True
        assert coupon.applies_to_plan(plan2) is True
    
    def test_coupon_applies_to_specific_plans(self):
        """Test coupon that applies to specific plans only"""
        plan1 = SubscriptionPlan.objects.create(
            name='Basic',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Pro',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        
        coupon = Coupon.objects.create(
            code='PROONLY',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        coupon.plans.add(plan2)
        
        assert coupon.applies_to_plan(plan1) is False
        assert coupon.applies_to_plan(plan2) is True
    
    def test_coupon_multiple_plans(self):
        """Test coupon that applies to multiple specific plans"""
        plan1 = SubscriptionPlan.objects.create(
            name='Basic',
            base_price=Decimal('9.99'),
            billing_period='monthly'
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Pro',
            base_price=Decimal('29.99'),
            billing_period='monthly'
        )
        plan3 = SubscriptionPlan.objects.create(
            name='Enterprise',
            base_price=Decimal('99.99'),
            billing_period='monthly'
        )
        
        coupon = Coupon.objects.create(
            code='PREMIUM',
            discount_type='percentage',
            discount_value=Decimal('15.00')
        )
        coupon.plans.add(plan2, plan3)
        
        assert coupon.applies_to_plan(plan1) is False
        assert coupon.applies_to_plan(plan2) is True
        assert coupon.applies_to_plan(plan3) is True


@pytest.mark.django_db
class TestCouponDiscountCalculation:
    """Test discount calculation methods"""
    
    def test_percentage_discount_calculation(self):
        """Test percentage discount calculation"""
        coupon = Coupon.objects.create(
            code='SAVE20',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        result = coupon.calculate_discount(Decimal('100.00'))
        
        assert result['original_price'] == Decimal('100.00')
        assert result['discount_amount'] == Decimal('20.00')
        assert result['final_price'] == Decimal('80.00')
        assert result['savings_percentage'] == 20.0
    
    def test_fixed_discount_calculation(self):
        """Test fixed amount discount calculation"""
        coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='fixed',
            discount_value=Decimal('10.00')
        )
        
        result = coupon.calculate_discount(Decimal('50.00'))
        
        assert result['original_price'] == Decimal('50.00')
        assert result['discount_amount'] == Decimal('10.00')
        assert result['final_price'] == Decimal('40.00')
        assert result['savings_percentage'] == 20.0
    
    def test_discount_cannot_be_negative(self):
        """Test that discount cannot make price negative"""
        coupon = Coupon.objects.create(
            code='SAVE100',
            discount_type='fixed',
            discount_value=Decimal('100.00')
        )
        
        result = coupon.calculate_discount(Decimal('50.00'))
        
        assert result['original_price'] == Decimal('50.00')
        assert result['discount_amount'] == Decimal('50.00')  # Capped at original price
        assert result['final_price'] == Decimal('0.00')
        assert result['savings_percentage'] == 100.0
    
    def test_100_percent_discount(self):
        """Test 100% discount makes price zero"""
        coupon = Coupon.objects.create(
            code='FREE',
            discount_type='percentage',
            discount_value=Decimal('100.00')
        )
        
        result = coupon.calculate_discount(Decimal('29.99'))
        
        assert result['final_price'] == Decimal('0.00')
        assert result['savings_percentage'] == 100.0
    
    def test_discount_on_zero_price(self):
        """Test discount calculation on zero price"""
        coupon = Coupon.objects.create(
            code='SAVE20',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        result = coupon.calculate_discount(Decimal('0.00'))
        
        assert result['final_price'] == Decimal('0.00')
        assert result['savings_percentage'] == 0.0
    
    def test_get_discount_display_percentage(self):
        """Test discount display for percentage"""
        coupon = Coupon.objects.create(
            code='SAVE25',
            discount_type='percentage',
            discount_value=Decimal('25.00')
        )
        
        assert coupon.get_discount_display() == '25% off'
    
    def test_get_discount_display_fixed(self):
        """Test discount display for fixed amount"""
        coupon = Coupon.objects.create(
            code='SAVE15',
            discount_type='fixed',
            discount_value=Decimal('15.50')
        )
        
        assert coupon.get_discount_display() == '$15.50 off'


@pytest.mark.django_db
class TestCouponEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_coupon_with_creator(self):
        """Test coupon with creator user"""
        user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        coupon = Coupon.objects.create(
            code='ADMIN123',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            created_by=user
        )
        
        assert coupon.created_by == user
    
    def test_coupon_with_description(self):
        """Test coupon with description"""
        coupon = Coupon.objects.create(
            code='SUMMER2024',
            discount_type='percentage',
            discount_value=Decimal('30.00'),
            description='Summer sale promotion for all users'
        )
        
        assert 'Summer sale' in coupon.description
    
    def test_coupon_valid_characters(self):
        """Test coupon code with valid special characters"""
        coupon = Coupon.objects.create(
            code='SAVE-20_2024',
            discount_type='percentage',
            discount_value=Decimal('20.00')
        )
        
        assert coupon.code == 'SAVE-20_2024'
    
    def test_coupon_deletion(self):
        """Test coupon can be deleted"""
        coupon = Coupon.objects.create(
            code='TEMP',
            discount_type='percentage',
            discount_value=Decimal('10.00')
        )
        
        coupon_id = coupon.id
        coupon.delete()
        
        assert Coupon.objects.filter(id=coupon_id).count() == 0
    
    def test_bulk_create_coupons(self):
        """Test creating multiple coupons at once"""
        coupons = [
            Coupon(
                code=f'BULK{i}',
                discount_type='percentage',
                discount_value=Decimal('10.00')
            )
            for i in range(1, 6)
        ]
        
        # Note: bulk_create bypasses save(), so validation won't happen
        Coupon.objects.bulk_create(coupons)
        
        assert Coupon.objects.filter(code__startswith='BULK').count() == 5
    
    def test_coupon_update(self):
        """Test updating coupon details"""
        coupon = Coupon.objects.create(
            code='UPDATE',
            discount_type='percentage',
            discount_value=Decimal('10.00')
        )
        
        coupon.discount_value = Decimal('20.00')
        coupon.save()
        
        coupon.refresh_from_db()
        assert coupon.discount_value == Decimal('20.00')
    
    def test_coupon_unicode_in_description(self):
        """Test coupon with Unicode characters in description"""
        coupon = Coupon.objects.create(
            code='INTERNATIONAL',
            discount_type='percentage',
            discount_value=Decimal('15.00'),
            description='International sale 🌍 - こんにちは'
        )
        
        assert '🌍' in coupon.description
        assert 'こんにちは' in coupon.description
    
    def test_coupon_max_uses_per_user(self):
        """Test coupon with max uses per user"""
        coupon = Coupon.objects.create(
            code='PERUSER',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_uses_per_user=3
        )
        
        assert coupon.max_uses_per_user == 3
    
    def test_filter_active_coupons(self):
        """Test filtering active coupons"""
        active = Coupon.objects.create(
            code='ACTIVE',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            is_active=True
        )
        inactive = Coupon.objects.create(
            code='INACTIVE',
            discount_type='percentage',
            discount_value=Decimal('15.00'),
            is_active=False
        )
        
        active_coupons = Coupon.objects.filter(is_active=True)
        assert active in active_coupons
        assert inactive not in active_coupons
