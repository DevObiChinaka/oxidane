"""
Complete admin login with OTP
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

# Override ALLOWED_HOSTS for testing
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from rest_framework.test import APIClient

print("=" * 80)
print("🔐 Completing Admin Login with OTP")
print("=" * 80)

client = APIClient()

# Step 1: Login
print("\n📝 Step 1: Login")
response = client.post('/api/admin-auth/login/', {
    'username': 'admin',
    'password': 'admin123'
}, format='json')

if response.status_code != 200:
    print(f"❌ Login failed: {response.json()}")
    exit(1)

data = response.json()
session_token = data['session_token']
otp = data.get('debug_otp')

print(f"✅ Login successful!")
print(f"Session Token: {session_token[:50]}...")
print(f"OTP: {otp}")

# Step 2: Verify OTP
print("\n📝 Step 2: Verify OTP")
verify_response = client.post('/api/admin-auth/verify-otp/', {
    'session_token': session_token,
    'otp': otp
}, format='json')

print(f"Status Code: {verify_response.status_code}")
print(f"Response: {verify_response.json()}")

if verify_response.status_code == 200:
    verify_data = verify_response.json()
    admin_token = verify_data.get('admin_token')
    
    print(f"\n✅ OTP verification successful!")
    print(f"Admin Token: {admin_token[:50]}...")
    
    # Step 3: Check session
    print("\n📝 Step 3: Check Session")
    check_response = client.get('/api/admin-auth/check-session/',
                                HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    
    print(f"Status Code: {check_response.status_code}")
    print(f"Response: {check_response.json()}")
    
    if check_response.status_code == 200:
        print(f"\n✅ Session is valid!")
        
        # Step 4: Try accessing protected endpoint
        print("\n📝 Step 4: Test Dashboard Metrics API")
        metrics_response = client.get('/api/admin/dashboard/metrics/',
                                      HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        print(f"Status Code: {metrics_response.status_code}")
        if metrics_response.status_code == 200:
            print(f"✅ Dashboard metrics accessible!")
            print(f"Response: {metrics_response.json()}")
        else:
            print(f"❌ Dashboard metrics failed:")
            print(f"Response: {metrics_response.content.decode('utf-8')[:200]}")
    else:
        print(f"\n❌ Session check failed")
else:
    print(f"\n❌ OTP verification failed")

print("\n" + "=" * 80)
print("🔑 For browser use:")
print(f"localStorage.setItem('admin_token', '{admin_token}');")
print(f"localStorage.setItem('admin_user', JSON.stringify({{username: 'admin', email: 'derachinaka@gmail.com'}}));")
print("=" * 80)
