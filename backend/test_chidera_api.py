"""
Test API for chiderachinaka06 account
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

# Override ALLOWED_HOSTS for testing
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

print("=" * 80)
print("🧪 Testing API for chiderachinaka06@gmail.com")
print("=" * 80)

try:
    user = User.objects.get(email='chiderachinaka06@gmail.com')
    print(f"\n✅ User found: {user.email}\n")
    
    # Create API client and authenticate
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test the my-subscriptions endpoint
    print("📋 Testing GET /api/subscriptions/my-subscriptions/")
    print("-" * 80)
    
    response = client.get('/api/subscriptions/my-subscriptions/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ API Response Successful!\n")
        
        # Display stats
        stats = data.get('stats', {})
        print("📊 STATS:")
        print(f"   Active Count: {stats.get('active_count', 0)}")
        print(f"   Total Monthly Cost: ${stats.get('total_monthly_cost', 0)}")
        print(f"   Days Until Renewal: {stats.get('days_until_renewal', 'N/A')}")
        print(f"   Next Renewal Date: {stats.get('next_renewal_date', 'N/A')}")
        
        # Display subscriptions
        subscriptions = data.get('subscriptions', [])
        print(f"\n📦 SUBSCRIPTIONS ({len(subscriptions)} total):")
        print("-" * 80)
        
        for sub in subscriptions:
            print(f"\n   Plan: {sub.get('plan_name')}")
            print(f"   Type: {sub.get('plan_type')}")
            print(f"   Status: {sub.get('status')}")
            print(f"   Amount: ${sub.get('amount')}/{sub.get('billing_cycle')}")
            print(f"   Currency: {sub.get('currency')}")
            print(f"   Start Date: {sub.get('start_date')}")
            print(f"   End Date: {sub.get('end_date')}")
            print(f"   Auto Renew: {sub.get('auto_renew')}")
            
            if sub.get('days_remaining') is not None:
                print(f"   Days Remaining: {sub.get('days_remaining')}")
            
            print(f"   Telegram: {sub.get('telegram_username', 'N/A')}")
            
            features = sub.get('features', [])
            if features:
                print(f"   Features:")
                for feature in features:
                    print(f"      ✓ {feature}")
        
        if not subscriptions:
            print("\n   ⚠️  No subscriptions returned by API")
    else:
        print(f"\n❌ API Error!")
        print(f"Response: {response.content.decode('utf-8')}")

except User.DoesNotExist:
    print("\n❌ User not found!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
