#!/usr/bin/env python
"""Test discover_chats functionality directly"""
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration
import requests

config = TelegramConfiguration.get_instance()
print(f"Token exists: {bool(config.bot_token)}")

if not config.bot_token:
    print("ERROR: No bot token configured")
    sys.exit(1)

try:
    # Get decrypted bot token
    bot_token = config.decrypt_field('bot_token')
    print(f"Decrypted token: {bot_token[:15]}...{bot_token[-10:]}")
    
    # Get recent updates from bot
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    print(f"\nCalling: {url[:60]}...")
    
    response = requests.get(url, timeout=10)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"\n✓ SUCCESS: Got {len(updates)} updates")
        else:
            print(f"\n✗ FAILED: {data.get('description', 'Unknown error')}")
    else:
        print(f"\n✗ HTTP {response.status_code}")
        
except Exception as e:
    print(f"\n✗ EXCEPTION: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
