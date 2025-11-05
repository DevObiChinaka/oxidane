"""
Comprehensive tests for Referral and ReferralCredit models (Discount System).

This test suite covers the discount-only referral system where:
- Referees get 10% discount immediately on signup
- Referrers earn 5% discount credits for every 10 successful referrals
- Credits are single-use (cannot be stacked)
- Credits can be used on multiple subscriptions (one at a time)
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import (
    ReferralCode, Referral, ReferralCredit,
    Subscription, SubscriptionPlan, BillingProfile
)

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def referrer_user(db):
    """Create a user who will be the referrer."""
    return User.objects.create_user(
        username='referrer',
        email='referrer@example.com',
        password='testpass123'
    )


@pytest.fixture
def referee_user(db):
    """Create a user who will be the referee."""
    return User.objects.create_user(
        username='referee',
        email='referee@example.com',
        password='testpass123'
    )


@pytest.fixture
def referral_code(db, referrer_user):
    """Create an active referral code."""
    return ReferralCode.objects.create(
        code='TEST2024',
        referrer=referrer_user,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('5.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00'),
        is_active=True
    )


@pytest.fixture
def billing_profile(db, referee_user):
    """Create a billing profile for a user."""
    profile, _ = BillingProfile.objects.get_or_create(
        user=referee_user
    )
    return profile


# DEPRECATED: PricingPlan removed in Phase 0.5, replaced by SubscriptionPlan
# @pytest.fixture
# def pricing_plan_old(db):
#     """Create an old PricingPlan for Subscription."""
#     from subscriptions.models import PricingPlan
#     return PricingPlan.objects.create(
#         name='Basic Plan',
#         description='Basic subscription plan',
#         duration_days=30,
#         price=Decimal('100.00'),
#         is_active=True
#     )


@pytest.fixture
def subscription_plan(db):
    """Create a SubscriptionPlan for Phase 0.5"""
    return SubscriptionPlan.objects.create(
        name='Basic Plan',
        base_price=Decimal('100.00'),
        billing_period='monthly',
        is_active=True
    )


@pytest.fixture
def subscription(db, referee_user, billing_profile, subscription_plan):
    """Create a subscription for a referee using Phase 0.5 Subscription model."""
    from django.utils import timezone
    from datetime import timedelta
    
    return Subscription.objects.create(
        billing_profile=billing_profile,
        plan=subscription_plan,
        status='active',
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        amount_paid=Decimal('90.00'),  # After 10% discount
        currency='USD'
    )


# ============================================================================
# TEST REFERRAL MODEL - BASIC CRUD
# ============================================================================

@pytest.mark.django_db
class TestReferralBasicOperations:
    """Test basic Referral model operations."""
    
    def test_create_referral_success(self, referral_code, referrer_user, referee_user, subscription):
        """Test creating a referral with all required fields."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            subscription=subscription,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('10.00'),
            referee_discount_amount=Decimal('10.00'),
            final_amount=Decimal('90.00'),
            status='completed'
        )
        
        assert referral.id is not None
        assert referral.referrer == referrer_user
        assert referral.referee == referee_user
        assert referral.status == 'completed'
        assert referral.currency == 'USD'  # Default
        
    def test_referral_string_representation(self, referral_code, referrer_user, referee_user):
        """Test the __str__ method of Referral."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        
        str_repr = str(referral)
        assert 'referrer' in str_repr.lower() or 'referee' in str_repr.lower()
        
    def test_referral_default_values(self, referral_code, referrer_user, referee_user):
        """Test that referral has correct default values."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        assert referral.referee_discount_percent == Decimal('10.00')
        assert referral.referee_discount_amount == Decimal('10.00')  # Auto-calculated: 10% of 100
        assert referral.final_amount == Decimal('90.00')  # Auto-calculated: 100 - 10
        assert referral.status == 'completed'
        assert referral.currency == 'USD'
        assert referral.conversion_date is not None
        
    def test_referral_ordering(self, referral_code, referrer_user, referee_user):
        """Test that referrals are ordered by conversion_date descending."""
        # Create referrals at different times
        ref1 = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        # Create another user for second referral
        referee2 = User.objects.create_user(
            username='referee2',
            email='referee2@example.com',
            password='testpass123'
        )
        
        ref2 = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee2,
            original_amount=Decimal('100.00')
        )
        
        referrals = list(Referral.objects.all())
        # Most recent should be first
        assert referrals[0].id == ref2.id
        assert referrals[1].id == ref1.id


# ============================================================================
# TEST REFERRAL MODEL - VALIDATION
# ============================================================================

@pytest.mark.django_db
class TestReferralValidation:
    """Test Referral model validation logic."""
    
    def test_referrer_cannot_refer_self(self, referral_code, referrer_user):
        """Test that a user cannot refer themselves."""
        referral = Referral(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referrer_user,  # Same as referrer!
            original_amount=Decimal('100.00')
        )
        
        with pytest.raises(ValidationError, match='self-referral not allowed'):
            referral.clean()
            
    def test_negative_original_amount_fails(self, referral_code, referrer_user, referee_user):
        """Test that negative original_amount is rejected."""
        referral = Referral(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('-100.00')
        )
        
        with pytest.raises(ValidationError, match='Original amount cannot be negative'):
            referral.clean()
            
    def test_negative_final_amount_fails(self, referral_code, referrer_user, referee_user):
        """Test that negative final_amount is rejected."""
        referral = Referral(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            final_amount=Decimal('-10.00')
        )
        
        with pytest.raises(ValidationError, match='Final amount cannot be negative'):
            referral.clean()
            
    def test_final_amount_exceeds_original_fails(self, referral_code, referrer_user, referee_user):
        """Test that final_amount cannot exceed original_amount."""
        referral = Referral(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            final_amount=Decimal('150.00')  # More than original!
        )
        
        with pytest.raises(ValidationError, match='cannot be greater than original amount'):
            referral.clean()
            
    def test_invalid_discount_percent_fails(self, referral_code, referrer_user, referee_user):
        """Test that discount_percent must be 0-100."""
        referral = Referral(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('150.00')  # Over 100%!
        )
        
        with pytest.raises(ValidationError, match='must be between 0 and 100'):
            referral.clean()
            
    def test_referrer_must_own_referral_code(self, referral_code, referrer_user, referee_user):
        """Test that referrer must be the owner of the referral code."""
        # Create another user who doesn't own the code
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        referral = Referral(
            referral_code=referral_code,
            referrer=other_user,  # Doesn't own TEST2024!
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        with pytest.raises(ValidationError, match='must be the owner of the referral code'):
            referral.clean()


# ============================================================================
# TEST REFERRAL MODEL - DISCOUNT CALCULATIONS
# ============================================================================

@pytest.mark.django_db
class TestReferralDiscountCalculations:
    """Test discount calculation logic."""
    
    def test_auto_calculate_discount_on_save(self, referral_code, referrer_user, referee_user):
        """Test that discount amounts are auto-calculated on save."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('10.00')
        )
        
        # Should auto-calculate
        assert referral.referee_discount_amount == Decimal('10.00')
        assert referral.final_amount == Decimal('90.00')
        
    def test_discount_calculation_different_percent(self, referral_code, referrer_user, referee_user):
        """Test discount calculation with different percentage."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('200.00'),
            referee_discount_percent=Decimal('15.00')  # 15% discount
        )
        
        assert referral.referee_discount_amount == Decimal('30.00')
        assert referral.final_amount == Decimal('170.00')
        
    def test_discount_calculation_fractional_amount(self, referral_code, referrer_user, referee_user):
        """Test discount calculation with fractional results."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('99.99'),
            referee_discount_percent=Decimal('10.00')
        )
        
        # Should round to 2 decimal places: 10% of 99.99 = 9.999 → 10.00
        expected_discount = Decimal('10.00')  # Rounded from 9.999
        assert referral.referee_discount_amount == expected_discount
        assert referral.final_amount == Decimal('89.99')  # 99.99 - 10.00
        
    def test_zero_discount_calculation(self, referral_code, referrer_user, referee_user):
        """Test calculation when discount is 0%."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('0.00')
        )
        
        assert referral.referee_discount_amount == Decimal('0.00')
        assert referral.final_amount == Decimal('100.00')
        
    def test_full_discount_calculation(self, referral_code, referrer_user, referee_user):
        """Test calculation when discount is 100%."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            referee_discount_percent=Decimal('100.00')
        )
        
        assert referral.referee_discount_amount == Decimal('100.00')
        assert referral.final_amount == Decimal('0.00')


# ============================================================================
# TEST REFERRAL MODEL - STATUS MANAGEMENT
# ============================================================================

@pytest.mark.django_db
class TestReferralStatusManagement:
    """Test referral status transitions and management."""
    
    def test_default_status_is_completed(self, referral_code, referrer_user, referee_user):
        """Test that new referrals default to 'completed' status."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        assert referral.status == 'completed'
        
    def test_mark_as_cancelled(self, referral_code, referrer_user, referee_user):
        """Test marking a referral as cancelled."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        
        referral.mark_as_cancelled('Fraudulent signup')
        
        assert referral.status == 'cancelled'
        assert referral.cancelled_date is not None
        assert 'Fraudulent signup' in referral.notes
        
    def test_get_status_display_color(self, referral_code, referrer_user, referee_user):
        """Test status color coding."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            status='completed'
        )
        
        assert referral.get_status_display_color() == '#28a745'  # Green
        
        referral.mark_as_cancelled('Test')
        assert referral.get_status_display_color() == '#dc3545'  # Red
        
    def test_cancelled_referral_has_timestamp(self, referral_code, referrer_user, referee_user):
        """Test that cancelled referrals have cancelled_date set."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        assert referral.cancelled_date is None
        
        referral.mark_as_cancelled('Testing')
        assert referral.cancelled_date is not None
        assert isinstance(referral.cancelled_date, timezone.datetime)


# ============================================================================
# TEST REFERRAL CREDIT AWARDING
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditAwarding:
    """Test the logic for awarding 5% credits every 10 referrals."""
    
    def test_no_credit_before_10_referrals(self, referral_code, referrer_user):
        """Test that no credit is awarded before 10 completed referrals."""
        # Create 9 referrals
        for i in range(9):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # Should have no credits yet
        credits = ReferralCredit.objects.filter(user=referrer_user)
        assert credits.count() == 0
        
    def test_credit_awarded_at_10_referrals(self, referral_code, referrer_user):
        """Test that a credit is awarded at exactly 10 completed referrals."""
        # Create 10 referrals
        for i in range(10):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # Should have 1 credit now
        credits = ReferralCredit.objects.filter(user=referrer_user)
        assert credits.count() == 1
        
        credit = credits.first()
        assert credit.credit_percentage == Decimal('5.00')
        assert credit.is_used == False
        
    def test_multiple_credits_awarded(self, referral_code, referrer_user):
        """Test that multiple credits are awarded for multiples of 10."""
        # Create 25 referrals
        for i in range(25):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # Should have 2 credits (at 10 and 20 referrals)
        credits = ReferralCredit.objects.filter(user=referrer_user)
        assert credits.count() == 2
        
    def test_cancelled_referrals_dont_count(self, referral_code, referrer_user):
        """Test that cancelled referrals don't count toward credit awarding."""
        # Create 5 completed and 5 cancelled referrals
        for i in range(10):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            referral = Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
            
            # Cancel half of them
            if i >= 5:
                referral.mark_as_cancelled('Test')
        
        # Should have no credits (only 5 completed referrals)
        credits = ReferralCredit.objects.filter(user=referrer_user)
        assert credits.count() == 0
        
    def test_credit_links_to_triggering_referral(self, referral_code, referrer_user):
        """Test that credit is linked to the 10th referral."""
        # Create 10 referrals
        for i in range(10):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            referral = Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # Get the credit
        credit = ReferralCredit.objects.filter(user=referrer_user).first()
        assert credit is not None
        assert credit.earned_from_referral is not None
        assert credit.earned_from_referral.referrer == referrer_user
        
    def test_no_duplicate_credits_for_same_milestone(self, referral_code, referrer_user):
        """Test that the same milestone doesn't award multiple credits."""
        # Create 10 referrals
        for i in range(10):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00'),
                status='completed'
            )
        
        # Re-save an existing referral (shouldn't create duplicate credit)
        referral = Referral.objects.filter(referrer=referrer_user).first()
        referral.notes = 'Updated'
        referral.save()
        
        # Should still have only 1 credit
        credits = ReferralCredit.objects.filter(user=referrer_user)
        assert credits.count() == 1


# ============================================================================
# TEST REFERRAL CREDIT MODEL - BASIC OPERATIONS
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditBasicOperations:
    """Test basic ReferralCredit model operations."""
    
    def test_create_referral_credit(self, referrer_user, referral_code, referee_user):
        """Test creating a referral credit."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            credit_percentage=Decimal('5.00'),
            earned_from_referral=referral
        )
        
        assert credit.id is not None
        assert credit.user == referrer_user
        assert credit.credit_percentage == Decimal('5.00')
        assert credit.is_used == False
        
    def test_referral_credit_string_representation(self, referrer_user, referral_code, referee_user):
        """Test the __str__ method of ReferralCredit."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            credit_percentage=Decimal('5.00'),
            earned_from_referral=referral
        )
        
        str_repr = str(credit)
        assert len(str_repr) > 0  # Just ensure it doesn't crash
        
    def test_referral_credit_default_values(self, referrer_user, referral_code, referee_user):
        """Test that credit has correct default values."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        assert credit.credit_percentage == Decimal('5.00')
        assert credit.is_used == False
        assert credit.used_on_subscription is None
        assert credit.used_date is None
        assert credit.expires_at is None
        assert credit.earned_date is not None
        
    def test_referral_credit_ordering(self, referrer_user, referral_code, referee_user):
        """Test that credits are ordered by earned_date descending."""
        # Create two referrals and credits
        ref1 = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        credit1 = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=ref1
        )
        
        referee2 = User.objects.create_user(
            username='referee2',
            email='referee2@example.com',
            password='testpass123'
        )
        ref2 = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee2,
            original_amount=Decimal('100.00')
        )
        credit2 = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=ref2
        )
        
        credits = list(ReferralCredit.objects.all())
        # Most recent should be first
        assert credits[0].id == credit2.id
        assert credits[1].id == credit1.id


# ============================================================================
# TEST REFERRAL CREDIT - VALIDATION
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditValidation:
    """Test ReferralCredit model validation logic."""
    
    def test_invalid_credit_percentage_fails(self, referrer_user, referral_code, referee_user):
        """Test that credit_percentage must be 0-100."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit(
            user=referrer_user,
            credit_percentage=Decimal('150.00'),  # Over 100%!
            earned_from_referral=referral
        )
        
        with pytest.raises(ValidationError, match='must be between 0 and 100'):
            credit.clean()
            
    def test_used_credit_must_have_subscription(self, referrer_user, referral_code, referee_user):
        """Test that used credits must have a subscription."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit(
            user=referrer_user,
            earned_from_referral=referral,
            is_used=True,
            used_on_subscription=None  # Missing!
        )
        
        with pytest.raises(ValidationError, match='must have an associated subscription'):
            credit.clean()
            
    def test_used_credit_must_have_used_date(self, referrer_user, referral_code, referee_user, subscription):
        """Test that used credits must have a used_date."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit(
            user=referrer_user,
            earned_from_referral=referral,
            is_used=True,
            used_on_subscription=subscription,
            used_date=None  # Missing!
        )
        
        with pytest.raises(ValidationError, match='must have a used date'):
            credit.clean()
            
    def test_expires_at_must_be_after_earned_date(self, referrer_user, referral_code, referee_user):
        """Test that expires_at must be after earned_date."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        # Try to set expiry date before earned date
        credit.expires_at = credit.earned_date - timedelta(days=1)
        
        with pytest.raises(ValidationError, match='cannot be before earned date'):
            credit.clean()


# ============================================================================
# TEST REFERRAL CREDIT - USAGE
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditUsage:
    """Test credit usage and redemption logic."""
    
    def test_use_credit_success(self, referrer_user, referral_code, referee_user, subscription):
        """Test successfully using a credit."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        discount_percent = credit.use_credit(subscription)
        
        assert discount_percent == Decimal('5.00')
        assert credit.is_used == True
        assert credit.used_on_subscription == subscription
        assert credit.used_date is not None
        
    def test_cannot_reuse_credit(self, referrer_user, referral_code, referee_user, subscription):
        """Test that a credit cannot be used twice."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        # Use it once
        credit.use_credit(subscription)
        
        # Try to use it again
        with pytest.raises(ValidationError, match='already been used'):
            credit.use_credit(subscription)
            
    def test_cannot_use_expired_credit(self, referrer_user, referral_code, referee_user, subscription):
        """Test that expired credits cannot be used."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral,
            expires_at=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        with pytest.raises(ValidationError, match='expired'):
            credit.use_credit(subscription)
            
    def test_using_credit_updates_all_fields(self, referrer_user, referral_code, referee_user, subscription):
        """Test that using a credit updates all relevant fields."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        assert credit.is_used == False
        assert credit.used_on_subscription is None
        assert credit.used_date is None
        
        credit.use_credit(subscription)
        
        assert credit.is_used == True
        assert credit.used_on_subscription == subscription
        assert credit.used_date is not None
        assert isinstance(credit.used_date, timezone.datetime)


# ============================================================================
# TEST REFERRAL CREDIT - EXPIRATION
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditExpiration:
    """Test credit expiration logic."""
    
    def test_credit_without_expiry_not_expired(self, referrer_user, referral_code, referee_user):
        """Test that credits without expiry never expire."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral,
            expires_at=None
        )
        
        assert credit.is_expired() == False
        
    def test_credit_expired_when_past_expiry(self, referrer_user, referral_code, referee_user):
        """Test that credits are expired when past expiry date."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        assert credit.is_expired() == True
        
    def test_credit_not_expired_before_expiry(self, referrer_user, referral_code, referee_user):
        """Test that credits are not expired before expiry date."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        assert credit.is_expired() == False
        
    def test_used_credit_reported_as_unavailable(self, referrer_user, referral_code, referee_user, subscription):
        """Test that used credits are not available."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00')
        )
        
        credit = ReferralCredit.objects.create(
            user=referrer_user,
            earned_from_referral=referral
        )
        
        assert credit.is_available() == True
        
        credit.use_credit(subscription)
        
        assert credit.is_available() == False


# ============================================================================
# TEST REFERRAL CREDIT - AVAILABILITY
# ============================================================================

@pytest.mark.django_db
class TestReferralCreditAvailability:
    """Test querying for available credits."""
    
    def test_filter_available_credits(self, referrer_user, referral_code, referee_user):
        """Test filtering for available (unused, unexpired) credits."""
        # Create 3 credits with different states
        for i in range(3):
            ref_user = User.objects.create_user(
                username=f'ref{i}',
                email=f'ref{i}@example.com',
                password='testpass123'
            )
            referral = Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=ref_user,
                original_amount=Decimal('100.00')
            )
            
            if i == 0:
                # Available credit
                ReferralCredit.objects.create(
                    user=referrer_user,
                    earned_from_referral=referral
                )
            elif i == 1:
                # Used credit - need subscription fixture
                from datetime import timedelta
                
                # Create billing profile
                billing_prof, _ = BillingProfile.objects.get_or_create(
                    user=referrer_user
                )
                
                # Create subscription plan (Phase 0.5)
                subscription_plan = SubscriptionPlan.objects.create(
                    name='Test Plan',
                    base_price=Decimal('100.00'),
                    billing_period='monthly',
                    is_active=True
                )
                
                # Create subscription
                subscription = Subscription.objects.create(
                    billing_profile=billing_prof,
                    plan=subscription_plan,
                    status='active',
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                    amount_paid=Decimal('95.00'),  # After 5% credit
                    currency='USD'
                )
                
                credit = ReferralCredit.objects.create(
                    user=referrer_user,
                    earned_from_referral=referral,
                    is_used=True,
                    used_on_subscription=subscription,
                    used_date=timezone.now()
                )
            else:
                # Expired credit
                ReferralCredit.objects.create(
                    user=referrer_user,
                    earned_from_referral=referral,
                    expires_at=timezone.now() - timedelta(days=1)
                )
        
        # Query available credits
        available = ReferralCredit.objects.filter(
            user=referrer_user,
            is_used=False
        ).exclude(
            expires_at__lt=timezone.now()
        )
        
        assert available.count() == 1
        
    def test_order_available_credits_by_earned_date(self, referrer_user, referral_code):
        """Test that available credits can be ordered by earned date."""
        # Create multiple available credits
        for i in range(3):
            ref_user = User.objects.create_user(
                username=f'ref{i}',
                email=f'ref{i}@example.com',
                password='testpass123'
            )
            referral = Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=ref_user,
                original_amount=Decimal('100.00')
            )
            ReferralCredit.objects.create(
                user=referrer_user,
                earned_from_referral=referral
            )
        
        # Get oldest first
        credits = ReferralCredit.objects.filter(
            user=referrer_user,
            is_used=False
        ).order_by('earned_date')
        
        assert credits.count() == 3
        # First should be oldest
        assert credits[0].earned_date <= credits[1].earned_date
        assert credits[1].earned_date <= credits[2].earned_date


# ============================================================================
# TEST EDGE CASES
# ============================================================================

@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_referral_with_zero_amount(self, referral_code, referrer_user, referee_user):
        """Test creating a referral with zero amount."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('0.00'),
            referee_discount_percent=Decimal('10.00')
        )
        
        assert referral.referee_discount_amount == Decimal('0.00')
        assert referral.final_amount == Decimal('0.00')
        
    def test_referral_with_null_subscription(self, referral_code, referrer_user, referee_user):
        """Test that referral can exist without subscription."""
        referral = Referral.objects.create(
            referral_code=referral_code,
            referrer=referrer_user,
            referee=referee_user,
            original_amount=Decimal('100.00'),
            subscription=None
        )
        
        assert referral.subscription is None
        assert referral.id is not None
        
    def test_multiple_users_with_same_referral_code(self, referral_code, referrer_user):
        """Test that multiple different users can use the same referral code."""
        referees = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            referees.append(user)
            
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=user,
                original_amount=Decimal('100.00')
            )
        
        referrals = Referral.objects.filter(referral_code=referral_code)
        assert referrals.count() == 3
        
    def test_user_can_have_multiple_unused_credits(self, referrer_user, referral_code):
        """Test that a user can accumulate multiple unused credits."""
        # Create 20 referrals (should award 2 credits)
        for i in range(20):
            referee = User.objects.create_user(
                username=f'referee{i}',
                email=f'referee{i}@example.com',
                password='testpass123'
            )
            Referral.objects.create(
                referral_code=referral_code,
                referrer=referrer_user,
                referee=referee,
                original_amount=Decimal('100.00')
            )
        
        unused_credits = ReferralCredit.objects.filter(
            user=referrer_user,
            is_used=False
        )
        
        assert unused_credits.count() == 2
