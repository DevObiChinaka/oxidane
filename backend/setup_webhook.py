#!/usr/bin/env python
"""
Setup Telegram Webhook
Configure Telegram to send updates to your backend
"""
import os
import sys
import django
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings

def setup_webhook(webhook_url):
    """Set Telegram webhook URL"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    # Full webhook URL
    full_url = f"{webhook_url}/api/telegram/webhook/"
    
    print(f"Setting webhook to: {full_url}")
    
    # Set webhook
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    response = requests.post(api_url, json={
        'url': full_url,
        'allowed_updates': ['message', 'chat_join_request', 'chat_member'],
        'drop_pending_updates': True  # Clear old pending updates
    })
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("✅ Webhook set successfully!")
            print(f"\nTelegram will now send updates to:")
            print(f"  {full_url}")
            print("\n✅ The /verify command will work now!")
        else:
            print(f"❌ Error: {result.get('description')}")
    else:
        print(f"❌ HTTP Error {response.status_code}")
        print(response.text)
    
    # Get webhook info to verify
    info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    info_response = requests.get(info_url)
    
    if info_response.status_code == 200:
        info = info_response.json().get('result', {})
        print("\n📊 Current Webhook Status:")
        print(f"  URL: {info.get('url', 'Not set')}")
        print(f"  Pending updates: {info.get('pending_update_count', 0)}")
        if info.get('last_error_message'):
            print(f"  ⚠️  Last error: {info.get('last_error_message')}")

if __name__ == '__main__':
    print("=" * 70)
    print("  TELEGRAM WEBHOOK SETUP")
    print("=" * 70)
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python setup_webhook.py <webhook_url>")
        print("\nExamples:")
        print("  python setup_webhook.py https://abc123.ngrok.io")
        print("  python setup_webhook.py https://yourdomain.com")
        print("\n💡 For local testing:")
        print("  1. Run: ngrok http 8000")
        print("  2. Copy the ngrok URL (e.g., https://abc123.ngrok.io)")
        print("  3. Run: python setup_webhook.py https://abc123.ngrok.io")
        sys.exit(1)
    
    webhook_url = sys.argv[1].rstrip('/')
    
    print(f"Backend URL: {webhook_url}")
    print()
    
    setup_webhook(webhook_url)
    
    print("\n" + "=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print()
    print("1. Make sure your backend is running:")
    print("   python manage.py runserver 0.0.0.0:8000")
    print()
    print("2. If using ngrok, make sure it's still running:")
    print("   ngrok http 8000")
    print()
    print("3. Test the bot:")
    print("   - Send: /verify YOUR-CODE")
    print("   - Bot should respond with verification result")
    print()
