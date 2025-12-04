#!/usr/bin/env python3
import os, sys, django
sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from rest_framework.routers import DefaultRouter
from subscriptions.api_views import TelegramConfigurationViewSet

print("Testing TelegramConfigurationViewSet routing...")
router = DefaultRouter()
router.register(r'admin/telegram/config', TelegramConfigurationViewSet, basename='telegram-config')

print("\nGenerated routes:")
for url in router.urls:
    if 'discover' in str(url.pattern) or 'test-connection' in str(url.pattern):
        print(f"  {url.pattern} -> {url.name}")

# Check if discover_chats action exists
print(f"\nActions on ViewSet:")
viewset = TelegramConfigurationViewSet()
if hasattr(viewset, 'discover_chats'):
    print("  ✓ discover_chats method exists")
else:
    print("  ✗ discover_chats method NOT FOUND")

if hasattr(viewset, 'test_connection'):
    print("  ✓ test_connection method exists")
else:
    print("  ✗ test_connection method NOT FOUND")
