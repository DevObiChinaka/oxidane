"""
Management command to generate a new encryption key for the ENCRYPTION_KEY setting.

Usage:
    python manage.py generate_encryption_key
    
The generated key should be added to your Django settings:
    ENCRYPTION_KEY = 'generated-key-here'
"""

from django.core.management.base import BaseCommand
from oxidane.encryption import EncryptionService


class Command(BaseCommand):
    help = 'Generate a new encryption key for ENCRYPTION_KEY setting'
    
    def handle(self, *args, **options):
        """Generate and display a new encryption key."""
        key = EncryptionService.generate_key()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('New Encryption Key Generated'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'\n{key}\n')
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANT: Add this to your Django settings (settings.py):'))
        self.stdout.write(self.style.WARNING('\nENCRYPTION_KEY = ' + repr(key)))
        self.stdout.write(self.style.WARNING('\n⚠️  Store this key securely - you cannot decrypt data without it!'))
        self.stdout.write(self.style.WARNING('⚠️  Never commit this key to version control!'))
        self.stdout.write(self.style.WARNING('⚠️  Use environment variables in production!\n'))
