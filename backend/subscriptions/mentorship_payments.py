# Mentorship Payment Processing
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
import requests
import hashlib
import hmac
from decimal import Decimal
import uuid

from .models import PricingPlan, SignalSubscription
from users.models import User
from django.conf import settings

# Note: Mentorship is now handled through SignalSubscription with plan_type='mentorship'

@csrf_exempt
@require_http_methods(["POST"])
def initiate_mentorship_payment(request):
    """Initialize Paystack payment for mentorship purchase (one-time, lifetime access)"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['user_email', 'telegram_username']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Get user
        try:
            user = User.objects.get(email=data['user_email'])
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user already purchased mentorship
        existing_purchase = SignalSubscription.objects.filter(
            user=user,
            plan_type='mentorship',
            payment_status='verified'
        ).first()
        
        if existing_purchase:
            return JsonResponse({
                'success': False,
                'error': 'You have already purchased the Mentorship Program. You have lifetime access to all courses.'
            }, status=400)
        
        # Get mentorship pricing plan
        try:
            plan = PricingPlan.objects.get(plan_type='mentorship', is_active=True)
        except PricingPlan.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Mentorship program not available'
            }, status=404)
        
        # Generate unique payment reference
        reference = f"MENTOR_{uuid.uuid4().hex[:12].upper()}"
        
        # Create subscription record (using SignalSubscription model)
        subscription = SignalSubscription.objects.create(
            user=user,
            plan_type='mentorship',
            pricing_plan=plan,
            paystack_reference=reference,
            amount_paid=plan.current_price,
            currency=plan.currency,
            telegram_username=data['telegram_username'],
            payment_status='pending',
            subscription_start=timezone.now()
            # No subscription_end - lifetime access
        )
        
        # Prepare Paystack payment data
        paystack_data = {
            'reference': reference,
            'amount': int(plan.current_price * 100),  # Convert to kobo/cents
            'email': user.email,
            'currency': plan.currency,
            'callback_url': data.get('callback_url', ''),
            'metadata': {
                'subscription_id': str(subscription.id),
                'plan_type': 'mentorship',
                'telegram_username': data['telegram_username'],
                'custom_fields': [
                    {
                        'display_name': 'Product',
                        'variable_name': 'product',
                        'value': 'Mentorship Program - Lifetime Access'
                    },
                    {
                        'display_name': 'Telegram Username',
                        'variable_name': 'telegram_username',
                        'value': data['telegram_username']
                    }
                ]
            }
        }
        
        # Initialize payment with Paystack
        paystack_headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        paystack_response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers=paystack_headers,
            json=paystack_data
        )
        
        if paystack_response.status_code == 200:
            paystack_result = paystack_response.json()
            
            if paystack_result['status']:
                return JsonResponse({
                    'success': True,
                    'payment_url': paystack_result['data']['authorization_url'],
                    'reference': reference,
                    'subscription_id': str(subscription.id),
                    'amount': float(plan.current_price),
                    'currency': plan.currency
                })
            else:
                # Delete the subscription if Paystack initialization failed
                subscription.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Payment initialization failed: {paystack_result.get("message", "Unknown error")}'
                }, status=400)
        else:
            # Delete the subscription if request failed
            subscription.delete()
            return JsonResponse({
                'success': False,
                'error': 'Payment service unavailable'
            }, status=503)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to initialize payment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def paystack_mentorship_webhook(request):
    """Handle Paystack webhook for mentorship payments"""
    try:
        # Verify webhook signature
        signature = request.headers.get('x-paystack-signature', '')
        body = request.body
        
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            body,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Parse webhook data
        data = json.loads(body)
        event = data.get('event')
        
        if event == 'charge.success':
            payment_data = data['data']
            reference = payment_data['reference']
            
            # Find mentorship purchase (in SignalSubscription with plan_type='mentorship')
            try:
                subscription = SignalSubscription.objects.get(
                    paystack_reference=reference,
                    plan_type='mentorship'
                )
            except SignalSubscription.DoesNotExist:
                return JsonResponse({'error': 'Subscription not found'}, status=404)
            
            # Verify payment amount
            expected_amount = int(subscription.amount_paid * 100)  # Convert to kobo/cents
            paid_amount = payment_data['amount']
            
            if paid_amount != expected_amount:
                return JsonResponse({'error': 'Amount mismatch'}, status=400)
            
            # Mark payment as verified (lifetime access, no expiration)
            subscription.payment_status = 'verified'
            subscription.payment_verified_at = timezone.now()
            if not subscription.subscription_start:
                subscription.subscription_start = timezone.now()
            # No subscription_end - lifetime access
            subscription.save()
            
            # Send welcome email (using existing email automation)
            from users.email_automation import EmailAutomationService
            try:
                EmailAutomationService.send_mentorship_welcome_email(
                    subscription.user,
                    subscription
                )
            except:
                pass  # Don't fail webhook if email fails
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'ignored'})
        
    except Exception as e:
        return JsonResponse({
            'error': f'Webhook processing failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def verify_mentorship_payment(request):
    """Manually verify a mentorship payment"""
    try:
        data = json.loads(request.body)
        reference = data.get('reference')
        
        if not reference:
            return JsonResponse({
                'success': False,
                'error': 'Payment reference required'
            }, status=400)
        
        # Find subscription
        try:
            subscription = SignalSubscription.objects.get(
                paystack_reference=reference,
                plan_type='mentorship'
            )
        except SignalSubscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Subscription not found'
            }, status=404)
        
        # Verify with Paystack
        paystack_headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        paystack_response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=paystack_headers
        )
        
        if paystack_response.status_code == 200:
            paystack_result = paystack_response.json()
            
            if paystack_result['status'] and paystack_result['data']['status'] == 'success':
                # Verify payment amount
                expected_amount = int(subscription.amount_paid * 100)
                paid_amount = paystack_result['data']['amount']
                
                if paid_amount == expected_amount:
                    # Mark as verified and activate
                    subscription.mark_payment_verified()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Payment verified and subscription activated',
                        'subscription_end': subscription.subscription_end.isoformat() if subscription.subscription_end else None
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Payment amount mismatch'
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment not successful on Paystack'
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to verify payment with Paystack'
            }, status=503)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to verify payment: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_mentorship_plans(request):
    """Get available mentorship plans"""
    try:
        # Get mentorship pricing plan (there should only be one)
        plans = PricingPlan.objects.filter(
            is_active=True, 
            plan_type='mentorship'
        ).order_by('sort_order', 'price')
        
        plan_data = []
        for plan in plans:
            plan_data.append({
                'id': str(plan.id),
                'plan_type': plan.plan_type,
                'name': plan.name,
                'description': plan.description,
                'price': float(plan.price),
                'currency': plan.currency,
                'features_list': plan.features_list or [],
                'gives_course_access': plan.gives_course_access,
                'gives_signals_access': plan.gives_signals_access,
                'telegram_group_key': plan.telegram_group_key or '',
                'billing_cycle': plan.billing_cycle,
                'duration_days': plan.duration_days,  # null for lifetime
                'is_featured': plan.is_featured
            })
        
        return JsonResponse({
            'success': True,
            'plans': plan_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch plans: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_user_mentorship_status(request):
    """Get current user's mentorship status"""
    try:
        user_email = request.GET.get('user_email')
        
        if not user_email:
            return JsonResponse({
                'success': False,
                'error': 'User email required'
            }, status=400)
        
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check for verified mentorship purchase (lifetime access)
        active_subscription = SignalSubscription.objects.filter(
            user=user,
            plan_type='mentorship',
            payment_status='verified'
        ).first()
        
        if active_subscription:
            return JsonResponse({
                'success': True,
                'has_active_mentorship': True,
                'subscription': {
                    'id': str(active_subscription.id),
                    'plan_name': 'Mentorship Program',
                    'plan_type': 'mentorship',
                    'subscription_end': None,  # Lifetime access
                    'days_remaining': None,  # No expiration
                    'sessions_remaining': 0,  # Arranged offline
                    'sessions_used': 0,  # Not tracked
                    'telegram_status': active_subscription.telegram_status,
                    'premium_content_access': True  # Always true for mentorship
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'has_active_mentorship': False,
                'subscription': None
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get mentorship status: {str(e)}'
        }, status=500)