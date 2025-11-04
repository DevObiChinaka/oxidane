# Mentorship Admin Views - Updated for DRF pattern
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .models import Subscription, SubscriptionPlan
from users.models import User
from users.permissions import IsAdmin

# Note: Mentorship is now handled through regular Subscription model (Phase 0.5)
# with a SubscriptionPlan that has mentorship features
# MentorshipPlan, MentorshipSubscription, and OneOnOneSession models have been deprecated

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def mentorship_subscription_list(request):
    """List all mentorship purchases with filtering"""
    try:
        # Get query parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        telegram_filter = request.GET.get('telegram_status', '')
        
        # Base queryset - all mentorship-related purchases
        subscriptions = Subscription.objects.filter(
            plan__slug__icontains='mentorship'
        ).select_related('billing_profile__user', 'plan').all()
        
        # Apply filters
        if search:
            subscriptions = subscriptions.filter(
                Q(billing_profile__user__email__icontains=search) |
                Q(billing_profile__user__first_name__icontains=search) |
                Q(billing_profile__user__last_name__icontains=search)
            )
        
        if status_filter:
            subscriptions = subscriptions.filter(status=status_filter)
            
        if telegram_filter:
            subscriptions = subscriptions.filter(telegram_status=telegram_filter)
        
        # Order by newest first
        subscriptions = subscriptions.order_by('-created_at')
        
        # Serialize data
        subscription_data = []
        for sub in subscriptions:
            # Mentorship is lifetime access
            is_active = sub.payment_status == 'verified'
            
            subscription_data.append({
                'id': str(sub.id),
                'user_email': sub.user.email,
                'user_name': f"{sub.user.first_name} {sub.user.last_name}".strip() or sub.user.username,
                'plan_name': 'Mentorship Program',
                'plan_type': 'mentorship',
                'amount_paid': float(sub.amount_paid),
                'currency': sub.currency,
                'payment_status': sub.payment_status,
                'subscription_status': 'active' if is_active else 'inactive',
                'subscription_start': sub.subscription_start.isoformat() if sub.subscription_start else sub.created_at.isoformat(),
                'subscription_end': None,  # Lifetime access
                'days_remaining': None,  # No expiration
                'telegram_username': sub.telegram_username or '',
                'telegram_status': sub.telegram_status,
                'sessions_used': 0,  # Not tracked in system
                'sessions_remaining': 0,  # Arranged offline
                'is_active': is_active,
                'created_at': sub.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'subscriptions': subscription_data,
            'count': len(subscription_data)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def mentorship_session_management(request):
    """
    Manage 1-on-1 mentorship sessions
    NOTE: Sessions are arranged offline and not tracked in the system currently.
    This endpoint returns empty data for frontend compatibility.
    """
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'sessions': [],
            'count': 0,
            'message': '1-on-1 sessions are arranged offline and not tracked in the system.'
        })
    
    elif request.method == 'POST':
        # Sessions are not managed in system
        return Response({
            'success': False,
            'error': '1-on-1 sessions are arranged offline. System management is not available.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def mentorship_analytics(request):
    """Get mentorship program analytics"""
    try:
        now = timezone.now()
        
        # Total mentorship purchases (active subscriptions)
        total_purchases = Subscription.objects.filter(
            plan__slug__icontains='mentorship',
            status='active'
        ).count()
        
        # Monthly revenue (current month)
        # TODO: Calculate from actual payment transactions when PaymentTransaction model is recreated
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_subs = Subscription.objects.filter(
            plan__slug__icontains='mentorship',
            start_date__gte=current_month_start,
            status='active'
        ).count()
        avg_price = SubscriptionPlan.objects.filter(
            slug__icontains='mentorship'
        ).aggregate(avg=Avg('base_price'))['avg'] or Decimal('0.00')
        monthly_revenue = Decimal(monthly_subs) * avg_price
        
        # Total revenue (all time estimate)
        total_revenue = Decimal(total_purchases) * avg_price
        
        # Telegram status distribution
        telegram_stats = list(
            Subscription.objects.filter(
                plan__slug__icontains='mentorship',
                status='active'
            )
            .values('telegram_status')
            .annotate(count=Count('id'))
        )
        
        # Recent purchases (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        recent_purchases = Subscription.objects.filter(
            plan__slug__icontains='mentorship',
            status='active',
            start_date__gte=thirty_days_ago
        ).count()
        
        return Response({
            'success': True,
            'analytics': {
                'total_purchases': total_purchases,
                'monthly_revenue': float(monthly_revenue),
                'total_revenue': float(total_revenue),
                'recent_purchases_30d': recent_purchases,
                'telegram_stats': telegram_stats,
                # Session stats not applicable (arranged offline)
                'total_sessions': 0,
                'completed_sessions': 0,
                'upcoming_sessions': 0,
                'physical_sessions_pending_notification': 0,
                'plan_distribution': [
                    {'name': 'Mentorship Program', 'count': total_purchases}
                ],
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def extend_subscription(request, subscription_id):
    """
    Admin note: Mentorship provides lifetime access
    This endpoint is kept for compatibility but returns appropriate message
    """
    try:
        subscription = get_object_or_404(Subscription, id=subscription_id, plan__slug__icontains='mentorship')
        
        return Response({
            'success': False,
            'error': 'Mentorship provides lifetime access and does not need extension. User already has permanent access to all courses.'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)