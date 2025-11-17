"""
Payment Management Admin Views
Provides transaction list and analytics for admin dashboard
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import calendar

from .models import Subscription, SubscriptionPlan
from .permissions import IsAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def payment_transactions_list(request):
    """
    Get list of payment transactions (from subscriptions) with analytics
    
    Query params:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    - status: Filter by subscription status
    - search: Search by user email/name
    - date_from: Filter by created date (ISO format)
    - date_to: Filter by created date (ISO format)
    - payment_method: Filter by payment method type
    """
    try:
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size
        
        # Filters
        status = request.GET.get('status', '')
        search = request.GET.get('search', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        payment_method = request.GET.get('payment_method', '')
        
        # Base queryset - all subscriptions are "transactions"
        queryset = Subscription.objects.select_related(
            'billing_profile__user',
            'plan',
            'payment_method'
        ).all()
        
        # Apply filters
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        if search:
            queryset = queryset.filter(
                Q(billing_profile__user__email__icontains=search) |
                Q(billing_profile__user__username__icontains=search) |
                Q(billing_profile__user__first_name__icontains=search) |
                Q(billing_profile__user__last_name__icontains=search)
            )
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if payment_method and payment_method != 'all':
            queryset = queryset.filter(payment_method__payment_type=payment_method)
        
        # Get total count
        total_count = queryset.count()
        
        # Calculate analytics
        all_subs = Subscription.objects.all()
        
        # Total revenue (sum all amounts, but group by currency for accuracy)
        revenue_by_currency = all_subs.values('currency').annotate(
            total=Sum('amount_paid')
        )
        
        # For simplicity, we'll show USD total (assuming base_price is in USD)
        total_revenue_usd = float(
            all_subs.aggregate(
                total=Sum('plan__base_price')
            )['total'] or 0
        )
        
        # Count by status
        status_counts = all_subs.values('status').annotate(count=Count('id'))
        verified_count = next((s['count'] for s in status_counts if s['status'] == 'active'), 0)
        pending_count = next((s['count'] for s in status_counts if s['status'] == 'pending'), 0)
        
        # Payment methods breakdown
        payment_methods = all_subs.filter(
            payment_method__isnull=False
        ).values(
            'payment_method__payment_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount_paid')
        )
        
        # Recent transactions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_revenue = float(
            all_subs.filter(
                created_at__gte=thirty_days_ago
            ).aggregate(
                total=Sum('plan__base_price')
            )['total'] or 0
        )
        
        # Average transaction value
        avg_value = float(
            all_subs.aggregate(
                avg=Avg('plan__base_price')
            )['avg'] or 0
        )
        
        # Get paginated results
        transactions = queryset.order_by('-created_at')[offset:offset + page_size]
        
        # Serialize transaction data
        transaction_data = []
        for sub in transactions:
            user = sub.billing_profile.user
            transaction_data.append({
                'id': str(sub.id),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                },
                'plan': {
                    'id': str(sub.plan.id) if sub.plan else None,
                    'name': sub.plan.name if sub.plan else 'No Plan',
                    'base_price_usd': float(sub.plan.base_price) if sub.plan else 0,
                },
                'amount_paid': float(sub.amount_paid),
                'currency': sub.currency,
                'status': sub.status,
                'payment_method': sub.payment_method.payment_type if sub.payment_method else 'unknown',
                'payment_details': {
                    'card_last4': sub.payment_method.card_last4 if sub.payment_method and sub.payment_method.payment_type == 'card' else None,
                    'card_brand': sub.payment_method.card_brand if sub.payment_method and sub.payment_method.payment_type == 'card' else None,
                    'bank_name': sub.payment_method.bank_name if sub.payment_method and sub.payment_method.payment_type == 'bank_transfer' else None,
                } if sub.payment_method else None,
                'created_at': sub.created_at.isoformat(),
                'start_date': sub.start_date.isoformat() if sub.start_date else None,
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
            })
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return Response({
            'transactions': transaction_data,
            'analytics': {
                'total_revenue_usd': round(total_revenue_usd, 2),
                'total_transactions': total_count,
                'verified_transactions': verified_count,
                'pending_transactions': pending_count,
                'recent_revenue_30d': round(recent_revenue, 2),
                'average_transaction_value': round(avg_value, 2),
                'payment_methods': [
                    {
                        'type': pm['payment_method__payment_type'],
                        'count': pm['count'],
                        'total_amount': float(pm['total_amount'] or 0),
                    }
                    for pm in payment_methods
                ],
                'revenue_by_currency': [
                    {
                        'currency': rc['currency'],
                        'total': float(rc['total'] or 0),
                    }
                    for rc in revenue_by_currency
                ],
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
        print(f"Error in payment_transactions_list: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': 'Failed to fetch payment transactions',
            'detail': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def revenue_analytics(request):
    """
    Get monthly revenue analytics for the last 12 months
    Returns revenue breakdown by month for charts
    """
    try:
        # Get last 12 months of data
        twelve_months_ago = timezone.now() - timedelta(days=365)
        
        # Group subscriptions by month and sum revenue
        monthly_revenue = Subscription.objects.filter(
            created_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount_paid'),
            count=Count('id')
        ).order_by('month')
        
        # Format the data for frontend
        revenue_data = []
        for item in monthly_revenue:
            month_date = item['month']
            revenue_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': calendar.month_abbr[month_date.month],
                'revenue': float(item['revenue'] or 0),
                'count': item['count'],
                'year': month_date.year,
                'month_number': month_date.month,
            })
        
        # Fill in missing months with zero revenue
        all_months = []
        current_date = timezone.now()
        for i in range(12):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            
            existing = next((r for r in revenue_data if r['month'] == month_key), None)
            if existing:
                all_months.append(existing)
            else:
                all_months.append({
                    'month': month_key,
                    'month_name': calendar.month_abbr[month_date.month],
                    'revenue': 0.0,
                    'count': 0,
                    'year': month_date.year,
                    'month_number': month_date.month,
                })
        
        # Sort by date (oldest first)
        all_months.sort(key=lambda x: x['month'])
        
        # Calculate growth rate
        for i in range(1, len(all_months)):
            prev_revenue = all_months[i-1]['revenue']
            curr_revenue = all_months[i]['revenue']
            
            if prev_revenue > 0:
                growth = ((curr_revenue - prev_revenue) / prev_revenue) * 100
                all_months[i]['growth_rate'] = round(growth, 2)
            else:
                all_months[i]['growth_rate'] = 0.0
        
        if all_months:
            all_months[0]['growth_rate'] = 0.0
        
        # Calculate total revenue
        total_revenue = sum(m['revenue'] for m in all_months)
        
        return Response({
            'success': True,
            'monthly_revenue': all_months,
            'total_revenue': round(total_revenue, 2),
            'total_months': len(all_months),
        })
        
    except Exception as e:
        import traceback
        print(f"Error in revenue_analytics: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': 'Failed to fetch revenue analytics',
            'detail': str(e)
        }, status=500)
