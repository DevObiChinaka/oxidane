# Advanced admin interface for pricing and subscription management
from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput, NumberInput
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q
from decimal import Decimal
import json
import csv

from .models import (
    PricingPlan, CouponCode, CouponUsage, SignalSubscription,
    TelegramGroupManagement
)

# Custom admin site configuration
class PricingPlanInline(admin.TabularInline):
    """Inline editor for pricing plans when editing coupons"""
    model = CouponCode.applicable_plans.through
    extra = 0
    verbose_name = "Applicable Plan"
    verbose_name_plural = "Applicable Plans"

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    """Enhanced admin interface for pricing plan management"""
    list_display = [
        'name', 'plan_type', 'plan_category', 'billing_cycle', 
        'current_price_display', 'currency', 'is_active_display',
        'promotion_status', 'usage_count'
    ]
    list_filter = [
        'plan_category', 'billing_cycle', 'currency', 'is_active', 
        'is_featured', 'created_at'
    ]
    search_fields = ['name', 'plan_type', 'description']
    ordering = ['sort_order', 'plan_category', 'billing_cycle', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('plan_type', 'plan_category', 'billing_cycle', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'discount_percentage', 'promotional_price'),
            'classes': ('wide',)
        }),
        ('Promotions', {
            'fields': ('promotion_start', 'promotion_end'),
            'classes': ('collapse',)
        }),
        ('Telegram Integration', {
            'fields': ('telegram_groups',),
            'description': 'JSON list of telegram group keys: ["mentorship", "signals", "vip"]',
            'classes': ('wide',)
        }),
        ('Display & Marketing', {
            'fields': ('features_list', 'call_to_action', 'is_featured', 'sort_order'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    # Custom form widgets for better UX
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '40'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
        models.DecimalField: {'widget': NumberInput(attrs={'step': '0.01'})},
    }
    
    actions = ['activate_plans', 'deactivate_plans', 'bulk_update_currency', 'export_plans']
    
    def current_price_display(self, obj):
        """Display current effective price with promotion indicators"""
        price = obj.current_price
        if obj.is_on_promotion:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span> '
                '<strong style="color: #28a745;">${}</strong>',
                obj.price, price
            )
        return f"${price}"
    current_price_display.short_description = "Current Price"
    current_price_display.admin_order_field = 'price'
    
    def is_active_display(self, obj):
        """Display active status with color coding"""
        if obj.is_active:
            return format_html('<span style="color: #28a745;">✓ Active</span>')
        return format_html('<span style="color: #dc3545;">✗ Inactive</span>')
    is_active_display.short_description = "Status"
    is_active_display.admin_order_field = 'is_active'
    
    def promotion_status(self, obj):
        """Display promotion status"""
        if obj.is_on_promotion:
            savings = obj.savings_amount
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">🎯 Save ${}</span>', 
                savings
            )
        return format_html('<span style="color: #6c757d;">No promotion</span>')
    promotion_status.short_description = "Promotion"
    
    def usage_count(self, obj):
        """Show how many active subscriptions use this plan"""
        count = SignalSubscription.objects.filter(
            pricing_plan=obj, 
            payment_status='verified'
        ).count()
        if count > 0:
            url = reverse('admin:subscriptions_signalsubscription_changelist') + f'?pricing_plan__id__exact={obj.id}'
            return format_html('<a href="{}">{} subscriptions</a>', url, count)
        return "0 subscriptions"
    usage_count.short_description = "Usage"
    
    # Custom actions
    def activate_plans(self, request, queryset):
        """Bulk activate plans"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} plans activated.')
    activate_plans.short_description = "Activate selected plans"
    
    def deactivate_plans(self, request, queryset):
        """Bulk deactivate plans"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} plans deactivated.')
    deactivate_plans.short_description = "Deactivate selected plans"
    
    def export_plans(self, request, queryset):
        """Export plans to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pricing_plans.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Plan Type', 'Category', 'Billing Cycle', 'Price', 'Currency', 'Active'])
        
        for plan in queryset:
            writer.writerow([
                plan.name, plan.plan_type, plan.plan_category,
                plan.billing_cycle, plan.current_price, plan.currency, plan.is_active
            ])
        
        return response
    export_plans.short_description = "Export selected plans to CSV"

@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    """Enhanced admin interface for coupon code management"""
    list_display = [
        'code', 'name', 'discount_display', 'status_display', 
        'usage_stats', 'valid_period', 'created_by'
    ]
    list_filter = [
        'discount_type', 'is_active', 'first_time_users_only',
        'created_at', 'valid_from', 'valid_until'
    ]
    search_fields = ['code', 'name', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'minimum_amount', 'maximum_discount'),
            'classes': ('wide',)
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user'),
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until'),
        }),
        ('Plan Restrictions', {
            'fields': ('applicable_plans', 'applicable_categories'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'first_time_users_only'),
        }),
    )
    
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_plans']
    
    actions = ['activate_coupons', 'deactivate_coupons', 'export_coupon_usage']
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new coupon"""
        if not change:  # Creating new coupon
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def discount_display(self, obj):
        """Display discount in human readable format"""
        return obj.get_discount_display()
    discount_display.short_description = "Discount"
    
    def status_display(self, obj):
        """Display coupon status with color coding"""
        status = obj.status
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d', 
            'expired': '#dc3545',
            'used_up': '#ffc107'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, '#000'),
            status.title()
        )
    status_display.short_description = "Status"
    
    def usage_stats(self, obj):
        """Display usage statistics"""
        used = obj.usage_count
        limit = obj.usage_limit or "∞"
        
        if obj.usage_limit and obj.usage_count >= obj.usage_limit:
            color = "#dc3545"  # Red for used up
        elif obj.usage_count > 0:
            color = "#ffc107"  # Yellow for partially used
        else:
            color = "#28a745"  # Green for unused
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{}</span>',
            color, used, limit
        )
    usage_stats.short_description = "Usage"
    
    def valid_period(self, obj):
        """Display validity period"""
        now = timezone.now()
        start = obj.valid_from
        end = obj.valid_until
        
        if now < start:
            return format_html('<span style="color: #007bff;">Starts {}</span>', start.strftime('%m/%d/%Y'))
        elif now > end:
            return format_html('<span style="color: #dc3545;">Expired {}</span>', end.strftime('%m/%d/%Y'))
        else:
            return format_html('<span style="color: #28a745;">Valid until {}</span>', end.strftime('%m/%d/%Y'))
    valid_period.short_description = "Validity"
    
    # Custom actions
    def activate_coupons(self, request, queryset):
        """Bulk activate coupons"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} coupons activated.')
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        """Bulk deactivate coupons"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} coupons deactivated.')
    deactivate_coupons.short_description = "Deactivate selected coupons"

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    """Admin interface for coupon usage tracking"""
    list_display = ['coupon_code', 'user_email', 'discount_amount_display', 'savings_display', 'used_at']
    list_filter = ['used_at', 'coupon__discount_type']
    search_fields = ['coupon__code', 'user__email', 'subscription__paystack_reference']
    ordering = ['-used_at']
    
    readonly_fields = ['coupon', 'user', 'subscription', 'original_amount', 'discount_amount', 'final_amount', 'used_at']
    
    def has_add_permission(self, request):
        """Prevent manual creation of usage records"""
        return False
    
    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = "Coupon Code"
    coupon_code.admin_order_field = 'coupon__code'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = 'user__email'
    
    def discount_amount_display(self, obj):
        return f"${obj.discount_amount}"
    discount_amount_display.short_description = "Discount Applied"
    discount_amount_display.admin_order_field = 'discount_amount'
    
    def savings_display(self, obj):
        """Show savings percentage"""
        if obj.original_amount > 0:
            percentage = (obj.discount_amount / obj.original_amount) * 100
            return f"{percentage:.1f}%"
        return "0%"
    savings_display.short_description = "Savings %"

# Enhanced SignalSubscription admin with pricing integration
class SignalSubscriptionAdmin(admin.ModelAdmin):
    """Enhanced subscription admin with pricing plan integration"""
    list_display = [
        'user_email', 'plan_display', 'amount_with_savings', 'payment_status',
        'subscription_period', 'telegram_status', 'created_at'
    ]
    list_filter = [
        'plan_type', 'payment_status', 'telegram_status', 'pricing_plan',
        'created_at', 'coupon_used'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'paystack_reference', 'telegram_username'
    ]
    ordering = ['-created_at']
    
    readonly_fields = ['paystack_reference', 'created_at', 'updated_at', 'payment_verified_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'telegram_username')
        }),
        ('Subscription Details', {
            'fields': ('plan_type', 'pricing_plan', 'subscription_start', 'subscription_end'),
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'currency', 'paystack_reference', 'payment_status', 'payment_verified_at'),
        }),
        ('Coupon Information', {
            'fields': ('coupon_used', 'original_amount', 'discount_amount'),
            'classes': ('collapse',)
        }),
        ('Telegram Status', {
            'fields': ('telegram_status', 'telegram_group_name', 'telegram_added_at'),
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
    user_email.admin_order_field = 'user__email'
    
    def plan_display(self, obj):
        """Display plan with pricing plan info"""
        if obj.pricing_plan:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.pricing_plan.name,
                obj.plan_type
            )
        return obj.plan_type
    plan_display.short_description = "Plan"
    
    def amount_with_savings(self, obj):
        """Display amount with coupon savings if applicable"""
        if obj.coupon_used and obj.discount_amount > 0:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span><br>'
                '<strong style="color: #28a745;">${}</strong> '
                '<small style="color: #28a745;">(Save ${})</small>',
                obj.original_amount, obj.amount_paid, obj.discount_amount
            )
        return f"${obj.amount_paid}"
    amount_with_savings.short_description = "Amount"
    amount_with_savings.admin_order_field = 'amount_paid'
    
    def subscription_period(self, obj):
        """Display subscription period"""
        if obj.subscription_start and obj.subscription_end:
            return f"{obj.subscription_start.strftime('%m/%d/%Y')} - {obj.subscription_end.strftime('%m/%d/%Y')}"
        return "Not set"
    subscription_period.short_description = "Subscription Period"

# Register the enhanced admin
admin.site.register(SignalSubscription, SignalSubscriptionAdmin)

# Admin site customization
admin.site.site_header = "OxiWorld Pricing & Subscription Management"
admin.site.site_title = "OxiWorld Admin"
admin.site.index_title = "Pricing & Subscription Dashboard"