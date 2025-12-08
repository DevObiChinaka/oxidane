"""
Management command to delete Telegram webhook and enable polling
"""
from django.core.management.base import BaseCommand
from subscriptions.models import TelegramConfiguration
import requests


class Command(BaseCommand):
    help = 'Delete Telegram webhook to enable polling'

    def handle(self, *args, **options):
        config = TelegramConfiguration.get_instance()
        bot_token = config.decrypt_field('bot_token')

        # Delete webhook
        url = f'https://api.telegram.org/bot{bot_token}/deleteWebhook'
        response = requests.post(url)
        self.stdout.write(f'Delete webhook: {response.json()}')

        # Get webhook info
        url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
        response = requests.get(url)
        self.stdout.write(f'Webhook info: {response.json()}')
