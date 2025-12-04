#!/usr/bin/env python
"""Find which api_views.py file is actually being imported"""
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

import subscriptions.api_views
print(f"Imported from: {subscriptions.api_views.__file__}")

# Count lines in the imported file
with open(subscriptions.api_views.__file__, 'r') as f:
    lines = f.readlines()
    print(f"Total lines in imported file: {len(lines)}")

# Check if discover_chats exists in the file
has_discover = any('def discover_chats' in line for line in lines)
print(f"Contains 'def discover_chats': {has_discover}")

# Find the line number
for i, line in enumerate(lines, 1):
    if 'def discover_chats' in line:
        print(f"Found at line: {i}")
        print(f"Context: {lines[i-2:i+3]}")
        break
