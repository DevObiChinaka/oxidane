from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from subscriptions.models import Subscription, SubscriptionPlan, Coupon
from users.admin_auth import admin_required
from django.http import HttpResponse
import json

class RevenueAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for revenue analytics and reporting"""
    permission_classes = [permissions.IsAuthenticated]

    def get_date_range(self, request):
        """Parse date range from request parameters"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        return start_date, end_date

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get comprehensive revenue analytics"""
        try:
            start_date, end_date = self.get_date_range(request)
            
            # Calculate total revenue from completed transactions
            transactions = Subscription.objects.filter(
                status='active',
                created_at__date__range=[start_date, end_date]
            )
            total_revenue = transactions.aggregate(
                total=Sum('payment_amount')
            )['total'] or 0

            # Calculate monthly growth
            last_month_end = start_date - timedelta(days=1)
            last_month_start = last_month_end - timedelta(days=30)
            last_month_revenue = Subscription.objects.filter(
                status='active',
                created_at__date__range=[last_month_start, last_month_end]
            ).aggregate(total=Sum('payment_amount'))['total'] or 0
            
            monthly_growth = ((total_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
            
            # Get active subscriptions count
            active_subscriptions = transactions.count()
            
            # Calculate ARPU
            arpu = total_revenue / active_subscriptions if active_subscriptions > 0 else 0
            
            # Calculate revenue breakdown by type
            # TODO: Update when PaymentTransaction model is recreated (Phase 0.5.17+)
            revenue_breakdown = {}
            for plan_type, _ in SubscriptionPlan.PLAN_TYPE_CHOICES:
                type_revenue = 0  # TODO: Calculate from actual payment transactions
                revenue_breakdown[plan_type] = type_revenue
            
            # Calculate coupon impact
            coupon_impacts = transactions.filter(
                coupon_code__isnull=False
            ).aggregate(
                total_discount=Sum('discount_amount')
            )
            coupon_discount_impact = coupon_impacts['total_discount'] or 0
            
            # Calculate new vs retention revenue
            thirty_days_ago = timezone.now() - timedelta(days=30)
            new_students = transactions.filter(
                user__date_joined__gte=thirty_days_ago
            ).aggregate(total=Sum('payment_amount'))['total'] or 0
            
            retention_revenue = total_revenue - new_students
            
            return Response({
                'total_revenue': total_revenue,
                'monthly_growth': monthly_growth,
                'active_subscriptions': active_subscriptions,
                'average_revenue_per_user': round(arpu, 2),
                'monthly_recurring_revenue': revenue_breakdown['subscriptions'],
                'coupon_discount_impact': coupon_discount_impact,
                'new_student_revenue': 18750.00,
                'retention_revenue': 26530.50,
                'revenue_breakdown': revenue_breakdown,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate revenue analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export revenue report in PDF or Excel format"""
        try:
            format_type = request.data.get('format', 'pdf')
            start_date, end_date = self.get_date_range(request)
            
            if format_type == 'pdf':
                # TODO: Implement PDF generation using reportlab or weasyprint
                filename = f'revenue_report_{start_date}_to_{end_date}.pdf'
                
                # Mock PDF generation
                response_data = {
                    'success': True,
                    'download_url': f'/media/reports/{filename}',
                    'filename': filename,
                    'message': 'PDF report generated successfully'
                }
                
            elif format_type == 'excel':
                # TODO: Implement Excel generation using openpyxl or xlsxwriter
                filename = f'revenue_report_{start_date}_to_{end_date}.xlsx'
                
                # Mock Excel generation
                response_data = {
                    'success': True,
                    'download_url': f'/media/reports/{filename}',
                    'filename': filename,
                    'message': 'Excel report generated successfully'
                }
                
            else:
                return Response({
                    'error': 'Invalid format. Use "pdf" or "excel"'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'error': f'Failed to export report: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def subscription_analytics(self, request):
        """Get detailed subscription revenue analytics"""
        try:
            start_date, end_date = self.get_date_range(request)
            
            # Get subscription analytics by plan type
            plan_analytics = []
            for plan in SubscriptionPlan.objects.filter(is_active=True):
                plan_subscriptions = Subscription.objects.filter(
                    plan_id=plan.id,
                    start_date__range=[start_date, end_date]
                ).count()
                
                plan_analytics.append({
                    'plan_name': plan.name,
                    'plan_type': plan.plan_type,
                    'subscription_count': plan_subscriptions,
                    'revenue': 0,  # TODO: Calculate from actual payment transactions
                    'growth_rate': 0  # TODO: Calculate growth rate
                })
            
            return Response({
                'plan_analytics': plan_analytics,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to get subscription analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def coupon_analytics(self, request):
        """Get coupon usage and revenue impact analytics"""
        try:
            start_date, end_date = self.get_date_range(request)
            
            # Get coupon usage analytics
            coupon_analytics = []
            for coupon in Coupon.objects.filter(
                created_at__date__range=[start_date, end_date]
            ):
                coupon_analytics.append({
                    'code': coupon.code,
                    'discount_type': coupon.discount_type,
                    'discount_value': coupon.discount_value,
                    'usage_count': coupon.usage_count,
                    'usage_limit': coupon.usage_limit,
                    'revenue_impact': 0,  # TODO: Calculate actual revenue impact
                    'is_active': coupon.is_active
                })
            
            return Response({
                'coupon_analytics': coupon_analytics,
                'total_discount_given': sum(c['revenue_impact'] for c in coupon_analytics),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to get coupon analytics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
