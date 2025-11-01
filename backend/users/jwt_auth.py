"""Custom JWT token serializer with user information"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user information in the response.
    This eliminates the need for a separate user info endpoint.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add comprehensive user data to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'is_active': self.user.is_active,
            'avatar': self.user.avatar if hasattr(self.user, 'avatar') else None,
        }
        
        # Send admin login notification if user is staff
        if self.user.is_staff:
            try:
                self._send_admin_login_notification()
            except Exception as e:
                # Don't fail login if notification fails
                logger.error(f"Failed to send admin login notification: {str(e)}")
        
        return data
    
    def _send_admin_login_notification(self):
        """Send email notification for admin login"""
        from .email_service import EmailTemplateService
        
        # Get request metadata
        request = self.context.get('request')
        if not request:
            return
        
        # Extract login information
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        device = self._parse_user_agent(user_agent)
        login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        # Get approximate location (can be enhanced with IP geolocation API)
        location = self._get_location_from_ip(ip_address)
        
        # Send email using template service
        email_service = EmailTemplateService()
        email_service.send_email(
            template_type='signin_notification',
            recipient_email=self.user.email,
            user=self.user,
            custom_vars={
                'user_name': self.user.get_full_name() or self.user.email.split('@')[0],
                'login_time': login_time,
                'ip_address': ip_address,
                'location': location,
                'device': device,
            }
        )
        
        logger.info(f"Admin login notification sent to {self.user.email}")
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip
    
    def _parse_user_agent(self, user_agent):
        """Parse user agent string to get device/browser info"""
        if not user_agent or user_agent == 'Unknown':
            return 'Unknown Device'
        
        # Simple parsing - can be enhanced with user-agents library
        if 'Mobile' in user_agent:
            device_type = 'Mobile'
        elif 'Tablet' in user_agent:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
        
        # Extract browser
        if 'Chrome' in user_agent and 'Edg' not in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'Safari'
        elif 'Edg' in user_agent:
            browser = 'Edge'
        else:
            browser = 'Unknown Browser'
        
        # Extract OS
        if 'Windows' in user_agent:
            os = 'Windows'
        elif 'Mac OS' in user_agent or 'Macintosh' in user_agent:
            os = 'macOS'
        elif 'Linux' in user_agent:
            os = 'Linux'
        elif 'Android' in user_agent:
            os = 'Android'
        elif 'iOS' in user_agent or 'iPhone' in user_agent or 'iPad' in user_agent:
            os = 'iOS'
        else:
            os = 'Unknown OS'
        
        return f"{browser} on {os} ({device_type})"
    
    def _get_location_from_ip(self, ip_address):
        """Get approximate location from IP address"""
        # Basic implementation - returns "Unknown Location"
        # Can be enhanced with IP geolocation API like ipapi.co or ip-api.com
        
        if ip_address in ['127.0.0.1', 'localhost', 'Unknown']:
            return 'Local Network'
        
        # For now, return generic message
        # TODO: Implement IP geolocation API integration
        return 'Unknown Location'


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view using our serializer"""
    serializer_class = CustomTokenObtainPairSerializer
