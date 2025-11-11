"""
Get Your Telegram User ID

This script helps you get your Telegram user ID which is required for testing.

Method 1: Using @userinfobot
1. Open Telegram
2. Search for @userinfobot
3. Send /start
4. Bot will reply with your user ID

Method 2: Using @raw_data_bot
1. Open Telegram
2. Search for @raw_data_bot
3. Send any message
4. Bot will reply with JSON containing your user ID

Method 3: Using our bot (if configured)
Run this script to create a simple endpoint to get your ID.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration
import requests


def get_telegram_updates():
    """Get recent updates from Telegram bot to find user ID"""
    try:
        config = TelegramConfiguration.get_instance()
        
        if not config.has_valid_token():
            print("❌ Telegram bot token is not configured or invalid")
            print("\nPlease configure your bot token in Django admin:")
            print("  1. Go to Admin > Telegram Configuration")
            print("  2. Add your bot token")
            print("  3. Run this script again")
            return
        
        bot_token = config.bot_token
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"\n✅ Bot Connected: @{bot_info['username']}")
            print(f"Bot Name: {bot_info['first_name']}")
            print(f"Bot ID: {bot_info['id']}")
            
            # Get updates
            updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            updates_response = requests.get(updates_url, timeout=10)
            updates_data = updates_response.json()
            
            if updates_data.get('ok'):
                updates = updates_data['result']
                
                if updates:
                    print(f"\n📬 Found {len(updates)} recent messages")
                    print("\nRecent users who messaged the bot:")
                    print("-" * 60)
                    
                    seen_users = {}
                    for update in updates:
                        if 'message' in update:
                            user = update['message']['from']
                            user_id = user['id']
                            
                            if user_id not in seen_users:
                                username = user.get('username', 'No username')
                                first_name = user.get('first_name', '')
                                last_name = user.get('last_name', '')
                                full_name = f"{first_name} {last_name}".strip()
                                
                                print(f"\nUser ID: {user_id}")
                                print(f"Username: @{username}")
                                print(f"Name: {full_name}")
                                
                                seen_users[user_id] = {
                                    'username': username,
                                    'name': full_name
                                }
                    
                    if seen_users:
                        print("\n" + "=" * 60)
                        print("\n💡 To test with your account:")
                        print("1. Find your user ID above")
                        print("2. Run the test script:")
                        print("\n   python test_telegram_auto_add.py --user-id YOUR_ID --username YOUR_USERNAME")
                        print("\nExample:")
                        for user_id, info in list(seen_users.items())[:1]:
                            print(f"   python test_telegram_auto_add.py --user-id {user_id} --username {info['username']}")
                else:
                    print("\n⚠️  No recent messages found")
                    print("\nTo get your user ID:")
                    print(f"1. Open Telegram and search for @{bot_info['username']}")
                    print("2. Send /start to the bot")
                    print("3. Run this script again")
                    print("\nOR use @userinfobot:")
                    print("1. Search for @userinfobot in Telegram")
                    print("2. Send /start")
                    print("3. Bot will reply with your user ID")
            else:
                print(f"❌ Failed to get updates: {updates_data.get('description')}")
        
        else:
            print(f"❌ Bot error: {data.get('description')}")
            print("\nPlease check your bot token is correct")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("=" * 60)
    print("  GET YOUR TELEGRAM USER ID")
    print("=" * 60)
    
    get_telegram_updates()
    
    print("\n" + "=" * 60)
    print("\n📱 Alternative Methods:")
    print("\nMethod 1: @userinfobot")
    print("  1. Open Telegram")
    print("  2. Search for @userinfobot")
    print("  3. Send /start")
    print("  4. Copy your user ID")
    
    print("\nMethod 2: @raw_data_bot")
    print("  1. Open Telegram")
    print("  2. Search for @raw_data_bot")
    print("  3. Send any message")
    print("  4. Find 'id' in the JSON response")
    
    print("\n" + "=" * 60)
