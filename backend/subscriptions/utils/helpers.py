"""
Helper Methods & Utilities for Subscription System

Common utility functions used across the subscription system including:
- Price calculations and currency formatting
- Date/time utilities for subscriptions
- Validation helpers
- Feature access utilities
- Referral calculations
- General formatting helpers
"""

import re
import random
import string
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings


# ============================================================================
# PRICE CALCULATION HELPERS
# ============================================================================

def calculate_price_with_discount(
    original_price: Decimal,
    discount_type: str,
    discount_value: Decimal
) -> Decimal:
    """
    Calculate final price after applying discount.
    
    Args:
        original_price: Original price before discount
        discount_type: 'percentage' or 'fixed_amount'
        discount_value: Discount amount (e.g., 10 for 10% or $10)
        
    Returns:
        Final price after discount (never negative)
        
    Example:
        >>> calculate_price_with_discount(Decimal('100'), 'percentage', Decimal('10'))
        Decimal('90.00')
        >>> calculate_price_with_discount(Decimal('100'), 'fixed_amount', Decimal('25'))
        Decimal('75.00')
    """
    if original_price < 0:
        raise ValueError("Original price cannot be negative")
    
    if discount_value < 0:
        raise ValueError("Discount value cannot be negative")
    
    if discount_type == 'percentage':
        if discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        discount_amount = (original_price * discount_value / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    elif discount_type == 'fixed_amount':
        discount_amount = discount_value.quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    else:
        raise ValueError(f"Invalid discount type: {discount_type}")
    
    final_price = original_price - discount_amount
    
    # Ensure price doesn't go negative
    return max(Decimal('0.00'), final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate_percentage_discount(original_price: Decimal, discount_percent: Decimal) -> Decimal:
    """
    Calculate discount amount from percentage.
    
    Args:
        original_price: Original price
        discount_percent: Discount percentage (e.g., 10 for 10%)
        
    Returns:
        Discount amount
        
    Example:
        >>> calculate_percentage_discount(Decimal('100'), Decimal('15'))
        Decimal('15.00')
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percentage must be between 0 and 100")
    
    return (original_price * discount_percent / 100).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


def calculate_final_price(
    base_price: Decimal,
    coupon_discount: Optional[Decimal] = None,
    referral_discount: Optional[Decimal] = None,
    max_discount_percent: Decimal = Decimal('100')
) -> Dict[str, Decimal]:
    """
    Calculate final price with multiple discounts applied sequentially.
    
    Args:
        base_price: Original price before discounts
        coupon_discount: Coupon discount amount (optional)
        referral_discount: Referral discount amount (optional)
        max_discount_percent: Maximum allowed discount percentage (default 100%)
        
    Returns:
        Dictionary with breakdown:
        - base_price: Original price
        - coupon_discount: Coupon discount applied
        - referral_discount: Referral discount applied
        - total_discount: Total discount amount
        - final_price: Price after all discounts
        - discount_percentage: Total discount as percentage
        
    Example:
        >>> calculate_final_price(Decimal('100'), Decimal('20'), Decimal('10'))
        {
            'base_price': Decimal('100.00'),
            'coupon_discount': Decimal('20.00'),
            'referral_discount': Decimal('10.00'),
            'total_discount': Decimal('30.00'),
            'final_price': Decimal('70.00'),
            'discount_percentage': Decimal('30.00')
        }
    """
    base_price = base_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    coupon_discount = (coupon_discount or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    referral_discount = (referral_discount or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Apply discounts sequentially
    price_after_coupon = max(Decimal('0.00'), base_price - coupon_discount)
    
    # Referral discount applies to price after coupon
    total_discount = coupon_discount + referral_discount
    final_price = max(Decimal('0.00'), price_after_coupon - referral_discount)
    
    # Check max discount
    if base_price > 0:
        discount_percentage = (total_discount / base_price * 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        if discount_percentage > max_discount_percent:
            # Cap the discount
            max_discount_amount = (base_price * max_discount_percent / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            total_discount = max_discount_amount
            final_price = base_price - total_discount
            discount_percentage = max_discount_percent
    else:
        discount_percentage = Decimal('0.00')
    
    return {
        'base_price': base_price,
        'coupon_discount': coupon_discount,
        'referral_discount': referral_discount,
        'total_discount': total_discount,
        'final_price': final_price,
        'discount_percentage': discount_percentage
    }


def apply_currency_conversion(
    amount: Decimal,
    from_currency: str,
    to_currency: str
) -> Optional[Decimal]:
    """
    Convert amount between currencies using ExchangeRate model.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'NGN')
        
    Returns:
        Converted amount or None if exchange rate not found
        
    Example:
        >>> apply_currency_conversion(Decimal('100'), 'USD', 'NGN')
        Decimal('41150.00')  # Assuming rate of 411.5
    """
    from subscriptions.models import ExchangeRate
    
    if from_currency == to_currency:
        return amount
    
    rate = ExchangeRate.get_rate(from_currency, to_currency)
    if rate is None:
        return None
    
    converted = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return converted


def format_price(amount: Decimal, currency: str = 'USD', include_symbol: bool = True) -> str:
    """
    Format price for display with currency symbol.
    
    Args:
        amount: Price amount
        currency: Currency code
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted price string
        
    Example:
        >>> format_price(Decimal('1234.50'), 'USD')
        '$1,234.50'
        >>> format_price(Decimal('1234.50'), 'NGN')
        '₦1,234.50'
    """
    currency_symbols = {
        'USD': '$',
        'NGN': '₦',
        'EUR': '€',
        'GBP': '£',
    }
    
    # Format with thousand separators
    formatted_amount = f"{amount:,.2f}"
    
    if include_symbol:
        symbol = currency_symbols.get(currency, currency + ' ')
        return f"{symbol}{formatted_amount}"
    
    return formatted_amount


# ============================================================================
# DATE AND TIME HELPERS
# ============================================================================

def calculate_subscription_end_date(
    start_date: datetime,
    billing_cycle: str,
    duration_months: Optional[int] = None
) -> datetime:
    """
    Calculate subscription end date based on billing cycle.
    
    Args:
        start_date: Subscription start date
        billing_cycle: 'weekly', 'monthly', 'quarterly', 'yearly', or 'lifetime'
        duration_months: Custom duration in months (optional)
        
    Returns:
        End date as datetime
        
    Example:
        >>> start = datetime(2025, 1, 1)
        >>> calculate_subscription_end_date(start, 'monthly')
        datetime(2025, 2, 1, 0, 0)
    """
    if billing_cycle == 'lifetime':
        # Return date far in future (100 years)
        return start_date + timedelta(days=36500)
    
    if duration_months:
        # Custom duration
        days = duration_months * 30  # Approximate
        return start_date + timedelta(days=days)
    
    # Standard billing cycles
    cycle_days = {
        'weekly': 7,
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365,
    }
    
    days = cycle_days.get(billing_cycle)
    if days is None:
        raise ValueError(f"Invalid billing cycle: {billing_cycle}")
    
    return start_date + timedelta(days=days)


def calculate_days_remaining(end_date: datetime) -> int:
    """
    Calculate days remaining until subscription ends.
    
    Args:
        end_date: Subscription end date
        
    Returns:
        Number of days remaining (0 if expired, -1 if lifetime)
        
    Example:
        >>> end = timezone.now() + timedelta(days=10)
        >>> calculate_days_remaining(end)
        10
    """
    # Check if lifetime (end date far in future)
    if end_date.year >= timezone.now().year + 50:
        return -1  # Special value for lifetime
    
    now = timezone.now()
    
    # Ensure both are timezone-aware
    if end_date.tzinfo is None:
        end_date = timezone.make_aware(end_date)
    
    delta = end_date - now
    days = delta.days
    
    return max(0, days)  # Return 0 if negative (expired)


def is_subscription_active(end_date: datetime, grace_period_days: int = 0) -> bool:
    """
    Check if subscription is currently active.
    
    Args:
        end_date: Subscription end date
        grace_period_days: Additional grace period after expiry (default 0)
        
    Returns:
        True if subscription is active
        
    Example:
        >>> end = timezone.now() + timedelta(days=5)
        >>> is_subscription_active(end)
        True
    """
    now = timezone.now()
    
    # Ensure timezone aware
    if end_date.tzinfo is None:
        end_date = timezone.make_aware(end_date)
    
    # Add grace period
    effective_end = end_date + timedelta(days=grace_period_days)
    
    return now < effective_end


def is_subscription_expiring_soon(
    end_date: datetime,
    warning_days: int = 7
) -> bool:
    """
    Check if subscription is expiring within warning period.
    
    Args:
        end_date: Subscription end date
        warning_days: Number of days before expiry to warn (default 7)
        
    Returns:
        True if expiring soon
        
    Example:
        >>> end = timezone.now() + timedelta(days=5)
        >>> is_subscription_expiring_soon(end, warning_days=7)
        True
    """
    days_remaining = calculate_days_remaining(end_date)
    
    # Lifetime subscriptions don't expire
    if days_remaining == -1:
        return False
    
    return 0 < days_remaining <= warning_days


def get_next_billing_date(
    current_end_date: datetime,
    billing_cycle: str
) -> datetime:
    """
    Calculate next billing date for recurring subscriptions.
    
    Args:
        current_end_date: Current subscription end date
        billing_cycle: Billing cycle type
        
    Returns:
        Next billing date
        
    Example:
        >>> end = datetime(2025, 1, 31)
        >>> get_next_billing_date(end, 'monthly')
        datetime(2025, 2, 28, 0, 0)  # Approximately
    """
    return calculate_subscription_end_date(current_end_date, billing_cycle)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_discount_percentage(value: Decimal) -> None:
    """
    Validate discount percentage is within valid range.
    
    Args:
        value: Discount percentage to validate
        
    Raises:
        ValidationError: If percentage is invalid
        
    Example:
        >>> validate_discount_percentage(Decimal('50'))  # OK
        >>> validate_discount_percentage(Decimal('150'))  # Raises ValidationError
    """
    if value < 0:
        raise ValidationError("Discount percentage cannot be negative")
    
    if value > 100:
        raise ValidationError("Discount percentage cannot exceed 100%")


def validate_currency_code(code: str) -> None:
    """
    Validate currency code format.
    
    Args:
        code: Currency code to validate (e.g., 'USD')
        
    Raises:
        ValidationError: If code is invalid
        
    Example:
        >>> validate_currency_code('USD')  # OK
        >>> validate_currency_code('INVALID')  # Raises ValidationError
    """
    valid_currencies = ['USD', 'NGN', 'EUR', 'GBP', 'CAD', 'JPY', 'CNY']
    
    if not code or len(code) != 3:
        raise ValidationError("Currency code must be exactly 3 characters")
    
    code_upper = code.upper()
    
    if code_upper not in valid_currencies:
        raise ValidationError(
            f"Invalid currency code: {code}. "
            f"Supported currencies: {', '.join(valid_currencies)}"
        )


def validate_telegram_username(username: str) -> None:
    """
    Validate Telegram username format.
    
    Args:
        username: Telegram username (with or without @)
        
    Raises:
        ValidationError: If username format is invalid
        
    Example:
        >>> validate_telegram_username('@john_doe')  # OK
        >>> validate_telegram_username('john.doe')  # Raises ValidationError (no dots allowed)
    """
    if not username:
        raise ValidationError("Telegram username cannot be empty")
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Telegram username rules:
    # - 5-32 characters
    # - Only letters, digits, underscores
    # - Must not start with digit
    # - Cannot end with underscore
    
    if len(username) < 5:
        raise ValidationError("Telegram username must be at least 5 characters")
    
    if len(username) > 32:
        raise ValidationError("Telegram username cannot exceed 32 characters")
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        raise ValidationError(
            "Telegram username must start with a letter and contain only "
            "letters, numbers, and underscores"
        )
    
    if username.endswith('_'):
        raise ValidationError("Telegram username cannot end with underscore")


def validate_email_address(email: str) -> None:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Raises:
        ValidationError: If email format is invalid
        
    Example:
        >>> validate_email_address('user@example.com')  # OK
        >>> validate_email_address('invalid-email')  # Raises ValidationError
    """
    if not email:
        raise ValidationError("Email address cannot be empty")
    
    # Basic email regex (Django has more sophisticated validation)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError("Invalid email address format")


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_currency(amount: Decimal, currency: str = 'USD') -> str:
    """
    Format currency amount with proper symbol and formatting.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
        
    Example:
        >>> format_currency(Decimal('1234.56'), 'USD')
        '$1,234.56'
    """
    return format_price(amount, currency, include_symbol=True)


def format_date_display(dt: datetime, format_type: str = 'long') -> str:
    """
    Format datetime for display.
    
    Args:
        dt: Datetime to format
        format_type: 'short', 'long', or 'relative'
        
    Returns:
        Formatted date string
        
    Example:
        >>> dt = datetime(2025, 11, 4, 14, 30)
        >>> format_date_display(dt, 'long')
        'November 4, 2025 at 2:30 PM'
        >>> format_date_display(dt, 'short')
        '11/04/2025'
    """
    if format_type == 'short':
        return dt.strftime('%m/%d/%Y')
    elif format_type == 'long':
        return dt.strftime('%B %d, %Y at %I:%M %p')
    elif format_type == 'relative':
        # Calculate relative time
        now = timezone.now()
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt)
        
        delta = now - dt
        
        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_duration(days: int) -> str:
    """
    Format duration in days to human-readable string.
    
    Args:
        days: Number of days (-1 for lifetime, negative for expired)
        
    Returns:
        Formatted duration string
        
    Example:
        >>> format_duration(7)
        '1 week'
        >>> format_duration(45)
        '1 month, 15 days'
        >>> format_duration(-1)
        'Lifetime'
    """
    if days == -1:  # Special value for lifetime
        return "Lifetime"
    
    if days < 0:
        return "Expired"
    
    if days == 0:
        return "Expires today"
    
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''}"
    
    if days < 30:
        weeks = days // 7
        remaining_days = days % 7
        result = f"{weeks} week{'s' if weeks != 1 else ''}"
        if remaining_days > 0:
            result += f", {remaining_days} day{'s' if remaining_days != 1 else ''}"
        return result
    
    if days < 365:
        months = days // 30
        remaining_days = days % 30
        result = f"{months} month{'s' if months != 1 else ''}"
        if remaining_days > 0:
            result += f", {remaining_days} day{'s' if remaining_days != 1 else ''}"
        return result
    
    years = days // 365
    remaining_days = days % 365
    result = f"{years} year{'s' if years != 1 else ''}"
    if remaining_days > 0:
        months = remaining_days // 30
        if months > 0:
            result += f", {months} month{'s' if months != 1 else ''}"
    return result


def format_billing_cycle(cycle: str) -> str:
    """
    Format billing cycle for display.
    
    Args:
        cycle: Billing cycle code
        
    Returns:
        Human-readable billing cycle
        
    Example:
        >>> format_billing_cycle('monthly')
        'Monthly'
        >>> format_billing_cycle('lifetime')
        'One-time (Lifetime Access)'
    """
    cycle_map = {
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'quarterly': 'Quarterly',
        'yearly': 'Yearly',
        'lifetime': 'One-time (Lifetime Access)',
        'one_time': 'One-time Payment',
    }
    
    return cycle_map.get(cycle, cycle.title())


# ============================================================================
# FEATURE ACCESS HELPERS
# ============================================================================

def get_user_features(user) -> List[str]:
    """
    Get list of feature keys user has access to.
    
    Args:
        user: Django User instance
        
    Returns:
        List of feature keys
        
    Example:
        >>> features = get_user_features(user)
        ['view_premium_signals', 'telegram_vip_group']
    """
    from subscriptions.models import Subscription
    
    # Get active subscriptions (status='active' and within date range)
    now = timezone.now()
    active_subscriptions = Subscription.objects.filter(
        billing_profile__user=user,
        status='active',
        start_date__lte=now,
        end_date__gte=now
    ).select_related('plan')
    
    # Collect all features from all active subscriptions
    features = set()
    for subscription in active_subscriptions:
        if subscription.plan:
            plan_features = subscription.plan.features.filter(is_active=True)
            features.update(plan_features.values_list('key', flat=True))
    
    return list(features)


def has_feature_access(user, feature_key: str) -> bool:
    """
    Check if user has access to a specific feature.
    
    Args:
        user: Django User instance
        feature_key: Feature key to check
        
    Returns:
        True if user has access to feature
        
    Example:
        >>> has_feature_access(user, 'view_premium_signals')
        True
    """
    user_features = get_user_features(user)
    return feature_key in user_features


def get_feature_status(user) -> Dict[str, Any]:
    """
    Get comprehensive feature access status for user.
    
    Args:
        user: Django User instance
        
    Returns:
        Dictionary with feature status information
        
    Example:
        >>> get_feature_status(user)
        {
            'total_features': 5,
            'features': ['view_premium_signals', ...],
            'active_plans': ['Premium', 'VIP'],
            'expires_soon': False
        }
    """
    from subscriptions.models import Subscription
    
    features = get_user_features(user)
    
    now = timezone.now()
    active_subscriptions = Subscription.objects.filter(
        billing_profile__user=user,
        status='active',
        start_date__lte=now,
        end_date__gte=now
    ).select_related('plan')
    
    active_plans = [sub.plan.name for sub in active_subscriptions if sub.plan]
    
    # Check if any subscription expires soon
    expires_soon = any(
        is_subscription_expiring_soon(sub.end_date)
        for sub in active_subscriptions
    )
    
    return {
        'total_features': len(features),
        'features': features,
        'active_plans': active_plans,
        'active_subscriptions_count': active_subscriptions.count(),
        'expires_soon': expires_soon
    }


# ============================================================================
# REFERRAL HELPERS
# ============================================================================

def calculate_referral_commission(
    transaction_amount: Decimal,
    commission_percent: Decimal
) -> Decimal:
    """
    Calculate referral commission amount.
    
    Args:
        transaction_amount: Amount of transaction
        commission_percent: Commission percentage (e.g., 10 for 10%)
        
    Returns:
        Commission amount
        
    Example:
        >>> calculate_referral_commission(Decimal('100'), Decimal('10'))
        Decimal('10.00')
    """
    if commission_percent < 0 or commission_percent > 100:
        raise ValueError("Commission percentage must be between 0 and 100")
    
    commission = (transaction_amount * commission_percent / 100).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    return commission


def calculate_referral_discount(
    base_price: Decimal,
    referral_discount_percent: Decimal
) -> Decimal:
    """
    Calculate referral discount amount.
    
    Args:
        base_price: Base price before discount
        referral_discount_percent: Referral discount percentage
        
    Returns:
        Discount amount
        
    Example:
        >>> calculate_referral_discount(Decimal('100'), Decimal('15'))
        Decimal('15.00')
    """
    return calculate_percentage_discount(base_price, referral_discount_percent)


# ============================================================================
# UTILITY HELPERS
# ============================================================================

def generate_unique_code(
    prefix: str = '',
    length: int = 8,
    uppercase: bool = True,
    include_numbers: bool = True
) -> str:
    """
    Generate unique alphanumeric code.
    
    Args:
        prefix: Prefix for code (e.g., 'OXI-')
        length: Length of random part (default 8)
        uppercase: Use uppercase letters (default True)
        include_numbers: Include numbers in code (default True)
        
    Returns:
        Generated unique code
        
    Example:
        >>> generate_unique_code('OXI-', 6)
        'OXI-A8F3K2'
    """
    chars = string.ascii_uppercase if uppercase else string.ascii_lowercase
    
    if include_numbers:
        chars += string.digits
    
    random_part = ''.join(random.choices(chars, k=length))
    
    return f"{prefix}{random_part}"


def truncate_string(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 50)
        suffix: Suffix to add when truncated (default '...')
        
    Returns:
        Truncated string
        
    Example:
        >>> truncate_string('This is a very long text', 15)
        'This is a ve...'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_decimal(value: Any, default: Decimal = Decimal('0.00')) -> Decimal:
    """
    Safely convert value to Decimal, returning default on error.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Decimal value or default
        
    Example:
        >>> safe_decimal('123.45')
        Decimal('123.45')
        >>> safe_decimal('invalid')
        Decimal('0.00')
    """
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return default
