from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration, TelegramGroup, User
import requests
import time


class Command(BaseCommand):
    help = 'Test creating invite link manually'

    def handle(self, *args, **options):
        try:
            config = TelegramConfiguration.objects.first()
            from cryptography.fernet import Fernet
            from django.conf import settings
            cipher = Fernet(settings.ENCRYPTION_KEY.encode())
            bot_token = cipher.decrypt(config.bot_token.encode()).decode()
            
            group = TelegramGroup.objects.get(name='OxiWorld Signals')
            user = User.objects.get(email='derachinaka@gmail.com')
            
            self.stdout.write(f'Group: {group.name}')
            self.stdout.write(f'Chat ID: {group.chat_id}')
            self.stdout.write(f'User: {user.billing_profile.telegram_username}\n')
            
            # Test 1: Try with string chat_id
            self.stdout.write('=== Test 1: String chat_id ===')
            expire_timestamp = int(time.time()) + 3600
            
            url = f"https://api.telegram.org/bot{bot_token}/createChatInviteLink"
            payload = {
                'chat_id': group.chat_id,  # As stored in DB (string)
                'member_limit': 1,
                'expire_date': expire_timestamp,
                'name': f"Access for @{user.billing_profile.telegram_username}"
            }
            
            self.stdout.write(f'Payload: {payload}')
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            if data.get('ok'):
                self.stdout.write(self.style.SUCCESS(f'✅ Success: {data["result"]["invite_link"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {data.get("description")}'))
                self.stdout.write(f'Error code: {data.get("error_code")}')
            
            # Test 2: Try with int chat_id
            self.stdout.write('\n=== Test 2: Integer chat_id ===')
            payload['chat_id'] = int(group.chat_id)
            self.stdout.write(f'Payload: {payload}')
            
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            if data.get('ok'):
                self.stdout.write(self.style.SUCCESS(f'✅ Success: {data["result"]["invite_link"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {data.get("description")}'))
                self.stdout.write(f'Error code: {data.get("error_code")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
