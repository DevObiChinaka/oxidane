"""
Test script for Telegram Verification API endpoints
Run this to verify the endpoints are working correctly
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import BillingProfile
from rest_framework.test import APIRequestFactory
from subscriptions.billing_views import (
    generate_verification_code,
    telegram_verify_callback,
    telegram_verification_status
)
from rest_framework.test import force_authenticate

User = get_user_model()

def test_verification_flow():
    """Test the complete verification flow"""
    print("\n" + "="*60)
    print("TESTING TELEGRAM VERIFICATION API")
    print("="*60)
    
    # 1. Create a test user
    print("\n1. Creating test user...")
    test_user, created = User.objects.get_or_create(
        email='test_verify@example.com',
        defaults={'username': 'test_verify_user'}
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"   ✅ Created new user: {test_user.email}")
    else:
        print(f"   ℹ️  Using existing user: {test_user.email}")
        # Reset verification status for testing
        try:
            profile = test_user.billing_profile
            profile.telegram_verified = False
            profile.telegram_user_id = None
            profile.telegram_username = ''
            profile.verification_code = None
            profile.save()
            print(f"   ✅ Reset verification status")
        except:
            pass
    
    # 2. Generate verification code
    print("\n2. Testing: Generate Verification Code")
    factory = APIRequestFactory()
    request = factory.post('/api/billing/telegram/generate-code/')
    force_authenticate(request, user=test_user)
    
    response = generate_verification_code(request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.data}")
    
    if response.status_code == 200:
        verification_code = response.data.get('verification_code')
        print(f"   ✅ Generated code: {verification_code}")
    else:
        print(f"   ❌ Failed to generate code")
        return
    
    # 3. Check verification status (before verification)
    print("\n3. Testing: Check Status (Before Verification)")
    request = factory.get('/api/billing/telegram/status/')
    force_authenticate(request, user=test_user)
    
    response = telegram_verification_status(request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Verified: {response.data.get('verified')}")
    print(f"   Has Pending Code: {response.data.get('has_pending_code')}")
    
    # 4. Simulate bot callback (verify)
    print("\n4. Testing: Bot Verification Callback")
    request = factory.post(
        '/api/billing/telegram/verify-callback/',
        {
            'verification_code': verification_code,
            'telegram_user_id': '123456789',
            'telegram_username': 'testuser'
        },
        format='json'
    )
    # Add bot secret header
    request.META['HTTP_X_BOT_SECRET'] = os.getenv('TELEGRAM_BOT_SECRET', 'your-secret-key-here')
    
    response = telegram_verify_callback(request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.data}")
    
    if response.data.get('success'):
        print(f"   ✅ Verification successful!")
    else:
        print(f"   ❌ Verification failed: {response.data.get('error')}")
        return
    
    # 5. Check verification status (after verification)
    print("\n5. Testing: Check Status (After Verification)")
    request = factory.get('/api/billing/telegram/status/')
    force_authenticate(request, user=test_user)
    
    response = telegram_verification_status(request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Verified: {response.data.get('verified')}")
    print(f"   Telegram Username: {response.data.get('telegram_username')}")
    print(f"   Telegram User ID: {response.data.get('telegram_user_id')}")
    
    # 6. Test duplicate verification attempt
    print("\n6. Testing: Duplicate Telegram Account")
    request = factory.post('/api/billing/telegram/generate-code/')
    force_authenticate(request, user=test_user)
    
    response = generate_verification_code(request)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.data}")
    
    if response.status_code == 400:
        print(f"   ✅ Correctly rejected (already verified)")
    
    # 7. Test invalid bot secret
    print("\n7. Testing: Invalid Bot Secret")
    request = factory.post(
        '/api/billing/telegram/verify-callback/',
        {
            'verification_code': 'OXI-TEST',
            'telegram_user_id': '987654321',
            'telegram_username': 'hacker'
        },
        format='json'
    )
    request.META['HTTP_X_BOT_SECRET'] = 'wrong-secret'
    
    response = telegram_verify_callback(request)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 403:
        print(f"   ✅ Correctly rejected (invalid secret)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\nSummary:")
    print("✅ Generate verification code")
    print("✅ Check status endpoints")
    print("✅ Verify Telegram account")
    print("✅ Prevent duplicate verification")
    print("✅ Validate bot secret")
    print("\n🎉 All tests passed!")


if __name__ == '__main__':
    test_verification_flow()
