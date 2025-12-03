"""
Management command to manually set and encrypt Telegram bot token.
Usage: python manage.py set_telegram_token <bot_token>
"""
from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration


class Command(BaseCommand):
    help = 'Set and encrypt Telegram bot token'

    def add_arguments(self, parser):
        parser.add_argument('bot_token', type=str, help='The Telegram bot token to set')

    def handle(self, *args, **options):
        bot_token = options['bot_token']
        
        # Validate format
        if ':' not in bot_token:
            self.stdout.write(self.style.ERROR(
                "Invalid token format. Expected: numbers:characters (e.g., 123456:ABC...)"
            ))
            return
        
        config = TelegramConfiguration.get_instance()
        
        self.stdout.write(f"\nSetting bot token...")
        self.stdout.write(f"Token length: {len(bot_token)}")
        self.stdout.write(f"First 30 chars: {bot_token[:30]}")
        
        # Set the token (plaintext)
        config.bot_token = bot_token
        config.is_connected = False
        config.connection_error = ''
        
        # Encrypt the token
        self.stdout.write(f"\nEncrypting token...")
        config.encrypt_field('bot_token')
        
        # Verify encryption
        config.refresh_from_db()
        encrypted_token = config.bot_token
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Token encrypted successfully!"))
        self.stdout.write(f"Encrypted token first 30 chars: {encrypted_token[:30]}")
        self.stdout.write(f"Starts with 'gAAAAA': {encrypted_token.startswith('gAAAAA')}")
        
        # Test decryption
        try:
            decrypted = config.decrypt_field('bot_token')
            if decrypted == bot_token:
                self.stdout.write(self.style.SUCCESS("✓ Decryption verified - matches original!"))
            else:
                self.stdout.write(self.style.ERROR("✗ Decryption mismatch!"))
                self.stdout.write(f"Original: {bot_token[:30]}")
                self.stdout.write(f"Decrypted: {decrypted[:30]}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Decryption failed: {str(e)}"))
        
        self.stdout.write("\n")
