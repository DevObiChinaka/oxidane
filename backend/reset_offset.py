#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache

# Delete the offset so the task will fetch ALL recent updates
# then save the latest offset properly
cache.delete('telegram_bot_update_offset')
print("Offset cache deleted - will reset on next poll")
