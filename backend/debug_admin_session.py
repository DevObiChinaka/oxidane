#!/usr/bin/env python3

"""
Debug admin token validation process
"""

import os
import sys
import django
from django.core.cache import cache
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

def debug_admin_session():
    """Debug admin session storage and retrieval"""
    
    token = "655ec11f736ae64eae39dcd7d1fc3f6bf9fe56af05e560631250aaf12b776b57"
    cache_key = f"admin_session_{token}"
    
    print("🔍 Debugging Admin Session")
    print("=" * 50)
    print(f"Token: {token}")
    print(f"Cache Key: {cache_key}")
    
    # Check if session exists in cache
    session_data_json = cache.get(cache_key)
    
    if session_data_json:
        print("✅ Session found in cache!")
        session_data = json.loads(session_data_json)
        print(f"Session Data: {session_data}")
        
        # Check expiration
        from django.utils import timezone
        expires_at = timezone.datetime.fromisoformat(session_data['expires_at'])
        current_time = timezone.now()
        
        print(f"Current Time: {current_time}")
        print(f"Expires At: {expires_at}")
        
        if current_time > expires_at:
            print("❌ Session has expired!")
        else:
            print("✅ Session is still valid!")
            time_remaining = expires_at - current_time
            print(f"Time remaining: {time_remaining}")
            
    else:
        print("❌ Session not found in cache")
        
        # List all cache keys to see what's there
        print("\nListing cache keys containing 'admin_session':")
        # Note: This depends on cache backend, for development we might see Redis keys
        try:
            # Try to get all keys (this works with Redis)
            from django.core.cache.backends.redis import RedisCache
            if isinstance(cache, RedisCache):
                keys = cache._cache.get_client().keys("*admin_session*")
                print(f"Found keys: {keys}")
            else:
                print("Cache backend doesn't support key listing")
        except:
            print("Could not list cache keys")

if __name__ == "__main__":
    debug_admin_session()