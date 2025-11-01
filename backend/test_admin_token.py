#!/usr/bin/env python3

"""
Test the admin token to make sure backend authentication is working
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
TOKEN = "655ec11f736ae64eae39dcd7d1fc3f6bf9fe56af05e560631250aaf12b776b57"

def test_admin_endpoints():
    """Test admin endpoints with authentication"""
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        f"{BASE_URL}/admin/subscriptions/",
        f"{BASE_URL}/admin/dashboard/", 
        f"{BASE_URL}/admin/analytics/dashboard/",
    ]
    
    print("🧪 Testing Admin Endpoints with Authentication")
    print("=" * 60)
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"Response keys: {list(data.keys())}")
                    print(f"Response length: {len(response.text)} chars")
                except:
                    print("Response is not valid JSON")
                    
            elif response.status_code == 401:
                print("🔐 UNAUTHORIZED - Token invalid or expired")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Raw response: {response.text}")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR - Is Django server running?")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            
        print("-" * 40)

if __name__ == "__main__":
    test_admin_endpoints()