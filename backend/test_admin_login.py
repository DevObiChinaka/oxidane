"""
Test admin login flow
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

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

User = get_user_model()

print("=" * 80)
print("🔐 Testing Admin Login Flow")
print("=" * 80)

# Find an admin user
admin_users = User.objects.filter(is_staff=True, is_superuser=True)

if not admin_users.exists():
    print("\n❌ No admin users found!")
    print("\nCreating a test admin user...")
    
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@oxiworld.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print(f"✅ Created admin user: {admin.email}")
else:
    admin = admin_users.first()
    print(f"\n✅ Found admin user: {admin.email}")

print(f"   Username: {admin.username}")
print(f"   Is Staff: {admin.is_staff}")
print(f"   Is Superuser: {admin.is_superuser}")

# Test login
client = APIClient()

print("\n📝 Step 1: Login Request")
print("-" * 80)

response = client.post('/api/admin-auth/login/', {
    'username': admin.username,
    'password': 'admin123'  # You might need to adjust this
}, format='json')

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    data = response.json()
    if data.get('success'):
        session_token = data.get('session_token')
        print(f"\n✅ Login successful!")
        print(f"Session Token: {session_token[:50]}...")
        
        # Test OTP verification (if you have the OTP)
        print("\n📝 Step 2: Verify OTP")
        print("-" * 80)
        print("⚠️  Check your email/console for the OTP code")
        print("   Then verify using:")
        print(f"   POST /api/admin-auth/verify-otp/")
        print(f"   {{ 'session_token': '{session_token}', 'otp': 'YOUR_OTP' }}")
        
        # Try to check session without verifying (should fail)
        print("\n📝 Step 3: Check Session (without verification - should fail)")
        print("-" * 80)
        
        check_response = client.get('/api/admin-auth/check-session/', 
                                    HTTP_AUTHORIZATION=f'Bearer {session_token}')
        print(f"Status Code: {check_response.status_code}")
        print(f"Response: {check_response.json()}")
        
    else:
        print(f"\n❌ Login failed: {data.get('error')}")
else:
    print(f"\n❌ Login request failed")

print("\n" + "=" * 80)
print("💡 To complete login:")
print("   1. Get the OTP from email/console")
print("   2. POST to /api/admin-auth/verify-otp/ with session_token and otp")
print("   3. Use the returned admin_token for authenticated requests")
print("=" * 80)
