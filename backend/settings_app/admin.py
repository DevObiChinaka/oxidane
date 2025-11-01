from django.contrib import admin
from .models import PlatformSetting, SettingChangeLog, TelegramGroup, SettingsBackup


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ['label', 'key', 'category', 'data_type', 'is_encrypted', 'is_active', 'updated_at']
    list_filter = ['category', 'data_type', 'is_encrypted', 'is_sensitive', 'is_active']
    search_fields = ['key', 'label', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_modified_by']
    ordering = ['category', 'key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'key', 'label', 'value', 'data_type', 'description', 'default_value')
        }),
        ('Security', {
            'fields': ('is_encrypted', 'is_sensitive')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_restart')
        }),
        ('Validation', {
            'fields': ('validation_rules',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_modified_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SettingChangeLog)
class SettingChangeLogAdmin(admin.ModelAdmin):
    list_display = ['setting', 'changed_by', 'changed_at', 'ip_address']
    list_filter = ['changed_at', 'changed_by']
    search_fields = ['setting__key', 'change_reason', 'ip_address']
    readonly_fields = ['setting', 'old_value', 'new_value', 'change_reason', 
                      'changed_by', 'changed_at', 'ip_address', 'user_agent']
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'group_key', 'access_level', 'is_active', 'member_count', 'sort_order']
    list_filter = ['access_level', 'is_active', 'auto_add_users', 'auto_remove_expired']
    search_fields = ['name', 'group_key', 'chat_id']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'chat_id', 'group_key', 'description')
        }),
        ('Access & Status', {
            'fields': ('access_level', 'is_active', 'sort_order')
        }),
        ('Automation', {
            'fields': ('auto_add_users', 'auto_remove_expired', 'welcome_message_enabled', 'welcome_message_template')
        }),
        ('Statistics', {
            'fields': ('member_count', 'last_sync_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['member_count', 'last_sync_at', 'created_at', 'updated_at']


@admin.register(SettingsBackup)
class SettingsBackupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'restored_at']
    list_filter = ['restored_at']
    search_fields = ['name', 'description']
    readonly_fields = ['settings_data', 'telegram_groups_data', 'created_by', 'created_at', 'restored_at', 'restored_by']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Backup Information', {
            'fields': ('name', 'description', 'created_by', 'created_at')
        }),
        ('Restore Information', {
            'fields': ('restored_at', 'restored_by'),
            'classes': ('collapse',)
        }),
        ('Snapshot Data', {
            'fields': ('settings_data', 'telegram_groups_data'),
            'classes': ('collapse',)
        }),
    )
    
    def has_change_permission(self, request, obj=None):
        return False
