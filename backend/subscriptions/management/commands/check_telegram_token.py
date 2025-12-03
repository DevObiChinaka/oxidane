"""
Management command to check Telegram token encryption status.
Usage: python manage.py check_telegram_token
"""
from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration


class Command(BaseCommand):
    help = 'Check Telegram bot token encryption status'

    def handle(self, *args, **options):
        config = TelegramConfiguration.get_instance()
        
        self.stdout.write("\n=== Telegram Configuration Debug ===\n")
        
        # Check raw token
        raw_token = config.bot_token
        self.stdout.write(f"Bot token exists: {bool(raw_token)}")
        
        if raw_token:
            self.stdout.write(f"Token length: {len(raw_token)}")
            self.stdout.write(f"First 30 chars: {raw_token[:30]}")
            self.stdout.write(f"Starts with 'gAAAAA': {raw_token.startswith('gAAAAA')}")
            self.stdout.write(f"Is encrypted: {config.has_valid_token()}")
            
            # Try to decrypt
            try:
                decrypted = config.decrypt_field('bot_token')
                self.stdout.write(f"\nDecryption successful!")
                self.stdout.write(f"Decrypted length: {len(decrypted)}")
                self.stdout.write(f"Decrypted first 30 chars: {decrypted[:30]}")
                self.stdout.write(f"Contains colon: {':' in decrypted}")
                
                # Validate format
                if ':' in decrypted:
                    parts = decrypted.split(':', 1)
                    self.stdout.write(f"Format valid: numbers={parts[0].isdigit()}, has_chars={len(parts[1]) > 0}")
                else:
                    self.stdout.write(self.style.ERROR("Invalid format: no colon found"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\nDecryption failed: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING("No token configured"))
        
        self.stdout.write(f"\nConnection status: {config.is_connected}")
        self.stdout.write(f"Connection error: {config.connection_error}")
        self.stdout.write("\n" + "="*40 + "\n")
