"""Test if my-subscriptions URL is accessible"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Try to resolve the URL
try:
    url = '/api/subscriptions/my-subscriptions/'
    resolved = resolve(url)
    print(f"✅ URL resolved: {url}")
    print(f"   View: {resolved.func}")
    print(f"   View name: {resolved.view_name}")
    print(f"   URL name: {resolved.url_name}")
except Exception as e:
    print(f"❌ URL NOT resolved: {url}")
    print(f"   Error: {e}")

# Try reverse lookup
try:
    reversed_url = reverse('subscriptions:my-subscriptions')
    print(f"\n✅ Reverse lookup successful: {reversed_url}")
except Exception as e:
    print(f"\n❌ Reverse lookup failed")
    print(f"   Error: {e}")

# List all subscription-related URLs
print("\n=== All registered subscription URLs ===")
from django.urls import get_resolver
resolver = get_resolver()

def show_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # It's an included URLconf
            show_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            # It's a URL pattern
            route = prefix + str(pattern.pattern)
            if 'subscription' in route.lower() or 'my-' in route.lower():
                print(f"  {route}")

show_urls(resolver.url_patterns)
