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

class CouponCode(models.Model):
    """Coupon codes for discounts on pricing plans"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'), 
        ('expired', 'Expired'),
        ('used_up', 'Used Up'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="Coupon code (e.g., SAVE20)")
    name = models.CharField(max_length=100, help_text="Internal name for the coupon")
    description = models.TextField(blank=True, help_text="Description of the offer")
    
    # Discount settings
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (1-100) or fixed amount")
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum purchase amount")
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount amount (for percentage discounts)")
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of uses (null = unlimited)")
    usage_count = models.PositiveIntegerField(default=0, help_text="Current usage count")
    usage_limit_per_user = models.PositiveIntegerField(default=1, help_text="Uses per user")
    
    # Validity
    valid_from = models.DateTimeField(help_text="Coupon valid from this date")
    valid_until = models.DateTimeField(help_text="Coupon valid until this date")
    
    # Plan restrictions
    applicable_plans = models.ManyToManyField(PricingPlan, blank=True, help_text="Restrict to specific plans (empty = all plans)")
    applicable_categories = models.JSONField(default=list, help_text="Restrict to plan categories: ['mentorship', 'signals', 'vip']")
    
    # Settings
    is_active = models.BooleanField(default=True)
    first_time_users_only = models.BooleanField(default=False, help_text="Only for users with no previous subscriptions")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.code} ({self.get_discount_display()})"
    
    def get_discount_display(self):
        """Get human readable discount display"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"${self.discount_value} off"
    
    @property
    def status(self):
        """Get current status of the coupon"""
        now = timezone.now()
        
        if not self.is_active:
            return 'inactive'
        elif now < self.valid_from or now > self.valid_until:
            return 'expired'
        elif self.usage_limit and self.usage_count >= self.usage_limit:
            return 'used_up'
        else:
            return 'active'
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        return self.status == 'active'
    
    def validate_for_user(self, user, plan):
        """Validate if coupon can be used by user for specific plan"""
        if not self.is_valid:
            return False, f"Coupon {self.code} is not valid"
        
        # Check plan restrictions
        if self.applicable_plans.exists() and plan not in self.applicable_plans.all():
            return False, "Coupon not applicable to this plan"
            
        if self.applicable_categories and plan.plan_category not in self.applicable_categories:
            return False, "Coupon not applicable to this plan category"
        
        # Check first-time user restriction
        if self.first_time_users_only:
            if SignalSubscription.objects.filter(user=user, payment_status='verified').exists():
                return False, "Coupon only for first-time users"
        
        # Check per-user usage limit
        user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
        if user_usage >= self.usage_limit_per_user:
            return False, f"You've already used this coupon {self.usage_limit_per_user} time(s)"
        
        return True, "Valid"
    
    def calculate_discount(self, amount):
        """Calculate discount amount for given price"""
        if self.discount_type == 'percentage':
            discount = (amount * self.discount_value) / 100
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
        else:
            discount = min(self.discount_value, amount)
        
        return min(discount, amount)  # Never exceed the original amount
    
    def apply_discount(self, user, plan, amount):
        """Apply discount and record usage"""
        is_valid, message = self.validate_for_user(user, plan)
        if not is_valid:
            raise ValidationError(message)
        
        if amount < self.minimum_amount:
            raise ValidationError(f"Minimum purchase amount is ${self.minimum_amount}")
        
        discount_amount = self.calculate_discount(amount)
        final_amount = amount - discount_amount
        
        return {
            'original_amount': amount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'coupon_code': self.code
        }

class CouponUsage(models.Model):
    """Track coupon usage by users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(CouponCode, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    subscription = models.ForeignKey('SignalSubscription', on_delete=models.CASCADE, related_name='coupon_usage')
    
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"

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
    
    # Coupon information
    coupon_used = models.ForeignKey(CouponCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
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