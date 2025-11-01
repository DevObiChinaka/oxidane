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
from datetime import timedelta
import json

from subscriptions.models import SignalSubscription
from courses.models import Course
from .permissions import IsAdmin

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
        users = User.objects.select_related().annotate(
            signal_subscriptions_count=Count('signal_subscriptions', distinct=True),
            active_signal_subscriptions_count=Count(
                'signal_subscriptions', 
                filter=Q(
                    signal_subscriptions__payment_status='verified',
                    signal_subscriptions__subscription_end__gt=timezone.now()
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
        if subscription_filter == 'has_signals':
            users = users.filter(active_signal_subscriptions_count__gt=0)
        elif subscription_filter == 'has_courses':
            # Add course enrollment logic when implemented
            pass
        elif subscription_filter == 'none':
            users = users.filter(
                signal_subscriptions_count=0
                # Add course enrollment count when implemented
            )
        
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
            latest_signal_sub = user.signal_subscriptions.filter(
                payment_status='verified'
            ).order_by('-created_at').first()
            
            # Get OAuth provider info for display names
            oauth_provider = user.oauth_providers.first() if hasattr(user, 'oauth_providers') else None
            
            # Determine display name priority: 
            # 1. User's first/last name if set
            # 2. OAuth data if available 
            # 3. Username as fallback
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            
            # If no names set and OAuth exists, check if we have provider data
            if not (first_name or last_name) and oauth_provider:
                # For Google OAuth, we might have stored name data
                # This would depend on how OAuth was implemented
                pass
            
            # Create full name with fallback logic
            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                # Use email prefix as fallback (before @)
                email_prefix = user.email.split('@')[0] if user.email else user.username
                full_name = email_prefix.replace('.', ' ').replace('_', ' ').title()
            
            user_data.append({
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'display_name': full_name or user.username,  # Best display name
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
                'signal_subscriptions_count': user.signal_subscriptions_count,
                'active_signal_subscriptions_count': user.active_signal_subscriptions_count,
                'latest_signal_subscription': {
                    'plan_type': latest_signal_sub.plan_type if latest_signal_sub else None,
                    'subscription_end': latest_signal_sub.subscription_end.isoformat() if latest_signal_sub and latest_signal_sub.subscription_end else None,
                    'telegram_status': latest_signal_sub.telegram_status if latest_signal_sub else None,
                } if latest_signal_sub else None,
                
                # Quick stats
                'days_since_registration': (timezone.now() - user.created_at).days,
                'days_since_last_login': (timezone.now() - user.last_login).days if user.last_login else None,
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
        user = User.objects.select_related().prefetch_related(
            'signal_subscriptions',
            'oauth_providers'
        ).get(id=user_id)
        
        # Get subscription history
        signal_subscriptions = user.signal_subscriptions.order_by('-created_at')
        
        # Calculate user metrics
        total_paid = sum(
            sub.amount_paid for sub in signal_subscriptions 
            if sub.payment_status == 'verified'
        )
        
        # Handle display names similar to user list
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        
        # Create full name with fallback logic
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            # Use email prefix as fallback (before @)
            email_prefix = user.email.split('@')[0] if user.email else user.username
            full_name = email_prefix.replace('.', ' ').replace('_', ' ').title()
        
        display_name = full_name or user.username

        # Debug logging
        print(f"🔍 User Detail Debug for {user.email}:")
        print(f"  first_name: '{first_name}'")
        print(f"  last_name: '{last_name}'")
        print(f"  full_name: '{full_name}'")
        print(f"  display_name: '{display_name}'")
        print(f"  username: '{user.username}'")
        print(f"  created_at: {user.created_at}")

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name,
                'display_name': display_name,
                'avatar': user.avatar,
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
                    'plan_type': sub.plan_type,
                    'amount_paid': float(sub.amount_paid),
                    'currency': sub.currency,
                    'payment_status': sub.payment_status,
                    'telegram_username': sub.telegram_username,
                    'telegram_status': sub.telegram_status,
                    'subscription_start': sub.subscription_start.isoformat() if sub.subscription_start else None,
                    'subscription_end': sub.subscription_end.isoformat() if sub.subscription_end else None,
                    'created_at': sub.created_at.isoformat(),
                    'paystack_reference': sub.paystack_reference,
                } for sub in signal_subscriptions
            ],
            'oauth_providers': [
                {
                    'provider': oauth.provider,
                    'provider_user_id': oauth.provider_user_id,
                    'created_at': oauth.created_at.isoformat(),
                } for oauth in user.oauth_providers.all()
            ],
            'metrics': {
                'days_since_registration': (timezone.now() - user.created_at).days,
                'days_since_last_login': (timezone.now() - user.last_login).days if user.last_login else None,
                'total_subscriptions': signal_subscriptions.count(),
                'active_subscriptions': signal_subscriptions.filter(
                    payment_status='verified',
                    subscription_end__gt=timezone.now()
                ).count(),
                'total_paid': float(total_paid),
                'has_oauth': user.oauth_providers.exists(),
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
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
            
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            message = f"User {user.email} deactivated successfully"
            
        elif action == 'verify_email':
            user.is_email_verified = True
            user.save()
            message = f"Email verified for {user.email}"
            
        elif action == 'make_staff':
            user.is_staff = True
            user.save()
            message = f"{user.email} granted staff privileges"
            
        elif action == 'remove_staff':
            user.is_staff = False
            user.save()
            message = f"Staff privileges removed for {user.email}"
            
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
        
        # Active subscriptions
        active_signal_subs = SignalSubscription.objects.filter(
            payment_status='verified',
            subscription_end__gt=now
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
                'active_signal_subscriptions': active_signal_subs,
                'subscription_rate': (active_signal_subs / total_users * 100) if total_users > 0 else 0,
            }
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch user analytics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)