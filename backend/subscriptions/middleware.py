"""
Subscription validation middleware.

This middleware provides real-time subscription status validation
as a failsafe mechanism in case Celery Beat fails.

It runs on EVERY authenticated request and automatically expires
subscriptions that have passed their end_date but are still marked
as active.
"""
import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SubscriptionValidationMiddleware(MiddlewareMixin):
    """
    Real-time subscription validation middleware.
    
    Checks if user's subscription has expired on EVERY request
    and updates status accordingly. This acts as a failsafe
    in case Celery Beat's check_expired_subscriptions task fails.
    
    Benefits:
    - Catches expired subscriptions in real-time
    - Works even if Celery Beat is down
    - Minimal performance impact (single DB query for authenticated users)
    - Automatically triggers Django signals (subscription_expired)
    - Self-healing: fixes inconsistent states automatically
    
    Usage:
        Add to MIDDLEWARE in settings.py:
        
        MIDDLEWARE = [
            ...
            'subscriptions.middleware.SubscriptionValidationMiddleware',
            ...
        ]
    """
    
    def process_request(self, request):
        """
        Check subscription status before processing request.
        
        Only runs for authenticated users to minimize performance impact.
        Applies 24-hour grace period consistent with scheduled expiration task.
        """
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
        
        # Skip for staff/admin (they don't have regular subscriptions)
        if request.user.is_staff or request.user.is_superuser:
            return None
        
        try:
            # Import here to avoid circular imports
            from subscriptions.models import Subscription
            from subscriptions.tasks import remove_user_from_telegram_groups
            from datetime import timedelta
            
            # Get user's active subscriptions
            active_subscriptions = Subscription.objects.filter(
                billing_profile__user=request.user,
                status='active'
            ).select_related('plan', 'billing_profile__user')
            
            now = timezone.now()
            grace_cutoff = now - timedelta(hours=24)  # 24-hour grace period
            expired_count = 0
            
            for subscription in active_subscriptions:
                # Check if subscription is past grace period (24 hours after end_date)
                if subscription.end_date < grace_cutoff:
                    # This should have been caught by Celery Beat
                    # but wasn't - fix it now
                    hours_past = int((now - subscription.end_date).total_seconds() / 3600)
                    logger.warning(
                        f"Middleware caught expired subscription {subscription.id} "
                        f"for user {request.user.email} (ended {subscription.end_date}, "
                        f"{hours_past} hours ago, past 24-hour grace period). "
                        f"This indicates Celery Beat may have missed this expiration."
                    )
                    
                    # Mark as expired
                    subscription.status = 'expired'
                    subscription.save()  # This triggers post_save signal → subscription_expired signal
                    
                    # Update user status
                    request.user.subscription_status = 'expired'
                    request.user.save()
                    
                    # Queue Telegram removal (same as Celery Beat would do)
                    if subscription.plan:
                        try:
                            remove_user_from_telegram_groups.delay(
                                request.user.id, 
                                str(subscription.plan.id)
                            )
                            logger.info(
                                f"Queued Telegram removal for user {request.user.id} "
                                f"from plan {subscription.plan.name}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to queue Telegram removal for user {request.user.id}: {e}"
                            )
                    
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(
                    f"Middleware expired {expired_count} subscription(s) "
                    f"for user {request.user.email}"
                )
        
        except Exception as e:
            # Never block requests due to subscription check errors
            logger.error(f"Error in SubscriptionValidationMiddleware: {e}", exc_info=True)
        
        return None
    
    def process_response(self, request, response):
        """
        Process response (no action needed, just pass through).
        """
        return response


class SubscriptionCacheMiddleware(MiddlewareMixin):
    """
    OPTIONAL: Cache subscription status on request object for performance.
    
    If you have many views checking subscription status, this middleware
    caches the subscription on request.subscription to avoid repeated DB queries.
    
    Usage:
        Add AFTER SubscriptionValidationMiddleware:
        
        MIDDLEWARE = [
            ...
            'subscriptions.middleware.SubscriptionValidationMiddleware',
            'subscriptions.middleware.SubscriptionCacheMiddleware',  # Optional
            ...
        ]
        
        In views:
            subscription = request.subscription  # No DB query
    """
    
    def process_request(self, request):
        """Cache user's active subscription on request object."""
        request.subscription = None
        
        if not request.user.is_authenticated:
            return None
        
        try:
            from subscriptions.models import Subscription
            
            # Get active subscription
            subscription = Subscription.objects.filter(
                billing_profile__user=request.user,
                status='active'
            ).select_related('plan', 'billing_profile__user').first()
            
            request.subscription = subscription
        
        except Exception as e:
            logger.error(f"Error in SubscriptionCacheMiddleware: {e}", exc_info=True)
        
        return None
