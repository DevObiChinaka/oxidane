from django.urls import path
from . import admin_views

app_name = 'settings_app'

urlpatterns = [
    # Platform Settings
    path('settings/', admin_views.get_all_settings, name='get_all_settings'),
    path('settings/by-category/', admin_views.get_settings_by_category, name='get_settings_by_category'),
    path('settings/<str:key>/', admin_views.get_setting, name='get_setting'),
    path('settings/<str:key>/update/', admin_views.update_setting, name='update_setting'),
    path('settings/<str:key>/history/', admin_views.get_setting_history, name='get_setting_history'),
    path('settings/actions/bulk-update/', admin_views.bulk_update_settings, name='bulk_update_settings'),
    path('settings/actions/validate/', admin_views.validate_setting, name='validate_setting'),
    path('settings/actions/test-email/', admin_views.test_email_configuration, name='test_email_configuration'),
    path('settings/actions/test-bot/', admin_views.test_bot_connection, name='test_bot_connection'),
    
    # Change Logs
    path('change-logs/', admin_views.get_change_logs, name='get_change_logs'),
    
    # Telegram Groups
    path('telegram-groups/', admin_views.get_telegram_groups, name='get_telegram_groups'),
    path('telegram-groups/create/', admin_views.create_telegram_group, name='create_telegram_group'),
    path('telegram-groups/<int:group_id>/', admin_views.get_telegram_group, name='get_telegram_group'),
    path('telegram-groups/<int:group_id>/update/', admin_views.update_telegram_group, name='update_telegram_group'),
    path('telegram-groups/<int:group_id>/delete/', admin_views.delete_telegram_group, name='delete_telegram_group'),
    path('telegram-groups/<int:group_id>/sync-members/', admin_views.sync_group_members, name='sync_group_members'),
    path('telegram-groups/actions/bulk-update/', admin_views.bulk_update_telegram_groups, name='bulk_update_telegram_groups'),
    
    # Backups
    path('backups/', admin_views.get_backups, name='get_backups'),
    path('backups/create/', admin_views.create_backup, name='create_backup'),
    path('backups/<int:backup_id>/restore/', admin_views.restore_backup, name='restore_backup'),
    path('backups/<int:backup_id>/delete/', admin_views.delete_backup, name='delete_backup'),
    
    # Statistics
    path('stats/', admin_views.get_settings_stats, name='get_settings_stats'),
]
