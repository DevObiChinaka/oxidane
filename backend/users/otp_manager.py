"""
Secure OTP and Password Reset Manager
Uses industry-standard practices for security and performance
"""
import secrets
import string
from datetime import timedelta, datetime
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from typing import Optional, Tuple
from .email_service import EmailTemplateService


class OTPManager:
    """Manages OTP generation, validation, and cleanup"""
    
    # Configuration
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
    MAX_REQUESTS_PER_WINDOW = 3
    
    # Cache key prefixes
    OTP_PREFIX = "otp:"
    ATTEMPTS_PREFIX = "otp_attempts:"
    RATE_LIMIT_PREFIX = "otp_rate_limit:"
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a cryptographically secure 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(OTPManager.OTP_LENGTH))
    
    @staticmethod
    def _get_cache_key(identifier: str, prefix: str) -> str:
        """Generate cache key for given identifier"""
        return f"{prefix}{identifier}"
    
    @classmethod
    def check_rate_limit(cls, identifier: str) -> Tuple[bool, int]:
        """
        Check if identifier has exceeded rate limit
        Returns: (is_allowed, remaining_time_in_seconds)
        """
        rate_key = cls._get_cache_key(identifier, cls.RATE_LIMIT_PREFIX)
        request_count = cache.get(rate_key, 0)
        
        if request_count >= cls.MAX_REQUESTS_PER_WINDOW:
            ttl = cache.ttl(rate_key)
            return False, ttl if ttl > 0 else cls.RATE_LIMIT_WINDOW
        
        return True, 0
    
    @classmethod
    def increment_rate_limit(cls, identifier: str):
        """Increment rate limit counter"""
        rate_key = cls._get_cache_key(identifier, cls.RATE_LIMIT_PREFIX)
        request_count = cache.get(rate_key, 0)
        
        if request_count == 0:
            # First request in window
            cache.set(rate_key, 1, cls.RATE_LIMIT_WINDOW)
        else:
            cache.incr(rate_key)
    
    @classmethod
    def send_otp(cls, identifier: str, email: str, purpose: str = "login") -> Tuple[bool, str]:
        """
        Generate and send OTP via email
        
        Args:
            identifier: Unique identifier (email or user_id)
            email: Email address to send OTP to
            purpose: Purpose of OTP (login, password_reset, 2fa)
            
        Returns:
            (success, message)
        """
        # Check rate limit
        is_allowed, wait_time = cls.check_rate_limit(identifier)
        if not is_allowed:
            return False, f"Too many OTP requests. Please wait {wait_time} seconds."
        
        # Generate OTP
        otp = cls.generate_otp()
        
        # Store OTP in cache
        otp_key = cls._get_cache_key(identifier, cls.OTP_PREFIX)
        attempts_key = cls._get_cache_key(identifier, cls.ATTEMPTS_PREFIX)
        
        print(f"[OTP_MANAGER_SEND] Identifier: {identifier}")
        print(f"[OTP_MANAGER_SEND] OTP Key: {otp_key}")
        print(f"[OTP_MANAGER_SEND] Generated OTP: {otp}")
        print(f"[OTP_MANAGER_SEND] Expiry: {cls.OTP_EXPIRY_MINUTES} minutes")
        
        cache.set(otp_key, otp, cls.OTP_EXPIRY_MINUTES * 60)
        cache.set(attempts_key, 0, cls.OTP_EXPIRY_MINUTES * 60)
        
        # Verify it was stored
        stored_value = cache.get(otp_key)
        print(f"[OTP_MANAGER_SEND] Stored value verification: {stored_value}")
        print(f"[OTP_MANAGER_SEND] Storage successful: {stored_value == otp}")
        
        # Increment rate limit
        cls.increment_rate_limit(identifier)
        
        # Send email
        try:
            subject_map = {
                "login": "Your Login OTP",
                "password_reset": "Password Reset OTP",
                "2fa": "Two-Factor Authentication OTP",
            }
            
            subject = subject_map.get(purpose, "Your OTP Code")
            
            message = f"""
            Your OTP code is: {otp}
            
            This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.
            
            If you didn't request this code, please ignore this email.
            
            For security reasons, never share this code with anyone.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            print(f"[OTP_MANAGER_SEND] Email sent successfully to {email}")
            return True, "OTP sent successfully"
        
        except Exception as e:
            # OTP is already stored in cache, so still return success
            # Email failure should not block OTP verification
            print(f"[OTP_MANAGER_SEND] Email send failed: {str(e)}")
            print(f"[OTP_MANAGER_SEND] But OTP is stored in cache and ready for verification")
            return True, f"OTP generated (email delivery issue: {str(e)})"
    
    @classmethod
    def verify_otp(cls, identifier: str, otp: str, purpose: str = "login") -> Tuple[bool, str]:
        """
        Verify OTP for given identifier
        
        Args:
            identifier: Unique identifier (user_id as string)
            otp: OTP code to verify
            purpose: Purpose of OTP (for logging/tracking)
        
        Returns:
            (is_valid, message)
        """
        otp_key = cls._get_cache_key(identifier, cls.OTP_PREFIX)
        attempts_key = cls._get_cache_key(identifier, cls.ATTEMPTS_PREFIX)
        
        print(f"[OTP_MANAGER_VERIFY] Identifier: {identifier}")
        print(f"[OTP_MANAGER_VERIFY] OTP Key: {otp_key}")
        print(f"[OTP_MANAGER_VERIFY] Received OTP: {otp}")
        
        # Check if OTP exists
        stored_otp = cache.get(otp_key)
        print(f"[OTP_MANAGER_VERIFY] Stored OTP: {stored_otp}")
        print(f"[OTP_MANAGER_VERIFY] OTP exists: {stored_otp is not None}")
        if not stored_otp:
            return False, "OTP has expired or is invalid"
        
        # Check attempts
        attempts = cache.get(attempts_key, 0)
        if attempts >= cls.MAX_ATTEMPTS:
            # Clear OTP after max attempts
            cache.delete(otp_key)
            cache.delete(attempts_key)
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
        
        # Verify OTP
        if otp == stored_otp:
            # Clear OTP after successful verification
            cache.delete(otp_key)
            cache.delete(attempts_key)
            return True, "OTP verified successfully"
        
        # Increment attempts
        cache.incr(attempts_key)
        remaining_attempts = cls.MAX_ATTEMPTS - (attempts + 1)
        
        return False, f"Invalid OTP. {remaining_attempts} attempts remaining."
    
    @classmethod
    def clear_otp(cls, identifier: str):
        """Clear OTP and attempts for identifier"""
        otp_key = cls._get_cache_key(identifier, cls.OTP_PREFIX)
        attempts_key = cls._get_cache_key(identifier, cls.ATTEMPTS_PREFIX)
        cache.delete(otp_key)
        cache.delete(attempts_key)
    
    @classmethod
    def generate_and_send_otp(cls, user_id: int, email: str, user_name: str, purpose: str = "login") -> Tuple[bool, str]:
        """
        Generate and send OTP to user's email using EmailTemplateService
        
        Args:
            user_id: User ID as identifier
            email: Email address to send OTP to
            user_name: User's name for email personalization
            purpose: Purpose of OTP (login, password_reset, 2fa)
            
        Returns:
            (success, message)
        """
        from .email_service import EmailTemplateService
        from .models import User
        
        identifier = str(user_id)
        
        # Check rate limit
        is_allowed, wait_time = cls.check_rate_limit(identifier)
        if not is_allowed:
            minutes = wait_time // 60
            seconds = wait_time % 60
            return False, f"Too many OTP requests. Please wait {minutes}m {seconds}s."
        
        # Generate OTP
        otp = cls.generate_otp()
        
        # Store OTP in cache
        otp_key = cls._get_cache_key(identifier, cls.OTP_PREFIX)
        attempts_key = cls._get_cache_key(identifier, cls.ATTEMPTS_PREFIX)
        
        cache.set(otp_key, otp, cls.OTP_EXPIRY_MINUTES * 60)
        cache.set(attempts_key, 0, cls.OTP_EXPIRY_MINUTES * 60)
        
        # Increment rate limit
        cls.increment_rate_limit(identifier)
        
        # Send email using EmailTemplateService
        try:
            user = User.objects.get(id=user_id)
            email_service = EmailTemplateService()
            
            if purpose == "password_reset":
                # Use password reset template
                result = email_service.send_email(
                    template_type='password_reset',
                    recipient_email=email,
                    user=user,
                    custom_vars={'otp_code': otp}
                )
                
                # Handle both dict and boolean return types
                if isinstance(result, dict):
                    if result.get('success'):
                        return True, "OTP sent successfully"
                    else:
                        return False, result.get('error', "Failed to send OTP email")
                elif result:  # Boolean True
                    return True, "OTP sent successfully"
                else:
                    return False, "Failed to send OTP email"
            else:
                # For login OTP, use simple email (can create template later if needed)
                return cls._send_simple_otp_email(email, otp, user_name, purpose, user)
                
        except User.DoesNotExist:
            # If user not found, still send email without user object
            return cls._send_simple_otp_email(email, otp, user_name, purpose, None)
        except Exception as e:
            return False, f"Failed to send OTP: {str(e)}"
    
    @classmethod
    def _send_simple_otp_email(cls, email: str, otp: str, user_name: str, purpose: str, user=None) -> Tuple[bool, str]:
        """Send OTP email using EmailTemplateService or fallback to simple email"""
        try:
            # Try using EmailTemplateService first
            email_service = EmailTemplateService()
            
            # Prepare context
            context = {
                'otp': otp,
                'otp_code': otp,
                'expiry_minutes': cls.OTP_EXPIRY_MINUTES,
            }
            
            if purpose == "password_reset":
                # Use password_reset template
                from django.conf import settings as django_settings
                frontend_url = getattr(django_settings, 'FRONTEND_URL', 'http://localhost:3000')
                reset_url = f"{frontend_url}/reset-password?email={email}"
                context['reset_url'] = reset_url
                
                result = email_service.send_email(
                    template_type='password_reset',
                    recipient_email=email,
                    user=user,
                    custom_vars=context
                )
                
                # Handle both dict and boolean return types
                if isinstance(result, dict):
                    if result.get('success'):
                        return True, "Password reset email sent successfully"
                elif result:  # Boolean True
                    return True, "Password reset email sent successfully"
            
            # Fallback to simple email if template doesn't exist or fails
            if purpose == "password_reset":
                subject = "Password Reset Code - OxiWorld Forex Academy"
                message = f"""
Hi {user_name},

You have requested to reset your password. Your password reset code is:

{otp}

This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.

If you didn't request a password reset, please ignore this email and ensure your account is secure.

For security reasons, never share this code with anyone.

Best regards,
OxiWorld Forex Academy Team
                """
            else:
                subject = "Your Login OTP - OxiWorld Forex Academy"
                message = f"""
Hi {user_name},

Your login verification code is:

{otp}

This code will expire in {cls.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

For security reasons, never share this code with anyone.

Best regards,
OxiWorld Forex Academy Team
                """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return True, "OTP sent successfully"
        
        except Exception as e:
            return False, f"Failed to send OTP: {str(e)}"


class PasswordResetManager:
    """Manages password reset tokens"""
    
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY_HOURS = 1
    RATE_LIMIT_WINDOW = 3600  # 1 hour
    MAX_REQUESTS_PER_WINDOW = 3
    
    RESET_TOKEN_PREFIX = "pwd_reset:"
    RESET_RATE_LIMIT_PREFIX = "pwd_reset_rate:"
    
    @staticmethod
    def generate_token() -> str:
        """Generate cryptographically secure reset token"""
        return secrets.token_urlsafe(PasswordResetManager.TOKEN_LENGTH)
    
    @classmethod
    def check_rate_limit(cls, email: str) -> Tuple[bool, int]:
        """Check password reset rate limit"""
        rate_key = f"{cls.RESET_RATE_LIMIT_PREFIX}{email}"
        request_count = cache.get(rate_key, 0)
        
        if request_count >= cls.MAX_REQUESTS_PER_WINDOW:
            ttl = cache.ttl(rate_key)
            return False, ttl if ttl > 0 else cls.RATE_LIMIT_WINDOW
        
        return True, 0
    
    @classmethod
    def create_reset_token(cls, user_id: int, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Create password reset token
        
        Returns:
            (success, message, token)
        """
        # Check rate limit
        is_allowed, wait_time = cls.check_rate_limit(email)
        if not is_allowed:
            wait_minutes = wait_time // 60
            return False, f"Too many password reset requests. Please wait {wait_minutes} minutes.", None
        
        # Generate token
        token = cls.generate_token()
        
        # Store token with user_id
        token_key = f"{cls.RESET_TOKEN_PREFIX}{token}"
        cache.set(token_key, user_id, cls.TOKEN_EXPIRY_HOURS * 3600)
        
        # Increment rate limit
        rate_key = f"{cls.RESET_RATE_LIMIT_PREFIX}{email}"
        current_count = cache.get(rate_key, 0)
        if current_count == 0:
            cache.set(rate_key, 1, cls.RATE_LIMIT_WINDOW)
        else:
            cache.incr(rate_key)
        
        return True, "Reset token created", token
    
    @classmethod
    def verify_reset_token(cls, token: str) -> Tuple[bool, Optional[int]]:
        """
        Verify reset token and return user_id
        
        Returns:
            (is_valid, user_id)
        """
        token_key = f"{cls.RESET_TOKEN_PREFIX}{token}"
        user_id = cache.get(token_key)
        
        if user_id:
            return True, user_id
        
        return False, None
    
    @classmethod
    def consume_reset_token(cls, token: str) -> Tuple[bool, Optional[int]]:
        """
        Verify and consume (delete) reset token
        
        Returns:
            (is_valid, user_id)
        """
        token_key = f"{cls.RESET_TOKEN_PREFIX}{token}"
        user_id = cache.get(token_key)
        
        if user_id:
            cache.delete(token_key)
            return True, user_id
        
        return False, None
    
    @classmethod
    def send_reset_email(cls, email: str, token: str, user_name: str = "") -> Tuple[bool, str]:
        """Send password reset email with token"""
        try:
            # Build reset URL
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            reset_url = f"{frontend_url}/reset-password?token={token}"
            
            subject = "Password Reset Request"
            message = f"""
            Hello{' ' + user_name if user_name else ''},
            
            You requested to reset your password for OxiWorld Forex Academy.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in {cls.TOKEN_EXPIRY_HOURS} hour(s).
            
            If you didn't request this, please ignore this email. Your password will remain unchanged.
            
            For security reasons, never share this link with anyone.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return True, "Password reset email sent"
        
        except Exception as e:
            return False, f"Failed to send reset email: {str(e)}"
