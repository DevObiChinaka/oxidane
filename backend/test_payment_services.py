#!/usr/bin/env python
"""
Test Payment Services Configuration
Tests that PaystackService and StripeService correctly read from PaymentConfiguration
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import PaymentConfiguration
from subscriptions.payment_service import PaystackService, StripeService, PaymentService


def test_payment_configuration():
    """Test PaymentConfiguration singleton"""
    print("\n" + "="*60)
    print("Testing PaymentConfiguration Model")
    print("="*60)
    
    try:
        config = PaymentConfiguration.get_instance()
        print(f"✅ PaymentConfiguration singleton loaded")
        print(f"   - Paystack Enabled: {config.paystack_enabled}")
        print(f"   - Stripe Enabled: {config.stripe_enabled}")
        print(f"   - Test Mode: {config.is_test_mode}")
        print(f"   - Primary Provider: {config.primary_provider}")
        
        # Check configuration status
        print(f"\n   Configuration Status:")
        print(f"   - Paystack Configured: {config.is_paystack_configured()}")
        print(f"   - Stripe Configured: {config.is_stripe_configured()}")
        print(f"   - Any Provider: {config.has_any_provider_configured()}")
        
        # Show masked keys
        if config.paystack_public_key:
            print(f"\n   Paystack Public Key: {config.get_masked_paystack_public_key()}")
        if config.paystack_secret_key:
            print(f"   Paystack Secret Key: {config.get_masked_paystack_secret_key()}")
        if config.stripe_publishable_key:
            print(f"   Stripe Publishable Key: {config.get_masked_stripe_publishable_key()}")
        if config.stripe_secret_key:
            print(f"   Stripe Secret Key: {config.get_masked_stripe_secret_key()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading PaymentConfiguration: {e}")
        return False


def test_paystack_service():
    """Test PaystackService initialization"""
    print("\n" + "="*60)
    print("Testing PaystackService")
    print("="*60)
    
    try:
        service = PaystackService()
        print(f"✅ PaystackService initialized")
        print(f"   - Is Enabled: {service.is_enabled}")
        print(f"   - Test Mode: {service.is_test_mode}")
        print(f"   - Has Secret Key: {bool(service.secret_key)}")
        print(f"   - Has Public Key: {bool(service.public_key)}")
        
        if service.secret_key:
            # Mask the key for display
            masked = service.secret_key[:8] + "..." + service.secret_key[-4:] if len(service.secret_key) > 12 else "***"
            print(f"   - Secret Key: {masked}")
        
        # Test methods exist
        print(f"\n   Available Methods:")
        print(f"   - initialize_payment: {hasattr(service, 'initialize_payment')}")
        print(f"   - verify_payment: {hasattr(service, 'verify_payment')}")
        print(f"   - verify_webhook_signature: {hasattr(service, 'verify_webhook_signature')}")
        print(f"   - create_customer: {hasattr(service, 'create_customer')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing PaystackService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stripe_service():
    """Test StripeService initialization"""
    print("\n" + "="*60)
    print("Testing StripeService")
    print("="*60)
    
    try:
        service = StripeService()
        print(f"✅ StripeService initialized")
        print(f"   - Is Enabled: {service.is_enabled}")
        print(f"   - Test Mode: {service.is_test_mode}")
        print(f"   - Has Secret Key: {bool(service.secret_key)}")
        print(f"   - Has Publishable Key: {bool(service.publishable_key)}")
        print(f"   - Has Webhook Secret: {bool(service.webhook_secret)}")
        
        if service.secret_key:
            # Mask the key for display
            masked = service.secret_key[:8] + "..." + service.secret_key[-4:] if len(service.secret_key) > 12 else "***"
            print(f"   - Secret Key: {masked}")
        
        # Test methods exist
        print(f"\n   Available Methods:")
        print(f"   - initialize_payment: {hasattr(service, 'initialize_payment')}")
        print(f"   - verify_payment: {hasattr(service, 'verify_payment')}")
        print(f"   - verify_webhook_signature: {hasattr(service, 'verify_webhook_signature')}")
        print(f"   - create_customer: {hasattr(service, 'create_customer')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing StripeService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_payment_service():
    """Test unified PaymentService wrapper"""
    print("\n" + "="*60)
    print("Testing PaymentService (Unified Wrapper)")
    print("="*60)
    
    try:
        # Test Paystack wrapper
        paystack_service = PaymentService(gateway='paystack')
        print(f"✅ PaymentService (Paystack) initialized")
        print(f"   - Provider Type: {type(paystack_service.provider).__name__}")
        
        # Test Stripe wrapper
        stripe_service = PaymentService(gateway='stripe')
        print(f"✅ PaymentService (Stripe) initialized")
        print(f"   - Provider Type: {type(stripe_service.provider).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing PaymentService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_warnings():
    """Test that services warn correctly when not configured"""
    print("\n" + "="*60)
    print("Testing Service Warnings")
    print("="*60)
    
    try:
        config = PaymentConfiguration.get_instance()
        
        # Test disabled Paystack
        if not config.paystack_enabled:
            print("\n   Testing Paystack (Disabled):")
            service = PaystackService()
            result = service.initialize_payment(
                email='test@example.com',
                amount=100.00,
                reference='TEST123'
            )
            print(f"   - Result: {result}")
            assert not result['success'], "Should fail when disabled"
            print(f"   ✅ Correctly returns error when disabled")
        
        # Test unconfigured Stripe
        if not config.stripe_secret_key:
            print("\n   Testing Stripe (No API Key):")
            service = StripeService()
            result = service.initialize_payment(
                email='test@example.com',
                amount=100.00
            )
            print(f"   - Result: {result}")
            assert not result['success'], "Should fail when not configured"
            print(f"   ✅ Correctly returns error when not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing warnings: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PAYMENT SERVICES CONFIGURATION TEST")
    print("Testing PaymentConfiguration Model Integration")
    print("="*60)
    
    results = []
    
    # Test 1: PaymentConfiguration Model
    results.append(('PaymentConfiguration', test_payment_configuration()))
    
    # Test 2: PaystackService
    results.append(('PaystackService', test_paystack_service()))
    
    # Test 3: StripeService
    results.append(('StripeService', test_stripe_service()))
    
    # Test 4: Unified PaymentService
    results.append(('PaymentService', test_payment_service()))
    
    # Test 5: Service Warnings
    results.append(('Service Warnings', test_service_warnings()))
    
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
        print("\n✅ All tests passed! Payment services correctly configured.")
    else:
        print("\n⚠️ Some tests failed. Check configuration above.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
