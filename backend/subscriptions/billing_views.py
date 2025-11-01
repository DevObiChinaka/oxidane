"""
Telegram Verification and Billing API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os

from .models import BillingProfile, Subscription
from .serializers import BillingProfileSerializer


# Bot Secret for webhook validation
BOT_SECRET = os.getenv('TELEGRAM_BOT_SECRET', 'your-secret-key-here')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_verification_code(request):
    """
    Generate a new Telegram verification code for the authenticated user.
    
    POST /api/billing/telegram/generate-code/
    
    Response:
    {
        "verification_code": "OXI-A1B2",
        "expires_at": "2024-01-25T10:00:00Z",
        "instructions": "Send this code to @OxiWorldBot using: /verify OXI-A1B2"
    }
    """
    try:
        # Get or create billing profile
        billing_profile, created = BillingProfile.objects.get_or_create(
            user=request.user
        )
        
        # Check if already verified
        if billing_profile.telegram_verified:
            return Response({
                'error': 'Telegram already verified',
                'telegram_username': billing_profile.telegram_username
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new code
        code = billing_profile.generate_verification_code()
        
        return Response({
            'verification_code': code,
            'expires_at': billing_profile.verification_code_expires_at,
            'instructions': f'Send this code to @OxiWorldBot using: /verify {code}',
            'bot_username': 'OxiWorldBot'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def telegram_verify_callback(request):
    """
    Webhook endpoint called by the Telegram bot when user sends /verify command.
    This endpoint is NOT authenticated with JWT - it uses a secret key instead.
    
    POST /api/billing/telegram/verify-callback/
    Headers:
        X-Bot-Secret: <secret-key>
    
    Body:
    {
        "verification_code": "OXI-A1B2",
        "telegram_user_id": "123456789",
        "telegram_username": "johndoe"
    }
    
    Response:
    {
        "success": true,
        "message": "Telegram account verified successfully!",
        "user_email": "user@example.com"
    }
    """
    # Validate bot secret
    bot_secret = request.headers.get('X-Bot-Secret')
    if bot_secret != BOT_SECRET:
        return Response({
            'success': False,
            'error': 'Invalid bot secret'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get request data
    verification_code = request.data.get('verification_code', '').upper().strip()
    telegram_user_id = request.data.get('telegram_user_id', '').strip()
    telegram_username = request.data.get('telegram_username', '').strip()
    
    # Validate inputs
    if not verification_code or not telegram_user_id:
        return Response({
            'success': False,
            'error': 'Missing required fields: verification_code, telegram_user_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find billing profile with this verification code
        billing_profile = BillingProfile.objects.get(
            verification_code=verification_code
        )
        
        # Check if code is still valid
        if not billing_profile.is_verification_code_valid():
            return Response({
                'success': False,
                'error': 'Verification code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if this Telegram account is already linked to another user
        existing_profile = BillingProfile.objects.filter(
            telegram_user_id=telegram_user_id
        ).exclude(id=billing_profile.id).first()
        
        if existing_profile:
            return Response({
                'success': False,
                'error': 'This Telegram account is already linked to another user.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the Telegram account
        billing_profile.verify_telegram(telegram_user_id, telegram_username)
        
        return Response({
            'success': True,
            'message': 'Telegram account verified successfully!',
            'user_email': billing_profile.user.email,
            'telegram_username': telegram_username
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid verification code'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def telegram_verification_status(request):
    """
    Check Telegram verification status for the authenticated user.
    
    GET /api/billing/telegram/status/
    
    Response:
    {
        "verified": true,
        "telegram_username": "johndoe",
        "telegram_user_id": "123456789",
        "verified_at": "2024-01-24T10:00:00Z",
        "active_subscriptions": [...]
    }
    """
    try:
        billing_profile = BillingProfile.objects.get(user=request.user)
        
        # Get active subscriptions
        active_subscriptions = Subscription.objects.filter(
            billing_profile=billing_profile,
            status='active',
            end_date__gte=timezone.now()
        )
        
        subscription_data = [{
            'plan_name': sub.pricing_plan.name,
            'plan_category': sub.pricing_plan.plan_category,
            'end_date': sub.end_date,
            'days_remaining': sub.days_remaining,
            'telegram_groups': sub.pricing_plan.telegram_groups
        } for sub in active_subscriptions]
        
        return Response({
            'verified': billing_profile.telegram_verified,
            'telegram_username': billing_profile.telegram_username or '',
            'telegram_user_id': billing_profile.telegram_user_id or '',
            'verified_at': billing_profile.telegram_verified_at,
            'active_subscriptions': subscription_data,
            'has_pending_code': bool(
                billing_profile.verification_code and 
                billing_profile.is_verification_code_valid()
            )
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        # Create billing profile if it doesn't exist
        billing_profile = BillingProfile.objects.create(user=request.user)
        return Response({
            'verified': False,
            'telegram_username': '',
            'telegram_user_id': '',
            'verified_at': None,
            'active_subscriptions': [],
            'has_pending_code': False
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_telegram(request):
    """
    Unlink Telegram account from the authenticated user.
    
    POST /api/billing/telegram/unlink/
    
    Response:
    {
        "success": true,
        "message": "Telegram account unlinked successfully"
    }
    """
    try:
        billing_profile = BillingProfile.objects.get(user=request.user)
        
        # Clear Telegram verification
        billing_profile.telegram_user_id = None
        billing_profile.telegram_username = ''
        billing_profile.telegram_verified = False
        billing_profile.telegram_verified_at = None
        billing_profile.save()
        
        return Response({
            'success': True,
            'message': 'Telegram account unlinked successfully'
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'error': 'Billing profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
