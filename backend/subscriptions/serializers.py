from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    PricingPlan, SignalSubscription, PaymentTransaction, 
    TelegramGroupManagement, Coupon,
    BillingProfile, PaymentMethod, Subscription, Payment
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
    current_price = serializers.ReadOnlyField()
    is_on_promotion = serializers.ReadOnlyField()
    savings_amount = serializers.ReadOnlyField()
    active_subscriptions_count = serializers.SerializerMethodField()
    access_level = serializers.ReadOnlyField(source='get_access_level')
    
    class Meta:
        model = PricingPlan
        fields = [
            'id', 'plan_type', 'plan_category', 'billing_cycle', 'name', 'description', 
            'price', 'currency', 'telegram_groups', 'discount_percentage', 
            'promotional_price', 'promotion_start', 'promotion_end', 'is_active', 
            'is_featured', 'sort_order', 'features_list', 'call_to_action', 
            'current_price', 'is_on_promotion', 'savings_amount', 'access_level',
            'active_subscriptions_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_subscriptions_count(self, obj):
        """Get count of active subscriptions using this plan"""
        return SignalSubscription.objects.filter(
            pricing_plan=obj,
            payment_status='verified',
            subscription_end__gt=timezone.now()
        ).count()
    
    def validate(self, data):
        """Validate promotion dates"""
        promotion_start = data.get('promotion_start')
        promotion_end = data.get('promotion_end')
        promotional_price = data.get('promotional_price')
        
        # If promotional price is set, ensure dates are provided
        if promotional_price and promotional_price > 0:
            if not promotion_start or not promotion_end:
                raise serializers.ValidationError(
                    "Promotion start and end dates are required when setting promotional price"
                )
            
            if promotion_start >= promotion_end:
                raise serializers.ValidationError(
                    "Promotion end date must be after start date"
                )
        
        return data

class SignalSubscriptionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    pricing_plan_name = serializers.CharField(source='pricing_plan.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = SignalSubscription
        fields = [
            'id', 'user_email', 'user_name', 'plan_type', 'pricing_plan_name',
            'paystack_reference', 'amount_paid', 'currency', 'payment_status',
            'payment_verified_at', 'subscription_start', 'subscription_end',
            'auto_renewal', 'telegram_username', 'telegram_group_name',
            'telegram_status', 'telegram_added_at', 'admin_notes',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'payment_verified_at',
            'subscription_start', 'subscription_end', 'telegram_added_at',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        """Get user's full name or email"""
        user = obj.user
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.email

class PaymentTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    subscription_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'user_email', 'transaction_type', 'reference', 'amount',
            'currency', 'payment_method', 'subscription_plan', 'status',
            'processed_at', 'created_at'
        ]
        read_only_fields = ['id', 'user_email', 'created_at']
    
    def get_subscription_plan(self, obj):
        """Get associated subscription plan details"""
        if obj.signal_subscription:
            return {
                'plan_type': obj.signal_subscription.plan_type,
                'telegram_username': obj.signal_subscription.telegram_username,
                'subscription_end': obj.signal_subscription.subscription_end
            }
        return None

class TelegramGroupManagementSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='signal_subscription.user.email', read_only=True)
    subscription_plan = serializers.CharField(source='signal_subscription.plan_type', read_only=True)
    subscription_end = serializers.DateTimeField(source='signal_subscription.subscription_end', read_only=True)
    processed_by_email = serializers.CharField(source='processed_by.email', read_only=True)
    
    class Meta:
        model = TelegramGroupManagement
        fields = [
            'id', 'action_type', 'telegram_username', 'telegram_group',
            'user_email', 'subscription_plan', 'subscription_end',
            'status', 'admin_notes', 'created_at', 'processed_at',
            'processed_by_email'
        ]
        read_only_fields = [
            'id', 'user_email', 'subscription_plan', 'subscription_end',
            'processed_by_email', 'created_at', 'processed_at'
        ]

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


class EnhancedSignalSubscriptionSerializer(serializers.ModelSerializer):
    """Enhanced subscription serializer with pricing and coupon info"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    pricing_plan_info = PricingPlanSerializer(source='pricing_plan', read_only=True)
    coupon_info = CouponSerializer(source='coupon_used', read_only=True)
    plan_category = serializers.ReadOnlyField()
    access_level = serializers.ReadOnlyField()
    telegram_groups = serializers.ReadOnlyField()
    savings_amount = serializers.ReadOnlyField(source='get_savings')
    
    class Meta:
        model = SignalSubscription
        fields = [
            'id', 'user_email', 'user_name', 'plan_type', 'pricing_plan_info',
            'plan_category', 'access_level', 'telegram_groups', 'paystack_reference',
            'amount_paid', 'original_amount', 'discount_amount', 'savings_amount',
            'currency', 'payment_status', 'payment_verified_at', 'subscription_start',
            'subscription_end', 'auto_renewal', 'telegram_username', 'telegram_status',
            'telegram_added_at', 'coupon_info', 'admin_notes', 'is_active',
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'paystack_reference', 'payment_verified_at',
            'telegram_added_at', 'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        """Get user full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

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
