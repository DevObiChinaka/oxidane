from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
import json

from .models import PlatformSetting, SettingChangeLog, TelegramGroup, SettingsBackup
from .serializers import (
    PlatformSettingSerializer,
    PlatformSettingUpdateSerializer,
    SettingChangeLogSerializer,
    TelegramGroupSerializer,
    TelegramGroupBulkUpdateSerializer,
    SettingsBackupSerializer,
    SettingsByCategorySerializer,
    SettingsValidationSerializer,
    SettingsBulkUpdateSerializer
)
from users.permissions import IsAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


def get_admin_user(request):
    """Get the authenticated admin user from request"""
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
        return request.user
    return None


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==================== Platform Settings Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_all_settings(request):
    """
    Get all platform settings, optionally filtered by category
    Query params: category, search
    """
    queryset = PlatformSetting.objects.all()
    
    # Filter by category
    category = request.query_params.get('category', None)
    if category:
        queryset = queryset.filter(category=category)
    
    # Search in key or description
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(key__icontains=search) | Q(description__icontains=search)
        )
    
    # Filter public/private
    is_public = request.query_params.get('is_public', None)
    if is_public is not None:
        queryset = queryset.filter(is_public=is_public.lower() == 'true')
    
    settings = queryset.order_by('category', 'key')
    serializer = PlatformSettingSerializer(settings, many=True)
    
    return Response({
        'success': True,
        'count': settings.count(),
        'settings': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_settings_by_category(request):
    """Get settings grouped by category"""
    categories = PlatformSetting.CATEGORY_CHOICES
    result = []
    
    for category_value, category_label in categories:
        settings = PlatformSetting.objects.filter(category=category_value)
        if settings.exists():
            result.append({
                'category': category_value,
                'category_label': category_label,
                'settings': PlatformSettingSerializer(settings, many=True).data,
                'count': settings.count()
            })
    
    return Response({
        'success': True,
        'categories': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_setting(request, key):
    """Get a single setting by key"""
    try:
        setting = PlatformSetting.objects.get(key=key)
        serializer = PlatformSettingSerializer(setting)
        return Response({
            'success': True,
            'setting': serializer.data
        })
    except PlatformSetting.DoesNotExist:
        return Response(
            {'error': f"Setting '{key}' not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def update_setting(request, key):
    """Update a single setting"""
    try:
        setting = PlatformSetting.objects.get(key=key)
    except PlatformSetting.DoesNotExist:
        return Response(
            {'error': f"Setting '{key}' not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = PlatformSettingUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_value = setting.value
    new_value = serializer.validated_data.get('value')
    change_reason = serializer.validated_data.get('change_reason', '')
    
    admin_user = get_admin_user(request)
    
    # Validate new value
    try:
        setting.validate_value(new_value)
    except ValueError as e:
        return Response(
            {'error': f"Validation failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update setting
    setting.value = new_value
    if 'description' in serializer.validated_data:
        setting.description = serializer.validated_data['description']
    setting.last_modified_by = admin_user
    setting.save()
    
    # Log the change
    SettingChangeLog.objects.create(
        setting=setting,
        old_value=old_value,
        new_value=new_value,
        change_reason=change_reason,
        changed_by=admin_user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
    )
    
    return Response({
        'success': True,
        'message': f"Setting '{key}' updated successfully",
        'setting': PlatformSettingSerializer(setting).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_update_settings(request):
    """Bulk update multiple settings"""
    serializer = SettingsBulkUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    settings_data = serializer.validated_data['settings']
    change_reason = serializer.validated_data.get('change_reason', 'Bulk update')
    
    updated = []
    failed = []
    
    admin_user = get_admin_user(request)
    
    with transaction.atomic():
        for setting_data in settings_data:
            key = setting_data['key']
            new_value = setting_data['value']
            
            try:
                setting = PlatformSetting.objects.get(key=key)
                old_value = setting.value
                
                # Validate
                setting.validate_value(new_value)
                
                # Update
                setting.value = new_value
                setting.last_modified_by = admin_user
                setting.save()
                
                # Log
                SettingChangeLog.objects.create(
                    setting=setting,
                    old_value=old_value,
                    new_value=new_value,
                    change_reason=change_reason,
                    changed_by=admin_user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
                
                updated.append(key)
                
            except PlatformSetting.DoesNotExist:
                failed.append({'key': key, 'reason': 'Setting not found'})
            except ValueError as e:
                failed.append({'key': key, 'reason': str(e)})
    
    return Response({
        'success': True,
        'updated': len(updated),
        'failed': len(failed),
        'updated_keys': updated,
        'failed_settings': failed
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def validate_setting(request):
    """Validate a setting value before saving"""
    serializer = SettingsValidationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'valid': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'valid': True,
        'message': 'Value is valid'
    })


# ==================== Change Log Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_change_logs(request):
    """
    Get change logs, optionally filtered
    Query params: setting_key, user_id, days
    """
    queryset = SettingChangeLog.objects.select_related('setting', 'changed_by')
    
    # Filter by setting key
    setting_key = request.query_params.get('setting_key', None)
    if setting_key:
        queryset = queryset.filter(setting__key=setting_key)
    
    # Filter by user
    user_id = request.query_params.get('user_id', None)
    if user_id:
        queryset = queryset.filter(changed_by_id=user_id)
    
    # Filter by date range
    days = request.query_params.get('days', None)
    if days:
        try:
            days_ago = timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(changed_at__gte=days_ago)
        except ValueError:
            pass
    
    logs = queryset.order_by('-changed_at')[:100]  # Limit to 100 recent logs
    serializer = SettingChangeLogSerializer(logs, many=True)
    
    return Response({
        'success': True,
        'count': logs.count(),
        'logs': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_setting_history(request, key):
    """Get change history for a specific setting"""
    try:
        setting = PlatformSetting.objects.get(key=key)
    except PlatformSetting.DoesNotExist:
        return Response(
            {'error': f"Setting '{key}' not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    logs = SettingChangeLog.objects.filter(setting=setting).order_by('-changed_at')
    serializer = SettingChangeLogSerializer(logs, many=True)
    
    return Response({
        'success': True,
        'setting_key': key,
        'count': logs.count(),
        'history': serializer.data
    })


# ==================== Telegram Groups Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_telegram_groups(request):
    """Get all Telegram groups"""
    groups = TelegramGroup.objects.all().order_by('sort_order', 'name')
    
    # Filter by access level
    access_level = request.query_params.get('access_level', None)
    if access_level:
        groups = groups.filter(access_level=access_level)
    
    # Filter by active status
    is_active = request.query_params.get('is_active', None)
    if is_active is not None:
        groups = groups.filter(is_active=is_active.lower() == 'true')
    
    serializer = TelegramGroupSerializer(groups, many=True)
    
    return Response({
        'success': True,
        'count': groups.count(),
        'groups': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_telegram_group(request, group_id):
    """Get a single Telegram group"""
    try:
        group = TelegramGroup.objects.get(id=group_id)
        serializer = TelegramGroupSerializer(group)
        return Response({
            'success': True,
            'group': serializer.data
        })
    except TelegramGroup.DoesNotExist:
        return Response(
            {'error': 'Telegram group not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def create_telegram_group(request):
    """Create a new Telegram group"""
    serializer = TelegramGroupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    group = serializer.save()
    
    return Response({
        'success': True,
        'message': 'Telegram group created successfully',
        'group': TelegramGroupSerializer(group).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def update_telegram_group(request, group_id):
    """Update a Telegram group"""
    try:
        group = TelegramGroup.objects.get(id=group_id)
    except TelegramGroup.DoesNotExist:
        return Response(
            {'error': 'Telegram group not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = TelegramGroupSerializer(group, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    group = serializer.save()
    
    return Response({
        'success': True,
        'message': 'Telegram group updated successfully',
        'group': TelegramGroupSerializer(group).data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_telegram_group(request, group_id):
    """Delete a Telegram group"""
    try:
        group = TelegramGroup.objects.get(id=group_id)
        group_name = group.name
        group.delete()
        return Response({
            'success': True,
            'message': f"Telegram group '{group_name}' deleted successfully"
        })
    except TelegramGroup.DoesNotExist:
        return Response(
            {'error': 'Telegram group not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_update_telegram_groups(request):
    """Bulk create/update Telegram groups"""
    serializer = TelegramGroupBulkUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    groups = serializer.save()
    
    return Response({
        'success': True,
        'message': f"{len(groups)} Telegram groups created/updated",
        'groups': TelegramGroupSerializer(groups, many=True).data
    })


# ==================== Backup & Restore Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_backups(request):
    """Get all settings backups"""
    backups = SettingsBackup.objects.all().order_by('-created_at')
    serializer = SettingsBackupSerializer(backups, many=True)
    
    return Response({
        'success': True,
        'count': backups.count(),
        'backups': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def create_backup(request):
    """Create a new settings backup"""
    name = request.data.get('name', f"Backup {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    description = request.data.get('description', '')
    
    admin_user = get_admin_user(request)
    
    try:
        backup = SettingsBackup.create_backup(
            created_by=admin_user,
            name=name,
            description=description
        )
        
        return Response({
            'success': True,
            'message': 'Backup created successfully',
            'backup': SettingsBackupSerializer(backup).data
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f"Failed to create backup: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def restore_backup(request, backup_id):
    """Restore settings from a backup"""
    try:
        backup = SettingsBackup.objects.get(id=backup_id)
    except SettingsBackup.DoesNotExist:
        return Response(
            {'error': 'Backup not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    admin_user = get_admin_user(request)
    
    try:
        backup.restore()
        
        # Log the restore action
        SettingChangeLog.objects.create(
            setting=None,
            old_value={},
            new_value={'backup_id': backup_id},
            change_reason=f"Restored from backup: {backup.name}",
            changed_by=admin_user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )
        
        return Response({
            'success': True,
            'message': f"Settings restored from backup '{backup.name}'"
        })
    except Exception as e:
        return Response(
            {'error': f"Failed to restore backup: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_backup(request, backup_id):
    """Delete a backup"""
    try:
        backup = SettingsBackup.objects.get(id=backup_id)
        backup_name = backup.name
        backup.delete()
        return Response({
            'success': True,
            'message': f"Backup '{backup_name}' deleted successfully"
        })
    except SettingsBackup.DoesNotExist:
        return Response(
            {'error': 'Backup not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== Statistics Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_settings_stats(request):
    """Get statistics about settings"""
    total_settings = PlatformSetting.objects.count()
    settings_by_category = PlatformSetting.objects.values('category').annotate(
        count=Count('id')
    )
    encrypted_count = PlatformSetting.objects.filter(is_encrypted=True).count()
    sensitive_count = PlatformSetting.objects.filter(is_sensitive=True).count()
    active_count = PlatformSetting.objects.filter(is_active=True).count()
    
    recent_changes = SettingChangeLog.objects.filter(
        changed_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    telegram_groups_count = TelegramGroup.objects.filter(is_active=True).count()
    total_backups = SettingsBackup.objects.count()
    
    return Response({
        'success': True,
        'stats': {
            'total_settings': total_settings,
            'active_settings': active_count,
            'encrypted_settings': encrypted_count,
            'sensitive_settings': sensitive_count,
            'settings_by_category': list(settings_by_category),
            'recent_changes_7days': recent_changes,
            'active_telegram_groups': telegram_groups_count,
            'total_backups': total_backups
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def test_email_configuration(request):
    """
    Test email configuration by sending a test email
    
    POST /api/admin/settings/test-email/
    Body: {
        "recipient_email": "test@example.com"
    }
    """
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    
    recipient_email = request.data.get('recipient_email')
    if not recipient_email:
        return Response(
            {'success': False, 'error': 'Recipient email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get email settings from database
    try:
        email_settings = {}
        email_keys = [
            'email_host', 'email_port', 'email_use_ssl',
            'email_host_user', 'default_from_email'
        ]
        
        for key in email_keys:
            try:
                setting = PlatformSetting.objects.get(key=key, is_active=True)
                email_settings[key] = setting.value
            except PlatformSetting.DoesNotExist:
                pass
        
        # Attempt to send test email
        subject = 'OxiWorld - Email Configuration Test'
        message = f"""
Hello,

This is a test email from OxiWorld Trading Academy.

If you're receiving this email, your email configuration is working correctly!

Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Best regards,
OxiWorld Team
        """.strip()
        
        from_email = email_settings.get('default_from_email', django_settings.DEFAULT_FROM_EMAIL)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False
        )
        
        admin_user = get_admin_user(request)
        
        # Log the test
        SettingChangeLog.objects.create(
            setting_key='email_test',
            old_value=None,
            new_value=recipient_email,
            changed_by=admin_user,
            change_reason=f'Test email sent to {recipient_email}',
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'success': True,
            'message': f'Test email sent successfully to {recipient_email}',
            'from_email': from_email
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to send test email: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def test_bot_connection(request):
    """
    Test Telegram bot connection by verifying bot token.
    
    POST /api/admin/settings/test-bot/
    Returns bot info if token is valid.
    """
    import requests
    
    try:
        # Get bot token from settings
        bot_token_setting = PlatformSetting.objects.get(
            key='telegram_bot_token',
            is_active=True
        )
        bot_token = bot_token_setting.value
        
        if not bot_token:
            return Response({
                'success': False,
                'error': 'Bot token not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Call Telegram Bot API to get bot info
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        admin_user = get_admin_user(request)
        
        if data.get('ok'):
            bot_info = data.get('result', {})
            
            # Log the test
            SettingChangeLog.objects.create(
                setting_key='telegram_bot_test',
                old_value=None,
                new_value=bot_info.get('username'),
                changed_by=admin_user,
                change_reason='Bot connection test successful',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'message': 'Bot connection successful!',
                'bot_info': {
                    'id': bot_info.get('id'),
                    'username': bot_info.get('username'),
                    'first_name': bot_info.get('first_name'),
                    'can_join_groups': bot_info.get('can_join_groups'),
                    'can_read_all_group_messages': bot_info.get('can_read_all_group_messages'),
                }
            })
        else:
            error_msg = data.get('description', 'Unknown error')
            return Response({
                'success': False,
                'error': f'Invalid bot token: {error_msg}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except PlatformSetting.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Bot token setting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except requests.Timeout:
        return Response({
            'success': False,
            'error': 'Connection to Telegram API timed out'
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to test bot connection: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def sync_group_members(request, group_id):
    """
    Sync member count for a specific Telegram group.
    
    POST /api/admin/telegram-groups/{group_id}/sync-members/
    """
    import requests
    
    try:
        group = TelegramGroup.objects.get(id=group_id)
        
        # Get bot token
        bot_token_setting = PlatformSetting.objects.get(
            key='telegram_bot_token',
            is_active=True
        )
        bot_token = bot_token_setting.value
        
        if not bot_token:
            return Response({
                'success': False,
                'error': 'Bot token not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get member count from Telegram API
        url = f"https://api.telegram.org/bot{bot_token}/getChatMemberCount"
        response = requests.get(url, params={'chat_id': group.chat_id}, timeout=10)
        data = response.json()
        
        admin_user = get_admin_user(request)
        
        if data.get('ok'):
            member_count = data.get('result', 0)
            
            # Update group
            group.member_count = member_count
            group.last_sync_at = timezone.now()
            group.save()
            
            # Log the sync
            SettingChangeLog.objects.create(
                setting_key=f'telegram_group_sync_{group.group_key}',
                old_value=None,
                new_value=member_count,
                changed_by=admin_user,
                change_reason=f'Synced member count for {group.name}',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'message': f'Member count synced successfully',
                'member_count': member_count,
                'last_sync_at': group.last_sync_at
            })
        else:
            error_msg = data.get('description', 'Unknown error')
            return Response({
                'success': False,
                'error': f'Failed to get member count: {error_msg}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except TelegramGroup.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Telegram group not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except PlatformSetting.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Bot token setting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except requests.Timeout:
        return Response({
            'success': False,
            'error': 'Connection to Telegram API timed out'
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to sync members: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
