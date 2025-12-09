import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration
import requests
import json

config = TelegramConfiguration.get_instance()
if not config.has_valid_token():
    print("No valid bot token configured")
    sys.exit(1)

bot_token = config.decrypt_field('bot_token')
response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
data = response.json()

print("="*60)
print("TELEGRAM WEBHOOK STATUS")
print("="*60)
print(json.dumps(data, indent=2))
print("="*60)

if data.get('result', {}).get('url'):
    print(f"\n✅ Webhook is SET: {data['result']['url']}")
    print("\n⚠️  This means polling won't work! Telegram sends updates to webhook only.")
else:
    print("\n✅ No webhook set - polling mode active")
    print("\n✅ Celery Beat task handles updates every 30 seconds")
