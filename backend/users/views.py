from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import json
import requests
import random
from datetime import timedelta
from .models import User, OAuthProvider, EmailTemplate

# Import template service if available
try:
    from .email_template_service import EmailTemplateService
    template_service = EmailTemplateService()
    USE_TEMPLATES = True
except ImportError:
    USE_TEMPLATES = False

# Old welcome email function removed - now using EmailTemplateService

def send_user_login_otp_email(user, otp, ip_address='Unknown'):
    """Send OTP email for user login using template system"""
    from .notification_helpers import should_send_notification
    
    # Check if user wants to receive login notifications
    if not should_send_notification(user, 'email_login'):
        return False
    
    try:
        if USE_TEMPLATES:
            # Use template system
            context = {
                'user': user,
                'otp_code': otp,
                'login_time': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
                'login_ip': ip_address,
                'company_name': 'OxiWorld Forex Academy',
                'current_year': timezone.now().year,
            }
            
            success = template_service.send_email(
                template_type='user_login_otp',
                recipient_email=user.email,
                context=context
            )
            
            if success:
                return True
            # Fallback to hardcoded if template fails
        
        # Fallback hardcoded email (simplified version)
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Sign-In Verification</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">OxiWorld</h1>
                <p style="color: #e0e0e0; margin: 8px 0 0 0;">Sign-In Verification</p>
            </div>
            <div style="background: white; padding: 40px 30px;">
                <h2>Hi {user.first_name},</h2>
                <p>Please use this verification code to complete your sign-in:</p>
                <div style="background: #f5f5f5; border: 2px solid #00B38F; border-radius: 8px; padding: 25px; text-align: center; margin: 30px 0;">
                    <div style="font-size: 36px; font-weight: bold; color: #000856; letter-spacing: 8px;">{otp}</div>
                    <p style="color: #666; font-size: 13px; margin: 10px 0 0 0;">Valid for 10 minutes</p>
                </div>
                <p style="font-size: 14px; color: #666;">Never share this code with anyone.</p>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject='Sign-In Verification Code - OxiWorld',
            message=f'Your verification code is: {otp}\n\nValid for 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending login OTP email: {str(e)}")
        return False

def send_signin_notification_email(user, signin_details=None, request=None):
    """Send sign-in notification email to users using EmailTemplateService"""
    try:
        # Try using EmailTemplateService first
        from .email_service import EmailTemplateService
        email_service = EmailTemplateService()
        
        current_time = timezone.now().strftime('%B %d, %Y at %I:%M %p')
        signin_method = signin_details.get('method', 'Email & Password') if signin_details else 'Email & Password'
        
        # Extract device and location info if request is available
        device = 'Unknown Device'
        location = 'Unknown Location'
        
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            # Simple device detection
            if 'Mobile' in user_agent:
                device = 'Mobile Device'
            elif 'Tablet' in user_agent:
                device = 'Tablet'
            else:
                device = 'Desktop/Laptop'
                
            # Get IP for location (basic)
            ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
            location = f"IP: {ip_address}"
        
        # Use user_signin_notification template (not admin signin_notification)
        context = {
            'signin_datetime': current_time,
            'signin_method': signin_method,
            'device': device,
            'location': location,
            'login_time': current_time,
            'login_ip': location,
        }
        
        result = email_service.send_email(
            template_type='user_signin_notification',
            recipient_email=user.email,
            user=user,
            custom_vars=context
        )
        
        if result and result.get('success'):
            return True
        
        # Fallback to hardcoded if template fails
        current_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        signin_method = signin_details.get('method', 'Email & Password') if signin_details else 'Email & Password'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>OxiWorld Forex Academy - Account Sign-In Notification</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">🔐 OxiWorld</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 14px;">Account Sign-In Notification</p>
            </div>
            
            <div style="background: white; padding: 35px 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
                <h2 style="color: #333; margin-top: 0; font-size: 22px; font-weight: 600;">👋 Welcome Back, {user.first_name}!</h2>
                <p style="font-size: 16px; margin-bottom: 25px; color: #555;">Your OxiWorld Forex Academy account was successfully accessed.</p>
                
                <div style="background: #f8f9ff; border: 2px solid #667eea; padding: 25px; border-radius: 10px; margin: 25px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #667eea; font-size: 18px; font-weight: 600;">📊 Sign-In Details</h3>
                    <p style="margin: 8px 0; color: #333; font-size: 15px;"><strong>Time:</strong> {current_time}</p>
                    <p style="margin: 8px 0; color: #333; font-size: 15px;"><strong>Method:</strong> {signin_method}</p>
                    <p style="margin: 8px 0; color: #333; font-size: 15px;"><strong>Email:</strong> {user.email}</p>
                </div>
                
                <div style="background: #e8f5e8; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <p style="margin: 0; color: #155724; font-size: 14px;">
                        <strong>✅ Secure Access:</strong> If this was you, no action is needed. 
                        Continue exploring your forex education journey!
                    </p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <p style="margin: 0; color: #856404; font-size: 14px;">
                        <strong>🚨 Suspicious Activity?</strong> If you didn't sign in, please immediately:
                        <br>• Change your password
                        <br>• Contact support@oxiworld.com
                        <br>• Review your account security
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')}/dashboard" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">
                        📈 View Dashboard
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 0 0 10px 0;">© 2025 OxiWorld Forex Academy. All rights reserved.</p>
                <p style="margin: 0;">This is an automated security notification.</p>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
🔐 OxiWorld Forex Academy - Account Sign-In Notification

Hi {user.first_name},

Your OxiWorld Forex Academy account was successfully accessed.

📊 Sign-In Details:
• Time: {current_time}
• Method: {signin_method}  
• Email: {user.email}

✅ If this was you, no action is needed.

🚨 If you didn't sign in:
• Change your password immediately
• Contact support@oxiworld.com
• Review your account security

Dashboard: {getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')}/dashboard

© 2025 OxiWorld Forex Academy
This is an automated security notification.
        """
        
        send_mail(
            subject=f'🔐 OxiWorld Forex Academy Sign-In Notification - {current_time}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
    except Exception as e:
        print(f"Failed to send sign-in notification to {user.email}: {str(e)}")

@csrf_exempt
@require_http_methods(["POST"])
def check_email(request):
    """
    Check if an email address is already registered
    Used for real-time email validation during registration
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check if user exists with this email
        user_exists = User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'exists': user_exists,
            'email': email,
            'message': 'Account already exists with this email' if user_exists else 'Email is available'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """
    Standards-compliant registration: Send OTP first, create user account only after verification
    Step 1: Validate data and send OTP (NO user account created yet)
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Support legacy 'name' field for backward compatibility
        if not first_name and not last_name:
            name = data.get('name', '')
            if name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if not email or not password or not first_name:
            return JsonResponse({'error': 'First name, email and password are required'}, status=400)
        
        # Check if user already exists and is verified
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.is_email_verified:
            return JsonResponse({'error': 'User with this email already exists'}, status=400)
        
        # Generate OTP for email verification
        otp = str(random.randint(100000, 999999))
        
        # Store pending registration data temporarily in cache (expires in 10 minutes)
        pending_registration = {
            'email': email,
            'password': password,  # Will be hashed when user is actually created
            'first_name': first_name,
            'last_name': last_name,
            'otp': otp,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat()
        }
        
        cache_key = f"pending_registration_{email}"
        cache.set(cache_key, pending_registration, timeout=600)  # 10 minutes
        
        # If existing unverified user, delete them since we're starting fresh
        if existing_user and not existing_user.is_email_verified:
            existing_user.delete()
        
        try:
            # Use the new email template system for verification emails
            from .email_automation import send_verification_email
            
            # Create temporary user object for template processing
            temp_user = type('TempUser', (), {
                'email': email,
                'username': email,  # Use email as username for temp user
                'first_name': first_name,
                'last_name': last_name,
            })()
            
            # Send verification email using template system
            email_sent = send_verification_email(temp_user, otp_code=otp)
            
            if email_sent:
                response_data = {
                    'message': 'Verification code sent. Please check your email and enter the code to create your account.',
                    'email': email,
                    'otp_sent': True,
                    'requires_verification': True,
                    'account_created': False  # Important: No account created yet!
                }
                
                # For development debugging
                if settings.DEBUG:
                    response_data['debug_otp'] = otp
                    
                return JsonResponse(response_data, status=200)
            else:
                # Clean up cache if email fails
                cache.delete(cache_key)
                return JsonResponse({'error': 'Failed to send verification email. Please try again.'}, status=500)
                
        except Exception as e:
            # Clean up cache if email fails
            cache.delete(cache_key)
            return JsonResponse({'error': f'Failed to send verification email: {str(e)}'}, status=500)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_email_otp(request):
    """
    Standards-compliant OTP verification: Create user account only after successful OTP verification
    Step 2: Verify OTP and create the user account
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return JsonResponse({'error': 'Email and OTP are required'}, status=400)
        
        # First check if user already exists and is verified
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.is_email_verified:
            return JsonResponse({'error': 'Email already verified'}, status=400)
        
        # Get pending registration data from cache
        cache_key = f"pending_registration_{email}"
        pending_registration = cache.get(cache_key)
        
        if not pending_registration:
            return JsonResponse({
                'error': 'Registration session expired or not found. Please register again.',
                'code': 'SESSION_EXPIRED'
            }, status=400)
        
        # Verify OTP matches and hasn't expired
        if pending_registration['otp'] != otp:
            return JsonResponse({'error': 'Invalid verification code'}, status=400)
        
        # Check if OTP has expired
        expires_at = timezone.datetime.fromisoformat(pending_registration['expires_at'].replace('Z', '+00:00'))
        if timezone.now() > expires_at:
            cache.delete(cache_key)  # Clean up expired session
            return JsonResponse({
                'error': 'Verification code has expired. Please register again.',
                'code': 'OTP_EXPIRED'
            }, status=400)
        
        # OTP is valid! Now create the user account
        try:
            # Get first_name and last_name from pending registration
            first_name = pending_registration.get('first_name', '')
            last_name = pending_registration.get('last_name', '')
            
            # Fallback to parsing 'name' field for backward compatibility
            if not first_name:
                name = pending_registration.get('name', '')
                if name:
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Delete any existing unverified user with same email
            if existing_user:
                existing_user.delete()
            
            # Create the new verified and active user
            user = User.objects.create(
                username=email,  # Use email as username
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(pending_registration['password']),
                is_active=True,  # Account is active immediately after verification
                is_email_verified=True  # Email is verified
            )
            
            # Welcome email will be sent automatically via Django signals in email_automation.py
            # No manual trigger needed - the post_save signal will handle it
            
            # Clean up the pending registration
            cache.delete(cache_key)
            
            return JsonResponse({
                'message': '🎉 Account created successfully! Welcome to OxiWorld.',
                'success': True,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}".strip(),
                    'is_email_verified': user.is_email_verified,
                    'is_active': user.is_active,
                }
            })
        
        except Exception as e:
            # Clean up cache on error
            cache.delete(cache_key)
            return JsonResponse({'error': f'Failed to create account: {str(e)}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def resend_verification_otp(request):
    """
    Resend OTP for pending registrations (cache-based) or existing unverified users
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check for existing verified user
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.is_email_verified:
            return JsonResponse({'error': 'Email is already verified'}, status=400)
        
        # Check if there's a pending registration in cache
        cache_key = f"pending_registration_{email}"
        pending_registration = cache.get(cache_key)
        
        if pending_registration:
            # Generate new OTP for pending registration
            otp = str(random.randint(100000, 999999))
            
            # Update pending registration with new OTP
            pending_registration['otp'] = otp
            pending_registration['expires_at'] = (timezone.now() + timedelta(minutes=10)).isoformat()
            cache.set(cache_key, pending_registration, timeout=600)
            
            # Get first_name and last_name with fallback support
            first_name = pending_registration.get('first_name', '')
            last_name = pending_registration.get('last_name', '')
            
            # Fallback to parsing 'name' field for backward compatibility
            if not first_name:
                name = pending_registration.get('name', '')
                if name:
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        elif existing_user and not existing_user.is_email_verified:
            # Handle existing unverified user (old system)
            otp = existing_user.generate_email_verification_otp()
            first_name = existing_user.first_name
            last_name = existing_user.last_name
        
        else:
            return JsonResponse({
                'error': 'No pending registration found. Please register first.',
                'code': 'NO_PENDING_REGISTRATION'
            }, status=404)
        
        try:
            # Use the new email template system for resend OTP
            from .email_automation import send_verification_email
            
            # Create temporary user object for template processing
            if pending_registration:
                temp_user = type('TempUser', (), {
                    'email': email,
                    'username': email,  # Use email as username for temp user
                    'first_name': first_name,
                    'last_name': last_name,
                })()
            else:
                # Use existing user object
                temp_user = existing_user
            
            # Send verification email using template system
            email_sent = send_verification_email(temp_user, otp_code=otp)
            
            if not email_sent:
                return JsonResponse({'error': 'Failed to send verification email. Please try again.'}, status=500)
            
            response_data = {'message': 'New verification code sent to your email'}
            
            # For development debugging
            if settings.DEBUG:
                response_data['debug_otp'] = otp
                
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to send email: {str(e)}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    Standards-compliant login: Only allow verified and active users to login
    Returns JWT tokens for authentication
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        user = authenticate(username=email, password=password)
        
        if user:
            if not user.is_email_verified:
                # User exists but email not verified
                return JsonResponse({
                    'error': 'Email not verified',
                    'code': 'EMAIL_NOT_VERIFIED',
                    'requires_verification': True,
                    'email': user.email,
                    'message': 'Please verify your email address before signing in.'
                }, status=403)
            
            if not user.is_active:
                return JsonResponse({
                    'error': 'Account not activated',
                    'code': 'ACCOUNT_INACTIVE',
                    'requires_verification': True,
                    'email': user.email,
                    'message': 'Your account is not active. Please verify your email address.'
                }, status=403)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Send sign-in notification email
            send_signin_notification_email(user, {'method': 'Email & Password'})
            
            return JsonResponse({
                'message': 'Login successful',
                'success': True,
                'token': access_token,
                'access': access_token,  # Add for compatibility
                'refresh': str(refresh),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                    'avatar': user.avatar,
                    'is_email_verified': user.is_email_verified,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,  # CRITICAL: Include admin flag
                    'is_superuser': user.is_superuser,  # CRITICAL: Include superuser flag
                }
            })
        else:
            # Check if user exists to provide better error message
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                return JsonResponse({
                    'error': 'Incorrect password. Please try again.',
                    'code': 'INVALID_PASSWORD'
                }, status=401)
            else:
                return JsonResponse({
                    'error': 'No account found with this email address.',
                    'code': 'ACCOUNT_NOT_FOUND'
                }, status=401)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def oauth_callback(request):
    try:
        data = json.loads(request.body)
        provider = data.get('provider')
        access_token = data.get('access_token')
        user_info = data.get('user_info')
        
        if not provider or not user_info:
            return JsonResponse({'error': 'Provider and user info are required'}, status=400)
        
        email = user_info.get('email')
        if not email:
            return JsonResponse({'error': 'Email is required from OAuth provider'}, status=400)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'avatar': user_info.get('picture'),
                'is_email_verified': True,  # OAuth providers verify emails
            }
        )
        
        # Update user info if not created
        if not created:
            if user_info.get('picture'):
                user.avatar = user_info.get('picture')
            if user_info.get('given_name'):
                user.first_name = user_info.get('given_name')
            if user_info.get('family_name'):
                user.last_name = user_info.get('family_name')
            user.save()
        
        # Get or create OAuth provider record
        provider_user_id = user_info.get('sub') or user_info.get('id')
        oauth_provider, _ = OAuthProvider.objects.get_or_create(
            user=user,
            provider=provider,
            defaults={
                'provider_user_id': provider_user_id,
                'access_token': access_token,
            }
        )
        
        # Update access token
        if access_token:
            oauth_provider.access_token = access_token
            oauth_provider.save()
        
        # Send appropriate email based on whether user was created or logged in
        if created:
            # Welcome email will be sent automatically via Django signals
            pass
        else:
            # Existing user - send sign-in notification
            from .email_automation import send_login_notification
            send_login_notification(user, {'method': f'{provider.title()} OAuth'})
        
        return JsonResponse({
            'id': str(user.id),
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}".strip(),
            'avatar': user.avatar,
            'provider': provider,
            'created': created,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def user_profile(request):
    """Get authenticated user's profile information"""
    from rest_framework_simplejwt.tokens import AccessToken
    
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token and get user
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Return user profile data
        return JsonResponse({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'avatar': user.avatar,
            'is_email_verified': user.is_email_verified,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            # Add subscription info if available
            'subscription_status': 'inactive',  # TODO: Get from subscription model
            'subscription_plan': None,
            'courses_enrolled': 0,  # TODO: Get from enrollment model
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_profile(request):
    """Update authenticated user's profile information"""
    from rest_framework_simplejwt.tokens import AccessToken
    
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token and get user
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Parse request data
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'first_name' in data:
            first_name = data['first_name'].strip()
            if not first_name:
                return JsonResponse({'error': 'First name cannot be empty'}, status=400)
            user.first_name = first_name
        
        if 'last_name' in data:
            last_name = data['last_name'].strip()
            if not last_name:
                return JsonResponse({'error': 'Last name cannot be empty'}, status=400)
            user.last_name = last_name
        
        # Save changes
        user.save()
        
        # Return updated profile
        return JsonResponse({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'avatar': user.avatar,
            'is_email_verified': user.is_email_verified,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'subscription_status': 'inactive',
            'subscription_plan': None,
            'courses_enrolled': 0,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def change_password(request):
    """Change user password"""
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth.hashers import check_password
    
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token and get user
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Parse request data
        data = json.loads(request.body)
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Validate inputs
        if not current_password or not new_password:
            return JsonResponse({'error': 'Current and new passwords are required'}, status=400)
        
        # Verify current password
        if not check_password(current_password, user.password):
            return JsonResponse({'error': 'Current password is incorrect'}, status=400)
        
        # Validate new password strength
        if len(new_password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)
        
        # Change password
        user.password = make_password(new_password)
        user.save()
        
        return JsonResponse({
            'message': 'Password changed successfully',
            'success': True
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_notifications(request):
    """Update user notification preferences"""
    from rest_framework_simplejwt.tokens import AccessToken
    from .models import UserPreferences
    
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token and get user
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Parse request data
        data = json.loads(request.body)
        
        # Get or create user preferences
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        # Update preferences
        if 'emailLogin' in data:
            preferences.email_login = data['emailLogin']
        if 'courseUpdates' in data:
            preferences.course_updates = data['courseUpdates']
        if 'subscriptionRenewal' in data:
            preferences.subscription_renewal = data['subscriptionRenewal']
        if 'promotionalEmails' in data:
            preferences.promotional_emails = data['promotionalEmails']
        if 'signalAlerts' in data:
            preferences.signal_alerts = data['signalAlerts']
        
        preferences.save()
        
        return JsonResponse({
            'message': 'Notification preferences updated successfully',
            'success': True,
            'preferences': {
                'emailLogin': preferences.email_login,
                'courseUpdates': preferences.course_updates,
                'subscriptionRenewal': preferences.subscription_renewal,
                'promotionalEmails': preferences.promotional_emails,
                'signalAlerts': preferences.signal_alerts,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_notifications(request):
    """Get user notification preferences"""
    from rest_framework_simplejwt.tokens import AccessToken
    from .models import UserPreferences
    
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token and get user
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Get or create user preferences with defaults
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        
        return JsonResponse({
            'preferences': {
                'emailLogin': preferences.email_login,
                'courseUpdates': preferences.course_updates,
                'subscriptionRenewal': preferences.subscription_renewal,
                'promotionalEmails': preferences.promotional_emails,
                'signalAlerts': preferences.signal_alerts,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Health check endpoint
def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'oxidane-auth'})

@csrf_exempt
@require_http_methods(["POST"])
def verify_email(request):
    """Verify user email with token"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)
        
        try:
            user = User.objects.get(email_verification_token=token)
            if user.verify_email(token):
                return JsonResponse({
                    'message': 'Email verified successfully',
                    'email': user.email
                })
            else:
                return JsonResponse({'error': 'Invalid or expired token'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def forgot_password(request):
    """Send password reset email"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
            token = user.generate_password_reset_token()
            
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            # Send password reset email using template system
            from .email_automation import send_password_reset_email
            send_password_reset_email(user, reset_token=token)
            
            return JsonResponse({
                'message': 'Password reset email sent successfully',
                'email': email
            })
            
        except User.DoesNotExist:
            # For security, don't reveal if email exists
            return JsonResponse({
                'message': 'If an account with this email exists, a password reset link has been sent.',
                'email': email
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    """Reset password with token"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return JsonResponse({'error': 'Token and new password are required'}, status=400)
        
        try:
            user = User.objects.get(password_reset_token=token)
            if user.reset_password(token, new_password):
                return JsonResponse({
                    'message': 'Password reset successfully',
                    'email': user.email
                })
            else:
                return JsonResponse({'error': 'Invalid or expired token'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def resend_verification(request):
    """Resend email verification"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                return JsonResponse({'error': 'Email is already verified'}, status=400)
            
            token = user.generate_email_verification_token()
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            
            # Try using EmailTemplateService
            try:
                from .email_service import EmailTemplateService
                email_service = EmailTemplateService()
                
                result = email_service.send_email(
                    template_type='email_verification',
                    recipient_email=email,
                    user=user,
                    custom_vars={'verification_url': verification_url}
                )
                
                if result and result.get('success'):
                    return JsonResponse({
                        'message': 'Verification email sent successfully',
                        'email': email
                    })
            except Exception as template_error:
                logger.warning(f"EmailTemplateService failed, using fallback: {template_error}")
            
            # Fallback to hardcoded email
            send_mail(
                subject='Verify your OxiWorld account',
                message=f'''
Welcome to OxiWorld Forex Academy!

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The OxiWorld Forex Academy Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'message': 'Verification email sent successfully',
                'email': email
            })
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_oauth_init(request):
    """
    Initiate Google OAuth flow by redirecting to Google's authorization endpoint
    """
    try:
        from django.conf import settings
        from urllib.parse import urlencode
        import secrets
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session
        request.session['oauth_state'] = state
        
        # Google OAuth parameters
        params = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Build Google OAuth URL
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        # Redirect to Google OAuth
        from django.shortcuts import redirect
        return redirect(google_auth_url)
        
    except Exception as e:
        return JsonResponse({'error': f'OAuth initiation failed: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_oauth_callback(request):
    """
    Handle Google OAuth callback and exchange authorization code for access token
    """
    try:
        from django.conf import settings
        import urllib.parse
        
        # Get authorization code and state from callback
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            return JsonResponse({'error': f'OAuth error: {error}'}, status=400)
        
        if not code:
            return JsonResponse({'error': 'Authorization code not received'}, status=400)
        
        # Verify state parameter (CSRF protection)
        stored_state = request.session.get('oauth_state')
        if not stored_state or stored_state != state:
            return JsonResponse({'error': 'Invalid state parameter'}, status=400)
        
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if token_response.status_code != 200:
            return JsonResponse({'error': f'Token exchange failed: {token_json.get("error", "Unknown error")}'}, status=400)
        
        access_token = token_json.get('access_token')
        if not access_token:
            return JsonResponse({'error': 'Access token not received'}, status=400)
        
        # Get user info from Google
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        user_response = requests.get(user_info_url)
        user_data = user_response.json()
        
        if user_response.status_code != 200:
            return JsonResponse({'error': 'Failed to get user information'}, status=400)
        
        email = user_data.get('email')
        if not email:
            return JsonResponse({'error': 'Email not provided by Google'}, status=400)
        
        # Create or get existing user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'avatar': user_data.get('picture'),
                'is_email_verified': True,  # Google verifies emails
            }
        )
        
        # Update user info if not created
        if not created:
            if user_data.get('picture'):
                user.avatar = user_data.get('picture')
            if user_data.get('given_name'):
                user.first_name = user_data.get('given_name')
            if user_data.get('family_name'):
                user.last_name = user_data.get('family_name')
            user.is_email_verified = True
            user.save()
        
        # Create or update OAuth provider record
        oauth_provider, _ = OAuthProvider.objects.get_or_create(
            user=user,
            provider='google',
            defaults={
                'provider_user_id': user_data.get('id'),
                'access_token': access_token,
                'refresh_token': token_json.get('refresh_token'),
            }
        )
        
        # Update tokens if provider already exists
        if not _:
            oauth_provider.access_token = access_token
            if token_json.get('refresh_token'):
                oauth_provider.refresh_token = token_json.get('refresh_token')
            oauth_provider.save()
        
        # Clean up session
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
        
        # Redirect to frontend with success
        frontend_base = getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')
        frontend_url = f"{frontend_base}/auth?success=true&user_id={user.id}"
        from django.shortcuts import redirect
        return redirect(frontend_url)
        
    except Exception as e:
        # Redirect to frontend with error
        error_message = urllib.parse.quote(str(e))
        frontend_base = getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')
        frontend_url = f"{frontend_base}/auth?error={error_message}"
        from django.shortcuts import redirect
        return redirect(frontend_url)


# ==================== User OTP Login System ====================

@csrf_exempt
@require_http_methods(["POST"])
def login_with_otp_request(request):
    """
    Step 1: Validate credentials and send OTP to user's email
    Does NOT return JWT token yet - requires OTP verification first
    """
    import hashlib
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if not user:
            # Check if user exists but password is wrong vs account doesn't exist
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                return JsonResponse({
                    'error': 'Invalid password',
                    'code': 'INVALID_PASSWORD'
                }, status=401)
            else:
                return JsonResponse({
                    'error': 'No account found with this email address',
                    'code': 'ACCOUNT_NOT_FOUND'
                }, status=404)
        
        # Check if email is verified
        if not user.is_email_verified:
            return JsonResponse({
                'error': 'Email not verified. Please verify your email before signing in.',
                'code': 'EMAIL_NOT_VERIFIED',
                'requires_verification': True,
                'email': user.email
            }, status=403)
        
        # Check if account is active
        if not user.is_active:
            return JsonResponse({
                'error': 'Account is not active. Please contact support.',
                'code': 'ACCOUNT_INACTIVE'
            }, status=403)
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        
        # Create session token
        session_token = hashlib.sha256(f"{user.id}{email}{timezone.now()}".encode()).hexdigest()
        
        # Store OTP in cache (expires in 10 minutes)
        cache_key = f"user_login_otp_{session_token}"
        cache.set(cache_key, {
            'user_id': str(user.id),
            'email': email,
            'otp': otp,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat()
        }, timeout=600)  # 10 minutes
        
        # Send OTP email using template system
        send_user_login_otp_email(user, otp, ip_address='request.META.get("REMOTE_ADDR", "Unknown")')
        
        return JsonResponse({
            'message': 'Verification code sent to your email',
            'session_token': session_token,
            'requires_otp': True,
            'email': email
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_login_otp(request):
    """
    Step 2: Verify OTP and issue JWT token
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    
    try:
        data = json.loads(request.body)
        session_token = data.get('session_token')
        otp = data.get('otp')
        
        if not session_token or not otp:
            return JsonResponse({'error': 'Session token and OTP are required'}, status=400)
        
        # Get OTP data from cache
        cache_key = f"user_login_otp_{session_token}"
        otp_data = cache.get(cache_key)
        
        if not otp_data:
            return JsonResponse({
                'error': 'Verification session expired or not found. Please sign in again.',
                'code': 'SESSION_EXPIRED'
            }, status=400)
        
        # Verify OTP
        if otp_data['otp'] != otp:
            return JsonResponse({
                'error': 'Invalid verification code',
                'code': 'INVALID_OTP'
            }, status=400)
        
        # Check if expired
        expires_at = timezone.datetime.fromisoformat(otp_data['expires_at'].replace('Z', '+00:00'))
        if timezone.now() > expires_at:
            cache.delete(cache_key)
            return JsonResponse({
                'error': 'Verification code has expired. Please sign in again.',
                'code': 'OTP_EXPIRED'
            }, status=400)
        
        # Get user
        user = User.objects.get(id=otp_data['user_id'])
        
        # Mark email as verified since they successfully verified OTP
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Send sign-in notification
        send_signin_notification_email(user, {'method': 'Email & Password'})
        
        # Clean up OTP session
        cache.delete(cache_key)
        
        return JsonResponse({
            'message': 'Sign-in successful',
            'token': access_token,
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'avatar': user.avatar,
                'is_email_verified': True,  # Always True after OTP verification
                'is_active': user.is_active,
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def resend_login_otp(request):
    """
    Resend OTP for login verification
    """
    try:
        data = json.loads(request.body)
        session_token = data.get('session_token')
        
        if not session_token:
            return JsonResponse({'error': 'Session token is required'}, status=400)
        
        # Get existing OTP data
        cache_key = f"user_login_otp_{session_token}"
        otp_data = cache.get(cache_key)
        
        if not otp_data:
            return JsonResponse({
                'error': 'Session expired. Please sign in again.',
                'code': 'SESSION_EXPIRED'
            }, status=400)
        
        # Generate new OTP
        otp = str(random.randint(100000, 999999))
        
        # Update cache with new OTP
        otp_data['otp'] = otp
        otp_data['expires_at'] = (timezone.now() + timedelta(minutes=10)).isoformat()
        cache.set(cache_key, otp_data, timeout=600)
        
        # Get user
        user = User.objects.get(id=otp_data['user_id'])
        
        # Send new OTP email (simplified version)
        try:
            send_mail(
                subject='🔐 OxiWorld - New Sign-In Verification Code',
                message=f"Hi {user.first_name},\n\nYour new verification code is: {otp}\n\nThis code expires in 10 minutes.\n\n© 2025 OxiWorld Forex Academy",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to resend OTP: {str(e)}")
            return JsonResponse({'error': 'Failed to send verification code'}, status=500)
        
        return JsonResponse({
            'message': 'New verification code sent to your email'
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
