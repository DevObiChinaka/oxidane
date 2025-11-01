#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

# Create test client
client = Client()

# Get admin user for authentication
User = get_user_model()
try:
    admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
    if not admin_user:
        print("No admin user found. Creating one...")
        admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
    
    print(f"Using admin user: {admin_user.email}")
    
    # Force login
    client.force_login(admin_user)
    
    # Test the coupon codes API endpoint
    print("\n=== Testing Coupon Codes API ===")
    response = client.get('/api/admin/pricing/coupons/')
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.get('content-type', 'N/A')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Data Type: {type(data)}")
        
        if isinstance(data, dict) and 'results' in data:
            coupons = data['results']
            print(f"Number of coupons returned: {len(coupons)}")
        elif isinstance(data, list):
            coupons = data
            print(f"Number of coupons returned: {len(coupons)}")
        else:
            coupons = []
            print("Unexpected response format")
            print(f"Response: {data}")
        
        if coupons:
            print("\nFirst coupon:")
            first_coupon = coupons[0]
            for key, value in first_coupon.items():
                print(f"  {key}: {value}")
        else:
            print("No coupons in API response")
    else:
        print(f"API Error: {response.content.decode()}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()