"""Custom authentication class for admin cache-based sessions"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from django.contrib.auth import get_user_model
import json
from django.utils import timezone

User = get_user_model()

class AdminSessionAuthentication(BaseAuthentication):
    """
    Authentication class for admin cache-based sessions.
    Checks for admin_session tokens in cache before falling back to JWT.
    """
    
    def authenticate(self, request):
        # Get the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None  # Let other authentication classes try
        
        # Extract token
        token = auth_header.replace('Bearer ', '')
        
        # Check if this is an admin session token
        cache_key = f"admin_session_{token}"
        session_data_json = cache.get(cache_key)
        
        if not session_data_json:
            return None  # Not an admin token, let JWT authentication try
        
        try:
            session_data = json.loads(session_data_json)
            
            # Check if session has expired
            expires_at = timezone.datetime.fromisoformat(session_data['expires_at'])
            if timezone.now() > expires_at:
                cache.delete(cache_key)  # Clean up expired session
                return None
            
            # Get the user
            user = User.objects.get(id=session_data['user_id'])
            
            # Return user and token (DRF expects this format)
            return (user, token)
            
        except (json.JSONDecodeError, User.DoesNotExist, KeyError) as e:
            return None  # Invalid session data, let other auth try
    
    def authenticate_header(self, request):
        return 'Bearer'
