#!/usr/bin/env python
"""Debug script to inspect TelegramConfigurationViewSet"""
import os
import sys
import django

# Set up Django environment
sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.api_views import TelegramConfigurationViewSet
import inspect

print("=" * 80)
print("TelegramConfigurationViewSet Method Inspection")
print("=" * 80)

# Get all methods
all_methods = inspect.getmembers(TelegramConfigurationViewSet, predicate=inspect.isfunction)

print(f"\n✓ Total methods found: {len(all_methods)}\n")

# Look for our specific methods
target_methods = ['test_connection', 'discover_chats', 'list', 'retrieve', 'create', 'update']

for method_name in target_methods:
    if hasattr(TelegramConfigurationViewSet, method_name):
        method = getattr(TelegramConfigurationViewSet, method_name)
        print(f"✓ {method_name}: EXISTS")
        
        # Check for @action decorator
        if hasattr(method, 'mapping'):
            print(f"    - @action decorator: YES")
            print(f"    - mapping: {method.mapping}")
        if hasattr(method, 'detail'):
            print(f"    - detail: {method.detail}")
        if hasattr(method, 'url_path'):
            print(f"    - url_path: {method.url_path}")
    else:
        print(f"✗ {method_name}: NOT FOUND")

print("\n" + "=" * 80)
print("All methods in class:")
print("=" * 80)
for name, method in all_methods:
    if not name.startswith('_'):
        print(f"  - {name}")
