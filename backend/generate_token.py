"""
Quick script to test if we can get a JWT token for chiderachinaka06
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print("=" * 80)
print("🔑 JWT TOKEN GENERATOR FOR chiderachinaka06")
print("=" * 80)

try:
    user = User.objects.get(email='chiderachinaka06@gmail.com')
    print(f"\n✅ User found: {user.email}")
    print(f"   Username: {user.username}")
    print(f"   Is Active: {user.is_active}")
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print(f"\n🔑 JWT TOKENS:")
    print(f"\nAccess Token (use this in Authorization: Bearer <token>):")
    print(f"{access_token}")
    print(f"\nRefresh Token:")
    print(f"{refresh_token}")
    
    print(f"\n📋 To test in browser console:")
    print(f"localStorage.setItem('access_token', '{access_token}');")
    print(f"localStorage.setItem('refresh_token', '{refresh_token}');")
    
    print(f"\n🌐 Test API call:")
    print(f"curl -H 'Authorization: Bearer {access_token}' http://localhost:8000/api/subscriptions/my-subscriptions/")

except User.DoesNotExist:
    print("\n❌ User not found!")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
