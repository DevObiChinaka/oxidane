"""
Test script to debug Telegram sync issues
Run this to verify bot token and group chat ID
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration, TelegramGroup
import requests

def test_telegram_sync():
    print("=" * 60)
    print("TELEGRAM SYNC DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Get config
    try:
        config = TelegramConfiguration.get_instance()
        print(f"\n✅ Configuration found")
        print(f"   - Bot username: {config.bot_username}")
        print(f"   - Is connected: {config.is_connected}")
        print(f"   - Is enabled: {config.is_enabled}")
        print(f"   - Has bot token: {'Yes' if config.bot_token else 'No'}")
        
        if not config.bot_token:
            print("\n❌ ERROR: Bot token is not configured!")
            print("   Please configure the bot token in the admin panel first.")
            return
        
        # Try to decrypt token
        try:
            bot_token = config.decrypt_field('bot_token')
            print(f"   - Token length: {len(bot_token)} characters")
            print(f"   - Token format: {'✅ Valid' if ':' in bot_token else '❌ Invalid'}")
        except Exception as e:
            print(f"\n❌ ERROR decrypting token: {e}")
            return
            
    except Exception as e:
        print(f"\n❌ ERROR: Could not load configuration: {e}")
        return
    
    # Get groups
    groups = TelegramGroup.objects.all()
    print(f"\n📊 Found {groups.count()} groups:")
    
    for group in groups:
        print(f"\n   Group: {group.name}")
        print(f"   - Chat ID: {group.chat_id}")
        print(f"   - Current member count: {group.member_count}")
        print(f"   - Is active: {group.is_active}")
        
        # Test sync for this group
        print(f"\n   Testing Telegram API connection...")
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMemberCount"
            print(f"   - API URL: {url[:50]}...")
            print(f"   - Sending chat_id: {group.chat_id}")
            
            response = requests.post(
                url,
                json={'chat_id': group.chat_id},
                timeout=10
            )
            
            print(f"   - Response status: {response.status_code}")
            data = response.json()
            print(f"   - Response data: {data}")
            
            if response.status_code == 200 and data.get('ok'):
                member_count = data['result']
                print(f"\n   ✅ SUCCESS! Current member count: {member_count}")
                print(f"   - Difference: {member_count - group.member_count}")
            elif response.status_code == 401:
                print(f"\n   ❌ ERROR: Invalid bot token (401 Unauthorized)")
                print(f"   - The bot token is invalid or expired")
            elif response.status_code == 403:
                print(f"\n   ❌ ERROR: Bot lacks permissions (403 Forbidden)")
                print(f"   - Bot may have been removed from the group")
                print(f"   - Or bot doesn't have required permissions")
            elif response.status_code == 400:
                error_desc = data.get('description', 'Unknown error')
                print(f"\n   ❌ ERROR: Bad Request (400)")
                print(f"   - Error: {error_desc}")
                if 'chat not found' in error_desc.lower():
                    print(f"   - The chat_id might be incorrect")
                    print(f"   - Or the bot is not a member of this group")
            else:
                print(f"\n   ❌ ERROR: Unexpected status {response.status_code}")
                print(f"   - Response: {data}")
                
        except requests.exceptions.Timeout:
            print(f"\n   ❌ ERROR: Connection timeout")
            print(f"   - The Telegram API took too long to respond")
            print(f"   - Check your internet connection")
        except requests.exceptions.RequestException as e:
            print(f"\n   ❌ ERROR: Request failed")
            print(f"   - {str(e)}")
        except Exception as e:
            print(f"\n   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_telegram_sync()
