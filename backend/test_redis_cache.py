import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache

print("Testing Redis cache...")
print(f"Cache backend: {cache.__class__.__name__}")

# Test 1: Simple set/get
print("\n--- Test 1: Simple set/get ---")
cache.set('test_key_1', 'test_value_1', 60)
result = cache.get('test_key_1')
print(f"Set: 'test_value_1'")
print(f"Get: {result}")
print(f"Result: {'✅ WORKING' if result == 'test_value_1' else '❌ NOT WORKING'}")

# Test 2: OTP-like key
print("\n--- Test 2: OTP-like key ---")
otp_key = "otp:email_change_test123"
cache.set(otp_key, '123456', 600)
result = cache.get(otp_key)
print(f"Set: '123456' with key '{otp_key}'")
print(f"Get: {result}")
print(f"Result: {'✅ WORKING' if result == '123456' else '❌ NOT WORKING'}")

# Test 3: Check if exceptions are being ignored
print("\n--- Test 3: Connection info ---")
try:
    from django.conf import settings
    print(f"REDIS_URL: {settings.REDIS_URL[:50]}...")
    print(f"IGNORE_EXCEPTIONS: {settings.CACHES['default']['OPTIONS']['IGNORE_EXCEPTIONS']}")
except Exception as e:
    print(f"Error getting settings: {e}")
