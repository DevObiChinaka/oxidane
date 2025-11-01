#!/usr/bin/env python
import os
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model

# Get admin user and create token
User = get_user_model()
admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()

if admin_user:
    print(f"Testing API with admin user: {admin_user.email}")
    
    # Create a session token (simulate login)
    from django.core.cache import cache
    from django.utils import timezone
    import uuid
    
    admin_token = str(uuid.uuid4())
    session_data = {
        'user_id': str(admin_user.id),
        'email': admin_user.email,
        'expires_at': (timezone.now() + timezone.timedelta(hours=24)).isoformat()
    }
    
    cache_key = f"admin_session_{admin_token}"
    cache.set(cache_key, json.dumps(session_data), 24 * 60 * 60)
    
    print(f"Created admin token: {admin_token}")
    
    # Test the API endpoint
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('http://localhost:8000/api/admin/pricing/coupons/', headers=headers)
        
        print(f"\nAPI Response Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nResponse Type: {type(data)}")
                
                if isinstance(data, dict):
                    print("Response is a dictionary:")
                    for key, value in data.items():
                        print(f"  {key}: {type(value)} - {len(value) if isinstance(value, (list, dict)) else value}")
                    
                    if 'results' in data:
                        print(f"\nCoupons in 'results': {len(data['results'])}")
                        if data['results']:
                            print("First coupon:")
                            first_coupon = data['results'][0]
                            for key, value in first_coupon.items():
                                print(f"  {key}: {value}")
                
                elif isinstance(data, list):
                    print(f"Response is a list with {len(data)} items")
                    if data:
                        print("First coupon:")
                        first_coupon = data[0]
                        for key, value in first_coupon.items():
                            print(f"  {key}: {value}")
                
                else:
                    print(f"Unexpected response type: {type(data)}")
                    print(f"Response: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
else:
    print("No admin user found")