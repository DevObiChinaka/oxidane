#!/usr/bin/env python
"""
Test Live Exchange Rates with open.er-api.com

Tests that the updated ExchangeRateService correctly fetches
live rates from open.er-api.com API.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.services import ExchangeRateService
from decimal import Decimal


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def test_api_connection():
    """Test 1: API Connection"""
    print_header("TEST 1: Testing API Connection to open.er-api.com")
    
    try:
        service = ExchangeRateService()
        print(f"✓ Service initialized with base currency: {service.base_currency}")
        print(f"✓ API URL: {service.EXCHANGERATE_API_URL}")
        print(f"✓ Cache duration: {service.CACHE_DURATION_HOURS} hour(s)")
        
        return service
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return None


def test_fetch_rates(service):
    """Test 2: Fetch Live Rates"""
    print_header("TEST 2: Fetching Live Exchange Rates")
    
    try:
        print("Fetching rates for USD from open.er-api.com...")
        rates = service.fetch_rates_from_exchangerate_api('USD')
        
        print(f"✓ Successfully fetched {len(rates)} currency rates")
        
        # Check for NGN specifically
        if 'NGN' in rates:
            print(f"✓ NGN rate found: 1 USD = {rates['NGN']} NGN")
        else:
            print(f"❌ NGN rate not found in response")
            return False
        
        # Show some sample rates
        print("\nSample rates (USD base):")
        sample_currencies = ['NGN', 'EUR', 'GBP', 'CAD', 'AUD']
        for curr in sample_currencies:
            if curr in rates:
                print(f"   {curr}: {rates[curr]}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to fetch rates: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_database(service):
    """Test 3: Update Database with Live Rates"""
    print_header("TEST 3: Updating Database with Live Rates")
    
    try:
        print("Fetching and updating rates...")
        success = service.fetch_and_update_rates(force_update=True)
        
        if success:
            print("✓ Database updated successfully")
            
            # Check USD → NGN rate in database
            from subscriptions.models import ExchangeRate
            ngn_rate = ExchangeRate.objects.filter(
                base_currency='USD',
                target_currency='NGN'
            ).first()
            
            if ngn_rate:
                print(f"\n✓ Database check:")
                print(f"   Rate: 1 USD = {ngn_rate.rate} NGN")
                print(f"   Last Updated: {ngn_rate.last_updated}")
                # Note: Rate is fresh (just updated)
            else:
                print("⚠️  USD→NGN rate not found in database")
                return False
            
            return True
        else:
            print("❌ Failed to update database")
            return False
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_amount(service):
    """Test 4: Convert USD to NGN"""
    print_header("TEST 4: Testing Currency Conversion")
    
    try:
        # Test conversion of typical subscription amounts
        test_amounts = [30, 50, 100]
        
        for usd_amount in test_amounts:
            ngn_amount = service.convert_amount(
                amount=Decimal(str(usd_amount)),
                from_currency='USD',
                to_currency='NGN'
            )
            
            if ngn_amount:
                print(f"✓ ${usd_amount} USD = ₦{ngn_amount:,.2f} NGN")
            else:
                print(f"❌ Failed to convert ${usd_amount}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*70)
    print("  LIVE EXCHANGE RATES TEST - open.er-api.com")
    print("="*70)
    
    # Run tests
    results = []
    
    # Test 1
    service = test_api_connection()
    results.append(('API Connection', service is not None))
    
    if not service:
        print("\n❌ Cannot proceed without service initialization")
        return False
    
    # Test 2
    success = test_fetch_rates(service)
    results.append(('Fetch Live Rates', success))
    
    # Test 3
    success = test_update_database(service)
    results.append(('Update Database', success))
    
    # Test 4
    success = test_convert_amount(service)
    results.append(('Currency Conversion', success))
    
    # Summary
    print_header("TEST SUMMARY")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests passed! Live rates are working with open.er-api.com")
        print("\nNext steps:")
        print("1. Rates will auto-update every hour via smart caching")
        print("2. Frontend can now fetch live conversion rates")
        print("3. Checkout page will display accurate NGN prices")
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
    
    return passed_count == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
