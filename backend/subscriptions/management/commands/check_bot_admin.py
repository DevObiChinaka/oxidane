from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration, TelegramGroup
import requests


class Command(BaseCommand):
    help = 'Check bot admin status and permissions'

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
            
            # First get bot info to get its user_id
            url = f'https://api.telegram.org/bot{bot_token}/getMe'
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    bot_user_id = bot_info['id']
                    self.stdout.write(f'Bot ID: {bot_user_id}')
                    self.stdout.write(f'Bot Username: @{bot_info["username"]}')
                    self.stdout.write(f'Bot Name: {bot_info["first_name"]}\n')
                else:
                    self.stdout.write(self.style.ERROR('Failed to get bot info'))
                    return
            
            # Get the group
            group = TelegramGroup.objects.get(name='OxiWorld Signals')
            chat_id = group.chat_id
            
            self.stdout.write(f'=== Checking Group: {group.name} ===')
            self.stdout.write(f'Chat ID: {chat_id}\n')
            
            # Get bot admin status
            url = f'https://api.telegram.org/bot{bot_token}/getChatMember'
            response = requests.get(url, params={'chat_id': chat_id, 'user_id': bot_user_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    member = data['result']
                    status = member.get('status')
                    
                    self.stdout.write(f'Bot Status: {status}')
                    
                    if status == 'administrator':
                        self.stdout.write(self.style.SUCCESS('✅ Bot is an administrator'))
                        self.stdout.write(f'\nAdmin Permissions:')
                        self.stdout.write(f'  can_invite_users: {member.get("can_invite_users", False)}')
                        self.stdout.write(f'  can_manage_chat: {member.get("can_manage_chat", False)}')
                        self.stdout.write(f'  can_delete_messages: {member.get("can_delete_messages", False)}')
                        self.stdout.write(f'  can_restrict_members: {member.get("can_restrict_members", False)}')
                        self.stdout.write(f'  can_promote_members: {member.get("can_promote_members", False)}')
                        self.stdout.write(f'  can_change_info: {member.get("can_change_info", False)}')
                        self.stdout.write(f'  can_post_messages: {member.get("can_post_messages", False)}')
                        self.stdout.write(f'  can_edit_messages: {member.get("can_edit_messages", False)}')
                        self.stdout.write(f'  can_pin_messages: {member.get("can_pin_messages", False)}')
                        
                        if not member.get('can_invite_users'):
                            self.stdout.write(self.style.ERROR('\n❌ Bot CANNOT invite users!'))
                            self.stdout.write('This is required to create invite links.')
                            self.stdout.write('Please enable "Invite Users" permission in group admin settings.')
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ Bot is not an admin (status: {status})'))
                else:
                    self.stdout.write(self.style.ERROR(f'API Error: {data.get("description")}'))
            else:
                self.stdout.write(self.style.ERROR(f'HTTP Error: {response.status_code}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
