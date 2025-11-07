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

def get_bot_updates(bot_token):
    """Get recent updates from the bot to find the correct chat ID"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"\n📬 Found {len(updates)} recent updates/messages")
                
                chat_ids = set()
                for update in updates:
                    # Check different message types
                    for msg_type in ['message', 'edited_message', 'channel_post', 'my_chat_member']:
                        if msg_type in update:
                            msg = update[msg_type]
                            if 'chat' in msg:
                                chat = msg['chat']
                                chat_id = chat.get('id')
                                chat_title = chat.get('title', 'Unknown')
                                chat_type = chat.get('type', 'unknown')
                                
                                if chat_id and chat_id < 0:  # Only show groups/supergroups
                                    chat_ids.add((chat_id, chat_title, chat_type))
                
                if chat_ids:
                    print("\n🔍 Found these groups/supergroups:")
                    for chat_id, title, chat_type in sorted(chat_ids):
                        print(f"   - {title}")
                        print(f"     Chat ID: {chat_id}")
                        print(f"     Type: {chat_type}")
                        print()
                    return chat_ids
                else:
                    print("\n⚠️  No group messages found in recent updates")
                    print("   Send a message in the TradeHub group to update the bot")
            else:
                print(f"\n❌ Bot API error: {data}")
        else:
            print(f"\n❌ Failed to get updates: HTTP {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error getting updates: {e}")
    
    return set()

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
    
    # Get recent bot updates to find correct chat IDs
    print("\n" + "=" * 60)
    print("CHECKING BOT UPDATES FOR CORRECT CHAT IDs")
    print("=" * 60)
    found_chats = get_bot_updates(bot_token)
    
    # Get groups
    groups = TelegramGroup.objects.all()
    print("\n" + "=" * 60)
    print(f"TESTING {groups.count()} CONFIGURED GROUPS")
    print("=" * 60)
    
    for group in groups:
        print(f"\n   Group: {group.name}")
        print(f"   - Configured Chat ID: {group.chat_id}")
        print(f"   - Current member count: {group.member_count}")
        print(f"   - Is active: {group.is_active}")
        
        # Check if this chat ID matches any found chats
        matching_chat = None
        for chat_id, title, chat_type in found_chats:
            if str(chat_id) == group.chat_id or title.lower() == group.name.lower():
                matching_chat = (chat_id, title, chat_type)
                break
        
        if matching_chat and str(matching_chat[0]) != group.chat_id:
            print(f"\n   ⚠️  CHAT ID MISMATCH DETECTED!")
            print(f"   - Configured: {group.chat_id}")
            print(f"   - Actual: {matching_chat[0]}")
            print(f"   - The group may have been upgraded to a supergroup")
            print(f"\n   💡 RECOMMENDATION: Update the Chat ID to: {matching_chat[0]}")
        
        # Test sync for this group
        print(f"\n   Testing Telegram API connection...")
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getChatMemberCount"
            print(f"   - Sending chat_id: {group.chat_id}")
            
            response = requests.post(
                url,
                json={'chat_id': group.chat_id},
                timeout=10
            )
            
            print(f"   - Response status: {response.status_code}")
            data = response.json()
            
            if response.status_code == 200 and data.get('ok'):
                member_count = data['result']
                print(f"\n   ✅ SUCCESS! Current member count: {member_count}")
                print(f"   - Difference from stored: {member_count - group.member_count}")
            elif response.status_code == 400:
                error_desc = data.get('description', 'Unknown error')
                print(f"\n   ❌ ERROR: {error_desc}")
                if 'chat not found' in error_desc.lower():
                    print(f"\n   💡 TROUBLESHOOTING:")
                    print(f"   1. The group may have been upgraded to a supergroup")
                    print(f"   2. Check the Chat IDs found above from bot updates")
                    print(f"   3. Send a test message in TradeHub to update bot cache")
                    
                    # Try with found chat IDs
                    if found_chats:
                        print(f"\n   🔄 Trying discovered chat IDs...")
                        for chat_id, title, chat_type in found_chats:
                            if title.lower() == group.name.lower():
                                print(f"\n   Testing with {chat_id}...")
                                test_response = requests.post(
                                    url,
                                    json={'chat_id': str(chat_id)},
                                    timeout=10
                                )
                                test_data = test_response.json()
                                if test_response.status_code == 200 and test_data.get('ok'):
                                    member_count = test_data['result']
                                    print(f"   ✅ SUCCESS with chat_id: {chat_id}")
                                    print(f"   Member count: {member_count}")
                                    print(f"\n   🎯 UPDATE YOUR GROUP CHAT ID TO: {chat_id}")
            elif response.status_code == 401:
                print(f"\n   ❌ ERROR: Invalid bot token (401 Unauthorized)")
            elif response.status_code == 403:
                print(f"\n   ❌ ERROR: Bot lacks permissions (403 Forbidden)")
            else:
                print(f"\n   ❌ ERROR: Unexpected status {response.status_code}")
                print(f"   Response: {data}")
                
        except requests.exceptions.Timeout:
            print(f"\n   ❌ ERROR: Connection timeout")
        except Exception as e:
            print(f"\n   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    if found_chats:
        print("\n📝 SUMMARY OF DISCOVERED CHAT IDs:")
        for chat_id, title, chat_type in sorted(found_chats):
            print(f"   {title}: {chat_id} ({chat_type})")

if __name__ == '__main__':
    test_telegram_sync()
