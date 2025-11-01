"""
Test script for User Subscription Management API
Tests all endpoints: my-subscriptions, cancel, auto-renewal, reactivate
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
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from subscriptions.models import PricingPlan, SignalSubscription, MentorshipSubscription
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def get_user_token(user):
    """Generate JWT token for user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def setup_test_data():
    """Create test user and subscriptions"""
    print("\n🔧 Setting up test data...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        email='testuser@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Create or get Signal pricing plan
    signal_plan, created = PricingPlan.objects.get_or_create(
        plan_type='signals_monthly',
        defaults={
            'name': 'Monthly Signals',
            'description': 'Get daily trading signals',
            'price': Decimal('29.00'),
            'billing_cycle': 'monthly',
            'category': 'signals',
            'is_active': True,
            'signals_per_day': 5,
        }
    )
    if created:
        print(f"✅ Created pricing plan: {signal_plan.name}")
    else:
        print(f"✅ Using existing pricing plan: {signal_plan.name}")
    
    # Get or create active signal subscription
    signal_sub = SignalSubscription.objects.filter(
        user=user,
        pricing_plan=signal_plan,
        payment_status='verified',
        subscription_end__gte=timezone.now()
    ).first()
    
    if not signal_sub:
        signal_sub = SignalSubscription.objects.create(
            user=user,
            pricing_plan=signal_plan,
            paystack_reference=f'test_ref_{int(timezone.now().timestamp())}',
            amount_paid=signal_plan.price,
            plan_type='signals_monthly',
            payment_status='verified',
            subscription_start=timezone.now(),
            subscription_end=timezone.now() + timedelta(days=30),
            auto_renewal=True,
            telegram_username='@testuser',
            telegram_status='added',
        )
        print(f"✅ Created active signal subscription")
    else:
        print(f"✅ Using existing active signal subscription")
    
    # Get or create expired signal subscription for reactivation test
    expired_signal_sub = SignalSubscription.objects.filter(
        user=user,
        payment_status='verified',
        subscription_end__lt=timezone.now()
    ).first()
    
    if not expired_signal_sub:
        expired_signal_sub = SignalSubscription.objects.create(
            user=user,
            pricing_plan=signal_plan,
            paystack_reference=f'test_ref_expired_{int(timezone.now().timestamp())}',
            amount_paid=signal_plan.price,
            plan_type='signals_monthly',
            payment_status='verified',
            subscription_start=timezone.now() - timedelta(days=60),
            subscription_end=timezone.now() - timedelta(days=30),
            auto_renewal=False,
            telegram_username='@testuser',
            telegram_status='removed',
        )
        print(f"✅ Created expired signal subscription for reactivation test")
    else:
        print(f"✅ Using existing expired signal subscription")
    
    return user, signal_sub, expired_signal_sub

def test_my_subscriptions(client, user):
    """Test GET /api/subscriptions/my-subscriptions/"""
    print("\n📋 Testing: GET /api/subscriptions/my-subscriptions/")
    
    client.force_authenticate(user=user)
    response = client.get('/api/subscriptions/my-subscriptions/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Active Subscriptions: {data['stats']['active_count']}")
        print(f"   Total Monthly Cost: ${data['stats']['total_monthly_cost']}")
        print(f"   Days Until Renewal: {data['stats']['days_until_renewal']}")
        print(f"   Total Subscriptions: {len(data['subscriptions'])}")
        
        for sub in data['subscriptions']:
            print(f"\n   📦 {sub['plan_name']}")
            print(f"      Status: {sub['status']}")
            print(f"      Price: ${sub['amount']}/{sub['billing_cycle']}")
            print(f"      Auto-renew: {sub['auto_renew']}")
            if sub.get('days_remaining'):
                print(f"      Days remaining: {sub['days_remaining']}")
        
        return data['subscriptions']
    else:
        print(f"❌ Failed: {response.json()}")
        return []

def test_toggle_auto_renewal(client, user, subscription_id):
    """Test PATCH /api/subscriptions/{id}/auto-renewal/"""
    print(f"\n🔄 Testing: PATCH /api/subscriptions/{subscription_id}/auto-renewal/")
    
    client.force_authenticate(user=user)
    
    # Toggle OFF
    response = client.patch(
        f'/api/subscriptions/{subscription_id}/auto-renewal/',
        {'auto_renew': False},
        format='json'
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Message: {data['message']}")
        print(f"   Auto-renew: {data['auto_renew']}")
        
        # Toggle back ON
        response = client.patch(
            f'/api/subscriptions/{subscription_id}/auto-renewal/',
            {'auto_renew': True},
            format='json'
        )
        if response.status_code == 200:
            print(f"   ✅ Successfully toggled back ON")
    else:
        print(f"❌ Failed: {response.json()}")

def test_cancel_subscription(client, user, subscription_id):
    """Test POST /api/subscriptions/{id}/cancel/"""
    print(f"\n❌ Testing: POST /api/subscriptions/{subscription_id}/cancel/")
    print("   ⚠️  Note: This will mark subscription for cancellation")
    
    response = input("   Proceed with test? (y/n): ")
    if response.lower() != 'y':
        print("   ⏭️  Skipped")
        return
    
    client.force_authenticate(user=user)
    response = client.post(f'/api/subscriptions/{subscription_id}/cancel/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Message: {data['message']}")
        print(f"   Access until: {data['end_date']}")
    else:
        print(f"❌ Failed: {response.json()}")

def test_reactivate_subscription(client, user, subscription_id):
    """Test POST /api/subscriptions/{id}/reactivate/"""
    print(f"\n♻️  Testing: POST /api/subscriptions/{subscription_id}/reactivate/")
    
    client.force_authenticate(user=user)
    response = client.post(f'/api/subscriptions/{subscription_id}/reactivate/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Message: {data['message']}")
        print(f"   New end date: {data['end_date']}")
    else:
        print(f"❌ Failed: {response.json()}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 User Subscription Management API Tests")
    print("=" * 60)
    
    # Setup
    user, signal_sub, expired_signal_sub = setup_test_data()
    client = APIClient()
    
    # Test 1: Get all subscriptions
    subscriptions = test_my_subscriptions(client, user)
    
    if not subscriptions:
        print("\n⚠️  No subscriptions found. Cannot proceed with other tests.")
        return
    
    # Get an active subscription for testing
    active_subs = [s for s in subscriptions if s['status'] == 'active']
    inactive_subs = [s for s in subscriptions if s['status'] != 'active']
    
    # Test 2: Toggle auto-renewal (on active subscription)
    if active_subs:
        test_toggle_auto_renewal(client, user, active_subs[0]['id'])
    
    # Test 3: Cancel subscription (optional, skippable)
    if active_subs:
        test_cancel_subscription(client, user, active_subs[0]['id'])
    
    # Test 4: Reactivate subscription (on inactive subscription)
    if inactive_subs:
        test_reactivate_subscription(client, user, inactive_subs[0]['id'])
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()
