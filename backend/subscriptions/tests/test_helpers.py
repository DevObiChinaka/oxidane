"""
Tests for Helper Methods & Utilities

Comprehensive tests for all helper functions including:
- Price calculations
- Date/time utilities
- Validation helpers
- Formatting functions
- Feature access helpers
- Referral calculations
- General utilities
"""

from decimal import Decimal
from datetime import datetime, timedelta
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError

from subscriptions.utils.helpers import (
    # Price calculations
    calculate_price_with_discount,
    calculate_percentage_discount,
    calculate_final_price,
    apply_currency_conversion,
    format_price,
    # Date/time
    calculate_subscription_end_date,
    calculate_days_remaining,
    is_subscription_active,
    is_subscription_expiring_soon,
    get_next_billing_date,
    # Validation
    validate_discount_percentage,
    validate_currency_code,
    validate_telegram_username,
    validate_email_address,
    # Formatting
    format_currency,
    format_date_display,
    format_duration,
    format_billing_cycle,
    # Features
    get_user_features,
    has_feature_access,
    get_feature_status,
    # Referrals
    calculate_referral_commission,
    calculate_referral_discount,
    # Utilities
    generate_unique_code,
    truncate_string,
    safe_decimal,
)


# ============================================================================
# PRICE CALCULATION TESTS
# ============================================================================

class TestPriceCalculations:
    """Test price calculation helpers"""
    
    def test_calculate_price_with_percentage_discount(self):
        """Test percentage discount calculation"""
        result = calculate_price_with_discount(
            Decimal('100'),
            'percentage',
            Decimal('10')
        )
        assert result == Decimal('90.00')
    
    def test_calculate_price_with_fixed_discount(self):
        """Test fixed amount discount calculation"""
        result = calculate_price_with_discount(
            Decimal('100'),
            'fixed_amount',
            Decimal('25')
        )
        assert result == Decimal('75.00')
    
    def test_calculate_price_discount_not_negative(self):
        """Test discount doesn't make price negative"""
        result = calculate_price_with_discount(
            Decimal('50'),
            'fixed_amount',
            Decimal('75')  # Discount larger than price
        )
        assert result == Decimal('0.00')
    
    def test_calculate_price_invalid_discount_type(self):
        """Test invalid discount type raises error"""
        with pytest.raises(ValueError, match="Invalid discount type"):
            calculate_price_with_discount(
                Decimal('100'),
                'invalid_type',
                Decimal('10')
            )
    
    def test_calculate_price_negative_price_raises_error(self):
        """Test negative price raises error"""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_price_with_discount(
                Decimal('-50'),
                'percentage',
                Decimal('10')
            )
    
    def test_calculate_price_percentage_over_100_raises_error(self):
        """Test percentage over 100 raises error"""
        with pytest.raises(ValueError, match="cannot exceed 100%"):
            calculate_price_with_discount(
                Decimal('100'),
                'percentage',
                Decimal('150')
            )
    
    def test_calculate_percentage_discount(self):
        """Test percentage discount calculation"""
        result = calculate_percentage_discount(Decimal('100'), Decimal('15'))
        assert result == Decimal('15.00')
    
    def test_calculate_percentage_discount_fractional(self):
        """Test percentage discount with fractional result"""
        result = calculate_percentage_discount(Decimal('99.99'), Decimal('10'))
        assert result == Decimal('10.00')  # Rounded
    
    def test_calculate_percentage_discount_invalid_range(self):
        """Test invalid percentage range"""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            calculate_percentage_discount(Decimal('100'), Decimal('150'))
    
    def test_calculate_final_price_with_multiple_discounts(self):
        """Test final price with coupon and referral discounts"""
        result = calculate_final_price(
            Decimal('100'),
            coupon_discount=Decimal('20'),
            referral_discount=Decimal('10')
        )
        
        assert result['base_price'] == Decimal('100.00')
        assert result['coupon_discount'] == Decimal('20.00')
        assert result['referral_discount'] == Decimal('10.00')
        assert result['total_discount'] == Decimal('30.00')
        assert result['final_price'] == Decimal('70.00')
        assert result['discount_percentage'] == Decimal('30.00')
    
    def test_calculate_final_price_no_discounts(self):
        """Test final price with no discounts"""
        result = calculate_final_price(Decimal('100'))
        
        assert result['base_price'] == Decimal('100.00')
        assert result['final_price'] == Decimal('100.00')
        assert result['total_discount'] == Decimal('0.00')
        assert result['discount_percentage'] == Decimal('0.00')
    
    def test_calculate_final_price_max_discount_cap(self):
        """Test maximum discount percentage cap"""
        result = calculate_final_price(
            Decimal('100'),
            coupon_discount=Decimal('60'),
            referral_discount=Decimal('50'),
            max_discount_percent=Decimal('80')
        )
        
        # Total discount should be capped at 80%
        assert result['discount_percentage'] == Decimal('80.00')
        assert result['final_price'] == Decimal('20.00')
    
    def test_format_price_usd(self):
        """Test USD price formatting"""
        result = format_price(Decimal('1234.50'), 'USD')
        assert result == '$1,234.50'
    
    def test_format_price_ngn(self):
        """Test NGN price formatting"""
        result = format_price(Decimal('50000'), 'NGN')
        assert result == '₦50,000.00'
    
    def test_format_price_without_symbol(self):
        """Test price formatting without symbol"""
        result = format_price(Decimal('1234.50'), 'USD', include_symbol=False)
        assert result == '1,234.50'


# ============================================================================
# CURRENCY CONVERSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestCurrencyConversion:
    """Test currency conversion helpers"""
    
    def test_apply_currency_conversion_same_currency(self):
        """Test conversion with same currency returns same amount"""
        result = apply_currency_conversion(
            Decimal('100'),
            'USD',
            'USD'
        )
        assert result == Decimal('100')
    
    def test_apply_currency_conversion_with_rate(self):
        """Test conversion with exchange rate"""
        from subscriptions.models import ExchangeRate
        
        # Create exchange rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('411.50')
        )
        
        result = apply_currency_conversion(
            Decimal('100'),
            'USD',
            'NGN'
        )
        
        assert result == Decimal('41150.00')
    
    def test_apply_currency_conversion_no_rate(self):
        """Test conversion without exchange rate returns None"""
        result = apply_currency_conversion(
            Decimal('100'),
            'USD',
            'XYZ'  # Non-existent currency
        )
        assert result is None


# ============================================================================
# DATE AND TIME TESTS
# ============================================================================

class TestDateTimeHelpers:
    """Test date and time helpers"""
    
    def test_calculate_subscription_end_date_monthly(self):
        """Test monthly subscription end date"""
        start = datetime(2025, 1, 1)
        end = calculate_subscription_end_date(start, 'monthly')
        
        # Should be approximately 30 days later
        expected = start + timedelta(days=30)
        assert end == expected
    
    def test_calculate_subscription_end_date_weekly(self):
        """Test weekly subscription end date"""
        start = datetime(2025, 1, 1)
        end = calculate_subscription_end_date(start, 'weekly')
        
        expected = start + timedelta(days=7)
        assert end == expected
    
    def test_calculate_subscription_end_date_yearly(self):
        """Test yearly subscription end date"""
        start = datetime(2025, 1, 1)
        end = calculate_subscription_end_date(start, 'yearly')
        
        expected = start + timedelta(days=365)
        assert end == expected
    
    def test_calculate_subscription_end_date_lifetime(self):
        """Test lifetime subscription returns far future date"""
        start = datetime(2025, 1, 1)
        end = calculate_subscription_end_date(start, 'lifetime')
        
        # Should be 100 years in future (36500 days = approximately 99.9 years)
        assert end.year >= 2124
    
    def test_calculate_subscription_end_date_custom_duration(self):
        """Test custom duration in months"""
        start = datetime(2025, 1, 1)
        end = calculate_subscription_end_date(start, 'monthly', duration_months=3)
        
        # 3 months = 90 days
        expected = start + timedelta(days=90)
        assert end == expected
    
    def test_calculate_subscription_end_date_invalid_cycle(self):
        """Test invalid billing cycle raises error"""
        start = datetime(2025, 1, 1)
        with pytest.raises(ValueError, match="Invalid billing cycle"):
            calculate_subscription_end_date(start, 'invalid_cycle')
    
    def test_calculate_days_remaining_future(self):
        """Test days remaining for future date"""
        end_date = timezone.now() + timedelta(days=10)
        days = calculate_days_remaining(end_date)
        
        assert 9 <= days <= 10  # Allow for slight timing differences
    
    def test_calculate_days_remaining_past(self):
        """Test days remaining for past date returns 0"""
        end_date = timezone.now() - timedelta(days=5)
        days = calculate_days_remaining(end_date)
        
        assert days == 0
    
    def test_calculate_days_remaining_lifetime(self):
        """Test days remaining for lifetime returns -1"""
        end_date = timezone.now() + timedelta(days=36500)  # 100 years
        days = calculate_days_remaining(end_date)
        
        assert days == -1
    
    def test_is_subscription_active_future(self):
        """Test subscription is active when end date in future"""
        end_date = timezone.now() + timedelta(days=10)
        assert is_subscription_active(end_date) is True
    
    def test_is_subscription_active_past(self):
        """Test subscription is inactive when end date in past"""
        end_date = timezone.now() - timedelta(days=5)
        assert is_subscription_active(end_date) is False
    
    def test_is_subscription_active_with_grace_period(self):
        """Test subscription active during grace period"""
        end_date = timezone.now() - timedelta(days=2)
        
        # Without grace period: inactive
        assert is_subscription_active(end_date) is False
        
        # With 3-day grace period: active
        assert is_subscription_active(end_date, grace_period_days=3) is True
    
    def test_is_subscription_expiring_soon(self):
        """Test subscription expiring soon detection"""
        # Expires in 5 days - should be expiring soon (default 7 days)
        end_date = timezone.now() + timedelta(days=5)
        assert is_subscription_expiring_soon(end_date) is True
        
        # Expires in 10 days - not expiring soon
        end_date = timezone.now() + timedelta(days=10)
        assert is_subscription_expiring_soon(end_date) is False
    
    def test_is_subscription_expiring_soon_lifetime(self):
        """Test lifetime subscription not expiring soon"""
        end_date = timezone.now() + timedelta(days=36500)
        assert is_subscription_expiring_soon(end_date) is False
    
    def test_get_next_billing_date(self):
        """Test next billing date calculation"""
        current_end = datetime(2025, 1, 31)
        next_date = get_next_billing_date(current_end, 'monthly')
        
        # Should be approximately 30 days after current end
        expected = current_end + timedelta(days=30)
        assert next_date == expected


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidationHelpers:
    """Test validation helpers"""
    
    def test_validate_discount_percentage_valid(self):
        """Test valid discount percentage"""
        validate_discount_percentage(Decimal('50'))  # Should not raise
        validate_discount_percentage(Decimal('0'))   # Should not raise
        validate_discount_percentage(Decimal('100')) # Should not raise
    
    def test_validate_discount_percentage_negative(self):
        """Test negative discount percentage raises error"""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_discount_percentage(Decimal('-10'))
    
    def test_validate_discount_percentage_over_100(self):
        """Test discount over 100% raises error"""
        with pytest.raises(ValidationError, match="cannot exceed 100%"):
            validate_discount_percentage(Decimal('150'))
    
    def test_validate_currency_code_valid(self):
        """Test valid currency codes"""
        validate_currency_code('USD')  # Should not raise
        validate_currency_code('NGN')  # Should not raise
        validate_currency_code('EUR')  # Should not raise
    
    def test_validate_currency_code_invalid_length(self):
        """Test invalid currency code length"""
        with pytest.raises(ValidationError, match="must be exactly 3 characters"):
            validate_currency_code('US')
        
        with pytest.raises(ValidationError, match="must be exactly 3 characters"):
            validate_currency_code('USDD')
    
    def test_validate_currency_code_invalid_code(self):
        """Test invalid currency code"""
        with pytest.raises(ValidationError, match="Invalid currency code"):
            validate_currency_code('XYZ')
    
    def test_validate_telegram_username_valid(self):
        """Test valid Telegram usernames"""
        validate_telegram_username('@john_doe')       # Should not raise
        validate_telegram_username('john_doe')        # Should not raise
        validate_telegram_username('@user123')        # Should not raise
        validate_telegram_username('user_name_123')   # Should not raise
    
    def test_validate_telegram_username_too_short(self):
        """Test username too short"""
        with pytest.raises(ValidationError, match="at least 5 characters"):
            validate_telegram_username('joe')
    
    def test_validate_telegram_username_too_long(self):
        """Test username too long"""
        long_username = 'a' * 33
        with pytest.raises(ValidationError, match="cannot exceed 32 characters"):
            validate_telegram_username(long_username)
    
    def test_validate_telegram_username_invalid_chars(self):
        """Test username with invalid characters"""
        with pytest.raises(ValidationError, match="must start with a letter"):
            validate_telegram_username('123user')
        
        with pytest.raises(ValidationError, match="letters, numbers, and underscores"):
            validate_telegram_username('user.name')
    
    def test_validate_telegram_username_ends_with_underscore(self):
        """Test username ending with underscore"""
        with pytest.raises(ValidationError, match="cannot end with underscore"):
            validate_telegram_username('username_')
    
    def test_validate_email_address_valid(self):
        """Test valid email addresses"""
        validate_email_address('user@example.com')     # Should not raise
        validate_email_address('test.user@test.co.uk') # Should not raise
        validate_email_address('user+tag@example.com') # Should not raise
    
    def test_validate_email_address_invalid(self):
        """Test invalid email addresses"""
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address('invalid-email')
        
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address('@example.com')
        
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_email_address('user@')


# ============================================================================
# FORMATTING TESTS
# ============================================================================

class TestFormattingHelpers:
    """Test formatting helpers"""
    
    def test_format_currency(self):
        """Test currency formatting"""
        result = format_currency(Decimal('1234.56'), 'USD')
        assert result == '$1,234.56'
    
    def test_format_date_display_short(self):
        """Test short date formatting"""
        dt = datetime(2025, 11, 4, 14, 30)
        result = format_date_display(dt, 'short')
        assert result == '11/04/2025'
    
    def test_format_date_display_long(self):
        """Test long date formatting"""
        dt = datetime(2025, 11, 4, 14, 30)
        result = format_date_display(dt, 'long')
        # Check for the key components (format might have 04 instead of 4)
        assert 'November' in result
        assert '2025' in result
        assert '2:30 PM' in result
    
    def test_format_date_display_relative_days(self):
        """Test relative date formatting (days)"""
        dt = timezone.now() - timedelta(days=3)
        result = format_date_display(dt, 'relative')
        assert '3 days ago' in result
    
    def test_format_date_display_relative_hours(self):
        """Test relative date formatting (hours)"""
        dt = timezone.now() - timedelta(hours=5)
        result = format_date_display(dt, 'relative')
        assert '5 hours ago' in result
    
    def test_format_duration_days(self):
        """Test duration formatting in days"""
        assert format_duration(1) == '1 day'
        assert format_duration(5) == '5 days'
    
    def test_format_duration_weeks(self):
        """Test duration formatting in weeks"""
        assert format_duration(7) == '1 week'
        assert format_duration(14) == '2 weeks'
        assert format_duration(10) == '1 week, 3 days'
    
    def test_format_duration_months(self):
        """Test duration formatting in months"""
        assert format_duration(30) == '1 month'
        assert format_duration(45) == '1 month, 15 days'
    
    def test_format_duration_years(self):
        """Test duration formatting in years"""
        assert format_duration(365) == '1 year'
        assert format_duration(400) == '1 year, 1 month'
    
    def test_format_duration_lifetime(self):
        """Test duration formatting for lifetime"""
        assert format_duration(-1) == 'Lifetime'
    
    def test_format_duration_expired(self):
        """Test duration formatting for expired"""
        assert format_duration(-10) == 'Expired'
    
    def test_format_billing_cycle(self):
        """Test billing cycle formatting"""
        assert format_billing_cycle('monthly') == 'Monthly'
        assert format_billing_cycle('lifetime') == 'One-time (Lifetime Access)'
        assert format_billing_cycle('yearly') == 'Yearly'


# ============================================================================
# FEATURE ACCESS TESTS
# ============================================================================

@pytest.mark.django_db
class TestFeatureAccessHelpers:
    """Test feature access helpers"""
    
    @pytest.fixture
    def setup_user_with_subscription(self, django_user_model):
        """Create user with active subscription"""
        from subscriptions.models import (
            BillingProfile, Feature, SubscriptionPlan, Subscription
        )
        
        # Create user
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create billing profile (use get_or_create to avoid duplicate errors)
        BillingProfile.objects.get_or_create(user=user)
        
        # Create features
        feature1 = Feature.objects.create(
            key='view_premium_signals',
            name='Premium Signals',
            category='signals',
            is_active=True
        )
        feature2 = Feature.objects.create(
            key='telegram_vip_group',
            name='VIP Telegram Group',
            category='telegram',
            is_active=True
        )
        
        # Create plan
        plan = SubscriptionPlan.objects.create(
            name='Premium Plan',
            slug='premium-plan',
            billing_period='monthly',
            base_price=Decimal('99.00'),
            is_active=True
        )
        plan.features.add(feature1, feature2)
        
        # Create active subscription
        subscription = Subscription.objects.create(
            plan=plan,
            billing_profile=user.billing_profile,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('99.00')
        )
        
        return {
            'user': user,
            'plan': plan,
            'subscription': subscription,
            'features': [feature1, feature2]
        }
    
    def test_get_user_features(self, setup_user_with_subscription):
        """Test getting user features"""
        data = setup_user_with_subscription
        features = get_user_features(data['user'])
        
        assert len(features) == 2
        assert 'view_premium_signals' in features
        assert 'telegram_vip_group' in features
    
    def test_has_feature_access_granted(self, setup_user_with_subscription):
        """Test user has feature access"""
        data = setup_user_with_subscription
        assert has_feature_access(data['user'], 'view_premium_signals') is True
    
    def test_has_feature_access_denied(self, setup_user_with_subscription):
        """Test user doesn't have feature access"""
        data = setup_user_with_subscription
        assert has_feature_access(data['user'], 'nonexistent_feature') is False
    
    def test_get_feature_status(self, setup_user_with_subscription):
        """Test getting feature status"""
        data = setup_user_with_subscription
        status = get_feature_status(data['user'])
        
        assert status['total_features'] == 2
        assert len(status['features']) == 2
        assert len(status['active_plans']) == 1
        assert status['active_subscriptions_count'] == 1
        assert 'Premium Plan' in status['active_plans']


# ============================================================================
# REFERRAL CALCULATION TESTS
# ============================================================================

class TestReferralHelpers:
    """Test referral calculation helpers"""
    
    def test_calculate_referral_commission(self):
        """Test referral commission calculation"""
        result = calculate_referral_commission(
            Decimal('100'),
            Decimal('10')
        )
        assert result == Decimal('10.00')
    
    def test_calculate_referral_commission_fractional(self):
        """Test commission with fractional result"""
        result = calculate_referral_commission(
            Decimal('99.99'),
            Decimal('15')
        )
        assert result == Decimal('15.00')  # Rounded
    
    def test_calculate_referral_commission_invalid_percent(self):
        """Test invalid commission percentage"""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            calculate_referral_commission(Decimal('100'), Decimal('150'))
    
    def test_calculate_referral_discount(self):
        """Test referral discount calculation"""
        result = calculate_referral_discount(
            Decimal('100'),
            Decimal('15')
        )
        assert result == Decimal('15.00')


# ============================================================================
# UTILITY HELPER TESTS
# ============================================================================

class TestUtilityHelpers:
    """Test general utility helpers"""
    
    def test_generate_unique_code_default(self):
        """Test unique code generation with defaults"""
        code = generate_unique_code()
        
        assert len(code) == 8
        assert code.isupper()
        assert code.isalnum()
    
    def test_generate_unique_code_with_prefix(self):
        """Test unique code generation with prefix"""
        code = generate_unique_code(prefix='REF-', length=6)
        
        assert code.startswith('REF-')
        assert len(code) == 10  # REF- (4) + 6 random
    
    def test_generate_unique_code_uniqueness(self):
        """Test generated codes are unique"""
        codes = set()
        for _ in range(100):
            codes.add(generate_unique_code())
        
        # All codes should be unique
        assert len(codes) == 100
    
    def test_truncate_string_short(self):
        """Test truncating short string (no change)"""
        text = "Short text"
        result = truncate_string(text, max_length=50)
        assert result == text
    
    def test_truncate_string_long(self):
        """Test truncating long string"""
        text = "This is a very long text that needs to be truncated"
        result = truncate_string(text, max_length=20)
        
        assert len(result) == 20
        assert result.endswith('...')
        assert result.startswith('This is a very')
    
    def test_truncate_string_custom_suffix(self):
        """Test truncating with custom suffix"""
        text = "This is a long text"
        result = truncate_string(text, max_length=15, suffix='…')
        
        assert len(result) == 15
        assert result.endswith('…')
    
    def test_safe_decimal_valid(self):
        """Test safe decimal conversion with valid input"""
        assert safe_decimal('123.45') == Decimal('123.45')
        assert safe_decimal(100) == Decimal('100.00')
        assert safe_decimal(Decimal('50.50')) == Decimal('50.50')
    
    def test_safe_decimal_invalid(self):
        """Test safe decimal conversion with invalid input"""
        assert safe_decimal('invalid') == Decimal('0.00')
        assert safe_decimal(None) == Decimal('0.00')
        assert safe_decimal('') == Decimal('0.00')
    
    def test_safe_decimal_custom_default(self):
        """Test safe decimal with custom default"""
        result = safe_decimal('invalid', default=Decimal('99.99'))
        assert result == Decimal('99.99')


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestHelpersIntegration:
    """Test helper functions working together"""
    
    def test_price_calculation_flow(self):
        """Test complete price calculation flow"""
        # Start with base price
        base_price = Decimal('100.00')
        
        # Apply coupon discount (20% off)
        coupon_discount = calculate_percentage_discount(base_price, Decimal('20'))
        
        # Apply referral discount (10% off original)
        referral_discount = calculate_percentage_discount(base_price, Decimal('10'))
        
        # Calculate final price
        final = calculate_final_price(base_price, coupon_discount, referral_discount)
        
        assert final['base_price'] == Decimal('100.00')
        assert final['coupon_discount'] == Decimal('20.00')
        assert final['referral_discount'] == Decimal('10.00')
        assert final['total_discount'] == Decimal('30.00')
        assert final['final_price'] == Decimal('70.00')
        assert final['discount_percentage'] == Decimal('30.00')
    
    def test_subscription_lifecycle(self):
        """Test subscription date calculations"""
        # Create subscription
        start_date = timezone.now()
        end_date = calculate_subscription_end_date(start_date, 'monthly')
        
        # Check active
        assert is_subscription_active(end_date) is True
        
        # Calculate days remaining
        days = calculate_days_remaining(end_date)
        assert 29 <= days <= 30
        
        # Not expiring soon (30 days remaining)
        assert is_subscription_expiring_soon(end_date, warning_days=7) is False
        
        # Get next billing date
        next_date = get_next_billing_date(end_date, 'monthly')
        assert next_date > end_date
