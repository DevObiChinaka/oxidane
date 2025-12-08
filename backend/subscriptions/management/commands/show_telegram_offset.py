from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Show current Telegram bot offset'

    def handle(self, *args, **options):
        offset = cache.get('telegram_bot_update_offset', 0)
        self.stdout.write(f'Current offset: {offset}')
