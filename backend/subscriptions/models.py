# Pricing and subscription management models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid
import json
from django.core.exceptions import ValidationError
from django.db import transaction

User = get_user_model()

class PricingPlan(models.Model):
    """Master pricing control for all platform services"""
    PLAN_CATEGORIES = [
        ('mentorship', 'Mentorship'),  # One-time lifetime access
        ('signals', 'Signals'),        # Recurring subscriptions
    ]
    
    BILLING_CYCLES = [
        ('one_time', 'One Time'),      # For mentorship
        ('weekly', 'Weekly'),          # For signals
        ('monthly', 'Monthly'),        # For signals
    ]
    
    PLAN_TYPES = [
        # Mentorship - One-time payment for lifetime course access
        ('mentorship', 'Mentorship Program'),
        
        # Signals - Duration-based recurring subscriptions
        ('signals_weekly', 'Weekly Signals'),
        ('signals_monthly', 'Monthly Signals'),
        ('vip_monthly', 'VIP Signals'),  # Premium tier with extra features
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('NGN', 'Nigerian Naira'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_type = models.CharField(max_length=25, choices=PLAN_TYPES, unique=True)
    plan_category = models.CharField(max_length=15, choices=PLAN_CATEGORIES)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES)
    name = models.CharField(max_length=100, help_text="Display name for users")
    description = models.TextField(help_text="Plan description for users")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Duration (for signals only - mentorship is lifetime)
    duration_days = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Subscription duration in days (null for mentorship/lifetime access)"
    )
    
    # Access levels
    gives_course_access = models.BooleanField(
        default=False, 
        help_text="Grants access to premium courses (mentorship only)"
    )
    gives_signals_access = models.BooleanField(
        default=False,
        help_text="Grants access to trading signals (signals plans only)"
    )
    telegram_group_key = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Telegram group identifier: 'mentorship', 'signals', or 'vip'"
    )
    
    # Discounts
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="0-100")
    promotional_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    promotion_start = models.DateTimeField(null=True, blank=True)
    promotion_end = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Highlight this plan to users")
    sort_order = models.PositiveIntegerField(default=0)
    
    # SEO and marketing
    features_list = models.JSONField(default=list, help_text="List of plan features for display")
    call_to_action = models.CharField(max_length=50, default="Get Started", help_text="Button text")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'price']
        
    def __str__(self):
        return f"{self.name} - {self.currency} {self.current_price}"
    
    @property
    def current_price(self):
        """Get current effective price (considering promotions)"""
        now = timezone.now()
        
        # Check if promotional price is active
        if (self.promotional_price and 
            self.promotion_start and self.promotion_end and
            self.promotion_start <= now <= self.promotion_end):
            return self.promotional_price
            
        # Check if discount percentage is active
        if self.discount_percentage > 0:
            discount_amount = (self.price * self.discount_percentage) / 100
            return self.price - discount_amount
            
        return self.price
    
    @property
    def is_on_promotion(self):
        """Check if plan is currently on promotion"""
        return self.current_price < self.price
    
    @property
    def savings_amount(self):
        """Calculate savings if on promotion"""
        if self.is_on_promotion:
            return self.price - self.current_price
        return Decimal('0.00')
    
    def get_access_level(self):
        """Get bot access level based on plan category"""
        if self.plan_category == 'mentorship':
            return 'mentorship'
        elif self.plan_type == 'vip_monthly':
            return 'vip'
        else:
            return 'signals'


class SignalSubscription(models.Model):
    """Handle all subscription payments (signals and mentorship) and Telegram access"""
    PLAN_TYPES = [
        # Mentorship - one-time payment
        ('mentorship', 'Mentorship Program'),
        
        # Signals - recurring subscriptions
        ('signals_weekly', 'Weekly Signals'),
        ('signals_monthly', 'Monthly Signals'),
        ('vip_monthly', 'VIP Signals'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('verified', 'Payment Verified'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    TELEGRAM_STATUS = [
        ('not_added', 'Not Added to Group'),
        ('pending_add', 'Pending Addition'),
        ('added', 'Added to Group'),
        ('removed', 'Removed from Group'),
        ('failed_add', 'Failed to Add'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signal_subscriptions')
    
    # Subscription details
    plan_type = models.CharField(max_length=25, choices=PLAN_TYPES)
    pricing_plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, null=True)
    
    # Coupon information (will be migrated to new Coupon model)
    coupon_used = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Amount before coupon discount")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount applied from coupon")
    
    # Payment information
    paystack_reference = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Subscription period
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    auto_renewal = models.BooleanField(default=False)
    
    # Telegram integration
    telegram_username = models.CharField(max_length=100, help_text="User's Telegram username")
    telegram_group_name = models.CharField(max_length=100, blank=True)
    telegram_status = models.CharField(max_length=15, choices=TELEGRAM_STATUS, default='not_added')
    telegram_added_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signal_subscriptions'
        ordering = ['-created_at']
        indexes = [
            # Performance optimization indexes
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['payment_status', '-created_at']),
            models.Index(fields=['plan_type', 'payment_status']),
            models.Index(fields=['subscription_start', 'subscription_end']),
            models.Index(fields=['paystack_reference']),  # For payment lookups
            models.Index(fields=['telegram_status']),
            models.Index(fields=['updated_at']),  # For recent changes queries
            
            # Composite indexes for common queries
            models.Index(fields=['user', 'payment_status', '-created_at']),
            models.Index(fields=['plan_type', 'subscription_start', 'subscription_end']),
            models.Index(fields=['telegram_status', 'telegram_added_at']),
        ]
        
        # Database constraints for data integrity
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_paid__gte=0),
                name='positive_amount_paid'
            ),
            models.CheckConstraint(
                check=models.Q(
                    subscription_end__gte=models.F('subscription_start')
                ) | models.Q(subscription_end__isnull=True),
                name='valid_subscription_period'
            ),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.plan_type} - {self.payment_status}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        if self.payment_status != 'verified':
            return False
        if not self.subscription_end:
            return False
        return timezone.now() <= self.subscription_end
    
    @property
    def days_remaining(self):
        """Get days remaining in subscription"""
        if not self.is_active:
            return 0
        delta = self.subscription_end - timezone.now()
        return max(0, delta.days)
    
    def mark_payment_verified(self):
        """Mark payment as verified and set subscription dates"""
        self.payment_status = 'verified'
        self.payment_verified_at = timezone.now()
        self.subscription_start = timezone.now()
        
        # Set end date based on plan type
        if 'weekly' in self.plan_type:
            self.subscription_end = self.subscription_start + timezone.timedelta(days=7)
        elif 'monthly' in self.plan_type:
            self.subscription_end = self.subscription_start + timezone.timedelta(days=30)
        elif 'yearly' in self.plan_type:
            self.subscription_end = self.subscription_start + timezone.timedelta(days=365)
        elif self.plan_type == 'mentorship_basic':
            # One-time access, set to 1 year for now
            self.subscription_end = self.subscription_start + timezone.timedelta(days=365)
        else:
            # Legacy handling
            if self.plan_type in ['weekly']:
                self.subscription_end = self.subscription_start + timezone.timedelta(days=7)
            elif self.plan_type in ['monthly', 'vip']:
                self.subscription_end = self.subscription_start + timezone.timedelta(days=30)
            
        self.telegram_status = 'pending_add'
        self.save()
    
    @property  
    def plan_category(self):
        """Get plan category for bot integration"""
        if self.pricing_plan:
            return self.pricing_plan.plan_category
        
        # Legacy mapping for backward compatibility
        if 'mentorship' in self.plan_type or self.plan_type == 'basic':
            return 'mentorship'
        elif 'signals' in self.plan_type or self.plan_type in ['weekly', 'monthly']:
            return 'signals'  
        elif 'vip' in self.plan_type or self.plan_type == 'vip':
            return 'vip'
        else:
            return 'mentorship'  # Default fallback
    
    @property
    def access_level(self):
        """Get bot access level based on plan category"""
        category_mapping = {
            'mentorship': 'basic',
            'signals': 'signals',
            'vip': 'vip'
        }
        return category_mapping.get(self.plan_category, 'basic')
    
    @property
    def telegram_groups(self):
        """Get list of telegram groups user should have access to"""
        if self.pricing_plan and self.pricing_plan.telegram_groups:
            return self.pricing_plan.telegram_groups
        
        # Legacy mapping
        group_mapping = {
            'mentorship': ['mentorship'],
            'signals': ['signals'],
            'vip': ['mentorship', 'signals', 'vip']
        }
        return group_mapping.get(self.plan_category, ['mentorship'])
    
    def get_final_amount(self):
        """Get final amount after coupon discount"""
        if self.coupon_used and self.discount_amount:
            return self.amount_paid  # amount_paid is already the final amount
        return self.amount_paid
    
    def get_savings(self):
        """Get savings from coupon usage"""
        return self.discount_amount if self.discount_amount else Decimal('0.00')
    
    def create_audit_log(self, action_type, admin_user, changes_made=None, reason="", request=None):
        """Create audit log entry for subscription changes"""
        from .audit_models import AdminActionLog, SubscriptionChangeLog
        
        # Create main audit log entry
        audit_log = AdminActionLog.objects.create(
            admin_user=admin_user,
            action_type=action_type,
            sensitivity='FINANCIAL',
            status='SUCCESS',
            ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR') if request else None,
            user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT', '')[:500] if request else '',
            target_user_id=self.user.id,
            target_subscription_id=self.id,
            action_description=f"{action_type} for subscription {self.id}",
            changes_made=changes_made or {},
        )
        
        # Create detailed change logs if changes were provided
        if changes_made:
            for field_name, change_data in changes_made.items():
                SubscriptionChangeLog.objects.create(
                    subscription=self,
                    admin_action_log=audit_log,
                    change_type=self._determine_change_type(field_name, change_data),
                    field_name=field_name,
                    previous_value=change_data.get('from'),
                    new_value=change_data.get('to'),
                    reason=reason,
                    financial_impact=self._calculate_financial_impact(field_name, change_data)
                )
        
        return audit_log
    
    def _determine_change_type(self, field_name, change_data):
        """Determine the type of change for audit logging"""
        change_type_mapping = {
            'payment_status': 'STATUS_CHANGE',
            'subscription_end': 'PERIOD_EXTENSION' if change_data.get('to') > change_data.get('from', timezone.now()) else 'PERIOD_SHORTENING',
            'amount_paid': 'AMOUNT_ADJUSTMENT',
            'plan_type': 'PLAN_UPGRADE',  # Determine upgrade/downgrade based on business logic
            'telegram_status': 'TELEGRAM_UPDATE',
            'admin_notes': 'ADMIN_NOTE_ADDED',
        }
        return change_type_mapping.get(field_name, 'STATUS_CHANGE')
    
    def _calculate_financial_impact(self, field_name, change_data):
        """Calculate financial impact of changes"""
        if field_name == 'amount_paid':
            old_amount = Decimal(str(change_data.get('from', 0)))
            new_amount = Decimal(str(change_data.get('to', 0)))
            return new_amount - old_amount
        elif field_name == 'payment_status' and change_data.get('to') == 'refunded':
            return -self.amount_paid
        return None
    
    def _serialize_value(self, value):
        """Convert values to JSON-serializable format"""
        if isinstance(value, Decimal):
            return float(value)
        elif hasattr(value, 'isoformat'):  # datetime objects
            return value.isoformat()
        elif hasattr(value, '__dict__'):  # Model instances
            return str(value)
        return value
    
    def update_with_audit(self, admin_user, updates, reason="", request=None):
        """Update subscription fields with automatic audit logging"""
        changes_made = {}
        
        # Capture before values
        for field_name in updates.keys():
            if hasattr(self, field_name):
                old_value = getattr(self, field_name)
                changes_made[field_name] = {'from': self._serialize_value(old_value)}
        
        # Apply updates
        for field_name, new_value in updates.items():
            if hasattr(self, field_name):
                setattr(self, field_name, new_value)
                changes_made[field_name]['to'] = self._serialize_value(new_value)
        
        # Save and create audit trail
        with transaction.atomic():
            self.save()
            self.create_audit_log('MODIFY_SUBSCRIPTION', admin_user, changes_made, reason, request)
    
    def mark_telegram_added(self, group_name):
        """Mark user as added to Telegram group"""
        self.telegram_status = 'added'
        self.telegram_group_name = group_name
        self.telegram_added_at = timezone.now()
        self.save()

class PaymentTransaction(models.Model):
    """Track all payment transactions"""
    TRANSACTION_TYPES = [
        ('course_purchase', 'Course Purchase'),
        ('signal_subscription', 'Signal Subscription'),
        ('bundle_purchase', 'Bundle Purchase'),
        ('refund', 'Refund'),
    ]
    
    PAYMENT_METHODS = [
        ('paystack', 'Paystack'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment processing
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    processor_response = models.JSONField(null=True, blank=True, help_text="Raw payment processor response")
    
    # Related objects
    signal_subscription = models.ForeignKey(SignalSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    course_access = models.ForeignKey('courses.CourseAccess', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=10, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency} - {self.status}"

class TelegramGroupManagement(models.Model):
    """Queue system for Telegram group additions/removals"""
    ACTION_TYPES = [
        ('add', 'Add User to Group'),
        ('remove', 'Remove User from Group'),
    ]
    
    ACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    signal_subscription = models.ForeignKey(SignalSubscription, on_delete=models.CASCADE)
    
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    telegram_username = models.CharField(max_length=100)
    telegram_group = models.CharField(max_length=100)
    
    status = models.CharField(max_length=10, choices=ACTION_STATUS, default='pending')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='telegram_actions_processed')
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.action_type.title()} @{self.telegram_username} - {self.status}"

# Mentorship Models

# Note: Mentorship is now handled through SignalSubscription with plan_type='mentorship'
# The separate MentorshipPlan and MentorshipSubscription models have been deprecated
# All pricing is managed through PricingPlan model


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
    currency_preference = models.CharField(max_length=3, default='USD', 
                                          choices=PricingPlan.CURRENCY_CHOICES)
    
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
    """User subscriptions (replaces SignalSubscription, more flexible)"""
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
    pricing_plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT)
    
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
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billing_profile', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.billing_profile.user.email} - {self.pricing_plan.name} ({self.status})"
    
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
        related_name='referral',
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

