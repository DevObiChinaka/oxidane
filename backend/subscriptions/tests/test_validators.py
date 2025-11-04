"""
Tests for Custom Django Field Validators

Comprehensive tests for all validator functions in subscriptions/validators.py
"""

from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError

from subscriptions.validators import (
    # Price & Discount Validators
    validate_positive_price,
    validate_non_negative_price,
    validate_discount_percentage_field,
    validate_commission_percentage,
    validate_price_range,
    # Code Format Validators
    validate_coupon_code_format,
    validate_referral_code_format,
    validate_verification_code_format,
    # Telegram Validators
    validate_telegram_chat_id,
    validate_telegram_group_chat_id,
    validate_telegram_username_field,
    validate_telegram_bot_token,
    # Duration Validators
    validate_billing_cycle,
    validate_trial_days,
    validate_subscription_duration_months,
    # Usage Limit Validators
    validate_max_uses,
    validate_current_uses,
    # Currency Validators
    validate_currency_code,
    # Sort Order Validators
    validate_sort_order,
    # Member Count Validators
    validate_member_count,
    validate_max_members,
)


# ============================================================================
# PRICE & DISCOUNT VALIDATOR TESTS
# ============================================================================

class TestPriceValidators:
    """Test price validation functions"""
    
    def test_validate_positive_price_valid(self):
        """Test valid positive prices"""
        validate_positive_price(Decimal('0.01'))
        validate_positive_price(Decimal('99.99'))
        validate_positive_price(Decimal('1000'))
    
    def test_validate_positive_price_zero_fails(self):
        """Test that zero price fails"""
        with pytest.raises(ValidationError, match='must be greater than zero'):
            validate_positive_price(Decimal('0'))
    
    def test_validate_positive_price_negative_fails(self):
        """Test that negative price fails"""
        with pytest.raises(ValidationError, match='must be greater than zero'):
            validate_positive_price(Decimal('-10'))
    
    def test_validate_positive_price_none(self):
        """Test that None is allowed"""
        validate_positive_price(None)  # Should not raise
    
    def test_validate_non_negative_price_valid(self):
        """Test valid non-negative prices"""
        validate_non_negative_price(Decimal('0'))
        validate_non_negative_price(Decimal('0.01'))
        validate_non_negative_price(Decimal('99.99'))
    
    def test_validate_non_negative_price_negative_fails(self):
        """Test that negative price fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_non_negative_price(Decimal('-0.01'))
    
    def test_validate_discount_percentage_field_valid(self):
        """Test valid discount percentages"""
        validate_discount_percentage_field(Decimal('0'))
        validate_discount_percentage_field(Decimal('50'))
        validate_discount_percentage_field(Decimal('100'))
        validate_discount_percentage_field(Decimal('99.99'))
    
    def test_validate_discount_percentage_field_negative_fails(self):
        """Test that negative percentage fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_discount_percentage_field(Decimal('-1'))
    
    def test_validate_discount_percentage_field_over_100_fails(self):
        """Test that percentage over 100 fails"""
        with pytest.raises(ValidationError, match='cannot exceed 100'):
            validate_discount_percentage_field(Decimal('100.01'))
    
    def test_validate_commission_percentage_valid(self):
        """Test valid commission percentages"""
        validate_commission_percentage(Decimal('0'))
        validate_commission_percentage(Decimal('10'))
        validate_commission_percentage(Decimal('25'))
        validate_commission_percentage(Decimal('100'))
    
    def test_validate_commission_percentage_negative_fails(self):
        """Test that negative commission fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_commission_percentage(Decimal('-5'))
    
    def test_validate_commission_percentage_over_100_fails(self):
        """Test that commission over 100% fails"""
        with pytest.raises(ValidationError, match='cannot exceed 100'):
            validate_commission_percentage(Decimal('150'))
    
    def test_validate_price_range_within_range(self):
        """Test price within valid range"""
        validator = validate_price_range(
            min_price=Decimal('10'),
            max_price=Decimal('100')
        )
        validator(Decimal('50'))  # Should not raise
    
    def test_validate_price_range_below_minimum_fails(self):
        """Test price below minimum fails"""
        validator = validate_price_range(min_price=Decimal('10'))
        with pytest.raises(ValidationError, match='must be at least'):
            validator(Decimal('5'))
    
    def test_validate_price_range_above_maximum_fails(self):
        """Test price above maximum fails"""
        validator = validate_price_range(max_price=Decimal('100'))
        with pytest.raises(ValidationError, match='cannot exceed'):
            validator(Decimal('150'))
    
    def test_validate_price_range_no_limits(self):
        """Test price range with no limits"""
        validator = validate_price_range()
        validator(Decimal('999999'))  # Should not raise


# ============================================================================
# CODE FORMAT VALIDATOR TESTS
# ============================================================================

class TestCodeFormatValidators:
    """Test code format validation functions"""
    
    def test_validate_coupon_code_format_valid(self):
        """Test valid coupon codes"""
        validate_coupon_code_format('SAVE20')
        validate_coupon_code_format('SUMMER2024')
        validate_coupon_code_format('NEW-USER')
        validate_coupon_code_format('VIP_MEMBER')
        validate_coupon_code_format('ABC')  # Minimum 3 chars
    
    def test_validate_coupon_code_format_too_short_fails(self):
        """Test coupon code too short fails"""
        with pytest.raises(ValidationError, match='at least 3 characters'):
            validate_coupon_code_format('AB')
    
    def test_validate_coupon_code_format_too_long_fails(self):
        """Test coupon code too long fails"""
        with pytest.raises(ValidationError, match='cannot exceed 50'):
            validate_coupon_code_format('A' * 51)
    
    def test_validate_coupon_code_format_invalid_chars_fails(self):
        """Test coupon code with invalid characters fails"""
        # Note: lowercase is auto-converted to uppercase, so it doesn't fail
        validate_coupon_code_format('save20')  # Gets converted to SAVE20
        
        with pytest.raises(ValidationError, match='uppercase letters, numbers'):
            validate_coupon_code_format('SAVE@20')  # special char
        
        with pytest.raises(ValidationError):
            validate_coupon_code_format('SAVE 20')  # space
    
    def test_validate_referral_code_format_valid(self):
        """Test valid referral codes"""
        validate_referral_code_format('JOHN2024')
        validate_referral_code_format('REFER_ME')
        validate_referral_code_format('ABC')  # Minimum 3 chars
    
    def test_validate_referral_code_format_no_hyphen(self):
        """Test referral code doesn't allow hyphens"""
        with pytest.raises(ValidationError, match='uppercase letters, numbers, and underscores'):
            validate_referral_code_format('REFER-ME')
    
    def test_validate_referral_code_format_too_short_fails(self):
        """Test referral code too short fails"""
        with pytest.raises(ValidationError, match='at least 3 characters'):
            validate_referral_code_format('AB')
    
    def test_validate_verification_code_format_valid(self):
        """Test valid verification codes"""
        validate_verification_code_format('OXI-ABCD')
        validate_verification_code_format('OXI-1234')
        validate_verification_code_format('OXI-A1B2')
    
    def test_validate_verification_code_format_invalid_fails(self):
        """Test invalid verification code formats fail"""
        with pytest.raises(ValidationError, match='OXI-XXXX'):
            validate_verification_code_format('OXI-ABC')  # Too short
        
        with pytest.raises(ValidationError):
            validate_verification_code_format('OXI-ABCDE')  # Too long
        
        with pytest.raises(ValidationError):
            validate_verification_code_format('OXIABCD')  # No dash
        
        with pytest.raises(ValidationError):
            validate_verification_code_format('ABC-1234')  # Wrong prefix


# ============================================================================
# TELEGRAM VALIDATOR TESTS
# ============================================================================

class TestTelegramValidators:
    """Test Telegram validation functions"""
    
    def test_validate_telegram_chat_id_valid(self):
        """Test valid Telegram chat IDs"""
        validate_telegram_chat_id('-1001234567890')  # Group
        validate_telegram_chat_id('123456789')       # User
        validate_telegram_chat_id('-100123')         # Small group
    
    def test_validate_telegram_chat_id_non_numeric_fails(self):
        """Test non-numeric chat ID fails"""
        with pytest.raises(ValidationError, match='must be a numeric value'):
            validate_telegram_chat_id('abc123')
        
        with pytest.raises(ValidationError):
            validate_telegram_chat_id('-100abc')
    
    def test_validate_telegram_chat_id_unusual_length_warns(self):
        """Test unusual length chat ID warns"""
        with pytest.raises(ValidationError, match='unusual'):
            validate_telegram_chat_id('12345')  # Too short
        
        with pytest.raises(ValidationError):
            validate_telegram_chat_id('1' * 16)  # Too long
    
    def test_validate_telegram_group_chat_id_valid(self):
        """Test valid group chat IDs"""
        validate_telegram_group_chat_id('-1001234567890')
    
    def test_validate_telegram_group_chat_id_positive_fails(self):
        """Test positive chat ID fails for group"""
        with pytest.raises(ValidationError, match='must be negative'):
            validate_telegram_group_chat_id('123456789')
    
    def test_validate_telegram_username_field_valid(self):
        """Test valid Telegram usernames"""
        validate_telegram_username_field('john_doe')
        validate_telegram_username_field('JohnDoe123')
        validate_telegram_username_field('user_123_test')
        validate_telegram_username_field('@john_doe')  # With @
    
    def test_validate_telegram_username_field_too_short_fails(self):
        """Test username too short fails"""
        with pytest.raises(ValidationError, match='at least 5 characters'):
            validate_telegram_username_field('john')
    
    def test_validate_telegram_username_field_too_long_fails(self):
        """Test username too long fails"""
        with pytest.raises(ValidationError, match='cannot exceed 32'):
            validate_telegram_username_field('a' * 33)
    
    def test_validate_telegram_username_field_start_with_letter(self):
        """Test username must start with letter"""
        with pytest.raises(ValidationError, match='must start with a letter'):
            validate_telegram_username_field('123john')
    
    def test_validate_telegram_username_field_invalid_chars_fails(self):
        """Test username with invalid characters fails"""
        with pytest.raises(ValidationError, match='letters, numbers, and underscores'):
            validate_telegram_username_field('john-doe')  # hyphen not allowed
        
        with pytest.raises(ValidationError):
            validate_telegram_username_field('john.doe')  # dot not allowed
    
    def test_validate_telegram_username_field_ends_with_underscore_fails(self):
        """Test username ending with underscore fails"""
        with pytest.raises(ValidationError, match='cannot end with an underscore'):
            validate_telegram_username_field('john_')
    
    def test_validate_telegram_bot_token_valid(self):
        """Test valid bot tokens"""
        validate_telegram_bot_token('123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890')
        validate_telegram_bot_token('987654321:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw')
    
    def test_validate_telegram_bot_token_invalid_format_fails(self):
        """Test invalid bot token format fails"""
        with pytest.raises(ValidationError, match='Invalid Telegram bot token'):
            validate_telegram_bot_token('123456789ABC')  # No colon
        
        with pytest.raises(ValidationError):
            validate_telegram_bot_token('ABC:123456789')  # Bot ID not numeric
    
    def test_validate_telegram_bot_token_unusual_length_warns(self):
        """Test unusual length bot token warns"""
        with pytest.raises(ValidationError, match='unusual'):
            validate_telegram_bot_token('123:ABC')  # Token too short


# ============================================================================
# DURATION VALIDATOR TESTS
# ============================================================================

class TestDurationValidators:
    """Test subscription duration validation functions"""
    
    def test_validate_billing_cycle_valid(self):
        """Test valid billing cycles"""
        validate_billing_cycle('weekly')
        validate_billing_cycle('monthly')
        validate_billing_cycle('quarterly')
        validate_billing_cycle('yearly')
        validate_billing_cycle('lifetime')
    
    def test_validate_billing_cycle_invalid_fails(self):
        """Test invalid billing cycle fails"""
        with pytest.raises(ValidationError, match='Invalid billing cycle'):
            validate_billing_cycle('daily')
        
        with pytest.raises(ValidationError):
            validate_billing_cycle('biweekly')
    
    def test_validate_trial_days_valid(self):
        """Test valid trial days"""
        validate_trial_days(0)
        validate_trial_days(7)
        validate_trial_days(30)
        validate_trial_days(365)
    
    def test_validate_trial_days_negative_fails(self):
        """Test negative trial days fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_trial_days(-1)
    
    def test_validate_trial_days_too_long_fails(self):
        """Test trial period over 365 days fails"""
        with pytest.raises(ValidationError, match='cannot exceed 365'):
            validate_trial_days(366)
    
    def test_validate_subscription_duration_months_valid(self):
        """Test valid subscription durations"""
        validate_subscription_duration_months(1)
        validate_subscription_duration_months(12)
        validate_subscription_duration_months(120)  # 10 years max
    
    def test_validate_subscription_duration_months_too_short_fails(self):
        """Test duration less than 1 month fails"""
        with pytest.raises(ValidationError, match='at least 1 month'):
            validate_subscription_duration_months(0)
    
    def test_validate_subscription_duration_months_too_long_fails(self):
        """Test duration over 120 months fails"""
        with pytest.raises(ValidationError, match='cannot exceed 120'):
            validate_subscription_duration_months(121)


# ============================================================================
# USAGE LIMIT VALIDATOR TESTS
# ============================================================================

class TestUsageLimitValidators:
    """Test usage limit validation functions"""
    
    def test_validate_max_uses_valid(self):
        """Test valid max uses"""
        validate_max_uses(1)
        validate_max_uses(100)
        validate_max_uses(1000000)
        validate_max_uses(None)  # Unlimited
    
    def test_validate_max_uses_zero_fails(self):
        """Test max uses of zero fails"""
        with pytest.raises(ValidationError, match='at least 1'):
            validate_max_uses(0)
    
    def test_validate_max_uses_too_high_fails(self):
        """Test max uses over 1 million fails"""
        with pytest.raises(ValidationError, match='cannot exceed'):
            validate_max_uses(1000001)
    
    def test_validate_current_uses_valid(self):
        """Test valid current uses"""
        validate_current_uses(0)
        validate_current_uses(100)
        validate_current_uses(1000000)
    
    def test_validate_current_uses_negative_fails(self):
        """Test negative current uses fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_current_uses(-1)


# ============================================================================
# CURRENCY VALIDATOR TESTS
# ============================================================================

class TestCurrencyValidators:
    """Test currency validation functions"""
    
    def test_validate_currency_code_valid(self):
        """Test valid currency codes"""
        validate_currency_code('USD')
        validate_currency_code('NGN')
        validate_currency_code('EUR')
        validate_currency_code('GBP')
        validate_currency_code('JPY')
    
    def test_validate_currency_code_invalid_length_fails(self):
        """Test invalid length currency code fails"""
        with pytest.raises(ValidationError, match='exactly 3 characters'):
            validate_currency_code('US')
        
        with pytest.raises(ValidationError):
            validate_currency_code('USDT')
    
    def test_validate_currency_code_invalid_format_fails(self):
        """Test invalid format currency code fails"""
        with pytest.raises(ValidationError, match='3 uppercase letters'):
            validate_currency_code('usd')  # lowercase
        
        with pytest.raises(ValidationError):
            validate_currency_code('US1')  # contains digit
    
    def test_validate_currency_code_unsupported_fails(self):
        """Test unsupported currency code fails"""
        with pytest.raises(ValidationError, match='Unsupported currency'):
            validate_currency_code('XYZ')


# ============================================================================
# SORT ORDER VALIDATOR TESTS
# ============================================================================

class TestSortOrderValidators:
    """Test sort order validation functions"""
    
    def test_validate_sort_order_valid(self):
        """Test valid sort orders"""
        validate_sort_order(-1000)
        validate_sort_order(0)
        validate_sort_order(100)
        validate_sort_order(1000)
    
    def test_validate_sort_order_too_low_fails(self):
        """Test sort order below -1000 fails"""
        with pytest.raises(ValidationError, match='cannot be less than -1000'):
            validate_sort_order(-1001)
    
    def test_validate_sort_order_too_high_fails(self):
        """Test sort order above 1000 fails"""
        with pytest.raises(ValidationError, match='cannot exceed 1000'):
            validate_sort_order(1001)


# ============================================================================
# MEMBER COUNT VALIDATOR TESTS
# ============================================================================

class TestMemberCountValidators:
    """Test member count validation functions"""
    
    def test_validate_member_count_valid(self):
        """Test valid member counts"""
        validate_member_count(0)
        validate_member_count(100)
        validate_member_count(200000)  # Telegram max
    
    def test_validate_member_count_negative_fails(self):
        """Test negative member count fails"""
        with pytest.raises(ValidationError, match='cannot be negative'):
            validate_member_count(-1)
    
    def test_validate_member_count_too_high_fails(self):
        """Test member count over 200k fails"""
        with pytest.raises(ValidationError, match='cannot exceed 200,000'):
            validate_member_count(200001)
    
    def test_validate_max_members_valid(self):
        """Test valid max members"""
        validate_max_members(1)
        validate_max_members(1000)
        validate_max_members(200000)
        validate_max_members(None)  # No limit
    
    def test_validate_max_members_zero_fails(self):
        """Test max members of zero fails"""
        with pytest.raises(ValidationError, match='at least 1'):
            validate_max_members(0)
    
    def test_validate_max_members_too_high_fails(self):
        """Test max members over 200k fails"""
        with pytest.raises(ValidationError, match='cannot exceed 200,000'):
            validate_max_members(200001)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestValidatorsIntegration:
    """Test validator integration scenarios"""
    
    def test_discount_and_price_validators_together(self):
        """Test discount and price validators work together"""
        # Valid discount and price
        validate_discount_percentage_field(Decimal('20'))
        validate_positive_price(Decimal('100'))
        
        # Calculate discounted price
        discount_percent = Decimal('20')
        original_price = Decimal('100')
        discount_amount = original_price * (discount_percent / 100)
        final_price = original_price - discount_amount
        
        # Validate final price
        validate_non_negative_price(final_price)
        assert final_price == Decimal('80')
    
    def test_coupon_code_workflow(self):
        """Test complete coupon code validation workflow"""
        code = 'SAVE20'
        discount = Decimal('20')
        
        validate_coupon_code_format(code)
        validate_discount_percentage_field(discount)
        validate_max_uses(100)
        validate_current_uses(0)
    
    def test_referral_code_workflow(self):
        """Test complete referral code validation workflow"""
        code = 'REFER_ME'
        commission = Decimal('10')
        
        validate_referral_code_format(code)
        validate_commission_percentage(commission)
        validate_max_uses(None)  # Unlimited
    
    def test_subscription_plan_workflow(self):
        """Test complete subscription plan validation workflow"""
        billing_cycle = 'monthly'
        price = Decimal('99.99')
        trial = 14
        
        validate_billing_cycle(billing_cycle)
        validate_positive_price(price)
        validate_trial_days(trial)
        validate_currency_code('USD')
    
    def test_telegram_group_workflow(self):
        """Test complete Telegram group validation workflow"""
        chat_id = '-1001234567890'
        members = 5000
        max_members = 10000
        
        validate_telegram_chat_id(chat_id)
        validate_telegram_group_chat_id(chat_id)
        validate_member_count(members)
        validate_max_members(max_members)
        
        assert members < max_members
