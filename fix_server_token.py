#!/usr/bin/env python3
import re

# Read the file
with open('/var/www/oxidane/backend/subscriptions/models.py', 'r') as f:
    content = f.read()

# Find and replace the has_valid_token method
old_method = '''    def has_valid_token(self):
        """Check if bot token has valid format (basic check)"""
        if not self.bot_token:
            return False
        # Telegram tokens format: numbers:letters (e.g., 123456789:ABCdefGHI...)
        parts = self.bot_token.split(':')
        return len(parts) == 2 and parts[0].isdigit() and len(parts[1]) > 0'''

new_method = '''    def has_valid_token(self):
        """Check if bot token exists (may be encrypted or plaintext)"""
        if not self.bot_token:
            return False
        
        # If encrypted (starts with Fernet prefix), assume it's valid
        if self.bot_token.startswith('gAAAAA'):
            return True
        
        # If not encrypted, validate format: numbers:letters
        parts = self.bot_token.split(':')
        return len(parts) == 2 and parts[0].isdigit() and len(parts[1]) > 0'''

content = content.replace(old_method, new_method)

# Write back
with open('/var/www/oxidane/backend/subscriptions/models.py', 'w') as f:
    f.write(content)

print('SUCCESS: Updated has_valid_token method to recognize encrypted tokens')
