"""
Admin API views for user management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
import json
import csv

from subscriptions.models import Subscription, BillingProfile, SubscriptionPlan
from courses.models import Course
from .permissions import IsAdmin
from .models import AdminAction

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_list(request):
    """Get paginated list of users with filters and search"""
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 25)), 100)  # Max 100 per page
        search = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '')  # active, inactive, verified, unverified
        subscription_filter = request.GET.get('subscription', '')  # has_signals, has_courses, none
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Base queryset with annotations
        users = User.objects.select_related('billing_profile').annotate(
            subscriptions_count=Count('billing_profile__subscriptions', distinct=True),
            active_subscriptions_count=Count(
                'billing_profile__subscriptions', 
                filter=Q(
                    billing_profile__subscriptions__status='active',
                    billing_profile__subscriptions__end_date__gt=timezone.now()
                ),
                distinct=True
            )
        ).order_by('-created_at')
        
        # Apply search filter
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        # Apply status filters
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        elif status_filter == 'verified':
            users = users.filter(is_email_verified=True)
        elif status_filter == 'unverified':
            users = users.filter(is_email_verified=False)
        
        # Apply subscription filters
        if subscription_filter:
            if subscription_filter == 'has_subscription':
                users = users.filter(subscriptions_count__gt=0)
            elif subscription_filter == 'no_subscription':
                users = users.filter(subscriptions_count=0)
            elif subscription_filter == 'active_subscription':
                users = users.filter(active_subscriptions_count__gt=0)
            else:
                # Filter by specific plan slug
                users = users.filter(
                    billing_profile__subscriptions__plan__slug=subscription_filter,
                    billing_profile__subscriptions__status='active',
                    billing_profile__subscriptions__end_date__gt=timezone.now()
                ).distinct()
        
        # Apply date filters
        if date_from:
            users = users.filter(created_at__gte=date_from)
        if date_to:
            users = users.filter(created_at__lte=date_to)
        
        # Paginate
        paginator = Paginator(users, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize users
        user_data = []
        for user in page_obj:
            # Get latest subscription info
            latest_sub = None
            if hasattr(user, 'billing_profile') and user.billing_profile:
                latest_sub = user.billing_profile.subscriptions.filter(
                    status='active'
                ).select_related('plan').order_by('-created_at').first()
            
            # Get OAuth provider info
            oauth_provider = user.oauth_providers.first() if hasattr(user, 'oauth_providers') else None
            
            # Simple display name logic
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f"{first_name} {last_name}".strip()
            display_name = full_name or user.username
            
            user_data.append({
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'display_name': display_name,
                'is_active': user.is_active,
                'is_email_verified': user.is_email_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                
                # OAuth info
                'has_oauth': bool(oauth_provider),
                'oauth_provider': oauth_provider.provider if oauth_provider else None,
                
                # Subscription info
                'subscriptions_count': user.subscriptions_count,
                'active_subscriptions_count': user.active_subscriptions_count,
                'latest_subscription': {
                    'plan_name': latest_sub.plan.name if latest_sub and latest_sub.plan else None,
                    'end_date': latest_sub.end_date.isoformat() if latest_sub else None,
                    'status': latest_sub.status if latest_sub else None,
                } if latest_sub else None,
            })
        
        return Response({
            'users': user_data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_users': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            },
            'filters': {
                'search': search,
                'status': status_filter,
                'subscription': subscription_filter,
                'date_from': date_from,
                'date_to': date_to,
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch users',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_detail(request, user_id):
    """Get detailed information about a specific user"""
    try:
        user = User.objects.select_related('billing_profile').prefetch_related(
            'billing_profile__subscriptions__plan',
            'oauth_providers'
        ).get(id=user_id)
        
        # Get subscription history
        subscriptions = []
        total_paid = Decimal('0.00')
        if hasattr(user, 'billing_profile') and user.billing_profile:
            subscriptions = list(user.billing_profile.subscriptions.order_by('-created_at'))
            # Calculate total in USD using plan base prices (not mixed currencies)
            total_paid = sum(
                (sub.plan.base_price if sub.plan else Decimal('0.00')) for sub in subscriptions 
                if sub.status in ['active', 'expired', 'cancelled']
            )
        
        # Simple display name logic
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        full_name = f"{first_name} {last_name}".strip()
        display_name = full_name or user.username
        
        # OAuth info
        oauth_provider = None
        if user.oauth_providers.exists():
            oauth_provider = user.oauth_providers.first().provider

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'display_name': display_name,
                'avatar': user.avatar if hasattr(user, 'avatar') else None,
                'has_oauth': user.oauth_providers.exists(),
                'oauth_provider': oauth_provider,
                'is_active': user.is_active,
                'is_email_verified': user.is_email_verified,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            },
            'subscription_history': [
                {
                    'id': str(sub.id),
                    'plan_name': sub.plan.name if sub.plan else 'Unknown',
                    'plan_base_price_usd': float(sub.plan.base_price) if sub.plan else 0.0,
                    'amount_paid': float(sub.amount_paid or 0),
                    'currency': sub.currency,
                    'status': sub.status,
                    'start_date': sub.start_date.isoformat() if sub.start_date else None,
                    'end_date': sub.end_date.isoformat() if sub.end_date else None,
                    'created_at': sub.created_at.isoformat(),
                    'auto_renew': sub.auto_renew,
                } for sub in subscriptions
            ],
            'oauth_providers': [
                {
                    'provider': oauth.provider,
                    'provider_user_id': oauth.provider_user_id,
                    'created_at': oauth.created_at.isoformat(),
                } for oauth in user.oauth_providers.all()
            ],
            'metrics': {
                'total_subscriptions': len(subscriptions),
                'active_subscriptions': sum(
                    1 for sub in subscriptions 
                    if sub.status == 'active' and (sub.end_date is None or sub.end_date > timezone.now())
                ),
                'total_paid': float(total_paid),
                'has_oauth': user.oauth_providers.exists(),
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print(f"Error in user_detail: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': 'Failed to fetch user details',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_action(request, user_id):
    """Perform actions on a user account"""
    try:
        user = User.objects.get(id=user_id)
        action = request.data.get('action')
        
        if action == 'activate':
            user.is_active = True
            user.save()
            message = f"User {user.email} activated successfully"
            AdminAction.log_action(request.user, 'activate', user, request=request)
            
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            message = f"User {user.email} deactivated successfully"
            AdminAction.log_action(request.user, 'deactivate', user, request=request)
            
        elif action == 'verify_email':
            user.is_email_verified = True
            user.save()
            message = f"Email verified for {user.email}"
            AdminAction.log_action(request.user, 'verify_email', user, request=request)
            
        elif action == 'make_staff':
            user.is_staff = True
            user.save()
            message = f"{user.email} granted staff privileges"
            AdminAction.log_action(request.user, 'make_staff', user, request=request)
            
        elif action == 'remove_staff':
            user.is_staff = False
            user.save()
            message = f"Staff privileges removed for {user.email}"
            AdminAction.log_action(request.user, 'remove_staff', user, request=request)
            
        else:
            return Response({
                'error': 'Invalid action. Allowed actions: activate, deactivate, verify_email, make_staff, remove_staff'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': message,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'is_active': user.is_active,
                'is_email_verified': user.is_email_verified,
                'is_staff': user.is_staff,
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to perform action',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def users_analytics(request):
    """Get user analytics and summary stats"""
    try:
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        # Basic counts
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_email_verified=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        # Registration trends
        new_users_30d = User.objects.filter(created_at__gte=last_30_days).count()
        new_users_7d = User.objects.filter(created_at__gte=last_7_days).count()
        
        # Active subscriptions (count unique billing profiles with active subs)
        active_subs = Subscription.objects.filter(
            status='active',
            end_date__gt=now
        ).count()
        
        # Recent activity
        recent_logins_7d = User.objects.filter(
            last_login__gte=last_7_days
        ).count()
        
        return Response({
            'summary': {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'staff_users': staff_users,
                'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
                'active_rate': (active_users / total_users * 100) if total_users > 0 else 0,
            },
            'growth': {
                'new_users_30d': new_users_30d,
                'new_users_7d': new_users_7d,
                'recent_logins_7d': recent_logins_7d,
            },
            'subscriptions': {
                'active_subscriptions': active_subs,
                'subscription_rate': (active_subs / total_users * 100) if total_users > 0 else 0,
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch user analytics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def bulk_user_action(request):
    """Perform bulk actions on multiple users"""
    try:
        user_ids = request.data.get('user_ids', [])
        action = request.data.get('action')
        
        if not user_ids or not isinstance(user_ids, list):
            return Response({
                'error': 'user_ids must be a non-empty list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate action
        valid_actions = ['activate', 'deactivate']
        if action not in valid_actions:
            return Response({
                'error': f"Invalid action. Allowed: {', '.join(valid_actions)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get users
        users = User.objects.filter(id__in=user_ids)
        
        if not users.exists():
            return Response({
                'error': 'No users found with provided IDs'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Perform action
        updated_count = 0
        user_emails = []
        
        for user in users:
            if action == 'activate':
                user.is_active = True
            elif action == 'deactivate':
                user.is_active = False
            
            user.save()
            user_emails.append(user.email)
            updated_count += 1
        
        # Log bulk action
        AdminAction.log_action(
            admin_user=request.user,
            action=f'bulk_{action}',
            details={
                'affected_users': user_emails,
                'count': updated_count
            },
            request=request
        )
        
        return Response({
            'message': f'Successfully {action}d {updated_count} user(s)',
            'count': updated_count,
            'affected_users': user_emails
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to perform bulk action',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_user(request, user_id):
    """Delete a user account (hard delete)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Prevent deleting superusers
        if user.is_superuser:
            return Response({
                'error': 'Cannot delete superuser accounts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'error': 'Cannot delete your own account'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Gather information before deletion for audit log
        user_email = user.email
        
        # Get cascade deletion info
        cascade_info = {
            'email': user_email,
            'had_billing_profile': hasattr(user, 'billing_profile'),
            'subscriptions_count': 0,
            'oauth_providers_count': user.oauth_providers.count() if hasattr(user, 'oauth_providers') else 0,
        }
        
        if hasattr(user, 'billing_profile') and user.billing_profile:
            cascade_info['subscriptions_count'] = user.billing_profile.subscriptions.count()
        
        # Log deletion before it happens
        AdminAction.log_action(
            admin_user=request.user,
            action='delete',
            target_user=user,
            details=cascade_info,
            request=request
        )
        
        # Delete user (CASCADE will handle related objects)
        user.delete()
        
        return Response({
            'message': f'User {user_email} deleted successfully',
            'cascade_info': cascade_info
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to delete user',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_audit_log(request, user_id):
    """Get audit log for a specific user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Get all actions related to this user
        actions = AdminAction.objects.filter(
            Q(target_user=user) | Q(target_email=user.email)
        ).order_by('-created_at')[:50]  # Last 50 actions
        
        action_list = [
            {
                'id': str(action.id),
                'admin_email': action.admin_email,
                'action': action.action,
                'action_display': action.action_display,
                'details': action.details,
                'ip_address': action.ip_address,
                'created_at': action.created_at.isoformat(),
            }
            for action in actions
        ]
        
        return Response({
            'user_email': user.email,
            'actions': action_list,
            'total_actions': len(action_list)
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to fetch audit log',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_users_csv(request):
    """Export users to CSV with current filters applied"""
    try:
        # Get same filters as user_list
        search = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '')
        subscription_filter = request.GET.get('subscription', '')
        
        # Base queryset
        users = User.objects.select_related('billing_profile').annotate(
            subscriptions_count=Count('billing_profile__subscriptions', distinct=True),
            active_subscriptions_count=Count(
                'billing_profile__subscriptions', 
                filter=Q(
                    billing_profile__subscriptions__status='active',
                    billing_profile__subscriptions__end_date__gt=timezone.now()
                ),
                distinct=True
            )
        ).order_by('-created_at')
        
        # Apply search filter
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        # Apply status filters
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        elif status_filter == 'verified':
            users = users.filter(is_email_verified=True)
        elif status_filter == 'unverified':
            users = users.filter(is_email_verified=False)
        
        # Apply subscription filters
        if subscription_filter == 'has_subscription':
            users = users.filter(subscriptions_count__gt=0)
        elif subscription_filter == 'no_subscription':
            users = users.filter(subscriptions_count=0)
        elif subscription_filter == 'active_subscription':
            users = users.filter(active_subscriptions_count__gt=0)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Email',
            'Username',
            'First Name',
            'Last Name',
            'Display Name',
            'Active',
            'Email Verified',
            'Staff',
            'Superuser',
            'OAuth Provider',
            'Total Subscriptions',
            'Active Subscriptions',
            'Latest Subscription Plan',
            'Latest Subscription Status',
            'Latest Subscription End Date',
            'Registration Date',
            'Last Login',
        ])
        
        # Write user data
        for user in users:
            # Get OAuth provider
            oauth_provider = ''
            if user.oauth_providers.exists():
                oauth_provider = user.oauth_providers.first().provider
            
            # Get latest subscription info
            latest_sub_plan = ''
            latest_sub_status = ''
            latest_sub_end = ''
            
            if hasattr(user, 'billing_profile') and user.billing_profile:
                latest_sub = user.billing_profile.subscriptions.order_by('-created_at').first()
                if latest_sub:
                    latest_sub_plan = latest_sub.plan.name if latest_sub.plan else ''
                    latest_sub_status = latest_sub.status
                    latest_sub_end = latest_sub.end_date.strftime('%Y-%m-%d') if latest_sub.end_date else ''
            
            # Build display name
            full_name = f"{user.first_name} {user.last_name}".strip()
            display_name = full_name or user.username
            
            writer.writerow([
                user.email,
                user.username,
                user.first_name,
                user.last_name,
                display_name,
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_email_verified else 'No',
                'Yes' if user.is_staff else 'No',
                'Yes' if user.is_superuser else 'No',
                oauth_provider,
                user.subscriptions_count,
                user.active_subscriptions_count,
                latest_sub_plan,
                latest_sub_status,
                latest_sub_end,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            ])
        
        # Log the export
        AdminAction.log_action(
            admin_user=request.user,
            action='export_users',
            details={
                'filters': {
                    'search': search,
                    'status': status_filter,
                    'subscription': subscription_filter,
                },
                'total_exported': users.count()
            },
            request=request
        )
        
        return response
        
    except Exception as e:
        return Response({
            'error': 'Failed to export users',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_plans_list(request):
    """Get list of active subscription plans for filtering"""
    try:
        from subscriptions.models import SubscriptionPlan
        
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'name')
        
        plan_list = [
            {
                'slug': plan.slug,
                'name': plan.name,
                'billing_period': plan.billing_period,
            }
            for plan in plans
        ]
        
        return Response({
            'plans': plan_list
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch subscription plans',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)