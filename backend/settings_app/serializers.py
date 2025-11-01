from rest_framework import serializers
from .models import PlatformSetting, SettingChangeLog, TelegramGroup, SettingsBackup
from django.contrib.auth import get_user_model

User = get_user_model()


class PlatformSettingSerializer(serializers.ModelSerializer):
    """Serializer for platform settings"""
    last_modified_by_username = serializers.CharField(
        source='last_modified_by.username',
        read_only=True,
        allow_null=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    class Meta:
        model = PlatformSetting
        fields = [
            'id', 'category', 'category_display', 'key', 'label', 'value', 'data_type',
            'is_encrypted', 'is_sensitive', 'description', 'default_value',
            'validation_rules', 'is_active', 'requires_restart',
            'created_at', 'updated_at',
            'last_modified_by', 'last_modified_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_modified_by_username', 'category_display']


class PlatformSettingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating platform settings (excludes sensitive fields)"""
    change_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Reason for the change (for audit log)"
    )
    
    class Meta:
        model = PlatformSetting
        fields = ['value', 'description', 'change_reason']


class SettingChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for setting change logs"""
    changed_by_username = serializers.CharField(
        source='changed_by.username',
        read_only=True
    )
    setting_key = serializers.CharField(
        source='setting.key',
        read_only=True
    )
    setting_category = serializers.CharField(
        source='setting.category',
        read_only=True
    )
    
    class Meta:
        model = SettingChangeLog
        fields = [
            'id', 'setting', 'setting_key', 'setting_category',
            'old_value', 'new_value', 'change_reason',
            'changed_by', 'changed_by_username', 'changed_at',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'changed_at']


class TelegramGroupSerializer(serializers.ModelSerializer):
    """Serializer for Telegram groups"""
    access_level_display = serializers.CharField(
        source='get_access_level_display',
        read_only=True
    )
    
    class Meta:
        model = TelegramGroup
        fields = [
            'id', 'name', 'chat_id', 'group_key', 'access_level', 'access_level_display',
            'description', 'is_active', 'auto_add_users',
            'auto_remove_expired', 'welcome_message_enabled', 'welcome_message_template',
            'is_public', 'invite_link',
            'sort_order', 'member_count', 'last_sync_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync_at', 'member_count', 'access_level_display']
    
    def validate_chat_id(self, value):
        """Validate Telegram chat ID format"""
        if not value.startswith('-'):
            raise serializers.ValidationError(
                "Telegram group chat ID must start with '-'"
            )
        try:
            int(value)
        except ValueError:
            raise serializers.ValidationError(
                "Chat ID must be a valid integer"
            )
        return value
    
    def validate_group_key(self, value):
        """Validate group key is lowercase and alphanumeric"""
        if not value.islower() or not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Group key must be lowercase alphanumeric with underscores only"
            )
        return value


class TelegramGroupBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating Telegram groups"""
    groups = TelegramGroupSerializer(many=True)
    
    def create(self, validated_data):
        """Bulk create/update groups"""
        groups_data = validated_data.get('groups', [])
        created_groups = []
        
        for group_data in groups_data:
            group_key = group_data.get('group_key')
            group, created = TelegramGroup.objects.update_or_create(
                group_key=group_key,
                defaults=group_data
            )
            created_groups.append(group)
        
        return created_groups


class SettingsBackupSerializer(serializers.ModelSerializer):
    """Serializer for settings backups"""
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )
    restored_by_username = serializers.CharField(
        source='restored_by.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = SettingsBackup
        fields = [
            'id', 'name', 'description', 'settings_data',
            'telegram_groups_data', 'created_by',
            'created_by_username', 'created_at',
            'restored_at', 'restored_by', 'restored_by_username'
        ]
        read_only_fields = [
            'id', 'settings_data', 'telegram_groups_data',
            'created_at', 'created_by_username',
            'restored_at', 'restored_by', 'restored_by_username'
        ]


class SettingsByCategorySerializer(serializers.Serializer):
    """Serializer for grouped settings by category"""
    category = serializers.CharField()
    settings = PlatformSettingSerializer(many=True)
    count = serializers.IntegerField()


class SettingsValidationSerializer(serializers.Serializer):
    """Serializer for validating settings values"""
    key = serializers.CharField()
    value = serializers.JSONField()
    
    def validate(self, data):
        """Validate setting value against its rules"""
        try:
            setting = PlatformSetting.objects.get(key=data['key'])
            setting.validate_value(data['value'])
        except PlatformSetting.DoesNotExist:
            raise serializers.ValidationError({
                'key': f"Setting with key '{data['key']}' does not exist"
            })
        except ValueError as e:
            raise serializers.ValidationError({
                'value': str(e)
            })
        
        return data


class SettingsBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating multiple settings"""
    settings = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    change_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_settings(self, value):
        """Validate each setting in the bulk update"""
        for setting_data in value:
            if 'key' not in setting_data or 'value' not in setting_data:
                raise serializers.ValidationError(
                    "Each setting must have 'key' and 'value' fields"
                )
        return value
