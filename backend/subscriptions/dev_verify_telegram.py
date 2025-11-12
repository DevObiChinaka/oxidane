"""
Development-only: Manual Telegram Verification
This bypasses the bot and allows testing the payment flow locally
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from subscriptions.models import BillingProfile

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dev_skip_telegram_verification(request):
    """
    DEV ONLY: Skip Telegram verification for testing
    
    POST /api/dev/skip-telegram-verification/
    
    This endpoint allows you to mark your account as Telegram-verified
    without actually going through the bot verification process.
    
    USE ONLY FOR DEVELOPMENT/TESTING!
    """
    try:
        # Get or create billing profile
        billing_profile, created = BillingProfile.objects.get_or_create(
            user=request.user
        )
        
        # Mark as verified with dummy data
        billing_profile.telegram_verified = True
        billing_profile.telegram_user_id = '999999999'  # Dummy ID
        billing_profile.telegram_username = f"{request.user.username}_dev"
        billing_profile.verification_code = None
        billing_profile.verification_code_expires_at = None
        billing_profile.save()
        
        return Response({
            'success': True,
            'message': '✅ [DEV] Telegram verification skipped',
            'telegram_verified': True,
            'telegram_username': billing_profile.telegram_username
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
