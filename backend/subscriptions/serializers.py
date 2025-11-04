from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    SubscriptionPlan, Subscription, Coupon,
    BillingProfile, PaymentMethod, Payment, TelegramGroup
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
    has_trial = serializers.SerializerMethodField()
    feature_count = serializers.SerializerMethodField()
    subscription_count = serializers.SerializerMethodField()
    revenue_total = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'base_price', 'billing_period',
            'trial_days', 'limits', 'stripe_price_id', 'paystack_plan_code',
            'is_active', 'is_featured', 'sort_order',
            'price_display', 'monthly_equivalent', 'has_trial', 'feature_count',
            'subscription_count', 'revenue_total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
    
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
    
    def get_has_trial(self, obj):
        """Check if plan has a trial period"""
        return obj.trial_days > 0
    
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

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription model (Phase 0.5)
    Replaces old SignalSubscriptionSerializer for deprecated SignalSubscription model
    """
    user_email = serializers.CharField(source='billing_profile.user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_slug = serializers.CharField(source='plan.slug', read_only=True)
    telegram_username = serializers.CharField(source='billing_profile.telegram_username', read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user_email', 'user_name', 'plan_name', 'plan_slug',
            'payment_reference', 'status', 'start_date', 'end_date',
            'auto_renew', 'telegram_username', 'cancel_at_period_end',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'start_date', 'end_date',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        """Get user's full name or email"""
        user = obj.billing_profile.user
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.email
    
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
    """Serializer for coupon code management"""
    status = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    discount_display = serializers.ReadOnlyField(source='get_discount_display')
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description', 'discount_type', 'discount_value',
            'minimum_amount', 'maximum_discount', 'usage_limit', 'usage_count',
            'usage_limit_per_user', 'valid_from', 'valid_until', 'applicable_categories',
            'is_active', 'first_time_users_only', 'status', 'is_valid', 
            'discount_display', 'usage_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def get_usage_percentage(self, obj):
        """Get usage percentage"""
        if not obj.usage_limit:
            return 0
        return min(100, (obj.usage_count / obj.usage_limit) * 100)
    
    def validate_code(self, value):
        """Validate coupon code format"""
        if not value.isalnum():
            raise serializers.ValidationError("Coupon code must be alphanumeric")
        return value.upper()
    
    def validate(self, data):
        """Cross-field validation"""
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value')
        
        # Validate dates
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError("Valid until date must be after valid from date")
        
        # Validate discount value based on type
        if discount_type == 'percentage':
            if not (0 < discount_value <= 100):
                raise serializers.ValidationError("Percentage discount must be between 0 and 100")
        elif discount_type == 'fixed_amount':
            if discount_value <= 0:
                raise serializers.ValidationError("Fixed amount discount must be positive")
        
        return data

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
