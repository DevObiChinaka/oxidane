from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OAuthProvider, EmailTemplate, UserPreferences

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_email_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'email_verification_expires', 'password_reset_expires')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Email Verification', {'fields': ('is_email_verified', 'email_verification_token', 'email_verification_expires')}),
        ('Password Reset', {'fields': ('password_reset_token', 'password_reset_expires')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

@admin.register(OAuthProvider)
class OAuthProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_user_id', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('user__email', 'provider_user_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'provider', 'provider_user_id')}),
        ('Important dates', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'status', 'is_default', 'created_at', 'updated_at')
    list_filter = ('template_type', 'status', 'is_default', 'created_at')
    search_fields = ('name', 'template_type', 'description', 'subject_template')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'description', 'status', 'is_default')
        }),
        ('Email Content', {
            'fields': ('subject_template', 'html_content', 'text_content'),
            'classes': ('wide',)
        }),
        ('Variables & Metadata', {
            'fields': ('available_variables',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ('status', 'is_default')
    
    actions = ['activate_templates', 'deactivate_templates', 'set_as_default']
    
    def activate_templates(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} template(s) activated successfully.')
    activate_templates.short_description = 'Activate selected templates'
    
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} template(s) deactivated successfully.')
    deactivate_templates.short_description = 'Deactivate selected templates'
    
    def set_as_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, 'You can only set one template as default at a time.', level='error')
            return
        
        template = queryset.first()
        # Remove default from other templates of same type
        EmailTemplate.objects.filter(template_type=template.template_type).update(is_default=False)
        # Set selected as default
        template.is_default = True
        template.save()
        self.message_user(request, f'"{template.name}" is now the default template for {template.template_type}.')
    set_as_default.short_description = 'Set as default template'


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_login', 'course_updates', 'subscription_renewal', 'signal_alerts', 'promotional_emails', 'updated_at')
    list_filter = ('email_login', 'course_updates', 'subscription_renewal', 'signal_alerts', 'promotional_emails')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Notification Preferences', {
            'fields': ('email_login', 'course_updates', 'subscription_renewal', 'signal_alerts', 'promotional_emails'),
            'description': 'Configure which email notifications the user receives'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ('email_login', 'course_updates', 'subscription_renewal', 'signal_alerts', 'promotional_emails')
