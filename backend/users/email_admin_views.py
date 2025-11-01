# Email Templates Admin API
# API endpoints for managing email templates

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .models import EmailTemplate, EmailLog, User
from .email_service import EmailTemplateService
from .admin_auth import admin_required
from subscriptions.models import SignalSubscription

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['GET', 'POST'])
@admin_required
def email_templates_list(request):
    """CRUD operations for email templates"""
    
    if request.method == 'GET':
        """Get list of email templates with pagination and filtering"""
        try:
            # Get query parameters
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 10)), 50)
            template_type = request.GET.get('type')
            status = request.GET.get('status')
            search = request.GET.get('search', '').strip()
            
            # Build queryset
            templates = EmailTemplate.objects.all()
            
            # Apply filters
            if template_type:
                templates = templates.filter(template_type=template_type)
            if status:
                templates = templates.filter(status=status)
            if search:
                templates = templates.filter(name__icontains=search)
            
            # Pagination
            paginator = Paginator(templates, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize data
            templates_data = []
            for template in page_obj:
                templates_data.append({
                    'id': str(template.id),
                    'name': template.name,
                    'template_type': template.template_type,
                    'template_type_display': template.get_template_type_display(),
                    'status': template.status,
                    'subject_template': template.subject_template,
                    'description': template.description,
                    'is_default': template.is_default,
                    'sent_count': template.sent_count,
                    'last_used': template.last_used.isoformat() if template.last_used else None,
                    'created_at': template.created_at.isoformat(),
                    'updated_at': template.updated_at.isoformat(),
                    'available_variables': template.available_variables,
                })
            
            return JsonResponse({
                'success': True,
                'templates': templates_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching email templates: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch email templates'
            }, status=500)
    
    elif request.method == 'POST':
        """Create new email template"""
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'template_type', 'subject_template', 'html_content']
            for field in required_fields:
                if not data.get(field):
                    return Response({
                        'success': False,
                        'error': f'Field "{field}" is required'
                    }, status=400)
            
            # Create template
            template = EmailTemplate.objects.create(
                name=data['name'],
                template_type=data['template_type'],
                subject_template=data['subject_template'],
                html_content=data['html_content'],
                text_content=data.get('text_content', ''),
                description=data.get('description', ''),
                status=data.get('status', 'draft'),
                is_default=data.get('is_default', False),
                from_email=data.get('from_email', ''),
                from_name=data.get('from_name', ''),
                # created_by=request.user if request.user.is_authenticated else None
            )
            
            logger.info(f"Email template created: {template.name}")
            
            return Response({
                'success': True,
                'template': {
                    'id': str(template.id),
                    'name': template.name,
                    'template_type': template.template_type,
                    'status': template.status,
                    'created_at': template.created_at.isoformat(),
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating email template: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to create email template'
            }, status=500)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@admin_required
def email_template_detail(request, template_id):
    """Individual email template operations"""
    
    if request.method == 'GET':
        """Get specific email template"""
        try:
            template = get_object_or_404(EmailTemplate, id=template_id)
            
            return JsonResponse({
                'success': True,
                'template': {
                    'id': str(template.id),
                    'name': template.name,
                    'template_type': template.template_type,
                    'template_type_display': template.get_template_type_display(),
                    'subject_template': template.subject_template,
                    'html_content': template.html_content,
                    'text_content': template.text_content,
                    'description': template.description,
                    'status': template.status,
                    'is_default': template.is_default,
                    'from_email': template.from_email,
                    'from_name': template.from_name,
                    'available_variables': template.available_variables,
                    'sent_count': template.sent_count,
                    'last_used': template.last_used.isoformat() if template.last_used else None,
                    'created_at': template.created_at.isoformat(),
                    'updated_at': template.updated_at.isoformat(),
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching email template {template_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Template not found'
            }, status=404)
    
    elif request.method == 'PUT':
        """Update email template"""
        try:
            template = get_object_or_404(EmailTemplate, id=template_id)
            data = json.loads(request.body)
            
            # Update fields
            updatable_fields = [
                'name', 'subject_template', 'html_content', 'text_content',
                'description', 'status', 'is_default', 'from_email', 'from_name'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(template, field, data[field])
            
            template.save()
            
            logger.info(f"Email template updated: {template.name} by {request.user.email}")
            
            return JsonResponse({
                'success': True,
                'template': {
                    'id': str(template.id),
                    'name': template.name,
                    'updated_at': template.updated_at.isoformat(),
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating email template {template_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to update email template'
            }, status=500)
    
    elif request.method == 'DELETE':
        """Delete email template"""
        try:
            template = get_object_or_404(EmailTemplate, id=template_id)
            template_name = template.name
            template.delete()
            
            logger.info(f"Email template deleted: {template_name}")
            
            return JsonResponse({
                'success': True,
                'message': 'Template deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting email template {template_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to delete email template'
            }, status=500)


@csrf_exempt
@api_view(['POST'])
@admin_required
def preview_email_template(request, template_id):
    """Preview email template with sample data"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
        
        service = EmailTemplateService()
        result = service.preview_email(template_id, data.get('sample_data'))
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error previewing email template {template_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to preview email template'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@admin_required
def send_test_email(request, template_id):
    """Send test email using template"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        recipient_email = data.get('recipient_email')
        
        if not recipient_email:
            return JsonResponse({
                'success': False,
                'error': 'Recipient email is required'
            }, status=400)
        
        # Get template
        template = get_object_or_404(EmailTemplate, id=template_id)
        
        # Try to find existing user with this email, or create a test user object
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user = User.objects.filter(email=recipient_email).first()
        except:
            test_user = None
        
        # If no existing user found, create test context data directly
        if not test_user:
            sample_data = data.get('sample_data', {})
            user_data = sample_data.get('user', {})
            test_user = type('TestUser', (), {
                'first_name': user_data.get('first_name', 'Test'),
                'last_name': user_data.get('last_name', 'User'),
                'email': recipient_email,
                'username': recipient_email.split('@')[0]
            })()
        
        # Send test email
        service = EmailTemplateService()
        
        # Debug logging
        logger.info(f"Sending test email to {recipient_email}")
        logger.info(f"Template type: {template.template_type}")
        logger.info(f"Template from_email: '{template.from_email}'")
        logger.info(f"Template from_name: '{template.from_name}'")
        logger.info(f"Service default_from_email: '{service.default_from_email}'")
        logger.info(f"Service company_name: '{service.company_name}'")
        
        result = service.send_email(
            template_type=template.template_type,
            recipient_email=recipient_email,
            user=test_user,
            test_mode=False  # Actually send the test email
        )
        
        logger.info(f"Test email sent for template {template.name} to {recipient_email}")
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending test email for template {template_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to send test email'
        }, status=500)


@csrf_exempt
@admin_required
def send_bulk_email(request, template_id):
    """Send bulk email to selected recipients"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        recipient_type = data.get('recipientType', 'all_users')
        specific_users = data.get('specificUsers', [])
        schedule_type = data.get('scheduleType', 'now')
        
        # Get template
        template = get_object_or_404(EmailTemplate, id=template_id)
        
        # Get users based on recipient type
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if recipient_type == 'all_users':
            recipients = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')
        elif recipient_type == 'active_subscribers':
            recipients = User.objects.filter(
                is_active=True, 
                email__isnull=False,
                signal_subscriptions__payment_status='verified'
            ).exclude(email='').distinct()
        elif recipient_type == 'trial_users':
            # Users who are active but don't have verified subscriptions
            recipients = User.objects.filter(
                is_active=True,
                email__isnull=False
            ).exclude(
                email='',
                signal_subscriptions__payment_status='verified'
            ).distinct()
        elif recipient_type == 'inactive_users':
            recipients = User.objects.filter(
                Q(is_active=False) | Q(last_login__isnull=True),
                email__isnull=False
            ).exclude(email='')
        elif recipient_type == 'specific_users':
            recipients = User.objects.filter(
                id__in=specific_users,
                email__isnull=False
            ).exclude(email='')
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid recipient type'
            }, status=400)
        
        # Send emails
        service = EmailTemplateService()
        sent_count = 0
        failed_count = 0
        errors = []
        
        for user in recipients:
            try:
                result = service.send_email(
                    template_type=template.template_type,
                    recipient_email=user.email,
                    user=user,
                    test_mode=False
                )
                if result.get('success'):
                    sent_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Failed to send to {user.email}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to send to {user.email}: {str(e)}")
        
        logger.info(f"Bulk email sent for template {template.name}: {sent_count} sent, {failed_count} failed")
        
        return JsonResponse({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_recipients': recipients.count(),
            'errors': errors[:10]  # Limit errors to first 10
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending bulk email for template {template_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to send bulk email: {str(e)}'
        }, status=500)


@api_view(['GET'])
@admin_required
def email_template_types(request):
    """Get available email template types"""
    return JsonResponse({
        'success': True,
        'types': [
            {
                'value': choice[0],
                'label': choice[1],
                'description': get_template_type_description(choice[0])
            }
            for choice in EmailTemplate.TEMPLATE_TYPES
        ]
    })


@api_view(['GET'])
@admin_required
def email_analytics(request):
    """Get email analytics and statistics"""
    try:
        # Overall stats
        total_templates = EmailTemplate.objects.count()
        active_templates = EmailTemplate.objects.filter(status='active').count()
        total_sent = EmailLog.objects.count()
        recent_sent = EmailLog.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        
        # Success rate
        successful_emails = EmailLog.objects.filter(status='sent').count()
        failed_emails = EmailLog.objects.filter(status='failed').count()
        success_rate = (successful_emails / total_sent * 100) if total_sent > 0 else 0
        
        # Top templates
        top_templates = EmailTemplate.objects.filter(
            sent_count__gt=0
        ).order_by('-sent_count')[:5]
        
        top_templates_data = [
            {
                'name': template.name,
                'template_type': template.get_template_type_display(),
                'sent_count': template.sent_count,
                'last_used': template.last_used.isoformat() if template.last_used else None
            }
            for template in top_templates
        ]
        
        return JsonResponse({
            'success': True,
            'analytics': {
                'total_templates': total_templates,
                'active_templates': active_templates,
                'total_sent': total_sent,
                'recent_sent': recent_sent,
                'success_rate': round(success_rate, 1),
                'failed_emails': failed_emails,
                'top_templates': top_templates_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching email analytics: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch email analytics'
        }, status=500)


def get_template_type_description(template_type):
    """Get description for template type"""
    descriptions = {
        'welcome': 'Sent to new users when they register',
        'subscription_success': 'Sent when subscription payment is successful',
        'subscription_expiry': 'Sent when subscription is about to expire',
        'payment_success': 'Sent when any payment is successful',
        'payment_failed': 'Sent when payment fails or is declined',
        'renewal_reminder': 'Sent to remind users to renew subscription',
        'telegram_added': 'Sent when user is added to Telegram group',
        'signin_notification': 'Sent when user signs in (if enabled)',
        'custom': 'Custom template for specific use cases'
    }
    return descriptions.get(template_type, 'Custom email template')