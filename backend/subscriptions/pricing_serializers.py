from rest_framework import serializers
from .models import PricingPlan, CouponCode, CouponUsage


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for pricing plans management
    
    Note: Telegram groups use simplified structure:
    - 'signals_main' for all signal subscribers (weekly, monthly, yearly)
    - 'vip_main' for all VIP subscribers
    - 'mentorship_group' for mentorship subscribers
    Bot tracks expiration based on payment data, not group separation.
    """
    current_price = serializers.SerializerMethodField()
    subscription_count = serializers.SerializerMethodField()
    revenue_total = serializers.SerializerMethodField()

    class Meta:
        model = PricingPlan
        fields = [
            'id', 'plan_type', 'plan_category', 'billing_cycle',
            'name', 'description', 'price', 'current_price', 'currency',
            'telegram_groups', 'discount_percentage', 'promotional_price',
            'promotion_start', 'promotion_end', 'is_active', 'is_featured',
            'sort_order', 'features_list', 'call_to_action',
            'subscription_count', 'revenue_total', 'created_at', 'updated_at'
        ]

    def get_current_price(self, obj):
        """Get the current effective price (considering promotions)"""
        return obj.current_price

    def get_subscription_count(self, obj):
        """Get number of active subscriptions for this plan"""
        try:
            from .models import SignalSubscription
            return SignalSubscription.objects.filter(
                plan_type=obj.plan_type,
                payment_status='verified'
            ).count()
        except:
            return 0

    def get_revenue_total(self, obj):
        """Get total revenue from this plan"""
        try:
            from .models import SignalSubscription
            from django.db.models import Sum
            result = SignalSubscription.objects.filter(
                plan_type=obj.plan_type,
                payment_status='verified'
            ).aggregate(total=Sum('amount_paid'))
            return float(result['total'] or 0)
        except:
            return 0.0


class CouponCodeSerializer(serializers.ModelSerializer):
    """Serializer for coupon codes management"""
    usage_percentage = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = CouponCode
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'minimum_amount', 'usage_limit', 'usage_count',
            'usage_percentage', 'applicable_plans', 'valid_from', 'valid_until',
            'is_active', 'is_valid', 'days_remaining', 'created_at', 'updated_at'
        ]

    def get_usage_percentage(self, obj):
        """Get usage percentage"""
        if obj.usage_limit and obj.usage_limit > 0:
            return round((obj.usage_count / obj.usage_limit) * 100, 1)
        return 0

    def get_is_valid(self, obj):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return (obj.is_active and 
                now >= obj.valid_from and 
                now <= obj.valid_until and
                (not obj.usage_limit or obj.usage_count < obj.usage_limit))

    def get_days_remaining(self, obj):
        """Get days remaining until expiration"""
        from django.utils import timezone
        now = timezone.now()
        if obj.valid_until > now:
            delta = obj.valid_until - now
            return delta.days
        return 0


class CouponUsageSerializer(serializers.ModelSerializer):
    """Serializer for coupon usage tracking"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'user', 'user_email', 'coupon', 'coupon_code',
            'subscription_id', 'discount_amount', 'original_amount',
            'final_amount', 'used_at'
        ]


class PricingAnalyticsSerializer(serializers.Serializer):
    """Serializer for pricing analytics data"""
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    active_plans = serializers.IntegerField()
    total_plans = serializers.IntegerField()
    active_coupons = serializers.IntegerField()
    total_coupon_usage = serializers.IntegerField()
    coupon_discount_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    plan_performance = serializers.ListField(
        child=serializers.DictField()
    )
    revenue_by_category = serializers.DictField()
    monthly_revenue_trend = serializers.ListField(
        child=serializers.DictField()
    )


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for coupon validation requests"""
    code = serializers.CharField(max_length=50)
    plan_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_code(self, value):
        """Validate coupon code format"""
        return value.upper().strip()