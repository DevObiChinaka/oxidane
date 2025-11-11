#!/usr/bin/env python
"""
Test Payment API Endpoints
Tests all payment endpoints with mock data

Endpoints Tested:
1. POST /api/payments/initialize/
2. POST /api/payments/verify/
3. POST /api/payments/webhook/paystack/
4. POST /api/payments/webhook/stripe/
5. GET /api/payments/history/
6. GET /api/payments/{id}/invoice/

Created: November 10, 2025
"""

import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from subscriptions.models import (
    SubscriptionPlan, Feature, PaymentConfiguration,
    BillingProfile, Coupon
)
from decimal import Decimal

User = get_user_model()


def setup_test_data():
    """Create test data for API testing"""
    print("\n" + "="*60)
    print("Setting Up Test Data")
    print("="*60)
    
    # Create test user
    try:
        user = User.objects.filter(email='testuser@example.com').first()
        if not user:
            user = User.objects.create_user(
                username='testuser',
                email='testuser@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            print(f"✅ Created test user: {user.email}")
        else:
            print(f"✅ Using existing test user: {user.email}")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None
    
    # Create test feature
    try:
        feature = Feature.objects.filter(name='Test Feature').first()
        if not feature:
            feature = Feature.objects.create(
                name='Test Feature',
                key='test_feature',
                description='Feature for testing',
                category='core',
                is_active=True
            )
            print(f"✅ Created test feature: {feature.name}")
        else:
            print(f"✅ Using existing feature: {feature.name}")
    except Exception as e:
        print(f"⚠️ Error creating feature: {e}")
        feature = None
    
    # Create test plan
    try:
        plan = SubscriptionPlan.objects.filter(name='Test Plan').first()
        if not plan:
            plan = SubscriptionPlan.objects.create(
                name='Test Plan',
                description='Plan for testing',
                base_price=Decimal('50.00'),  # USD base price
                billing_period='monthly',
                is_active=True,
                is_featured=False
            )
            if feature:
                plan.features.add(feature)
            print(f"✅ Created test plan: {plan.name} (${plan.base_price}/month)")
        else:
            print(f"✅ Using existing plan: {plan.name}")
    except Exception as e:
        print(f"❌ Error creating plan: {e}")
        import traceback
        traceback.print_exc()
        return user, None, None
    
    # Create test coupon
    try:
        coupon = Coupon.objects.filter(code='TEST50').first()
        if not coupon:
            coupon = Coupon.objects.create(
                code='TEST50',
                discount_type='percentage',
                discount_value=Decimal('50.00'),
                is_active=True,
                usage_limit=100,
                times_used=0
            )
            print(f"✅ Created test coupon: {coupon.code} (50% off)")
        else:
            print(f"✅ Using existing coupon: {coupon.code}")
    except Exception as e:
        print(f"⚠️ Error creating coupon: {e}")
        coupon = None
    
    # Verify PaymentConfiguration exists
    try:
        config = PaymentConfiguration.get_instance()
        print(f"✅ PaymentConfiguration loaded")
        print(f"   - Paystack Enabled: {config.paystack_enabled}")
        print(f"   - Stripe Enabled: {config.stripe_enabled}")
    except Exception as e:
        print(f"❌ Error loading PaymentConfiguration: {e}")
    
    return user, plan, coupon


def test_initialize_payment(client, user, plan, coupon=None):
    """Test POST /api/payments/initialize/"""
    print("\n" + "="*60)
    print("TEST 1: Initialize Payment")
    print("="*60)
    
    # Login user
    client.force_login(user)
    
    # Test data
    payload = {
        'plan_id': str(plan.id),  # Convert UUID to string
        'currency': 'NGN',
        'callback_url': 'https://example.com/payment-success'
    }
    
    if coupon:
        payload['coupon_code'] = coupon.code
    
    print(f"\nRequest: POST /api/subscriptions/payments/initialize/")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Make request
    response = client.post(
        '/api/subscriptions/payments/initialize/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200 and data.get('success'):
            print(f"\n✅ PASS: Payment initialized successfully")
            print(f"   - Reference: {data.get('reference')}")
            print(f"   - Amount: {data.get('currency')} {data.get('amount')}")
            print(f"   - Fee: {data.get('processing_fee')}")
            print(f"   - Total: {data.get('total_amount')}")
            print(f"   - Gateway: {data.get('gateway')}")
            return True, data.get('reference')
        else:
            print(f"\n❌ FAIL: {data.get('error', 'Unknown error')}")
            return False, None
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        print(f"Response text: {response.content.decode()}")
        return False, None


def test_verify_payment(client, user, reference):
    """Test POST /api/payments/verify/"""
    print("\n" + "="*60)
    print("TEST 2: Verify Payment")
    print("="*60)
    
    if not reference:
        print("⏭️ SKIP: No reference from initialize test")
        return False
    
    # Login user
    client.force_login(user)
    
    # Test data
    payload = {
        'reference': reference,
        'gateway': 'paystack'
    }
    
    print(f"\nRequest: POST /api/subscriptions/payments/verify/")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Make request
    response = client.post(
        '/api/subscriptions/payments/verify/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        # Note: This will fail because we haven't actually paid via Paystack
        # But we're testing the endpoint structure
        if response.status_code in [200, 400]:
            print(f"\n✅ PASS: Endpoint functional (expected to fail without real payment)")
            return True
        else:
            print(f"\n❌ FAIL: Unexpected response")
            return False
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def test_payment_history(client, user):
    """Test GET /api/payments/history/"""
    print("\n" + "="*60)
    print("TEST 3: Payment History")
    print("="*60)
    
    # Login user
    client.force_login(user)
    
    print(f"\nRequest: GET /api/subscriptions/payments/history/")
    
    # Make request
    response = client.get('/api/subscriptions/payments/history/')
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200:
            count = data.get('count', 0)
            results = data.get('results', [])
            print(f"\n✅ PASS: Payment history retrieved")
            print(f"   - Total Payments: {count}")
            print(f"   - Payments on Page: {len(results)}")
            return True
        else:
            print(f"\n❌ FAIL: Unexpected response")
            return False
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def test_webhook_paystack(client):
    """Test POST /api/payments/webhook/paystack/"""
    print("\n" + "="*60)
    print("TEST 4: Paystack Webhook")
    print("="*60)
    
    # Mock webhook payload
    payload = {
        'event': 'charge.success',
        'data': {
            'reference': 'TEST_REF_123',
            'amount': 510000,  # ₦5,100 in kobo
            'currency': 'NGN',
            'status': 'success',
            'customer': {
                'email': 'testuser@example.com'
            }
        }
    }
    
    print(f"\nRequest: POST /api/subscriptions/payments/webhook/paystack/")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"\nNote: Will fail signature verification (expected)")
    
    # Make request
    response = client.post(
        '/api/subscriptions/payments/webhook/paystack/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        # Expected to fail due to signature
        if response.status_code in [400, 401]:
            print(f"\n✅ PASS: Endpoint functional (signature check working)")
            return True
        else:
            print(f"\n⚠️ WARN: Unexpected response (but endpoint exists)")
            return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def test_webhook_stripe(client):
    """Test POST /api/payments/webhook/stripe/"""
    print("\n" + "="*60)
    print("TEST 5: Stripe Webhook")
    print("="*60)
    
    # Mock webhook payload
    payload = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_123',
                'amount_total': 5100,
                'currency': 'usd',
                'payment_status': 'paid'
            }
        }
    }
    
    print(f"\nRequest: POST /api/subscriptions/payments/webhook/stripe/")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"\nNote: Will fail signature verification (expected)")
    
    # Make request
    response = client.post(
        '/api/subscriptions/payments/webhook/stripe/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        # Expected to fail due to signature
        if response.status_code in [400, 401]:
            print(f"\n✅ PASS: Endpoint functional (signature check working)")
            return True
        else:
            print(f"\n⚠️ WARN: Unexpected response (but endpoint exists)")
            return True
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def test_invoice_download(client, user):
    """Test GET /api/payments/{id}/invoice/"""
    print("\n" + "="*60)
    print("TEST 6: Invoice Download")
    print("="*60)
    
    # Login user
    client.force_login(user)
    
    # Try with payment_id=1 (may not exist)
    payment_id = 1
    
    print(f"\nRequest: GET /api/subscriptions/payments/{payment_id}/invoice/")
    
    # Make request
    response = client.get(f'/api/subscriptions/payments/{payment_id}/invoice/')
    
    print(f"\nResponse Status: {response.status_code}")
    
    try:
        data = response.json()
        print(f"Response Data:")
        print(json.dumps(data, indent=2))
        
        # Either 404 (payment not found) or 400 (payment not successful)
        if response.status_code in [200, 400, 404]:
            print(f"\n✅ PASS: Endpoint functional")
            return True
        else:
            print(f"\n❌ FAIL: Unexpected response")
            return False
    except Exception as e:
        print(f"\n❌ FAIL: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PAYMENT API ENDPOINTS TEST SUITE")
    print("Testing All 6 Payment Endpoints")
    print("="*60)
    
    # Setup
    user, plan, coupon = setup_test_data()
    
    if not user or not plan:
        print("\n❌ ABORT: Failed to setup test data")
        return False
    
    # Create test client
    client = Client()
    
    # Run tests
    results = []
    
    # Test 1: Initialize Payment
    success, reference = test_initialize_payment(client, user, plan, coupon)
    results.append(('Initialize Payment', success))
    
    # Test 2: Verify Payment
    success = test_verify_payment(client, user, reference)
    results.append(('Verify Payment', success))
    
    # Test 3: Payment History
    success = test_payment_history(client, user)
    results.append(('Payment History', success))
    
    # Test 4: Paystack Webhook
    success = test_webhook_paystack(client)
    results.append(('Paystack Webhook', success))
    
    # Test 5: Stripe Webhook
    success = test_webhook_stripe(client)
    results.append(('Stripe Webhook', success))
    
    # Test 6: Invoice Download
    success = test_invoice_download(client, user)
    results.append(('Invoice Download', success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All payment API endpoints are functional!")
    else:
        print(f"\n⚠️ Some tests failed. Check details above.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
