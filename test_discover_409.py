#!/usr/bin/env python
"""Simulate the discover_chats API call"""
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration, TelegramGroup
import requests

config = TelegramConfiguration.get_instance()

try:
    # Get decrypted bot token
    bot_token = config.decrypt_field('bot_token')
    
    # Get recent updates from bot
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, timeout=10)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 409:
        print("\n409 Conflict - Webhook is active")
        print("Attempting to get existing groups from database...")
        
        # This is the code that's failing
        existing_groups = TelegramGroup.objects.all().values(
            'id', 'chat_id', 'name', 'group_type', 'member_count'
        )
        
        print(f"Found {len(existing_groups)} groups in database")
        
        chats_list = [
            {
                'chat_id': str(group['chat_id']),
                'title': group['name'],
                'type': group['group_type'],
                'username': '',
                'member_count': group['member_count']
            }
            for group in existing_groups if group['chat_id']
        ]
        
        print(f"Formatted {len(chats_list)} chats")
        print(f"Result: {chats_list}")
        
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
