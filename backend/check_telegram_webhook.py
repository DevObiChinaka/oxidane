#!/usr/bin/env python
"""Check current Telegram webhook status"""
import os
import sys
import django
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings

def check_webhook():
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    # Get webhook info
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            info = data.get('result', {})
            print("=" * 70)
            print("  TELEGRAM WEBHOOK STATUS")
            print("=" * 70)
            print()
            print(f"URL: {info.get('url', 'NOT SET')}")
            print(f"Has Custom Certificate: {info.get('has_custom_certificate', False)}")
            print(f"Pending Update Count: {info.get('pending_update_count', 0)}")
            print(f"Last Error Date: {info.get('last_error_date', 'None')}")
            print(f"Last Error Message: {info.get('last_error_message', 'None')}")
            print(f"Max Connections: {info.get('max_connections', 40)}")
            print(f"Allowed Updates: {info.get('allowed_updates', [])}")
            print()
            
            if not info.get('url'):
                print("⚠️  Webhook is NOT set!")
                print("   The bot will not receive messages.")
                print()
                print("To set webhook, you need:")
                print("1. A public URL (use ngrok for local testing)")
                print("2. Run: python set_telegram_webhook.py <your-public-url>")
            else:
                print("✅ Webhook is configured")
                if info.get('last_error_message'):
                    print(f"⚠️  Last error: {info.get('last_error_message')}")
            
            print()
            print("=" * 70)
        else:
            print(f"Error: {data}")
    else:
        print(f"HTTP Error {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    check_webhook()
