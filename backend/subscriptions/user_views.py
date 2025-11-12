"""
User-facing subscription views
Provides subscription information for authenticated users
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Subscription, BillingProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_subscriptions(request):
    """
    Get all subscriptions for the authenticated user with stats
    
    Returns:
        {
            'subscriptions': [
                {
                    'id': uuid,
                    'plan_name': str,
                    'status': str,
                    'start_date': datetime,
                    'end_date': datetime,
                    'days_remaining': int,
                    'amount_paid': decimal,
                    'currency': str,
                    'auto_renew': bool,
                    'features': {...},
                    'is_trial': bool,
                    'trial_end_date': datetime,
                    'days_until_trial_end': int
                },
                ...
            ],
            'stats': {
                'active_count': int,
                'total_monthly_cost': decimal,
                'next_renewal_date': datetime,
                'days_until_renewal': int,
            }
        }
    """
    user = request.user
    
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
    
    # Get active subscriptions
    subscriptions = Subscription.objects.filter(
        billing_profile=billing_profile,
        status='active'
    ).select_related('plan').order_by('-created_at')
    
    subscription_list = []
    total_monthly_cost = 0  # Total in USD (plan base prices)
    next_renewal_date = None
    
    for sub in subscriptions:
        # Check if subscription is actually active
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
            
            # Track earliest renewal date
            if next_renewal_date is None or sub.end_date < next_renewal_date:
                next_renewal_date = sub.end_date
        
        # Determine actual status
        if is_active:
            subscription_status = 'active'
        elif sub.end_date and timezone.now() > sub.end_date:
            subscription_status = 'expired'
        else:
            subscription_status = 'cancelled'
        
        # Get plan features - return as array of feature names (strings)
        features = []
        if sub.plan:
            # Get features from the plan's many-to-many relationship
            plan_features = sub.plan.features.all()
            for feature in plan_features:
                # Frontend expects simple string array, use icon + name for display
                features.append(f"{feature.icon} {feature.name}")
        
        subscription_data = {
            'id': str(sub.id),
            'plan_name': sub.plan.name if sub.plan else 'Unknown Plan',
            'plan_slug': sub.plan.slug if sub.plan else '',
            'billing_cycle': sub.plan.billing_period if sub.plan else 'monthly',  # weekly, monthly, one_time
            'status': subscription_status,
            'start_date': sub.start_date.isoformat() if sub.start_date else None,
            'end_date': sub.end_date.isoformat() if sub.end_date else None,
            'days_remaining': days_remaining,
            'is_lifetime': sub.plan.billing_period == 'lifetime' if sub.plan else False,
            'amount_paid': float(sub.amount_paid) if sub.amount_paid else 0,  # Actual amount paid
            'currency': sub.currency,  # Currency they paid in (NGN/USD)
            'plan_base_price': float(sub.plan.base_price) if sub.plan else 0,  # Plan's base price in USD
            'plan_currency': 'USD',  # Plans are priced in USD by default
            'auto_renew': sub.auto_renew,
            'features': features,
        }
        
        subscription_list.append(subscription_data)
        
        # Add to monthly cost using plan base price (USD) for consistency
        # This represents the recurring cost, not what they paid with coupons/discounts
        if is_active and sub.plan:
            total_monthly_cost += float(sub.plan.base_price)
    
    # Calculate days until renewal
    days_until_renewal = None
    if next_renewal_date:
        days_until_renewal = (next_renewal_date - timezone.now()).days
    
    return Response({
        'subscriptions': subscription_list,
        'stats': {
            'active_count': len([s for s in subscription_list if s['status'] == 'active']),
            'total_monthly_cost': total_monthly_cost,
            'next_renewal_date': next_renewal_date.isoformat() if next_renewal_date else None,
            'days_until_renewal': days_until_renewal,
        }
    })
