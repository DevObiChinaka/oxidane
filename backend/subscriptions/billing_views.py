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
        "verification_code": "A3F8K2",
        "expires_at": "2024-01-25T10:00:00Z",
        "bot_url": "https://t.me/YourBot",
        "bot_username": "@YourBot",
        "instructions": "Send this code to @YourBot using: /verify A3F8K2"
    }
    """
    try:
        # Get bot configuration
        from subscriptions.models import TelegramConfiguration
        telegram_config = TelegramConfiguration.objects.first()
        
        if not telegram_config or not telegram_config.bot_username:
            return Response({
                'error': 'Telegram bot not configured. Please contact support.',
                'code': 'BOT_NOT_CONFIGURED'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Get or create billing profile
        billing_profile, created = BillingProfile.objects.get_or_create(
            user=request.user
        )
        
        # Check if already verified
        if billing_profile.telegram_verified:
            return Response({
                'already_verified': True,
                'telegram_verified': True,
                'telegram_username': billing_profile.telegram_username,
                'telegram_user_id': billing_profile.telegram_user_id,
                'message': 'Your Telegram account is already verified. You can proceed with payment.'
            }, status=status.HTTP_200_OK)
        
        # Generate new code
        code = billing_profile.generate_verification_code()
        
        # Format bot username (ensure it has @)
        bot_username = telegram_config.bot_username
        if not bot_username.startswith('@'):
            bot_username = f'@{bot_username}'
        
        # Create deep link URL (opens bot chat with START button)
        # Format: https://t.me/BotUsername?start=VERIFY_CODE
        bot_username_clean = telegram_config.bot_username.replace('@', '')
        deep_link = f'https://t.me/{bot_username_clean}?start=VERIFY_{code}'
        
        return Response({
            'verification_code': code,
            'expires_at': billing_profile.verification_code_expires_at,
            'deep_link': deep_link,
            'bot_username': bot_username,
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
        "verification_code": "A3F8K2",
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
            'plan_name': sub.plan.name if sub.plan else 'Unknown',
            'billing_period': sub.plan.billing_period if sub.plan else '',
            'end_date': sub.end_date,
            'days_remaining': sub.days_remaining,
            'telegram_groups': [group.name for group in sub.plan.telegram_groups.all()] if sub.plan else []
        } for sub in active_subscriptions]
        
        return Response({
            'verified': billing_profile.telegram_verified,
            'telegram_verified': billing_profile.telegram_verified,  # For frontend compatibility
            'telegram_username': billing_profile.telegram_username or '',
            'telegram_user_id': billing_profile.telegram_user_id or '',
            'verified_at': billing_profile.telegram_verified_at,
            'verification_error': billing_profile.telegram_verification_error or None,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_telegram_username(request):
    """
    Verify Telegram account ownership by sending confirmation code.
    
    POST /api/billing/telegram/verify-username/
    
    Body:
    {
        "verification_code": "OXI-A1B2",
        "telegram_username": "@johndoe"
    }
    
    Response:
    {
        "success": true,
        "message": "Confirmation code sent to Telegram",
        "confirmation_code": "123456"
    }
    """
    try:
        import requests
        import random
        import string
        from django.core.cache import cache
        
        verification_code = request.data.get('verification_code', '').upper().strip()
        telegram_username = request.data.get('telegram_username', '').strip()
        
        # Validate inputs
        if not verification_code or not telegram_username:
            return Response({
                'error': 'Missing required fields: verification_code, telegram_username'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure username starts with @
        if not telegram_username.startswith('@'):
            telegram_username = f'@{telegram_username}'
        
        # Get billing profile with this verification code
        try:
            billing_profile = BillingProfile.objects.get(
                user=request.user,
                verification_code=verification_code
            )
        except BillingProfile.DoesNotExist:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if code is still valid
        if not billing_profile.is_verification_code_valid():
            return Response({
                'error': 'Verification code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already verified
        if billing_profile.telegram_verified:
            return Response({
                'error': 'Telegram already verified',
                'telegram_username': billing_profile.telegram_username
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get bot configuration
        from subscriptions.models import TelegramConfiguration
        telegram_config = TelegramConfiguration.objects.first()
        
        if not telegram_config or not telegram_config.bot_token:
            return Response({
                'error': 'Telegram bot not configured. Please contact support.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        bot_token = telegram_config.bot_token
        
        # Try to get user info from Telegram
        try:
            chat_response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getChat',
                params={'chat_id': telegram_username},
                timeout=10
            )
            
            if not chat_response.ok:
                return Response({
                    'error': f'Could not find Telegram user {telegram_username}. Please check the username and try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = chat_response.json()['result']
            telegram_user_id = str(user_data['id'])
            
        except Exception as e:
            return Response({
                'error': f'Failed to verify Telegram username: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if this Telegram account is already linked to another user
        existing_profile = BillingProfile.objects.filter(
            telegram_user_id=telegram_user_id
        ).exclude(user=request.user).first()
        
        if existing_profile:
            return Response({
                'error': 'This Telegram account is already linked to another user.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate 6-digit confirmation code
        confirmation_code = ''.join(random.choices(string.digits, k=6))
        
        # Store confirmation code in cache (5 minutes expiry)
        cache_key = f'telegram_confirm_{verification_code}'
        cache.set(cache_key, {
            'confirmation_code': confirmation_code,
            'telegram_user_id': telegram_user_id,
            'telegram_username': telegram_username
        }, 300)  # 5 minutes
        
        # Send confirmation code via Telegram
        try:
            send_response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendMessage',
                json={
                    'chat_id': telegram_user_id,
                    'text': f'🔐 *Oxidane Verification*\n\nYour confirmation code: `{confirmation_code}`\n\nEnter this code on the website to complete verification.\n\nThis code expires in 5 minutes.',
                    'parse_mode': 'Markdown'
                },
                timeout=10
            )
            
            if not send_response.ok:
                return Response({
                    'error': 'Failed to send confirmation code. Please make sure you have started a chat with the bot first.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Failed to send Telegram message: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': f'Confirmation code sent to {telegram_username}',
            'telegram_username': telegram_username
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_telegram_verification(request):
    """
    Confirm Telegram verification with the code sent via Telegram.
    
    POST /api/billing/telegram/confirm/
    
    Body:
    {
        "verification_code": "OXI-A1B2",
        "confirmation_code": "123456"
    }
    
    Response:
    {
        "success": true,
        "message": "Telegram account verified successfully!",
        "telegram_username": "@johndoe"
    }
    """
    try:
        from django.core.cache import cache
        
        verification_code = request.data.get('verification_code', '').upper().strip()
        confirmation_code = request.data.get('confirmation_code', '').strip()
        
        # Validate inputs
        if not verification_code or not confirmation_code:
            return Response({
                'error': 'Missing required fields: verification_code, confirmation_code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get billing profile
        try:
            billing_profile = BillingProfile.objects.get(
                user=request.user,
                verification_code=verification_code
            )
        except BillingProfile.DoesNotExist:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if code is still valid
        if not billing_profile.is_verification_code_valid():
            return Response({
                'error': 'Verification code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cached confirmation data
        cache_key = f'telegram_confirm_{verification_code}'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return Response({
                'error': 'Confirmation code has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify confirmation code
        if cached_data['confirmation_code'] != confirmation_code:
            return Response({
                'error': 'Invalid confirmation code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update billing profile
        billing_profile.telegram_user_id = cached_data['telegram_user_id']
        billing_profile.telegram_username = cached_data['telegram_username']
        billing_profile.telegram_verified = True
        billing_profile.telegram_verified_at = timezone.now()
        billing_profile.verification_code = None
        billing_profile.verification_code_expires_at = None
        billing_profile.save()
        
        # Clear cache
        cache.delete(cache_key)
        
        return Response({
            'success': True,
            'message': 'Telegram account verified successfully!',
            'telegram_username': billing_profile.telegram_username,
            'verified_at': billing_profile.telegram_verified_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

