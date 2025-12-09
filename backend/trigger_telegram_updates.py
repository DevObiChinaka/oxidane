import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import process_telegram_updates

print("Triggering Telegram update processing...")
result = process_telegram_updates()
print(f"\nResult: {result}")
