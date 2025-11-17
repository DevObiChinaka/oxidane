"""
Payment Method Management Views
Handles saving, listing, and managing user payment methods (cards)
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import logging

from subscriptions.models import BillingProfile, PaymentMethod, Subscription, PaymentConfiguration
from subscriptions.payment_service import PaystackService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_payment_method(request):
    """
    Save payment method from Paystack transaction
    
    POST /api/payment-methods/save/
    {
        "reference": "TXN_1234567890"  // Paystack transaction reference
    }
    
    Returns:
        201: Payment method saved successfully
        400: Validation errors
        404: Billing profile not found
    """
    user = request.user
    reference = request.data.get('reference')
    
    if not reference:
        return Response(
            {'error': 'Transaction reference is required'},
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
    
    # Verify transaction with Paystack
    paystack = PaystackService()
    verification_result = paystack.verify_payment(reference)
    
    if not verification_result.get('success'):
        return Response(
            {'error': 'Payment verification failed', 'details': verification_result.get('error')},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not verification_result.get('verified'):
        return Response(
            {'error': 'Payment was not successful'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Extract authorization details
    authorization = paystack.extract_authorization_from_verification(verification_result)
    
    if not authorization:
        return Response(
            {'error': 'No reusable authorization found in transaction'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if payment method already exists with same authorization
    existing_method = PaymentMethod.objects.filter(
        billing_profile=billing_profile,
        gateway_authorization_code=authorization['authorization_code']
    ).first()
    
    if existing_method:
        # Update last used and make it active/default
        existing_method.last_used_at = timezone.now()
        existing_method.is_active = True
        existing_method.is_default = True
        existing_method.save()
        
        # Deactivate all other payment methods (enforce single payment method)
        PaymentMethod.objects.filter(
            billing_profile=billing_profile,
            is_active=True
        ).exclude(id=existing_method.id).update(is_active=False, is_default=False)
        
        return Response({
            'message': 'Payment method updated as your primary card',
            'payment_method': {
                'id': str(existing_method.id),
                'card_type': existing_method.card_brand,
                'last4': existing_method.card_last4,
                'exp_month': existing_method.card_exp_month,
                'exp_year': existing_method.card_exp_year,
                'is_default': existing_method.is_default,
            }
        }, status=status.HTTP_200_OK)
    
    # Deactivate all existing payment methods (enforce single payment method policy)
    old_methods = PaymentMethod.objects.filter(
        billing_profile=billing_profile,
        is_active=True
    )
    if old_methods.exists():
        logger.info(f"Replacing {old_methods.count()} old payment method(s) for user {user.email}")
        old_methods.update(is_active=False, is_default=False)
    
    # Create new payment method (always set as default since it's the only active one)
    payment_method = PaymentMethod.objects.create(
        billing_profile=billing_profile,
        payment_type='card',
        gateway_authorization_code=authorization['authorization_code'],
        card_last4=authorization['last4'],
        card_brand=authorization['brand'],
        card_exp_month=authorization['exp_month'],
        card_exp_year=authorization['exp_year'],
        bank_name=authorization.get('bank', ''),
        is_default=True,  # Always default (only one active)
        is_active=True
    )
    
    payment_method.last_used_at = timezone.now()
    payment_method.save()
    
    logger.info(f"Payment method saved for user {user.email}: {payment_method.card_brand} ****{payment_method.card_last4}")
    
    return Response({
        'message': 'Payment method saved successfully',
        'payment_method': {
            'id': str(payment_method.id),
            'card_type': payment_method.card_brand,
            'last4': payment_method.card_last4,
            'exp_month': payment_method.card_exp_month,
            'exp_year': payment_method.card_exp_year,
            'is_default': payment_method.is_default,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payment_methods(request):
    """
    List user's saved payment methods
    
    GET /api/payment-methods/
    
    Returns:
        200: List of payment methods
        404: Billing profile not found
    """
    user = request.user
    
    try:
        billing_profile = BillingProfile.objects.get(user=user)
    except BillingProfile.DoesNotExist:
        return Response(
            {'error': 'Billing profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    payment_methods = billing_profile.payment_methods.filter(is_active=True)
    
    methods_data = [{
        'id': str(pm.id),
        'payment_type': pm.payment_type,
        'card_brand': pm.card_brand,
        'card_last4': pm.card_last4,
        'card_exp_month': pm.card_exp_month,
        'card_exp_year': pm.card_exp_year,
        'bank_name': pm.bank_name,
        'is_default': pm.is_default,
        'last_used_at': pm.last_used_at.isoformat() if pm.last_used_at else None,
    } for pm in payment_methods]
    
    return Response({
        'payment_methods': methods_data,
        'count': len(methods_data)
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def set_default_payment_method(request, payment_method_id):
    """
    Set a payment method as default
    
    PATCH /api/payment-methods/<id>/set-default/
    
    Returns:
        200: Default payment method updated
        404: Payment method not found
        403: Not authorized
    """
    user = request.user
    
    try:
        billing_profile = BillingProfile.objects.get(user=user)
        payment_method = PaymentMethod.objects.get(
            id=payment_method_id,
            billing_profile=billing_profile,
            is_active=True
        )
    except BillingProfile.DoesNotExist:
        return Response(
            {'error': 'Billing profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except PaymentMethod.DoesNotExist:
        return Response(
            {'error': 'Payment method not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Set as default (model's save() method handles unsetting others)
    payment_method.is_default = True
    payment_method.save()
    
    return Response({
        'message': 'Default payment method updated',
        'payment_method_id': str(payment_method.id)
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_payment_method(request, payment_method_id):
    """
    Delete (deactivate) a payment method
    
    DELETE /api/payment-methods/<id>/
    
    Returns:
        200: Payment method deleted
        400: Cannot delete default if auto-renewal active
        404: Payment method not found
    """
    user = request.user
    
    try:
        billing_profile = BillingProfile.objects.get(user=user)
        payment_method = PaymentMethod.objects.get(
            id=payment_method_id,
            billing_profile=billing_profile
        )
    except BillingProfile.DoesNotExist:
        return Response(
            {'error': 'Billing profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except PaymentMethod.DoesNotExist:
        return Response(
            {'error': 'Payment method not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if any active subscriptions depend on this payment method
    dependent_subscriptions = Subscription.objects.filter(
        billing_profile=billing_profile,
        payment_method=payment_method,
        status='active',
        auto_renew=True
    )
    
    if dependent_subscriptions.exists():
        # Disable auto-renewal on these subscriptions
        dependent_subscriptions.update(auto_renew=False)
        logger.info(f"Disabled auto-renewal for {dependent_subscriptions.count()} subscriptions due to payment method deletion")
    
    # Deactivate payment method (don't actually delete for audit trail)
    payment_method.is_active = False
    payment_method.is_default = False
    payment_method.save()
    
    logger.info(f"Payment method deleted for user {user.email}: {payment_method.card_brand} ****{payment_method.card_last4}")
    
    return Response({
        'message': 'Payment method deleted successfully',
        'affected_subscriptions': dependent_subscriptions.count()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_config(request):
    """
    Get Paystack public key for frontend integration
    
    GET /api/payment-methods/config/
    
    Returns:
        200: { 
            "paystack_public_key": "pk_test_...",
            "paystack_enabled": true
        }
    """
    config = PaymentConfiguration.get_instance()
    
    return Response({
        'paystack_public_key': config.paystack_public_key,
        'paystack_enabled': config.paystack_enabled
    }, status=status.HTTP_200_OK)
