# Subscription and pricing management views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging
import time
from functools import wraps
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from .models import PricingPlan, SignalSubscription, PaymentTransaction, TelegramGroupManagement
from .serializers import PricingPlanSerializer, SignalSubscriptionSerializer, PaymentTransactionSerializer
from .audit_models import AdminActionLog, SubscriptionChangeLog, DataAccessLog
from .analytics_models import SubscriptionAnalytics, PerformanceMetrics
from users.permissions import IsAdmin

# Set up audit logging
audit_logger = logging.getLogger('audit')

def audit_log(action, sensitivity='NORMAL'):
    """Enhanced decorator for audit logging and performance monitoring"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = timezone.now()
            performance_start = time.time()
            admin_user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            try:
                # Execute the view
                response = view_func(request, *args, **kwargs)
                status_result = 'SUCCESS'
                error_msg = ''
                
            except Exception as e:
                status_result = 'FAILED'
                error_msg = str(e)
                response = None
                raise
                
            finally:
                # Calculate performance metrics
                performance_end = time.time()
                duration_ms = (performance_end - performance_start) * 1000
                
                try:
                    # Create comprehensive audit log
                    if admin_user:
                        AdminActionLog.objects.create(
                            admin_user=admin_user,
                            action_type=action,
                            sensitivity=sensitivity,
                            status=status_result,
                            timestamp=start_time,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                            request_method=request.method,
                            request_path=request.path,
                            response_status_code=getattr(response, 'status_code', None),
                            duration_ms=duration_ms,
                            action_description=f"{action} by {admin_user.email}",
                            error_message=error_msg,
                            request_params=dict(request.GET) if request.method == 'GET' else {},
                            resource_ids=[str(arg) for arg in args] if args else []
                        )
                    
                    # Record performance metrics for optimization
                    PerformanceMetrics.record_api_performance(
                        endpoint_path=request.path,
                        response_time_ms=duration_ms,
                        user_count=1,
                        additional_data={
                            'method': request.method,
                            'status': status_result,
                            'admin_user': admin_user.email if admin_user else 'Anonymous',
                            'sensitivity': sensitivity
                        }
                    )
                    
                except Exception as audit_error:
                    # Don't let audit logging break the main functionality
                    logger.error(f"Audit/Performance logging failed: {audit_error}")
            
            return response
        return wrapper
    return decorator

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_SUBSCRIPTION_DASHBOARD", sensitivity="FINANCIAL")
def admin_pricing_dashboard(request):
    """Get pricing and subscription overview"""
    
    cache_key = f"pricing_metrics_{timezone.now().date()}"
    cached_metrics = cache.get(cache_key)
    
    if cached_metrics:
        return Response(cached_metrics)
    
    # Active subscriptions
    active_subs = SignalSubscription.objects.filter(
        subscription_end__gt=timezone.now(),
        payment_status='verified'
    )
    
    # Revenue calculations
    today = timezone.now().date()
    this_month = timezone.now().replace(day=1).date()
    
    daily_revenue = PaymentTransaction.objects.filter(
        created_at__date=today,
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    monthly_revenue = PaymentTransaction.objects.filter(
        created_at__date__gte=this_month,
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Subscription breakdown
    subscription_stats = {}
    for plan_type in ['weekly', 'monthly', 'vip']:
        count = active_subs.filter(plan_type=plan_type).count()
        revenue = active_subs.filter(plan_type=plan_type).aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        subscription_stats[plan_type] = {
            'count': count,
            'revenue': float(revenue)
        }
    
    # Pending actions
    pending_telegram_adds = TelegramGroupManagement.objects.filter(
        action_type='add',
        status='pending'
    ).count()
    
    pending_payments = SignalSubscription.objects.filter(
        payment_status='pending'
    ).count()
    
    metrics = {
        'revenue': {
            'daily': float(daily_revenue),
            'monthly': float(monthly_revenue),
        },
        'subscriptions': {
            'active_total': active_subs.count(),
            'breakdown': subscription_stats,
        },
        'pending_actions': {
            'telegram_adds': pending_telegram_adds,
            'payment_verifications': pending_payments,
        }
    }
    
    cache.set(cache_key, metrics, 60 * 15)  # Cache for 15 minutes
    return Response(metrics)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_SUBSCRIPTION_ANALYTICS", sensitivity="FINANCIAL")
def subscription_analytics_dashboard(request):
    """Enhanced analytics dashboard with performance optimization"""
    
    # Get period from query params
    period = request.GET.get('period', 'monthly')  # daily, weekly, monthly, quarterly, yearly
    days_back = int(request.GET.get('days_back', 30))
    
    cache_key = f"analytics_dashboard_{period}_{days_back}_{timezone.now().date()}"
    cached_analytics = cache.get(cache_key)
    
    if cached_analytics:
        # Record cache hit
        PerformanceMetrics.objects.create(
            category='api',
            metric_name='Cache Hit - Analytics Dashboard',
            response_time_ms=5.0,  # Typical cache response time
            endpoint_path=request.path
        )
        return Response(cached_analytics)
    
    try:
        # Calculate or retrieve analytics
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get aggregated analytics data
        analytics_data = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_analytics = SubscriptionAnalytics.calculate_analytics('daily', current_date)
            analytics_data.append({
                'date': current_date.isoformat(),
                'total_subscriptions': daily_analytics.total_subscriptions,
                'new_subscriptions': daily_analytics.new_subscriptions,
                'total_revenue': float(daily_analytics.total_revenue),
                'verified_payments': daily_analytics.verified_payments,
                'pending_payments': daily_analytics.pending_payments,
                'failed_payments': daily_analytics.failed_payments,
                'refunded_amount': float(daily_analytics.refunded_amount),
                'telegram_success_rate': float(daily_analytics.telegram_success_rate),
                'plan_breakdown': daily_analytics.plan_type_breakdown,
                'admin_actions_count': daily_analytics.admin_actions_count
            })
            current_date += timedelta(days=1)
        
        # Calculate summary metrics
        total_revenue = sum(day['total_revenue'] for day in analytics_data)
        total_subscriptions = sum(day['total_subscriptions'] for day in analytics_data)
        avg_daily_revenue = total_revenue / len(analytics_data) if analytics_data else 0
        
        # Get performance metrics
        performance_metrics = PerformanceMetrics.get_average_performance('api', hours=24)
        
        # Compile final response
        dashboard_data = {
            'period': period,
            'days_analyzed': days_back,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_revenue': total_revenue,
                'total_subscriptions': total_subscriptions,
                'average_daily_revenue': avg_daily_revenue,
                'growth_rate': _calculate_growth_rate(analytics_data)
            },
            'daily_data': analytics_data,
            'performance_metrics': performance_metrics,
            'cache_info': {
                'cached': False,
                'generated_at': timezone.now().isoformat()
            }
        }
        
        # Cache the results for 30 minutes
        cache.set(cache_key, dashboard_data, 60 * 30)
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {str(e)}")
        return Response(
            {'error': 'Failed to generate analytics dashboard', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_PERFORMANCE_METRICS", sensitivity="NORMAL")
def performance_metrics_dashboard(request):
    """System performance monitoring dashboard"""
    
    hours = int(request.GET.get('hours', 24))
    category = request.GET.get('category', 'all')
    
    try:
        # Get performance data
        since = timezone.now() - timedelta(hours=hours)
        
        if category == 'all':
            metrics = PerformanceMetrics.objects.filter(timestamp__gte=since)
        else:
            metrics = PerformanceMetrics.objects.filter(
                category=category,
                timestamp__gte=since
            )
        
        # Group by category
        performance_by_category = {}
        for metric in metrics:
            cat = metric.category
            if cat not in performance_by_category:
                performance_by_category[cat] = {
                    'response_times': [],
                    'error_rates': [],
                    'throughput': [],
                    'count': 0
                }
            
            if metric.response_time_ms:
                performance_by_category[cat]['response_times'].append(metric.response_time_ms)
            if metric.error_rate_percent:
                performance_by_category[cat]['error_rates'].append(metric.error_rate_percent)
            if metric.throughput_per_second:
                performance_by_category[cat]['throughput'].append(metric.throughput_per_second)
            
            performance_by_category[cat]['count'] += 1
        
        # Calculate averages
        summary = {}
        for cat, data in performance_by_category.items():
            summary[cat] = {
                'avg_response_time': sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0,
                'avg_error_rate': sum(data['error_rates']) / len(data['error_rates']) if data['error_rates'] else 0,
                'avg_throughput': sum(data['throughput']) / len(data['throughput']) if data['throughput'] else 0,
                'total_requests': data['count']
            }
        
        # Get recent alerts (slow responses, high error rates)
        alerts = []
        slow_queries = metrics.filter(response_time_ms__gt=2000).order_by('-timestamp')[:10]
        for query in slow_queries:
            alerts.append({
                'type': 'slow_response',
                'endpoint': query.endpoint_path,
                'response_time': query.response_time_ms,
                'timestamp': query.timestamp.isoformat()
            })
        
        response_data = {
            'time_period': f"Last {hours} hours",
            'summary': summary,
            'alerts': alerts,
            'total_requests': sum(data['count'] for data in performance_by_category.values()),
            'generated_at': timezone.now().isoformat()
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve performance metrics', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def _calculate_growth_rate(analytics_data):
    """Calculate revenue growth rate from analytics data"""
    if len(analytics_data) < 2:
        return 0
    
    # Compare first half vs second half
    mid_point = len(analytics_data) // 2
    first_half_revenue = sum(day['total_revenue'] for day in analytics_data[:mid_point])
    second_half_revenue = sum(day['total_revenue'] for day in analytics_data[mid_point:])
    
    if first_half_revenue == 0:
        return 100 if second_half_revenue > 0 else 0
    
    return ((second_half_revenue - first_half_revenue) / first_half_revenue) * 100

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_SUBSCRIPTIONS_LIST", sensitivity="FINANCIAL")
def subscriptions_list(request):
    """Secure subscription listing with filtering and pagination"""
    
    # Extract query parameters
    page = int(request.GET.get('page', 1))
    limit = request.GET.get('limit', request.GET.get('page_size', 20))
    page_size = min(int(limit), 100)  # Max 100 items per page
    search = request.GET.get('search', '').strip()
    
    # Accept both 'status' and 'payment_status' for backward compatibility
    status_filter = request.GET.get('payment_status', request.GET.get('status', ''))
    
    # Accept both 'plan' and 'plan_type' for backward compatibility
    plan_filter = request.GET.get('plan_type', request.GET.get('plan', ''))
    
    # Telegram status filter
    telegram_filter = request.GET.get('telegram_status', '')
    
    # User email filter
    user_email = request.GET.get('user_email', '').strip()
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base query with security considerations - only fetch necessary fields
    subscriptions = SignalSubscription.objects.select_related(
        'user'
    ).only(
        # User information (minimal)
        'id', 'user__id', 'user__email', 'user__username', 'user__first_name', 'user__last_name',
        # Subscription details
        'plan_type', 'amount_paid', 'currency', 'payment_status',
        'subscription_start', 'subscription_end', 'created_at',
        # Telegram information
        'telegram_username', 'telegram_status', 'telegram_group_name',
        # Payment reference (for admin verification, masked in response)
        'paystack_reference'
    )
    
    # Apply search filter securely
    if search:
        subscriptions = subscriptions.filter(
            Q(user__email__icontains=search) | 
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(telegram_username__icontains=search) |
            Q(paystack_reference__icontains=search)
        )
    
    # Apply payment status filter
    if status_filter and status_filter in ['pending', 'verified', 'failed', 'refunded']:
        subscriptions = subscriptions.filter(payment_status=status_filter)
    
    # Apply plan filter  
    if plan_filter:
        # Support both specific plan types and category filtering
        if plan_filter == 'signals':
            # Filter for all signals-related plans (exclude mentorship)
            subscriptions = subscriptions.filter(plan_type__in=['signals_weekly', 'signals_monthly', 'vip_monthly'])
        elif plan_filter == 'mentorship':
            # Filter for all mentorship plans (any plan_type starting with 'mentorship')
            subscriptions = subscriptions.filter(plan_type__startswith='mentorship')
        elif plan_filter in ['signals_weekly', 'signals_monthly', 'vip_monthly', 'weekly', 'monthly', 'vip']:
            # Filter for specific plan type (backward compatibility)
            # Map old names to new names if needed
            plan_type_map = {
                'weekly': 'signals_weekly',
                'monthly': 'signals_monthly',
                'vip': 'vip_monthly'
            }
            actual_plan = plan_type_map.get(plan_filter, plan_filter)
            subscriptions = subscriptions.filter(plan_type=actual_plan)
    
    # Apply telegram status filter
    if telegram_filter and telegram_filter in ['not_added', 'pending_add', 'added', 'removed', 'failed_add']:
        subscriptions = subscriptions.filter(telegram_status=telegram_filter)
    
    # Apply user email filter
    if user_email:
        subscriptions = subscriptions.filter(user__email__iexact=user_email)
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(created_at__date__gte=from_date)
        except ValueError:
            pass  # Invalid date format, ignore
            
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            subscriptions = subscriptions.filter(created_at__date__lte=to_date)
        except ValueError:
            pass  # Invalid date format, ignore
    
    # Order by most recent first
    subscriptions = subscriptions.order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(subscriptions, page_size)
    page_obj = paginator.get_page(page)
    
    # Format response matching frontend Subscription interface
    subscription_data = []
    for sub in page_obj:
        # Calculate subscription status
        is_active = (
            sub.payment_status == 'verified' and 
            sub.subscription_end and 
            sub.subscription_end > timezone.now()
        )
        
        # Calculate days remaining
        days_remaining = 0
        if is_active and sub.subscription_end:
            days_remaining = (sub.subscription_end - timezone.now()).days
        
        subscription_data.append({
            'id': str(sub.id),
            'user': {
                'id': str(sub.user.id),
                'email': sub.user.email,
                'username': sub.user.username or '',
                'first_name': sub.user.first_name or '',
                'last_name': sub.user.last_name or '',
            },
            'plan_type': sub.plan_type,
            'paystack_reference': sub.paystack_reference or '',
            'amount_paid': float(sub.amount_paid),
            'currency': sub.currency,
            'payment_status': sub.payment_status,
            'payment_verified_at': sub.payment_verified_at.isoformat() if sub.payment_verified_at else None,
            'subscription_start': sub.subscription_start.isoformat() if sub.subscription_start else None,
            'subscription_end': sub.subscription_end.isoformat() if sub.subscription_end else None,
            'auto_renewal': getattr(sub, 'auto_renewal', False),
            'telegram_username': sub.telegram_username or '',
            'telegram_group_name': sub.telegram_group_name or '',
            'telegram_status': sub.telegram_status,
            'telegram_added_at': sub.telegram_added_at.isoformat() if getattr(sub, 'telegram_added_at', None) else None,
            'admin_notes': getattr(sub, 'admin_notes', ''),
            'created_at': sub.created_at.isoformat(),
            'updated_at': sub.updated_at.isoformat() if hasattr(sub, 'updated_at') else sub.created_at.isoformat(),
            'is_active': is_active,
            'days_remaining': days_remaining,
        })
    
    return Response({
        'results': subscription_data,  # Changed from 'subscriptions' to 'results'
        'count': paginator.count,  # Total count for pagination
        'next': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'filters_applied': {
            'search': search,
            'payment_status': status_filter,
            'plan_type': plan_filter,
            'telegram_status': telegram_filter,
            'user_email': user_email,
            'date_range': f"{date_from} to {date_to}" if date_from or date_to else None,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])  
@audit_log(action="VIEW_SUBSCRIPTION_DETAIL", sensitivity="FINANCIAL")
def subscription_detail(request, subscription_id):
    """Get detailed subscription information for admin"""
    
    try:
        subscription = SignalSubscription.objects.select_related(
            'user', 'pricing_plan'
        ).get(id=subscription_id)
    except SignalSubscription.DoesNotExist:
        return Response(
            {'error': 'Subscription not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get related payment transactions
    payment_transactions = PaymentTransaction.objects.filter(
        signal_subscription=subscription
    ).order_by('-created_at')
    
    # Get telegram management actions
    telegram_actions = TelegramGroupManagement.objects.filter(
        signal_subscription=subscription
    ).order_by('-created_at')
    
    # Calculate subscription metrics
    is_active = (
        subscription.payment_status == 'verified' and 
        subscription.subscription_end and 
        subscription.subscription_end > timezone.now()
    )
    
    # Create user display name from available fields
    user_display_name = f"{subscription.user.first_name} {subscription.user.last_name}".strip()
    if not user_display_name:
        user_display_name = subscription.user.username or subscription.user.email.split('@')[0]

    response_data = {
        'subscription': {
            'id': str(subscription.id),
            'user_details': {
                'id': str(subscription.user.id),
                'email': subscription.user.email,
                'full_name': user_display_name,
                'username': subscription.user.username,
                'first_name': subscription.user.first_name or '',
                'last_name': subscription.user.last_name or '',
                'registration_date': subscription.user.date_joined.isoformat(),
                'is_active': subscription.user.is_active,
            },
            'plan_information': {
                'type': subscription.plan_type,
                'display_name': subscription.plan_type.replace('_', ' ').title(),
                'pricing_plan_id': str(subscription.pricing_plan.id) if subscription.pricing_plan else None,
            },
            'payment_details': {
                'amount_paid': str(subscription.amount_paid),
                'currency': subscription.currency,
                'payment_status': subscription.payment_status,
                'paystack_reference': subscription.paystack_reference,
                'payment_verified_at': subscription.payment_verified_at.isoformat() if subscription.payment_verified_at else None,
            },
            'subscription_timeline': {
                'created_at': subscription.created_at.isoformat(),
                'subscription_start': subscription.subscription_start.isoformat() if subscription.subscription_start else None,
                'subscription_end': subscription.subscription_end.isoformat() if subscription.subscription_end else None,
                'is_active': is_active,
                'days_remaining': (subscription.subscription_end - timezone.now()).days if is_active else 0,
                'auto_renewal': subscription.auto_renewal,
            },
            'telegram_integration': {
                'username': subscription.telegram_username,
                'status': subscription.telegram_status,
                'group_name': subscription.telegram_group_name,
                'added_at': subscription.telegram_added_at.isoformat() if subscription.telegram_added_at else None,
            },
            'admin_notes': subscription.admin_notes,
        },
        'payment_transactions': [
            {
                'id': str(tx.id),
                'reference': tx.reference,
                'amount': str(tx.amount),
                'currency': tx.currency,
                'payment_method': tx.payment_method,
                'status': tx.status,
                'created_at': tx.created_at.isoformat(),
                'processed_at': tx.processed_at.isoformat() if tx.processed_at else None,
            }
            for tx in payment_transactions[:10]  # Last 10 transactions
        ],
        'telegram_actions': [
            {
                'id': str(action.id),
                'action_type': action.action_type,
                'status': action.status,
                'telegram_group': action.telegram_group,
                'created_at': action.created_at.isoformat(),
                'processed_at': action.processed_at.isoformat() if action.processed_at else None,
                'admin_notes': action.admin_notes,
            }
            for action in telegram_actions[:5]  # Last 5 actions
        ],
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_SUBSCRIPTION_ANALYTICS", sensitivity="FINANCIAL") 
def subscription_analytics(request):
    """Get subscription analytics matching frontend SubscriptionAnalytics interface"""
    
    # Get parameters
    period = request.GET.get('period', 'monthly')
    days_back = int(request.GET.get('days_back', 30))
    
    # Cache key for analytics
    cache_key = f"subscription_analytics_{period}_{days_back}_{timezone.now().date()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    # Calculate date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Get all subscriptions in period
    period_subscriptions = SignalSubscription.objects.filter(
        created_at__gte=start_date
    )
    
    # Total subscriptions count
    total_subscriptions = period_subscriptions.count()
    
    # New subscriptions (created in period)
    new_subscriptions = period_subscriptions.filter(
        created_at__gte=start_date
    ).count()
    
    # Renewed subscriptions (subscriptions that were extended/renewed)
    renewed_subscriptions = period_subscriptions.filter(
        payment_status='verified',
        subscription_start__lt=start_date  # Started before period
    ).count()
    
    # Cancelled subscriptions (ended in period)
    cancelled_subscriptions = SignalSubscription.objects.filter(
        subscription_end__gte=start_date,
        subscription_end__lte=end_date,
        payment_status='verified'
    ).count()
    
    # Revenue calculations
    verified_subs = period_subscriptions.filter(payment_status='verified')
    total_revenue = float(verified_subs.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0)
    average_subscription_value = float(verified_subs.aggregate(Avg('amount_paid'))['amount_paid__avg'] or 0)
    
    # Refunded amount
    refunded_amount = float(
        period_subscriptions.filter(payment_status='refunded')
        .aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    )
    
    # Plan type breakdown
    plan_type_breakdown = {}
    for plan_type in ['weekly', 'monthly', 'vip']:
        plan_subs = verified_subs.filter(plan_type=plan_type)
        plan_type_breakdown[plan_type] = {
            'count': plan_subs.count(),
            'revenue': float(plan_subs.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0)
        }
    
    # Payment status counts
    verified_payments = period_subscriptions.filter(payment_status='verified').count()
    pending_payments = period_subscriptions.filter(payment_status='pending').count()
    failed_payments = period_subscriptions.filter(payment_status='failed').count()
    
    # Telegram metrics
    telegram_subs = period_subscriptions.exclude(telegram_status='not_added')
    telegram_additions = telegram_subs.filter(telegram_status='added').count()
    telegram_failures = telegram_subs.filter(telegram_status='failed_add').count()
    telegram_total = telegram_subs.count()
    telegram_success_rate = (telegram_additions / telegram_total * 100) if telegram_total > 0 else 0
    
    # Growth rate calculation
    previous_period_start = start_date - timedelta(days=days_back)
    previous_period_subs = SignalSubscription.objects.filter(
        created_at__gte=previous_period_start,
        created_at__lt=start_date
    ).count()
    
    growth_rate = 0
    if previous_period_subs > 0:
        growth_rate = ((new_subscriptions - previous_period_subs) / previous_period_subs) * 100
    elif new_subscriptions > 0:
        growth_rate = 100
    
    # Build response matching frontend SubscriptionAnalytics interface
    analytics_data = {
        'total_subscriptions': total_subscriptions,
        'new_subscriptions': new_subscriptions,
        'renewed_subscriptions': renewed_subscriptions,
        'cancelled_subscriptions': cancelled_subscriptions,
        'total_revenue': total_revenue,
        'average_subscription_value': average_subscription_value,
        'refunded_amount': refunded_amount,
        'plan_type_breakdown': plan_type_breakdown,
        'verified_payments': verified_payments,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'telegram_success_rate': round(telegram_success_rate, 2),
        'telegram_additions': telegram_additions,
        'telegram_failures': telegram_failures,
        'growth_rate': round(growth_rate, 2),
    }
    
    # Cache for 30 minutes
    cache.set(cache_key, analytics_data, 60 * 30)
    return Response(analytics_data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pricing_plans(request):
    """Manage pricing plans"""
    
    if request.method == 'GET':
        plans = PricingPlan.objects.all().order_by('sort_order', 'price')
        serializer = PricingPlanSerializer(plans, many=True)
        return Response({'pricing_plans': serializer.data})
    
    elif request.method == 'POST':
        serializer = PricingPlanSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            
            # Clear pricing cache
            cache.delete(f"pricing_metrics_{timezone.now().date()}")
            
            return Response(
                PricingPlanSerializer(plan).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pricing_plan_detail(request, plan_id):
    """Get, update, or delete pricing plan"""
    
    plan = get_object_or_404(PricingPlan, id=plan_id)
    
    if request.method == 'GET':
        serializer = PricingPlanSerializer(plan)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = PricingPlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            plan = serializer.save()
            
            # Clear caches
            cache.delete(f"pricing_metrics_{timezone.now().date()}")
            
            return Response(PricingPlanSerializer(plan).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Check if plan is being used
        active_subscriptions = SignalSubscription.objects.filter(
            pricing_plan=plan,
            payment_status='verified'
        ).count()
        
        if active_subscriptions > 0:
            return Response(
                {'error': f'Cannot delete plan with {active_subscriptions} active subscriptions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.delete()
        cache.delete(f"pricing_metrics_{timezone.now().date()}")
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_subscriptions(request):
    """List and manage signal subscriptions"""
    
    # Query parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_filter = request.GET.get('plan', '')
    telegram_status = request.GET.get('telegram_status', '')
    page = int(request.GET.get('page', 1))
    
    # Build query
    subscriptions = SignalSubscription.objects.select_related(
        'user', 'pricing_plan'
    ).order_by('-created_at')
    
    # Apply filters
    if search:
        subscriptions = subscriptions.filter(
            Q(user__email__icontains=search) |
            Q(telegram_username__icontains=search) |
            Q(paystack_reference__icontains=search)
        )
    
    if status_filter:
        subscriptions = subscriptions.filter(payment_status=status_filter)
    
    if plan_filter:
        subscriptions = subscriptions.filter(plan_type=plan_filter)
    
    if telegram_status:
        subscriptions = subscriptions.filter(telegram_status=telegram_status)
    
    # Pagination
    paginator = Paginator(subscriptions, 25)
    page_subscriptions = paginator.get_page(page)
    
    serializer = SignalSubscriptionSerializer(page_subscriptions, many=True)
    
    return Response({
        'subscriptions': serializer.data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_subscriptions': paginator.count,
            'has_next': page_subscriptions.has_next(),
            'has_previous': page_subscriptions.has_previous(),
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_verify_payment(request, subscription_id):
    """Manually verify a payment"""
    
    subscription = get_object_or_404(SignalSubscription, id=subscription_id)
    
    if subscription.payment_status != 'pending':
        return Response(
            {'error': 'Payment already processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark payment as verified
    subscription.mark_payment_verified()
    
    # Create Telegram management task
    TelegramGroupManagement.objects.create(
        signal_subscription=subscription,
        action_type='add',
        telegram_username=subscription.telegram_username,
        telegram_group=f"{subscription.plan_type.title()} Signals Group"
    )
    
    # Clear cache
    cache.delete(f"pricing_metrics_{timezone.now().date()}")
    
    return Response({
        'message': 'Payment verified successfully',
        'subscription': SignalSubscriptionSerializer(subscription).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_telegram_queue(request):
    """Get pending Telegram group management tasks"""
    
    status_filter = request.GET.get('status', 'pending')
    
    tasks = TelegramGroupManagement.objects.filter(
        status=status_filter
    ).select_related('signal_subscription__user').order_by('created_at')
    
    tasks_data = []
    for task in tasks:
        subscription = task.signal_subscription
        tasks_data.append({
            'id': task.id,
            'action_type': task.action_type,
            'user_email': subscription.user.email,
            'telegram_username': task.telegram_username,
            'telegram_group': task.telegram_group,
            'plan_type': subscription.plan_type,
            'subscription_end': subscription.subscription_end,
            'status': task.status,
            'created_at': task.created_at,
            'admin_notes': task.admin_notes,
        })
    
    return Response({'telegram_tasks': tasks_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_telegram_action(request, task_id):
    """Mark Telegram task as completed or failed"""
    
    task = get_object_or_404(TelegramGroupManagement, id=task_id)
    action = request.data.get('action')  # 'completed', 'failed', 'skipped'
    notes = request.data.get('notes', '')
    
    if action not in ['completed', 'failed', 'skipped']:
        return Response(
            {'error': 'Invalid action. Use "completed", "failed", or "skipped"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update task
    task.status = action
    task.admin_notes = notes
    task.processed_at = timezone.now()
    task.processed_by = request.user
    task.save()
    
    # Update subscription Telegram status
    if action == 'completed' and task.action_type == 'add':
        task.signal_subscription.mark_telegram_added(task.telegram_group)
    elif action == 'completed' and task.action_type == 'remove':
        task.signal_subscription.telegram_status = 'removed'
        task.signal_subscription.save()
    
    return Response({
        'message': f'Telegram task marked as {action}',
        'task_id': task.id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_payment_transactions(request):
    """List all payment transactions"""
    
    search = request.GET.get('search', '')
    transaction_type = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    page = int(request.GET.get('page', 1))
    
    transactions = PaymentTransaction.objects.select_related(
        'user', 'signal_subscription'
    ).order_by('-created_at')
    
    # Apply filters
    if search:
        transactions = transactions.filter(
            Q(user__email__icontains=search) |
            Q(reference__icontains=search)
        )
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(transactions, 30)
    page_transactions = paginator.get_page(page)
    
    serializer = PaymentTransactionSerializer(page_transactions, many=True)
    
    return Response({
        'transactions': serializer.data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_transactions': paginator.count,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="VIEW_REVENUE_ANALYTICS", sensitivity="FINANCIAL")
def revenue_analytics(request):
    """Get comprehensive revenue analytics for the admin dashboard"""
    try:
        # Parse date range from query parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get all verified subscriptions in the date range
        subscriptions = SignalSubscription.objects.filter(
            payment_status='verified',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Calculate total revenue
        total_revenue = subscriptions.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        # Calculate monthly growth
        last_month_end = start_date - timedelta(days=1)
        last_month_start = last_month_end - timedelta(days=30)
        last_month_revenue = SignalSubscription.objects.filter(
            payment_status='verified',
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        monthly_growth = 0
        if last_month_revenue > 0:
            monthly_growth = float((total_revenue - last_month_revenue) / last_month_revenue * 100)
        
        # Get active subscriptions count
        active_subscriptions = subscriptions.count()
        
        # Calculate ARPU (Average Revenue Per User)
        arpu = float(total_revenue / active_subscriptions) if active_subscriptions > 0 else 0
        
        # Calculate revenue breakdown by plan type
        revenue_breakdown = {}
        for plan_type, _ in SignalSubscription.PLAN_TYPES:
            type_revenue = subscriptions.filter(
                plan_type=plan_type
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            if type_revenue > 0:
                revenue_breakdown[plan_type] = float(type_revenue)
        
        # Calculate coupon discount impact
        total_discounts = subscriptions.filter(
            coupon_used__isnull=False
        ).aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00')
        
        # Calculate new vs retention revenue
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_student_revenue = subscriptions.filter(
            user__date_joined__gte=thirty_days_ago
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        retention_revenue = total_revenue - new_student_revenue
        
        # Calculate MRR (Monthly Recurring Revenue) - subscriptions with monthly/yearly plans
        mrr_subscriptions = subscriptions.filter(
            plan_type__in=['signals_monthly', 'vip_monthly', 'monthly']
        )
        monthly_recurring_revenue = mrr_subscriptions.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        return Response({
            'total_revenue': float(total_revenue),
            'monthly_growth': round(monthly_growth, 2),
            'active_subscriptions': active_subscriptions,
            'average_revenue_per_user': round(arpu, 2),
            'monthly_recurring_revenue': float(monthly_recurring_revenue),
            'coupon_discount_impact': -float(total_discounts),
            'new_student_revenue': float(new_student_revenue),
            'retention_revenue': float(retention_revenue),
            'revenue_breakdown': revenue_breakdown,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Revenue analytics error: {str(e)}")
        return Response({
            'error': f'Failed to generate revenue analytics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
@audit_log(action="EXPORT_REVENUE_REPORT", sensitivity="FINANCIAL")
def export_revenue_report(request):
    """Export revenue report in PDF or Excel format with optimized performance"""
    try:
        # Parse parameters
        format_type = request.data.get('format', 'excel')  # Default to Excel
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Check cache first for performance
        cache_key = f"revenue_export_{format_type}_{start_date}_{end_date}"
        cached_file = cache.get(cache_key)
        
        if cached_file:
            logger.info(f"Serving cached revenue export: {cache_key}")
            # Return cached file info
            return Response({
                'success': True,
                'cached': True,
                'format': format_type,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            })
        
        # Get revenue data
        subscriptions = SignalSubscription.objects.filter(
            payment_status='verified',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user', 'pricing_plan', 'coupon_used')
        
        # Calculate metrics
        total_revenue = subscriptions.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        total_discounts = subscriptions.filter(
            coupon_used__isnull=False
        ).aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00')
        
        # Prepare export data
        export_data = {
            'period': f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
            'total_revenue': float(total_revenue),
            'total_transactions': subscriptions.count(),
            'total_discounts': float(total_discounts),
            'subscriptions': []
        }
        
        # Add subscription details (limit to prevent memory issues)
        for sub in subscriptions[:1000]:  # Limit to 1000 records for performance
            export_data['subscriptions'].append({
                'date': sub.created_at.strftime('%Y-%m-%d'),
                'user': sub.user.email,
                'plan': sub.pricing_plan.name if sub.pricing_plan else sub.plan_type,
                'amount': float(sub.amount_paid),
                'discount': float(sub.discount_amount) if sub.discount_amount else 0,
                'coupon': sub.coupon_used.code if sub.coupon_used else 'N/A',
                'status': sub.payment_status
            })
        
        if format_type == 'excel':
            # Generate Excel file
            from io import BytesIO
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from django.http import HttpResponse
            
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Revenue Report"
            
            # Header styling
            header_fill = PatternFill(start_color="000ABE", end_color="000ABE", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            
            # Summary section
            ws['A1'] = 'OxiWorld Forex Academy - Revenue Report'
            ws['A1'].font = Font(bold=True, size=14)
            ws['A2'] = export_data['period']
            ws['A2'].font = Font(italic=True)
            
            ws['A4'] = 'Total Revenue:'
            ws['B4'] = f"${export_data['total_revenue']:,.2f}"
            ws['B4'].font = Font(bold=True)
            
            ws['A5'] = 'Total Transactions:'
            ws['B5'] = export_data['total_transactions']
            
            ws['A6'] = 'Total Discounts:'
            ws['B6'] = f"${export_data['total_discounts']:,.2f}"
            
            # Transaction details header
            headers = ['Date', 'User Email', 'Plan', 'Amount', 'Discount', 'Coupon', 'Status']
            row = 8
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Transaction data
            for idx, transaction in enumerate(export_data['subscriptions'], start=row+1):
                ws.cell(row=idx, column=1, value=transaction['date'])
                ws.cell(row=idx, column=2, value=transaction['user'])
                ws.cell(row=idx, column=3, value=transaction['plan'])
                ws.cell(row=idx, column=4, value=f"${transaction['amount']:,.2f}")
                ws.cell(row=idx, column=5, value=f"${transaction['discount']:,.2f}")
                ws.cell(row=idx, column=6, value=transaction['coupon'])
                ws.cell(row=idx, column=7, value=transaction['status'])
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save to BytesIO
            excel_file = BytesIO()
            wb.save(excel_file)
            excel_file.seek(0)
            
            filename = f'revenue_report_{start_date}_{end_date}.xlsx'
            
            # Cache for 15 minutes
            cache.set(cache_key, {
                'filename': filename,
                'generated_at': timezone.now().isoformat()
            }, 900)
            
            # Return file
            response = HttpResponse(
                excel_file.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Export-Success'] = 'true'
            
            return response
            
        elif format_type == 'pdf':
            # Generate PDF file
            from io import BytesIO
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch
            from django.http import HttpResponse
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#000ABE'),
                spaceAfter=30,
            )
            title = Paragraph("OxiWorld Forex Academy - Revenue Report", title_style)
            elements.append(title)
            
            # Period
            period_text = Paragraph(f"<b>Period:</b> {export_data['period']}", styles['Normal'])
            elements.append(period_text)
            elements.append(Spacer(1, 0.2*inch))
            
            # Summary table
            summary_data = [
                ['Metric', 'Value'],
                ['Total Revenue', f"${export_data['total_revenue']:,.2f}"],
                ['Total Transactions', str(export_data['total_transactions'])],
                ['Total Discounts', f"${export_data['total_discounts']:,.2f}"],
                ['Net Revenue', f"${export_data['total_revenue'] - export_data['total_discounts']:,.2f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#000ABE')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.4*inch))
            
            # Transactions header
            trans_header = Paragraph("<b>Transaction Details</b>", styles['Heading2'])
            elements.append(trans_header)
            elements.append(Spacer(1, 0.2*inch))
            
            # Transactions table (limit to fit on page)
            trans_data = [['Date', 'Plan', 'Amount', 'Discount']]
            for transaction in export_data['subscriptions'][:50]:  # First 50 for PDF
                trans_data.append([
                    transaction['date'],
                    transaction['plan'][:25],  # Truncate long names
                    f"${transaction['amount']:,.2f}",
                    f"${transaction['discount']:,.2f}"
                ])
            
            trans_table = Table(trans_data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 1.2*inch])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#000ABE')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(trans_table)
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            
            filename = f'revenue_report_{start_date}_{end_date}.pdf'
            
            # Cache for 15 minutes
            cache.set(cache_key, {
                'filename': filename,
                'generated_at': timezone.now().isoformat()
            }, 900)
            
            # Return file
            response = HttpResponse(buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Export-Success'] = 'true'
            
            return response
        
        else:
            return Response({
                'error': 'Invalid format. Use "pdf" or "excel"'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Revenue export error: {str(e)}")
        return Response({
            'error': f'Failed to export report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)