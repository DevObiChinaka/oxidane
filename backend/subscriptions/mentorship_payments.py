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

from .models import SubscriptionPlan, Subscription
from users.models import User
from django.conf import settings

# Note: Mentorship is now handled through regular Subscription model (Phase 0.5)
# with a SubscriptionPlan that has mentorship features

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
        # Get billing profile first
        from .models import BillingProfile
        billing_profile, _ = BillingProfile.objects.get_or_create(
            user=user,
            defaults={'currency_preference': 'USD'}
        )
        
        existing_purchase = Subscription.objects.filter(
            billing_profile=billing_profile,
            plan__slug__icontains='mentorship',
            status='active'
        ).first()
        
        if existing_purchase:
            return JsonResponse({
                'success': False,
                'error': 'You have already purchased the Mentorship Program. You have lifetime access to all courses.'
            }, status=400)
        
        # Get mentorship pricing plan
        try:
            # Look for a mentorship plan (by slug or name containing "mentorship")
            plan = SubscriptionPlan.objects.filter(
                slug__icontains='mentorship',
                is_active=True
            ).first()
            if not plan:
                plan = SubscriptionPlan.objects.filter(
                    name__icontains='mentorship',
                    is_active=True
                ).first()
            if not plan:
                raise SubscriptionPlan.DoesNotExist
        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Mentorship program not available'
            }, status=404)
        
        # Generate unique payment reference
        reference = f"MENTOR_{uuid.uuid4().hex[:12].upper()}"
        
        # Create subscription record
        # Calculate subscription end date (lifetime = 100 years from now)
        from datetime import timedelta
        subscription_end = timezone.now() + timedelta(days=36500)  # 100 years
        
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            payment_reference=reference,
            start_date=timezone.now(),
            end_date=subscription_end,
            status='pending_payment',
            telegram_username=data['telegram_username'],
            auto_renew=False  # Lifetime subscription doesn't renew
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
            
            # Find mentorship purchase
            try:
                subscription = Subscription.objects.get(
                    payment_reference=reference,
                    plan__slug__icontains='mentorship'
                )
            except Subscription.DoesNotExist:
                return JsonResponse({'error': 'Subscription not found'}, status=404)
            
            # Verify payment amount
            expected_amount = int(subscription.plan.base_price * 100)  # Convert to kobo/cents
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
            subscription = Subscription.objects.get(
                payment_reference=reference,
                plan__slug__icontains='mentorship'
            )
        except Subscription.DoesNotExist:
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
        plans = SubscriptionPlan.objects.filter(
            is_active=True, 
            slug__icontains='mentorship'
        ).order_by('sort_order', 'base_price')
        
        plan_data = []
        for plan in plans:
            # Get features list
            features_list = [
                {'name': f.name, 'description': f.description}
                for f in plan.features.filter(is_active=True)
            ]
            
            plan_data.append({
                'id': str(plan.id),
                'slug': plan.slug,
                'name': plan.name,
                'description': plan.description,
                'price': float(plan.base_price),
                'currency': 'USD',  # Phase 0.5 uses USD with multi-currency conversion
                'features_list': features_list,
                'billing_period': plan.billing_period,
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
        # Get billing profile first
        from .models import BillingProfile
        billing_profile = BillingProfile.objects.filter(user=user).first()
        
        active_subscription = None
        if billing_profile:
            active_subscription = Subscription.objects.filter(
                billing_profile=billing_profile,
                plan__slug__icontains='mentorship',
                status='active'
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