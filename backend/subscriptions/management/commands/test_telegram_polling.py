"""
Management command to test Telegram bot polling
"""
from django.core.management.base import BaseCommand
from subscriptions.tasks import process_telegram_updates


class Command(BaseCommand):
    help = 'Test Telegram bot polling for updates'

    def handle(self, *args, **options):
        self.stdout.write('Testing Telegram bot polling...')
        
        try:
            result = process_telegram_updates()
            self.stdout.write(self.style.SUCCESS(f'Result: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
