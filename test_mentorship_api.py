#!/usr/bin/env python3
"""
Test script for Mentorship API endpoints
Run this after starting the Django server with: python manage.py runserver
"""

import requests
import json
from datetime import datetime, timedelta

# Base URL for the Django API
BASE_URL = "http://localhost:8000/api/admin"

def test_mentorship_endpoints():
    """Test all mentorship API endpoints"""
    
    print("🔍 Testing Mentorship API Endpoints...")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        "/mentorship/subscriptions/",
        "/mentorship/sessions/",
        "/mentorship/analytics/"
    ]
    
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        print(f"\n📡 Testing: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS: {response.status_code}")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Returned {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   📊 Returned object with {len(data)} keys")
                        for key, value in data.items():
                            if isinstance(value, (int, float)):
                                print(f"      {key}: {value}")
                            elif isinstance(value, list):
                                print(f"      {key}: {len(value)} items")
                except json.JSONDecodeError:
                    print(f"   ⚠️  Response not JSON: {response.text[:100]}")
            else:
                print(f"❌ ERROR: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 CONNECTION ERROR: Cannot connect to {url}")
            print("   Make sure Django server is running: python manage.py runserver")
        except requests.exceptions.Timeout:
            print(f"⏱️  TIMEOUT: Request to {url} timed out")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete!")

def create_sample_data():
    """Create sample mentorship data for testing"""
    print("\n🛠️  Creating Sample Data...")
    print("=" * 50)
    
    # This would require Django management command or direct database access
    print("ℹ️  To create sample data, run these Django commands:")
    print("   python manage.py shell")
    print("   >>> from subscriptions.models import MentorshipPlan")
    print("   >>> MentorshipPlan.objects.create(")
    print("       name='Premium Mentorship + 1-on-1',")
    print("       plan_type='mentorship_premium',")
    print("       price=799.00,")
    print("       currency='USD',")
    print("       description='3-month mentorship with 1-on-1 sessions',")
    print("       features=['Telegram access', 'Premium content', '3 x 1-on-1 sessions'],")
    print("       max_sessions=3")
    print("   )")

if __name__ == "__main__":
    test_mentorship_endpoints()
    create_sample_data()