#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/var/www/oxidane/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import TelegramGroup

groups = TelegramGroup.objects.all()
print(f'Total groups: {groups.count()}')
for g in groups:
    print(f'  - {g.name} (chat_id: {g.chat_id}, member_count: {g.member_count})')
