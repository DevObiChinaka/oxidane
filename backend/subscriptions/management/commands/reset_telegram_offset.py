from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Reset Telegram bot offset cache'

    def handle(self, *args, **options):
        cache.delete('telegram_bot_update_offset')
        self.stdout.write(self.style.SUCCESS('Telegram offset cache deleted'))
