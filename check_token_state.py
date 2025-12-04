#!/usr/bin/env python
"""Check current state of Telegram bot token"""
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramConfiguration

config = TelegramConfiguration.get_instance()
print(f'Bot token exists: {bool(config.bot_token)}')
print(f'Token length: {len(config.bot_token) if config.bot_token else 0}')
print(f'Token starts with: {config.bot_token[:20] if config.bot_token else "(empty)"}...')
print(f'Has valid token: {config.has_valid_token()}')
print(f'Is connected: {config.is_connected}')

# Try to decrypt
if config.bot_token:
    try:
        decrypted = config.decrypt_field('bot_token')
        print(f'\nDecryption: SUCCESS')
        print(f'Decrypted length: {len(decrypted)}')
        print(f'Decrypted format: {decrypted[:10]}...:{decrypted[-10:]}')
    except Exception as e:
        print(f'\nDecryption: FAILED')
        print(f'Error: {e}')
else:
    print('\nNo token to decrypt')
