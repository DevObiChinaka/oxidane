#!/usr/bin/env python
"""Check v1_router generated URLs"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions import urls as sub_urls

print("\n=== v1_router URL patterns ===\n")
for pattern in sub_urls.v1_router.urls:
    print(f"  {pattern.pattern} -> {pattern.name}")
