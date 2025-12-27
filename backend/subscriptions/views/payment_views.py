"""
Payment API Views
Handles payment initialization, verification, webhooks, and invoice generation

Endpoints:
- POST /api/payments/initialize/ - Initialize payment
- POST /api/payments/verify/ - Verify payment
- POST /api/payments/webhook/paystack/ - Paystack webhook
- POST /api/payments/webhook/stripe/ - Stripe webhook
- GET /api/payments/history/ - Payment history
- GET /api/payments/{id}/invoice/ - Download invoice

Created: November 10, 2025
"""

import logging
import uuid
import json
import time
from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from ..models import (
    SubscriptionPlan, 
    Payment, 
    PaymentMethod,
    PaymentConfiguration,
    Coupon,
    BillingProfile,
    Subscription,
    ExchangeRate
)
from ..serializers import PaymentSerializer
from ..payment_service import PaystackService, StripeService, PaymentService
from ..payment_calculator import PaymentCalculator
from ..tasks import (
    activate_subscription,
    add_user_to_telegram_groups,
    send_payment_receipt_email,
)

logger = logging.getLogger(__name__)


class PaymentPagination(PageNumberPagination):
    """Pagination for payment history"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_pending_payment(request):
    """
    Check if user has a pending payment for a plan
    Prevents duplicate payment attempts and allows resuming interrupted payments
    
    POST /api/payments/check-pending/
    
    Request Body:
        {
            "plan_id": "uuid-string"
        }
    
    Response:
        {
            "has_pending": true,
            "reference": "PAY_ABC123",
            "payment_url": "https://checkout.paystack.com/...",
            "amount": 5000.00,
            "created_at": "2025-12-27T10:30:00Z"
        }
    """
    try:
        plan_id = request.data.get('plan_id')
        
        if not plan_id:
            return Response({
                'success': False,
                'error': 'plan_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's billing profile
        try:
            billing_profile = BillingProfile.objects.get(user=request.user)
        except BillingProfile.DoesNotExist:
            return Response({
                'has_pending': False
            }, status=status.HTTP_200_OK)
        
        # Check for recent pending payment (last 30 minutes)
        pending_payment = Payment.objects.filter(
            billing_profile=billing_profile,
            status__in=['pending', 'processing'],
            created_at__gte=timezone.now() - timedelta(minutes=30),
            gateway_response__metadata__plan_id=str(plan_id)
        ).order_by('-created_at').first()
        
        if pending_payment and pending_payment.gateway_response.get('authorization_url'):
            logger.info(f"Found pending payment {pending_payment.gateway_reference} for user {request.user.id}")
            
            return Response({
                'has_pending': True,
                'reference': pending_payment.gateway_reference,
                'payment_url': pending_payment.gateway_response.get('authorization_url'),
                'amount': float(pending_payment.total_amount),
                'currency': pending_payment.currency,
                'created_at': pending_payment.created_at.isoformat(),
                'payment_id': str(pending_payment.id)
            }, status=status.HTTP_200_OK)
        
        return Response({
            'has_pending': False
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking pending payment: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Failed to check pending payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitializePaymentView(APIView):
    """
    Initialize a payment transaction
    
    POST /api/payments/initialize/
    
    Request Body:
        {
            "plan_id": 1,
            "currency": "NGN",  # Optional, defaults to plan currency
            "coupon_code": "WELCOME50",  # Optional
            "gateway": "paystack",  # Optional, defaults to primary provider
            "callback_url": "https://example.com/payment-success"  # Optional
        }
    
    Response:
        {
            "success": true,
            "payment_url": "https://checkout.paystack.com/...",
            "reference": "PAY_123456",
            "amount": 5000.00,
            "processing_fee": 100.00,
            "total_amount": 5100.00,
            "currency": "NGN",
            "gateway": "paystack"
        }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get request data
            plan_id = request.data.get('plan_id')
            currency = request.data.get('currency', '')
            coupon_code = request.data.get('coupon_code', '')
            gateway = request.data.get('gateway', '')
            callback_url = request.data.get('callback_url', '')
            
            # Validate plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid subscription plan'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create billing profile
            billing_profile, created = BillingProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'billing_email': request.user.email,
                }
            )
            
            # Validate subscription rules
            # Rule 1: Only one active recurring plan allowed
            if plan.billing_period in ['weekly', 'monthly', 'quarterly', 'yearly']:
                existing_recurring = Subscription.objects.filter(
                    billing_profile=billing_profile,
                    status='active',
                    plan__billing_period__in=['weekly', 'monthly', 'quarterly', 'yearly']
                ).select_related('plan').first()
                
                if existing_recurring:
                    return Response({
                        'success': False,
                        'error': f'You already have an active subscription ({existing_recurring.plan.name}). Please wait until it expires before purchasing another recurring plan.',
                        'current_plan': existing_recurring.plan.name,
                        'current_plan_expires': existing_recurring.end_date.isoformat() if existing_recurring.end_date else None,
                        'conflict': True
                    }, status=status.HTTP_409_CONFLICT)
            
            # Rule 2: Prevent duplicate lifetime/one-time plans
            if plan.billing_period in ['lifetime', 'one_time']:
                existing_lifetime = Subscription.objects.filter(
                    billing_profile=billing_profile,
                    plan=plan,
                    status='active'
                ).first()
                
                if existing_lifetime:
                    return Response({
                        'success': False,
                        'error': f'You already have access to {plan.name}.',
                        'redirect_to_subscriptions': True
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate Telegram connection for plans with Telegram groups
            if plan.telegram_groups.filter(is_active=True).exists():
                if not billing_profile.telegram_user_id:
                    return Response({
                        'success': False,
                        'error': 'Telegram account required',
                        'message': 'This subscription includes Telegram groups. Please link your Telegram account in your profile before subscribing.',
                        'telegram_required': True
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Determine currency (plan currency or requested)
            if not currency:
                currency = plan.currency
            
            # Get plan price in requested currency
            plan_price = plan.get_price_in_currency(currency)
            if plan_price is None:
                return Response({
                    'success': False,
                    'error': f'Plan not available in {currency}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Trials disabled - all subscriptions are paid (with optional coupon discount)
            is_trial = False
            amount = plan_price
            discount_amount = Decimal('0.00')
            
            # Apply coupon if provided
            if coupon_code:
                    try:
                        coupon = Coupon.objects.get(
                            code=coupon_code.upper(),
                            is_active=True
                        )
                        
                        # Validate coupon time validity
                        if not coupon.is_valid():
                            from django.utils import timezone as tz
                            now = tz.now()
                            if coupon.valid_from and now < coupon.valid_from:
                                return Response({
                                    'success': False,
                                    'error': f'Coupon is not valid until {coupon.valid_from.strftime("%Y-%m-%d")}'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            elif coupon.valid_until and now > coupon.valid_until:
                                return Response({
                                    'success': False,
                                    'error': f'Coupon expired on {coupon.valid_until.strftime("%Y-%m-%d")}'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                return Response({
                                    'success': False,
                                    'error': 'Coupon is not currently valid'
                                }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Check usage availability
                        if not coupon.is_usage_available():
                            return Response({
                                'success': False,
                                'error': 'This coupon has reached its usage limit'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Check user-specific usage limit
                        user_usage_count = Payment.objects.filter(
                            billing_profile=billing_profile,
                            status__in=['completed', 'success'],
                            gateway_response__metadata__coupon_code=coupon_code.upper()
                        ).count()
                        
                        if user_usage_count >= coupon.max_uses_per_user:
                            return Response({
                                'success': False,
                                'error': f'You have already used this coupon {coupon.max_uses_per_user} time(s)'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Check if coupon applies to this plan
                        if not coupon.applies_to_plan(plan):
                            return Response({
                                'success': False,
                                'error': 'This coupon does not apply to the selected plan'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Calculate discount
                        discount_result = coupon.calculate_discount(amount)
                        discount_amount = discount_result['discount_amount']
                        amount = discount_result['final_price']
                        
                    except Coupon.DoesNotExist:
                        return Response({
                            'success': False,
                            'error': 'Invalid coupon code'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate processing fee
            calculation = PaymentCalculator.calculate_total_with_fees(
                base_amount=amount,
                currency=currency,
                pass_fee_to_customer=True
            )
            
            processing_fee = calculation['processing_fee']
            total_amount = calculation['total_to_charge']
            
            # Determine gateway
            config = PaymentConfiguration.get_instance()
            if not gateway:
                gateway = config.primary_provider
            
            # Validate gateway is enabled
            if gateway == 'paystack' and not config.paystack_enabled:
                return Response({
                    'success': False,
                    'error': 'Paystack is currently unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            elif gateway == 'stripe' and not config.stripe_enabled:
                return Response({
                    'success': False,
                    'error': 'Stripe is currently unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Generate idempotency key and reference
            idempotency_key = f"{request.user.id}_{plan.id}_{currency}_{int(timezone.now().timestamp())}"
            reference = f"PAY_{uuid.uuid4().hex[:12].upper()}"
            
            # Check for recent pending payment (last 15 minutes) to prevent duplicates
            recent_payment = Payment.objects.filter(
                billing_profile=billing_profile,
                status__in=['pending', 'processing'],
                created_at__gte=timezone.now() - timedelta(minutes=15),
                currency=currency,
                gateway_response__metadata__plan_id=str(plan.id)
            ).first()
            
            if recent_payment:
                # Reuse existing payment if initialization succeeded
                if recent_payment.gateway_response.get('authorization_url'):
                    logger.info(f"Reusing pending payment {recent_payment.gateway_reference} for user {request.user.id}")
                    
                    response_data = {
                        'success': True,
                        'payment_url': recent_payment.gateway_response['authorization_url'],
                        'reference': recent_payment.gateway_reference,
                        'amount': float(recent_payment.amount),
                        'processing_fee': float(recent_payment.processing_fee),
                        'total_amount': float(recent_payment.total_amount),
                        'currency': recent_payment.currency,
                        'gateway': recent_payment.payment_gateway,
                        'payment_id': recent_payment.id,
                        'paystack_public_key': config.paystack_public_key if gateway == 'paystack' else None,
                        'existing_payment': True
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    # Previous initialization failed, use existing payment record
                    payment = recent_payment
                    reference = payment.gateway_reference
                    logger.info(f"Retrying payment initialization for {reference}")
            else:
                # Create new payment record
                payment = Payment.objects.create(
                    billing_profile=billing_profile,
                    subscription=None,  # Will be linked after verification
                    amount=amount,
                    processing_fee=processing_fee,
                    total_amount=total_amount,
                    currency=currency,
                    payment_gateway=gateway,
                    gateway_reference=reference,
                    status='pending',
                    idempotency_key=idempotency_key,
                    gateway_response={}
                )
            
            # Build metadata for payment gateway
            metadata = {
                'plan_id': str(plan.id),  # Convert UUID to string
                'plan_name': plan.name,
                'user_id': str(request.user.id),  # Convert UUID to string
                'user_email': request.user.email,
                'payment_id': str(payment.id),  # Convert UUID to string
            }
            
            if coupon_code:
                metadata['coupon_code'] = coupon_code
                metadata['discount_amount'] = str(discount_amount)
            
            # Initialize payment with gateway
            payment_service = PaymentService(gateway=gateway)
            
            if gateway == 'paystack':
                # Set default callback URL
                if not callback_url:
                    callback_url = f"{settings.FRONTEND_URL}/payment/verify"
                
                result = payment_service.initialize_payment(
                    email=request.user.email,
                    amount=total_amount,
                    reference=reference,
                    currency=currency,
                    callback_url=callback_url,
                    metadata=metadata
                )
                
                if result.get('success'):
                    # Update payment with authorization URL
                    payment.gateway_response = result
                    payment.status = 'processing'
                    payment.save()
                    
                    logger.info(f"Payment initialized: {reference} for user {request.user.id}")
                    
                    response_data = {
                        'success': True,
                        'payment_url': result['authorization_url'],
                        'reference': reference,
                        'amount': float(amount),
                        'processing_fee': float(processing_fee),
                        'total_amount': float(total_amount),
                        'currency': currency,
                        'gateway': gateway,
                        'payment_id': payment.id,
                        'paystack_public_key': config.paystack_public_key if gateway == 'paystack' else None,
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    # Payment initialization failed
                    payment.status = 'failed'
                    payment.failure_reason = result.get('error', 'Unknown error')
                    payment.gateway_response = result
                    payment.save()
                    
                    return Response({
                        'success': False,
                        'error': result.get('error', 'Payment initialization failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elif gateway == 'stripe':
                # Set default URLs
                success_url = callback_url or f"{settings.FRONTEND_URL}/payment/success"
                cancel_url = f"{settings.FRONTEND_URL}/payment/cancel"
                
                result = payment_service.initialize_payment(
                    email=request.user.email,
                    amount=total_amount,
                    currency=currency,
                    metadata=metadata,
                    success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=cancel_url
                )
                
                if result.get('success'):
                    # Update payment with session details
                    payment.gateway_reference = result['session_id']
                    payment.gateway_response = result
                    payment.status = 'processing'
                    payment.save()
                    
                    logger.info(f"Stripe session created: {result['session_id']} for user {request.user.id}")
                    
                    response_data = {
                        'success': True,
                        'payment_url': result['checkout_url'],
                        'reference': result['session_id'],
                        'amount': float(amount),
                        'processing_fee': float(processing_fee),
                        'total_amount': float(total_amount),
                        'currency': currency,
                        'gateway': gateway,
                        'payment_id': payment.id,
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    # Payment initialization failed
                    payment.status = 'failed'
                    payment.failure_reason = result.get('error', 'Unknown error')
                    payment.gateway_response = result
                    payment.save()
                    
                    return Response({
                        'success': False,
                        'error': result.get('error', 'Payment initialization failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            else:
                return Response({
                    'success': False,
                    'error': f'Unsupported payment gateway: {gateway}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Payment initialization error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while initializing payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def charge_with_saved_card(request):
    """
    Charge user using their saved payment method
    
    POST /api/payments/charge-saved-card/
    
    Request Body:
        {
            "plan_id": "uuid",
            "coupon_code": "SAVE20"  # Optional
        }
    
    Response:
        {
            "success": true,
            "reference": "PAY_123456",
            "subscription_id": "uuid",
            "message": "Payment processed successfully"
        }
    """
    try:
        user = request.user
        plan_id = request.data.get('plan_id')
        coupon_code = request.data.get('coupon_code', '').strip().upper()
        currency = request.data.get('currency', 'NGN').upper()  # Get currency from request, default to NGN
        amount = request.data.get('amount')  # Get the already-converted amount from frontend
        
        if not plan_id:
            return Response({
                'success': False,
                'error': 'Plan ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not amount:
            return Response({
                'success': False,
                'error': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get billing profile
        billing_profile, _ = BillingProfile.objects.get_or_create(user=user)
        
        # Get user's active payment method
        payment_method = PaymentMethod.objects.filter(
            billing_profile=billing_profile,
            is_active=True
        ).first()
        
        if not payment_method:
            return Response({
                'success': False,
                'error': 'No payment method found. Please add a payment method first.',
                'redirect_to_billing': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Subscription plan not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate subscription rules
        # Rule 1: Only one active recurring plan allowed
        if plan.billing_period in ['weekly', 'monthly', 'quarterly', 'yearly']:
            existing_recurring = Subscription.objects.filter(
                billing_profile=billing_profile,
                status='active',
                plan__billing_period__in=['weekly', 'monthly', 'quarterly', 'yearly']
            ).first()
            
            if existing_recurring:
                return Response({
                    'success': False,
                    'error': f'You already have an active subscription ({existing_recurring.plan.name}). Please wait until it expires before purchasing another recurring plan.',
                    'current_plan': existing_recurring.plan.name,
                    'current_plan_expires': existing_recurring.end_date.isoformat() if existing_recurring.end_date else None
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Rule 2: Prevent duplicate lifetime/one-time plans
        if plan.billing_period in ['lifetime', 'one_time']:
            existing_lifetime = Subscription.objects.filter(
                billing_profile=billing_profile,
                plan=plan,
                status='active'
            ).first()
            
            if existing_lifetime:
                return Response({
                    'success': False,
                    'error': f'You already have access to {plan.name}.',
                    'redirect_to_subscriptions': True
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate pricing
        # Amount is already converted to the selected currency by the frontend
        amount = Decimal(str(amount))
        discount_amount = Decimal('0.00')
        
        # Validate and apply coupon if provided
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_until__gte=timezone.now()
                )
                
                # Check if coupon applies to this plan
                if coupon.applicable_plans.exists() and plan not in coupon.applicable_plans.all():
                    return Response({
                        'success': False,
                        'error': 'This coupon is not applicable to the selected plan'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate discount
                if coupon.discount_type == 'percentage':
                    discount_amount = (amount * coupon.discount_value) / Decimal('100')
                else:  # fixed_amount
                    discount_amount = min(coupon.discount_value, amount)
                
            except Coupon.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid coupon code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate final amount
        calculator = PaymentCalculator()
        calculation = calculator.calculate_total_with_fees(
            base_amount=amount - discount_amount,
            currency=currency,
            pass_fee_to_customer=True
        )
        
        processing_fee = calculation['processing_fee']
        total_amount = calculation['total_to_charge']
        
        # Generate reference
        reference = f"PAY_{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment record
        payment = Payment.objects.create(
            billing_profile=billing_profile,
            amount=amount - discount_amount,
            processing_fee=processing_fee,
            total_amount=total_amount,
            currency=currency,
            payment_gateway='paystack',
            gateway_reference=reference,
            status='processing',
            gateway_response={}
        )
        
        # Charge the saved card
        paystack = PaystackService()
        charge_result = paystack.charge_authorization(
            authorization_code=payment_method.gateway_authorization_code,
            email=user.email,
            amount=total_amount,
            currency=currency,
            metadata={
                'plan_id': str(plan.id),
                'plan_name': plan.name,
                'user_id': str(user.id),
                'user_email': user.email,
                'payment_id': str(payment.id),
                'coupon_code': coupon_code if coupon_code else None
            }
        )
        
        if charge_result.get('success'):
            # Payment successful - wrap in atomic transaction
            try:
                with transaction.atomic():
                    # Update payment with Paystack's reference
                    payment.status = 'verified'
                    payment.gateway_reference = charge_result.get('reference')
                    payment.gateway_response = charge_result
                    payment.log_event('payment_successful', charge_result)
                    payment.save()
                    
                    # Create subscription
                    subscription_start = timezone.now()
                    if plan.billing_period == 'weekly':
                        subscription_end = subscription_start + timedelta(days=7)
                        next_billing_date = subscription_start + timedelta(days=7)
                    elif plan.billing_period == 'monthly':
                        subscription_end = subscription_start + timedelta(days=30)
                        next_billing_date = subscription_start + timedelta(days=30)
                    elif plan.billing_period == 'quarterly':
                        subscription_end = subscription_start + timedelta(days=90)
                        next_billing_date = subscription_start + timedelta(days=90)
                    elif plan.billing_period == 'yearly':
                        subscription_end = subscription_start + timedelta(days=365)
                        next_billing_date = subscription_start + timedelta(days=365)
                    elif plan.billing_period == 'lifetime':
                        subscription_end = subscription_start + timedelta(days=36500)
                        next_billing_date = None
                    else:
                        subscription_end = subscription_start + timedelta(days=30)
                        next_billing_date = subscription_start + timedelta(days=30)
                    
                    # Create or update subscription (match on billing_profile AND plan)
                    subscription, created = Subscription.objects.update_or_create(
                        billing_profile=billing_profile,
                        plan=plan,
                        defaults={
                            'status': 'active',
                            'start_date': subscription_start,
                            'end_date': subscription_end,
                            'amount_paid': amount - discount_amount,
                            'currency': currency,
                            'auto_renew': True,
                            'payment_method': payment_method,
                            'next_billing_date': next_billing_date,
                        }
                    )
                    
                    # Link payment to subscription
                    payment.subscription = subscription
                    payment.save()
                    
                    # Update user subscription fields
                    user.current_plan = plan
                    user.subscription_status = 'active'
                    user.save()
                
                # Queue Celery tasks AFTER database commit (capture variables to avoid closure issues)
                payment_id_captured = payment.id
                user_id_captured = user.id
                plan_id_captured = str(plan.id)
                subscription_id_captured = str(subscription.id)
                reference_captured = charge_result.get('reference')
                
                try:
                    transaction.on_commit(lambda: activate_subscription.delay(payment_id_captured))
                    transaction.on_commit(lambda: add_user_to_telegram_groups.delay(user_id_captured, plan_id_captured))
                    transaction.on_commit(lambda: send_payment_receipt_email.delay(payment_id_captured))
                except Exception as task_error:
                    # Log task queueing errors but don't fail the payment
                    logger.error(f"Failed to queue background tasks: {str(task_error)}", exc_info=True)
                
                logger.info(f"Charged saved card for user {user.email}: {currency} {total_amount}")
                
                return Response({
                    'success': True,
                    'reference': reference_captured,
                    'subscription_id': subscription_id_captured,
                    'message': 'Payment processed successfully',
                    'amount': float(total_amount),
                    'currency': currency
                }, status=status.HTTP_200_OK)
                
            except Exception as transaction_error:
                # If transaction fails, log it with details
                logger.error(f"Transaction error in charge_with_saved_card: {str(transaction_error)}", exc_info=True)
                # Payment was charged but subscription creation failed - needs manual review
                return Response({
                    'success': False,
                    'error': 'Payment was processed but subscription activation failed. Please contact support.',
                    'reference': charge_result.get('reference'),
                    'requires_manual_review': True
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Payment failed
            payment.status = 'failed'
            payment.failure_reason = charge_result.get('message', 'Payment declined')
            payment.gateway_response = charge_result
            payment.save()
            
            return Response({
                'success': False,
                'error': charge_result.get('message', 'Payment was declined. Please try another card.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error charging saved card: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An error occurred while processing payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    """
    Verify a payment transaction
    
    POST /api/payments/verify/
    
    Request Body:
        {
            "reference": "PAY_123456",  # For Paystack
            "session_id": "cs_test_...",  # For Stripe
            "gateway": "paystack"  # Optional, will be detected from reference
        }
    
    Response:
        {
            "success": true,
            "verified": true,
            "amount": 5000.00,
            "currency": "NGN",
            "subscription_id": 42,
            "message": "Payment verified successfully"
        }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            reference = request.data.get('reference', '')
            session_id = request.data.get('session_id', '')
            gateway = request.data.get('gateway', '')
            
            # Determine which reference to use
            if reference:
                lookup_ref = reference
            elif session_id:
                lookup_ref = session_id
            else:
                return Response({
                    'success': False,
                    'error': 'Payment reference or session_id required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find payment record with locking to prevent race conditions
            try:
                with transaction.atomic():
                    # SELECT FOR UPDATE prevents concurrent verification
                    payment = Payment.objects.select_for_update().get(
                        gateway_reference=lookup_ref,
                        billing_profile__user=request.user
                    )
                    
                    # If already verified, return success immediately
                    if payment.status == 'success':
                        return Response({
                            'success': True,
                            'verified': True,
                            'amount': float(payment.amount),
                            'currency': payment.currency,
                            'subscription_id': payment.subscription.id if payment.subscription else None,
                            'message': 'Payment already verified'
                        }, status=status.HTTP_200_OK)
            except Payment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify with gateway
            payment_service = PaymentService(gateway=payment.payment_gateway)
            
            if payment.payment_gateway == 'paystack':
                result = payment_service.verify_payment(reference=lookup_ref)
            elif payment.payment_gateway == 'stripe':
                result = payment_service.verify_payment(session_id=lookup_ref)
            else:
                return Response({
                    'success': False,
                    'error': 'Unsupported payment gateway'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update payment record
            payment.gateway_response = result
            
            if result.get('success') and result.get('verified'):
                # Payment successful
                payment.mark_as_paid()
                
                # Get plan_id from metadata
                metadata = payment.gateway_response.get('metadata', {})
                plan_id = metadata.get('plan_id')
                
                if plan_id:
                    try:
                        plan = SubscriptionPlan.objects.get(id=plan_id)
                        
                        # Calculate subscription dates
                        start_date = timezone.now()
                        
                        # Calculate end date and next billing based on billing period
                        if plan.billing_period == 'weekly':
                            end_date = start_date + timedelta(days=7)
                            next_billing_date = start_date + timedelta(days=7)
                        elif plan.billing_period == 'monthly':
                            end_date = start_date + timedelta(days=30)
                            next_billing_date = start_date + timedelta(days=30)
                        elif plan.billing_period == 'quarterly':
                            end_date = start_date + timedelta(days=90)
                            next_billing_date = start_date + timedelta(days=90)
                        elif plan.billing_period == 'yearly':
                            end_date = start_date + timedelta(days=365)
                            next_billing_date = start_date + timedelta(days=365)
                        elif plan.billing_period == 'lifetime':
                            end_date = start_date + timedelta(days=36500)  # 100 years
                            next_billing_date = None  # No renewal for lifetime
                        else:
                            end_date = start_date + timedelta(days=30)  # Default to monthly
                            next_billing_date = start_date + timedelta(days=30)
                        
                        # Extract authorization code from payment verification for auto-renewal
                        payment_method = None
                        authorization_code = None
                        
                        if payment.payment_gateway == 'paystack':
                            paystack_service = PaystackService()
                            auth_data = paystack_service.extract_authorization_from_verification(result)
                            
                            if auth_data:
                                # Create or update payment method
                                payment_method, pm_created = PaymentMethod.objects.update_or_create(
                                    billing_profile=payment.billing_profile,
                                    gateway_authorization_code=auth_data['authorization_code'],
                                    defaults={
                                        'payment_type': 'card',
                                        'card_last4': auth_data['last4'],
                                        'card_brand': auth_data['brand'],
                                        'card_exp_month': auth_data['exp_month'],
                                        'card_exp_year': auth_data['exp_year'],
                                        'is_active': True,
                                        # Only set as default if user has no payment methods
                                        'is_default': not PaymentMethod.objects.filter(
                                            billing_profile=payment.billing_profile,
                                            is_active=True
                                        ).exists()
                                    }
                                )
                                
                                if pm_created:
                                    logger.info(f"Payment method created from trial signup: {auth_data['last4']}")
                                else:
                                    logger.info(f"Payment method updated from trial signup: {auth_data['last4']}")
                        
                        # Create or update subscription (match on billing_profile AND plan)
                        subscription, created = Subscription.objects.update_or_create(
                            billing_profile=payment.billing_profile,
                            plan=plan,
                            defaults={
                                'status': 'active',
                                'start_date': start_date,
                                'end_date': end_date,
                                'amount_paid': payment.amount,
                                'currency': payment.currency,
                                'auto_renew': True,
                                'payment_method': payment_method,
                                'next_billing_date': next_billing_date,
                            }
                        )
                        
                        # Link payment to subscription
                        payment.subscription = subscription
                        payment.save()
                        
                        # Update user subscription fields
                        request.user.current_plan = plan
                        request.user.subscription_status = 'active'
                        request.user.save()
                        
                        logger.info(f"Subscription activated for user {request.user.id}: {plan.name}")
                        
                        # Trigger Celery tasks (wrap in try-except to prevent Redis errors from failing response)
                        # NOTE: Don't trigger add_user_to_telegram_groups here - webhook will handle it
                        # to avoid duplicate invite links
                        try:
                            activate_subscription.delay(payment.id)
                            send_payment_receipt_email.delay(payment.id)
                        except Exception as task_error:
                            logger.error(f"Failed to queue background tasks in verify: {str(task_error)}", exc_info=True)
                        
                    except SubscriptionPlan.DoesNotExist:
                        logger.error(f"Plan {plan_id} not found for payment {payment.id}")
                
                response_data = {
                    'success': True,
                    'verified': True,
                    'amount': float(payment.amount),
                    'currency': payment.currency,
                    'subscription_id': payment.subscription.id if payment.subscription else None,
                    'message': 'Payment verified successfully'
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
            
            else:
                # Payment failed
                payment.mark_as_failed(
                    reason=result.get('error', 'Payment verification failed')
                )
                
                return Response({
                    'success': False,
                    'verified': False,
                    'error': result.get('error', 'Payment verification failed')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while verifying payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def paystack_webhook(request):
    """
    Paystack webhook handler
    
    POST /api/payments/webhook/paystack/
    
    Handles events:
    - charge.success - Payment successful
    - subscription.create - Recurring subscription created
    - subscription.disable - Subscription cancelled
    """
    
    try:
        # Get signature from header
        signature = request.headers.get('X-Paystack-Signature', '')
        
        if not signature:
            logger.warning("Paystack webhook: Missing signature")
            return JsonResponse({
                'success': False,
                'error': 'Missing signature'
            }, status=400)
        
        # Verify signature
        service = PaystackService()
        if not service.verify_webhook_signature(request.body, signature):
            logger.warning("Paystack webhook: Invalid signature")
            return JsonResponse({
                'success': False,
                'error': 'Invalid signature'
            }, status=401)
        
        # Parse webhook data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Paystack webhook: Invalid JSON")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
        
        event = data.get('event')
        event_data = data.get('data', {})
        
        logger.info(f"Paystack webhook received: {event}")
        
        # Handle charge.success event
        if event == 'charge.success':
            reference = event_data.get('reference')
            
            # Retry logic for race condition where webhook arrives before payment record is created
            max_retries = 3
            payment = None
            
            for attempt in range(max_retries):
                try:
                    payment = Payment.objects.get(gateway_reference=reference)
                    break
                except Payment.DoesNotExist:
                    if attempt < max_retries - 1:
                        logger.warning(f"Payment {reference} not found, retry {attempt + 1}/{max_retries}")
                        time.sleep(2)  # Wait 2 seconds before retry
                        continue
                    else:
                        logger.error(f"Payment {reference} not found after {max_retries} attempts")
                        return JsonResponse({
                            'success': False,
                            'error': 'Payment not found'
                        }, status=404)
            
            try:
                # Use atomic transaction with locking for consistency
                with transaction.atomic():
                    # SELECT FOR UPDATE prevents race condition with manual verification
                    payment = Payment.objects.select_for_update().get(id=payment.id)
                    
                    # Update payment status if not already paid (idempotency check)
                    if payment.status != 'success':
                        payment.mark_as_paid()
                        payment.gateway_response = event_data
                        payment.log_event('webhook_received', {'event': event, 'reference': reference})
                        payment.save()
                        
                        logger.info(f"Payment {reference} marked as paid via webhook")
                
                # Queue Celery tasks AFTER database commit (idempotent)
                transaction.on_commit(lambda: activate_subscription.delay(payment.id))
                
                # Get plan_id from metadata for Telegram groups
                metadata = event_data.get('metadata', {})
                plan_id = metadata.get('plan_id')
                user_id = metadata.get('user_id')
                
                if plan_id and user_id:
                    transaction.on_commit(lambda: add_user_to_telegram_groups.delay(user_id, plan_id))
                
                transaction.on_commit(lambda: send_payment_receipt_email.delay(payment.id))
                
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for reference: {reference}")
        
        # Handle subscription.create event
        elif event == 'subscription.create':
            logger.info(f"Subscription created: {event_data.get('subscription_code')}")
            # TODO: Handle recurring subscription setup
        
        # Handle subscription.disable event
        elif event == 'subscription.disable':
            logger.info(f"Subscription disabled: {event_data.get('subscription_code')}")
            # TODO: Handle subscription cancellation
        
        return JsonResponse({
            'success': True,
            'message': 'Webhook processed'
        }, status=200)
    
    except Exception as e:
        logger.error(f"Paystack webhook error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Webhook processing failed'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Stripe webhook handler
    
    POST /api/payments/webhook/stripe/
    
    Handles events:
    - checkout.session.completed - Payment successful
    - payment_intent.succeeded - Payment confirmed
    - customer.subscription.created - Subscription created
    - customer.subscription.deleted - Subscription cancelled
    """
    
    try:
        # Get signature from header
        signature = request.headers.get('Stripe-Signature', '')
        
        if not signature:
            logger.warning("Stripe webhook: Missing signature")
            return JsonResponse({
                'success': False,
                'error': 'Missing signature'
            }, status=400)
        
        # Verify signature and construct event
        service = StripeService()
        result = service.verify_webhook_signature(request.body, signature)
        
        if not result.get('success'):
            logger.warning(f"Stripe webhook: {result.get('error')}")
            return JsonResponse({
                'success': False,
                'error': result.get('error')
            }, status=401)
        
        event = result['event']
        event_type = event['type']
        event_data = event['data']['object']
        
        logger.info(f"Stripe webhook received: {event_type}")
        
        # Handle checkout.session.completed event
        if event_type == 'checkout.session.completed':
            session_id = event_data['id']
            
            try:
                payment = Payment.objects.get(gateway_reference=session_id)
                
                # Update payment status
                if payment.status != 'success':
                    payment.mark_as_paid()
                    payment.gateway_response = event_data
                    payment.save()
                    
                    logger.info(f"Payment {session_id} marked as paid via webhook")
                    
                    # Trigger Celery tasks
                    activate_subscription.delay(payment.id)
                    
                    # Get plan_id and user_id from metadata
                    metadata = event_data.get('metadata', {})
                    plan_id = metadata.get('plan_id')
                    user_id = metadata.get('user_id')
                    
                    if plan_id and user_id:
                        add_user_to_telegram_groups.delay(int(user_id), plan_id)
                    
                    send_payment_receipt_email.delay(payment.id)
                
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for session: {session_id}")
        
        # Handle payment_intent.succeeded event
        elif event_type == 'payment_intent.succeeded':
            payment_intent_id = event_data['id']
            logger.info(f"Payment intent succeeded: {payment_intent_id}")
            # TODO: Handle direct payment intent (non-checkout)
        
        # Handle subscription events
        elif event_type == 'customer.subscription.created':
            logger.info(f"Subscription created: {event_data['id']}")
            # TODO: Handle recurring subscription setup
        
        elif event_type == 'customer.subscription.deleted':
            logger.info(f"Subscription deleted: {event_data['id']}")
            # TODO: Handle subscription cancellation
        
        return JsonResponse({
            'success': True,
            'message': 'Webhook processed'
        }, status=200)
    
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Webhook processing failed'
        }, status=500)


class PaymentHistoryView(APIView):
    """
    Get payment history for authenticated user
    
    GET /api/payments/history/?page=1&page_size=20
    
    Response:
        {
            "count": 42,
            "next": "http://api.example.com/payments/history/?page=2",
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "amount": 5000.00,
                    "currency": "NGN",
                    "status": "success",
                    "created_at": "2025-11-10T12:00:00Z",
                    ...
                }
            ]
        }
    """
    
    permission_classes = [IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get(self, request):
        try:
            # Get user's billing profile
            try:
                billing_profile = BillingProfile.objects.get(user=request.user)
            except BillingProfile.DoesNotExist:
                return Response({
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'results': []
                }, status=status.HTTP_200_OK)
            
            # Get payments
            payments = Payment.objects.filter(
                billing_profile=billing_profile
            ).select_related('subscription', 'subscription__plan').order_by('-created_at')
            
            # Paginate
            paginator = self.pagination_class()
            paginated_payments = paginator.paginate_queryset(payments, request)
            
            # Serialize
            serializer = PaymentSerializer(paginated_payments, many=True)
            
            return paginator.get_paginated_response(serializer.data)
        
        except Exception as e:
            logger.error(f"Payment history error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while fetching payment history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceDownloadView(APIView):
    """
    Download invoice PDF for a payment
    
    GET /api/payments/{id}/invoice/
    
    Response:
        PDF file download
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            # Get payment
            try:
                payment = Payment.objects.select_related(
                    'billing_profile__user',
                    'subscription__plan'
                ).get(
                    id=payment_id,
                    billing_profile__user=request.user
                )
            except Payment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if payment is successful
            if payment.status != 'success':
                return Response({
                    'success': False,
                    'error': 'Invoice not available for unsuccessful payments'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # TODO: Generate PDF invoice
            # For now, return JSON invoice data
            invoice_data = {
                'invoice_number': f"INV-{payment.id:06d}",
                'payment_date': payment.paid_at.isoformat() if payment.paid_at else None,
                'customer': {
                    'name': f"{request.user.first_name} {request.user.last_name}",
                    'email': request.user.email,
                },
                'items': [
                    {
                        'description': payment.subscription.plan.name if payment.subscription else 'Subscription',
                        'amount': float(payment.amount),
                        'currency': payment.currency,
                    }
                ],
                'processing_fee': float(payment.processing_fee),
                'total': float(payment.total_amount),
                'currency': payment.currency,
                'payment_method': payment.payment_gateway.title(),
                'reference': payment.gateway_reference,
            }
            
            return Response(invoice_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Invoice download error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while generating invoice'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckSubscriptionConflictView(APIView):
    """
    Check if user has active subscription that conflicts with purchasing a new plan
    
    GET /api/payments/check-conflict/?plan_id=123
    
    Returns:
        {
            "can_purchase": false,
            "conflict": true,
            "existing_subscription": {
                "plan_name": "Monthly Signals",
                "billing_period": "monthly",
                "end_date": "2025-12-10"
            },
            "message": "You already have an active monthly subscription..."
        }
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            plan_id = request.query_params.get('plan_id')
            
            if not plan_id:
                return Response({
                    'success': False,
                    'error': 'plan_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid subscription plan'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get user's billing profile
            try:
                billing_profile = BillingProfile.objects.get(user=request.user)
            except BillingProfile.DoesNotExist:
                # No billing profile = no subscriptions = can purchase
                return Response({
                    'can_purchase': True,
                    'conflict': False
                }, status=status.HTTP_200_OK)
            
            # Lifetime plans are always allowed (one-time purchases)
            if plan.billing_period == 'lifetime':
                return Response({
                    'can_purchase': True,
                    'conflict': False,
                    'message': 'Lifetime plans can always be purchased'
                }, status=status.HTTP_200_OK)
            
            # Check for existing active recurring subscriptions
            existing_recurring = Subscription.objects.filter(
                billing_profile=billing_profile,
                status='active',
                plan__billing_period__in=['weekly', 'monthly', 'quarterly', 'yearly']
            ).select_related('plan').first()
            
            if existing_recurring:
                return Response({
                    'can_purchase': False,
                    'conflict': True,
                    'existing_subscription': {
                        'id': str(existing_recurring.id),
                        'plan_id': str(existing_recurring.plan.id),
                        'plan_name': existing_recurring.plan.name,
                        'billing_period': existing_recurring.plan.billing_period,
                        'billing_period_display': existing_recurring.plan.get_billing_period_display(),
                        'end_date': existing_recurring.end_date.date().isoformat() if existing_recurring.end_date else None,
                        'auto_renew': existing_recurring.auto_renew
                    },
                    'message': f'You already have an active {existing_recurring.plan.get_billing_period_display()} subscription ({existing_recurring.plan.name}). Please cancel it before purchasing a new plan.'
                }, status=status.HTTP_200_OK)
            
            # No conflicts - can purchase
            return Response({
                'can_purchase': True,
                'conflict': False
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Conflict check error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while checking subscription conflict'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
