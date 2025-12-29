import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
import django
django.setup()
from subscriptions.models import ExchangeRate
rates = ExchangeRate.objects.all().order_by('-updated_at')[:5]
for r in rates:
    print(f'{r.from_currency}/{r.to_currency}: {r.rate} - Updated: {r.updated_at}')
