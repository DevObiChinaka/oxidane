"""
User Subscription Management Views
Handles user-facing subscription management functionality
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from decimal import Decimal

from .models import SignalSubscription
from .serializers import SignalSubscriptionSerializer


class UserSubscriptionViewSet(viewsets.ViewSet):
    """
    ViewSet for user subscription management
    """
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='my-subscriptions')
    def my_subscriptions(self, request):
        """
        Get all subscriptions for the authenticated user with stats
        """
        user = request.user
        subscriptions = []
        
        # Get Signal Subscriptions
        signal_subs = SignalSubscription.objects.filter(
            user=user,
            payment_status='verified'
        ).order_by('-created_at')
        
        for sub in signal_subs:
            # Check if subscription is active
            is_active = False
            if sub.subscription_start and sub.subscription_end:
                is_active = (
                    sub.payment_status == 'verified' and
                    timezone.now() >= sub.subscription_start and
                    timezone.now() <= sub.subscription_end
                )
            
            days_remaining = None
            if is_active and sub.subscription_end:
                days_remaining = (sub.subscription_end - timezone.now()).days
            
            # Determine status
            if is_active:
                subscription_status = 'active'
            elif sub.subscription_end and timezone.now() > sub.subscription_end:
                subscription_status = 'expired'
            else:
                subscription_status = 'cancelled'
            
            # Get features based on plan
            features = self._get_plan_features(sub, 'signal')
            
            subscriptions.append({
                'id': str(sub.id),
                'plan_name': sub.pricing_plan.name if sub.pricing_plan else 'Signal Plan',
                'plan_type': 'signal',
                'status': subscription_status,
                'amount': float(sub.amount_paid),
                'currency': sub.currency,
                'billing_cycle': 'monthly',  # Adjust based on your plan structure
                'start_date': sub.subscription_start.date().isoformat() if sub.subscription_start else sub.created_at.date().isoformat(),
                'end_date': sub.subscription_end.date().isoformat() if sub.subscription_end else None,
                'auto_renew': sub.auto_renewal,
                'features': features,
                'telegram_username': sub.telegram_username,
                'days_remaining': days_remaining,
            })
        
        # Get Mentorship Purchases (now stored in SignalSubscription with plan_type starting with 'mentorship')
        mentorship_subs = SignalSubscription.objects.filter(
            user=user,
            payment_status='verified',
            plan_type__startswith='mentorship'
        ).order_by('-created_at')
        
        for sub in mentorship_subs:
            # Mentorship is lifetime, so always active if verified
            is_active = sub.payment_status == 'verified'
            days_remaining = None  # Lifetime access, no expiration
            
            features = self._get_plan_features(sub, 'mentorship')
            
            subscriptions.append({
                'id': str(sub.id),
                'plan_name': 'Mentorship Program',
                'plan_type': 'mentorship',
                'status': 'active' if is_active else 'inactive',
                'amount': float(sub.amount_paid),
                'currency': sub.currency,
                'billing_cycle': 'one_time',
                'start_date': sub.subscription_start.date().isoformat() if sub.subscription_start else sub.created_at.date().isoformat(),
                'end_date': None,  # Lifetime access
                'auto_renew': False,  # One-time payment
                'features': features,
                'days_remaining': days_remaining,
            })
        
        # Calculate stats
        active_subs = [s for s in subscriptions if s['status'] == 'active']
        stats = {
            'active_count': len(active_subs),
            'total_monthly_cost': sum(s['amount'] for s in active_subs if s['billing_cycle'] == 'monthly'),
            'next_renewal_date': None,
            'days_until_renewal': None,
        }
        
        # Find next renewal date
        active_with_dates = [s for s in active_subs if s['end_date']]
        if active_with_dates:
            next_renewal = min(active_with_dates, key=lambda x: x['end_date'])
            stats['next_renewal_date'] = next_renewal['end_date']
            stats['days_until_renewal'] = next_renewal['days_remaining']
        
        return Response({
            'subscriptions': subscriptions,
            'stats': stats,
        })

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_subscription(self, request, pk=None):
        """
        Cancel a subscription (will remain active until end of billing period)
        """
        user = request.user
        
        # Try to find in signal subscriptions
        try:
            signal_sub = SignalSubscription.objects.get(id=pk, user=user)
            
            # Check if active
            is_active = (
                signal_sub.payment_status == 'verified' and
                signal_sub.subscription_end and
                timezone.now() <= signal_sub.subscription_end
            )
            
            if not is_active:
                return Response(
                    {'error': 'Subscription is already inactive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark for cancellation at end of period
            signal_sub.auto_renewal = False
            
            # Add cancellation note
            current_notes = signal_sub.admin_notes or ""
            signal_sub.admin_notes = f"{current_notes}\nCancelled by user on {timezone.now().date()}"
            signal_sub.save()
            
            return Response({
                'message': 'Subscription cancelled successfully. Access will continue until end of billing period.',
                'end_date': signal_sub.subscription_end.date().isoformat() if signal_sub.subscription_end else None,
            })
        except SignalSubscription.DoesNotExist:
            # Check if it's a mentorship (one-time payment)
            try:
                mentorship_sub = SignalSubscription.objects.get(id=pk, user=user, plan_type__startswith='mentorship')
                return Response(
                    {'error': 'Mentorship is a one-time purchase and cannot be cancelled. You have lifetime access.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except SignalSubscription.DoesNotExist:
                return Response(
                    {'error': 'Subscription not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=True, methods=['patch'], url_path='auto-renewal')
    def toggle_auto_renewal(self, request, pk=None):
        """
        Toggle auto-renewal for a subscription
        """
        user = request.user
        auto_renew = request.data.get('auto_renew')
        
        if auto_renew is None:
            return Response(
                {'error': 'auto_renew field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try signal subscription
        try:
            signal_sub = SignalSubscription.objects.get(id=pk, user=user)
            signal_sub.auto_renewal = auto_renew
            signal_sub.save()
            return Response({
                'message': 'Auto-renewal updated successfully',
                'auto_renew': auto_renew,
            })
        except SignalSubscription.DoesNotExist:
            # Check if it's mentorship (one-time purchase)
            try:
                SignalSubscription.objects.get(id=pk, user=user, plan_type__startswith='mentorship')
                return Response({
                    'error': 'Mentorship is a one-time purchase and does not have auto-renewal',
                }, status=status.HTTP_400_BAD_REQUEST)
            except SignalSubscription.DoesNotExist:
                return Response(
                    {'error': 'Subscription not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate_subscription(self, request, pk=None):
        """
        Reactivate an expired subscription
        """
        user = request.user
        
        # Try signal subscription
        try:
            signal_sub = SignalSubscription.objects.get(id=pk, user=user)
            
            # Check if active
            is_active = (
                signal_sub.payment_status == 'verified' and
                signal_sub.subscription_end and
                timezone.now() <= signal_sub.subscription_end
            )
            
            if is_active:
                return Response(
                    {'error': 'Subscription is already active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reactivate for another period
            signal_sub.subscription_start = timezone.now()
            signal_sub.subscription_end = timezone.now() + timedelta(days=30)  # Default to 30 days
            signal_sub.payment_status = 'verified'
            signal_sub.auto_renewal = True
            signal_sub.save()
            
            return Response({
                'message': 'Subscription reactivated successfully',
                'end_date': signal_sub.subscription_end.date().isoformat(),
            })
        except SignalSubscription.DoesNotExist:
            # Check if it's mentorship
            try:
                mentorship_sub = SignalSubscription.objects.get(id=pk, user=user, plan_type__startswith='mentorship')
                # Mentorship is lifetime, doesn't need reactivation
                if mentorship_sub.payment_status == 'verified':
                    return Response(
                        {'error': 'Mentorship is already active with lifetime access'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Reactivate if payment was somehow not verified
                mentorship_sub.payment_status = 'verified'
                mentorship_sub.save()
                
                return Response({
                    'message': 'Mentorship access reactivated successfully',
                    'end_date': None,  # Lifetime
                })
            except SignalSubscription.DoesNotExist:
                return Response(
                    {'error': 'Subscription not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    def _get_plan_features(self, subscription, plan_type):
        """
        Get features list for a subscription
        """
        if plan_type == 'signal':
            features = [
                'Daily Trading Signals',
                'Telegram Channel Access',
                'Market Analysis',
                'Entry & Exit Points',
            ]
            if hasattr(subscription, 'pricing_plan') and subscription.pricing_plan:
                # Add plan-specific features
                if hasattr(subscription.pricing_plan, 'signals_per_day') and subscription.pricing_plan.signals_per_day:
                    features.insert(0, f'{subscription.pricing_plan.signals_per_day} Signals per Day')
        elif plan_type == 'mentorship':
            features = [
                'Premium Course Access',
                '1-on-1 Mentorship Sessions',
                'Trading Signals Included',
                'Priority Support',
                'Private Community Access',
            ]
            if hasattr(subscription, 'mentorship_plan') and subscription.mentorship_plan:
                # Add plan-specific features
                plan = subscription.mentorship_plan
                if hasattr(plan, 'one_on_one_sessions') and plan.one_on_one_sessions:
                    features.insert(1, f'{plan.one_on_one_sessions} Sessions per Month')
        else:
            features = ['Full Platform Access']
        
        return features
