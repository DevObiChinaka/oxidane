"""
Password Reset and OTP API Views
Following Django REST Framework best practices
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .otp_manager import OTPManager, PasswordResetManager

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset email
    
    POST /api/auth/password-reset/request/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Always return success to prevent email enumeration
    try:
        user = User.objects.get(email=email, is_active=True)
        
        # Create reset token
        success, message, token = PasswordResetManager.create_reset_token(user.id, email)
        
        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Send reset email
        user_name = user.get_full_name() or user.email.split('@')[0]
        email_success, email_message = PasswordResetManager.send_reset_email(
            email, token, user_name
        )
        
        if not email_success:
            return Response(
                {'error': 'Failed to send reset email. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except User.DoesNotExist:
        # Don't reveal that user doesn't exist
        pass
    
    # Always return success message
    return Response({
        'success': True,
        'message': 'If an account exists with this email, you will receive password reset instructions.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_token(request):
    """
    Verify password reset token is valid
    
    POST /api/auth/password-reset/verify/
    Body: { "token": "reset_token" }
    """
    token = request.data.get('token', '').strip()
    
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_valid, user_id = PasswordResetManager.verify_reset_token(token)
    
    if not is_valid:
        return Response(
            {'error': 'Invalid or expired reset token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'success': True,
        'message': 'Token is valid'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password using token
    
    POST /api/auth/password-reset/confirm/
    Body: {
        "token": "reset_token",
        "new_password": "new_password",
        "confirm_password": "new_password"
    }
    """
    token = request.data.get('token', '').strip()
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')
    
    # Validation
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not new_password:
        return Response(
            {'error': 'New password is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {'error': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify and consume token
    is_valid, user_id = PasswordResetManager.consume_reset_token(token)
    
    if not is_valid:
        return Response(
            {'error': 'Invalid or expired reset token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
        
        # Validate password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password reset successfully. You can now login with your new password.'
        })
    
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def request_login_otp(request):
    """
    Request OTP for login (optional 2FA)
    
    POST /api/auth/otp/request/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email, is_active=True)
        
        # Send OTP
        success, message = OTPManager.send_otp(
            identifier=email,
            email=email,
            purpose='login'
        )
        
        if not success:
            if 'wait' in message.lower():
                return Response(
                    {'error': message},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            return Response(
                {'error': message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'success': True,
            'message': 'OTP sent to your email',
            'expires_in': OTPManager.OTP_EXPIRY_MINUTES * 60  # seconds
        })
    
    except User.DoesNotExist:
        # Don't reveal that user doesn't exist
        return Response({
            'success': True,
            'message': 'If an account exists with this email, an OTP has been sent.'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_login_otp(request):
    """
    Verify OTP for login
    
    POST /api/auth/otp/verify/
    Body: {
        "email": "user@example.com",
        "otp": "123456"
    }
    """
    email = request.data.get('email', '').lower().strip()
    otp = request.data.get('otp', '').strip()
    
    if not email or not otp:
        return Response(
            {'error': 'Email and OTP are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OTP
    is_valid, message = OTPManager.verify_otp(email, otp)
    
    if not is_valid:
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'success': True,
        'message': 'OTP verified successfully'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password for authenticated user
    
    POST /api/auth/change-password/
    Body: {
        "current_password": "old_password",
        "new_password": "new_password",
        "confirm_password": "new_password"
    }
    """
    user = request.user
    current_password = request.data.get('current_password', '')
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')
    
    # Validation
    if not current_password:
        return Response(
            {'error': 'Current password is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not new_password:
        return Response(
            {'error': 'New password is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {'error': 'New passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check current password
    if not user.check_password(current_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password strength
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response(
            {'error': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset_otp(request):
    """
    Request password reset OTP code (instead of email link)
    
    POST /api/auth/password-reset-otp/request/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Always return success to prevent email enumeration
    try:
        user = User.objects.get(email=email, is_active=True)
        
        # Generate and send OTP
        success, message = OTPManager.generate_and_send_otp(
            user.id, 
            email, 
            user.get_full_name() or email.split('@')[0],
            purpose='password_reset'
        )
        
        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
    
    except User.DoesNotExist:
        # Don't reveal that user doesn't exist
        pass
    
    # Always return success message
    return Response({
        'success': True,
        'message': 'If an account exists with this email, you will receive a password reset code.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_password_reset_otp(request):
    """
    Verify OTP and reset password
    
    POST /api/auth/password-reset-otp/verify/
    Body: { 
        "email": "user@example.com",
        "otp": "123456",
        "new_password": "newpassword123"
    }
    """
    email = request.data.get('email', '').lower().strip()
    otp = request.data.get('otp', '').strip()
    new_password = request.data.get('new_password', '')
    
    if not email or not otp or not new_password:
        return Response(
            {'error': 'Email, OTP, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OTP
    try:
        user = User.objects.get(email=email, is_active=True)
        
        is_valid, message = OTPManager.verify_otp(user.id, otp, purpose='password_reset')
        
        if not is_valid:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password reset successfully'
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid email or OTP'},
            status=status.HTTP_400_BAD_REQUEST
        )
