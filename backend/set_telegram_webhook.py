#!/usr/bin/env python
"""Set Telegram webhook URL"""
import os
import sys
import django
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings

def set_webhook(public_url):
    """Set the webhook URL for Telegram bot"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    # Construct webhook URL
    webhook_url = f"{public_url}/api/telegram/webhook/"
    
    print("=" * 70)
    print("  SETTING TELEGRAM WEBHOOK")
    print("=" * 70)
    print()
    print(f"Bot Token: {bot_token[:10]}***")
    print(f"Webhook URL: {webhook_url}")
    print()
    
    # Set webhook
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = {
        'url': webhook_url,
        'allowed_updates': ['message', 'chat_join_request', 'my_chat_member']
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("✅ Webhook set successfully!")
            print()
            print("Test it:")
            print("1. Send a message to your bot on Telegram")
            print("2. Send /verify <CODE> to test verification")
            print()
        else:
            print(f"❌ Error: {result.get('description')}")
    else:
        print(f"❌ HTTP Error {response.status_code}")
        print(response.text)
    
    print("=" * 70)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python set_telegram_webhook.py <public-url>")
        print()
        print("Example:")
        print("  python set_telegram_webhook.py https://abc123.ngrok-free.app")
        print()
        print("For local testing, use ngrok:")
        print("  1. Run: ngrok http 8000")
        print("  2. Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)")
        print("  3. Run this script with that URL")
        sys.exit(1)
    
    public_url = sys.argv[1].rstrip('/')
    set_webhook(public_url)
