"""
Verify Telegram Bot Group Access

This script checks if the bot has proper access to groups and gets correct chat IDs.
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


def verify_bot_in_group(bot_token, chat_id):
    """Verify bot has access to a group"""
    try:
        # Get chat information
        url = f"https://api.telegram.org/bot{bot_token}/getChat"
        payload = {'chat_id': chat_id}
        
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            chat = data['result']
            print(f"\n✅ Chat Found!")
            print(f"  Title: {chat.get('title')}")
            print(f"  Type: {chat.get('type')}")
            print(f"  ID: {chat.get('id')}")
            print(f"  Username: @{chat.get('username', 'N/A')}")
            
            # Get bot's status in the chat
            get_member_url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
            bot_info_url = f"https://api.telegram.org/bot{bot_token}/getMe"
            
            bot_response = requests.get(bot_info_url, timeout=10)
            bot_data = bot_response.json()
            
            if bot_data.get('ok'):
                bot_id = bot_data['result']['id']
                
                member_payload = {
                    'chat_id': chat_id,
                    'user_id': bot_id
                }
                
                member_response = requests.post(get_member_url, json=member_payload, timeout=10)
                member_data = member_response.json()
                
                if member_data.get('ok'):
                    member = member_data['result']
                    print(f"\n🤖 Bot Status in Group:")
                    print(f"  Status: {member.get('status')}")
                    
                    if member.get('status') == 'administrator':
                        print(f"  ✅ Is Administrator: YES")
                        
                        # Check permissions
                        if 'can_invite_users' in member:
                            can_invite = member.get('can_invite_users', False)
                            if can_invite:
                                print(f"  ✅ Can Invite Users: YES")
                            else:
                                print(f"  ❌ Can Invite Users: NO - Please grant this permission!")
                        else:
                            print(f"  ⚠️  Can't check invite permission")
                        
                        return True
                    else:
                        print(f"  ❌ Is Administrator: NO - Bot is only: {member.get('status')}")
                        print(f"  Please make the bot an administrator!")
                        return False
                else:
                    print(f"\n❌ Bot Status Check Failed: {member_data.get('description')}")
                    return False
        else:
            print(f"\n❌ Chat Not Found: {data.get('description')}")
            print(f"\nPossible issues:")
            print(f"  1. Chat ID is incorrect")
            print(f"  2. Bot is not in the group")
            print(f"  3. Group type doesn't support bots")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_add_user_to_group(bot_token, chat_id, user_id):
    """Test adding a specific user to the group"""
    try:
        print(f"\n🔄 Testing addChatMember for user {user_id}...")
        
        url = f"https://api.telegram.org/bot{bot_token}/addChatMember"
        payload = {
            'chat_id': chat_id,
            'user_id': int(user_id)
        }
        
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            print(f"✅ Successfully added user to group!")
            return True
        else:
            error = data.get('description', 'Unknown error')
            print(f"❌ Failed to add user: {error}")
            
            # Provide helpful error messages
            if 'USER_ALREADY_PARTICIPANT' in error:
                print(f"  ℹ️  User is already in the group")
                return True
            elif 'CHAT_ADMIN_REQUIRED' in error:
                print(f"  ⚠️  Bot needs admin permission with 'Add Members'")
            elif 'USER_PRIVACY_RESTRICTED' in error:
                print(f"  ⚠️  User's privacy settings prevent auto-add")
            elif 'Not Found' in error or 'CHAT_NOT_FOUND' in error:
                print(f"  ⚠️  Chat ID might be incorrect or bot not in group")
            
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    print("=" * 70)
    print("  TELEGRAM BOT GROUP ACCESS VERIFICATION")
    print("=" * 70)
    
    # Get bot configuration
    config = TelegramConfiguration.get_instance()
    
    if not config.has_valid_token():
        print("\n❌ Bot token not configured!")
        return
    
    bot_token = config.bot_token
    print(f"\n✅ Bot token configured: {config.get_masked_token()}")
    
    # Get all Telegram groups
    groups = TelegramGroup.objects.filter(is_active=True)
    
    if not groups.exists():
        print("\n⚠️  No active Telegram groups found in database")
        return
    
    print(f"\n📊 Found {groups.count()} active group(s):")
    
    for group in groups:
        print("\n" + "=" * 70)
        print(f"Group: {group.name}")
        print(f"Chat ID: {group.chat_id}")
        print("=" * 70)
        
        # Verify bot access
        verify_bot_in_group(bot_token, group.chat_id)
    
    # Test with specific user
    print("\n" + "=" * 70)
    print("TEST: Adding User to Group")
    print("=" * 70)
    
    user_id = input("\nEnter Telegram User ID to test (or press Enter to skip): ").strip()
    
    if user_id:
        for group in groups:
            print(f"\n--- Testing {group.name} ---")
            test_add_user_to_group(bot_token, group.chat_id, user_id)
    
    print("\n" + "=" * 70)
    print("Verification Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
