#!/usr/bin/env python3
"""
Test script to verify subscription API authentication
"""

import os
import sys
import django
import requests

# Setup Django environment
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache
from users.models import User

def test_subscription_api():
    # Create a test admin token (same as we created before)
    admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
    
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Use the same token we created earlier
    test_token = "655ec11f736ae64eae39dcd7d1fc3f6bf9fe56af05e560631250aaf12b776b57"
    
    # Set it in cache (simulating proper authentication)
    cache.set(f"admin_session:{test_token}", {
        'user_id': str(admin_user.id),
        'username': admin_user.username,
        'is_admin': True
    }, timeout=86400)  # 24 hours
    
    print(f"✅ Admin token set in cache: {test_token[:20]}...")
    
    # Test the API endpoint
    url = "http://127.0.0.1:8000/api/admin/subscriptions/"
    headers = {
        'Authorization': f'Bearer {test_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 Testing API endpoint: {url}")
    print(f"📋 Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"📄 Response body: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is Django server running on 127.0.0.1:8000?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Subscription API Authentication...")
    success = test_subscription_api()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("💡 The authentication pattern is working correctly.")
        print("🔧 Frontend should now be able to call the API with this token.")
    else:
        print("\n❌ Test failed!")
        print("🔧 Check Django server status and endpoint implementation.")