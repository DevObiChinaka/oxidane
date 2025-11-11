#!/usr/bin/env python
"""
Test Currency Conversion API Endpoint

Tests the new /api/v1/currency/convert/ endpoint
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.test import Client
from django.conf import settings
import json

# Add testserver to ALLOWED_HOSTS for Django test client
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def test_convert_endpoint():
    """Test GET /api/v1/currency/convert/"""
    print_header("TEST 1: Convert Currency Endpoint")
    
    client = Client()
    
    # Test 1: USD to NGN
    print("\n1. Convert $30 USD to NGN:")
    response = client.get('/api/v1/currency/convert/?from=USD&to=NGN&amount=30')
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response:")
        print(f"      From: ${data['from_amount']} {data['from_currency']}")
        print(f"      To: ₦{data['to_amount']:,.2f} {data['to_currency']}")
        print(f"      Rate: 1 USD = ₦{data['exchange_rate']:,.4f}")
        print(f"      Cached: {data['cached']}")
        print(f"      ✓ SUCCESS")
    else:
        print(f"   ✗ FAILED: {response.content.decode()}")
        return False
    
    # Test 2: USD to EUR
    print("\n2. Convert $100 USD to EUR:")
    response = client.get('/api/v1/currency/convert/?from=USD&to=EUR&amount=100')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ${data['from_amount']} USD = €{data['to_amount']:.2f} EUR")
        print(f"   Rate: {data['exchange_rate']}")
        print(f"   ✓ SUCCESS")
    else:
        print(f"   ✗ FAILED")
        return False
    
    # Test 3: Same currency
    print("\n3. Convert USD to USD (same currency):")
    response = client.get('/api/v1/currency/convert/?from=USD&to=USD&amount=50')
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ${data['from_amount']} USD = ${data['to_amount']} USD")
        print(f"   Rate: {data['exchange_rate']} (expected: 1.0)")
        print(f"   ✓ SUCCESS")
    else:
        print(f"   ✗ FAILED")
        return False
    
    # Test 4: Invalid currency code
    print("\n4. Test invalid currency code:")
    response = client.get('/api/v1/currency/convert/?from=INVALID&to=NGN&amount=10')
    
    print(f"   Status: {response.status_code} (expected: 400)")
    if response.status_code == 400:
        data = response.json()
        print(f"   Error: {data.get('error')}")
        print(f"   ✓ SUCCESS (correctly rejected)")
    else:
        print(f"   ✗ FAILED")
        return False
    
    return True


def test_rates_endpoint():
    """Test GET /api/v1/currency/rates/"""
    print_header("TEST 2: Get All Rates Endpoint")
    
    client = Client()
    
    # Test 1: Get all USD rates
    print("\n1. Get all rates for USD:")
    response = client.get('/api/v1/currency/rates/?base=USD')
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Base Currency: {data['base_currency']}")
        print(f"   Total Rates: {data['count']}")
        print(f"   Last Updated: {data['last_updated']}")
        
        # Show sample rates
        print(f"\n   Sample Rates:")
        sample_currencies = ['NGN', 'EUR', 'GBP', 'CAD', 'JPY']
        for curr in sample_currencies:
            if curr in data['rates']:
                print(f"      {curr}: {data['rates'][curr]}")
        
        print(f"   ✓ SUCCESS")
    else:
        print(f"   ✗ FAILED: {response.content.decode()}")
        return False
    
    return True


def main():
    print("\n" + "="*70)
    print("  CURRENCY CONVERSION API TEST")
    print("="*70)
    
    results = []
    
    # Test 1: Convert endpoint
    results.append(('Convert Endpoint', test_convert_endpoint()))
    
    # Test 2: Rates endpoint
    results.append(('Rates Endpoint', test_rates_endpoint()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All API tests passed!")
        print("\nEndpoint URLs:")
        print("  Convert: GET /api/v1/currency/convert/?from=USD&to=NGN&amount=30")
        print("  Rates:   GET /api/v1/currency/rates/?base=USD")
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
    
    return passed_count == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
