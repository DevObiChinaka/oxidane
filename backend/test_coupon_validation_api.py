"""
Test the coupon validation API endpoint to verify per-user limit enforcement
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import Coupon

User = get_user_model()

def test_coupon_validation_api():
    """Test coupon validation via API"""
    
    print("=" * 70)
    print("TESTING COUPON VALIDATION API")
    print("=" * 70)
    
    # Test user who has already used SAVE20 twice
    user_email = "obbinachidera123@gmail.com"
    coupon_code = "SAVE20"
    
    try:
        user = User.objects.get(email=user_email)
        print(f"\n✓ Testing with user: {user.email}")
        print(f"✓ Testing coupon: {coupon_code}")
        
        # Get coupon details
        coupon = Coupon.objects.get(code=coupon_code)
        print(f"✓ Coupon max uses per user: {coupon.max_uses_per_user}")
        
    except User.DoesNotExist:
        print(f"\n❌ User {user_email} not found")
        return
    except Coupon.DoesNotExist:
        print(f"\n❌ Coupon {coupon_code} not found")
        return
    
    # Make API request
    url = "http://localhost:8000/api/v1/subscriptions/validate-coupon/validate/"
    
    payload = {
        "code": coupon_code,
        "user_id": str(user.id),
        "amount": 100.00
    }
    
    print(f"\n📤 Making API request to: {url}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        data = response.json()
        
        print("\n" + "=" * 70)
        print("TEST RESULT")
        print("=" * 70)
        
        if response.status_code == 400 and not data.get('valid', True):
            if 'already used this coupon' in data.get('error', ''):
                print("\n✅ SUCCESS! Per-user limit is being enforced")
                print(f"   Error message: {data.get('error')}")
                print(f"   Error code: {data.get('error_code')}")
            else:
                print(f"\n⚠️  Coupon rejected but for a different reason:")
                print(f"   {data.get('error')}")
        elif data.get('valid'):
            print("\n❌ FAILURE! Coupon was accepted even though user exceeded limit")
            print("   This should NOT happen!")
        else:
            print(f"\n⚠️  Unexpected response: {data}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API. Is the Django server running?")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_coupon_validation_api()
