"""
DEPRECATED: Phase 0.4 Admin Views - Replaced by Phase 0.5 Admin System

This file contains stub functions to prevent URL resolution errors.
Most Phase 0.4 views are deprecated and return 410 GONE status.

NEW: Phase 0.5 Unified Subscriptions Management endpoints at end of file:
- subscription_management_list
- update_subscription_action  
- subscription_plans_filter
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsAdmin
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


def _deprecated_response(view_name):
    """Return a deprecated response for old admin views."""
    return Response({
        'error': 'This endpoint is deprecated',
        'message': f'{view_name} is part of Phase 0.4 and has been replaced by Phase 0.5 admin system',
        'suggestion': 'Please use the new admin endpoints or wait for Phase 0.6 admin dashboard rewrite'
    }, status=status.HTTP_410_GONE)


# ============================================================================
# DEPRECATED STUB VIEWS (Phase 0.4)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pricing_dashboard(request):
    return _deprecated_response('admin_pricing_dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_analytics(request):
    return _deprecated_response('subscription_analytics')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_analytics_dashboard(request):
    return _deprecated_response('subscription_analytics_dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def performance_metrics_dashboard(request):
    return _deprecated_response('performance_metrics_dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def revenue_analytics(request):
    return _deprecated_response('revenue_analytics')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_revenue_report(request):
    return _deprecated_response('export_revenue_report')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscriptions_list(request):
    return _deprecated_response('subscriptions_list')


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def subscription_detail(request, subscription_id):
    return _deprecated_response('subscription_detail')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pricing_plans(request):
    return _deprecated_response('admin_pricing_plans')


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_pricing_plan_detail(request, plan_id):
    return _deprecated_response('admin_pricing_plan_detail')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_subscriptions(request):
    return _deprecated_response('admin_subscriptions')


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_verify_payment(request, subscription_id):
    return _deprecated_response('admin_verify_payment')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_telegram_queue(request):
    return _deprecated_response('admin_telegram_queue')


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_telegram_action(request, task_id):
    return _deprecated_response('admin_telegram_action')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_payment_transactions(request):
    return _deprecated_response('admin_payment_transactions')


# ============================================================================
# PHASE 0.5: Unified Subscriptions Management
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAdmin])
def subscription_management_list(request):
    """
    Get paginated list of subscriptions with filters and analytics.
    Phase 0.5 singleton: User -> BillingProfile -> Subscription -> SubscriptionPlan
    
    Filters: status, plan, date_from, date_to, auto_renew, search, page, page_size
    """
    try:
        from subscriptions.models import Subscription
        from users.models import User
        
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        plan_filter = request.GET.get('plan', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        auto_renew_filter = request.GET.get('auto_renew', 'all')
        search = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Base queryset with related data
        subscriptions = Subscription.objects.select_related(
            'billing_profile__user',
            'plan',
            'payment_method'
        ).all()
        
        # Apply filters
        if status_filter != 'all':
            subscriptions = subscriptions.filter(status=status_filter)
        if plan_filter:
            subscriptions = subscriptions.filter(plan__slug=plan_filter)
        if date_from:
            subscriptions = subscriptions.filter(start_date__gte=date_from)
        if date_to:
            subscriptions = subscriptions.filter(end_date__lte=date_to)
        if auto_renew_filter == 'true':
            subscriptions = subscriptions.filter(auto_renew=True)
        elif auto_renew_filter == 'false':
            subscriptions = subscriptions.filter(auto_renew=False)
        if search:
            subscriptions = subscriptions.filter(
                Q(billing_profile__user__email__icontains=search) |
                Q(billing_profile__user__first_name__icontains=search) |
                Q(billing_profile__user__last_name__icontains=search) |
                Q(billing_profile__user__username__icontains=search)
            )
        
        # Get analytics (before pagination)
        total_count = subscriptions.count()
        active_count = subscriptions.filter(status='active').count()
        
        # Calculate total revenue (use plan base prices in USD)
        total_revenue = sum(
            float(sub.plan.base_price) if sub.plan else 0.0
            for sub in subscriptions.filter(status__in=['active', 'expired', 'cancelled'])
        )
        
        avg_value = total_revenue / total_count if total_count > 0 else 0
        
        # Plan breakdown
        plan_breakdown = {}
        for sub in subscriptions:
            plan_name = sub.plan.name if sub.plan else 'Unknown'
            plan_breakdown[plan_name] = plan_breakdown.get(plan_name, 0) + 1
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_subs = subscriptions.order_by('-created_at')[start_idx:end_idx]
        
        # Serialize
        subscription_data = []
        for sub in paginated_subs:
            user = sub.billing_profile.user
            subscription_data.append({
                'id': str(sub.id),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                },
                'plan': {
                    'id': str(sub.plan.id) if sub.plan else None,
                    'name': sub.plan.name if sub.plan else 'Unknown',
                    'slug': sub.plan.slug if sub.plan else '',
                    'base_price_usd': float(sub.plan.base_price) if sub.plan else 0.0,
                    'billing_period': sub.plan.billing_period if sub.plan else '',
                },
                'status': sub.status,
                'start_date': sub.start_date.isoformat() if sub.start_date else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
                'auto_renew': sub.auto_renew,
                'next_billing_date': sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                'amount_paid': float(sub.amount_paid or 0),
                'currency': sub.currency,
                'payment_method': sub.payment_method.payment_type if sub.payment_method else None,
                'cancelled_at': sub.cancelled_at.isoformat() if sub.cancelled_at else None,
                'days_remaining': sub.days_remaining if sub.status == 'active' else 0,
                'created_at': sub.created_at.isoformat(),
            })
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return Response({
            'subscriptions': subscription_data,
            'analytics': {
                'total_count': total_count,
                'active_count': active_count,
                'total_revenue_usd': round(total_revenue, 2),
                'average_value_usd': round(avg_value, 2),
                'plan_breakdown': plan_breakdown,
            },
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'total_count': total_count,
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error in subscription_management_list: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': 'Failed to fetch subscriptions',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdmin])
def update_subscription_action(request, subscription_id):
    """
    Update subscription: cancel, toggle_auto_renew, extend.
    Body: action, reason (for cancel), days (for extend)
    """
    try:
        from subscriptions.models import Subscription
        from users.models import AdminAction
        
        subscription = Subscription.objects.select_related(
            'billing_profile__user', 'plan'
        ).get(id=subscription_id)
        
        action = request.data.get('action')
        
        if action == 'cancel':
            reason = request.data.get('reason', 'Admin cancellation')
            subscription.cancel(reason=reason)
            AdminAction.log_action(
                admin_user=request.user,
                action='update_subscription',
                target_user=subscription.billing_profile.user,
                details={'action': 'cancel', 'subscription_id': str(subscription.id),
                        'plan': subscription.plan.name if subscription.plan else 'Unknown', 'reason': reason},
                request=request
            )
            message = 'Subscription cancelled successfully'
            
        elif action == 'toggle_auto_renew':
            subscription.auto_renew = not subscription.auto_renew
            subscription.save()
            AdminAction.log_action(
                admin_user=request.user,
                action='update_subscription',
                target_user=subscription.billing_profile.user,
                details={'action': 'toggle_auto_renew', 'subscription_id': str(subscription.id),
                        'plan': subscription.plan.name if subscription.plan else 'Unknown',
                        'auto_renew': subscription.auto_renew},
                request=request
            )
            message = f"Auto-renew {'enabled' if subscription.auto_renew else 'disabled'}"
            
        elif action == 'extend':
            days = int(request.data.get('days', 0))
            if days <= 0:
                return Response({'error': 'Invalid days value'}, status=status.HTTP_400_BAD_REQUEST)
            
            if subscription.end_date:
                subscription.end_date = subscription.end_date + timedelta(days=days)
            else:
                subscription.end_date = timezone.now() + timedelta(days=days)
            subscription.save()
            
            AdminAction.log_action(
                admin_user=request.user,
                action='update_subscription',
                target_user=subscription.billing_profile.user,
                details={'action': 'extend', 'subscription_id': str(subscription.id),
                        'plan': subscription.plan.name if subscription.plan else 'Unknown',
                        'days_added': days, 'new_end_date': subscription.end_date.isoformat()},
                request=request
            )
            message = f'Subscription extended by {days} days'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': message,
            'subscription': {
                'id': str(subscription.id),
                'status': subscription.status,
                'auto_renew': subscription.auto_renew,
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            }
        })
        
    except Subscription.DoesNotExist:
        return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print(f"Error in update_subscription_action: {str(e)}")
        print(traceback.format_exc())
        return Response({'error': 'Failed to update subscription', 'details': str(e)},
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def subscription_plans_filter(request):
    """Get active subscription plans for filter dropdown."""
    try:
        from subscriptions.models import SubscriptionPlan
        
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'name')
        plans_data = [{
            'id': str(plan.id),
            'name': plan.name,
            'slug': plan.slug,
            'base_price': float(plan.base_price),
            'billing_period': plan.billing_period,
        } for plan in plans]
        
        return Response({'plans': plans_data})
        
    except Exception as e:
        return Response({'error': 'Failed to fetch plans', 'details': str(e)},
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
