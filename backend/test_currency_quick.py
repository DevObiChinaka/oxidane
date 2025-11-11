#!/usr/bin/env python
"""Quick test of currency API with trailing slash"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.test import Client
from django.conf import settings

# Add testserver to ALLOWED_HOSTS
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

client = Client()

print("\n=== Test 1: /api/v1/currency/ (list) ===")
response = client.get('/api/v1/currency/')
print(f"Status: {response.status_code}")
if response.status_code != 404:
    print(f"Response: {response.content.decode()[:500]}")

print("\n=== Test 2: /api/v1/currency/convert/ ===")
response = client.get('/api/v1/currency/convert/', {'from': 'USD', 'to': 'NGN', 'amount': '30'})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"✓ SUCCESS!")
    print(f"  $30 USD = ₦{data['to_amount']:,.2f} NGN")
    print(f"  Rate: {data['exchange_rate']}")
else:
    print(f"✗ FAILED")
    print(f"Response: {response.content.decode()[:500]}")

print("\n=== Test 3: /api/v1/currency/rates/ ===")
response = client.get('/api/v1/currency/rates/', {'base': 'USD'})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"✓ SUCCESS!")
    print(f"  Currencies: {data['count']}")
    print(f"  Sample rates: NGN={data['rates'].get('NGN', 'N/A')}, EUR={data['rates'].get('EUR', 'N/A')}")
else:
    print(f"✗ FAILED")
    print(f"Response: {response.content.decode()[:500]}")
