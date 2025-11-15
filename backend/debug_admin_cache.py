"""
Debug Admin Authentication Cache
Run this to check if admin sessions are being stored correctly
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache
import json

print("=" * 60)
print("🔍 ADMIN SESSION CACHE DEBUGGER")
print("=" * 60)

# Try to inspect cache
try:
    # Check if Redis is being used
    from django.conf import settings
    print(f"\n📋 Cache Backend: {settings.CACHES['default']['BACKEND']}")
    print(f"📋 Cache Location: {settings.CACHES.get('default', {}).get('LOCATION', 'N/A')}")
    
    # Try Redis inspection
    try:
        import redis
        from urllib.parse import urlparse
        
        cache_location = settings.CACHES['default'].get('LOCATION', 'redis://127.0.0.1:6379/1')
        print(f"📋 Redis URL: {cache_location[:30]}...")
        
        # Parse Redis URL properly
        parsed = urlparse(cache_location)
        
        # Connect using URL (handles auth automatically)
        r = redis.from_url(cache_location, decode_responses=False)
        
        # Get all admin session keys
        admin_keys = r.keys('*admin_session*')
        admin_otp_keys = r.keys('*admin_otp*')
        
        print(f"\n🔑 Found {len(admin_keys)} admin session keys")
        print(f"🔑 Found {len(admin_otp_keys)} admin OTP keys")
        
        if admin_keys:
            print("\n" + "=" * 60)
            print("ADMIN SESSIONS:")
            print("=" * 60)
            for key in admin_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                print(f"\n📌 Key: {key_str}")
                
                # Get value from Django cache
                token = key_str.replace('admin_session_', '').replace(':1:', '')
                cached_value = cache.get(token)
                
                if cached_value:
                    try:
                        session_data = json.loads(cached_value) if isinstance(cached_value, str) else cached_value
                        print(f"   User: {session_data.get('username', 'N/A')}")
                        print(f"   Email: {session_data.get('email', 'N/A')}")
                        print(f"   Login Time: {session_data.get('login_time', 'N/A')}")
                        print(f"   Expires At: {session_data.get('expires_at', 'N/A')}")
                    except:
                        print(f"   Raw Value: {str(cached_value)[:200]}")
                else:
                    print(f"   ⚠️ Could not retrieve value from cache")
        else:
            print("\n⚠️  No active admin sessions found!")
            print("   This might mean:")
            print("   1. No admin has logged in recently")
            print("   2. Sessions have expired (24 hour limit)")
            print("   3. Cache was cleared/restarted")
            
        if admin_otp_keys:
            print("\n" + "=" * 60)
            print("PENDING OTP VERIFICATIONS:")
            print("=" * 60)
            for key in admin_otp_keys[:5]:  # Show first 5 only
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                print(f"\n📌 Key: {key_str}")
                
                # Get OTP data
                otp_token = key_str.replace('admin_otp_', '').replace(':1:', '')
                otp_data = cache.get(otp_token)
                if otp_data:
                    try:
                        otp_info = json.loads(otp_data) if isinstance(otp_data, str) else otp_data
                        print(f"   Username: {otp_info.get('username', 'N/A')}")
                        print(f"   Email: {otp_info.get('email', 'N/A')}")
                        print(f"   Expires At: {otp_info.get('expires_at', 'N/A')}")
                    except:
                        print(f"   Raw Value: {str(otp_data)[:100]}")
                        
    except ImportError:
        print("\n⚠️  Redis module not found, using default cache")
        print("   Cannot inspect cache keys directly")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🔧 TROUBLESHOOTING TIPS:")
print("=" * 60)
print("""
1. If no sessions found:
   - Login to admin panel
   - Complete OTP verification
   - Run this script again

2. If sessions exist but page shows 401:
   - Check browser localStorage: localStorage.getItem('access_token')
   - Compare token with cache keys above
   - Tokens should match exactly

3. If using wrong token:
   - Check admin login response in Network tab
   - Look for 'admin_session_token' field
   - Verify frontend saves it as 'access_token'

4. If cache keeps clearing:
   - Check Redis is running: redis-cli ping
   - Check Django cache config in settings.py
   - Verify cache timeout (should be 86400 = 24 hours)
""")

print("\n" + "=" * 60)
