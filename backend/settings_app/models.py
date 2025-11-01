# Platform settings models and management
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json

User = get_user_model()

class PlatformSetting(models.Model):
    """
    Centralized storage for all platform configuration settings.
    Settings are organized by category and stored as JSON for flexibility.
    """
    CATEGORY_CHOICES = [
        ('platform', 'Platform Settings'),
        ('email', 'Email Configuration'),
        ('telegram', 'Telegram Integration'),
        ('courses', 'Course Settings'),
        ('security', 'User & Security'),
        ('notifications', 'Notifications'),
        ('system', 'System & Maintenance'),
        ('payment', 'Payment Gateway'),
        ('legal', 'Legal & Compliance'),
    ]
    
    DATA_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON Object'),
        ('text', 'Long Text'),
        ('email', 'Email Address'),
        ('url', 'URL'),
        ('color', 'Color Code'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    key = models.CharField(max_length=100, db_index=True)
    value = models.JSONField(help_text="Setting value stored as JSON for flexibility")
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, default='string')
    
    # Security
    is_encrypted = models.BooleanField(
        default=False, 
        help_text="Whether this value is encrypted (for passwords, API keys)"
    )
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Whether to hide this value in UI (show asterisks)"
    )
    
    # Metadata
    label = models.CharField(max_length=200, help_text="Human-readable label for UI")
    description = models.TextField(blank=True, help_text="Help text explaining this setting")
    default_value = models.JSONField(null=True, blank=True, help_text="Default value if not set")
    
    # Validation
    validation_rules = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON object with validation rules: {'min': 0, 'max': 100, 'pattern': '^[a-z]+$'}"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_restart = models.BooleanField(
        default=False,
        help_text="Whether changing this setting requires a server restart"
    )
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='modified_settings'
    )
    
    class Meta:
        unique_together = ['category', 'key']
        ordering = ['category', 'key']
        verbose_name = 'Platform Setting'
        verbose_name_plural = 'Platform Settings'
        indexes = [
            models.Index(fields=['category', 'key']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.label}"
    
    def get_value(self):
        """Get the actual value, decrypting if necessary"""
        if self.is_encrypted and self.value:
            # TODO: Implement decryption logic
            # For now, return as-is
            pass
        return self.value
    
    def set_value(self, new_value, encrypted=False):
        """Set value, encrypting if necessary"""
        if encrypted:
            # TODO: Implement encryption logic
            pass
        self.value = new_value
    
    def validate_value(self, value):
        """Validate value against validation rules"""
        if not self.validation_rules:
            return True
        
        rules = self.validation_rules
        
        # Validate based on data type
        if self.data_type == 'integer':
            if 'min' in rules and value < rules['min']:
                raise ValidationError(f"Value must be at least {rules['min']}")
            if 'max' in rules and value > rules['max']:
                raise ValidationError(f"Value must be at most {rules['max']}")
        
        elif self.data_type == 'string' or self.data_type == 'text':
            if 'min_length' in rules and len(value) < rules['min_length']:
                raise ValidationError(f"Value must be at least {rules['min_length']} characters")
            if 'max_length' in rules and len(value) > rules['max_length']:
                raise ValidationError(f"Value must be at most {rules['max_length']} characters")
        
        return True
    
    def save(self, *args, **kwargs):
        # Validate value before saving
        if self.value is not None:
            try:
                self.validate_value(self.value)
            except ValidationError as e:
                raise ValidationError(f"Invalid value for {self.label}: {str(e)}")
        
        super().save(*args, **kwargs)


class SettingChangeLog(models.Model):
    """
    Audit trail for all setting changes.
    Tracks who changed what, when, and why.
    """
    setting = models.ForeignKey(
        PlatformSetting, 
        on_delete=models.CASCADE,
        related_name='change_logs'
    )
    changed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='setting_changes'
    )
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField()
    
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    change_reason = models.TextField(
        blank=True,
        help_text="Optional reason for this change"
    )
    
    # Track request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Setting Change Log'
        verbose_name_plural = 'Setting Change Logs'
        indexes = [
            models.Index(fields=['setting', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.setting.label} changed by {self.changed_by} at {self.changed_at}"


class TelegramGroup(models.Model):
    """
    Telegram group configuration.
    Moves hardcoded TELEGRAM_GROUPS from settings.py to database.
    """
    ACCESS_LEVEL_CHOICES = [
        ('all', 'All Paid Subscribers'),
        ('weekly', 'Weekly+ Subscribers'),
        ('monthly', 'Monthly+ Subscribers'),
        ('vip', 'VIP Only'),
        ('mentorship', 'Mentorship Members'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    chat_id = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Telegram chat ID (e.g., -1002920074390)"
    )
    group_key = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Internal key for code reference (e.g., 'premium_signals')"
    )
    
    access_level = models.CharField(
        max_length=20, 
        choices=ACCESS_LEVEL_CHOICES,
        default='monthly'
    )
    
    description = models.TextField(blank=True)
    
    # Group settings
    is_active = models.BooleanField(default=True)
    auto_add_users = models.BooleanField(
        default=True,
        help_text="Automatically add verified users to this group"
    )
    auto_remove_expired = models.BooleanField(
        default=True,
        help_text="Automatically remove users when subscription expires"
    )
    
    # Welcome message
    welcome_message_enabled = models.BooleanField(default=True)
    welcome_message_template = models.TextField(
        blank=True,
        help_text="Template for welcome message. Use {{user_name}}, {{plan_type}} variables."
    )
    
    # Public vs Private groups
    is_public = models.BooleanField(
        default=False,
        help_text="Public groups show invite link; private groups are bot-invite only"
    )
    invite_link = models.URLField(
        blank=True,
        help_text="Telegram invite link (only for public groups)"
    )
    
    # Order for display
    sort_order = models.PositiveIntegerField(default=0)
    
    # Stats
    member_count = models.PositiveIntegerField(default=0, editable=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Telegram Group'
        verbose_name_plural = 'Telegram Groups'
    
    def __str__(self):
        return f"{self.name} ({self.access_level})"
    
    def get_eligible_subscription_types(self):
        """
        Get list of subscription plan types that can access this group.
        """
        access_map = {
            'all': ['weekly', 'monthly', 'yearly', 'vip_weekly', 'vip_monthly', 'vip_yearly', 'signals_weekly', 'signals_monthly', 'signals_yearly'],
            'weekly': ['weekly', 'monthly', 'yearly', 'vip_weekly', 'vip_monthly', 'vip_yearly', 'signals_weekly', 'signals_monthly', 'signals_yearly'],
            'monthly': ['monthly', 'yearly', 'vip_monthly', 'vip_yearly', 'signals_monthly', 'signals_yearly'],
            'vip': ['vip_weekly', 'vip_monthly', 'vip_yearly'],
            'mentorship': ['mentorship_basic'],
        }
        return access_map.get(self.access_level, [])
    
    def sync_member_count(self):
        """
        Sync member count with actual Telegram group.
        To be implemented with Telegram Bot API.
        """
        # TODO: Implement with Telegram Bot API
        pass


class SettingsBackup(models.Model):
    """
    Backup snapshots of all settings.
    Allows restore to previous state.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Backup data
    settings_data = models.JSONField(
        help_text="JSON snapshot of all settings at backup time"
    )
    telegram_groups_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON snapshot of Telegram groups"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='settings_backups'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Restore tracking
    restored_at = models.DateTimeField(null=True, blank=True)
    restored_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restored_settings'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Settings Backup'
        verbose_name_plural = 'Settings Backups'
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def create_backup(cls, user, name=None, description=''):
        """Create a new backup of current settings"""
        if not name:
            name = f"Auto Backup - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Collect all settings
        settings_data = {}
        for setting in PlatformSetting.objects.filter(is_active=True):
            key = f"{setting.category}.{setting.key}"
            settings_data[key] = {
                'value': setting.value,
                'data_type': setting.data_type,
                'label': setting.label,
            }
        
        # Collect Telegram groups
        telegram_groups_data = list(TelegramGroup.objects.filter(is_active=True).values())
        
        backup = cls.objects.create(
            name=name,
            description=description,
            settings_data=settings_data,
            telegram_groups_data=telegram_groups_data,
            created_by=user
        )
        
        return backup
    
    def restore(self, user):
        """Restore settings from this backup"""
        # TODO: Implement restore logic
        self.restored_at = timezone.now()
        self.restored_by = user
        self.save()
        
        return True
