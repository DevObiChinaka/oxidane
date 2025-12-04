#!/usr/bin/env python
"""Set production webhook URL for Telegram bot"""
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration
import requests

config = TelegramConfiguration.get_instance()
bot_token = config.decrypt_field('bot_token')

# Production webhook URL (using your API domain)
webhook_url = "https://api.oxiworldforexacademy.com/api/telegram/webhook/"

print(f"Setting webhook to: {webhook_url}")

# Set webhook
url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
response = requests.post(url, json={'url': webhook_url}, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data.get('ok'):
        print("✓ Webhook set successfully!")
        print(f"  Description: {data.get('description', 'N/A')}")
        
        # Verify webhook
        verify_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        verify_response = requests.get(verify_url, timeout=10)
        
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            if verify_data.get('ok'):
                webhook_info = verify_data.get('result', {})
                print("\nWebhook Info:")
                print(f"  URL: {webhook_info.get('url')}")
                print(f"  Pending updates: {webhook_info.get('pending_update_count', 0)}")
                print(f"  Last error: {webhook_info.get('last_error_message', 'None')}")
    else:
        print(f"✗ Failed: {data.get('description', 'Unknown error')}")
else:
    print(f"✗ HTTP {response.status_code}: {response.text}")
