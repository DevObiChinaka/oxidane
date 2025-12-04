#!/usr/bin/env python
"""Check and optionally delete Telegram webhook"""
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

# Get webhook info
url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data.get('ok'):
        webhook_info = data.get('result', {})
        print("Current Webhook Info:")
        print(f"  URL: {webhook_info.get('url', '(none)')}")
        print(f"  Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
        print(f"  Pending update count: {webhook_info.get('pending_update_count', 0)}")
        print(f"  Max connections: {webhook_info.get('max_connections', 0)}")
        
        if webhook_info.get('url'):
            print("\n⚠️  Webhook is active. To discover groups, you need to:")
            print("  1. Temporarily delete webhook: python delete_webhook.py")
            print("  2. Use discover-chats button")
            print("  3. Re-enable webhook after discovery")
        else:
            print("\n✓ No webhook configured. You can use discover-chats now.")
