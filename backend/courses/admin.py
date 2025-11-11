from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Course, Lesson, CourseProgress, LessonProgress, CourseCategory, CourseAccess


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'course_count', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'course_type',
        'access_type',  # NEW: Subscription integration
        'plan_count',  # NEW: Phase 2
        'difficulty_level', 
        'status', 
        'estimated_duration',
        'order',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'category',
        'course_type',
        'access_type',  # NEW: Subscription integration
        'difficulty_level', 
        'status', 
        'created_at',
        'updated_at'
    ]
    search_fields = ['title', 'description', 'keywords']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'published_at',
        'plan_list_display', 'subscriber_count_display'  # NEW: Phase 2
    ]
    filter_horizontal = ['required_plans']  # NEW: Better M2M widget
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'slug', 
                'description',
                'short_description',
                'category'
            )
        }),
        ('Course Settings', {
            'fields': (
                'course_type',
                'difficulty_level',
                'status',
                'estimated_duration',
                'order'
            )
        }),
        ('Subscription & Access Settings', {  # Phase 2: Subscription integration
            'fields': (
                'access_type',
                'required_plans',
                'plan_list_display',
                'subscriber_count_display'
            ),
            'description': 'Configure how users can access this course. Use "required_plans" field below to add this course to subscription plans.'
        }),
        ('SEO & Metadata', {
            'fields': (
                'meta_title',
                'meta_description',
                'keywords'
            ),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': (
                'thumbnail',
                'trailer_video_url'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
                'published_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def plan_count(self, obj):
        """Display count of plans that include this course"""
        count = obj.required_plans.count()
        if count > 0:
            return format_html(
                '<span style="background: #007bff; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: #6c757d;">0</span>'
        )
    plan_count.short_description = 'Plans'
    
    def plan_list_display(self, obj):
        """Display list of plans that include this course"""
        from django.urls import reverse
        
        plans = obj.required_plans.filter(is_active=True).order_by('sort_order', 'name')
        
        if not plans.exists():
            return format_html(
                '<em style="color: #6c757d;">This course is not included in any subscription plans yet. '
                'Use the "Required plans" field above to add this course to plans.</em>'
            )
        
        plan_items = []
        for plan in plans:
            url = reverse('admin:subscriptions_subscriptionplan_change', args=[plan.id])
            plan_items.append(
                f'<li><a href="{url}" target="_blank"><strong>{plan.name}</strong></a> '
                f'<span style="color: #6c757d;">({plan.get_billing_period_display()} - '
                f'{plan.get_price_display()})</span></li>'
            )
        
        return format_html(
            '<div style="max-height: 200px; overflow-y: auto; padding: 10px; '
            'background: #e3f2fd; border-left: 4px solid #007bff; border-radius: 4px;">'
            '<strong>📦 Included in {} subscription plan{}:</strong>'
            '<ol style="margin: 10px 0 0 0; padding-left: 20px;">{}</ol>'
            '</div>',
            plans.count(),
            's' if plans.count() != 1 else '',
            format_html(''.join(plan_items))
        )
    plan_list_display.short_description = 'Subscription Plans'
    
    def subscriber_count_display(self, obj):
        """Display count of users with active subscriptions to this course"""
        from subscriptions.models import Subscription
        
        # Count unique users with active subscriptions to plans containing this course
        subscriber_count = Subscription.objects.filter(
            plan__courses=obj,
            status='active'
        ).values('billing_profile__user').distinct().count()
        
        if subscriber_count > 0:
            return format_html(
                '<div style="padding: 10px; background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px;">'
                '<strong style="color: #155724;">✓ {} Active Subscriber{}</strong><br>'
                '<span style="color: #155724; font-size: 12px;">Users can access this course through their subscription plans</span>'
                '</div>',
                subscriber_count,
                's' if subscriber_count != 1 else ''
            )
        
        return format_html(
            '<em style="color: #6c757d;">No active subscribers yet</em>'
        )
    subscriber_count_display.short_description = 'Active Subscribers'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('required_plans')



@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'course',
        'video_source',
        'order',
        'duration',
        'is_preview',
        'created_at'
    ]
    list_filter = [
        'video_source',
        'is_preview',
        'course__title',
        'created_at'
    ]
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order', 'title']
    readonly_fields = ['id', 'youtube_video_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'course',
                'title',
                'slug',
                'description'
            )
        }),
        ('Video Content', {
            'fields': (
                'video_source',
                'video_file',
                'video_url',
                'youtube_video_id'
            )
        }),
        ('Lesson Settings', {
            'fields': (
                'order',
                'duration',
                'is_preview'
            )
        }),
        ('Additional Resources', {
            'fields': (
                'lesson_notes',
                'downloadable_resources'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'id',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'course',
        'started_at',
        'completion_percentage',
        'lessons_completed',
        'completed_at'
    ]
    list_filter = [
        'started_at',
        'completed_at',
        'course__title',
        'certificate_generated'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'course__title'
    ]
    readonly_fields = [
        'id',
        'started_at',
        'completed_at'
    ]
    ordering = ['-started_at']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'lesson',
        'completed',
        'completion_percentage',
        'time_spent',
        'last_watched_at',
        'completed_at'
    ]
    list_filter = [
        'completed',
        'completed_at',
        'lesson__course__title',
        'last_watched_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'lesson__title',
        'lesson__course__title'
    ]
    readonly_fields = [
        'id',
        'last_watched_at',
        'completed_at'
    ]
    ordering = ['-last_watched_at']


@admin.register(CourseAccess)
class CourseAccessAdmin(admin.ModelAdmin):
    """Admin interface for managing course access records"""
    
    list_display = [
        'user_email',
        'course_title',
        'access_granted_by',
        'subscription_plan',
        'access_status',
        'access_granted_at',
        'expiration_display',
    ]
    
    list_filter = [
        'access_granted_by',
        'subscription_plan',
        'access_granted_at',
        ('access_expires_at', admin.EmptyFieldListFilter),
    ]
    
    search_fields = [
        'user__email',
        'user__username',
        'user__first_name',
        'user__last_name',
        'course__title',
        'payment_reference',
    ]
    
    readonly_fields = [
        'id',
        'access_granted_at',
        'updated_at',
        'is_active',
        'access_status_display',
    ]
    
    ordering = ['-access_granted_at']
    
    date_hierarchy = 'access_granted_at'
    
    fieldsets = (
        ('Access Information', {
            'fields': (
                'user',
                'course',
                'access_granted_by',
                'subscription_plan',
            )
        }),
        ('Payment Details', {
            'fields': ('payment_reference',),
            'classes': ('collapse',)
        }),
        ('Access Dates', {
            'fields': (
                'access_granted_at',
                'access_expires_at',
                'updated_at',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'access_status_display',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'grant_admin_access',
        'revoke_access',
        'extend_access_30_days',
        'extend_access_90_days',
    ]
    
    # Custom display methods
    def user_email(self, obj):
        """Display user email with link to user admin"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def course_title(self, obj):
        """Display course title"""
        return obj.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'
    
    def access_status(self, obj):
        """Display access status with color coding"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Expired</span>'
            )
    access_status.short_description = 'Status'
    
    def expiration_display(self, obj):
        """Display expiration date or 'Lifetime'"""
        if obj.access_expires_at:
            if obj.is_active:
                days_remaining = (obj.access_expires_at - timezone.now()).days
                if days_remaining <= 7:
                    return format_html(
                        '<span style="color: orange; font-weight: bold;">{} ({}d left)</span>',
                        obj.access_expires_at.strftime('%Y-%m-%d'),
                        days_remaining
                    )
                return obj.access_expires_at.strftime('%Y-%m-%d')
            return format_html(
                '<span style="color: gray;">{}</span>',
                obj.access_expires_at.strftime('%Y-%m-%d')
            )
        return format_html('<span style="color: green;">Lifetime</span>')
    expiration_display.short_description = 'Expires'
    expiration_display.admin_order_field = 'access_expires_at'
    
    def access_status_display(self, obj):
        """Detailed status display for detail view"""
        status_info = []
        status_info.append(f"Active: {'Yes' if obj.is_active else 'No'}")
        
        if obj.access_expires_at:
            if obj.is_active:
                days_remaining = (obj.access_expires_at - timezone.now()).days
                status_info.append(f"Days remaining: {days_remaining}")
            else:
                days_expired = (timezone.now() - obj.access_expires_at).days
                status_info.append(f"Expired {days_expired} days ago")
        else:
            status_info.append("Access type: Lifetime")
        
        return " | ".join(status_info)
    access_status_display.short_description = 'Detailed Status'
    
    # Custom admin actions
    def grant_admin_access(self, request, queryset):
        """Change access_granted_by to 'admin' for selected records"""
        updated = queryset.update(access_granted_by='admin')
        self.message_user(
            request,
            f'{updated} access record(s) updated to admin-granted.'
        )
    grant_admin_access.short_description = 'Mark as admin-granted access'
    
    def revoke_access(self, request, queryset):
        """Revoke access for selected records"""
        count = 0
        for access in queryset:
            access.revoke_access()
            count += 1
        self.message_user(
            request,
            f'{count} access record(s) revoked successfully.'
        )
    revoke_access.short_description = 'Revoke access immediately'
    
    def extend_access_30_days(self, request, queryset):
        """Extend access by 30 days for selected records"""
        count = 0
        for access in queryset:
            access.extend_access(30)
            count += 1
        self.message_user(
            request,
            f'{count} access record(s) extended by 30 days.'
        )
    extend_access_30_days.short_description = 'Extend access by 30 days'
    
    def extend_access_90_days(self, request, queryset):
        """Extend access by 90 days for selected records"""
        count = 0
        for access in queryset:
            access.extend_access(90)
            count += 1
        self.message_user(
            request,
            f'{count} access record(s) extended by 90 days.'
        )
    extend_access_90_days.short_description = 'Extend access by 90 days'
