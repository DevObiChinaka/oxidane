#!/usr/bin/env python3

"""
Test script to verify backend subscription API endpoints are working
Run this to test the API endpoints that the frontend is trying to call
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
ENDPOINTS_TO_TEST = [
    {
        'name': 'Subscription List',
        'url': f"{BASE_URL}/admin/subscriptions/",
        'method': 'GET',
        'params': {'page': 1, 'limit': 20}
    },
    {
        'name': 'Analytics Dashboard', 
        'url': f"{BASE_URL}/admin/analytics/dashboard/",
        'method': 'GET',
        'params': {'period': 'monthly', 'days_back': 30}
    },
    {
        'name': 'Performance Metrics',
        'url': f"{BASE_URL}/admin/performance/metrics/",
        'method': 'GET',
        'params': {'hours': 24}
    },
    {
        'name': 'Main Dashboard',
        'url': f"{BASE_URL}/admin/dashboard/",
        'method': 'GET'
    }
]

def test_endpoints():
    """Test each endpoint and report results"""
    print("🧪 Testing Backend API Endpoints")
    print("=" * 50)
    
    results = []
    
    for endpoint in ENDPOINTS_TO_TEST:
        print(f"Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            # Make the request
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'], 
                    params=endpoint.get('params', {}),
                    timeout=10
                )
            else:
                response = requests.post(endpoint['url'], timeout=10)
            
            # Check response
            status_code = response.status_code
            
            if status_code == 200:
                print(f"✅ SUCCESS - Status: {status_code}")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   Response keys: {list(data.keys())}")
                    else:
                        print(f"   Response type: {type(data)}")
                except:
                    print(f"   Response length: {len(response.text)} chars")
            elif status_code == 404:
                print(f"❌ NOT FOUND - Status: {status_code}")
            elif status_code == 403:
                print(f"🔒 FORBIDDEN - Status: {status_code} (Authentication required)")
            elif status_code == 401:
                print(f"🔐 UNAUTHORIZED - Status: {status_code} (Login required)")
            else:
                print(f"⚠️  UNEXPECTED - Status: {status_code}")
                
            results.append({
                'endpoint': endpoint['name'],
                'status_code': status_code,
                'success': 200 <= status_code < 300
            })
            
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR - Is Django server running on localhost:8000?")
            results.append({
                'endpoint': endpoint['name'], 
                'status_code': 'Connection Error',
                'success': False
            })
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            results.append({
                'endpoint': endpoint['name'],
                'status_code': f'Error: {str(e)}',
                'success': False
            })
        
        print("-" * 30)
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Total endpoints tested: {total}")
    print(f"Successful responses: {successful}")
    print(f"Failed responses: {total - successful}")
    
    if successful == total:
        print("\n🎉 All endpoints are working!")
    elif successful == 0:
        print("\n💥 All endpoints failed - Check Django server")
    else:
        print(f"\n⚠️  {total - successful} endpoints need attention")
        
    print("\n🔧 Next Steps:")
    if successful == 0:
        print("1. Start Django server: python manage.py runserver 8000")
        print("2. Check Django URLs configuration")
    else:
        print("1. Check failed endpoints in Django views")
        print("2. Verify authentication requirements") 
        print("3. Test frontend connectivity")

if __name__ == "__main__":
    test_endpoints()