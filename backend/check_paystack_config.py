"""Check Paystack configuration in PaymentConfiguration model"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import PaymentConfiguration

config = PaymentConfiguration.get_instance()

print("\n=== PaymentConfiguration Status ===")
print(f"Paystack Enabled: {config.paystack_enabled}")
print(f"Test Mode: {config.is_test_mode}")
print(f"\nPublic Key: {config.paystack_public_key[:30] if config.paystack_public_key else 'NOT SET'}...")
print(f"Secret Key exists: {bool(config.paystack_secret_key)}")

if config.paystack_secret_key:
    print(f"Secret Key starts with: {config.paystack_secret_key[:10]}...")
    print(f"Secret Key length: {len(config.paystack_secret_key)}")
    
    # Check if encrypted
    if config.paystack_secret_key.startswith('gAAAAA'):
        print("⚠️  Secret key appears to be ENCRYPTED")
        try:
            decrypted = config.decrypt_field('paystack_secret_key')
            print(f"Decrypted key starts with: {decrypted[:10] if decrypted else 'FAILED'}...")
            print(f"Decrypted key valid format: {decrypted.startswith('sk_') if decrypted else False}")
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
    elif config.paystack_secret_key.startswith('sk_'):
        print("✅ Secret key is in PLAIN TEXT (valid format)")
    else:
        print(f"❌ Secret key has INVALID format (should start with 'sk_' or 'gAAAAA')")
else:
    print("❌ NO SECRET KEY CONFIGURED")

# Test the PaystackService initialization
print("\n=== Testing PaystackService ===")
from subscriptions.payment_service import PaystackService

service = PaystackService()
print(f"Service secret_key: {service.secret_key[:20] if service.secret_key else 'NOT SET'}...")
print(f"Service enabled: {service.is_enabled}")
print(f"Service test mode: {service.is_test_mode}")
