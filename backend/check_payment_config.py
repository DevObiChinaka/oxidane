import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import PaymentConfiguration

# Get payment configuration
config = PaymentConfiguration.get_instance()

print("="*60)
print("PAYMENT CONFIGURATION STATUS")
print("="*60)

print(f"\nPaystack Secret Key: {'SET' if config.paystack_secret_key else 'NOT SET'}")
if config.paystack_secret_key:
    key_preview = config.decrypt_field('paystack_secret_key')
    # Check if it's a live or test key
    is_live = key_preview.startswith('sk_live_') if key_preview else False
    is_test = key_preview.startswith('sk_test_') if key_preview else False
    print(f"  Key Type: {'LIVE' if is_live else 'TEST' if is_test else 'UNKNOWN'}")
    print(f"  Preview: {key_preview[:15]}...")

print(f"\nStripe Secret Key: {'SET' if config.stripe_secret_key else 'NOT SET'}")
if config.stripe_secret_key:
    key_preview = config.decrypt_field('stripe_secret_key')
    is_live = key_preview.startswith('sk_live_') if key_preview else False
    is_test = key_preview.startswith('sk_test_') if key_preview else False
    print(f"  Key Type: {'LIVE' if is_live else 'TEST' if is_test else 'UNKNOWN'}")
    print(f"  Preview: {key_preview[:15]}...")

print(f"\nTest Mode Setting: {config.is_test_mode}")
print(f"Primary Provider: {config.primary_provider}")

# Check if keys suggest live mode but setting is test
if config.paystack_secret_key:
    key = config.decrypt_field('paystack_secret_key')
    if key.startswith('sk_live_') and config.is_test_mode:
        print("\n⚠️  WARNING: Live Paystack key detected but test_mode is True!")
        print("   The system will show 'Test' mode despite using live keys.")
        print("\n   Fix: Set is_test_mode to False")
        
        response = input("\nUpdate test_mode to False? (yes/no): ")
        if response.lower() == 'yes':
            config.is_test_mode = False
            config.save()
            print("✅ Updated! test_mode is now False (LIVE mode)")
        else:
            print("❌ Not updated. Manual fix required.")

print("\n" + "="*60)
