"""
Subscriptions utilities package.

Common utility functions used across the subscription system.
"""

from .helpers import (
    # Price calculation helpers
    calculate_price_with_discount,
    calculate_percentage_discount,
    calculate_final_price,
    apply_currency_conversion,
    format_price,
    
    # Date and time helpers
    calculate_subscription_end_date,
    calculate_days_remaining,
    is_subscription_active,
    is_subscription_expiring_soon,
    get_next_billing_date,
    
    # Validation helpers
    validate_discount_percentage,
    validate_currency_code,
    validate_telegram_username,
    validate_email_address,
    
    # Formatting helpers
    format_currency,
    format_date_display,
    format_duration,
    format_billing_cycle,
    
    # Feature access helpers
    get_user_features,
    has_feature_access,
    get_feature_status,
    
    # Referral helpers
    calculate_referral_commission,
    calculate_referral_discount,
    
    # Utility helpers
    generate_unique_code,
    truncate_string,
    safe_decimal,
)

__all__ = [
    # Price calculations
    'calculate_price_with_discount',
    'calculate_percentage_discount',
    'calculate_final_price',
    'apply_currency_conversion',
    'format_price',
    
    # Date/time
    'calculate_subscription_end_date',
    'calculate_days_remaining',
    'is_subscription_active',
    'is_subscription_expiring_soon',
    'get_next_billing_date',
    
    # Validation
    'validate_discount_percentage',
    'validate_currency_code',
    'validate_telegram_username',
    'validate_email_address',
    
    # Formatting
    'format_currency',
    'format_date_display',
    'format_duration',
    'format_billing_cycle',
    
    # Features
    'get_user_features',
    'has_feature_access',
    'get_feature_status',
    
    # Referrals
    'calculate_referral_commission',
    'calculate_referral_discount',
    
    # Utilities
    'generate_unique_code',
    'truncate_string',
    'safe_decimal',
]
