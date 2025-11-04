"""
Custom Django Field Validators for Subscription System

Validators designed to be used directly in Django model field definitions.
These validators provide reusable validation logic with clear error messages.

Usage:
    from subscriptions.validators import validate_discount_percentage_field
    
    class MyModel(models.Model):
        discount = models.DecimalField(
            max_digits=5,
            decimal_places=2,
            validators=[validate_discount_percentage_field]
        )
"""

import re
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ============================================================================
# PRICE & DISCOUNT VALIDATORS
# ============================================================================

def validate_positive_price(value):
    """
    Validate that price is positive (greater than zero).
    
    Args:
        value: Decimal price value
        
    Raises:
        ValidationError: If price is not positive
        
    Usage:
        price = models.DecimalField(validators=[validate_positive_price])
    """
    if value is None:
        return
    
    if value <= 0:
        raise ValidationError(
            _('Price must be greater than zero. Got: %(value)s'),
            params={'value': value},
            code='invalid_price'
        )


def validate_non_negative_price(value):
    """
    Validate that price is non-negative (zero or positive).
    
    Args:
        value: Decimal price value
        
    Raises:
        ValidationError: If price is negative
        
    Usage:
        discount_amount = models.DecimalField(validators=[validate_non_negative_price])
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Price cannot be negative. Got: %(value)s'),
            params={'value': value},
            code='negative_price'
        )


def validate_discount_percentage_field(value):
    """
    Validate that discount percentage is between 0 and 100.
    
    Args:
        value: Decimal percentage value
        
    Raises:
        ValidationError: If percentage is out of range
        
    Usage:
        discount_percent = models.DecimalField(
            validators=[validate_discount_percentage_field]
        )
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Discount percentage cannot be negative. Got: %(value)s%%'),
            params={'value': value},
            code='negative_percentage'
        )
    
    if value > 100:
        raise ValidationError(
            _('Discount percentage cannot exceed 100%%. Got: %(value)s%%'),
            params={'value': value},
            code='percentage_too_high'
        )


def validate_commission_percentage(value):
    """
    Validate that commission percentage is between 0 and 100.
    
    Args:
        value: Decimal percentage value
        
    Raises:
        ValidationError: If percentage is out of range
        
    Usage:
        commission_rate = models.DecimalField(
            validators=[validate_commission_percentage]
        )
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Commission percentage cannot be negative. Got: %(value)s%%'),
            params={'value': value},
            code='negative_commission'
        )
    
    if value > 100:
        raise ValidationError(
            _('Commission percentage cannot exceed 100%%. Got: %(value)s%%'),
            params={'value': value},
            code='commission_too_high'
        )


def validate_price_range(min_price=None, max_price=None):
    """
    Create a validator for price range.
    
    Args:
        min_price: Minimum allowed price (optional)
        max_price: Maximum allowed price (optional)
        
    Returns:
        Validator function
        
    Usage:
        price = models.DecimalField(
            validators=[validate_price_range(min_price=Decimal('0.01'), max_price=Decimal('10000'))]
        )
    """
    def validator(value):
        if value is None:
            return
        
        if min_price is not None and value < min_price:
            raise ValidationError(
                _('Price must be at least %(min_price)s. Got: %(value)s'),
                params={'min_price': min_price, 'value': value},
                code='price_too_low'
            )
        
        if max_price is not None and value > max_price:
            raise ValidationError(
                _('Price cannot exceed %(max_price)s. Got: %(value)s'),
                params={'max_price': max_price, 'value': value},
                code='price_too_high'
            )
    
    return validator


# ============================================================================
# CODE FORMAT VALIDATORS
# ============================================================================

def validate_coupon_code_format(value):
    """
    Validate coupon code format (uppercase alphanumeric + underscore/hyphen).
    
    Args:
        value: Coupon code string
        
    Raises:
        ValidationError: If code format is invalid
        
    Usage:
        code = models.CharField(validators=[validate_coupon_code_format])
    """
    if not value:
        return
    
    # Convert to uppercase
    value = value.upper().strip()
    
    # Must be at least 3 characters
    if len(value) < 3:
        raise ValidationError(
            _('Coupon code must be at least 3 characters long. Got: %(length)s'),
            params={'length': len(value)},
            code='code_too_short'
        )
    
    # Must be at most 50 characters
    if len(value) > 50:
        raise ValidationError(
            _('Coupon code cannot exceed 50 characters. Got: %(length)s'),
            params={'length': len(value)},
            code='code_too_long'
        )
    
    # Only uppercase letters, numbers, underscore, hyphen
    if not re.match(r'^[A-Z0-9_-]+$', value):
        raise ValidationError(
            _('Coupon code must contain only uppercase letters, numbers, underscores, and hyphens.'),
            code='invalid_code_format'
        )


def validate_referral_code_format(value):
    """
    Validate referral code format (uppercase alphanumeric + underscore).
    
    Args:
        value: Referral code string
        
    Raises:
        ValidationError: If code format is invalid
        
    Usage:
        code = models.CharField(validators=[validate_referral_code_format])
    """
    if not value:
        return
    
    # Convert to uppercase
    value = value.upper().strip()
    
    # Must be at least 3 characters
    if len(value) < 3:
        raise ValidationError(
            _('Referral code must be at least 3 characters long. Got: %(length)s'),
            params={'length': len(value)},
            code='code_too_short'
        )
    
    # Must be at most 50 characters
    if len(value) > 50:
        raise ValidationError(
            _('Referral code cannot exceed 50 characters. Got: %(length)s'),
            params={'length': len(value)},
            code='code_too_long'
        )
    
    # Only uppercase letters, numbers, underscore (no hyphens for referral codes)
    if not re.match(r'^[A-Z0-9_]+$', value):
        raise ValidationError(
            _('Referral code must contain only uppercase letters, numbers, and underscores.'),
            code='invalid_code_format'
        )


def validate_verification_code_format(value):
    """
    Validate verification code format (OXI-XXXX pattern).
    
    Args:
        value: Verification code string
        
    Raises:
        ValidationError: If code format is invalid
        
    Usage:
        code = models.CharField(validators=[validate_verification_code_format])
    """
    if not value:
        return
    
    # Must match OXI-XXXX pattern (4 alphanumeric chars after prefix)
    if not re.match(r'^OXI-[A-Z0-9]{4}$', value.upper()):
        raise ValidationError(
            _('Verification code must be in format OXI-XXXX (4 alphanumeric characters).'),
            code='invalid_verification_code'
        )


# ============================================================================
# TELEGRAM VALIDATORS
# ============================================================================

def validate_telegram_chat_id(value):
    """
    Validate Telegram chat ID format.
    
    For groups: must start with '-' (negative number)
    For users: must be positive number
    
    Args:
        value: Telegram chat ID string
        
    Raises:
        ValidationError: If chat ID format is invalid
        
    Usage:
        chat_id = models.CharField(validators=[validate_telegram_chat_id])
    """
    if not value:
        return
    
    value = str(value).strip()
    
    # Must be numeric (optionally with leading minus for groups)
    if not re.match(r'^-?\d+$', value):
        raise ValidationError(
            _('Telegram chat ID must be a numeric value (e.g., -1001234567890 for groups).'),
            code='invalid_chat_id'
        )
    
    # Length validation (typical Telegram IDs are 10-13 digits)
    num_digits = len(value.lstrip('-'))
    if num_digits < 6 or num_digits > 15:
        raise ValidationError(
            _('Telegram chat ID length is unusual. Expected 6-15 digits, got %(length)s.'),
            params={'length': num_digits},
            code='unusual_chat_id_length'
        )


def validate_telegram_group_chat_id(value):
    """
    Validate Telegram group chat ID (must be negative).
    
    Args:
        value: Telegram group chat ID string
        
    Raises:
        ValidationError: If chat ID is not for a group
        
    Usage:
        chat_id = models.CharField(validators=[validate_telegram_group_chat_id])
    """
    if not value:
        return
    
    value = str(value).strip()
    
    # First validate basic format
    validate_telegram_chat_id(value)
    
    # Groups must have negative IDs
    if not value.startswith('-'):
        raise ValidationError(
            _('Telegram group chat ID must be negative (start with "-").'),
            code='not_group_chat_id'
        )


def validate_telegram_username_field(value):
    """
    Validate Telegram username format for model fields.
    
    Rules:
    - 5-32 characters
    - Only letters, digits, underscores
    - Must start with letter
    - Cannot end with underscore
    - No @ symbol (stored without @)
    
    Args:
        value: Telegram username string
        
    Raises:
        ValidationError: If username format is invalid
        
    Usage:
        username = models.CharField(validators=[validate_telegram_username_field])
    """
    if not value:
        return
    
    # Remove @ if present
    username = value.lstrip('@').strip()
    
    # Length validation
    if len(username) < 5:
        raise ValidationError(
            _('Telegram username must be at least 5 characters long. Got: %(length)s'),
            params={'length': len(username)},
            code='username_too_short'
        )
    
    if len(username) > 32:
        raise ValidationError(
            _('Telegram username cannot exceed 32 characters. Got: %(length)s'),
            params={'length': len(username)},
            code='username_too_long'
        )
    
    # Must start with letter
    if not username[0].isalpha():
        raise ValidationError(
            _('Telegram username must start with a letter.'),
            code='username_invalid_start'
        )
    
    # Only letters, digits, underscores
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        raise ValidationError(
            _('Telegram username can only contain letters, numbers, and underscores.'),
            code='username_invalid_characters'
        )
    
    # Cannot end with underscore
    if username.endswith('_'):
        raise ValidationError(
            _('Telegram username cannot end with an underscore.'),
            code='username_ends_with_underscore'
        )


def validate_telegram_bot_token(value):
    """
    Validate Telegram bot token format.
    
    Format: <bot_id>:<random_string>
    Example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    
    Args:
        value: Telegram bot token string
        
    Raises:
        ValidationError: If token format is invalid
        
    Usage:
        bot_token = models.CharField(validators=[validate_telegram_bot_token])
    """
    if not value:
        return
    
    # Must match bot token pattern: numbers:alphanumeric_string
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', value):
        raise ValidationError(
            _('Invalid Telegram bot token format. Expected: <bot_id>:<token>'),
            code='invalid_bot_token'
        )
    
    # Split and validate parts
    parts = value.split(':')
    if len(parts) != 2:
        raise ValidationError(
            _('Bot token must contain exactly one colon (:) separator.'),
            code='invalid_bot_token_format'
        )
    
    bot_id, token = parts
    
    # Bot ID should be reasonable length (typically 8-10 digits)
    if len(bot_id) < 8 or len(bot_id) > 12:
        raise ValidationError(
            _('Bot ID length is unusual. Expected 8-12 digits, got %(length)s.'),
            params={'length': len(bot_id)},
            code='unusual_bot_id_length'
        )
    
    # Token should be reasonable length (typically 35-45 characters)
    if len(token) < 30 or len(token) > 50:
        raise ValidationError(
            _('Bot token length is unusual. Expected 30-50 characters, got %(length)s.'),
            params={'length': len(token)},
            code='unusual_token_length'
        )


# ============================================================================
# SUBSCRIPTION DURATION VALIDATORS
# ============================================================================

def validate_billing_cycle(value):
    """
    Validate billing cycle is a supported value.
    
    Args:
        value: Billing cycle string
        
    Raises:
        ValidationError: If billing cycle is invalid
        
    Usage:
        billing_cycle = models.CharField(validators=[validate_billing_cycle])
    """
    if not value:
        return
    
    valid_cycles = ['weekly', 'monthly', 'quarterly', 'yearly', 'lifetime']
    
    if value not in valid_cycles:
        raise ValidationError(
            _('Invalid billing cycle. Must be one of: %(cycles)s. Got: %(value)s'),
            params={'cycles': ', '.join(valid_cycles), 'value': value},
            code='invalid_billing_cycle'
        )


def validate_trial_days(value):
    """
    Validate trial period is reasonable (0-365 days).
    
    Args:
        value: Number of trial days
        
    Raises:
        ValidationError: If trial period is invalid
        
    Usage:
        trial_days = models.IntegerField(validators=[validate_trial_days])
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Trial days cannot be negative. Got: %(value)s'),
            params={'value': value},
            code='negative_trial_days'
        )
    
    if value > 365:
        raise ValidationError(
            _('Trial period cannot exceed 365 days. Got: %(value)s'),
            params={'value': value},
            code='trial_too_long'
        )


def validate_subscription_duration_months(value):
    """
    Validate subscription duration in months (1-120 months / 10 years).
    
    Args:
        value: Number of months
        
    Raises:
        ValidationError: If duration is invalid
        
    Usage:
        duration_months = models.IntegerField(
            validators=[validate_subscription_duration_months]
        )
    """
    if value is None:
        return
    
    if value < 1:
        raise ValidationError(
            _('Subscription duration must be at least 1 month. Got: %(value)s'),
            params={'value': value},
            code='duration_too_short'
        )
    
    if value > 120:  # 10 years max
        raise ValidationError(
            _('Subscription duration cannot exceed 120 months (10 years). Got: %(value)s'),
            params={'value': value},
            code='duration_too_long'
        )


# ============================================================================
# USAGE LIMIT VALIDATORS
# ============================================================================

def validate_max_uses(value):
    """
    Validate maximum usage limit is reasonable.
    
    Args:
        value: Maximum number of uses
        
    Raises:
        ValidationError: If max uses is invalid
        
    Usage:
        max_uses = models.IntegerField(
            validators=[validate_max_uses],
            null=True,
            blank=True
        )
    """
    if value is None:  # Null means unlimited
        return
    
    if value < 1:
        raise ValidationError(
            _('Maximum uses must be at least 1. Got: %(value)s'),
            params={'value': value},
            code='max_uses_too_low'
        )
    
    if value > 1000000:
        raise ValidationError(
            _('Maximum uses cannot exceed 1,000,000. Got: %(value)s'),
            params={'value': value},
            code='max_uses_too_high'
        )


def validate_current_uses(value):
    """
    Validate current usage count is non-negative.
    
    Args:
        value: Current number of uses
        
    Raises:
        ValidationError: If current uses is negative
        
    Usage:
        current_uses = models.IntegerField(validators=[validate_current_uses])
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Current uses cannot be negative. Got: %(value)s'),
            params={'value': value},
            code='negative_uses'
        )


# ============================================================================
# CURRENCY VALIDATORS
# ============================================================================

def validate_currency_code(value):
    """
    Validate currency code is a supported 3-letter ISO code.
    
    Args:
        value: Currency code string
        
    Raises:
        ValidationError: If currency code is invalid
        
    Usage:
        currency = models.CharField(validators=[validate_currency_code])
    """
    if not value:
        return
    
    # Must be 3 characters
    if len(value) != 3:
        raise ValidationError(
            _('Currency code must be exactly 3 characters. Got: %(length)s'),
            params={'length': len(value)},
            code='invalid_currency_length'
        )
    
    # Must be uppercase letters only
    if not value.isupper() or not value.isalpha():
        raise ValidationError(
            _('Currency code must be 3 uppercase letters.'),
            code='invalid_currency_format'
        )
    
    # Check against supported currencies
    supported_currencies = ['USD', 'NGN', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY', 'INR']
    
    if value not in supported_currencies:
        raise ValidationError(
            _('Unsupported currency code. Supported: %(codes)s. Got: %(value)s'),
            params={'codes': ', '.join(supported_currencies), 'value': value},
            code='unsupported_currency'
        )


# ============================================================================
# SORT ORDER VALIDATORS
# ============================================================================

def validate_sort_order(value):
    """
    Validate sort order is reasonable (-1000 to 1000).
    
    Args:
        value: Sort order integer
        
    Raises:
        ValidationError: If sort order is out of range
        
    Usage:
        sort_order = models.IntegerField(validators=[validate_sort_order])
    """
    if value is None:
        return
    
    if value < -1000:
        raise ValidationError(
            _('Sort order cannot be less than -1000. Got: %(value)s'),
            params={'value': value},
            code='sort_order_too_low'
        )
    
    if value > 1000:
        raise ValidationError(
            _('Sort order cannot exceed 1000. Got: %(value)s'),
            params={'value': value},
            code='sort_order_too_high'
        )


# ============================================================================
# MEMBER COUNT VALIDATORS
# ============================================================================

def validate_member_count(value):
    """
    Validate member count is non-negative and reasonable.
    
    Args:
        value: Number of members
        
    Raises:
        ValidationError: If member count is invalid
        
    Usage:
        member_count = models.IntegerField(validators=[validate_member_count])
    """
    if value is None:
        return
    
    if value < 0:
        raise ValidationError(
            _('Member count cannot be negative. Got: %(value)s'),
            params={'value': value},
            code='negative_member_count'
        )
    
    if value > 200000:  # Telegram max for groups
        raise ValidationError(
            _('Member count cannot exceed 200,000 (Telegram limit). Got: %(value)s'),
            params={'value': value},
            code='member_count_too_high'
        )


def validate_max_members(value):
    """
    Validate maximum members is reasonable.
    
    Args:
        value: Maximum number of members
        
    Raises:
        ValidationError: If max members is invalid
        
    Usage:
        max_members = models.IntegerField(
            validators=[validate_max_members],
            null=True,
            blank=True
        )
    """
    if value is None:  # Null means no limit
        return
    
    if value < 1:
        raise ValidationError(
            _('Maximum members must be at least 1. Got: %(value)s'),
            params={'value': value},
            code='max_members_too_low'
        )
    
    if value > 200000:  # Telegram max for groups
        raise ValidationError(
            _('Maximum members cannot exceed 200,000 (Telegram limit). Got: %(value)s'),
            params={'value': value},
            code='max_members_too_high'
        )
