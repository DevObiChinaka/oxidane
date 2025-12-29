from rest_framework import serializers
from .models import SubscriptionPlan, Coupon, Subscription


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for subscription plans management (Phase 0.5)
    
    Uses new SubscriptionPlan model with dynamic features and multi-currency support.
    """
    price_display = serializers.SerializerMethodField()
    monthly_equivalent = serializers.SerializerMethodField()
    subscription_count = serializers.SerializerMethodField()
    revenue_total = serializers.SerializerMethodField()
    feature_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 
            'base_price', 'billing_period', 'price_display', 'monthly_equivalent',
            'is_active', 'is_featured',
            'sort_order', 'limits', 'paystack_plan_code',
            'feature_count', 'subscription_count', 'revenue_total', 
            'created_at', 'updated_at'
        ]

    def get_price_display(self, obj):
        """Get formatted price with period"""
        return obj.get_price_display()
    
    def get_monthly_equivalent(self, obj):
        """Get monthly equivalent price for comparison"""
        return float(obj.get_monthly_equivalent())
    
    
    def get_feature_count(self, obj):
        """Get number of features in plan"""
        return obj.get_feature_count()

    def get_subscription_count(self, obj):
        """Get number of active subscriptions for this plan"""
        try:
            return Subscription.objects.filter(
                plan=obj,
                status='active'
            ).count()
        except:
            return 0

    def get_revenue_total(self, obj):
        """Get total revenue from this plan"""
        try:
            from django.db.models import Sum
            # TODO: Calculate from actual payment transactions when PaymentTransaction model is recreated
            # For now, estimate based on subscription count * base price
            active_subs = Subscription.objects.filter(
                plan=obj,
                status='active'
            ).count()
            return float(active_subs * obj.base_price)
        except:
            return 0.0


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for coupon codes management"""
    usage_percentage = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'minimum_amount', 'usage_limit', 'usage_count',
            'usage_percentage', 'plans', 'valid_from', 'valid_until',
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
