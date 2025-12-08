from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration, TelegramGroup
import requests


class Command(BaseCommand):
    help = 'Check bot permissions in Telegram group'

    def handle(self, *args, **options):
        try:
            config = TelegramConfiguration.objects.first()
            if not config or not config.bot_token:
                self.stdout.write(self.style.ERROR('Bot token not configured'))
                return
            
            from cryptography.fernet import Fernet
            from django.conf import settings
            cipher = Fernet(settings.ENCRYPTION_KEY.encode())
            bot_token = cipher.decrypt(config.bot_token.encode()).decode()
            
            # Get the group
            group = TelegramGroup.objects.get(name='OxiWorld Signals')
            chat_id = group.chat_id
            
            self.stdout.write(f'\n=== Checking Group: {group.name} ===')
            self.stdout.write(f'Chat ID: {chat_id}')
            
            # Get chat info
            url = f'https://api.telegram.org/bot{bot_token}/getChat'
            response = requests.get(url, params={'chat_id': chat_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    chat = data['result']
                    self.stdout.write(f'\nChat Type: {chat.get("type")}')
                    self.stdout.write(f'Title: {chat.get("title")}')
                    self.stdout.write(f'Username: @{chat.get("username", "none")}')
                    self.stdout.write(f'Permissions: {chat.get("permissions", {})}')
                else:
                    self.stdout.write(self.style.ERROR(f'API Error: {data.get("description")}'))
            else:
                self.stdout.write(self.style.ERROR(f'HTTP Error: {response.status_code}'))
            
            # Get bot member status
            url = f'https://api.telegram.org/bot{bot_token}/getChatMember'
            response = requests.get(url, params={'chat_id': chat_id, 'user_id': config.bot_user_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    member = data['result']
                    self.stdout.write(f'\n=== Bot Status ===')
                    self.stdout.write(f'Status: {member.get("status")}')
                    self.stdout.write(f'Is Admin: {member.get("status") == "administrator"}')
                    
                    if 'can_invite_users' in member:
                        self.stdout.write(f'Can invite users: {member.get("can_invite_users")}')
                    if 'can_manage_chat' in member:
                        self.stdout.write(f'Can manage chat: {member.get("can_manage_chat")}')
                    
                    self.stdout.write(f'\nFull permissions: {member}')
                else:
                    self.stdout.write(self.style.ERROR(f'API Error: {data.get("description")}'))
            
            # Try to create invite link
            self.stdout.write(f'\n=== Testing Invite Link Creation ===')
            url = f'https://api.telegram.org/bot{bot_token}/createChatInviteLink'
            response = requests.post(url, json={
                'chat_id': chat_id,
                'member_limit': 1,
                'name': 'Test Subscription Access'
            })
            
            data = response.json()
            if data.get('ok'):
                self.stdout.write(self.style.SUCCESS('✅ Can create invite links'))
                self.stdout.write(f'Test link: {data["result"]["invite_link"]}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Cannot create invite link: {data.get("description")}'))
                self.stdout.write(f'Error code: {data.get("error_code")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
