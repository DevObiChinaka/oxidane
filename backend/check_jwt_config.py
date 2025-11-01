"""
Check JWT token expiration settings
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings
from datetime import timedelta

print("=" * 80)
print("🔍 JWT TOKEN CONFIGURATION")
print("=" * 80)

# Check if SIMPLE_JWT is configured
simple_jwt = getattr(settings, 'SIMPLE_JWT', None)

if simple_jwt:
    print("\n✅ SIMPLE_JWT configuration found:")
    for key, value in simple_jwt.items():
        if isinstance(value, timedelta):
            print(f"   {key}: {value.total_seconds() / 60} minutes")
        else:
            print(f"   {key}: {value}")
else:
    print("\n⚠️  No SIMPLE_JWT configuration found!")
    print("   Using default settings:")
    print("   ACCESS_TOKEN_LIFETIME: 5 minutes")
    print("   REFRESH_TOKEN_LIFETIME: 1 day")
    print("\n💡 Recommendation: Add SIMPLE_JWT settings to extend token lifetime")

print("\n" + "=" * 80)
print("📝 SUGGESTED CONFIGURATION")
print("=" * 80)
print("""
Add this to settings.py:

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Extend to 1 day
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # 7 days
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
""")
print("=" * 80)
