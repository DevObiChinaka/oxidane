#!/usr/bin/env python3

"""
Development helper script to create an admin session token for testing
This bypasses the OTP flow for development purposes
"""

import os
import sys
import django
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
import hashlib
import json
from datetime import timedelta

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

User = get_user_model()

def create_dev_admin_token():
    """Create a development admin token for testing"""
    
    # Find or create admin user
    admin_users = User.objects.filter(is_staff=True, is_superuser=True)
    
    if not admin_users.exists():
        print("❌ No admin users found. Creating one...")
        admin_user = User.objects.create_superuser(
            username='dev_admin',
            email='admin@oxiworld.com',
            password='admin123',
            first_name='Dev',
            last_name='Admin'
        )
        print(f"✅ Created admin user: {admin_user.email}")
    else:
        admin_user = admin_users.first()
        print(f"✅ Using existing admin user: {admin_user.email}")
    
    # Generate admin session token
    admin_session_token = hashlib.sha256(f"dev_admin_{admin_user.id}_{timezone.now()}".encode()).hexdigest()
    
    # Store admin session (expires in 24 hours)
    admin_session_key = f"admin_session_{admin_session_token}"
    admin_session_data = {
        'user_id': str(admin_user.id),
        'username': admin_user.username,
        'email': admin_user.email,
        'is_admin': True,
        'login_time': timezone.now().isoformat(),
        'expires_at': (timezone.now() + timedelta(hours=24)).isoformat()
    }
    
    # Store in cache for 24 hours
    cache.set(admin_session_key, json.dumps(admin_session_data), 86400)
    
    # Verify the token was stored correctly
    stored_data = cache.get(admin_session_key)
    if stored_data:
        print(f"✅ Token stored in cache successfully")
        print(f"Cache key: {admin_session_key}")
        print(f"Stored data: {json.loads(stored_data)}")
    else:
        print(f"❌ Failed to store token in cache")
    
    print(f"\n🔑 Development Admin Token Generated:")
    print(f"Token: {admin_session_token}")
    print(f"Expires: {(timezone.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📋 To use this token in frontend development:")
    print(f"1. Add to localStorage: localStorage.setItem('admin_token', '{admin_session_token}')")
    print(f"2. Or set in AdminAPIClient: AdminAPIClient.setAuthToken('{admin_session_token}')")
    
    print(f"\n🧪 Test with curl:")
    print(f'curl -H "Authorization: Bearer {admin_session_token}" http://localhost:8000/api/admin/subscriptions/')
    
    return admin_session_token

if __name__ == "__main__":
    print("🚀 Creating Development Admin Token")
    print("=" * 50)
    
    try:
        token = create_dev_admin_token()
        print("\n✅ Development token created successfully!")
    except Exception as e:
        print(f"\n❌ Error creating token: {str(e)}")
        sys.exit(1)