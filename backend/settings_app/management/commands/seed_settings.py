from django.core.management.base import BaseCommand
from django.conf import settings as django_settings
from settings_app.models import PlatformSetting, TelegramGroup


class Command(BaseCommand):
    help = 'Seeds default platform settings'

    def handle(self, *args, **options):
        self.stdout.write('Seeding default platform settings...')
        
        settings_data = [
            # Email Settings
            {'category': 'email', 'key': 'email_host', 'label': 'SMTP Host', 'value': getattr(django_settings, 'EMAIL_HOST', 'smtp.gmail.com'), 'data_type': 'string', 'description': 'SMTP host for sending emails', 'is_encrypted': False, 'is_sensitive': True, 'is_active': True},
            {'category': 'email', 'key': 'email_port', 'label': 'SMTP Port', 'value': getattr(django_settings, 'EMAIL_PORT', 465), 'data_type': 'integer', 'description': 'SMTP port', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'email', 'key': 'email_use_ssl', 'label': 'Use SSL', 'value': getattr(django_settings, 'EMAIL_USE_SSL', True), 'data_type': 'boolean', 'description': 'Use SSL for email connection', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'email', 'key': 'email_host_user', 'label': 'Email Username', 'value': getattr(django_settings, 'EMAIL_HOST_USER', ''), 'data_type': 'email', 'description': 'Email account username', 'is_encrypted': True, 'is_sensitive': True, 'is_active': True},
            {'category': 'email', 'key': 'email_host_password', 'label': 'Email Password', 'value': '', 'data_type': 'string', 'description': 'Email account password (encrypted)', 'is_encrypted': True, 'is_sensitive': True, 'is_active': True},
            {'category': 'email', 'key': 'default_from_email', 'label': 'From Email', 'value': getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'OxiWorld <noreply@oxiworld.com>'), 'data_type': 'email', 'description': 'Default FROM email address', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'email', 'key': 'email_timeout', 'label': 'Connection Timeout', 'value': getattr(django_settings, 'EMAIL_TIMEOUT', 30), 'data_type': 'integer', 'description': 'Email connection timeout (seconds)', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            
            # Telegram Settings
            {'category': 'telegram', 'key': 'telegram_bot_token', 'label': 'Bot Token', 'value': getattr(django_settings, 'TELEGRAM_BOT_TOKEN', ''), 'data_type': 'string', 'description': 'Telegram Bot API token', 'is_encrypted': True, 'is_sensitive': True, 'is_active': True},
            {'category': 'telegram', 'key': 'telegram_bot_enabled', 'label': 'Bot Enabled', 'value': True, 'data_type': 'boolean', 'description': 'Enable Telegram bot integration', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'telegram', 'key': 'telegram_welcome_message', 'label': 'Welcome Message', 'value': 'Welcome to OxiWorld Trading Academy! 🎉', 'data_type': 'text', 'description': 'Default welcome message for new members', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            
            # System Settings
            {'category': 'system', 'key': 'maintenance_mode', 'label': 'Maintenance Mode', 'value': False, 'data_type': 'boolean', 'description': 'Enable maintenance mode (blocks non-admin access)', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'system', 'key': 'maintenance_message', 'label': 'Maintenance Message', 'value': 'We are currently performing scheduled maintenance. Please check back soon.', 'data_type': 'text', 'description': 'Message shown during maintenance', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'system', 'key': 'cache_enabled', 'label': 'Cache Enabled', 'value': True, 'data_type': 'boolean', 'description': 'Enable Redis caching', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'system', 'key': 'cache_ttl', 'label': 'Cache TTL', 'value': 900, 'data_type': 'integer', 'description': 'Default cache TTL in seconds (900 = 15 minutes)', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            
            # Security Settings
            {'category': 'security', 'key': 'session_timeout', 'label': 'Session Timeout', 'value': 3600, 'data_type': 'integer', 'description': 'User session timeout in seconds (3600 = 1 hour)', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'security', 'key': 'password_min_length', 'label': 'Min Password Length', 'value': 8, 'data_type': 'integer', 'description': 'Minimum password length', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'security', 'key': 'otp_expiry_minutes', 'label': 'OTP Expiry', 'value': 10, 'data_type': 'integer', 'description': 'OTP expiry time in minutes', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'security', 'key': 'max_login_attempts', 'label': 'Max Login Attempts', 'value': 5, 'data_type': 'integer', 'description': 'Maximum failed login attempts before lockout', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            
            # Notification Settings
            {'category': 'notifications', 'key': 'email_notifications_enabled', 'label': 'Email Notifications', 'value': True, 'data_type': 'boolean', 'description': 'Enable email notifications', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
            {'category': 'notifications', 'key': 'telegram_notifications_enabled', 'label': 'Telegram Notifications', 'value': True, 'data_type': 'boolean', 'description': 'Enable Telegram notifications', 'is_encrypted': False, 'is_sensitive': False, 'is_active': True},
        ]
        
        created_count = 0
        for setting_data in settings_data:
            setting, created = PlatformSetting.objects.update_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {setting.label}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Settings seeded: {created_count} created\n'))
        
        # Migrate Telegram groups from settings.py if they exist
        if hasattr(django_settings, 'TELEGRAM_GROUPS'):
            self.stdout.write('Migrating Telegram groups from settings.py...')
            telegram_groups = django_settings.TELEGRAM_GROUPS
            groups_created = 0
            
            for group_key, group_data in telegram_groups.items():
                group, created = TelegramGroup.objects.update_or_create(
                    group_key=group_key,
                    defaults={
                        'name': group_data.get('name', group_key.replace('_', ' ').title()),
                        'chat_id': group_data.get('chat_id', ''),
                        'access_level': group_key.replace('_group', '') if '_group' in group_key else 'monthly',
                        'description': 'Migrated from settings.py',
                        'is_active': True,
                        'auto_add_users': True,
                        'auto_remove_expired': True,
                    }
                )
                if created:
                    groups_created += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Created group: {group.name}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Telegram groups: {groups_created} created'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Seeding completed successfully!'))
