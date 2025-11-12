"""
Telegram Username Verification (Deep Link + Username Entry)
No webhook required - works in development without ngrok

Flow:
1. User clicks deep link to open bot
2. User returns to website and enters their Telegram username
3. Backend sends confirmation code to that username via bot
4. User enters confirmation code on website
5. Verification complete
"""

import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests

from subscriptions.models import BillingProfile, TelegramConfiguration


def generate_confirmation_code():
    """Generate a 6-digit confirmation code"""
    return ''.join(random.choices(string.digits, k=6))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_telegram_username(request):
    """
    Step 1: User enters their Telegram username
    Backend sends them a confirmation code via Telegram
    
    POST /api/v1/subscriptions/verify-telegram-username/
    Body: {
        "verification_code": "A3F8K2",
        "telegram_username": "@johndoe" or "johndoe"
    }
    
    Response: {
        "success": true,
        "message": "Confirmation code sent to your Telegram",
        "expires_in": 300
    }
    """
    verification_code = request.data.get('verification_code', '').upper().strip()
    telegram_username = request.data.get('telegram_username', '').strip()
    
    # Validate inputs
    if not verification_code or not telegram_username:
        return Response({
            'error': 'verification_code and telegram_username are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Normalize username (add @ if missing)
    if not telegram_username.startswith('@'):
        telegram_username = f'@{telegram_username}'
    
    try:
        # Check if verification code exists and belongs to this user
        billing_profile = BillingProfile.objects.get(
            user=request.user,
            verification_code=verification_code
        )
        
        # Check if code is still valid
        if not billing_profile.is_verification_code_valid():
            return Response({
                'error': 'Verification code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get bot configuration
        telegram_config = TelegramConfiguration.get_instance()
        if not telegram_config or not telegram_config.bot_token:
            return Response({
                'error': 'Telegram bot not configured. Please contact support.',
                'code': 'BOT_NOT_CONFIGURED'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        bot_token = telegram_config.bot_token
        
        # Try to get user info from Telegram API
        chat_response = requests.get(
            f'https://api.telegram.org/bot{bot_token}/getChat',
            params={'chat_id': telegram_username},
            timeout=10
        )
        
        if not chat_response.ok:
            error_data = chat_response.json()
            error_description = error_data.get('description', 'Unknown error')
            
            # User not found or invalid username
            if 'not found' in error_description.lower():
                return Response({
                    'error': f'Telegram user {telegram_username} not found. Please check your username.',
                    'code': 'USER_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            elif 'chat not found' in error_description.lower():
                return Response({
                    'error': f'Cannot send message to {telegram_username}. Please start a chat with the bot first.',
                    'code': 'CHAT_NOT_STARTED',
                    'hint': 'Click "Open Bot" button first, then click START in Telegram'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': f'Telegram API error: {error_description}',
                    'code': 'TELEGRAM_API_ERROR'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract user ID
        user_data = chat_response.json()['result']
        telegram_user_id = str(user_data['id'])
        
        # Check if this Telegram account is already linked to another user
        existing_profile = BillingProfile.objects.filter(
            telegram_user_id=telegram_user_id
        ).exclude(user=request.user).first()
        
        if existing_profile:
            return Response({
                'error': f'This Telegram account is already linked to another user.',
                'code': 'ALREADY_LINKED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate confirmation code
        confirmation_code = generate_confirmation_code()
        
        # Store confirmation code in cache (5 minutes expiry)
        cache_key = f'telegram_confirm_{verification_code}_{telegram_user_id}'
        cache.set(cache_key, {
            'confirmation_code': confirmation_code,
            'telegram_user_id': telegram_user_id,
            'telegram_username': telegram_username,
            'user_id': request.user.id
        }, timeout=300)  # 5 minutes
        
        # Send confirmation code via Telegram
        send_response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            json={
                'chat_id': telegram_user_id,
                'text': f'🔐 Your Oxidane verification code:\n\n<b>{confirmation_code}</b>\n\nEnter this code on the website to complete verification.\n\nCode expires in 5 minutes.',
                'parse_mode': 'HTML'
            },
            timeout=10
        )
        
        if not send_response.ok:
            error_data = send_response.json()
            return Response({
                'error': f'Failed to send message: {error_data.get("description")}',
                'code': 'MESSAGE_SEND_FAILED'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': f'Confirmation code sent to {telegram_username}',
            'expires_in': 300,
            'hint': 'Check your Telegram messages'
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'error': 'Invalid verification code or code does not belong to your account'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except requests.RequestException as e:
        return Response({
            'error': f'Network error communicating with Telegram: {str(e)}',
            'code': 'NETWORK_ERROR'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        return Response({
            'error': f'Unexpected error: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_telegram_code(request):
    """
    Step 2: User enters the confirmation code they received via Telegram
    Backend verifies the code and completes verification
    
    POST /api/v1/subscriptions/confirm-telegram-code/
    Body: {
        "verification_code": "A3F8K2",
        "confirmation_code": "123456"
    }
    
    Response: {
        "success": true,
        "message": "Telegram account verified successfully!",
        "telegram_username": "@johndoe"
    }
    """
    verification_code = request.data.get('verification_code', '').upper().strip()
    confirmation_code = request.data.get('confirmation_code', '').strip()
    
    # Validate inputs
    if not verification_code or not confirmation_code:
        return Response({
            'error': 'verification_code and confirmation_code are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get billing profile
        billing_profile = BillingProfile.objects.get(
            user=request.user,
            verification_code=verification_code
        )
        
        # Check if code is still valid
        if not billing_profile.is_verification_code_valid():
            return Response({
                'error': 'Verification code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find cached confirmation data
        # We need to search for the cache key since we don't know the telegram_user_id yet
        cache_pattern = f'telegram_confirm_{verification_code}_*'
        
        # Try to get from cache (simplified - check common pattern)
        cache_key = None
        cached_data = None
        
        # Try to find the cache entry by iterating possible user IDs
        # Alternative: store a mapping of verification_code -> telegram_user_id
        # For now, we'll use a secondary cache key
        temp_cache_key = f'telegram_verify_map_{verification_code}'
        telegram_user_id = cache.get(temp_cache_key)
        
        if telegram_user_id:
            cache_key = f'telegram_confirm_{verification_code}_{telegram_user_id}'
            cached_data = cache.get(cache_key)
        
        if not cached_data:
            return Response({
                'error': 'Confirmation code expired or invalid. Please request a new code.',
                'code': 'CODE_EXPIRED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify confirmation code matches
        if cached_data['confirmation_code'] != confirmation_code:
            return Response({
                'error': 'Invalid confirmation code. Please check and try again.',
                'code': 'INVALID_CODE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user ID matches
        if cached_data['user_id'] != request.user.id:
            return Response({
                'error': 'This confirmation code belongs to a different user',
                'code': 'USER_MISMATCH'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # All checks passed - update billing profile
        billing_profile.telegram_user_id = cached_data['telegram_user_id']
        billing_profile.telegram_username = cached_data['telegram_username']
        billing_profile.telegram_verified = True
        billing_profile.telegram_verified_at = timezone.now()
        billing_profile.verification_code = None  # Clear verification code
        billing_profile.verification_code_expires_at = None
        billing_profile.save()
        
        # Clear cache
        cache.delete(cache_key)
        cache.delete(temp_cache_key)
        
        return Response({
            'success': True,
            'message': 'Telegram account verified successfully!',
            'telegram_username': cached_data['telegram_username'],
            'telegram_verified': True
        }, status=status.HTTP_200_OK)
        
    except BillingProfile.DoesNotExist:
        return Response({
            'error': 'Invalid verification code or code does not belong to your account'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': f'Unexpected error: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
