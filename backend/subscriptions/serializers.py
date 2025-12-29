from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    SubscriptionPlan, Subscription, Coupon, Feature,
    BillingProfile, PaymentMethod, Payment, TelegramGroup, TelegramConfiguration,
    PaymentConfiguration, EmailConfiguration
)

User = get_user_model()


class BillingProfileSerializer(serializers.ModelSerializer):
    """Serializer for BillingProfile with Telegram verification info"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_verification_code_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = BillingProfile
        fields = [
            'id', 'user', 'user_email', 'telegram_user_id', 'telegram_username',
            'telegram_verified', 'telegram_verified_at', 'verification_code',
            'verification_code_expires_at', 'is_verification_code_valid',
            'country', 'currency_preference', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'telegram_verified', 'telegram_verified_at',
            'verification_code', 'verification_code_expires_at', 'created_at', 'updated_at'
        ]
    
    def get_is_verification_code_valid(self, obj):
        """Check if verification code is still valid"""
        return obj.is_verification_code_valid()


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for saved payment methods"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'payment_type', 'card_last4', 'card_brand', 
            'card_exp_month', 'card_exp_year', 'bank_name', 
            'account_name', 'is_default', 'is_active', 
            'created_at', 'last_used_at', 'display_name'
        ]
        read_only_fields = ['id', 'created_at', 'last_used_at']
    
    def get_display_name(self, obj):
        """Get user-friendly display name"""
        return str(obj)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan_name = serializers.CharField(source='pricing_plan.name', read_only=True)
    plan_category = serializers.CharField(source='pricing_plan.plan_category', read_only=True)
    telegram_groups = serializers.JSONField(source='pricing_plan.telegram_groups', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'billing_profile', 'pricing_plan', 'plan_name', 'plan_category',
            'telegram_groups', 'status', 'start_date', 'end_date', 'amount_paid',
            'currency', 'auto_renew', 'next_billing_date', 'is_active',
            'days_remaining', 'cancelled_at', 'cancellation_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'start_date', 'end_date', 'is_active',
            'days_remaining', 'cancelled_at', 'created_at', 'updated_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions"""
    subscription_plan = serializers.CharField(
        source='subscription.pricing_plan.name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'billing_profile', 'subscription', 'subscription_plan',
            'amount', 'processing_fee', 'total_amount', 'currency',
            'payment_gateway', 'gateway_reference', 'status',
            'created_at', 'paid_at', 'failed_at', 'failure_reason'
        ]
        read_only_fields = [
            'id', 'gateway_reference', 'status', 'created_at',
            'paid_at', 'failed_at', 'failure_reason'
        ]

class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for SubscriptionPlan model (Phase 0.5)
    Replaces old PricingPlanSerializer for deprecated PricingPlan model
    """
    price_display = serializers.SerializerMethodField()
    monthly_equivalent = serializers.SerializerMethodField()
    feature_count = serializers.SerializerMethodField()
    subscription_count = serializers.SerializerMethodField()
    revenue_total = serializers.SerializerMethodField()
    
    # Alias fields for frontend compatibility
    price = serializers.DecimalField(source='base_price', max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.SerializerMethodField()
    billing_cycle = serializers.CharField(source='billing_period', read_only=True)
    
    # Nested serializers for reading (GET requests)
    features = serializers.SerializerMethodField()
    telegram_groups = serializers.SerializerMethodField()
    
    # Write-only fields for creating/updating (POST/PUT requests)
    feature_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    telegram_group_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'base_price', 'price', 'currency', 'billing_period', 'billing_cycle',
            'limits', 'paystack_plan_code',
            'is_active', 'is_featured', 'sort_order',
            'price_display', 'monthly_equivalent', 'feature_count',
            'subscription_count', 'revenue_total',
            'features', 'telegram_groups', 'feature_ids', 'telegram_group_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
    
    def get_currency(self, obj):
        """Return USD as default currency (can be enhanced for multi-currency support)"""
        return 'USD'
    
    def validate_base_price(self, value):
        """Validate base_price is positive"""
        if value < 0:
            raise serializers.ValidationError("Base price must be positive.")
        return value
    
    def validate_name(self, value):
        """Validate plan name is unique"""
        # Get the instance being updated (if any)
        instance = getattr(self, 'instance', None)
        
        # Check for existing plan with same name
        queryset = SubscriptionPlan.objects.filter(name__iexact=value.strip())
        
        # Exclude current instance when updating
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                f"A plan with the name '{value}' already exists. Please choose a different name."
            )
        
        return value.strip()
    
    def get_price_display(self, obj):
        """Get formatted price with currency"""
        return f"${obj.base_price:.2f}"
    
    def get_monthly_equivalent(self, obj):
        """Calculate monthly equivalent price for annual/quarterly plans"""
        if obj.billing_period == 'monthly':
            return obj.base_price
        elif obj.billing_period == 'quarterly':
            return obj.base_price / 3
        elif obj.billing_period == 'annual':
            return obj.base_price / 12
        return obj.base_price
    
    def get_feature_count(self, obj):
        """Get count of features in this plan"""
        return obj.features.count()
    
    def get_subscription_count(self, obj):
        """Get count of active subscriptions using this plan"""
        return Subscription.objects.filter(
            plan=obj,
            status='active'
        ).count()
    
    def get_revenue_total(self, obj):
        """
        Estimate total revenue from this plan
        TODO: Calculate from actual Payment transactions (Phase 0.5.17+)
        """
        active_subs = self.get_subscription_count(obj)
        # Estimate: active_subs * base_price
        return float(active_subs * obj.base_price)
    
    def get_features(self, obj):
        """Get list of features with their details"""
        # Import here to avoid circular dependency (FeatureSerializer defined later in file)
        features = obj.features.all()
        return [
            {
                'id': str(f.id),
                'key': f.key,
                'name': f.name,
                'description': f.description,
                'category': f.category,
                'icon': f.icon,
                'sort_order': f.sort_order,
                'is_active': f.is_active,
            }
            for f in features
        ]
    
    def get_telegram_groups(self, obj):
        """Get list of telegram groups with their details"""
        # Import here to avoid circular dependency (TelegramGroupSerializer defined later in file)
        groups = obj.telegram_groups.all()
        return [
            {
                'id': str(g.id),
                'name': g.name,
                'chat_id': g.chat_id,
                'group_key': g.group_key,
                'invite_link': g.invite_link,
                'is_active': g.is_active,
            }
            for g in groups
        ]
    
    def create(self, validated_data):
        """Handle creation with feature_ids and telegram_group_ids"""
        feature_ids = validated_data.pop('feature_ids', [])
        telegram_group_ids = validated_data.pop('telegram_group_ids', [])
        
        plan = SubscriptionPlan.objects.create(**validated_data)
        
        if feature_ids:
            plan.features.set(feature_ids)
        if telegram_group_ids:
            plan.telegram_groups.set(telegram_group_ids)
        
        return plan
    
    def update(self, instance, validated_data):
        """Handle update with feature_ids and telegram_group_ids"""
        feature_ids = validated_data.pop('feature_ids', None)
        telegram_group_ids = validated_data.pop('telegram_group_ids', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships if provided
        if feature_ids is not None:
            instance.features.set(feature_ids)
        if telegram_group_ids is not None:
            instance.telegram_groups.set(telegram_group_ids)
        
        return instance

class FeatureSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for Feature model (Phase 0.5 - Task 0.5.22)
    
    Supports full CRUD operations with validation for key format and category choices.
    Includes computed field for plan_count (how many plans use this feature).
    """
    plan_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Feature
        fields = [
            'id', 'key', 'name', 'description', 'category', 'icon', 
            'sort_order', 'is_active', 'plan_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'plan_count']
    
    def get_plan_count(self, obj):
        """Get count of subscription plans using this feature"""
        return obj.plans.count()
    
    def validate_key(self, value):
        """Validate feature key format (lowercase, underscores, alphanumeric)"""
        if not value:
            raise serializers.ValidationError("Feature key is required.")
        
        # Check alphanumeric with underscores/hyphens only
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                "Feature key must contain only lowercase letters, numbers, underscores, and hyphens."
            )
        
        # Check lowercase
        if value != value.lower():
            raise serializers.ValidationError("Feature key must be lowercase.")
        
        return value


class PublicFeatureSerializer(serializers.ModelSerializer):
    """
    Simplified Feature serializer for public pricing API (Phase 0.5 - Task 0.5.33)
    Only exposes essential feature info without sensitive data like plan_count
    """
    class Meta:
        model = Feature
        fields = ['id', 'key', 'name', 'description', 'icon', 'category', 'sort_order']
        read_only_fields = ['id', 'key', 'name', 'description', 'icon', 'category', 'sort_order']


class PublicPricingPlanSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer for SubscriptionPlan (Phase 0.5 - Task 0.5.33)
    Used by PublicPricingViewSet for /api/v1/subscriptions/plans/ endpoint
    
    Includes features list and billing_period_display for frontend pricing page.
    Price fields are returned as floats (not Decimal strings) for consistency.
    """
    features = PublicFeatureSerializer(many=True, read_only=True)
    billing_period_display = serializers.CharField(source='get_billing_period_display', read_only=True)
    price = serializers.SerializerMethodField()
    base_price = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'billing_period', 'billing_period_display',
            'is_featured', 'is_active', 'sort_order', 'price', 'base_price',
            'features', 'limits'
        ]
        read_only_fields = ['id', 'name', 'slug', 'description', 'billing_period', 
                            'billing_period_display', 'is_featured', 'is_active',
                            'sort_order', 'price', 'base_price', 'features', 'limits']
    
    def get_price(self, obj):
        """Return base_price as float (not Decimal string)"""
        return float(obj.base_price)
    
    def get_base_price(self, obj):
        """Return base_price as float (not Decimal string)"""
        return float(obj.base_price)


class NestedSubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Nested serializer for SubscriptionPlan (for use in SubscriptionSerializer)
    Includes features for complete plan information
    """
    features = FeatureSerializer(many=True, read_only=True)
    feature_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'base_price', 'billing_period',
            'is_active', 'is_featured', 'features', 'feature_count'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_feature_count(self, obj):
        """Get count of features in this plan"""
        return obj.features.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for Subscription model (Phase 0.5 - Task 0.5.20)
    
    Features:
    - Full CRUD support with validation
    - Nested plan details with features
    - Computed fields (is_active, days_remaining)
    - Read-only user information
    - Support for metadata storage
    """
    # Read-only user information
    user_email = serializers.CharField(source='billing_profile.user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    telegram_username = serializers.CharField(source='billing_profile.telegram_username', read_only=True)
    
    # Nested plan details with features
    plan_details = NestedSubscriptionPlanSerializer(source='plan', read_only=True)
    
    # Basic plan info (for list views)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_slug = serializers.CharField(source='plan.slug', read_only=True)
    
    # Computed properties
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    # Writable fields (for create/update)
    plan = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        required=True,
        help_text='Active subscription plan ID'
    )
    billing_profile = serializers.PrimaryKeyRelatedField(
        queryset=BillingProfile.objects.all(),
        required=True,
        help_text='Billing profile ID'
    )
    
    class Meta:
        model = Subscription
        fields = [
            # IDs and relationships
            'id', 'billing_profile', 'plan',
            # Read-only user info
            'user_email', 'user_name', 'telegram_username',
            # Nested details
            'plan_details', 'plan_name', 'plan_slug',
            # Subscription status
            'status', 'start_date', 'end_date',
            # Payment info
            'payment_method', 'amount_paid', 'currency',
            # Auto-renewal
            'auto_renew', 'next_billing_date', 'last_renewed_at',
            # Cancellation
            'cancelled_at', 'cancellation_reason',
            # Computed fields
            'is_active', 'days_remaining',
            # Metadata
            'metadata',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'telegram_username',
            'plan_details', 'plan_name', 'plan_slug',
            'status', 'start_date', 'end_date', 'amount_paid', 'currency',
            'cancelled_at', 'is_active', 'days_remaining',
            'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        """Get user's full name or email"""
        user = obj.billing_profile.user
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.email
    
    def get_is_active(self, obj):
        """Check if subscription is currently active (uses model property)"""
        return obj.is_active
    
    def get_days_remaining(self, obj):
        """Calculate days remaining in subscription (uses model property)"""
        return obj.days_remaining
    
    def validate_plan(self, value):
        """Validate plan is active and available"""
        if not value.is_active:
            raise serializers.ValidationError("Selected plan is not currently available")
        return value
    
    def validate_billing_profile(self, value):
        """Validate billing profile exists and user has permission"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            # Users can only create subscriptions for their own billing profile
            # Admins can create for any billing profile
            if not user.is_staff and value.user != user:
                raise serializers.ValidationError(
                    "You can only create subscriptions for your own billing profile"
                )
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Check for duplicate active subscriptions
        if self.instance is None:  # Creating new subscription
            billing_profile = data.get('billing_profile')
            plan = data.get('plan')
            
            # Check if user already has an active subscription to this plan
            existing = Subscription.objects.filter(
                billing_profile=billing_profile,
                plan=plan,
                status='active'
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    "An active subscription to this plan already exists for this billing profile"
                )
        
        return data
    
    def create(self, validated_data):
        """
        Create subscription with calculated dates and default values
        Note: Start/end dates should be calculated by signal handlers or service layer
        This is a basic implementation - production should use subscription service
        """
        from datetime import timedelta
        
        # Extract plan for calculations
        plan = validated_data.get('plan')
        
        # Set start_date to now if not provided
        if 'start_date' not in validated_data:
            validated_data['start_date'] = timezone.now()
        
        # Calculate end_date based on billing period
        if 'end_date' not in validated_data:
            start = validated_data['start_date']
            if plan.billing_period == 'monthly':
                validated_data['end_date'] = start + timedelta(days=30)
            elif plan.billing_period == 'quarterly':
                validated_data['end_date'] = start + timedelta(days=90)
            elif plan.billing_period == 'annual':
                validated_data['end_date'] = start + timedelta(days=365)
            else:
                validated_data['end_date'] = start + timedelta(days=30)  # Default to monthly
        
        # Set amount_paid to plan base_price if not provided
        if 'amount_paid' not in validated_data:
            validated_data['amount_paid'] = plan.base_price
        
        # Set currency to USD if not provided
        if 'currency' not in validated_data:
            validated_data['currency'] = 'USD'
        
        # Set default status to pending (will be activated by payment/signal)
        if 'status' not in validated_data:
            validated_data['status'] = 'pending'
        
        return super().create(validated_data)


# DEPRECATED: SignalSubscriptionSerializer - use SubscriptionSerializer instead
# Keeping as alias for backward compatibility during transition
SignalSubscriptionSerializer = SubscriptionSerializer

# DEPRECATED: PaymentTransactionSerializer
# PaymentTransaction model will be recreated in Phase 0.5.17+
# For now, use Payment model serializer (PaymentSerializer already exists above)
# class PaymentTransactionSerializer(serializers.ModelSerializer):
#     """
#     DEPRECATED - PaymentTransaction model removed in Phase 0.5
#     Will be recreated with proper structure in Phase 0.5.17+
#     Use PaymentSerializer for Phase 0.5 Payment model instead
#     """
#     pass


class TelegramGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for TelegramGroup model (Phase 0.5)
    Replaces old TelegramGroupManagementSerializer for deprecated TelegramGroupManagement model
    """
    subscription_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TelegramGroup
        fields = [
            'id', 'name', 'group_id', 'invite_link', 'is_active',
            'subscription_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subscription_count(self, obj):
        """Get count of subscriptions using this telegram group"""
        # TODO: Add M2M relationship between Subscription and TelegramGroup in Phase 0.5.15+
        return 0


# DEPRECATED: TelegramGroupManagementSerializer - use TelegramGroupSerializer instead
# Keeping as alias for backward compatibility during transition
TelegramGroupManagementSerializer = TelegramGroupSerializer

# Simplified serializers for dashboard widgets
class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics"""
    total_active = serializers.IntegerField()
    weekly_count = serializers.IntegerField()
    monthly_count = serializers.IntegerField()
    vip_count = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    expiring_soon = serializers.IntegerField()

class RevenueStatsSerializer(serializers.Serializer):
    """Serializer for revenue statistics"""
    daily_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    weekly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

class PendingActionsSerializer(serializers.Serializer):
    """Serializer for pending admin actions"""
    telegram_adds = serializers.IntegerField()
    telegram_removes = serializers.IntegerField()
    payment_verifications = serializers.IntegerField()
    expiring_subscriptions = serializers.IntegerField()

# New serializers for enhanced pricing system

class CouponSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for coupon management (Phase 0.5 - Task 0.5.23).
    Includes validation, computed fields, and plan relationship management.
    """
    # Explicitly define plans field to handle ManyToMany relationship
    plans = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SubscriptionPlan.objects.all(),
        required=False,
        allow_empty=True
    )
    
    # Computed fields
    discount_display = serializers.ReadOnlyField(source='get_discount_display')
    is_valid_now = serializers.SerializerMethodField()
    usage_available = serializers.SerializerMethodField()
    can_be_used_now = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()
    plan_count = serializers.SerializerMethodField()
    
    # Creator info
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'description',
            'valid_from', 'valid_until', 'max_uses', 'max_uses_per_user',
            'current_uses', 'is_active', 'plans',
            # Computed fields
            'discount_display', 'is_valid_now', 'usage_available', 'can_be_used_now',
            'usage_percentage', 'remaining_uses', 'plan_count',
            # Creator & timestamps
            'created_by', 'created_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_by', 'created_at', 'updated_at']
    
    def get_is_valid_now(self, obj):
        """Check if coupon is currently valid (time-based only)"""
        return obj.is_valid()
    
    def get_usage_available(self, obj):
        """Check if coupon has usage remaining"""
        return obj.is_usage_available()
    
    def get_can_be_used_now(self, obj):
        """Check if coupon can be used (combines validity and usage)"""
        return obj.can_be_used()
    
    def get_usage_percentage(self, obj):
        """Get usage percentage (0-100)"""
        if obj.max_uses is None or obj.max_uses == 0:
            return 0
        return min(100, (obj.current_uses / obj.max_uses) * 100)
    
    def get_remaining_uses(self, obj):
        """Get number of remaining uses (None if unlimited)"""
        return obj.get_remaining_uses()
    
    def get_plan_count(self, obj):
        """Get count of plans this coupon applies to (0 = all plans)"""
        return obj.plans.count()
    
    def validate_code(self, value):
        """Validate and normalize coupon code"""
        if not value:
            raise serializers.ValidationError("Coupon code cannot be empty.")
        
        # Normalize to uppercase
        normalized_code = value.upper().strip()
        
        # Validate format: alphanumeric + underscore/hyphen
        import re
        if not re.match(r'^[A-Z0-9_-]+$', normalized_code):
            raise serializers.ValidationError(
                "Coupon code must contain only uppercase letters, numbers, underscores, and hyphens."
            )
        
        # Check minimum length
        if len(normalized_code) < 3:
            raise serializers.ValidationError("Coupon code must be at least 3 characters long.")
        
        # Check uniqueness (only on create)
        if not self.instance:
            if Coupon.objects.filter(code=normalized_code).exists():
                raise serializers.ValidationError(f"Coupon with code '{normalized_code}' already exists.")
        
        return normalized_code
    
    def validate_discount_value(self, value):
        """Validate discount value is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Discount value cannot be negative.")
        return value
    
    def validate_max_uses(self, value):
        """Validate max_uses is positive if specified"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Maximum uses cannot be negative.")
        return value
    
    def validate_max_uses_per_user(self, value):
        """Validate max_uses_per_user is positive"""
        if value < 0:
            raise serializers.ValidationError("Maximum uses per user cannot be negative.")
        if value == 0:
            raise serializers.ValidationError("Maximum uses per user must be at least 1.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        discount_type = data.get('discount_type', getattr(self.instance, 'discount_type', None))
        discount_value = data.get('discount_value', getattr(self.instance, 'discount_value', None))
        valid_from = data.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_until = data.get('valid_until', getattr(self.instance, 'valid_until', None))
        
        # Validate discount value based on type
        if discount_type and discount_value is not None:
            if discount_type == 'percentage':
                if not (0 <= discount_value <= 100):
                    raise serializers.ValidationError({
                        'discount_value': 'Percentage discount must be between 0 and 100.'
                    })
            elif discount_type == 'fixed':
                if discount_value <= 0:
                    raise serializers.ValidationError({
                        'discount_value': 'Fixed discount amount must be positive.'
                    })
        
        # Validate date range
        if valid_from and valid_until:
            if valid_until <= valid_from:
                raise serializers.ValidationError({
                    'valid_until': 'Expiration date must be after start date.'
                })
        
        return data
    
    def create(self, validated_data):
        """Override create to handle ManyToMany plans field"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Log incoming data for debugging
        logger.info(f"Creating coupon with validated_data: {validated_data}")
        
        # Extract plans for ManyToMany relationship handling
        plans = validated_data.pop('plans', [])
        logger.info(f"Extracted plans: {plans} (type: {type(plans)})")
        
        # Create the coupon instance with scalar fields
        instance = super().create(validated_data)
        logger.info(f"Created coupon instance: {instance.id}")
        
        # Set ManyToMany plans field
        if plans:
            logger.info(f"Setting {len(plans)} plans to coupon")
            instance.plans.set(plans)
        else:
            logger.info("No plans to set (empty list)")
        
        return instance
    
    def update(self, instance, validated_data):
        """Override update to prevent code modification and handle ManyToMany plans"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Updating coupon {instance.id} with validated_data: {validated_data}")
        
        # Remove code from validated_data if present (code is immutable)
        validated_data.pop('code', None)
        
        # Extract plans for ManyToMany relationship handling
        plans = validated_data.pop('plans', None)
        logger.info(f"Extracted plans: {plans} (type: {type(plans)})")
        
        # Update scalar fields
        instance = super().update(instance, validated_data)
        
        # Update ManyToMany plans field if provided
        if plans is not None:
            logger.info(f"Setting {len(plans)} plans to coupon")
            instance.plans.set(plans)
        else:
            logger.info("Plans is None, not updating")
        
        return instance

class CouponValidationSerializer(serializers.Serializer):
    """Serializer for coupon validation requests"""
    coupon_code = serializers.CharField(max_length=50)
    plan_id = serializers.UUIDField()
    user_id = serializers.IntegerField(required=False)
    
    def validate_coupon_code(self, value):
        """Validate coupon exists and is active"""
        try:
            coupon = Coupon.objects.get(code=value.upper())
            if not coupon.is_valid:
                raise serializers.ValidationError(f"Coupon {value} is not valid")
            return value.upper()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError(f"Coupon {value} does not exist")

class CouponApplicationSerializer(serializers.Serializer):
    """Serializer for coupon application results"""
    is_valid = serializers.BooleanField()
    message = serializers.CharField()
    original_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    coupon_code = serializers.CharField(required=False)
    savings_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class EnhancedSubscriptionSerializer(serializers.ModelSerializer):
    """
    Enhanced subscription serializer with plan and payment info (Phase 0.5)
    Replaces old EnhancedSignalSubscriptionSerializer for deprecated SignalSubscription model
    """
    user_email = serializers.CharField(source='billing_profile.user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    plan_info = PricingPlanSerializer(source='plan', read_only=True)
    telegram_username = serializers.CharField(source='billing_profile.telegram_username', read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user_email', 'user_name', 'plan_info', 'payment_reference',
            'status', 'start_date', 'end_date', 'auto_renew', 'telegram_username',
            'cancel_at_period_end', 'is_active', 'days_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'payment_reference',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        """Get user full name"""
        user = obj.billing_profile.user
        return f"{user.first_name} {user.last_name}".strip() or user.email
    
    def get_is_active(self, obj):
        """Check if subscription is currently active"""
        return (
            obj.status == 'active' and
            obj.end_date and
            timezone.now() <= obj.end_date
        )
    
    def get_days_remaining(self, obj):
        """Calculate days remaining in subscription"""
        if obj.end_date and self.get_is_active(obj):
            return (obj.end_date - timezone.now()).days
        return 0


# DEPRECATED: EnhancedSignalSubscriptionSerializer - use EnhancedSubscriptionSerializer instead
# Keeping as alias for backward compatibility during transition
EnhancedSignalSubscriptionSerializer = EnhancedSubscriptionSerializer

class PricingStructureSerializer(serializers.Serializer):
    """Serializer for complete pricing structure"""
    mentorship = PricingPlanSerializer(many=True)
    signals = PricingPlanSerializer(many=True) 
    vip = PricingPlanSerializer(many=True)
    featured_plans = PricingPlanSerializer(many=True)

class DynamicPricingResponseSerializer(serializers.Serializer):
    """Serializer for dynamic pricing API responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    pricing_structure = PricingStructureSerializer(required=False)
    total_plans = serializers.IntegerField(required=False)
    active_promotions = serializers.IntegerField(required=False)


# ============================================================================
# TELEGRAM CONFIGURATION SERIALIZER (Task 0.5.27)
# ============================================================================

class TelegramConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for TelegramConfiguration (singleton model).
    
    Features:
    - Write-only bot_token field (never expose in responses)
    - Masked token display for security
    - Settings bulk update support
    - Comprehensive validation
    """
    
    # Write-only field for setting bot token
    bot_token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text='Telegram bot API token from @BotFather'
    )
    
    # Read-only masked token display
    masked_token = serializers.SerializerMethodField(
        help_text='Masked version of bot token for display'
    )
    
    # Read-only computed fields
    is_healthy = serializers.SerializerMethodField(
        help_text='Whether bot is enabled and connected'
    )
    has_valid_token_format = serializers.SerializerMethodField(
        help_text='Whether bot token has valid format'
    )
    
    class Meta:
        model = TelegramConfiguration
        fields = [
            'id',
            'bot_token',  # write-only
            'masked_token',  # read-only
            'bot_username',
            'is_enabled',
            'is_connected',
            'connection_error',
            'last_health_check',
            'auto_add_enabled',
            'auto_remove_enabled',
            'welcome_message',
            'removal_message',
            'max_retries',
            'retry_delay_seconds',
            'rate_limit_per_minute',
            'is_healthy',  # read-only computed
            'has_valid_token_format',  # read-only computed
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'masked_token', 'is_connected', 'connection_error',
            'last_health_check', 'is_healthy', 'has_valid_token_format',
            'created_at', 'updated_at'
        ]
    
    def get_masked_token(self, obj):
        """Return masked version of bot token"""
        return obj.get_masked_token()
    
    def get_is_healthy(self, obj):
        """Return health status"""
        return obj.is_healthy()
    
    def get_has_valid_token_format(self, obj):
        """Check if token has valid format"""
        return obj.has_valid_token()
    
    def validate_bot_username(self, value):
        """Validate bot username format (optional field, auto-detected on test)"""
        # Allow empty/None values - username will be auto-detected on connection test
        if not value or value.strip() == '':
            return value
        
        # If provided, must start with @
        if not value.startswith('@'):
            raise serializers.ValidationError(
                'Bot username must start with @ (e.g., @OxidaneBot)'
            )
        return value
    
    def validate_max_retries(self, value):
        """Validate max retries is non-negative"""
        if value < 0:
            raise serializers.ValidationError('Max retries must be 0 or greater.')
        return value
    
    def validate_retry_delay_seconds(self, value):
        """Validate retry delay is positive"""
        if value <= 0:
            raise serializers.ValidationError('Retry delay must be greater than 0.')
        return value
    
    def validate_rate_limit_per_minute(self, value):
        """Validate rate limit is positive"""
        if value <= 0:
            raise serializers.ValidationError('Rate limit must be greater than 0.')
        return value
    
    def validate_bot_token(self, value):
        """Validate bot token format (basic check)"""
        if not value:
            return value
        
        # Telegram bot token format: numbers:alphanumeric+dash+underscore
        # Example: 123456789:ABCdefGHI-jklMNO_pqr
        parts = value.split(':')
        if len(parts) != 2:
            raise serializers.ValidationError(
                'Invalid bot token format. Expected format: numbers:characters'
            )
        
        if not parts[0].isdigit():
            raise serializers.ValidationError(
                'Invalid bot token format. First part must be numeric.'
            )
        
        if len(parts[0]) < 8 or len(parts[0]) > 10:
            raise serializers.ValidationError(
                'Invalid bot token format. Bot ID should be 8-10 digits.'
            )
        
        if len(parts[1]) < 30:
            raise serializers.ValidationError(
                'Invalid bot token format. Token part seems too short.'
            )
        
        return value
    
    def create(self, validated_data):
        """
        Create or update singleton instance.
        Since TelegramConfiguration is a singleton, this always updates the existing instance.
        """
        # Extract bot_token if provided
        bot_token = validated_data.pop('bot_token', None)
        
        # Get singleton instance
        instance = TelegramConfiguration.get_instance()
        
        # Update fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        # Set bot token if provided (marks as disconnected)
        if bot_token is not None and bot_token.strip():
            instance.bot_token = bot_token
            instance.is_connected = False
            instance.connection_error = ''
            # Encrypt and save (encrypt_field will save the model)
            instance.encrypt_field('bot_token')
        
        # Save other fields (or all fields if no token update)
        # Use update_fields to avoid overwriting the encrypted token
        update_fields = [k for k in validated_data.keys()]
        if bot_token is not None and bot_token.strip():
            # Also update connection status fields
            update_fields.extend(['is_connected', 'connection_error'])
        if update_fields:
            instance.save(update_fields=update_fields)
        
        return instance
    
    def update(self, instance, validated_data):
        """Update singleton instance"""
        # Extract bot_token if provided
        bot_token = validated_data.pop('bot_token', None)
        
        # Update regular fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        # Set bot token if provided (marks as disconnected)
        if bot_token is not None and bot_token.strip():
            instance.bot_token = bot_token
            instance.is_connected = False
            instance.connection_error = ''
            # Encrypt and save (encrypt_field will save the model)
            instance.encrypt_field('bot_token')
        
        # Save other fields (or all fields if no token update)
        # Use update_fields to avoid overwriting the encrypted token
        update_fields = [k for k in validated_data.keys()]
        if bot_token is not None and bot_token.strip():
            # Also update connection status fields
            update_fields.extend(['is_connected', 'connection_error'])
        if update_fields:
            instance.save(update_fields=update_fields)
        
        return instance


class TelegramGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for TelegramGroup model with plan associations.
    
    Handles:
    - M2M relationships with SubscriptionPlan
    - Member count tracking and capacity checks
    - Bot permission flags
    - Computed fields for group health status
    
    Phase 0.5, Task 0.5.28
    """
    # M2M relationship - writable with plan IDs
    associated_plan_ids = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='associated_plans',
        help_text="List of subscription plan IDs that grant access to this group"
    )
    
    # Read-only plan details for response
    associated_plans = serializers.SerializerMethodField(
        help_text="Full details of associated subscription plans"
    )
    
    # Computed fields
    has_capacity = serializers.SerializerMethodField(
        help_text="Whether group can accept new members (based on max_members)"
    )
    is_healthy = serializers.SerializerMethodField(
        help_text="Whether group is active and bot has required permissions"
    )
    capacity_percentage = serializers.SerializerMethodField(
        help_text="Current capacity utilization (0-100, null if unlimited)"
    )
    days_since_sync = serializers.SerializerMethodField(
        help_text="Days since last member count sync (null if never synced)"
    )
    
    class Meta:
        model = TelegramGroup
        fields = [
            # Identity
            'id', 'name', 'chat_id', 'group_key',
            
            # Metadata
            'description', 'invite_link',
            
            # Status
            'is_active', 'is_private',
            
            # Member tracking
            'member_count', 'max_members', 'last_sync_at',
            
            # Settings
            'auto_add_enabled', 'auto_remove_enabled',
            'welcome_message', 'removal_message', 'notification_enabled',
            
            # Bot permissions
            'can_send_messages', 'can_add_users', 'can_remove_users',
            'can_pin_messages', 'can_delete_messages', 'is_admin',
            
            # Relationships
            'associated_plan_ids', 'associated_plans',
            
            # Display
            'sort_order',
            
            # Computed fields
            'has_capacity', 'is_healthy', 'capacity_percentage', 'days_since_sync',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'member_count', 'last_sync_at', 'created_at', 'updated_at',
            'has_capacity', 'is_healthy', 'capacity_percentage', 'days_since_sync'
        ]
    
    def get_associated_plans(self, obj):
        """Return minimal plan details for associated plans."""
        plans = obj.associated_plans.all()
        return [
            {
                'id': str(plan.id),
                'name': plan.name,
                'billing_period': plan.billing_period,
                'is_active': plan.is_active
            }
            for plan in plans
        ]
    
    def get_has_capacity(self, obj):
        """Check if group has capacity for new members."""
        return obj.has_capacity()
    
    def get_is_healthy(self, obj):
        """
        Check if group is healthy (active + has required permissions).
        """
        return (
            obj.is_active and
            obj.can_add_users and
            obj.can_remove_users
        )
    
    def get_capacity_percentage(self, obj):
        """Calculate capacity utilization percentage."""
        if obj.max_members is None:
            return None  # Unlimited capacity
        if obj.max_members == 0:
            return 100.0
        return round((obj.member_count / obj.max_members) * 100, 2)
    
    def get_days_since_sync(self, obj):
        """Calculate days since last sync."""
        if obj.last_sync_at is None:
            return None
        delta = timezone.now() - obj.last_sync_at
        return delta.days
    
    def validate_chat_id(self, value):
        """Validate chat_id format (must start with '-' for groups)."""
        if value and not value.startswith('-'):
            raise serializers.ValidationError(
                "Telegram group chat ID must start with '-' (negative number)"
            )
        return value
    
    def validate_member_count(self, value):
        """Validate member_count is non-negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Member count cannot be negative"
            )
        return value
    
    def validate_max_members(self, value):
        """Validate max_members is positive or null."""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Maximum members cannot be negative"
            )
        return value
    
    def validate_sort_order(self, value):
        """Validate sort_order is non-negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Sort order cannot be negative"
            )
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # Check if member_count exceeds max_members
        member_count = data.get('member_count', getattr(self.instance, 'member_count', 0) if self.instance else 0)
        max_members = data.get('max_members', getattr(self.instance, 'max_members', None) if self.instance else None)
        
        if max_members is not None and member_count > max_members:
            raise serializers.ValidationError({
                'member_count': f'Member count ({member_count}) cannot exceed max_members ({max_members})'
            })
        
        return data
    
    def create(self, validated_data):
        """Create a new TelegramGroup with plan associations."""
        # Extract M2M data
        plans = validated_data.pop('associated_plans', [])
        
        # Create the group
        group = TelegramGroup.objects.create(**validated_data)
        
        # Set plan associations
        if plans:
            group.associated_plans.set(plans)
        
        return group
    
    def update(self, instance, validated_data):
        """Update TelegramGroup including plan associations."""
        # Extract M2M data
        plans = validated_data.pop('associated_plans', None)
        
        # Update regular fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        
        # Update plan associations if provided
        if plans is not None:
            instance.associated_plans.set(plans)
        
        return instance


# ============================================================================
# PAYMENT CONFIGURATION SERIALIZER (Task 0.5.29)
# ============================================================================

class PaymentConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment Configuration singleton with Paystack/Stripe settings.
    
    Features:
    - Write-only encrypted keys (never expose in responses)
    - Masked key display for security
    - Computed fields (is_configured, is_healthy, provider_status)
    - Singleton pattern handling
    - Multi-currency support
    
    Phase 0.5, Task 0.5.29
    """
    
    # Write-only fields for setting keys (will be encrypted)
    paystack_public_key_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Paystack public key (pk_test_... or pk_live_...)'
    )
    paystack_secret_key_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Paystack secret key (sk_test_... or sk_live_...)'
    )
    paystack_webhook_secret_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Paystack webhook secret'
    )
    stripe_publishable_key_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Stripe publishable key (pk_test_... or pk_live_...)'
    )
    stripe_secret_key_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Stripe secret key (sk_test_... or sk_live_...)'
    )
    stripe_webhook_secret_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Stripe webhook secret (whsec_...)'
    )
    
    # Read-only masked keys (for display)
    paystack_public_key_masked = serializers.SerializerMethodField()
    paystack_secret_key_masked = serializers.SerializerMethodField()
    paystack_webhook_secret_masked = serializers.SerializerMethodField()
    stripe_publishable_key_masked = serializers.SerializerMethodField()
    stripe_secret_key_masked = serializers.SerializerMethodField()
    stripe_webhook_secret_masked = serializers.SerializerMethodField()
    
    # Computed fields
    is_paystack_configured = serializers.SerializerMethodField()
    is_stripe_configured = serializers.SerializerMethodField()
    has_any_provider = serializers.SerializerMethodField()
    provider_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentConfiguration
        fields = [
            # IDs and timestamps
            'id', 'created_at', 'updated_at',
            
            # Write-only keys (for setting)
            'paystack_public_key_write', 'paystack_secret_key_write', 'paystack_webhook_secret_write',
            'stripe_publishable_key_write', 'stripe_secret_key_write', 'stripe_webhook_secret_write',
            
            # Read-only masked keys (for display)
            'paystack_public_key_masked', 'paystack_secret_key_masked', 'paystack_webhook_secret_masked',
            'stripe_publishable_key_masked', 'stripe_secret_key_masked', 'stripe_webhook_secret_masked',
            
            # Webhook URLs
            'paystack_webhook_url', 'stripe_webhook_url',
            
            # Provider settings
            'paystack_enabled', 'stripe_enabled', 'primary_provider', 'is_test_mode',
            
            # Currency settings
            'supported_currencies',
            
            # Computed fields
            'is_paystack_configured', 'is_stripe_configured', 'has_any_provider', 'provider_status',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'paystack_public_key_masked', 'paystack_secret_key_masked', 'paystack_webhook_secret_masked',
            'stripe_publishable_key_masked', 'stripe_secret_key_masked', 'stripe_webhook_secret_masked',
            'is_paystack_configured', 'is_stripe_configured', 'has_any_provider', 'provider_status',
        ]
    
    # ============================================================================
    # MASKED KEY METHODS
    # ============================================================================
    
    def get_paystack_public_key_masked(self, obj):
        """Return masked Paystack public key."""
        return obj.get_masked_paystack_public_key()
    
    def get_paystack_secret_key_masked(self, obj):
        """Return masked Paystack secret key."""
        return obj.get_masked_paystack_secret_key()
    
    def get_paystack_webhook_secret_masked(self, obj):
        """Return masked Paystack webhook secret."""
        return obj._mask_key(obj.paystack_webhook_secret)
    
    def get_stripe_publishable_key_masked(self, obj):
        """Return masked Stripe publishable key."""
        return obj.get_masked_stripe_publishable_key()
    
    def get_stripe_secret_key_masked(self, obj):
        """Return masked Stripe secret key."""
        return obj.get_masked_stripe_secret_key()
    
    def get_stripe_webhook_secret_masked(self, obj):
        """Return masked Stripe webhook secret."""
        return obj._mask_key(obj.stripe_webhook_secret)
    
    # ============================================================================
    # COMPUTED FIELD METHODS
    # ============================================================================
    
    def get_is_paystack_configured(self, obj):
        """Check if Paystack is configured."""
        return obj.is_paystack_configured()
    
    def get_is_stripe_configured(self, obj):
        """Check if Stripe is configured."""
        return obj.is_stripe_configured()
    
    def get_has_any_provider(self, obj):
        """Check if any provider is configured."""
        return obj.has_any_provider_configured()
    
    def get_provider_status(self, obj):
        """Get status of all providers."""
        return {
            'paystack': {
                'enabled': obj.paystack_enabled,
                'configured': obj.is_paystack_configured(),
                'is_primary': obj.primary_provider == 'paystack',
            },
            'stripe': {
                'enabled': obj.stripe_enabled,
                'configured': obj.is_stripe_configured(),
                'is_primary': obj.primary_provider == 'stripe',
            },
            'has_active_provider': (
                (obj.paystack_enabled and obj.is_paystack_configured()) or
                (obj.stripe_enabled and obj.is_stripe_configured())
            ),
        }
    
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    def validate_paystack_public_key_write(self, value):
        """Validate Paystack public key format."""
        if value and not value.startswith('pk_'):
            raise serializers.ValidationError(
                'Paystack public key must start with "pk_"'
            )
        return value
    
    def validate_paystack_secret_key_write(self, value):
        """Validate Paystack secret key format."""
        if value and not value.startswith('sk_'):
            raise serializers.ValidationError(
                'Paystack secret key must start with "sk_"'
            )
        return value
    
    def validate_stripe_publishable_key_write(self, value):
        """Validate Stripe publishable key format."""
        if value and not value.startswith('pk_'):
            raise serializers.ValidationError(
                'Stripe publishable key must start with "pk_"'
            )
        return value
    
    def validate_stripe_secret_key_write(self, value):
        """Validate Stripe secret key format."""
        if value and not value.startswith('sk_'):
            raise serializers.ValidationError(
                'Stripe secret key must start with "sk_"'
            )
        return value
    
    def validate_stripe_webhook_secret_write(self, value):
        """Validate Stripe webhook secret format."""
        if value and not value.startswith('whsec_'):
            raise serializers.ValidationError(
                'Stripe webhook secret must start with "whsec_"'
            )
        return value
    
    def validate_supported_currencies(self, value):
        """Validate currency codes."""
        if value:
            for currency in value:
                if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
                    raise serializers.ValidationError(
                        f'Invalid currency code: {currency}. Must be 3 uppercase letters (e.g., "NGN", "USD")'
                    )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # If primary_provider is set, ensure that provider is enabled and configured
        primary_provider = attrs.get('primary_provider', getattr(self.instance, 'primary_provider', 'paystack'))
        
        # Check if we're updating keys for the primary provider
        if primary_provider == 'paystack':
            paystack_public_key = attrs.get('paystack_public_key_write') or (
                self.instance.paystack_public_key if self.instance else None
            )
            paystack_secret_key = attrs.get('paystack_secret_key_write') or (
                self.instance.paystack_secret_key if self.instance else None
            )
            
            if not (paystack_public_key and paystack_secret_key):
                # Warn but don't fail - they might configure it later
                pass
        
        elif primary_provider == 'stripe':
            stripe_publishable_key = attrs.get('stripe_publishable_key_write') or (
                self.instance.stripe_publishable_key if self.instance else None
            )
            stripe_secret_key = attrs.get('stripe_secret_key_write') or (
                self.instance.stripe_secret_key if self.instance else None
            )
            
            if not (stripe_publishable_key and stripe_secret_key):
                # Warn but don't fail
                pass
        
        return attrs
    
    # ============================================================================
    # CREATE/UPDATE METHODS
    # ============================================================================
    
    def create(self, validated_data):
        """
        Create or update the singleton instance.
        Extract write-only key fields and encrypt them.
        """
        # Extract write-only fields
        paystack_public_key = validated_data.pop('paystack_public_key_write', None)
        paystack_secret_key = validated_data.pop('paystack_secret_key_write', None)
        paystack_webhook_secret = validated_data.pop('paystack_webhook_secret_write', None)
        stripe_publishable_key = validated_data.pop('stripe_publishable_key_write', None)
        stripe_secret_key = validated_data.pop('stripe_secret_key_write', None)
        stripe_webhook_secret = validated_data.pop('stripe_webhook_secret_write', None)
        
        # Get or create singleton instance
        instance = PaymentConfiguration.get_instance()
        
        # Update non-key fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update keys if provided
        if paystack_public_key is not None:
            instance.paystack_public_key = paystack_public_key
        if paystack_secret_key is not None:
            instance.paystack_secret_key = paystack_secret_key
        if paystack_webhook_secret is not None:
            instance.paystack_webhook_secret = paystack_webhook_secret
        if stripe_publishable_key is not None:
            instance.stripe_publishable_key = stripe_publishable_key
        if stripe_secret_key is not None:
            instance.stripe_secret_key = stripe_secret_key
        if stripe_webhook_secret is not None:
            instance.stripe_webhook_secret = stripe_webhook_secret
        
        instance.save()
        
        # Encrypt sensitive fields
        if paystack_secret_key:
            instance.encrypt_field('paystack_secret_key')
        if paystack_webhook_secret:
            instance.encrypt_field('paystack_webhook_secret')
        if stripe_secret_key:
            instance.encrypt_field('stripe_secret_key')
        if stripe_webhook_secret:
            instance.encrypt_field('stripe_webhook_secret')
        
        return instance
    
    def update(self, instance, validated_data):
        """
        Update the singleton instance.
        Extract write-only key fields and encrypt them.
        """
        # Extract write-only fields
        paystack_public_key = validated_data.pop('paystack_public_key_write', None)
        paystack_secret_key = validated_data.pop('paystack_secret_key_write', None)
        paystack_webhook_secret = validated_data.pop('paystack_webhook_secret_write', None)
        stripe_publishable_key = validated_data.pop('stripe_publishable_key_write', None)
        stripe_secret_key = validated_data.pop('stripe_secret_key_write', None)
        stripe_webhook_secret = validated_data.pop('stripe_webhook_secret_write', None)
        
        # Update non-key fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update keys if provided (set plaintext values)
        if paystack_public_key is not None:
            instance.paystack_public_key = paystack_public_key
        if paystack_secret_key is not None:
            instance.paystack_secret_key = paystack_secret_key
        if paystack_webhook_secret is not None:
            instance.paystack_webhook_secret = paystack_webhook_secret
        if stripe_publishable_key is not None:
            instance.stripe_publishable_key = stripe_publishable_key
        if stripe_secret_key is not None:
            instance.stripe_secret_key = stripe_secret_key
        if stripe_webhook_secret is not None:
            instance.stripe_webhook_secret = stripe_webhook_secret
        
        # Encrypt sensitive fields BEFORE saving to avoid validation errors
        if paystack_secret_key:
            instance.encrypt_field('paystack_secret_key')
        if paystack_webhook_secret:
            instance.encrypt_field('paystack_webhook_secret')
        if stripe_secret_key:
            instance.encrypt_field('stripe_secret_key')
        if stripe_webhook_secret:
            instance.encrypt_field('stripe_webhook_secret')
        
        instance.save()
        
        return instance


# ============================================================================
# EMAIL CONFIGURATION SERIALIZER (Task 0.5.30)
# ============================================================================

class EmailConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for Email Configuration singleton with SMTP settings.
    
    Features:
    - Write-only password (encrypted storage)
    - Masked password display for security
    - Computed fields (is_configured, connection_status)
    - Singleton pattern handling
    - SMTP validation
    
    Phase 0.5, Task 0.5.30
    """
    
    # Write-only field for setting SMTP password (will be encrypted)
    smtp_password_write = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='SMTP password (will be encrypted)'
    )
    
    # Read-only masked password
    masked_smtp_password = serializers.SerializerMethodField(
        help_text='Masked SMTP password for display (***XX)'
    )
    
    # Computed fields
    is_configured = serializers.SerializerMethodField(
        help_text='Whether all required SMTP settings are configured'
    )
    connection_status = serializers.SerializerMethodField(
        help_text='Connection status information'
    )
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'id',
            'smtp_host',
            'smtp_port',
            'use_tls',
            'use_ssl',
            'smtp_username',
            'smtp_password_write',  # Write-only
            'masked_smtp_password',  # Read-only
            'from_email',
            'from_name',
            'is_enabled',
            'is_configured',  # Computed
            'is_connected',
            'connection_status',  # Computed
            'connection_error',
            'last_test_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'is_connected',
            'connection_error',
            'last_test_at',
            'created_at',
            'updated_at',
        ]
    
    def get_masked_smtp_password(self, obj):
        """Return masked SMTP password for security."""
        return obj.get_masked_password()
    
    def get_is_configured(self, obj):
        """Check if email configuration is complete."""
        return obj.is_configured()
    
    def get_connection_status(self, obj):
        """Get connection status information."""
        return {
            'is_connected': obj.is_connected,
            'last_test_at': obj.last_test_at,
            'error': obj.connection_error if not obj.is_connected else None,
        }
    
    def validate_smtp_host(self, value):
        """Validate SMTP host format."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError('SMTP host cannot be empty or whitespace.')
        return value.strip()
    
    def validate_smtp_port(self, value):
        """Validate SMTP port range."""
        if value and (value < 1 or value > 65535):
            raise serializers.ValidationError('SMTP port must be between 1 and 65535.')
        return value
    
    def validate_smtp_username(self, value):
        """Validate SMTP username is not empty."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError('SMTP username cannot be empty.')
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Check TLS/SSL conflict
        use_tls = attrs.get('use_tls', getattr(self.instance, 'use_tls', True) if self.instance else True)
        use_ssl = attrs.get('use_ssl', getattr(self.instance, 'use_ssl', False) if self.instance else False)
        
        if use_tls and use_ssl:
            raise serializers.ValidationError({
                'use_ssl': 'Cannot enable both TLS and SSL. Choose one.'
            })
        
        if not use_tls and not use_ssl:
            raise serializers.ValidationError({
                'use_tls': 'Either TLS or SSL must be enabled for security.'
            })
        
        # Validate port matches encryption type
        smtp_port = attrs.get('smtp_port', getattr(self.instance, 'smtp_port', 587) if self.instance else 587)
        
        if use_ssl and smtp_port not in [465]:
            # Warning: SSL typically uses port 465
            pass  # Allow but log warning in production
        
        if use_tls and smtp_port not in [587, 25]:
            # Warning: TLS typically uses port 587 or 25
            pass  # Allow but log warning in production
        
        return attrs
    
    def create(self, validated_data):
        """
        Create or update singleton instance.
        Handle SMTP password encryption.
        """
        # Extract write-only password
        smtp_password = validated_data.pop('smtp_password_write', None)
        
        # Get or create singleton
        instance = EmailConfiguration.get_instance()
        
        # Update non-password fields first
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save non-password fields first
        instance.save()
        
        # Update and encrypt SMTP password if provided
        if smtp_password:
            instance.smtp_password = smtp_password
            instance.encrypt_field('smtp_password')  # This calls save() internally
        
        return instance
    
    def update(self, instance, validated_data):
        """
        Update existing instance.
        Handle SMTP password encryption.
        """
        # Extract write-only password
        smtp_password = validated_data.pop('smtp_password_write', None)
        
        # Update non-password fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save non-password fields first
        instance.save()
        
        # Update and encrypt SMTP password if provided
        if smtp_password:
            instance.smtp_password = smtp_password
            instance.encrypt_field('smtp_password')  # This calls save() internally
        
        return instance


