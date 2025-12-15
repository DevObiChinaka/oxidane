"""
Check current exchange rates in the database
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import ExchangeRate
from django.utils import timezone
from datetime import timedelta

def check_exchange_rates():
    """Check all exchange rates and their last update times."""
    print("\n" + "="*80)
    print("EXCHANGE RATE STATUS")
    print("="*80 + "\n")
    
    # Get all exchange rates
    rates = ExchangeRate.objects.all().order_by('base_currency', 'target_currency')
    
    if not rates.exists():
        print("❌ NO EXCHANGE RATES FOUND IN DATABASE")
        print("\nTo add exchange rates, run:")
        print("  python manage.py update_exchange_rates")
        return
    
    print(f"Total Exchange Rates: {rates.count()}\n")
    
    now = timezone.now()
    
    # Group by base currency
    base_currencies = {}
    for rate in rates:
        if rate.base_currency not in base_currencies:
            base_currencies[rate.base_currency] = []
        base_currencies[rate.base_currency].append(rate)
    
    # Display rates grouped by base currency
    for base, rate_list in base_currencies.items():
        print(f"\n📊 Base Currency: {base}")
        print("-" * 80)
        
        for rate in rate_list:
            age = now - rate.last_updated
            age_str = format_timedelta(age)
            
            # Determine freshness status
            if age > timedelta(days=7):
                status = "⚠️  STALE"
            elif age > timedelta(days=1):
                status = "⚡ OLD"
            else:
                status = "✅ FRESH"
            
            print(f"  {status}  1 {rate.base_currency} = {rate.rate:,.6f} {rate.target_currency}")
            print(f"           Last Updated: {rate.last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')} ({age_str} ago)")
            print()
    
    # Summary
    print("\n" + "="*80)
    print("FRESHNESS SUMMARY")
    print("="*80 + "\n")
    
    stale = rates.filter(last_updated__lt=now - timedelta(days=7)).count()
    old = rates.filter(
        last_updated__lt=now - timedelta(days=1),
        last_updated__gte=now - timedelta(days=7)
    ).count()
    fresh = rates.filter(last_updated__gte=now - timedelta(days=1)).count()
    
    print(f"✅ Fresh (< 1 day old):    {fresh}")
    print(f"⚡ Old (1-7 days old):     {old}")
    print(f"⚠️  Stale (> 7 days old):  {stale}")
    
    if stale > 0 or old > 0:
        print("\n⚠️  RECOMMENDATION: Update exchange rates")
        print("   Run: python manage.py update_exchange_rates")
    else:
        print("\n✅ All exchange rates are fresh!")

def format_timedelta(td):
    """Format timedelta in human-readable form."""
    total_seconds = int(td.total_seconds())
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if days > 0:
        if days == 1:
            return f"{days} day, {hours} hours"
        return f"{days} days, {hours} hours"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"

if __name__ == "__main__":
    check_exchange_rates()
