#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache
import requests

# Check current offset
current_offset = cache.get('telegram_bot_update_offset', 0)
print(f"Current cached offset: {current_offset}")

# Get the latest update ID from Telegram
from subscriptions.models import TelegramConfiguration
from cryptography.fernet import Fernet
from django.conf import settings

config = TelegramConfiguration.objects.first()
if config and config.bot_token:
    # Decrypt token
    cipher = Fernet(settings.TELEGRAM_ENCRYPTION_KEY.encode())
    bot_token = cipher.decrypt(config.bot_token.encode()).decode()
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, params={'offset': -1, 'limit': 1})
    if response.status_code == 200:
        data = response.json()
        if data.get('ok') and data.get('result'):
            latest_update = data['result'][-1]
            latest_update_id = latest_update['update_id']
            print(f"Latest update ID from Telegram: {latest_update_id}")
            
            # Set offset to skip all messages
            new_offset = latest_update_id + 1
            cache.set('telegram_bot_update_offset', new_offset, timeout=None)
            print(f"Set new offset to: {new_offset}")
        else:
            print("No updates available")
    else:
        print(f"API request failed: {response.status_code}")
