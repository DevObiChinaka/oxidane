"""
Django signals for subscription lifecycle events.

This module provides:
1. Custom signals for subscription events (created, cancelled, expired, etc.)
2. Signal handlers for automated responses (emails, analytics, Telegram, etc.)
3. Integration points for webhooks, referrals, and audit logging

Signals fire automatically when subscription events occur, enabling a reactive,
event-driven architecture that supports enterprise automation features.
"""
import logging
from decimal import Decimal
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

User = get_user_model()

# ============================================================================
# CUSTOM SIGNALS (Business Events)
# ============================================================================

# Subscription lifecycle signals
subscription_created = Signal()          # When new subscription starts
subscription_renewed = Signal()          # When subscription renews (auto-renewal)
subscription_cancelled = Signal()        # When user cancels
subscription_expired = Signal()          # When subscription ends
subscription_upgraded = Signal()         # When user upgrades to better plan
subscription_downgraded = Signal()       # When user downgrades plan
subscription_suspended = Signal()        # When subscription is suspended (payment failure)
subscription_reactivated = Signal()      # When suspended subscription is reactivated

# Payment signals
payment_received = Signal()              # When payment succeeds
payment_failed = Signal()                # When payment fails

# Referral signals
referral_converted = Signal()            # When referral becomes paying customer
referral_commission_earned = Signal()    # When referrer earns commission

# Feature access signals
feature_access_granted = Signal()        # When user gains feature access
feature_access_revoked = Signal()        # When user loses feature access


# ============================================================================
# BILLINGPROFILE SIGNALS (User Creation)
# ============================================================================

@receiver(post_save, sender=User)
def create_billing_profile(sender, instance, created, **kwargs):
    """
    Automatically create a BillingProfile when a new user is created.
    This ensures every user has a billing profile ready for subscriptions.
    """
    if created:
        from .models import BillingProfile
        BillingProfile.objects.create(user=instance)
        logger.info(f"Created BillingProfile for user {instance.email}")


@receiver(post_save, sender=User)
def save_billing_profile(sender, instance, **kwargs):
    """
    Save the billing profile whenever the user is saved.
    Creates one if it doesn't exist (edge case handling).
    """
    from .models import BillingProfile
    # Check if billing profile exists (more reliable than hasattr)
    try:
        _ = instance.billing_profile
    except BillingProfile.DoesNotExist:
        BillingProfile.objects.create(user=instance)
        logger.warning(f"Missing BillingProfile created for user {instance.email}")


# ============================================================================
# SUBSCRIPTION LIFECYCLE HANDLERS
# ============================================================================

@receiver(subscription_created)
def log_subscription_created(sender, subscription, user, **kwargs):
    """
    Log when a new subscription is created.
    
    Args:
        sender: The model class that sent the signal
        subscription: The Subscription instance
        user: The user who subscribed
    """
    logger.info(
        f"Subscription created: {subscription.id} for user {user.email} "
        f"(Plan: {subscription.plan.name if subscription.plan else 'N/A'})"
    )


@receiver(subscription_created)
def track_subscription_analytics(sender, subscription, user, **kwargs):
    """
    Update analytics when subscription is created.
    
    This increments:
    - Active subscriptions count
    - Monthly Recurring Revenue (MRR)
    - New customer count
    """
    try:
        # Cache key for today's analytics
        today = timezone.now().date()
        cache_key = f"analytics:subscriptions:created:{today}"
        
        # Increment counter
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=86400)  # 24 hours
        
        logger.info(f"Analytics updated for subscription {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to track subscription analytics: {str(e)}")


# Referral system removed - signal handler disabled
# @receiver(subscription_created)
# def credit_referrer_on_subscription(sender, subscription, user, **kwargs):
#     """
#     Credit the referrer when referred user subscribes.
#     """
#     pass


@receiver(subscription_cancelled)
def log_subscription_cancelled(sender, subscription, user, reason, **kwargs):
    """
    Log when a subscription is cancelled.
    
    Args:
        sender: The model class that sent the signal
        subscription: The Subscription instance
        user: The user who cancelled
        reason: Cancellation reason (optional)
    """
    logger.info(
        f"Subscription cancelled: {subscription.id} for user {user.email} "
        f"(Reason: {reason or 'Not provided'})"
    )


@receiver(subscription_cancelled)
def track_churn_analytics(sender, subscription, user, reason, **kwargs):
    """
    Track churn when subscription is cancelled.
    
    Updates:
    - Churn count
    - Churn reasons
    - Retention metrics
    """
    try:
        # Cache key for today's analytics
        today = timezone.now().date()
        cache_key = f"analytics:subscriptions:cancelled:{today}"
        
        # Increment counter
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=86400)  # 24 hours
        
        # Track cancellation reason
        if reason:
            reason_key = f"analytics:churn_reasons:{today}"
            reasons = cache.get(reason_key, {})
            reasons[reason] = reasons.get(reason, 0) + 1
            cache.set(reason_key, reasons, timeout=86400)
        
        logger.info(f"Churn analytics updated for subscription {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to track churn analytics: {str(e)}")


@receiver(subscription_expired)
def log_subscription_expired(sender, subscription, user, **kwargs):
    """
    Log when a subscription expires.
    
    Args:
        sender: The model class that sent the signal
        subscription: The Subscription instance
        user: The user whose subscription expired
    """
    logger.info(
        f"Subscription expired: {subscription.id} for user {user.email} "
        f"(Ended: {subscription.end_date})"
    )


@receiver(subscription_expired)
def revoke_expired_subscription_access(sender, subscription, user, **kwargs):
    """
    Revoke feature access when subscription expires.
    
    This fires feature_access_revoked signals for all features in the expired plan.
    """
    if not subscription.plan:
        return
    
    try:
        # Get all features from the plan
        features = subscription.plan.features.all()
        
        for feature in features:
            # Fire feature access revoked signal
            feature_access_revoked.send(
                sender=subscription.__class__,
                subscription=subscription,
                feature=feature,
                user=user
            )
        
        logger.info(
            f"Revoked access to {features.count()} features for user {user.email} "
            f"(Subscription {subscription.id} expired)"
        )
    except Exception as e:
        logger.error(f"Failed to revoke subscription access: {str(e)}")


@receiver(subscription_expired)
def send_subscription_expired_email(sender, subscription, user, **kwargs):
    """
    Send email notification when subscription expires.
    
    This notifies the user that their subscription has ended and they've
    lost access to premium features.
    
    Args:
        sender: The model class that sent the signal
        subscription: The Subscription instance that expired
        user: The user whose subscription expired
    """
    try:
        from users.email_automation import send_subscription_expired_email as send_email
        
        # Prepare subscription details for email
        # Note: The template expects these specific variable names
        subscription_details = {
            'plan_name': subscription.plan.name if subscription.plan else 'Your Plan',
            'days_remaining': 0,  # Already expired
            'subscription_end': subscription.end_date.strftime("%B %d, %Y") if subscription.end_date else 'recently',
            'renewal_url': 'https://oxidane.com/pricing',  # Resubscribe URL
            'support_email': 'support@oxidane.com'
        }
        
        # Send email
        result = send_email(
            user=user,
            subscription_details=subscription_details,
            test_mode=False
        )
        
        if result and result.get('success'):
            logger.info(
                f"Subscription expiry email sent to {user.email} "
                f"(Subscription {subscription.id})"
            )
        else:
            logger.warning(
                f"Failed to send subscription expiry email to {user.email}: "
                f"{result.get('error') if result else 'Unknown error'}"
            )
    
    except Exception as e:
        logger.error(
            f"Error sending subscription expiry email to {user.email}: {str(e)}",
            exc_info=True
        )


@receiver(subscription_upgraded)
def log_subscription_upgraded(sender, old_subscription, new_subscription, user, **kwargs):
    """
    Log when a subscription is upgraded.
    
    Args:
        sender: The model class
        old_subscription: Previous subscription
        new_subscription: New upgraded subscription
        user: The user who upgraded
    """
    old_plan = old_subscription.plan.name if old_subscription.plan else 'N/A'
    new_plan = new_subscription.plan.name if new_subscription.plan else 'N/A'
    
    logger.info(
        f"Subscription upgraded: {user.email} from {old_plan} to {new_plan}"
    )


@receiver(subscription_downgraded)
def log_subscription_downgraded(sender, old_subscription, new_subscription, user, **kwargs):
    """
    Log when a subscription is downgraded.
    
    Args:
        sender: The model class
        old_subscription: Previous subscription
        new_subscription: New downgraded subscription
        user: The user who downgraded
    """
    old_plan = old_subscription.plan.name if old_subscription.plan else 'N/A'
    new_plan = new_subscription.plan.name if new_subscription.plan else 'N/A'
    
    logger.info(
        f"Subscription downgraded: {user.email} from {old_plan} to {new_plan}"
    )


@receiver(subscription_suspended)
def log_subscription_suspended(sender, subscription, user, reason, **kwargs):
    """
    Log when a subscription is suspended (usually due to payment failure).
    
    Args:
        sender: The model class
        subscription: The suspended subscription
        user: The user whose subscription was suspended
        reason: Suspension reason
    """
    logger.warning(
        f"Subscription suspended: {subscription.id} for user {user.email} "
        f"(Reason: {reason})"
    )


@receiver(subscription_reactivated)
def log_subscription_reactivated(sender, subscription, user, **kwargs):
    """
    Log when a suspended subscription is reactivated.
    
    Args:
        sender: The model class
        subscription: The reactivated subscription
        user: The user whose subscription was reactivated
    """
    logger.info(
        f"Subscription reactivated: {subscription.id} for user {user.email}"
    )


# ============================================================================
# PAYMENT SIGNAL HANDLERS
# ============================================================================

@receiver(payment_received)
def log_payment_received(sender, subscription, amount, payment_reference, **kwargs):
    """
    Log when payment is received.
    
    Args:
        sender: The model class
        subscription: The subscription that was paid for
        amount: Payment amount
        payment_reference: Payment reference/transaction ID
    """
    logger.info(
        f"Payment received: {amount} for subscription {subscription.id} "
        f"(Reference: {payment_reference})"
    )


@receiver(payment_received)
def update_revenue_analytics(sender, subscription, amount, payment_reference, **kwargs):
    """
    Update revenue analytics when payment is received.
    
    Tracks:
    - Total revenue
    - Revenue by plan
    - Revenue by currency
    """
    try:
        today = timezone.now().date()
        
        # Total revenue
        revenue_key = f"analytics:revenue:total:{today}"
        total_revenue = cache.get(revenue_key, Decimal('0'))
        cache.set(revenue_key, total_revenue + Decimal(str(amount)), timeout=86400)
        
        # Revenue by plan
        if subscription.plan:
            plan_key = f"analytics:revenue:plan:{subscription.plan.id}:{today}"
            plan_revenue = cache.get(plan_key, Decimal('0'))
            cache.set(plan_key, plan_revenue + Decimal(str(amount)), timeout=86400)
        
        logger.info(f"Revenue analytics updated: {amount}")
    except Exception as e:
        logger.error(f"Failed to update revenue analytics: {str(e)}")


@receiver(payment_failed)
def log_payment_failed(sender, subscription, amount, reason, **kwargs):
    """
    Log when payment fails.
    
    Args:
        sender: The model class
        subscription: The subscription payment failed for
        amount: Payment amount that failed
        reason: Failure reason
    """
    logger.error(
        f"Payment failed: {amount} for subscription {subscription.id} "
        f"(Reason: {reason})"
    )


@receiver(payment_failed)
def track_payment_failure(sender, subscription, amount, reason, **kwargs):
    """
    Track payment failure metrics.
    
    This is used for dunning system to retry failed payments.
    """
    try:
        today = timezone.now().date()
        
        # Payment failure count
        failure_key = f"analytics:payment_failures:{today}"
        count = cache.get(failure_key, 0)
        cache.set(failure_key, count + 1, timeout=86400)
        
        # Track failure reasons
        reason_key = f"analytics:payment_failure_reasons:{today}"
        reasons = cache.get(reason_key, {})
        reasons[reason] = reasons.get(reason, 0) + 1
        cache.set(reason_key, reasons, timeout=86400)
        
        logger.info(f"Payment failure tracked for subscription {subscription.id}")
    except Exception as e:
        logger.error(f"Failed to track payment failure: {str(e)}")


# ============================================================================
# REFERRAL SIGNAL HANDLERS
# ============================================================================

@receiver(referral_converted)
def log_referral_conversion(sender, referral, referred_user, subscription, **kwargs):
    """
    Log when a referral converts to a paying customer.
    
    Args:
        sender: The model class
        referral: The Referral instance
        referred_user: The user who was referred
        subscription: The subscription that converted the referral
    """
    logger.info(
        f"Referral converted: {referred_user.email} subscribed "
        f"(Referrer: {referral.referral_code.referrer.email})"
    )


@receiver(referral_commission_earned)
def log_commission_earned(sender, credit, referrer, amount, **kwargs):
    """
    Log when a referrer earns commission.
    
    Args:
        sender: The ReferralCredit model class
        credit: The ReferralCredit instance
        referrer: The user who earned commission
        amount: Commission amount
    """
    logger.info(
        f"Commission earned: {referrer.email} earned {amount} "
        f"(Credit ID: {credit.id})"
    )


# ============================================================================
# FEATURE ACCESS SIGNAL HANDLERS
# ============================================================================

@receiver(feature_access_granted)
def log_feature_access_granted(sender, subscription, feature, user, **kwargs):
    """
    Log when user gains access to a feature.
    
    Args:
        sender: The model class
        subscription: The subscription granting access
        feature: The Feature instance
        user: The user gaining access
    """
    logger.info(
        f"Feature access granted: {feature.name} to {user.email} "
        f"(Subscription: {subscription.id})"
    )


@receiver(feature_access_revoked)
def log_feature_access_revoked(sender, subscription, feature, user, **kwargs):
    """
    Log when user loses access to a feature.
    
    Args:
        sender: The model class
        subscription: The subscription that expired
        feature: The Feature instance
        user: The user losing access
    """
    logger.info(
        f"Feature access revoked: {feature.name} from {user.email} "
        f"(Subscription: {subscription.id})"
    )


# ============================================================================
# SUBSCRIPTION MODEL INTEGRATION
# ============================================================================

@receiver(post_save, sender='subscriptions.Subscription')
def handle_subscription_changes(sender, instance, created, **kwargs):
    """
    Central handler for subscription model changes.
    
    This fires appropriate custom signals based on subscription state changes.
    Integrates with the Subscription model's save() method.
    """
    from .models import Subscription
    
    subscription = instance
    user = subscription.billing_profile.user if subscription.billing_profile else None
    
    if not user:
        logger.warning(f"Subscription {subscription.id} has no associated user")
        return
    
    # New subscription created
    if created:
        subscription_created.send(
            sender=Subscription,
            subscription=subscription,
            user=user
        )
        
        # Grant feature access
        if subscription.plan:
            for feature in subscription.plan.features.all():
                feature_access_granted.send(
                    sender=Subscription,
                    subscription=subscription,
                    feature=feature,
                    user=user
                )
        return
    
    # Use pre_save captured old status to detect changes
    old_status = getattr(subscription, '_old_status', None)
    if not old_status:
        return  # Can't detect change without old status
    
    # Status changed to cancelled
    if old_status != 'cancelled' and subscription.status == 'cancelled':
        subscription_cancelled.send(
            sender=Subscription,
            subscription=subscription,
            user=user,
            reason=subscription.cancellation_reason or ''
        )
    
    # Status changed to expired
    elif old_status == 'active' and subscription.status == 'expired':
        subscription_expired.send(
            sender=Subscription,
            subscription=subscription,
            user=user
        )
    
    # Status changed to suspended
    elif old_status == 'active' and subscription.status == 'suspended':
        subscription_suspended.send(
            sender=Subscription,
            subscription=subscription,
            user=user,
            reason='Payment failure or administrative action'
        )
    
    # Reactivated from suspended
    elif old_status == 'suspended' and subscription.status == 'active':
        subscription_reactivated.send(
            sender=Subscription,
            subscription=subscription,
            user=user
        )


@receiver(pre_save, sender='subscriptions.Subscription')
def detect_subscription_changes(sender, instance, **kwargs):
    """
    Detect changes before subscription is saved.
    
    This is used to capture the old state before it's overwritten.
    """
    if instance.pk:
        try:
            from .models import Subscription
            old = Subscription.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_plan_id = old.plan_id if old.plan else None
        except Exception:
            pass


# ============================================================================
# UTILITY FUNCTIONS (For Manual Signal Emission)
# ============================================================================

def emit_payment_received_signal(subscription, amount, payment_reference):
    """
    Manually emit payment_received signal.
    
    Use this in payment webhook handlers when payment succeeds.
    
    Args:
        subscription: Subscription instance
        amount: Payment amount (Decimal or float)
        payment_reference: Payment reference/transaction ID (string)
    
    Example:
        from subscriptions.signals import emit_payment_received_signal
        emit_payment_received_signal(subscription, 99.99, 'pay_abc123')
    """
    from .models import Subscription
    
    payment_received.send(
        sender=Subscription,
        subscription=subscription,
        amount=Decimal(str(amount)),
        payment_reference=payment_reference
    )
    logger.info(f"Payment received signal emitted for {subscription.id}")


def emit_payment_failed_signal(subscription, amount, reason):
    """
    Manually emit payment_failed signal.
    
    Use this in payment webhook handlers when payment fails.
    
    Args:
        subscription: Subscription instance
        amount: Payment amount that failed (Decimal or float)
        reason: Failure reason (string)
    
    Example:
        from subscriptions.signals import emit_payment_failed_signal
        emit_payment_failed_signal(subscription, 99.99, 'Insufficient funds')
    """
    from .models import Subscription
    
    payment_failed.send(
        sender=Subscription,
        subscription=subscription,
        amount=Decimal(str(amount)),
        reason=reason
    )
    logger.warning(f"Payment failed signal emitted for {subscription.id}: {reason}")


def emit_referral_converted_signal(referral, referred_user, subscription):
    """
    Manually emit referral_converted signal.
    
    Use this when a referred user completes their first subscription.
    
    Args:
        referral: Referral instance
        referred_user: User who was referred
        subscription: Subscription that converted the referral
    
    Example:
        from subscriptions.signals import emit_referral_converted_signal
        emit_referral_converted_signal(referral, user, subscription)
    """
    from .models import Referral
    
    referral_converted.send(
        sender=Referral,
        referral=referral,
        referred_user=referred_user,
        subscription=subscription
    )
    logger.info(f"Referral converted signal emitted for {referred_user.email}")


def emit_subscription_renewed_signal(subscription, user):
    """
    Manually emit subscription_renewed signal.
    
    Use this when a subscription auto-renews successfully.
    
    Args:
        subscription: Subscription instance
        user: User whose subscription renewed
    
    Example:
        from subscriptions.signals import emit_subscription_renewed_signal
        emit_subscription_renewed_signal(subscription, user)
    """
    from .models import Subscription
    
    subscription_renewed.send(
        sender=Subscription,
        subscription=subscription,
        user=user
    )
    logger.info(f"Subscription renewed signal emitted for {user.email}")


def emit_subscription_upgraded_signal(old_subscription, new_subscription, user):
    """
    Manually emit subscription_upgraded signal.
    
    Use this when user upgrades to a better plan.
    
    Args:
        old_subscription: Previous subscription
        new_subscription: New upgraded subscription
        user: User who upgraded
    
    Example:
        from subscriptions.signals import emit_subscription_upgraded_signal
        emit_subscription_upgraded_signal(old_sub, new_sub, user)
    """
    from .models import Subscription
    
    subscription_upgraded.send(
        sender=Subscription,
        old_subscription=old_subscription,
        new_subscription=new_subscription,
        user=user
    )
    logger.info(f"Subscription upgraded signal emitted for {user.email}")


def emit_subscription_downgraded_signal(old_subscription, new_subscription, user):
    """
    Manually emit subscription_downgraded signal.
    
    Use this when user downgrades to a cheaper plan.
    
    Args:
        old_subscription: Previous subscription
        new_subscription: New downgraded subscription
        user: User who downgraded
    
    Example:
        from subscriptions.signals import emit_subscription_downgraded_signal
        emit_subscription_downgraded_signal(old_sub, new_sub, user)
    """
    from .models import Subscription
    
    subscription_downgraded.send(
        sender=Subscription,
        old_subscription=old_subscription,
        new_subscription=new_subscription,
        user=user
    )
    logger.info(f"Subscription downgraded signal emitted for {user.email}")


# ============================================================================
# SIGNAL TESTING UTILITIES
# ============================================================================

def get_signal_receivers(signal_obj):
    """
    Get all receivers connected to a signal (for testing/debugging).
    
    Args:
        signal_obj: Signal instance (e.g., subscription_created)
    
    Returns:
        list: List of receiver functions
    
    Example:
        from subscriptions.signals import subscription_created, get_signal_receivers
        receivers = get_signal_receivers(subscription_created)
        print(f"Found {len(receivers)} receivers")
    """
    return [receiver[1]() for receiver in signal_obj.receivers if receiver[1]()]


def disconnect_all_handlers(signal_obj):
    """
    Disconnect all handlers from a signal (for testing).
    
    Args:
        signal_obj: Signal instance
    
    Warning:
        Use only in tests! This will break production functionality.
    
    Example:
        from subscriptions.signals import subscription_created, disconnect_all_handlers
        disconnect_all_handlers(subscription_created)
    """
    signal_obj.receivers = []
    logger.warning(f"Disconnected all handlers from {signal_obj}")


# ============================================================================
# SIGNAL SUMMARY
# ============================================================================

"""
AVAILABLE SIGNALS:

Subscription Lifecycle:
- subscription_created: Fires when new subscription starts
- subscription_renewed: Fires when subscription auto-renews
- subscription_cancelled: Fires when user cancels
- subscription_expired: Fires when subscription ends
- subscription_upgraded: Fires when user upgrades plan
- subscription_downgraded: Fires when user downgrades plan
- subscription_suspended: Fires when subscription is suspended
- subscription_reactivated: Fires when suspended subscription reactivates

Payment Events:
- payment_received: Fires when payment succeeds
- payment_failed: Fires when payment fails

Referral Events:
- referral_converted: Fires when referral becomes paying customer
- referral_commission_earned: Fires when referrer earns commission

Feature Access:
- feature_access_granted: Fires when user gains feature access
- feature_access_revoked: Fires when user loses feature access

HANDLERS:
Each signal has multiple handlers for:
- Logging (all signals)
- Analytics tracking (subscription/payment signals)
- Referral credits (subscription_created)
- Churn tracking (subscription_cancelled)
- Feature access management (subscription_created/expired)
- Revenue tracking (payment_received)

USAGE:
Most signals fire automatically via model save() integration.
For manual emission in webhooks or views, use utility functions:
- emit_payment_received_signal()
- emit_payment_failed_signal()
- emit_referral_converted_signal()
- emit_subscription_renewed_signal()
- emit_subscription_upgraded_signal()
- emit_subscription_downgraded_signal()

TESTING:
- get_signal_receivers(signal): Get all receivers for a signal
- disconnect_all_handlers(signal): Remove all handlers (test only)
"""
