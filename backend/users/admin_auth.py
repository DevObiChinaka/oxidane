from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.sessions.models import Session
import random
import string
import hashlib
import json
from datetime import timedelta
from .email_service import EmailTemplateService
import logging

logger = logging.getLogger(__name__)

# Get the custom User model
User = get_user_model()

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.sessions.models import Session
import random
import string
import hashlib
import json
from datetime import timedelta
from .email_service import EmailTemplateService
import logging

logger = logging.getLogger(__name__)

# Get the custom User model
User = get_user_model()


# ============================================================================
# MODERN ADMIN AUTH: OTP + JWT (Secure 2FA with JWT session management)
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_request_jwt(request):
    """
    Step 1: Validate admin credentials and send OTP (2FA)
    Returns session token for OTP verification
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    try:
        user_obj = User.objects.get(email=email)
        user = authenticate(username=user_obj.username, password=password)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user:
        return Response({
            'success': False,
            'error': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user is admin/staff
    if not (user.is_staff or user.is_superuser):
        return Response({
            'success': False,
            'error': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Create session token for OTP verification
    session_token = hashlib.sha256(f"{user.id}{timezone.now()}".encode()).hexdigest()
    
    # Store OTP in cache (10 minutes expiry)
    cache_key = f"admin_otp_jwt_{session_token}"
    cache_data = {
        'user_id': str(user.id),
        'otp': otp,
        'email': user.email,
        'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat()
    }
    cache.set(cache_key, json.dumps(cache_data), 600)
    
    # Send OTP email
    try:
        login_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', 'Unknown')
        login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        email_service = EmailTemplateService()
        
        # Email content for OTP
        subject = f'Admin Login OTP - {otp}'
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">OxiWorld Admin Login</h1>
                <p style="color: #e0e0e0; margin: 8px 0 0 0;">Two-Factor Authentication</p>
            </div>
            <div style="background: white; padding: 40px 30px; border: 1px solid #e0e0e0;">
                <h2 style="color: #000856;">Hi {user.first_name or user.username},</h2>
                <p>Please use this verification code to complete your admin login:</p>
                <div style="background: #f5f5f5; border: 2px solid #00B38F; border-radius: 8px; padding: 25px; text-align: center; margin: 30px 0;">
                    <div style="font-size: 36px; font-weight: bold; color: #000856; letter-spacing: 8px;">{otp}</div>
                    <p style="color: #666; font-size: 13px; margin: 10px 0 0 0;">Valid for 10 minutes</p>
                </div>
                <p style="font-size: 14px; color: #666;">Login Time: {login_time}</p>
                <p style="font-size: 14px; color: #666;">Login IP: {login_ip}</p>
                <p style="font-size: 14px; color: #ff0000; font-weight: bold;">Never share this code with anyone.</p>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject=subject,
            message=f'Your admin login OTP is: {otp}\n\nValid for 10 minutes.\nLogin Time: {login_time}\nLogin IP: {login_ip}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Admin OTP sent to {user.email}")
        
        response_data = {
            'success': True,
            'session_token': session_token,
            'message': f'OTP sent to {user.email[:3]}***@{user.email.split("@")[1]}',
            'expires_in': 600
        }
        
        # Include OTP in response for development ONLY
        if settings.DEBUG:
            response_data['debug_otp'] = otp
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_verify_otp_jwt(request):
    """
    Step 2: Verify OTP and return JWT tokens for API authentication
    Returns standard JWT access + refresh tokens
    """
    session_token = request.data.get('session_token')
    otp_input = request.data.get('otp')
    
    if not session_token or not otp_input:
        return Response({
            'success': False,
            'error': 'Session token and OTP are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get OTP data from cache
    cache_key = f"admin_otp_jwt_{session_token}"
    cache_data_json = cache.get(cache_key)
    
    if not cache_data_json:
        return Response({
            'success': False,
            'error': 'Invalid or expired session'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache_data = json.loads(cache_data_json)
    
    # Verify OTP
    if cache_data['otp'] != otp_input:
        return Response({
            'success': False,
            'error': 'Invalid OTP'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if OTP expired
    expires_at = timezone.datetime.fromisoformat(cache_data['expires_at'])
    if timezone.now() > expires_at:
        cache.delete(cache_key)
        return Response({
            'success': False,
            'error': 'OTP has expired'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # OTP valid! Get user and generate JWT tokens
    try:
        user = User.objects.get(id=cache_data['user_id'])
        
        # Generate JWT tokens using rest_framework_simplejwt
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Clear OTP from cache
        cache.delete(cache_key)
        
        # Send successful login notification using EmailTemplateService
        try:
            from .email_service import EmailTemplateService
            email_service = EmailTemplateService()
            
            login_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', 'Unknown')
            login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p')
            
            # Get device info
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if 'Mobile' in user_agent:
                device = 'Mobile Device'
            elif 'Tablet' in user_agent:
                device = 'Tablet'
            else:
                device = 'Desktop/Laptop'
            
            context = {
                'login_time': login_time,
                'login_ip': login_ip,
                'signin_datetime': login_time,
                'device': device,
                'location': login_ip,
            }
            
            # Use admin signin notification template - specifically the success template, not OTP
            result = email_service.send_email(
                template_type='signin_notification',
                template_name='Admin Login Success - Welcome Back',  # Specify exact template name
                recipient_email=user.email,
                user=user,
                custom_vars=context
            )
            
            if not result or not result.get('success'):
                # Fallback to plain email if template fails
                send_mail(
                    subject='Admin Login Successful',
                    message=f"Hello {user.first_name or user.username},\n\nYou have successfully logged in.\n\nLogin Time: {login_time}\nLogin IP: {login_ip}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except Exception as e:
            logger.error(f"Failed to send login success notification: {str(e)}")
        
        # Return JWT tokens and user data (same format as regular login)
        return Response({
            'success': True,
            'message': 'Login successful',
            'access': access_token,
            'refresh': refresh_token,
            'token': access_token,  # For compatibility
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'avatar': user.avatar if hasattr(user, 'avatar') else None,
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# OLD ADMIN AUTH: Session-based (Legacy - kept for reference)
# ============================================================================

# Admin authentication views
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_request(request):
    """First step: Validate admin credentials and send OTP"""
    
    credential = request.data.get('username')  # Can be email or username
    password = request.data.get('password')
    
    if not credential or not password:
        return Response({
            'success': False,
            'error': 'Email/username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Try to authenticate with username first, then email
    user = None
    
    # Check if credential looks like an email
    if '@' in credential:
        try:
            user_obj = User.objects.get(email=credential)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    
    # If email auth failed or credential is username, try username auth
    if not user:
        user = authenticate(username=credential, password=password)
    
    if not user:
        return Response({
            'success': False,
            'error': 'Invalid email/username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user is admin/staff
    if not (user.is_staff or user.is_superuser):
        return Response({
            'success': False,
            'error': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Create session token for OTP verification
    session_token = hashlib.sha256(f"{user.username}{timezone.now()}".encode()).hexdigest()
    
    # Store OTP and user info in cache (expires in 10 minutes)
    cache_key = f"admin_otp_{session_token}"
    cache_data = {
        'username': user.username,
        'user_id': str(user.id),  # Convert UUID to string
        'otp': otp,
        'email': user.email,
        'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat()
    }
    cache.set(cache_key, json.dumps(cache_data), 600)  # 10 minutes
    
    # Send OTP email using email template service
    try:
        admin_email = user.email
        if not admin_email:
            return Response({
                'success': False,
                'error': 'Admin email not configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get request IP and user agent for security tracking
        login_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', 'Unknown')
        login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        # Prepare email service and send OTP using template
        email_service = EmailTemplateService()
        
        # Custom variables for the OTP email
        custom_vars = {
            'otp_code': otp,
            'login_time': login_time,
            'login_ip': login_ip,
        }
        
        # Send the email using the signin_notification template
        email_result = email_service.send_email(
            template_type='signin_notification',
            recipient_email=admin_email,
            user=user,
            custom_vars=custom_vars
        )
        
        if not email_result['success']:
            logger.error(f"Failed to send OTP email to {admin_email}: {email_result}")
            # Fallback to basic email if template service fails
            subject = 'OxiWorld Admin Login - OTP Verification'
            message = f"""
            Hello {user.first_name or user.username},
            
            Your OTP for admin login is: {otp}
            
            This code will expire in 10 minutes.
            Login attempt from IP: {login_ip} at {login_time}
            
            If you did not request this login, please change your password immediately.
            
            Best regards,
            OxiWorld Forex Academy Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False
            )
        
        logger.info(f"OTP email sent successfully to {admin_email} for admin login")
        
        response_data = {
            'success': True,
            'session_token': session_token,
            'message': f'OTP sent to {admin_email[:3]}***@{admin_email.split("@")[1]}',
            'expires_in': 600  # 10 minutes
        }
        
        # Include OTP in response for development/testing (only in DEBUG mode)
        if settings.DEBUG:
            response_data['debug_otp'] = otp
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_verify_otp(request):
    """Second step: Verify OTP and create admin session"""
    
    session_token = request.data.get('session_token')
    otp_input = request.data.get('otp')
    credential = request.data.get('credential')  # Alternative method: use credential instead of session_token
    
    # Check if we have either session_token or credential
    if not otp_input:
        return Response({
            'success': False,
            'error': 'OTP is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not session_token and not credential:
        return Response({
            'success': False,
            'error': 'Either session_token or credential is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache_data = None
    
    # Method 1: Using session token (standard flow)
    if session_token:
        cache_key = f"admin_otp_{session_token}"
        cache_data_json = cache.get(cache_key)
        
        if not cache_data_json:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cache_data = json.loads(cache_data_json)
    
    # Method 2: Using credential (alternative for testing)
    elif credential:
        # Find user by credential
        user = None
        try:
            if '@' in credential:
                user = User.objects.get(email=credential)
            else:
                user = User.objects.get(username=credential)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has a valid OTP
        if not user.email_verification_otp or not user.email_verification_otp_expires:
            return Response({
                'success': False,
                'error': 'No valid OTP found for this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create cache_data structure for consistency
        cache_data = {
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'otp': user.email_verification_otp,
            'expires_at': user.email_verification_otp_expires.isoformat()
        }
    
    # Verify OTP
    if cache_data['otp'] != otp_input:
        return Response({
            'success': False,
            'error': 'Invalid OTP'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if OTP has expired
    expires_at = timezone.datetime.fromisoformat(cache_data['expires_at'])
    if timezone.now() > expires_at:
        cache.delete(cache_key)  # Clean up expired OTP
        return Response({
            'success': False,
            'error': 'OTP has expired'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create admin session
    try:
        user = User.objects.get(id=cache_data['user_id'])
        
        # Generate admin session token
        admin_session_token = hashlib.sha256(f"admin_{user.id}_{timezone.now()}".encode()).hexdigest()
        
        # Store admin session (expires in 24 hours)
        login_time_formatted = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        admin_session_key = f"admin_session_{admin_session_token}"
        admin_session_data = {
            'user_id': str(user.id),  # Convert UUID to string
            'username': user.username,
            'email': user.email,
            'is_admin': True,
            'login_time': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=24)).isoformat()
        }
        cache.set(admin_session_key, json.dumps(admin_session_data), 86400)  # 24 hours
        
        # Clean up OTP cache
        if session_token:
            cache.delete(cache_key)
        
        # Send successful login notification email
        try:
            login_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', 'Unknown')
            
            email_service = EmailTemplateService()
            
            # Custom variables for success notification
            success_vars = {
                'login_time': login_time_formatted,
                'login_ip': login_ip,
                'admin_dashboard_url': f"{settings.FRONTEND_URL}/admin" if hasattr(settings, 'FRONTEND_URL') else "#",
            }
            
            # Send success notification email using signin_notification template
            success_result = email_service.send_email(
                template_type='signin_notification',
                recipient_email=user.email,
                user=user,
                custom_vars=success_vars
            )
            
            if success_result['success']:
                logger.info(f"Login success notification sent to {user.email}")
            else:
                logger.warning(f"Failed to send login success notification to {user.email}")
                
        except Exception as e:
            logger.error(f"Error sending login success notification: {str(e)}")
            # Don't fail the login if notification fails
        
        return Response({
            'success': True,
            'admin_token': admin_session_token,
            'message': 'Login successful',
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'expires_in': 86400  # 24 hours
        })
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_logout(request):
    """Logout admin and invalidate session"""
    
    admin_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    
    if admin_token:
        cache_key = f"admin_session_{admin_token}"
        cache.delete(cache_key)
    
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@api_view(['GET'])
@permission_classes([AllowAny])
def admin_check_session(request):
    """Check if admin session is valid"""
    
    admin_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    
    if not admin_token:
        return Response({
            'authenticated': False,
            'error': 'No admin token provided'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    cache_key = f"admin_session_{admin_token}"
    session_data_json = cache.get(cache_key)
    
    if not session_data_json:
        return Response({
            'authenticated': False,
            'error': 'Invalid or expired session'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    session_data = json.loads(session_data_json)
    
    # Check if session has expired
    expires_at = timezone.datetime.fromisoformat(session_data['expires_at'])
    if timezone.now() > expires_at:
        cache.delete(cache_key)  # Clean up expired session
        return Response({
            'authenticated': False,
            'error': 'Session expired'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'authenticated': True,
        'user': {
            'username': session_data['username'],
            'email': session_data['email']
        },
        'expires_at': session_data['expires_at']
    })


# Admin permission decorator
def admin_required(view_func):
    """Decorator to check admin authentication for API views"""
    def wrapper(request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug logging
        logger.info(f"🔐 admin_required check for {request.path}")
        logger.info(f"🔐 Authorization header: {request.META.get('HTTP_AUTHORIZATION', 'NOT FOUND')[:50]}")
        
        admin_token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        if not admin_token:
            logger.warning(f"🔐 No admin token provided for {request.path}")
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"🔐 Checking cache for admin_session_{admin_token[:20]}...")
        cache_key = f"admin_session_{admin_token}"
        session_data_json = cache.get(cache_key)
        
        if not session_data_json:
            logger.warning(f"🔐 Session not found in cache for token: {admin_token[:20]}...")
            return Response({
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
            return Response({
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        session_data = json.loads(session_data_json)
        
        # Check if session has expired
        expires_at = timezone.datetime.fromisoformat(session_data['expires_at'])
        if timezone.now() > expires_at:
            cache.delete(cache_key)
            return Response({
                'error': 'Session expired'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Add admin user to request
        request.admin_user = session_data
        
        return view_func(request, *args, **kwargs)
    
    return wrapper