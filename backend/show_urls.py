#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.urls import get_resolver
from django.conf import settings

def show_urls(urllist, depth=0):
    for entry in urllist:
        print("  " * depth + f"{entry.pattern}")
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

if __name__ == '__main__':
    print("Available URL patterns:")
    resolver = get_resolver(settings.ROOT_URLCONF)
    show_urls(resolver.url_patterns)