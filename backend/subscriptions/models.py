# Pricing and subscription management models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
import json
from django.core.exceptions import ValidationError
from django.db import transaction
from oxidane.encryption import encrypt_field, decrypt_field

User = get_user_model()

# ============================================================================
# DEPRECATED MODELS REMOVED (Phase 0.5 Cleanup - November 2, 2025)
# ============================================================================
# The following models have been removed and replaced with new Phase 0.5 models:
# - PricingPlan → Replaced by SubscriptionPlan (more flexible, multi-currency)
# - SignalSubscription → Replaced by Subscription (unified billing)
# - PaymentTransaction → Will be recreated in Phase 0.5.17+ with proper structure
# - TelegramGroupManagement → Replaced by TelegramGroup (represents actual groups)
# ============================================================================


# ============================================================================
# DEPRECATED MODELS REMOVED (Phase 0.5 Cleanup - November 2, 2025)
# ============================================================================
# The following models have been removed and replaced:
# - SignalSubscription → Subscription (unified billing)
# - PaymentTransaction → Will be recreated in Phase 0.5.17+ with proper structure
# - TelegramGroupManagement → TelegramGroup (represents actual groups)
# ============================================================================

# Mentorship Models

# Note: Mentorship is now handled through Subscription model with SubscriptionPlan
# The separate MentorshipPlan and MentorshipSubscription models have been deprecated
# All pricing is managed through SubscriptionPlan model (Phase 0.5)


# Note: 1-on-1 sessions are arranged offline and don't concern the system currently
# Keeping model commented out for potential future use
#
# class OneOnOneSession(models.Model):
#     """Track 1-on-1 mentorship sessions - DEPRECATED"""
#     pass


# ============================================================================
# BILLING AND PAYMENT MODELS
# ============================================================================

class BillingProfile(models.Model):
    """Central billing profile for each user with Telegram verification"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='billing_profile')
    
    # Telegram Verification
    telegram_user_id = models.CharField(max_length=50, blank=True, null=True, unique=True, 
                                       help_text="Telegram user ID for group access")
    telegram_username = models.CharField(max_length=100, blank=True, 
                                        help_text="Telegram @username for reference")
    telegram_verified = models.BooleanField(default=False, 
                                           help_text="Has user verified their Telegram account?")
    telegram_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Verification Code (temporary, expires after use)
    verification_code = models.CharField(max_length=20, blank=True, null=True, unique=True,
                                        help_text="OXI-XXXX format code for Telegram verification")
    verification_code_created_at = models.DateTimeField(null=True, blank=True)
    verification_code_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Billing Information
    country = models.CharField(max_length=2, blank=True, help_text="ISO country code")
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('NGN', 'Nigerian Naira'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    currency_preference = models.CharField(max_length=3, default='USD', 
                                          choices=CURRENCY_CHOICES)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Billing Profile: {self.user.email}"
    
    def generate_verification_code(self):
        """Generate a new verification code (OXI-XXXX format)"""
        import random
        import string
        
        # Generate random 4-character alphanumeric code
        code_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        self.verification_code = f"OXI-{code_suffix}"
        self.verification_code_created_at = timezone.now()
        self.verification_code_expires_at = timezone.now() + timezone.timedelta(hours=24)
        self.save()
        return self.verification_code
    
    def verify_telegram(self, telegram_user_id, telegram_username):
        """Mark Telegram as verified and save user info"""
        self.telegram_user_id = str(telegram_user_id)
        self.telegram_username = telegram_username
        self.telegram_verified = True
        self.telegram_verified_at = timezone.now()
        # Clear verification code after use
        self.verification_code = None
        self.verification_code_created_at = None
        self.verification_code_expires_at = None
        self.save()
    
    def is_verification_code_valid(self):
        """Check if verification code is still valid"""
        if not self.verification_code or not self.verification_code_expires_at:
            return False
        return timezone.now() < self.verification_code_expires_at


class PaymentMethod(models.Model):
    """Stored payment methods (tokenized, never raw card data)"""
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Account'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.CASCADE, 
                                       related_name='payment_methods')
    
    # Payment Gateway Info (Paystack)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='card')
    gateway_authorization_code = models.CharField(max_length=255, unique=True,
                                                  help_text="Paystack authorization code")
    
    # Display Info (for user to identify card)
    card_last4 = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_brand = models.CharField(max_length=20, blank=True, help_text="Visa, Mastercard, etc.")
    card_exp_month = models.CharField(max_length=2, blank=True)
    card_exp_year = models.CharField(max_length=4, blank=True)
    
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.payment_type == 'card':
            return f"{self.card_brand} ****{self.card_last4}"
        return f"{self.payment_type} - {self.bank_name}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset other defaults
        if self.is_default:
            PaymentMethod.objects.filter(
                billing_profile=self.billing_profile,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """
    User subscriptions (replaces SignalSubscription, more flexible).
    
    Phase 0.5 Updates (Task 0.5.11):
    - Added `plan` FK to SubscriptionPlan (replaces pricing_plan)
    - Added `referral` FK to Referral (optional, for tracking referral conversions)
    - Added `metadata` JSONField (for flexible data storage)
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.CASCADE, 
                                       related_name='subscriptions')
    
    # NEW: SubscriptionPlan relationship (Phase 0.5)
    plan = models.ForeignKey(
        'SubscriptionPlan',
        on_delete=models.PROTECT,
        related_name='subscriptions',
        null=True,  # Temporary for migration
        blank=True,
        help_text='New Phase 0.5 dynamic subscription plan'
    )
    
    # NEW: Referral tracking (Phase 0.5)
    referral = models.ForeignKey(
        'Referral',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_subscriptions',
        help_text='Referral that led to this subscription (if any)'
    )
    
    # Subscription Period
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Payment
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, 
                                      null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # NEW: Flexible metadata storage (Phase 0.5)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional subscription metadata (source, campaign, notes, etc.)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billing_profile', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        plan_name = self.plan.name if self.plan else 'No Plan'
        return f"{self.billing_profile.user.email} - {plan_name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return (
            self.status == 'active' and
            self.start_date <= timezone.now() <= self.end_date
        )
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if not self.is_active:
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    def cancel(self, reason=""):
        """Cancel subscription (access continues until end_date)"""
        self.auto_renew = False
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.status = 'cancelled'
        self.save()
    
    def check_expiration(self):
        """Check and update status if expired"""
        if timezone.now() > self.end_date and self.status == 'active':
            self.status = 'expired'
            self.save()
            return True
        return False


class Payment(models.Model):
    """Payment transaction records"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_GATEWAYS = [
        ('paystack', 'Paystack'),
        ('manual', 'Manual/Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.CASCADE, 
                                       related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='payments')
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                                help_text="Base subscription amount")
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        help_text="Gateway processing fee")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                      help_text="Total charged (amount + fee)")
    currency = models.CharField(max_length=3, default='USD')
    
    # Gateway Info
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAYS, 
                                      default='paystack')
    gateway_reference = models.CharField(max_length=255, unique=True, 
                                        help_text="Paystack reference/transaction ID")
    gateway_authorization_code = models.CharField(max_length=255, blank=True,
                                                 help_text="For recurring payments")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, 
                                      null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Info
    failure_reason = models.TextField(blank=True)
    gateway_response = models.JSONField(default=dict, 
                                       help_text="Full gateway response data")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billing_profile', 'status']),
            models.Index(fields=['gateway_reference']),
        ]
    
    def __str__(self):
        return f"Payment {self.gateway_reference} - {self.total_amount} {self.currency} ({self.status})"
    
    def mark_as_paid(self):
        """Mark payment as successful"""
        self.status = 'success'
        self.paid_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, reason=""):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        self.failure_reason = reason
        self.save()


# ============================================================================
# PHASE 0.5: DYNAMIC PLANS FOUNDATION - NEW MODELS
# ============================================================================

class Feature(models.Model):
    """
    Represents a platform capability that can be assigned to subscription plans.
    
    Features are granular, reusable capabilities that define what users can access.
    Examples:
    - view_premium_signals: Access to premium trading signals
    - telegram_vip_group: Access to VIP Telegram group
    - download_course_materials: Download course files
    - one_on_one_mentorship: 1-on-1 mentorship sessions
    
    Features are organized by category for better admin UI organization.
    """
    
    CATEGORY_CHOICES = [
        ('signals', 'Signals & Trading'),
        ('telegram', 'Telegram Groups'),
        ('courses', 'Courses & Education'),
        ('support', 'Support & Mentorship'),
        ('api', 'API & Integrations'),
        ('analytics', 'Analytics & Reporting'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique identifier for programmatic access (e.g., 'view_premium_signals')"
    )
    name = models.CharField(
        max_length=200,
        help_text="Display name shown to users (e.g., 'View Premium Signals')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what this feature provides"
    )
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        help_text="Feature category for organization"
    )
    icon = models.CharField(
        max_length=10, 
        default='✨',
        help_text="Emoji icon for visual representation"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this feature is currently available"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'sort_order', 'name']
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def clean(self):
        """Validate feature key format"""
        if self.key:
            # Ensure key is lowercase with underscores
            if not self.key.replace('_', '').replace('-', '').isalnum():
                raise ValidationError({
                    'key': 'Feature key must contain only letters, numbers, underscores, and hyphens.'
                })
            # Auto-convert to lowercase
            self.key = self.key.lower().replace('-', '_')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SubscriptionPlan(models.Model):
    """
    Dynamic subscription plan with configurable features and pricing.
    Supports multiple billing periods and currencies via auto-conversion.
    """
    BILLING_PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly (3 months)'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True, blank=True)
    description = models.TextField(blank=True)
    
    # Feature relationships
    features = models.ManyToManyField(
        Feature,
        related_name='plans',
        blank=True,
        help_text='Features included in this plan'
    )
    
    # Pricing (stored in USD, auto-converted to other currencies)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Base price in USD'
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BILLING_PERIOD_CHOICES,
        default='monthly'
    )
    
    # Trial period
    trial_days = models.IntegerField(
        default=0,
        help_text='Number of days for free trial (0 = no trial)'
    )
    
    # Plan metadata
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this plan is available for purchase'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Highlight this plan on pricing page'
    )
    sort_order = models.IntegerField(
        default=0,
        help_text='Display order on pricing page (lower = first)'
    )
    
    # Limits and quotas (stored as JSON for flexibility)
    limits = models.JSONField(
        default=dict,
        blank=True,
        help_text='Plan limits (e.g., {"max_signals": 100, "max_courses": 5})'
    )
    
    # Stripe integration (for future use)
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Stripe Price ID for this plan'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'base_price']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['slug']),
            models.Index(fields=['billing_period', 'is_active']),
        ]
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def __str__(self):
        period_display = self.get_billing_period_display()
        return f"{self.name} ({period_display})"
    
    def clean(self):
        """Validate plan data"""
        # Ensure base_price is positive
        if self.base_price and self.base_price < 0:
            raise ValidationError({
                'base_price': 'Base price must be positive.'
            })
        
        # Ensure trial_days is non-negative
        if self.trial_days and self.trial_days < 0:
            raise ValidationError({
                'trial_days': 'Trial days cannot be negative.'
            })
        
        # Auto-generate slug from name if not provided
        if not self.slug and self.name:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            # Add billing period to make it unique
            self.slug = f"{base_slug}-{self.billing_period}"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_price_display(self):
        """Get formatted price with period"""
        if self.billing_period == 'lifetime':
            return f"${self.base_price}"
        elif self.billing_period == 'weekly':
            return f"${self.base_price}/wk"
        elif self.billing_period == 'monthly':
            return f"${self.base_price}/mo"
        elif self.billing_period == 'quarterly':
            return f"${self.base_price}/3mo"
        elif self.billing_period == 'yearly':
            return f"${self.base_price}/yr"
        return f"${self.base_price}"
    
    def get_monthly_equivalent(self):
        """Calculate monthly equivalent price for comparison"""
        if self.billing_period == 'weekly':
            # Assume 4.33 weeks per month (52 weeks / 12 months)
            return self.base_price * Decimal('4.33')
        elif self.billing_period == 'monthly':
            return self.base_price
        elif self.billing_period == 'quarterly':
            return self.base_price / 3
        elif self.billing_period == 'yearly':
            return self.base_price / 12
        elif self.billing_period == 'lifetime':
            # Assume 2 years for lifetime comparison
            return self.base_price / 24
        return self.base_price
    
    def has_trial(self):
        """Check if plan has trial period"""
        return self.trial_days > 0
    
    def get_feature_count(self):
        """Get count of features in this plan"""
        return self.features.count()
    
    def get_features_by_category(self):
        """Get features grouped by category"""
        features_dict = {}
        for feature in self.features.filter(is_active=True).order_by('category', 'sort_order'):
            category = feature.get_category_display()
            if category not in features_dict:
                features_dict[category] = []
            features_dict[category].append(feature)
        return features_dict


class Coupon(models.Model):
    """
    Discount coupon for subscription plans.
    Supports percentage and fixed amount discounts with usage limits.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Coupon code (e.g., SAVE20, SUMMER2024)'
    )
    
    # Discount details
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Percentage (0-100) or fixed amount in USD'
    )
    
    # Applicable plans (empty = applies to all plans)
    plans = models.ManyToManyField(
        SubscriptionPlan,
        related_name='coupons',
        blank=True,
        help_text='Plans this coupon applies to (empty = all plans)'
    )
    
    # Validity period
    valid_from = models.DateTimeField(
        default=timezone.now,
        help_text='When the coupon becomes valid'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the coupon expires (null = never expires)'
    )
    
    # Usage limits
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maximum total uses (null = unlimited)'
    )
    max_uses_per_user = models.IntegerField(
        default=1,
        help_text='Maximum uses per user'
    )
    current_uses = models.IntegerField(
        default=0,
        help_text='Current number of times used'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this coupon is currently active'
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text='Internal description of the coupon'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_coupons',
        help_text='Admin who created this coupon'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
    
    def __str__(self):
        discount_display = self.get_discount_display()
        return f"{self.code} ({discount_display})"
    
    def clean(self):
        """Validate coupon data"""
        # Ensure code is uppercase
        if self.code:
            self.code = self.code.upper().strip()
            
            # Validate code format (alphanumeric + underscore/hyphen)
            import re
            if not re.match(r'^[A-Z0-9_-]+$', self.code):
                raise ValidationError({
                    'code': 'Coupon code must contain only uppercase letters, numbers, underscores, and hyphens.'
                })
        
        # Validate discount value based on type
        if self.discount_value is not None:
            if self.discount_type == 'percentage':
                if self.discount_value < 0 or self.discount_value > 100:
                    raise ValidationError({
                        'discount_value': 'Percentage discount must be between 0 and 100.'
                    })
            elif self.discount_type == 'fixed':
                if self.discount_value < 0:
                    raise ValidationError({
                        'discount_value': 'Fixed discount amount must be positive.'
                    })
        
        # Validate date range
        if self.valid_from and self.valid_until:
            if self.valid_until <= self.valid_from:
                raise ValidationError({
                    'valid_until': 'Expiration date must be after start date.'
                })
        
        # Validate usage limits
        if self.max_uses is not None and self.max_uses < 0:
            raise ValidationError({
                'max_uses': 'Maximum uses cannot be negative.'
            })
        
        if self.max_uses_per_user < 0:
            raise ValidationError({
                'max_uses_per_user': 'Maximum uses per user cannot be negative.'
            })
        
        if self.current_uses < 0:
            raise ValidationError({
                'current_uses': 'Current uses cannot be negative.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_discount_display(self):
        """Get formatted discount display"""
        if self.discount_type == 'percentage':
            return f"{int(self.discount_value)}% off"
        else:
            return f"${self.discount_value} off"
    
    def is_valid(self):
        """Check if coupon is currently valid (time-based only)"""
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False
        
        # Check if started
        if self.valid_from and now < self.valid_from:
            return False
        
        # Check if expired
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def is_usage_available(self):
        """Check if coupon has usage remaining"""
        # Check total usage limit
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def can_be_used(self):
        """Check if coupon can be used (combines validity and usage checks)"""
        return self.is_valid() and self.is_usage_available()
    
    def applies_to_plan(self, plan):
        """Check if coupon applies to a specific plan"""
        # If no plans specified, applies to all
        if self.plans.count() == 0:
            return True
        
        # Otherwise check if plan is in the list
        return self.plans.filter(id=plan.id).exists()
    
    def calculate_discount(self, original_price):
        """Calculate discounted price"""
        original_price = Decimal(str(original_price))
        
        if self.discount_type == 'percentage':
            discount_amount = original_price * (self.discount_value / 100)
        else:
            discount_amount = self.discount_value
        
        # Ensure discount doesn't make price negative
        discount_amount = min(discount_amount, original_price)
        
        final_price = original_price - discount_amount
        return {
            'original_price': original_price,
            'discount_amount': discount_amount,
            'final_price': final_price,
            'savings_percentage': (discount_amount / original_price * 100) if original_price > 0 else 0
        }
    
    def increment_usage(self):
        """Increment the usage counter"""
        self.current_uses += 1
        self.save(update_fields=['current_uses', 'updated_at'])
    
    def get_remaining_uses(self):
        """Get number of remaining uses (None if unlimited)"""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)


class ReferralCode(models.Model):
    """
    Referral code system for user-to-user referrals.
    Both referrer and referee can receive discounts.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Referral code (e.g., JOHN2024, REFMARY)'
    )
    
    # Referrer (user who owns this referral code)
    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referral_codes',
        help_text='User who owns this referral code'
    )
    
    # Discount for referrer (reward for referring)
    referrer_discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        help_text='Type of discount for the referrer'
    )
    referrer_discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text='Discount value for referrer'
    )
    
    # Discount for referee (person using the code)
    referee_discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        help_text='Type of discount for the referee'
    )
    referee_discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text='Discount value for referee'
    )
    
    # Usage limits
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maximum total uses (null = unlimited)'
    )
    current_uses = models.IntegerField(
        default=0,
        help_text='Current number of times used'
    )
    
    # Validity period
    valid_from = models.DateTimeField(
        default=timezone.now,
        help_text='When the referral code becomes valid'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the referral code expires (null = never expires)'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this referral code is currently active'
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text='Optional description'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['referrer']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Referral Code'
        verbose_name_plural = 'Referral Codes'
        constraints = [
            models.CheckConstraint(
                check=models.Q(referrer_discount_value__gte=0),
                name='referrer_discount_value_positive'
            ),
            models.CheckConstraint(
                check=models.Q(referee_discount_value__gte=0),
                name='referee_discount_value_positive'
            ),
            models.CheckConstraint(
                check=models.Q(current_uses__gte=0),
                name='referral_current_uses_positive'
            ),
        ]
    
    def __str__(self):
        return f"{self.code} (by {self.referrer.username})"
    
    def clean(self):
        """Validate referral code data"""
        # Ensure code is uppercase
        if self.code:
            self.code = self.code.upper().strip()
            
            # Validate code format (alphanumeric + underscore)
            import re
            if not re.match(r'^[A-Z0-9_]+$', self.code):
                raise ValidationError({
                    'code': 'Referral code must contain only uppercase letters, numbers, and underscores.'
                })
            
            # Minimum length
            if len(self.code) < 3:
                raise ValidationError({
                    'code': 'Referral code must be at least 3 characters long.'
                })
        
        # Validate referrer discount value
        if self.referrer_discount_value is not None:
            if self.referrer_discount_type == 'percentage':
                if self.referrer_discount_value < 0 or self.referrer_discount_value > 100:
                    raise ValidationError({
                        'referrer_discount_value': 'Percentage discount must be between 0 and 100.'
                    })
            elif self.referrer_discount_type == 'fixed':
                if self.referrer_discount_value < 0:
                    raise ValidationError({
                        'referrer_discount_value': 'Fixed discount amount must be positive.'
                    })
        
        # Validate referee discount value
        if self.referee_discount_value is not None:
            if self.referee_discount_type == 'percentage':
                if self.referee_discount_value < 0 or self.referee_discount_value > 100:
                    raise ValidationError({
                        'referee_discount_value': 'Percentage discount must be between 0 and 100.'
                    })
            elif self.referee_discount_type == 'fixed':
                if self.referee_discount_value < 0:
                    raise ValidationError({
                        'referee_discount_value': 'Fixed discount amount must be positive.'
                    })
        
        # Validate date range
        if self.valid_from and self.valid_until:
            if self.valid_until <= self.valid_from:
                raise ValidationError({
                    'valid_until': 'Expiration date must be after start date.'
                })
        
        # Validate usage limits
        if self.max_uses is not None and self.max_uses < 0:
            raise ValidationError({
                'max_uses': 'Maximum uses cannot be negative.'
            })
        
        if self.current_uses < 0:
            raise ValidationError({
                'current_uses': 'Current uses cannot be negative.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if referral code is currently valid (time-based only)"""
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False
        
        # Check if started
        if self.valid_from and now < self.valid_from:
            return False
        
        # Check if expired
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def is_usage_available(self):
        """Check if referral code has usage remaining"""
        # Check total usage limit
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def can_be_used(self):
        """Check if referral code can be used (combines validity and usage checks)"""
        return self.is_valid() and self.is_usage_available()
    
    def get_referrer_discount_display(self):
        """Get formatted discount display for referrer"""
        if self.referrer_discount_type == 'percentage':
            return f"{int(self.referrer_discount_value)}% off"
        else:
            return f"${self.referrer_discount_value} off"
    
    def get_referee_discount_display(self):
        """Get formatted discount display for referee"""
        if self.referee_discount_type == 'percentage':
            return f"{int(self.referee_discount_value)}% off"
        else:
            return f"${self.referee_discount_value} off"
    
    def calculate_referrer_discount(self, original_price):
        """Calculate discount for the referrer"""
        original_price = Decimal(str(original_price))
        
        if self.referrer_discount_type == 'percentage':
            discount_amount = original_price * (self.referrer_discount_value / 100)
        else:
            discount_amount = self.referrer_discount_value
        
        # Ensure discount doesn't make price negative
        discount_amount = min(discount_amount, original_price)
        
        final_price = original_price - discount_amount
        return {
            'original_price': original_price,
            'discount_amount': discount_amount,
            'final_price': final_price,
            'savings_percentage': (discount_amount / original_price * 100) if original_price > 0 else 0
        }
    
    def calculate_referee_discount(self, original_price):
        """Calculate discount for the referee"""
        original_price = Decimal(str(original_price))
        
        if self.referee_discount_type == 'percentage':
            discount_amount = original_price * (self.referee_discount_value / 100)
        else:
            discount_amount = self.referee_discount_value
        
        # Ensure discount doesn't make price negative
        discount_amount = min(discount_amount, original_price)
        
        final_price = original_price - discount_amount
        return {
            'original_price': original_price,
            'discount_amount': discount_amount,
            'final_price': final_price,
            'savings_percentage': (discount_amount / original_price * 100) if original_price > 0 else 0
        }
    
    def increment_usage(self):
        """Increment the usage counter"""
        self.current_uses += 1
        self.save(update_fields=['current_uses', 'updated_at'])
    
    def get_remaining_uses(self):
        """Get number of remaining uses (None if unlimited)"""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)

class Referral(models.Model):
    """
    Track actual referral conversions when someone uses a referral code.
    Records the discount applied to the referee (new user).
    Referrer earns credits separately (see ReferralCredit model).
    """
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Referral relationships
    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name='referrals',
        help_text='The referral code that was used'
    )
    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referrals_made',
        help_text='User who referred (owner of the code)'
    )
    referee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referrals_received',
        help_text='User who was referred (used the code)'
    )
    
    # Subscription that resulted from referral
    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_entry',
        help_text='Subscription created from this referral (NEW billing system)'
    )
    
    # Discount tracking (referee only - referrer gets credits)
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Original subscription price before discount'
    )
    referee_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        help_text='Discount percentage applied to referee (default 10%)'
    )
    referee_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Discount amount given to referee in currency'
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Final amount paid after discount'
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text='Currency code'
    )
    
    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text='Status of this referral'
    )
    conversion_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When the referral conversion occurred'
    )
    cancelled_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this referral was cancelled (if applicable)'
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text='Internal notes about this referral'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-conversion_date']
        indexes = [
            models.Index(fields=['referrer', '-conversion_date']),
            models.Index(fields=['referee']),
            models.Index(fields=['status']),
            models.Index(fields=['-conversion_date']),
        ]
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        constraints = [
            models.CheckConstraint(
                check=models.Q(original_amount__gte=0),
                name='referral_original_amount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(referee_discount_amount__gte=0),
                name='referral_referee_discount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(final_amount__gte=0),
                name='referral_final_amount_positive'
            ),
            models.CheckConstraint(
                check=models.Q(referee_discount_percent__gte=0) & models.Q(referee_discount_percent__lte=100),
                name='referral_discount_percent_valid'
            ),
        ]
    
    def __str__(self):
        return f"Referral: {self.referrer.username} → {self.referee.username} ({self.status})"
    
    def clean(self):
        """Validate referral data"""
        # Ensure referrer matches the referral code owner
        if self.referral_code and self.referrer:
            if self.referral_code.referrer != self.referrer:
                raise ValidationError({
                    'referrer': 'Referrer must be the owner of the referral code.'
                })
        
        # Ensure referee is not the same as referrer
        if self.referrer and self.referee:
            if self.referrer == self.referee:
                raise ValidationError({
                    'referee': 'Referee cannot be the same as referrer (self-referral not allowed).'
                })
        
        # Validate amounts are non-negative
        if self.original_amount and self.original_amount < 0:
            raise ValidationError({
                'original_amount': 'Original amount cannot be negative.'
            })
        
        if self.referee_discount_amount and self.referee_discount_amount < 0:
            raise ValidationError({
                'referee_discount_amount': 'Referee discount amount cannot be negative.'
            })
        
        if self.final_amount and self.final_amount < 0:
            raise ValidationError({
                'final_amount': 'Final amount cannot be negative.'
            })
        
        # Validate discount percentage is 0-100
        if self.referee_discount_percent is not None:
            if self.referee_discount_percent < 0 or self.referee_discount_percent > 100:
                raise ValidationError({
                    'referee_discount_percent': 'Discount percentage must be between 0 and 100.'
                })
        
        # Validate discount makes sense
        if self.original_amount and self.final_amount:
            if self.final_amount > self.original_amount:
                raise ValidationError({
                    'final_amount': 'Final amount cannot be greater than original amount.'
                })
    
    def save(self, *args, **kwargs):
        # Calculate discount amount if not set (round to 2 decimal places)
        if self.original_amount and self.referee_discount_percent is not None:
            discount_raw = self.original_amount * (self.referee_discount_percent / 100)
            self.referee_discount_amount = discount_raw.quantize(Decimal('0.01'))
        
        # Calculate final amount if not set (round to 2 decimal places)
        if self.original_amount and self.referee_discount_amount is not None:
            final_raw = self.original_amount - self.referee_discount_amount
            self.final_amount = final_raw.quantize(Decimal('0.01'))
        
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Check if referrer should earn a credit (every 10 referrals)
        self.check_and_award_credit()
    
    def mark_as_cancelled(self, reason=''):
        """Mark referral as cancelled"""
        self.status = 'cancelled'
        self.cancelled_date = timezone.now()
        
        if reason:
            self.notes = f"{self.notes}\nCancelled: {reason}" if self.notes else f"Cancelled: {reason}"
        
        self.save()
    
    def check_and_award_credit(self):
        """
        Check if referrer has earned a new credit.
        Awards 5% discount credit for every 10 completed referrals.
        """
        if self.status != 'completed':
            return
        
        # Count completed referrals by this referrer
        completed_count = Referral.objects.filter(
            referrer=self.referrer,
            status='completed'
        ).count()
        
        # Check if this is a milestone (every 10 referrals)
        if completed_count % 10 == 0:
            # Check if credit already exists for this referral
            if not ReferralCredit.objects.filter(earned_from_referral=self).exists():
                ReferralCredit.objects.create(
                    user=self.referrer,
                    credit_percentage=Decimal('5.00'),
                    earned_from_referral=self,
                    notes=f'Earned from {completed_count} completed referrals'
                )
    
    def get_status_display_color(self):
        """Get color for status display"""
        colors = {
            'completed': '#28a745',  # Green
            'cancelled': '#dc3545',  # Red
        }
        return colors.get(self.status, '#6c757d')


class ReferralCredit(models.Model):
    """
    Track discount credits earned by referrers.
    Referrers earn 5% discount credits for every 10 successful referrals.
    Credits are single-use and cannot be stacked.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who earned this credit
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referral_credits',
        help_text='User who earned this discount credit'
    )
    
    # Credit details
    credit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text='Discount percentage (typically 5%)'
    )
    
    # Tracking
    earned_from_referral = models.OneToOneField(
        Referral,
        on_delete=models.CASCADE,
        related_name='generated_credit',
        help_text='The referral that triggered this credit'
    )
    
    # Usage tracking
    is_used = models.BooleanField(
        default=False,
        help_text='Whether this credit has been redeemed'
    )
    used_on_subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_credit_used',
        help_text='Subscription where this credit was applied (NEW billing system)'
    )
    
    # Dates
    earned_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When this credit was earned'
    )
    used_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this credit was redeemed'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this credit expires (null = never expires)'
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text='Internal notes about this credit'
    )
    
    class Meta:
        ordering = ['-earned_date']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['user', '-earned_date']),
            models.Index(fields=['is_used']),
        ]
        verbose_name = 'Referral Credit'
        verbose_name_plural = 'Referral Credits'
    
    def __str__(self):
        status = "Used" if self.is_used else "Available"
        return f"{self.user.username} - {self.credit_percentage}% ({status})"
    
    def clean(self):
        """Validate credit data"""
        # Validate credit percentage
        if self.credit_percentage < 0 or self.credit_percentage > 100:
            raise ValidationError({
                'credit_percentage': 'Credit percentage must be between 0 and 100.'
            })
        
        # If used, must have used_on_subscription and used_date
        if self.is_used:
            if not self.used_on_subscription:
                raise ValidationError({
                    'used_on_subscription': 'Used credits must have an associated subscription.'
                })
            if not self.used_date:
                raise ValidationError({
                    'used_date': 'Used credits must have a used date.'
                })
        
        # Check expiry
        if self.expires_at and self.earned_date:
            if self.expires_at < self.earned_date:
                raise ValidationError({
                    'expires_at': 'Expiry date cannot be before earned date.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def use_credit(self, subscription):
        """
        Mark this credit as used on a specific subscription.
        Returns the credit percentage to apply.
        """
        if self.is_used:
            raise ValidationError('This credit has already been used.')
        
        if self.is_expired():
            raise ValidationError('This credit has expired.')
        
        self.is_used = True
        self.used_on_subscription = subscription
        self.used_date = timezone.now()
        self.save()
        
        return self.credit_percentage
    
    def is_expired(self):
        """Check if this credit has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_available(self):
        """Check if this credit is available for use"""
        return not self.is_used and not self.is_expired()


# ============================================================================
# TELEGRAM CONFIGURATION MODEL (Phase 0.5 - Task 0.5.6)
# ============================================================================

class TelegramConfiguration(models.Model):
    """
    Singleton model for storing Telegram bot configuration.
    Only one instance of this model should exist at any time.
    
    This replaces the old settings-based approach with a proper model.
    """
    
    # Bot Credentials (bot_token will be encrypted in Phase 0.5.12)
    bot_token = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Telegram bot API token from @BotFather'
    )
    bot_username = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Bot username (e.g., @OxidaneBot)'
    )
    
    # Status
    is_enabled = models.BooleanField(
        default=True,
        help_text='Enable/disable Telegram integration'
    )
    is_connected = models.BooleanField(
        default=False,
        help_text='Whether the bot is currently connected'
    )
    connection_error = models.TextField(
        blank=True,
        default='',
        help_text='Last connection error message'
    )
    last_health_check = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time bot connection was verified'
    )
    
    # Automation Settings
    auto_add_enabled = models.BooleanField(
        default=True,
        help_text='Automatically add users to groups on subscription'
    )
    auto_remove_enabled = models.BooleanField(
        default=True,
        help_text='Automatically remove users from groups when subscription expires'
    )
    
    # Messages
    welcome_message = models.TextField(
        blank=True,
        default='',
        help_text='Welcome message sent to users when added to groups'
    )
    removal_message = models.TextField(
        blank=True,
        default='',
        help_text='Message sent when users are removed from groups'
    )
    
    # Queue Settings
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text='Maximum number of retry attempts for failed operations'
    )
    retry_delay_seconds = models.PositiveIntegerField(
        default=300,  # 5 minutes
        help_text='Delay in seconds between retry attempts'
    )
    
    # Rate Limiting
    rate_limit_per_minute = models.PositiveIntegerField(
        default=30,
        help_text='Maximum Telegram API calls per minute'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Telegram Configuration'
        verbose_name_plural = 'Telegram Configuration'
    
    def __str__(self):
        return f'Telegram Bot: {self.bot_username or "(not configured)"}'
    
    def clean(self):
        """Validate model fields"""
        # Enforce singleton pattern
        if not self.pk and TelegramConfiguration.objects.exists():
            raise ValidationError(
                'Only one Telegram configuration instance is allowed. '
                'Please update the existing configuration instead.'
            )
        
        # Validate bot_username format if provided
        if self.bot_username and not self.bot_username.startswith('@'):
            raise ValidationError({
                'bot_username': 'Bot username must start with @ (e.g., @OxidaneBot)'
            })
        
        # Validate positive integers
        if self.max_retries < 0:
            raise ValidationError({
                'max_retries': 'Max retries must be 0 or greater.'
            })
        
        if self.retry_delay_seconds <= 0:
            raise ValidationError({
                'retry_delay_seconds': 'Retry delay must be greater than 0.'
            })
        
        if self.rate_limit_per_minute <= 0:
            raise ValidationError({
                'rate_limit_per_minute': 'Rate limit must be greater than 0.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance.
        Creates one with defaults if it doesn't exist.
        """
        instance = cls.objects.first()
        if not instance:
            instance = cls.objects.create(
                bot_token='',
                is_enabled=True,
            )
        return instance
    
    def mark_as_connected(self, bot_username=None):
        """Mark the bot as successfully connected"""
        self.is_connected = True
        self.connection_error = ''
        self.last_health_check = timezone.now()
        if bot_username:
            self.bot_username = bot_username
        self.save()
    
    def mark_as_disconnected(self, error_message=''):
        """Mark the bot as disconnected"""
        self.is_connected = False
        self.connection_error = error_message
        self.last_health_check = timezone.now()
        self.save()
    
    def is_healthy(self):
        """Check if the bot is healthy and ready to use"""
        return self.is_enabled and self.is_connected
    
    def set_bot_token(self, token):
        """
        Update the bot token.
        Marks as disconnected since new token needs verification.
        """
        self.bot_token = token
        self.is_connected = False
        self.connection_error = ''
        self.save()
    
    def has_valid_token(self):
        """Check if bot token has valid format (basic check)"""
        if not self.bot_token:
            return False
        # Telegram tokens format: numbers:letters (e.g., 123456789:ABCdefGHI...)
        parts = self.bot_token.split(':')
        return len(parts) == 2 and parts[0].isdigit() and len(parts[1]) > 0
    
    def get_masked_token(self):
        """Get a masked version of the token for display"""
        if not self.bot_token:
            return '(not set)'
        
        parts = self.bot_token.split(':')
        if len(parts) != 2:
            return '***'
        
        # Show first part and mask second part
        return f'{parts[0]}:***{parts[1][-4:]}'
    
    def get_settings(self):
        """Get all settings as a dictionary (excluding sensitive data)"""
        return {
            'bot_username': self.bot_username,
            'is_enabled': self.is_enabled,
            'is_connected': self.is_connected,
            'connection_error': self.connection_error,
            'last_health_check': self.last_health_check,
            'auto_add_enabled': self.auto_add_enabled,
            'auto_remove_enabled': self.auto_remove_enabled,
            'welcome_message': self.welcome_message,
            'removal_message': self.removal_message,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds,
            'rate_limit_per_minute': self.rate_limit_per_minute,
        }
    
    def update_settings(self, settings_dict):
        """
        Update multiple settings at once.
        Protected fields like bot_token and timestamps are ignored.
        Validates before saving - raises ValidationError if invalid.
        """
        protected_fields = ['bot_token', 'created_at', 'updated_at', 'id', 'pk']
        
        # Store original values for rollback on validation error
        original_values = {}
        
        for key, value in settings_dict.items():
            if key not in protected_fields and hasattr(self, key):
                original_values[key] = getattr(self, key)
                setattr(self, key, value)
        
        try:
            self.save()
        except ValidationError:
            # Rollback changes on validation error
            for key, value in original_values.items():
                setattr(self, key, value)
            raise
    
    # ============================================================================
    # ENCRYPTION METHODS (Task 0.5.13)
    # ============================================================================
    
    def encrypt_field(self, field_name):
        """
        Encrypt a sensitive field value.
        
        Encrypts the specified field using Fernet encryption and saves the model.
        The field will be encrypted in-place.
        
        Args:
            field_name (str): Name of the field to encrypt (e.g., 'bot_token')
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            
        Example:
            >>> config = TelegramConfiguration.get_instance()
            >>> config.bot_token = '123456789:ABCdefGHI...'
            >>> config.encrypt_field('bot_token')
            >>> # bot_token is now encrypted
        """
        # List of encryptable fields
        encryptable_fields = [
            'bot_token',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            # Empty field, nothing to encrypt
            return
        
        # Check if already encrypted (basic check)
        if value.startswith('gAAAAA'):  # Fernet tokens start with this
            # Already encrypted, skip
            return
        
        # Encrypt the value
        encrypted_value = encrypt_field(value)
        
        # Set the encrypted value
        setattr(self, field_name, encrypted_value)
        
        # Save the model with only this field updated, bypassing validation
        super(TelegramConfiguration, self).save(update_fields=[field_name])
    
    def decrypt_field(self, field_name):
        """
        Decrypt a sensitive field value.
        
        Decrypts the specified field using Fernet encryption and returns the plaintext.
        The field value in the database remains encrypted.
        
        Args:
            field_name (str): Name of the field to decrypt
            
        Returns:
            str: Decrypted field value, or empty string if field is empty
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            cryptography.fernet.InvalidToken: If decryption fails
            
        Example:
            >>> config = TelegramConfiguration.get_instance()
            >>> decrypted_token = config.decrypt_field('bot_token')
            >>> print(decrypted_token)  # '123456789:ABCdefGHI...'
        """
        # List of encryptable fields
        encryptable_fields = [
            'bot_token',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            return ""
        
        # Check if it's encrypted (basic check)
        if not value.startswith('gAAAAA'):
            # Not encrypted, return as-is
            return value
        
        # Decrypt and return
        return decrypt_field(value)


class TelegramGroup(models.Model):
    """
    Model representing a Telegram group/channel for subscription management.
    Replaces the old TelegramGroupManagement queue-based system.
    This model represents actual Telegram groups with their properties,
    not queue actions for adding/removing users.
    
    Phase 0.5, Task 0.5.7
    """
    # Primary identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Display name for the Telegram group"
    )
    chat_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Telegram chat ID (must start with '-', e.g., -1001234567890)"
    )
    group_key = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Internal identifier for the group (lowercase, no spaces)"
    )
    
    # Group metadata
    description = models.TextField(
        blank=True,
        help_text="Description of the group's purpose and content"
    )
    invite_link = models.URLField(
        blank=True,
        help_text="Telegram invite link for public groups"
    )
    
    # Status and visibility
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this group is currently active"
    )
    is_private = models.BooleanField(
        default=False,
        help_text="Private groups require bot invitation; public groups use invite links"
    )
    
    # Member tracking
    member_count = models.PositiveIntegerField(
        default=0,
        help_text="Current number of members in the group"
    )
    max_members = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum allowed members (null = unlimited)"
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time member count was synced from Telegram"
    )
    
    # Settings
    auto_add_enabled = models.BooleanField(
        default=True,
        help_text="Automatically add users when they subscribe"
    )
    auto_remove_enabled = models.BooleanField(
        default=True,
        help_text="Automatically remove users when subscription expires"
    )
    welcome_message = models.TextField(
        blank=True,
        help_text="Custom welcome message for new members (supports {{user_name}}, {{group_name}} variables)"
    )
    removal_message = models.TextField(
        blank=True,
        help_text="Custom message when removing members (supports {{user_name}}, {{group_name}} variables)"
    )
    notification_enabled = models.BooleanField(
        default=True,
        help_text="Enable notifications for group events"
    )
    
    # Bot permissions in this group
    can_send_messages = models.BooleanField(
        default=True,
        help_text="Bot can send messages in this group"
    )
    can_add_users = models.BooleanField(
        default=True,
        help_text="Bot can add users to this group"
    )
    can_remove_users = models.BooleanField(
        default=True,
        help_text="Bot can remove users from this group"
    )
    can_pin_messages = models.BooleanField(
        default=False,
        help_text="Bot can pin messages in this group"
    )
    can_delete_messages = models.BooleanField(
        default=False,
        help_text="Bot can delete messages in this group"
    )
    is_admin = models.BooleanField(
        default=False,
        help_text="Bot has admin privileges in this group"
    )
    
    # Relationships
    associated_plans = models.ManyToManyField(
        'SubscriptionPlan',
        related_name='telegram_groups',
        blank=True,
        help_text="Subscription plans that grant access to this group"
    )
    
    # Display order
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying groups (lower numbers first)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Telegram Group'
        verbose_name_plural = 'Telegram Groups'
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['chat_id']),
            models.Index(fields=['group_key']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate chat_id format (must be negative for groups)
        if self.chat_id and not self.chat_id.startswith('-'):
            raise ValidationError({
                'chat_id': 'Telegram group chat ID must start with "-" (negative number)'
            })
        
        # Validate member_count is non-negative
        if self.member_count < 0:
            raise ValidationError({
                'member_count': 'Member count cannot be negative'
            })
        
        # Validate max_members if set
        if self.max_members is not None and self.max_members < 0:
            raise ValidationError({
                'max_members': 'Maximum members cannot be negative'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def get_member_count(self):
        """Get current member count."""
        return self.member_count
    
    def can_auto_add(self):
        """Check if auto-add is enabled and group is active."""
        return self.is_active and self.auto_add_enabled
    
    def can_auto_remove(self):
        """Check if auto-remove is enabled and group is active."""
        return self.is_active and self.auto_remove_enabled
    
    def is_accessible_to_plan(self, plan):
        """
        Check if a subscription plan can access this group.
        
        Args:
            plan: SubscriptionPlan instance
            
        Returns:
            bool: True if plan has access to this group
        """
        return self.associated_plans.filter(id=plan.id).exists()
    
    def has_capacity(self):
        """
        Check if group has capacity for new members.
        
        Returns:
            bool: True if group can accept new members
        """
        if self.max_members is None:
            return True  # Unlimited capacity
        return self.member_count < self.max_members
    
    def update_member_count(self, new_count):
        """
        Update member count and sync timestamp.
        
        Args:
            new_count: New member count value
        """
        self.member_count = new_count
        self.last_sync_at = timezone.now()
        self.save()
    
    def get_welcome_message(self, user_name=None):
        """
        Get formatted welcome message with variable substitution.
        
        Args:
            user_name: Optional username to substitute in message
            
        Returns:
            str: Formatted welcome message
        """
        message = self.welcome_message or "Welcome to the group!"
        
        if user_name:
            message = message.replace('{{user_name}}', user_name)
        message = message.replace('{{group_name}}', self.name)
        
        return message
    
    def get_removal_message(self, user_name=None):
        """
        Get formatted removal message with variable substitution.
        
        Args:
            user_name: Optional username to substitute in message
            
        Returns:
            str: Formatted removal message
        """
        message = self.removal_message or "Your subscription has ended."
        
        if user_name:
            message = message.replace('{{user_name}}', user_name)
        message = message.replace('{{group_name}}', self.name)
        
        return message


class PaymentConfiguration(models.Model):
    """
    Singleton model for storing payment gateway configuration.
    Manages Paystack and Stripe API keys, webhook settings, and provider selection.
    
    Phase 0.5, Task 0.5.8
    """
    PROVIDER_CHOICES = [
        ('paystack', 'Paystack (Nigerian Market)'),
        ('stripe', 'Stripe (International)'),
    ]
    
    # Singleton ID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Paystack Configuration
    paystack_public_key = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Paystack public/publishable key (pk_test_... or pk_live_...)'
    )
    paystack_secret_key = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Paystack secret key (sk_test_... or sk_live_...)'
    )
    paystack_webhook_secret = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Paystack webhook secret for signature verification'
    )
    paystack_webhook_url = models.URLField(
        blank=True,
        help_text='Auto-generated webhook URL for Paystack'
    )
    paystack_enabled = models.BooleanField(
        default=True,
        help_text='Enable Paystack as a payment option'
    )
    
    # Stripe Configuration
    stripe_publishable_key = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Stripe publishable key (pk_test_... or pk_live_...)'
    )
    stripe_secret_key = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Stripe secret key (sk_test_... or sk_live_...)'
    )
    stripe_webhook_secret = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Stripe webhook secret (whsec_...)'
    )
    stripe_webhook_url = models.URLField(
        blank=True,
        help_text='Auto-generated webhook URL for Stripe'
    )
    stripe_enabled = models.BooleanField(
        default=False,
        help_text='Enable Stripe as a payment option'
    )
    
    # General Settings
    primary_provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='paystack',
        help_text='Primary payment provider to use'
    )
    is_test_mode = models.BooleanField(
        default=True,
        help_text='Use test API keys (sandbox mode)'
    )
    supported_currencies = models.JSONField(
        default=list,
        blank=True,
        help_text='List of supported currency codes (e.g., ["NGN", "USD", "GBP"])'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Configuration'
        verbose_name_plural = 'Payment Configuration'
    
    def __str__(self):
        return "Payment Configuration"
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate Paystack key formats
        if self.paystack_public_key and not self.paystack_public_key.startswith('pk_'):
            raise ValidationError({
                'paystack_public_key': 'Paystack public key must start with "pk_"'
            })
        
        if self.paystack_secret_key and not self.paystack_secret_key.startswith('sk_'):
            raise ValidationError({
                'paystack_secret_key': 'Paystack secret key must start with "sk_"'
            })
        
        # Validate Stripe key formats
        if self.stripe_publishable_key and not self.stripe_publishable_key.startswith('pk_'):
            raise ValidationError({
                'stripe_publishable_key': 'Stripe publishable key must start with "pk_"'
            })
        
        if self.stripe_secret_key and not self.stripe_secret_key.startswith('sk_'):
            raise ValidationError({
                'stripe_secret_key': 'Stripe secret key must start with "sk_"'
            })
        
        # Validate currency codes
        if self.supported_currencies:
            for currency in self.supported_currencies:
                if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
                    raise ValidationError({
                        'supported_currencies': f'Invalid currency code: {currency}. Must be 3 uppercase letters (e.g., "NGN", "USD")'
                    })
        
        # Enforce singleton pattern
        existing_count = PaymentConfiguration.objects.exclude(pk=self.pk).count()
        if existing_count > 0:
            raise ValidationError('Only one PaymentConfiguration instance is allowed.')
    
    def save(self, *args, **kwargs):
        """Override save to run validation and set defaults."""
        # Set default currencies if empty (only on initial creation)
        if self._state.adding and not self.supported_currencies:
            self.supported_currencies = ['NGN', 'USD']
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance.
        
        Returns:
            PaymentConfiguration: The singleton instance
        """
        instance = cls.objects.first()
        if not instance:
            instance = cls()
            instance.save()
        return instance
    
    # ============================================================================
    # PROVIDER STATUS METHODS
    # ============================================================================
    
    def is_paystack_configured(self):
        """
        Check if Paystack is properly configured.
        
        Returns:
            bool: True if both public and secret keys are set
        """
        return bool(self.paystack_public_key and self.paystack_secret_key)
    
    def is_stripe_configured(self):
        """
        Check if Stripe is properly configured.
        
        Returns:
            bool: True if both publishable and secret keys are set
        """
        return bool(self.stripe_publishable_key and self.stripe_secret_key)
    
    def has_any_provider_configured(self):
        """
        Check if at least one payment provider is configured.
        
        Returns:
            bool: True if any provider is configured
        """
        return self.is_paystack_configured() or self.is_stripe_configured()
    
    # ============================================================================
    # KEY MASKING METHODS
    # ============================================================================
    
    def get_masked_paystack_public_key(self):
        """Get masked Paystack public key for display."""
        return self._mask_key(self.paystack_public_key)
    
    def get_masked_paystack_secret_key(self):
        """Get masked Paystack secret key for display."""
        return self._mask_key(self.paystack_secret_key)
    
    def get_masked_stripe_publishable_key(self):
        """Get masked Stripe publishable key for display."""
        return self._mask_key(self.stripe_publishable_key)
    
    def get_masked_stripe_secret_key(self):
        """Get masked Stripe secret key for display."""
        return self._mask_key(self.stripe_secret_key)
    
    def _mask_key(self, key):
        """
        Mask an API key for secure display.
        
        Args:
            key: The API key to mask
            
        Returns:
            str: Masked key (e.g., "pk_test_***cdef")
        """
        if not key:
            return ""
        
        if len(key) < 4:
            return "***"
        
        # Show prefix and last 4 characters
        if '_' in key:
            prefix = key.split('_')[0] + '_' + key.split('_')[1]
            return f"{prefix}_***{key[-4:]}"
        
        return f"***{key[-4:]}"
    
    # ============================================================================
    # SETTINGS MANAGEMENT METHODS
    # ============================================================================
    
    def get_settings(self):
        """
        Get all configuration settings as a dictionary.
        
        Returns:
            dict: All settings
        """
        return {
            'paystack_public_key': self.paystack_public_key,
            'paystack_secret_key': self.paystack_secret_key,
            'paystack_webhook_secret': self.paystack_webhook_secret,
            'paystack_webhook_url': self.paystack_webhook_url,
            'paystack_enabled': self.paystack_enabled,
            'stripe_publishable_key': self.stripe_publishable_key,
            'stripe_secret_key': self.stripe_secret_key,
            'stripe_webhook_secret': self.stripe_webhook_secret,
            'stripe_webhook_url': self.stripe_webhook_url,
            'stripe_enabled': self.stripe_enabled,
            'primary_provider': self.primary_provider,
            'is_test_mode': self.is_test_mode,
            'supported_currencies': self.supported_currencies,
        }
    
    def get_paystack_settings(self):
        """
        Get Paystack-specific settings.
        
        Returns:
            dict: Paystack settings
        """
        return {
            'public_key': self.paystack_public_key,
            'secret_key': self.paystack_secret_key,
            'webhook_secret': self.paystack_webhook_secret,
            'webhook_url': self.paystack_webhook_url,
            'enabled': self.paystack_enabled,
        }
    
    def get_stripe_settings(self):
        """
        Get Stripe-specific settings.
        
        Returns:
            dict: Stripe settings
        """
        return {
            'publishable_key': self.stripe_publishable_key,
            'secret_key': self.stripe_secret_key,
            'webhook_secret': self.stripe_webhook_secret,
            'webhook_url': self.stripe_webhook_url,
            'enabled': self.stripe_enabled,
        }
    
    def get_active_provider_settings(self):
        """
        Get settings for the active (primary) provider.
        
        Returns:
            dict: Active provider settings with provider name
        """
        settings = {
            'provider': self.primary_provider,
            'is_test_mode': self.is_test_mode,
        }
        
        if self.primary_provider == 'paystack':
            settings.update({
                'public_key': self.paystack_public_key,
                'secret_key': self.paystack_secret_key,
                'webhook_secret': self.paystack_webhook_secret,
            })
        else:  # stripe
            settings.update({
                'public_key': self.stripe_publishable_key,
                'secret_key': self.stripe_secret_key,
                'webhook_secret': self.stripe_webhook_secret,
            })
        
        return settings
    
    def update_settings(self, settings_dict):
        """
        Bulk update settings from dictionary.
        
        Args:
            settings_dict: Dictionary of settings to update
            
        Raises:
            ValidationError: If validation fails
        """
        # Store original values for rollback
        original_values = {}
        readonly_fields = ['id', 'created_at', 'updated_at']
        
        for key, value in settings_dict.items():
            if key in readonly_fields:
                continue  # Skip readonly fields
            
            if hasattr(self, key):
                original_values[key] = getattr(self, key)
                setattr(self, key, value)
        
        try:
            self.save()
        except ValidationError:
            # Rollback changes on validation error
            for key, value in original_values.items():
                setattr(self, key, value)
            raise
    
    # ============================================================================
    # CURRENCY MANAGEMENT METHODS
    # ============================================================================
    
    def add_currency(self, currency_code):
        """
        Add a currency to supported currencies.
        
        Args:
            currency_code: 3-letter currency code (e.g., "GBP")
        """
        if currency_code not in self.supported_currencies:
            self.supported_currencies.append(currency_code)
            self.save()
    
    def remove_currency(self, currency_code):
        """
        Remove a currency from supported currencies.
        
        Args:
            currency_code: 3-letter currency code to remove
        """
        if currency_code in self.supported_currencies:
            self.supported_currencies.remove(currency_code)
            self.save()
    
    def is_currency_supported(self, currency_code):
        """
        Check if a currency is supported.
        
        Args:
            currency_code: Currency code to check
            
        Returns:
            bool: True if currency is supported
        """
        return currency_code in self.supported_currencies
    
    def get_default_currency(self):
        """
        Get the default currency (first in the list).
        
        Returns:
            str: Default currency code
        """
        return self.supported_currencies[0] if self.supported_currencies else "USD"
    
    # ============================================================================
    # ENCRYPTION METHODS (Task 0.5.13)
    # ============================================================================
    
    def encrypt_field(self, field_name):
        """
        Encrypt a sensitive field value.
        
        Encrypts the specified field using Fernet encryption and saves the model.
        The field will be encrypted in-place.
        
        Args:
            field_name (str): Name of the field to encrypt (e.g., 'paystack_secret_key')
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            
        Example:
            >>> config = PaymentConfiguration.get_instance()
            >>> config.paystack_secret_key = 'sk_test_abc123'
            >>> config.encrypt_field('paystack_secret_key')
            >>> # paystack_secret_key is now encrypted
        """
        # List of encryptable fields
        encryptable_fields = [
            'paystack_secret_key',
            'paystack_webhook_secret',
            'stripe_secret_key',
            'stripe_webhook_secret',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            # Empty field, nothing to encrypt
            return
        
        # Check if already encrypted (basic check)
        if value.startswith('gAAAAA'):  # Fernet tokens start with this
            # Already encrypted, skip
            return
        
        # Encrypt the value
        encrypted_value = encrypt_field(value)
        
        # Set the encrypted value
        setattr(self, field_name, encrypted_value)
        
        # Save the model with only this field updated, bypassing validation
        # (encrypted values won't match the format validators like "sk_" prefix)
        super(PaymentConfiguration, self).save(update_fields=[field_name])
    
    def decrypt_field(self, field_name):
        """
        Decrypt a sensitive field value.
        
        Decrypts the specified field using Fernet encryption and returns the plaintext.
        The field value in the database remains encrypted.
        
        Args:
            field_name (str): Name of the field to decrypt
            
        Returns:
            str: Decrypted field value, or empty string if field is empty
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            cryptography.fernet.InvalidToken: If decryption fails
            
        Example:
            >>> config = PaymentConfiguration.get_instance()
            >>> decrypted_key = config.decrypt_field('paystack_secret_key')
            >>> print(decrypted_key)  # 'sk_test_abc123'
        """
        # List of encryptable fields
        encryptable_fields = [
            'paystack_secret_key',
            'paystack_webhook_secret',
            'stripe_secret_key',
            'stripe_webhook_secret',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            return ""
        
        # Check if it's encrypted (basic check)
        if not value.startswith('gAAAAA'):
            # Not encrypted, return as-is
            return value
        
        # Decrypt and return
        return decrypt_field(value)


class EmailConfiguration(models.Model):
    """
    Singleton model for storing email/SMTP configuration.
    Manages SMTP server settings, credentials, and connection status.
    
    Phase 0.5, Task 0.5.9
    """
    # Singleton ID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # SMTP Server Settings
    smtp_host = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='SMTP server hostname (e.g., smtp.gmail.com)'
    )
    smtp_port = models.PositiveIntegerField(
        default=587,
        help_text='SMTP server port (25, 587 for TLS, 465 for SSL)'
    )
    use_tls = models.BooleanField(
        default=True,
        help_text='Use TLS encryption (port 587)'
    )
    use_ssl = models.BooleanField(
        default=False,
        help_text='Use SSL encryption (port 465)'
    )
    
    # Authentication
    smtp_username = models.EmailField(
        max_length=255,
        blank=True,
        default='',
        help_text='SMTP username (usually an email address)'
    )
    smtp_password = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='SMTP password (will be encrypted in Phase 2)'
    )
    
    # Sender Information
    from_email = models.EmailField(
        max_length=255,
        blank=True,
        default='',
        help_text='Default "From" email address'
    )
    from_name = models.CharField(
        max_length=200,
        default='OxiWorld',
        help_text='Default "From" name'
    )
    
    # Status
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable email sending'
    )
    is_connected = models.BooleanField(
        default=False,
        help_text='Last connection test was successful'
    )
    connection_error = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Last connection error message'
    )
    last_test_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Last connection test timestamp'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Configuration'
        verbose_name_plural = 'Email Configuration'
    
    def __str__(self):
        return "Email Configuration"
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate SMTP port range
        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise ValidationError({
                'smtp_port': 'SMTP port must be between 1 and 65535'
            })
        
        # Cannot enable both TLS and SSL
        if self.use_tls and self.use_ssl:
            raise ValidationError('Cannot enable both TLS and SSL. Choose one.')
        
        # Must have at least TLS or SSL
        if not self.use_tls and not self.use_ssl:
            raise ValidationError('Either TLS or SSL must be enabled for security.')
        
        # Validate from_name length
        if len(self.from_name) > 200:
            raise ValidationError({
                'from_name': 'From name must be 200 characters or less'
            })
        
        # Enforce singleton pattern
        existing_count = EmailConfiguration.objects.exclude(pk=self.pk).count()
        if existing_count > 0:
            raise ValidationError('Only one EmailConfiguration instance is allowed.')
    
    def save(self, *args, **kwargs):
        """Override save to run validation and normalize data."""
        # Normalize from_email to lowercase
        if self.from_email:
            self.from_email = self.from_email.lower()
        
        # Truncate connection_error if too long
        if self.connection_error and len(self.connection_error) > 500:
            self.connection_error = self.connection_error[:500]
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance.
        
        Returns:
            EmailConfiguration: The singleton instance
        """
        instance = cls.objects.first()
        if not instance:
            instance = cls()
            instance.save()
        return instance
    
    # ============================================================================
    # CONNECTION TESTING METHODS
    # ============================================================================
    
    def test_connection(self):
        """
        Test SMTP connection with current settings.
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        from django.utils import timezone
        import smtplib
        import ssl
        
        # Update last test timestamp
        self.last_test_at = timezone.now()
        
        # Validate required fields
        if not self.smtp_host:
            return {
                'success': False,
                'message': 'SMTP host is required'
            }
        
        if not self.smtp_username or not self.smtp_password:
            return {
                'success': False,
                'message': 'SMTP credentials (username and password) are required'
            }
        
        try:
            if self.use_ssl:
                # SSL connection (port 465)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=10) as server:
                    server.login(self.smtp_username, self.smtp_password)
            else:
                # TLS connection (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
            
            # Connection successful
            self.mark_as_connected()
            self.save()
            
            return {
                'success': True,
                'message': f'Successfully connected to {self.smtp_host}:{self.smtp_port}'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f'Authentication failed: {str(e)}'
            self.mark_as_disconnected(error_msg)
            self.save()
            return {
                'success': False,
                'message': error_msg
            }
            
        except smtplib.SMTPConnectError as e:
            error_msg = f'Failed to connect: {str(e)}'
            self.mark_as_disconnected(error_msg)
            self.save()
            return {
                'success': False,
                'message': error_msg
            }
            
        except smtplib.SMTPException as e:
            error_msg = f'SMTP error: {str(e)}'
            self.mark_as_disconnected(error_msg)
            self.save()
            return {
                'success': False,
                'message': error_msg
            }
            
        except Exception as e:
            error_msg = f'Connection error: {str(e)}'
            self.mark_as_disconnected(error_msg)
            self.save()
            return {
                'success': False,
                'message': error_msg
            }
    
    def mark_as_connected(self):
        """Mark configuration as successfully connected."""
        self.is_connected = True
        self.connection_error = None
    
    def mark_as_disconnected(self, error_message):
        """
        Mark configuration as disconnected with error.
        
        Args:
            error_message (str): Error message to store
        """
        self.is_connected = False
        self.connection_error = error_message[:500] if error_message else None
    
    # ============================================================================
    # SECURITY METHODS
    # ============================================================================
    
    def get_masked_password(self):
        """
        Get masked password for display purposes.
        
        Returns:
            str: Masked password (e.g., "***23" for "password123")
        """
        if not self.smtp_password:
            return "(not set)"
        
        if len(self.smtp_password) <= 3:
            return "***"
        
        # Show last 2 characters
        return "***" + self.smtp_password[-2:]
    
    def is_configured(self):
        """
        Check if email is properly configured.
        
        Returns:
            bool: True if all required fields are set
        """
        return bool(
            self.smtp_host and
            self.smtp_port and
            self.smtp_username and
            self.smtp_password and
            self.from_email
        )
    
    # ============================================================================
    # SETTINGS MANAGEMENT METHODS
    # ============================================================================
    
    def get_settings(self):
        """
        Get all settings as a dictionary.
        
        Returns:
            dict: All configuration settings
        """
        return {
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'smtp_password': self.smtp_password,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'use_tls': self.use_tls,
            'use_ssl': self.use_ssl,
            'is_enabled': self.is_enabled,
            'is_connected': self.is_connected,
            'connection_error': self.connection_error,
        }
    
    def get_smtp_settings_for_django(self):
        """
        Get SMTP settings in Django settings format.
        
        Returns:
            dict: Settings formatted for Django EMAIL_* settings
        """
        return {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': self.smtp_host,
            'EMAIL_PORT': self.smtp_port,
            'EMAIL_HOST_USER': self.smtp_username,
            'EMAIL_HOST_PASSWORD': self.smtp_password,
            'EMAIL_USE_TLS': self.use_tls,
            'EMAIL_USE_SSL': self.use_ssl,
            'DEFAULT_FROM_EMAIL': self.from_email or f'{self.from_name} <{self.smtp_username}>',
        }
    
    def update_settings(self, settings_dict):
        """
        Update multiple settings at once with validation.
        
        Args:
            settings_dict (dict): Dictionary of settings to update
            
        Raises:
            ValidationError: If validation fails
        """
        # Save original values for rollback
        original_values = {}
        
        # Readonly fields that cannot be updated
        readonly_fields = ['id', 'created_at', 'updated_at', 'last_test_at']
        
        try:
            # Update allowed fields
            for key, value in settings_dict.items():
                if key in readonly_fields:
                    continue
                    
                if hasattr(self, key):
                    original_values[key] = getattr(self, key)
                    setattr(self, key, value)
            
            # Validate before saving
            self.full_clean()
            self.save()
            
        except ValidationError as e:
            # Rollback changes
            for key, value in original_values.items():
                setattr(self, key, value)
            raise e
    
    # ============================================================================
    # ENCRYPTION METHODS (Task 0.5.13)
    # ============================================================================
    
    def encrypt_field(self, field_name):
        """
        Encrypt a sensitive field value.
        
        Encrypts the specified field using Fernet encryption and saves the model.
        The field will be encrypted in-place.
        
        Args:
            field_name (str): Name of the field to encrypt (e.g., 'smtp_password')
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            
        Example:
            >>> config = EmailConfiguration.get_instance()
            >>> config.smtp_password = 'mypassword123'
            >>> config.encrypt_field('smtp_password')
            >>> # smtp_password is now encrypted
        """
        # List of encryptable fields
        encryptable_fields = [
            'smtp_password',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            # Empty field, nothing to encrypt
            return
        
        # Check if already encrypted (basic check)
        if value.startswith('gAAAAA'):  # Fernet tokens start with this
            # Already encrypted, skip
            return
        
        # Encrypt the value
        encrypted_value = encrypt_field(value)
        
        # Set the encrypted value
        setattr(self, field_name, encrypted_value)
        
        # Save the model with only this field updated, bypassing validation
        super(EmailConfiguration, self).save(update_fields=[field_name])
    
    def decrypt_field(self, field_name):
        """
        Decrypt a sensitive field value.
        
        Decrypts the specified field using Fernet encryption and returns the plaintext.
        The field value in the database remains encrypted.
        
        Args:
            field_name (str): Name of the field to decrypt
            
        Returns:
            str: Decrypted field value, or empty string if field is empty
            
        Raises:
            ValueError: If field_name is invalid or not encryptable
            AttributeError: If field doesn't exist on the model
            cryptography.fernet.InvalidToken: If decryption fails
            
        Example:
            >>> config = EmailConfiguration.get_instance()
            >>> decrypted_password = config.decrypt_field('smtp_password')
            >>> print(decrypted_password)  # 'mypassword123'
        """
        # List of encryptable fields
        encryptable_fields = [
            'smtp_password',
        ]
        
        if field_name not in encryptable_fields:
            raise ValueError(
                f"Field '{field_name}' is not encryptable. "
                f"Encryptable fields are: {', '.join(encryptable_fields)}"
            )
        
        # Get the current field value
        value = getattr(self, field_name)
        
        if not value:
            return ""
        
        # Check if it's encrypted (basic check)
        if not value.startswith('gAAAAA'):
            # Not encrypted, return as-is
            return value
        
        # Decrypt and return
        return decrypt_field(value)


# ============================================================================
# EXCHANGE RATE MODEL (Phase 0.5, Task 0.5.10)
# ============================================================================

class ExchangeRate(models.Model):
    """
    Model to store currency exchange rates for multi-currency pricing.
    
    Supports:
    - Direct currency pair rates (e.g., USD -> NGN)
    - Automatic reverse rate calculation (e.g., NGN -> USD)
    - Currency conversion with precision
    - Staleness detection for rate updates
    - Bulk rate updates
    
    Design:
    - Base currency is typically USD (industry standard)
    - Rates stored as Decimal for precision
    - Last update timestamp for staleness checks
    - Unique constraint on currency pairs
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    base_currency = models.CharField(
        max_length=3,
        help_text="Base currency code (e.g., USD)"
    )
    target_currency = models.CharField(
        max_length=3,
        help_text="Target currency code (e.g., NGN)"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Exchange rate from base to target currency"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time this rate was updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exchange_rates'
        verbose_name = 'Exchange Rate'
        verbose_name_plural = 'Exchange Rates'
        unique_together = [['base_currency', 'target_currency']]
        indexes = [
            models.Index(fields=['base_currency', 'target_currency']),
            models.Index(fields=['last_updated']),
        ]
        ordering = ['base_currency', 'target_currency']
    
    def __str__(self):
        """String representation."""
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"
    
    def clean(self):
        """Validate exchange rate data."""
        errors = {}
        
        # Note: Normalization happens in save() before validation
        
        # Validate currency code length
        if self.base_currency and len(self.base_currency) != 3:
            errors['base_currency'] = 'Currency code must be exactly 3 characters'
        
        if self.target_currency and len(self.target_currency) != 3:
            errors['target_currency'] = 'Currency code must be exactly 3 characters'
        
        # Validate rate is positive and non-zero
        if self.rate is not None:
            if self.rate <= 0:
                errors['rate'] = 'Exchange rate must be greater than zero'
        
        # Validate base and target are different
        if self.base_currency and self.target_currency:
            if self.base_currency == self.target_currency:
                errors['target_currency'] = 'Base and target currencies must be different'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save to normalize and validate."""
        # Normalize currency codes BEFORE validation
        if self.base_currency:
            self.base_currency = self.base_currency.strip().upper()
        if self.target_currency:
            self.target_currency = self.target_currency.strip().upper()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ========================================================================
    # RATE RETRIEVAL METHODS
    # ========================================================================
    
    @classmethod
    def get_rate(cls, from_currency, to_currency):
        """
        Get exchange rate between two currencies.
        
        Supports:
        - Direct rates (USD -> NGN)
        - Reverse rates (NGN -> USD, calculated as 1/rate)
        - Same currency (returns 1.0)
        
        Args:
            from_currency (str): Source currency code
            to_currency (str): Target currency code
            
        Returns:
            Decimal: Exchange rate, or None if not found
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency
        if from_currency == to_currency:
            return Decimal('1.00')
        
        # Try direct rate
        try:
            rate = cls.objects.get(
                base_currency=from_currency,
                target_currency=to_currency
            )
            return rate.rate
        except cls.DoesNotExist:
            pass
        
        # Try reverse rate
        try:
            rate = cls.objects.get(
                base_currency=to_currency,
                target_currency=from_currency
            )
            return Decimal('1') / rate.rate
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_all_rates_for_base(cls, base_currency):
        """
        Get all exchange rates for a base currency.
        
        Args:
            base_currency (str): Base currency code
            
        Returns:
            dict: Dictionary of {target_currency: rate}
        """
        base_currency = base_currency.upper()
        rates = cls.objects.filter(base_currency=base_currency)
        return {rate.target_currency: rate.rate for rate in rates}
    
    @classmethod
    def get_supported_currencies(cls):
        """
        Get list of all supported currencies.
        
        Returns:
            set: Set of currency codes
        """
        rates = cls.objects.all()
        currencies = set()
        for rate in rates:
            currencies.add(rate.base_currency)
            currencies.add(rate.target_currency)
        return currencies
    
    @classmethod
    def is_supported(cls, currency_code):
        """
        Check if a currency is supported.
        
        Args:
            currency_code (str): Currency code to check
            
        Returns:
            bool: True if currency is supported
        """
        currency_code = currency_code.upper()
        return cls.objects.filter(
            models.Q(base_currency=currency_code) |
            models.Q(target_currency=currency_code)
        ).exists()
    
    # ========================================================================
    # CURRENCY CONVERSION METHODS
    # ========================================================================
    
    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency, round_result=False):
        """
        Convert amount from one currency to another.
        
        Args:
            amount (Decimal): Amount to convert
            from_currency (str): Source currency
            to_currency (str): Target currency
            round_result (bool): Whether to round to 2 decimal places
            
        Returns:
            Decimal: Converted amount, or None if rate not found
        """
        rate = cls.get_rate(from_currency, to_currency)
        
        if rate is None:
            return None
        
        result = amount * rate
        
        if round_result:
            from decimal import ROUND_HALF_UP
            return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return result
    
    # ========================================================================
    # RATE UPDATE METHODS
    # ========================================================================
    
    @classmethod
    def update_rate(cls, base_currency, target_currency, rate):
        """
        Update or create an exchange rate.
        
        Args:
            base_currency (str): Base currency code
            target_currency (str): Target currency code
            rate (Decimal): Exchange rate
            
        Returns:
            ExchangeRate: The updated or created rate object
        """
        base_currency = base_currency.upper()
        target_currency = target_currency.upper()
        
        obj, created = cls.objects.update_or_create(
            base_currency=base_currency,
            target_currency=target_currency,
            defaults={'rate': rate}
        )
        return obj
    
    @classmethod
    def bulk_update_rates(cls, base_currency, rates_dict):
        """
        Bulk update multiple exchange rates for a base currency.
        
        Args:
            base_currency (str): Base currency code
            rates_dict (dict): Dictionary of {target_currency: rate}
            
        Returns:
            list: List of created/updated ExchangeRate objects
        """
        base_currency = base_currency.upper()
        results = []
        
        for target_currency, rate in rates_dict.items():
            obj = cls.update_rate(base_currency, target_currency, rate)
            results.append(obj)
        
        return results
    
    def is_stale(self, hours=24):
        """
        Check if this exchange rate is stale.
        
        Args:
            hours (int): Number of hours before rate is considered stale
            
        Returns:
            bool: True if rate is older than specified hours
        """
        if not self.last_updated:
            return True
        
        age = timezone.now() - self.last_updated
        return age > timedelta(hours=hours)
    
    @classmethod
    def get_stale_rates(cls, hours=24):
        """
        Get all rates that are older than specified hours.
        
        Args:
            hours (int): Number of hours before rate is considered stale
            
        Returns:
            QuerySet: ExchangeRate objects that need updating
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(last_updated__lt=cutoff_time)
    
    @classmethod
    def needs_update(cls, hours=24):
        """
        Check if any rates need updating.
        
        Args:
            hours (int): Number of hours before rate is considered stale
            
        Returns:
            bool: True if no rates exist or any rates are stale
        """
        if not cls.objects.exists():
            return True
        
        return cls.get_stale_rates(hours=hours).exists()

