# Mentorship Admin Views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .models import (
    MentorshipPlan, MentorshipSubscription, OneOnOneSession
)
from users.models import User
from users.admin_auth import admin_required

@api_view(['GET'])
@admin_required
def mentorship_subscription_list(request):
        try:
            # Get query parameters
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 20))
            search = request.GET.get('search', '').strip()
            status_filter = request.GET.get('status', 'all')
            plan_filter = request.GET.get('plan_type', 'all')
            
            # Base queryset
            subscriptions = MentorshipSubscription.objects.select_related(
                'user', 'mentorship_plan'
            ).all()
            
            # Apply filters
            if search:
                subscriptions = subscriptions.filter(
                    Q(user__email__icontains=search) |
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search) |
                    Q(paystack_reference__icontains=search) |
                    Q(telegram_username__icontains=search)
                )
            
            if status_filter != 'all':
                if status_filter == 'active':
                    subscriptions = subscriptions.filter(
                        subscription_status='active',
                        payment_status='verified',
                        subscription_end__gte=timezone.now()
                    )
                elif status_filter == 'expired':
                    subscriptions = subscriptions.filter(
                        Q(subscription_status='expired') |
                        Q(subscription_end__lt=timezone.now())
                    )
                else:
                    subscriptions = subscriptions.filter(subscription_status=status_filter)
            
            if plan_filter != 'all':
                subscriptions = subscriptions.filter(mentorship_plan__plan_type=plan_filter)
            
            # Pagination
            total_count = subscriptions.count()
            start = (page - 1) * per_page
            end = start + per_page
            subscriptions = subscriptions[start:end]
            
            # Serialize data
            subscription_data = []
            for sub in subscriptions:
                subscription_data.append({
                    'id': str(sub.id),
                    'user_email': sub.user.email,
                    'user_name': f"{sub.user.first_name} {sub.user.last_name}".strip(),
                    'plan_name': sub.mentorship_plan.name,
                    'plan_type': sub.mentorship_plan.plan_type,
                    'amount_paid': float(sub.amount_paid),
                    'currency': sub.currency,
                    'payment_status': sub.payment_status,
                    'subscription_status': sub.subscription_status,
                    'subscription_start': sub.subscription_start.isoformat() if sub.subscription_start else None,
                    'subscription_end': sub.subscription_end.isoformat() if sub.subscription_end else None,
                    'days_remaining': sub.days_remaining,
                    'telegram_username': sub.telegram_username,
                    'telegram_status': sub.telegram_status,
                    'sessions_used': sub.sessions_used,
                    'sessions_remaining': sub.sessions_remaining,
                    'is_active': sub.is_active,
                    'created_at': sub.created_at.isoformat(),
                })
            
            return JsonResponse({
                'success': True,
                'subscriptions': subscription_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to fetch mentorship subscriptions: {str(e)}'
            }, status=500)

class OneOnOneSessionManagementView(View):
    """Manage 1-on-1 mentorship sessions"""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        """List all 1-on-1 sessions"""
        try:
            # Get query parameters
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 20))
            session_type = request.GET.get('session_type', 'all')
            status_filter = request.GET.get('status', 'all')
            upcoming_only = request.GET.get('upcoming_only', 'false').lower() == 'true'
            
            # Base queryset
            sessions = OneOnOneSession.objects.select_related(
                'mentorship_subscription__user',
                'mentorship_subscription__mentorship_plan'
            ).all()
            
            # Apply filters
            if session_type != 'all':
                sessions = sessions.filter(session_type=session_type)
            
            if status_filter != 'all':
                sessions = sessions.filter(status=status_filter)
            
            if upcoming_only:
                sessions = sessions.filter(
                    scheduled_datetime__gte=timezone.now(),
                    status='scheduled'
                )
            
            # Pagination
            total_count = sessions.count()
            start = (page - 1) * per_page
            end = start + per_page
            sessions = sessions[start:end]
            
            # Serialize data
            session_data = []
            for session in sessions:
                session_data.append({
                    'id': str(session.id),
                    'user_email': session.mentorship_subscription.user.email,
                    'user_name': f"{session.mentorship_subscription.user.first_name} {session.mentorship_subscription.user.last_name}".strip(),
                    'session_type': session.session_type,
                    'scheduled_datetime': session.scheduled_datetime.isoformat(),
                    'duration_minutes': session.duration_minutes,
                    'status': session.status,
                    'meeting_link': session.meeting_link,
                    'physical_location': session.physical_location,
                    'phone_number': session.phone_number,
                    'admin_notified': session.admin_notified,
                    'session_notes': session.session_notes,
                    'created_at': session.created_at.isoformat(),
                    'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                })
            
            return JsonResponse({
                'success': True,
                'sessions': session_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to fetch sessions: {str(e)}'
            }, status=500)
    
    def post(self, request):
        """Create new 1-on-1 session"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['mentorship_subscription_id', 'session_type', 'scheduled_datetime']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Get mentorship subscription
            mentorship_subscription = get_object_or_404(
                MentorshipSubscription, 
                id=data['mentorship_subscription_id']
            )
            
            # Check if user has sessions remaining
            if mentorship_subscription.sessions_remaining <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'No sessions remaining for this user'
                }, status=400)
            
            # Parse scheduled datetime
            scheduled_datetime = datetime.fromisoformat(data['scheduled_datetime'].replace('Z', '+00:00'))
            
            # Create session
            session = OneOnOneSession.objects.create(
                mentorship_subscription=mentorship_subscription,
                session_type=data['session_type'],
                scheduled_datetime=scheduled_datetime,
                duration_minutes=data.get('duration_minutes', 60),
                meeting_link=data.get('meeting_link', ''),
                physical_location=data.get('physical_location', ''),
                phone_number=data.get('phone_number', ''),
                admin_notes=data.get('admin_notes', '')
            )
            
            # Use a session from the subscription
            mentorship_subscription.use_session()
            
            # Send admin notification if physical session
            if session.session_type == 'physical':
                session.send_admin_notification()
            
            return JsonResponse({
                'success': True,
                'session_id': str(session.id),
                'message': 'Session created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to create session: {str(e)}'
            }, status=500)
    
    def put(self, request, session_id):
        """Update session status and notes"""
        try:
            data = json.loads(request.body)
            session = get_object_or_404(OneOnOneSession, id=session_id)
            
            # Update allowed fields
            if 'status' in data:
                session.status = data['status']
                if data['status'] == 'completed':
                    session.completed_at = timezone.now()
            
            if 'session_notes' in data:
                session.session_notes = data['session_notes']
            
            if 'admin_notes' in data:
                session.admin_notes = data['admin_notes']
            
            session.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Session updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to update session: {str(e)}'
            }, status=500)

class MentorshipAnalyticsView(View):
    """Mentorship program analytics"""
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        try:
            # Date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            # Active subscriptions
            active_subscriptions = MentorshipSubscription.objects.filter(
                subscription_status='active',
                payment_status='verified',
                subscription_end__gte=timezone.now()
            ).count()
            
            # Revenue this month
            monthly_revenue = MentorshipSubscription.objects.filter(
                payment_verified_at__gte=timezone.now().replace(day=1),
                payment_status='verified'
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            
            # Sessions stats
            total_sessions = OneOnOneSession.objects.count()
            completed_sessions = OneOnOneSession.objects.filter(status='completed').count()
            upcoming_sessions = OneOnOneSession.objects.filter(
                scheduled_datetime__gte=timezone.now(),
                status='scheduled'
            ).count()
            
            # Physical sessions requiring admin notification
            physical_sessions_pending = OneOnOneSession.objects.filter(
                session_type='physical',
                status='scheduled',
                admin_notified=False,
                scheduled_datetime__gte=timezone.now()
            ).count()
            
            # Plan distribution
            plan_distribution = MentorshipSubscription.objects.filter(
                subscription_status='active',
                payment_status='verified'
            ).values('mentorship_plan__name').annotate(
                count=Count('id')
            )
            
            # Telegram status distribution
            telegram_stats = MentorshipSubscription.objects.filter(
                subscription_status='active'
            ).values('telegram_status').annotate(
                count=Count('id')
            )
            
            return JsonResponse({
                'success': True,
                'analytics': {
                    'active_subscriptions': active_subscriptions,
                    'monthly_revenue': float(monthly_revenue),
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'upcoming_sessions': upcoming_sessions,
                    'physical_sessions_pending_notification': physical_sessions_pending,
                    'plan_distribution': list(plan_distribution),
                    'telegram_stats': list(telegram_stats)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to fetch analytics: {str(e)}'
            }, status=500)

# Note: Telegram task management will be handled by the existing telegram queue system

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def extend_mentorship_subscription(request, subscription_id):
    """Extend a mentorship subscription"""
    try:
        data = json.loads(request.body)
        subscription = get_object_or_404(MentorshipSubscription, id=subscription_id)
        
        extend_days = int(data.get('extend_days', 0))
        reason = data.get('reason', 'Admin extension')
        
        if extend_days <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid extension days'
            }, status=400)
        
        # Extend subscription
        if subscription.subscription_end:
            new_end_date = subscription.subscription_end + timedelta(days=extend_days)
        else:
            new_end_date = timezone.now() + timedelta(days=extend_days)
        
        old_end_date = subscription.subscription_end
        subscription.subscription_end = new_end_date
        
        # Update telegram removal schedule
        subscription.telegram_removal_scheduled = new_end_date + timedelta(days=1)
        
        # Extend premium course access
        from courses.models import CourseAccess
        CourseAccess.objects.filter(
            user=subscription.user,
            access_expires_at=old_end_date
        ).update(access_expires_at=new_end_date)
        
        subscription.admin_notes = f"{subscription.admin_notes}\n[{timezone.now()}] Extended by {extend_days} days. Reason: {reason}"
        subscription.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Subscription extended by {extend_days} days',
            'new_end_date': new_end_date.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to extend subscription: {str(e)}'
        }, status=500)