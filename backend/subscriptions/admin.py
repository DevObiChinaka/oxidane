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
    SubscriptionPlan, Subscription, BillingProfile,
    Coupon, ReferralCode, Referral, ReferralCredit,
    PaymentConfiguration, EmailConfiguration, TelegramConfiguration, TelegramGroup,
    ExchangeRate
)

# ============================================================================
# DEPRECATED ADMIN CLASSES REMOVED (Phase 0.5 Cleanup - November 2, 2025)
# ============================================================================
# The following admin classes have been removed along with their models:
# - PricingPlanAdmin (for PricingPlan model)
# - SignalSubscriptionAdmin (for SignalSubscription model)
# - TelegramGroupManagementAdmin (for TelegramGroupManagement model)
# These models were replaced by:
# - PricingPlan → SubscriptionPlan
# - SignalSubscription → Subscription
# - TelegramGroupManagement → TelegramGroup
# ============================================================================


# ============================================================================
# SUBSCRIPTION PLAN & SUBSCRIPTION ADMIN (Phase 2)
# ============================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Enhanced admin interface for subscription plans with course management"""
    list_display = [
        'name_display',
        'billing_period',
        'price_display',
        'course_count',
        'subscriber_count',
        'trial_display',
        'status_display',
        'sort_order',
        'created_at'
    ]
    list_filter = [
        'billing_period',
        'is_active',
        'is_featured',
        'created_at'
    ]
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'base_price']
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'course_list_display', 'subscriber_list_display',
        'monthly_equivalent_display'
    ]
    
    # Phase 2: M2M widget for features (courses managed from Course admin)
    filter_horizontal = ['features']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'description'
            )
        }),
        ('Pricing', {
            'fields': (
                'base_price',
                'billing_period',
                'monthly_equivalent_display',
            ),
            'description': 'Base price is in USD and auto-converted to other currencies. Use coupon codes (WELCOME50) instead of trials for promotions.'
        }),
        ('Features & Courses', {
            'fields': (
                'features',
                'course_list_display'
            ),
            'description': 'Select features included in this plan. Courses are managed from the Course admin page.'
        }),
        ('Plan Settings', {
            'fields': (
                'is_active',
                'is_featured',
                'sort_order',
                'limits'
            )
        }),
        ('Integration', {
            'fields': ('paystack_plan_code',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('subscriber_list_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def name_display(self, obj):
        """Display plan name with featured badge"""
        if obj.is_featured:
            return format_html(
                '<strong>{}</strong> <span style="background: #ffd700; color: #000; '
                'padding: 2px 6px; border-radius: 3px; font-size: 10px;">★ FEATURED</span>',
                obj.name
            )
        return obj.name
    name_display.short_description = 'Plan Name'
    name_display.admin_order_field = 'name'
    
    def price_display(self, obj):
        """Display price with billing period"""
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">{}</strong>',
            obj.get_price_display()
        )
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'base_price'
    
    def monthly_equivalent_display(self, obj):
        """Show monthly equivalent for comparison"""
        if obj.billing_period == 'monthly':
            return 'N/A (already monthly)'
        
        monthly_eq = obj.get_monthly_equivalent()
        savings_percent = 0
        
        if obj.billing_period == 'yearly':
            monthly_single = obj.base_price / 12
            savings_percent = ((monthly_eq - monthly_single) / monthly_eq * 100) if monthly_eq > 0 else 0
        
        return format_html(
            '<strong>${:.2f}/mo</strong> equivalent{}',
            monthly_eq,
            f' (saves {savings_percent:.0f}%)' if savings_percent > 0 else ''
        )
    monthly_equivalent_display.short_description = 'Monthly Equivalent'
    
    def course_count(self, obj):
        """Display count of courses in plan with link"""
        count = obj.courses.count()
        if count > 0:
            return format_html(
                '<span style="background: #007bff; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: #6c757d;">0</span>'
        )
    course_count.short_description = 'Courses'
    
    def course_list_display(self, obj):
        """Display list of courses in this plan"""
        courses = obj.courses.filter(status='published').order_by('order', 'title')
        
        if not courses.exists():
            return format_html(
                '<em style="color: #6c757d;">No courses assigned to this plan yet. '
                'Use the "Courses" field above to add courses.</em>'
            )
        
        course_items = []
        for course in courses:
            url = reverse('admin:courses_course_change', args=[course.id])
            course_items.append(
                f'<li><a href="{url}" target="_blank">{course.title}</a> '
                f'<span style="color: #6c757d;">({course.get_difficulty_level_display()})</span></li>'
            )
        
        return format_html(
            '<div style="max-height: 200px; overflow-y: auto; padding: 10px; '
            'background: #f8f9fa; border-radius: 4px;">'
            '<strong>Courses in this plan ({}):</strong>'
            '<ol style="margin: 10px 0 0 0; padding-left: 20px;">{}</ol>'
            '</div>',
            courses.count(),
            format_html(''.join(course_items))
        )
    course_list_display.short_description = 'Courses in Plan'
    
    def subscriber_count(self, obj):
        """Display active subscriber count"""
        count = Subscription.objects.filter(
            plan=obj,
            status='active'
        ).count()
        
        if count > 0:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: #6c757d;">0</span>')
    subscriber_count.short_description = 'Active Subscribers'
    
    def subscriber_list_display(self, obj):
        """Display list of active subscribers"""
        subscriptions = Subscription.objects.filter(
            plan=obj,
            status='active'
        ).select_related('billing_profile__user')[:10]
        
        if not subscriptions.exists():
            return format_html('<em style="color: #6c757d;">No active subscribers</em>')
        
        total_count = Subscription.objects.filter(plan=obj, status='active').count()
        
        sub_items = []
        for sub in subscriptions:
            user_url = reverse('admin:accounts_customuser_change', args=[sub.billing_profile.user.id])
            sub_items.append(
                f'<li><a href="{user_url}" target="_blank">{sub.billing_profile.user.email}</a> '
                f'<span style="color: #6c757d;">(ends: {sub.end_date.strftime("%Y-%m-%d")})</span></li>'
            )
        
        more_text = f'<li><em>... and {total_count - 10} more</em></li>' if total_count > 10 else ''
        
        return format_html(
            '<div style="max-height: 250px; overflow-y: auto; padding: 10px; '
            'background: #f8f9fa; border-radius: 4px;">'
            '<strong>Active Subscribers ({}):</strong>'
            '<ol style="margin: 10px 0 0 0; padding-left: 20px;">{}{}</ol>'
            '</div>',
            total_count,
            format_html(''.join(sub_items)),
            format_html(more_text)
        )
    subscriber_list_display.short_description = 'Active Subscribers'
    
    def trial_display(self, obj):
        """Trial status (trials disabled platform-wide)"""
        return format_html('<span style="color: #28a745; font-weight: 500;">✓ Trials Disabled</span>')
    trial_display.short_description = 'Trial Status'
    
    def status_display(self, obj):
        """Display plan status"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">● Inactive</span>'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_active'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('courses', 'features')
    
    actions = ['activate_plans', 'deactivate_plans', 'mark_as_featured', 'unmark_as_featured']
    
    def activate_plans(self, request, queryset):
        """Bulk activate plans"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Successfully activated {updated} plan(s).')
    activate_plans.short_description = "Activate selected plans"
    
    def deactivate_plans(self, request, queryset):
        """Bulk deactivate plans"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Successfully deactivated {updated} plan(s).')
    deactivate_plans.short_description = "Deactivate selected plans"
    
    def mark_as_featured(self, request, queryset):
        """Mark plans as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'Successfully marked {updated} plan(s) as featured.')
    mark_as_featured.short_description = "Mark as featured"
    
    def unmark_as_featured(self, request, queryset):
        """Unmark plans as featured"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'Successfully unmarked {updated} plan(s) as featured.')
    unmark_as_featured.short_description = "Remove featured status"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for user subscriptions"""
    list_display = [
        'id_short',
        'user_display',
        'plan_display',
        'status_badge',
        'period_display',
        'amount_display',
        'auto_renew_display',
        'created_at'
    ]
    list_filter = [
        'status',
        'plan',
        'auto_renew',
        'currency',
        'created_at',
        'start_date',
        'end_date'
    ]
    search_fields = [
        'id',
        'billing_profile__user__username',
        'billing_profile__user__email',
        'plan__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'subscription_duration', 'time_remaining'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': (
                'id',
                'billing_profile',
                'plan',
                'status'
            )
        }),
        ('Period & Billing', {
            'fields': (
                'start_date',
                'end_date',
                'subscription_duration',
                'time_remaining',
                'amount_paid',
                'currency',
                'payment_method'
            )
        }),
        ('Auto-Renewal', {
            'fields': (
                'auto_renew',
                'next_billing_date'
            )
        }),
        ('Cancellation', {
            'fields': (
                'cancelled_at',
                'cancellation_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return format_html(
            '<span style="font-family: monospace; font-size: 11px;">{}</span>',
            str(obj.id)[:8]
        )
    id_short.short_description = 'ID'
    
    def user_display(self, obj):
        """Display user with link"""
        user_url = reverse('admin:accounts_customuser_change', args=[obj.billing_profile.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            user_url,
            obj.billing_profile.user.email
        )
    user_display.short_description = 'User'
    
    def plan_display(self, obj):
        """Display plan with link"""
        plan_url = reverse('admin:subscriptions_subscriptionplan_change', args=[obj.plan.id])
        return format_html(
            '<a href="{}">{}</a>',
            plan_url,
            obj.plan.name
        )
    plan_display.short_description = 'Plan'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'active': '#28a745',
            'cancelled': '#dc3545',
            'expired': '#6c757d',
            'pending': '#ffc107',
            'past_due': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-weight: bold; text-transform: uppercase; '
            'font-size: 10px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def period_display(self, obj):
        """Display subscription period"""
        return format_html(
            '<span style="font-size: 12px;">{}<br><span style="color: #6c757d;">to</span><br>{}</span>',
            obj.start_date.strftime('%Y-%m-%d'),
            obj.end_date.strftime('%Y-%m-%d')
        )
    period_display.short_description = 'Period'
    
    def amount_display(self, obj):
        """Display amount paid"""
        return format_html(
            '<strong style="color: #28a745;">{} {}</strong>',
            obj.currency,
            obj.amount_paid
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount_paid'
    
    def auto_renew_display(self, obj):
        """Display auto-renew status"""
        if obj.auto_renew:
            return format_html(
                '<span style="color: #28a745;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">✗ No</span>'
        )
    auto_renew_display.short_description = 'Auto-Renew'
    auto_renew_display.admin_order_field = 'auto_renew'
    
    def subscription_duration(self, obj):
        """Calculate subscription duration"""
        if obj.start_date and obj.end_date:
            duration = obj.end_date - obj.start_date
            days = duration.days
            
            if days >= 365:
                years = days / 365.25
                return f"{years:.1f} years ({days} days)"
            elif days >= 30:
                months = days / 30.44
                return f"{months:.1f} months ({days} days)"
            else:
                return f"{days} days"
        return 'N/A'
    subscription_duration.short_description = 'Duration'
    
    def time_remaining(self, obj):
        """Calculate time remaining"""
        if obj.status == 'active' and obj.end_date:
            now = timezone.now()
            if obj.end_date > now:
                remaining = obj.end_date - now
                days = remaining.days
                
                if days > 30:
                    return format_html(
                        '<span style="color: #28a745;">{} days remaining</span>',
                        days
                    )
                elif days > 7:
                    return format_html(
                        '<span style="color: #ffc107;">{} days remaining</span>',
                        days
                    )
                else:
                    return format_html(
                        '<span style="color: #dc3545;">{} days remaining ⚠</span>',
                        days
                    )
            else:
                return format_html(
                    '<span style="color: #dc3545;">Expired</span>'
                )
        return 'N/A'
    time_remaining.short_description = 'Time Remaining'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('billing_profile__user', 'plan', 'payment_method')
    
    actions = ['cancel_subscriptions', 'reactivate_subscriptions']
    
    def cancel_subscriptions(self, request, queryset):
        """Bulk cancel subscriptions"""
        active_subs = queryset.filter(status='active')
        updated = active_subs.update(
            status='cancelled',
            cancelled_at=timezone.now(),
            auto_renew=False
        )
        self.message_user(
            request,
            f'Successfully cancelled {updated} subscription(s).',
            messages.WARNING
        )
    cancel_subscriptions.short_description = "Cancel selected subscriptions"
    
    def reactivate_subscriptions(self, request, queryset):
        """Reactivate cancelled subscriptions"""
        cancelled_subs = queryset.filter(status='cancelled')
        count = 0
        for sub in cancelled_subs:
            if sub.end_date > timezone.now():
                sub.status = 'active'
                sub.cancelled_at = None
                sub.save()
                count += 1
        
        self.message_user(
            request,
            f'Successfully reactivated {count} subscription(s).',
            messages.SUCCESS
        )
    reactivate_subscriptions.short_description = "Reactivate cancelled subscriptions"


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


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for email/SMTP configuration (singleton).
    Manages SMTP server settings, credentials, and connection testing.
    Phase 0.5, Task 0.5.9
    """
    list_display = [
        'smtp_host_display', 'status_display', 'connection_display',
        'from_email_display'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'masked_password_display',
        'connection_status_display', 'last_test_at'
    ]
    fieldsets = (
        ('SMTP Server Settings', {
            'fields': (
                'id', 'smtp_host', 'smtp_port', 'use_tls', 'use_ssl'
            ),
            'description': 'Configure SMTP server connection'
        }),
        ('Authentication', {
            'fields': (
                'smtp_username', 'smtp_password', 'masked_password_display'
            ),
            'description': 'SMTP login credentials'
        }),
        ('Sender Information', {
            'fields': (
                'from_email', 'from_name'
            ),
            'description': 'Default sender details for outgoing emails'
        }),
        ('Status', {
            'fields': (
                'is_enabled', 'connection_status_display', 'last_test_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def smtp_host_display(self, obj):
        """Display SMTP host with port"""
        if obj.smtp_host:
            protocol = 'SSL' if obj.use_ssl else 'TLS'
            return format_html(
                '<strong>{}</strong>:{} ({})',
                obj.smtp_host,
                obj.smtp_port,
                protocol
            )
        return format_html('<em style="color: #6c757d;">(not configured)</em>')
    smtp_host_display.short_description = 'SMTP Server'
    
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
        elif not obj.is_configured():
            return format_html('<span style="color: #ffc107;">⚠ Not Configured</span>')
        elif obj.is_connected:
            return format_html('<span style="color: #28a745;">● Connected</span>')
        else:
            return format_html('<span style="color: #dc3545;">○ Disconnected</span>')
    connection_display.short_description = 'Connection'
    
    def from_email_display(self, obj):
        """Display from email"""
        if obj.from_email:
            return format_html(
                '<strong>{}</strong> &lt;{}&gt;',
                obj.from_name,
                obj.from_email
            )
        return format_html('<em style="color: #dc3545;">(not set)</em>')
    from_email_display.short_description = 'From Address'
    
    def masked_password_display(self, obj):
        """Display masked password for security"""
        masked = obj.get_masked_password()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code style="color: #dc3545;">{}</code>', masked)
    masked_password_display.short_description = 'Password (Masked)'
    
    def connection_status_display(self, obj):
        """Display detailed connection status"""
        if not obj.is_enabled:
            return format_html('<div style="color: #6c757d;">⚫ Email system is disabled</div>')
        
        if not obj.is_configured():
            return format_html(
                '<div style="color: #ffc107;"><strong>⚠ Not Configured</strong></div>'
                '<div style="font-size: 11px; color: #856404;">Please configure SMTP settings</div>'
            )
        
        if obj.is_connected:
            return format_html(
                '<div style="color: #28a745;"><strong>✓ Connected</strong></div>'
                '<div style="font-size: 11px; color: #6c757d;">SMTP connection successful</div>'
            )
        else:
            error_msg = obj.connection_error or 'Not tested yet'
            return format_html(
                '<div style="color: #dc3545;"><strong>✗ Disconnected</strong></div>'
                '<div style="font-size: 11px; color: #dc3545;">{}</div>',
                error_msg[:100]
            )
    connection_status_display.short_description = 'Connection Status'
    
    def has_add_permission(self, request):
        """Prevent adding more than one configuration (singleton)"""
        from .models import EmailConfiguration
        if EmailConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Allow delete to reset configuration if needed (superuser only)"""
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Override to handle credential changes"""
        if 'smtp_password' in form.changed_data and obj.smtp_password:
            # Password changed, mark as disconnected for re-verification
            obj.is_connected = False
            obj.connection_error = 'Password changed - please test connection'
        super().save_model(request, obj, form, change)


@admin.register(PaymentConfiguration)
class PaymentConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for payment gateway configuration (singleton).
    Manages Paystack and Stripe API keys, webhook settings, and provider selection.
    Phase 0.5, Task 0.5.8
    """
    list_display = [
        'primary_provider_display', 'mode_display', 'paystack_status',
        'stripe_status', 'currencies_display'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'masked_paystack_public', 'masked_paystack_secret',
        'masked_stripe_publishable', 'masked_stripe_secret'
    ]
    fieldsets = (
        ('Primary Settings', {
            'fields': (
                'id', 'primary_provider', 'is_test_mode', 'supported_currencies'
            ),
            'description': 'Core payment configuration and currency support'
        }),
        ('Paystack Configuration', {
            'fields': (
                'paystack_enabled',
                'paystack_public_key', 'masked_paystack_public',
                'paystack_secret_key', 'masked_paystack_secret',
                'paystack_webhook_secret', 'paystack_webhook_url'
            ),
            'description': 'Paystack payment gateway settings (Nigerian market)'
        }),
        ('Stripe Configuration', {
            'fields': (
                'stripe_enabled',
                'stripe_publishable_key', 'masked_stripe_publishable',
                'stripe_secret_key', 'masked_stripe_secret',
                'stripe_webhook_secret', 'stripe_webhook_url'
            ),
            'description': 'Stripe payment gateway settings (International)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def primary_provider_display(self, obj):
        """Display primary provider with icon"""
        icons = {
            'paystack': '🇳🇬',
            'stripe': '🌐'
        }
        icon = icons.get(obj.primary_provider, '❓')
        return format_html(
            '{} <strong>{}</strong>',
            icon,
            obj.get_primary_provider_display()
        )
    primary_provider_display.short_description = 'Primary Provider'
    
    def mode_display(self, obj):
        """Display test/live mode"""
        if obj.is_test_mode:
            return format_html(
                '<span style="background: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 3px;">'
                '🧪 Test Mode</span>'
            )
        return format_html(
            '<span style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 3px;">'
            '✓ Live Mode</span>'
        )
    mode_display.short_description = 'Mode'
    
    def paystack_status(self, obj):
        """Display Paystack configuration status"""
        if not obj.paystack_enabled:
            return format_html('<span style="color: #6c757d;">○ Disabled</span>')
        elif obj.is_paystack_configured():
            return format_html('<span style="color: #28a745;">● Configured</span>')
        return format_html('<span style="color: #dc3545;">○ Not Configured</span>')
    paystack_status.short_description = 'Paystack'
    
    def stripe_status(self, obj):
        """Display Stripe configuration status"""
        if not obj.stripe_enabled:
            return format_html('<span style="color: #6c757d;">○ Disabled</span>')
        elif obj.is_stripe_configured():
            return format_html('<span style="color: #28a745;">● Configured</span>')
        return format_html('<span style="color: #dc3545;">○ Not Configured</span>')
    stripe_status.short_description = 'Stripe'
    
    def currencies_display(self, obj):
        """Display supported currencies"""
        if not obj.supported_currencies:
            return format_html('<em style="color: #dc3545;">(none)</em>')
        currencies_str = ', '.join(obj.supported_currencies[:3])
        if len(obj.supported_currencies) > 3:
            currencies_str += f' +{len(obj.supported_currencies) - 3} more'
        return format_html('<code>{}</code>', currencies_str)
    currencies_display.short_description = 'Currencies'
    
    def masked_paystack_public(self, obj):
        """Display masked Paystack public key"""
        masked = obj.get_masked_paystack_public_key()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code>{}</code>', masked)
    masked_paystack_public.short_description = 'Public Key (Masked)'
    
    def masked_paystack_secret(self, obj):
        """Display masked Paystack secret key"""
        masked = obj.get_masked_paystack_secret_key()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code style="color: #dc3545;">{}</code>', masked)
    masked_paystack_secret.short_description = 'Secret Key (Masked)'
    
    def masked_stripe_publishable(self, obj):
        """Display masked Stripe publishable key"""
        masked = obj.get_masked_stripe_publishable_key()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code>{}</code>', masked)
    masked_stripe_publishable.short_description = 'Publishable Key (Masked)'
    
    def masked_stripe_secret(self, obj):
        """Display masked Stripe secret key"""
        masked = obj.get_masked_stripe_secret_key()
        if masked == '(not set)':
            return format_html('<em style="color: #dc3545;">{}</em>', masked)
        return format_html('<code style="color: #dc3545;">{}</code>', masked)
    masked_stripe_secret.short_description = 'Secret Key (Masked)'
    
    def has_add_permission(self, request):
        """Prevent adding more than one configuration (singleton)"""
        from .models import PaymentConfiguration
        if PaymentConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Allow delete to reset configuration if needed (superuser only)"""
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Override to handle key changes"""
        # Could add validation or notifications here
        super().save_model(request, obj, form, change)


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


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """
    Admin interface for currency exchange rates.
    Manages rates for multi-currency pricing with auto-conversion.
    Phase 0.5, Task 0.5.10
    """
    list_display = [
        'currency_pair_display', 'rate_display', 'last_updated_display',
        'staleness_display', 'conversion_calculator'
    ]
    list_filter = ['base_currency', 'target_currency', 'last_updated']
    search_fields = ['base_currency', 'target_currency']
    readonly_fields = [
        'id', 'created_at', 'last_updated',
        'reverse_rate_display', 'staleness_info'
    ]
    fieldsets = (
        ('Currency Pair', {
            'fields': ('base_currency', 'target_currency'),
            'description': 'Currency codes (e.g., USD, NGN, GBP, EUR)'
        }),
        ('Exchange Rate', {
            'fields': ('rate', 'reverse_rate_display'),
            'description': 'Rate from base to target currency'
        }),
        ('Status', {
            'fields': ('last_updated', 'staleness_info'),
            'description': 'Rate freshness and update information'
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['base_currency', 'target_currency']
    
    # Custom actions
    actions = ['mark_as_stale', 'refresh_rates', 'delete_selected']
    
    def currency_pair_display(self, obj):
        """Display currency pair with flag emojis"""
        # Basic flag mapping (extend as needed)
        flags = {
            'USD': '🇺🇸', 'NGN': '🇳🇬', 'GBP': '🇬🇧', 'EUR': '🇪🇺',
            'CAD': '🇨🇦', 'JPY': '🇯🇵', 'CNY': '🇨🇳', 'INR': '🇮🇳'
        }
        base_flag = flags.get(obj.base_currency, '🌐')
        target_flag = flags.get(obj.target_currency, '🌐')
        
        return format_html(
            '{} <strong>{}</strong> → {} <strong>{}</strong>',
            base_flag, obj.base_currency,
            target_flag, obj.target_currency
        )
    currency_pair_display.short_description = 'Currency Pair'
    
    def rate_display(self, obj):
        """Display rate with formatting"""
        # Use different precision based on rate magnitude
        if obj.rate >= 100:
            formatted_rate = f'{obj.rate:,.2f}'
        elif obj.rate >= 1:
            formatted_rate = f'{obj.rate:.4f}'
        else:
            formatted_rate = f'{obj.rate:.6f}'
        
        return format_html(
            '<span style="font-family: monospace; font-weight: bold;">{}</span>',
            formatted_rate
        )
    rate_display.short_description = 'Rate'
    
    def last_updated_display(self, obj):
        """Display last update time in human-readable format"""
        from django.utils.timesince import timesince
        time_ago = timesince(obj.last_updated)
        
        return format_html(
            '<span title="{}">{} ago</span>',
            obj.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
            time_ago
        )
    last_updated_display.short_description = 'Last Updated'
    
    def staleness_display(self, obj):
        """Display staleness indicator"""
        if obj.is_stale(hours=24):
            hours_stale = (timezone.now() - obj.last_updated).total_seconds() / 3600
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;" '
                'title="Rate is {:.1f} hours old">⚠ Stale</span>',
                hours_stale
            )
        elif obj.is_stale(hours=12):
            return format_html(
                '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px;">'
                '⚡ Aging</span>'
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">'
            '✓ Fresh</span>'
        )
    staleness_display.short_description = 'Status'
    
    def conversion_calculator(self, obj):
        """Quick conversion calculator link"""
        return format_html(
            '<a href="#" onclick="alert(\'1 {} = {} {}\\n1 {} = {:.6f} {}\'); return false;" '
            'style="color: #007bff; text-decoration: none;">📊 Calculate</a>',
            obj.base_currency, obj.rate, obj.target_currency,
            obj.target_currency, 1/obj.rate, obj.base_currency
        )
    conversion_calculator.short_description = 'Calculator'
    
    def reverse_rate_display(self, obj):
        """Display reverse rate"""
        if obj.rate > 0:
            reverse = 1 / obj.rate
            if reverse >= 100:
                formatted = f'{reverse:,.2f}'
            elif reverse >= 1:
                formatted = f'{reverse:.4f}'
            else:
                formatted = f'{reverse:.6f}'
            
            return format_html(
                '1 {} = <strong>{}</strong> {} (reverse)',
                obj.target_currency, formatted, obj.base_currency
            )
        return 'N/A'
    reverse_rate_display.short_description = 'Reverse Rate'
    
    def staleness_info(self, obj):
        """Detailed staleness information"""
        from django.utils.timesince import timesince
        hours_old = (timezone.now() - obj.last_updated).total_seconds() / 3600
        
        if obj.is_stale(hours=24):
            color = '#dc3545'
            status = 'STALE - needs update'
        elif obj.is_stale(hours=12):
            color = '#ffc107'
            status = 'AGING - update soon'
        else:
            color = '#28a745'
            status = 'FRESH'
        
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-left: 4px solid {};">'
            '<strong>{}</strong><br>'
            'Last updated: {} ago ({:.1f} hours)<br>'
            'Updated at: {}'
            '</div>',
            color, status,
            timesince(obj.last_updated), hours_old,
            obj.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        )
    staleness_info.short_description = 'Staleness Information'
    
    # Custom actions
    
    def mark_as_stale(self, request, queryset):
        """Mark selected rates as stale (for testing)"""
        from datetime import timedelta
        from django.utils import timezone
        
        old_time = timezone.now() - timedelta(hours=25)
        updated = 0
        
        for rate in queryset:
            # Use update() to bypass auto_now
            ExchangeRate.objects.filter(id=rate.id).update(last_updated=old_time)
            updated += 1
        
        self.message_user(
            request,
            f'Marked {updated} rate(s) as stale.',
            messages.SUCCESS
        )
    mark_as_stale.short_description = 'Mark as stale (for testing)'
    
    def refresh_rates(self, request, queryset):
        """Refresh selected rates (placeholder for future API integration)"""
        self.message_user(
            request,
            'Rate refresh functionality will be implemented in Phase 0.5 infrastructure tasks.',
            messages.INFO
        )
    refresh_rates.short_description = 'Refresh rates (placeholder)'
    
    # Permissions
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete rates"""
        return request.user.is_superuser
    
    # Save override
    
    def save_model(self, request, obj, form, change):
        """Add logging for rate changes"""
        if change and 'rate' in form.changed_data:
            old_rate = ExchangeRate.objects.get(id=obj.id).rate
            self.message_user(
                request,
                f'Rate updated: {old_rate} → {obj.rate} ({obj.base_currency}/{obj.target_currency})',
                messages.SUCCESS
            )
        super().save_model(request, obj, form, change)


# Admin site customization
admin.site.site_header = "OxiWorld Pricing & Subscription Management"
admin.site.site_title = "OxiWorld Admin"
admin.site.index_title = "Pricing & Subscription Dashboard"