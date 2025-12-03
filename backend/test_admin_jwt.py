#!/usr/bin/env python
"""
Test Admin JWT Token Generation and Validation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
import json

User = get_user_model()

def test_admin_jwt():
    print("=" * 60)
    print("ADMIN JWT TOKEN TEST")
    print("=" * 60)
    
    # Get admin user
    admin = User.objects.filter(is_staff=True).first()
    if not admin:
        print("❌ No admin user found!")
        return
    
    print(f"\n✅ Admin User Found:")
    print(f"   Username: {admin.username}")
    print(f"   Email: {admin.email}")
    print(f"   is_staff: {admin.is_staff}")
    print(f"   is_superuser: {admin.is_superuser}")
    print(f"   is_active: {admin.is_active}")
    
    # Generate JWT tokens
    print(f"\n🔑 Generating JWT Tokens...")
    refresh = RefreshToken.for_user(admin)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print(f"   Access Token (first 80 chars): {access_token[:80]}...")
    print(f"   Refresh Token (first 80 chars): {refresh_token[:80]}...")
    
    # Decode and show payload
    print(f"\n📋 Access Token Payload:")
    payload = refresh.access_token.payload
    for key, value in payload.items():
        print(f"   {key}: {value}")
    
    # Validate the token
    print(f"\n✓ Validating Access Token...")
    try:
        validated_token = AccessToken(access_token)
        print(f"   ✅ Token is valid!")
        print(f"   User ID from token: {validated_token['user_id']}")
        
        # Get user from token
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        
        # Simulate request with this token
        print(f"\n🔍 Simulating API Request with Token...")
        try:
            validated_token_obj = jwt_auth.get_validated_token(access_token)
            user = jwt_auth.get_user(validated_token_obj)
            print(f"   ✅ Token authentication successful!")
            print(f"   Authenticated user: {user.username}")
            print(f"   Is staff: {user.is_staff}")
            print(f"   Is superuser: {user.is_superuser}")
        except Exception as e:
            print(f"   ❌ Token validation failed: {str(e)}")
            
    except TokenError as e:
        print(f"   ❌ Token validation error: {str(e)}")
    
    # Test the user data format that would be returned
    print(f"\n📦 User Data Format (as returned by admin_verify_otp_jwt):")
    user_data = {
        'id': str(admin.id),
        'email': admin.email,
        'username': admin.username,
        'first_name': admin.first_name,
        'last_name': admin.last_name,
        'is_staff': admin.is_staff,
        'is_superuser': admin.is_superuser,
        'is_active': admin.is_active,
    }
    print(json.dumps(user_data, indent=2))
    
    # Check permissions
    print(f"\n🔐 Testing IsAdmin Permission...")
    from users.permissions import IsAdmin
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    mock_request = MockRequest(admin)
    is_admin_perm = IsAdmin()
    has_permission = is_admin_perm.has_permission(mock_request, None)
    print(f"   IsAdmin permission check: {'✅ PASSED' if has_permission else '❌ FAILED'}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_admin_jwt()
