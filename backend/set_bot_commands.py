#!/usr/bin/env python3
"""
Set Bot Commands via Telegram API
This script registers bot commands so they appear in Telegram's autocomplete menu
"""

import os
import sys
import django
import requests

# Setup Django
sys.path.append('C:/Users/user/OneDrive/Desktop/Oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings

def set_bot_commands():
    """Set bot commands via Telegram API"""
    
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    # Define commands
    commands = [
        {"command": "start", "description": "Welcome message and introduction"},
        {"command": "verify", "description": "Link your Telegram account (use: /verify CODE)"},
        {"command": "status", "description": "Check your subscription and group access"},
        {"command": "help", "description": "Show all available commands"},
        {"command": "support", "description": "Get support contact information"},
    ]
    
    # First, delete existing commands to clear cache
    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteMyCommands"
    delete_response = requests.post(delete_url)
    
    if delete_response.status_code == 200:
        print("✅ Old commands cleared")
    
    # Wait a moment
    import time
    time.sleep(1)
    
    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
    
    # Send request
    response = requests.post(url, json={"commands": commands})
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("✅ Commands successfully registered!")
            print("\nRegistered commands:")
            for cmd in commands:
                print(f"  /{cmd['command']} - {cmd['description']}")
            print("\n🎉 Users will now see commands in autocomplete menu when they type '/'")
        else:
            print(f"❌ Error: {result.get('description', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    print("=" * 60)
    print("TELEGRAM BOT COMMANDS SETUP")
    print("=" * 60)
    print("\nSetting up bot commands for autocomplete menu...\n")
    
    set_bot_commands()
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print("\n📱 Test it:")
    print("1. Open your bot in Telegram")
    print("2. Type '/' (forward slash)")
    print("3. You should see all commands in the menu\n")
