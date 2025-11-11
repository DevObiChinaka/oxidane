#!/usr/bin/env python
"""Check URL patterns"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.urls import get_resolver

resolver = get_resolver()

print("\n=== All URL Patterns containing 'currency' ===\n")
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'api' in pattern_str or hasattr(pattern, 'url_patterns'):
        if hasattr(pattern, 'url_patterns'):
            for sub_pattern in pattern.url_patterns:
                sub_str = str(sub_pattern.pattern)
                full_pattern = pattern_str + sub_str
                if 'currency' in full_pattern.lower() or 'v1' in full_pattern:
                    print(f"  {full_pattern}")

print("\n=== Checking subscriptions URLs directly ===\n")
from subscriptions import urls as sub_urls
print(f"v1_router registered: {hasattr(sub_urls, 'v1_router')}")
if hasattr(sub_urls, 'v1_router'):
    print(f"v1_router.registry: {sub_urls.v1_router.registry}")
