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
    PricingPlan, SignalSubscription,
    TelegramGroupManagement, Coupon, ReferralCode, Referral, ReferralCredit,
    TelegramConfiguration, TelegramGroup
)

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


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    """Admin interface for referral code management"""
    list_display = [
        'code', 'referrer_link', 'referrer_discount_display', 
        'referee_discount_display', 'usage_display', 
        'validity_status', 'is_active'
    ]
    list_filter = ['is_active', 'referrer_discount_type', 'referee_discount_type', 'created_at']
    search_fields = ['code', 'referrer__username', 'referrer__email', 'description']
    readonly_fields = ['id', 'current_uses', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'referrer', 'description', 'is_active')
        }),
        ('Referrer Discount (Reward for referring)', {
            'fields': ('referrer_discount_type', 'referrer_discount_value'),
            'description': 'Discount given to the referrer when someone uses their code'
        }),
        ('Referee Discount (For person using code)', {
            'fields': ('referee_discount_type', 'referee_discount_value'),
            'description': 'Discount given to the person using the referral code'
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'current_uses'),
            'description': 'Leave max_uses empty for unlimited uses'
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until'),
            'description': 'Leave valid_until empty for no expiration'
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def referrer_link(self, obj):
        """Display referrer as a link"""
        if obj.referrer:
            url = reverse('admin:auth_user_change', args=[obj.referrer.pk])
            return format_html('<a href="{}">{}</a>', url, obj.referrer.username)
        return '-'
    referrer_link.short_description = 'Referrer'
    
    def referrer_discount_display(self, obj):
        """Display referrer discount"""
        return obj.get_referrer_discount_display()
    referrer_discount_display.short_description = 'Referrer Gets'
    
    def referee_discount_display(self, obj):
        """Display referee discount"""
        return obj.get_referee_discount_display()
    referee_discount_display.short_description = 'Referee Gets'
    
    def usage_display(self, obj):
        """Display usage statistics"""
        if obj.max_uses:
            percentage = (obj.current_uses / obj.max_uses * 100) if obj.max_uses > 0 else 0
            color = '#28a745' if percentage < 75 else ('#ffc107' if percentage < 90 else '#dc3545')
            return format_html(
                '<span style="color: {};">{} / {}</span> ({}%)',
                color, obj.current_uses, obj.max_uses, int(percentage)
            )
        return f'{obj.current_uses} (unlimited)'
    usage_display.short_description = 'Usage'
    usage_display.admin_order_field = 'current_uses'
    
    def validity_status(self, obj):
        """Display validity status"""
        if not obj.is_active:
            return format_html('<span style="color: #dc3545;">● Inactive</span>')
        
        if not obj.is_valid():
            now = timezone.now()
            if obj.valid_from and now < obj.valid_from:
                return format_html('<span style="color: #ffc107;">● Not Started</span>')
            else:
                return format_html('<span style="color: #dc3545;">● Expired</span>')
        
        if not obj.is_usage_available():
            return format_html('<span style="color: #dc3545;">● Exhausted</span>')
        
        return format_html('<span style="color: #28a745;">● Valid</span>')
    validity_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('referrer')
    
    actions = ['activate_codes', 'deactivate_codes', 'reset_usage']
    
    def activate_codes(self, request, queryset):
        """Bulk activate referral codes"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Successfully activated {updated} referral code(s).')
    activate_codes.short_description = "Activate selected referral codes"
    
    def deactivate_codes(self, request, queryset):
        """Bulk deactivate referral codes"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Successfully deactivated {updated} referral code(s).')
    deactivate_codes.short_description = "Deactivate selected referral codes"
    
    def reset_usage(self, request, queryset):
        """Reset usage counter for selected codes"""
        updated = queryset.update(current_uses=0)
        self.message_user(request, f'Successfully reset usage for {updated} referral code(s).')
    reset_usage.short_description = "Reset usage counter to 0"


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """Admin interface for referral conversion tracking"""
    list_display = [
        'id', 'referrer_display', 'referee_display', 'referral_code_display',
        'status_display', 'discount_display', 'conversion_date_display'
    ]
    list_filter = [
        'status', 'conversion_date', 'currency',
    ]
    search_fields = [
        'referrer__username', 'referrer__email',
        'referee__username', 'referee__email',
        'referral_code__code', 'notes'
    ]
    readonly_fields = [
        'id', 'conversion_date', 'savings_display'
    ]
    fieldsets = (
        ('Referral Information', {
            'fields': (
                'id', 'referral_code', 'referrer', 'referee', 'subscription'
            )
        }),
        ('Discount Details', {
            'fields': (
                'original_amount', 
                'referee_discount_percent',
                'referee_discount_amount',
                'final_amount',
                'currency',
                'savings_display'
            )
        }),
        ('Status & Dates', {
            'fields': (
                'status', 'conversion_date', 'cancelled_date', 'notes'
            )
        }),
    )
    date_hierarchy = 'conversion_date'
    ordering = ['-conversion_date']
    
    def referrer_display(self, obj):
        """Display referrer with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:accounts_customuser_change', args=[obj.referrer.id]),
            obj.referrer.username
        )
    referrer_display.short_description = 'Referrer'
    
    def referee_display(self, obj):
        """Display referee with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:accounts_customuser_change', args=[obj.referee.id]),
            obj.referee.username
        )
    referee_display.short_description = 'Referee'
    
    def referral_code_display(self, obj):
        """Display referral code with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:subscriptions_referralcode_change', args=[obj.referral_code.id]),
            obj.referral_code.code
        )
    referral_code_display.short_description = 'Code'
    
    def status_display(self, obj):
        """Display status with color"""
        color = obj.get_status_display_color()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def discount_display(self, obj):
        """Display discount applied"""
        return format_html(
            '<span title="Original: {} {}">{} {} ({}%)</span>',
            obj.original_amount, obj.currency,
            obj.referee_discount_amount, obj.currency,
            obj.referee_discount_percent
        )
    discount_display.short_description = 'Discount Applied'
    
    def conversion_date_display(self, obj):
        """Display conversion date"""
        return obj.conversion_date.strftime('%Y-%m-%d %H:%M')
    conversion_date_display.short_description = 'Converted'
    
    def savings_display(self, obj):
        """Display total savings"""
        return format_html(
            '<strong>{} {}</strong> saved ({}% discount)',
            obj.referee_discount_amount,
            obj.currency,
            obj.referee_discount_percent
        )
    savings_display.short_description = 'Total Savings'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('referrer', 'referee', 'referral_code', 'subscription')
    
    actions = ['mark_as_cancelled_action', 'export_to_csv']
    
    def mark_as_cancelled_action(self, request, queryset):
        """Bulk cancel referrals"""
        for referral in queryset:
            referral.mark_as_cancelled(reason='Cancelled via admin bulk action')
        count = queryset.count()
        self.message_user(request, f'Successfully cancelled {count} referral(s).')
    mark_as_cancelled_action.short_description = "Mark as cancelled"
    
    def export_to_csv(self, request, queryset):
        """Export selected referrals to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="referrals_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Referrer', 'Referee', 'Referral Code', 'Status',
            'Original Amount', 'Discount %', 'Discount Amount', 'Final Amount',
            'Currency', 'Conversion Date', 'Notes'
        ])
        
        for referral in queryset:
            writer.writerow([
                str(referral.id),
                referral.referrer.username,
                referral.referee.username,
                referral.referral_code.code,
                referral.get_status_display(),
                referral.original_amount,
                referral.referee_discount_percent,
                referral.referee_discount_amount,
                referral.final_amount,
                referral.currency,
                referral.conversion_date.strftime('%Y-%m-%d %H:%M:%S'),
                referral.notes
            ])
        
        return response
    export_to_csv.short_description = "Export to CSV"


@admin.register(ReferralCredit)
class ReferralCreditAdmin(admin.ModelAdmin):
    """Admin interface for referral credits (earned discounts)"""
    list_display = [
        'user_display', 'credit_percentage', 'status_display',
        'earned_from_display', 'earned_date', 'used_date_display'
    ]
    list_filter = [
        'is_used', 'earned_date',
        ('expires_at', admin.EmptyFieldListFilter),
    ]
    search_fields = [
        'user__username', 'user__email', 'notes'
    ]
    readonly_fields = [
        'id', 'earned_date', 'availability_display'
    ]
    fieldsets = (
        ('Credit Information', {
            'fields': (
                'id', 'user', 'credit_percentage', 'earned_from_referral'
            )
        }),
        ('Usage Tracking', {
            'fields': (
                'is_used', 'used_on_subscription', 'used_date',
                'availability_display'
            )
        }),
        ('Dates & Expiry', {
            'fields': (
                'earned_date', 'expires_at', 'notes'
            )
        }),
    )
    date_hierarchy = 'earned_date'
    ordering = ['-earned_date']
    
    def user_display(self, obj):
        """Display user with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:accounts_customuser_change', args=[obj.user.id]),
            obj.user.username
        )
    user_display.short_description = 'User'
    
    def status_display(self, obj):
        """Display status with color"""
        if obj.is_used:
            return format_html('<span style="color: #6c757d;">✓ Used</span>')
        elif obj.is_expired():
            return format_html('<span style="color: #dc3545;">✗ Expired</span>')
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">● Available</span>')
    status_display.short_description = 'Status'
    
    def earned_from_display(self, obj):
        """Display the referral that earned this credit"""
        return format_html(
            '<a href="{}">Referral {}</a>',
            reverse('admin:subscriptions_referral_change', args=[obj.earned_from_referral.id]),
            str(obj.earned_from_referral.id)[:8]
        )
    earned_from_display.short_description = 'Earned From'
    
    def used_date_display(self, obj):
        """Display used date or dash"""
        if obj.used_date:
            return obj.used_date.strftime('%Y-%m-%d %H:%M')
        return '—'
    used_date_display.short_description = 'Used On'
    
    def availability_display(self, obj):
        """Display availability status"""
        if obj.is_available():
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Available for use</span>')
        elif obj.is_used:
            return format_html('<span style="color: #6c757d;">Used on {}</span>', obj.used_date.strftime('%Y-%m-%d'))
        elif obj.is_expired():
            return format_html('<span style="color: #dc3545;">Expired on {}</span>', obj.expires_at.strftime('%Y-%m-%d'))
        return '—'
    availability_display.short_description = 'Availability'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'earned_from_referral', 'used_on_subscription')
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        """Export credits to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="referral_credits_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Credit %', 'Is Used', 'Earned Date',
            'Used Date', 'Expires At', 'Notes'
        ])
        
        for credit in queryset:
            writer.writerow([
                str(credit.id),
                credit.user.username,
                credit.credit_percentage,
                'Yes' if credit.is_used else 'No',
                credit.earned_date.strftime('%Y-%m-%d %H:%M:%S'),
                credit.used_date.strftime('%Y-%m-%d %H:%M:%S') if credit.used_date else '',
                credit.expires_at.strftime('%Y-%m-%d') if credit.expires_at else 'Never',
                credit.notes
            ])
        
        return response
    export_to_csv.short_description = "Export to CSV"


@admin.register(TelegramConfiguration)
class TelegramConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for Telegram bot configuration (singleton).
    Only one instance should exist.
    """
    list_display = [
        'bot_username_display', 'status_display', 'connection_display',
        'auto_add_enabled', 'auto_remove_enabled', 'last_health_check'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'masked_token_display',
        'connection_status_display', 'last_health_check'
    ]
    fieldsets = (
        ('Bot Credentials', {
            'fields': (
                'id', 'bot_token', 'masked_token_display', 'bot_username'
            ),
            'description': 'Configure your Telegram bot credentials from @BotFather'
        }),
        ('Status', {
            'fields': (
                'is_enabled', 'connection_status_display', 'last_health_check'
            )
        }),
        ('Automation Settings', {
            'fields': (
                'auto_add_enabled', 'auto_remove_enabled'
            ),
            'description': 'Control automatic user management'
        }),
        ('Messages', {
            'fields': (
                'welcome_message', 'removal_message'
            ),
            'classes': ('collapse',),
            'description': 'Customize messages sent to users'
        }),
        ('Queue & Rate Limiting', {
            'fields': (
                'max_retries', 'retry_delay_seconds', 'rate_limit_per_minute'
            ),
            'classes': ('collapse',),
            'description': 'Configure queue processing and rate limiting'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def bot_username_display(self, obj):
        """Display bot username or placeholder"""
        if obj.bot_username:
            return format_html('<strong>{}</strong>', obj.bot_username)
        return format_html('<em style="color: #6c757d;">(not configured)</em>')
    bot_username_display.short_description = 'Bot Username'
    
    def status_display(self, obj):
        """Display enabled/disabled status"""
        if obj.is_enabled:
            return format_html('<span style="color: #28a745;">● Enabled</span>')
        return format_html('<span style="color: #dc3545;">○ Disabled</span>')
    status_display.short_description = 'Status'
    
    def connection_display(self, obj):
        """Display connection status"""
        if not obj.is_enabled:
            return format_html('<span style="color: #6c757d;">⚫ Disabled</span>')
        elif obj.is_connected:
            return format_html('<span style="color: #28a745;">● Connected</span>')
        else:
            return format_html('<span style="color: #dc3545;">○ Disconnected</span>')
    connection_display.short_description = 'Connection'
    
    def masked_token_display(self, obj):
        """Display masked bot token for security"""
        masked = obj.get_masked_token()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code>{}</code>', masked)
    masked_token_display.short_description = 'Token (Masked)'
    
    def connection_status_display(self, obj):
        """Display detailed connection status"""
        if not obj.is_enabled:
            return format_html('<div style="color: #6c757d;">⚫ Bot is disabled</div>')
        
        if obj.is_connected:
            return format_html(
                '<div style="color: #28a745;"><strong>✓ Connected</strong></div>'
                '<div style="font-size: 11px; color: #6c757d;">Bot is operational</div>'
            )
        else:
            error_msg = obj.connection_error or 'Not tested yet'
            return format_html(
                '<div style="color: #dc3545;"><strong>✗ Disconnected</strong></div>'
                '<div style="font-size: 11px; color: #dc3545;">{}</div>',
                error_msg
            )
    connection_status_display.short_description = 'Connection Status'
    
    def has_add_permission(self, request):
        """Prevent adding more than one configuration (singleton)"""
        if TelegramConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Allow delete to reset configuration if needed"""
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Override to handle token changes"""
        if 'bot_token' in form.changed_data and obj.bot_token:
            # Token changed, mark as disconnected for re-verification
            obj.is_connected = False
            obj.connection_error = 'Token changed - please test connection'
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """No special optimization needed for singleton"""
        return super().get_queryset(request)


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    """
    Admin interface for TelegramGroup model.
    Manages Telegram groups with plan associations, settings, and permissions.
    Phase 0.5, Task 0.5.7
    """
    list_display = [
        'name',
        'chat_id_display',
        'is_active_badge',
        'is_private',
        'member_count_display',
        'capacity_status',
        'plan_count',
        'auto_settings_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'is_private',
        'auto_add_enabled',
        'auto_remove_enabled',
        'notification_enabled',
        'is_admin',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'chat_id',
        'group_key',
        'description',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_sync_at',
        'capacity_indicator',
        'permissions_summary',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'name',
                'chat_id',
                'group_key',
                'description',
            )
        }),
        ('Status & Visibility', {
            'fields': (
                'is_active',
                'is_private',
                'invite_link',
                'sort_order',
            )
        }),
        ('Member Tracking', {
            'fields': (
                'member_count',
                'max_members',
                'capacity_indicator',
                'last_sync_at',
            )
        }),
        ('Auto-Management Settings', {
            'fields': (
                'auto_add_enabled',
                'auto_remove_enabled',
                'welcome_message',
                'removal_message',
                'notification_enabled',
            ),
            'classes': ['collapse'],
        }),
        ('Bot Permissions', {
            'fields': (
                'permissions_summary',
                'can_send_messages',
                'can_add_users',
                'can_remove_users',
                'can_pin_messages',
                'can_delete_messages',
                'is_admin',
            ),
            'classes': ['collapse'],
        }),
        ('Associated Plans', {
            'fields': ('associated_plans',),
            'description': 'Select subscription plans that grant access to this group'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse'],
        }),
    )
    
    filter_horizontal = ['associated_plans']
    
    ordering = ['sort_order', 'name']
    
    actions = [
        'activate_groups',
        'deactivate_groups',
        'enable_auto_add',
        'disable_auto_add',
        'reset_member_counts',
    ]
    
    # Custom display methods
    
    @admin.display(description='Chat ID', ordering='chat_id')
    def chat_id_display(self, obj):
        """Display chat ID with copy button"""
        return format_html(
            '<span title="Click to copy" style="cursor:pointer; font-family:monospace">{}</span>',
            obj.chat_id
        )
    
    @admin.display(description='Status', boolean=True)
    def is_active_badge(self, obj):
        """Display active status as badge"""
        return obj.is_active
    
    @admin.display(description='Members', ordering='member_count')
    def member_count_display(self, obj):
        """Display member count with max limit"""
        if obj.max_members:
            percentage = (obj.member_count / obj.max_members) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
            return format_html(
                '<span style="color:{}">{} / {}</span>',
                color,
                obj.member_count,
                obj.max_members
            )
        return f"{obj.member_count} (unlimited)"
    
    @admin.display(description='Capacity')
    def capacity_status(self, obj):
        """Display capacity status"""
        if obj.max_members is None:
            return format_html('<span style="color:green">✓ Unlimited</span>')
        if obj.has_capacity():
            available = obj.max_members - obj.member_count
            return format_html('<span style="color:green">✓ {} slots</span>', available)
        return format_html('<span style="color:red">✗ Full</span>')
    
    @admin.display(description='Plans', ordering='associated_plans__count')
    def plan_count(self, obj):
        """Display count of associated plans"""
        count = obj.associated_plans.count()
        if count == 0:
            return format_html('<span style="color:gray">No plans</span>')
        return format_html('<span style="color:blue">{} plan(s)</span>', count)
    
    @admin.display(description='Auto-Management')
    def auto_settings_display(self, obj):
        """Display auto-add/remove settings"""
        add_icon = '✓' if obj.auto_add_enabled else '✗'
        remove_icon = '✓' if obj.auto_remove_enabled else '✗'
        return format_html(
            'Add:{} Remove:{}',
            add_icon,
            remove_icon
        )
    
    @admin.display(description='Capacity Status')
    def capacity_indicator(self, obj):
        """Show detailed capacity information"""
        if obj.max_members is None:
            return "Unlimited capacity"
        
        percentage = (obj.member_count / obj.max_members) * 100 if obj.max_members > 0 else 0
        status = "Available" if obj.has_capacity() else "Full"
        color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
        
        return format_html(
            '<div style="color:{}">'
            '<strong>{}</strong><br>'
            'Current: {} / {} members<br>'
            'Usage: {:.1f}%'
            '</div>',
            color, status, obj.member_count, obj.max_members, percentage
        )
    
    @admin.display(description='Permissions Summary')
    def permissions_summary(self, obj):
        """Show bot permissions in this group"""
        perms = []
        if obj.can_send_messages:
            perms.append('Send Messages')
        if obj.can_add_users:
            perms.append('Add Users')
        if obj.can_remove_users:
            perms.append('Remove Users')
        if obj.can_pin_messages:
            perms.append('Pin Messages')
        if obj.can_delete_messages:
            perms.append('Delete Messages')
        if obj.is_admin:
            perms.append('<strong>Admin</strong>')
        
        if not perms:
            return format_html('<span style="color:gray">No permissions</span>')
        
        return format_html('<br>'.join(['✓ ' + p for p in perms]))
    
    # Bulk actions
    
    @admin.action(description='✓ Activate selected groups')
    def activate_groups(self, request, queryset):
        """Bulk activate groups"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} group(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='✗ Deactivate selected groups')
    def deactivate_groups(self, request, queryset):
        """Bulk deactivate groups"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} group(s).',
            messages.WARNING
        )
    
    @admin.action(description='🔄 Enable auto-add for selected groups')
    def enable_auto_add(self, request, queryset):
        """Bulk enable auto-add"""
        updated = queryset.update(auto_add_enabled=True)
        self.message_user(
            request,
            f'Enabled auto-add for {updated} group(s).',
            messages.SUCCESS
        )
    
    @admin.action(description='⏸️ Disable auto-add for selected groups')
    def disable_auto_add(self, request, queryset):
        """Bulk disable auto-add"""
        updated = queryset.update(auto_add_enabled=False)
        self.message_user(
            request,
            f'Disabled auto-add for {updated} group(s).',
            messages.INFO
        )
    
    @admin.action(description='🔄 Reset member counts to 0')
    def reset_member_counts(self, request, queryset):
        """Bulk reset member counts (for testing/cleanup)"""
        from django.utils import timezone
        updated = queryset.update(member_count=0, last_sync_at=timezone.now())
        self.message_user(
            request,
            f'Reset member counts for {updated} group(s).',
            messages.WARNING
        )
    
    # Override save to add custom logic
    
    def save_model(self, request, obj, form, change):
        """Add custom save logic"""
        # If deactivating, log warning
        if change and 'is_active' in form.changed_data and not obj.is_active:
            self.message_user(
                request,
                f'Warning: Deactivated "{obj.name}". Users will not be auto-added to this group.',
                messages.WARNING
            )
        
        # If member_count manually changed, update sync timestamp
        if 'member_count' in form.changed_data:
            from django.utils import timezone
            obj.last_sync_at = timezone.now()
        
        super().save_model(request, obj, form, change)
    
    # Custom queryset optimization
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('associated_plans')


# Admin site customization
admin.site.site_header = "OxiWorld Pricing & Subscription Management"
admin.site.site_title = "OxiWorld Admin"
admin.site.index_title = "Pricing & Subscription Dashboard"