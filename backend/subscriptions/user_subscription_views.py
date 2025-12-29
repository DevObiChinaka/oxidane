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

from .models import Subscription, BillingProfile
# from .serializers import SignalSubscriptionSerializer  # TODO: Create new SubscriptionSerializer for Phase 0.5


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
        
        # Get user's billing profile
        try:
            billing_profile = BillingProfile.objects.get(user=user)
        except BillingProfile.DoesNotExist:
            # No billing profile, no subscriptions
            return Response({
                'subscriptions': [],
                'stats': {
                    'active_count': 0,
                    'total_monthly_cost': 0,
                    'next_renewal_date': None,
                    'days_until_renewal': None,
                }
            })
        
        # Get Signal Subscriptions (exclude mentorship plans)
        signal_subs = Subscription.objects.filter(
            billing_profile=billing_profile,
            status='active'
        ).exclude(plan__slug__icontains='mentorship').select_related('plan', 'payment_method').order_by('-created_at')
        
        for sub in signal_subs:
            # Check if subscription is active
            is_active = False
            if sub.start_date and sub.end_date:
                is_active = (
                    sub.status == 'active' and
                    timezone.now() >= sub.start_date and
                    timezone.now() <= sub.end_date
                )
            
            days_remaining = None
            if is_active and sub.end_date:
                days_remaining = (sub.end_date - timezone.now()).days
            
            # Determine status
            if is_active:
                subscription_status = 'active'
            elif sub.end_date and timezone.now() > sub.end_date:
                subscription_status = 'expired'
            else:
                subscription_status = 'cancelled'
            
            # Get features based on plan
            features = self._get_plan_features(sub, 'signal')
            
            # Use actual amount paid, fallback to plan price if not set
            if sub.amount_paid:
                amount = float(sub.amount_paid)
            elif sub.plan and sub.plan.base_price:
                amount = float(sub.plan.base_price)
            else:
                amount = 0
            
            # Get payment method details if exists
            payment_method_data = None
            if sub.payment_method and sub.payment_method.is_active:
                payment_method_data = {
                    'id': str(sub.payment_method.id),
                    'card_brand': sub.payment_method.card_brand,
                    'card_last4': sub.payment_method.card_last4,
                    'card_exp_month': sub.payment_method.card_exp_month,
                    'card_exp_year': sub.payment_method.card_exp_year,
                    'is_default': sub.payment_method.is_default,
                    'last_used_at': sub.payment_method.last_used_at.isoformat() if sub.payment_method.last_used_at else None,
                }
            
            subscriptions.append({
                'id': str(sub.id),
                'plan_name': sub.plan.name if sub.plan else 'Signal Plan',
                'plan_type': 'signal',
                'status': subscription_status,
                'amount': amount,
                'currency': sub.currency or 'USD',
                'plan_base_price': float(sub.plan.base_price) if sub.plan else 0,
                'plan_currency': 'USD',
                'billing_cycle': sub.plan.billing_period if sub.plan else 'monthly',
                'start_date': sub.start_date.date().isoformat() if sub.start_date else sub.created_at.date().isoformat(),
                'end_date': sub.end_date.date().isoformat() if sub.end_date else None,
                'auto_renew': sub.auto_renew,
                'last_renewed_at': sub.last_renewed_at.date().isoformat() if sub.last_renewed_at else None,
                'features': features,
                'telegram_username': billing_profile.telegram_username,
                'days_remaining': days_remaining,
                'is_lifetime': False,
                'payment_method': payment_method_data,
            })
        
        # Get Mentorship Purchases
        mentorship_subs = Subscription.objects.filter(
            billing_profile=billing_profile,
            status='active',
            plan__slug__icontains='mentorship'
        ).select_related('plan').order_by('-created_at')
        
        for sub in mentorship_subs:
            # Mentorship is lifetime, so always active if verified
            is_active = sub.status == 'active'
            days_remaining = None  # Lifetime access, no expiration
            
            features = self._get_plan_features(sub, 'mentorship')
            
            # Use actual amount paid, fallback to plan price if not set
            if sub.amount_paid:
                amount = float(sub.amount_paid)
            elif sub.plan and sub.plan.base_price:
                amount = float(sub.plan.base_price)
            else:
                amount = 0
            
            # Mentorship is one-time, no payment method needed
            payment_method_data = None
            
            subscriptions.append({
                'id': str(sub.id),
                'plan_name': sub.plan.name if sub.plan else 'Mentorship Program',
                'plan_type': 'mentorship',
                'status': 'active' if is_active else 'inactive',
                'amount': amount,
                'currency': sub.currency or 'USD',
                'plan_base_price': float(sub.plan.base_price) if sub.plan else 0,
                'plan_currency': 'USD',
                'billing_cycle': 'lifetime',
                'start_date': sub.start_date.date().isoformat() if sub.start_date else sub.created_at.date().isoformat(),
                'end_date': None,  # Lifetime access
                'auto_renew': False,  # One-time payment
                'last_renewed_at': None,  # Lifetime plans don't renew
                'features': features,
                'days_remaining': days_remaining,
                'is_lifetime': True,
                'payment_method': payment_method_data,
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
        
        # Get user's billing profile
        try:
            billing_profile = BillingProfile.objects.get(user=user)
        except BillingProfile.DoesNotExist:
            return Response(
                {'error': 'Billing profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Try to find subscription
        try:
            subscription = Subscription.objects.get(id=pk, billing_profile=billing_profile)
            
            # Check if it's a mentorship (one-time lifetime payment)
            if subscription.plan and 'mentorship' in subscription.plan.slug.lower():
                return Response(
                    {'error': 'Mentorship is a one-time purchase and cannot be cancelled. You have lifetime access.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if active
            is_active = (
                subscription.status == 'active' and
                subscription.end_date and
                timezone.now() <= subscription.end_date
            )
            
            if not is_active:
                return Response(
                    {'error': 'Subscription is already inactive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark for cancellation at end of period
            subscription.auto_renew = False
            subscription.save()
            
            return Response({
                'message': 'Subscription cancelled successfully. Access will continue until end of billing period.',
                'end_date': subscription.end_date.date().isoformat() if subscription.end_date else None,
            })
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post', 'patch'], url_path='auto-renewal')
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
        
        # Get user's billing profile
        try:
            billing_profile = BillingProfile.objects.get(user=user)
        except BillingProfile.DoesNotExist:
            return Response(
                {'error': 'Billing profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Try to find subscription
        try:
            subscription = Subscription.objects.get(id=pk, billing_profile=billing_profile)
            
            # Check if it's mentorship (one-time purchase)
            if subscription.plan and 'mentorship' in subscription.plan.slug.lower():
                return Response({
                    'error': 'Mentorship is a one-time purchase and does not have auto-renewal',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subscription.auto_renew = auto_renew
            subscription.save()
            return Response({
                'message': 'Auto-renewal updated successfully',
                'auto_renew': auto_renew,
            })
        except Subscription.DoesNotExist:
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
        
        # Get user's billing profile
        try:
            billing_profile = BillingProfile.objects.get(user=user)
        except BillingProfile.DoesNotExist:
            return Response(
                {'error': 'Billing profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Try to find subscription
        try:
            subscription = Subscription.objects.get(id=pk, billing_profile=billing_profile)
            
            # Check if mentorship
            is_mentorship = subscription.plan and 'mentorship' in subscription.plan.slug.lower()
            
            if is_mentorship:
                # Mentorship is lifetime, doesn't need reactivation
                if subscription.status == 'active':
                    return Response(
                        {'error': 'Mentorship is already active with lifetime access'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Reactivate if payment was somehow not verified
                subscription.status = 'active'
                subscription.save()
                
                return Response({
                    'message': 'Mentorship access reactivated successfully',
                    'end_date': None,  # Lifetime
                })
            else:
                # Signal subscription
                # Check if active
                is_active = (
                    subscription.status == 'active' and
                    subscription.end_date and
                    timezone.now() <= subscription.end_date
                )
                
                if is_active:
                    return Response(
                        {'error': 'Subscription is already active'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Reactivate for another period
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=30)  # Default to 30 days
                subscription.status = 'active'
                subscription.auto_renew = True
                subscription.save()
                
                return Response({
                    'message': 'Subscription reactivated successfully',
                    'end_date': subscription.end_date.date().isoformat(),
                })
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _get_plan_features(self, subscription, plan_type):
        """
        Get features list for a subscription
        """
        # Get features from the subscription plan's M2M relationship
        if subscription.plan and subscription.plan.features.exists():
            # Return feature names from the Feature model (M2M relationship)
            return [feature.name for feature in subscription.plan.features.all()]
        
        # Fallback to default features based on plan type
        if plan_type == 'signal':
            features = [
                'Daily Trading Signals',
                'Telegram Channel Access',
                'Market Analysis',
                'Entry & Exit Points',
            ]
        elif plan_type == 'mentorship':
            features = [
                'Premium Course Access',
                '1-on-1 Mentorship Sessions',
                'Trading Signals Included',
                'Priority Support',
                'Private Community Access',
            ]
        else:
            features = ['Full Platform Access']
        
        return features
