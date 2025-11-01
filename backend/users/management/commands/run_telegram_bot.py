"""
Django management command to run the OxiWord Telegram Bot
Usage: python manage.py run_telegram_bot
"""

from django.core.management.base import BaseCommand
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir))

try:
    from oxiword_bot_simple import OxiWordBotSimple
except ImportError:
    print("Error: Could not import OxiWordBotSimple. Make sure oxiword_bot_simple.py is in the backend directory.")
    sys.exit(1)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the OxiWord Telegram Bot for user management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Run bot in debug mode with verbose logging',
        )
        parser.add_argument(
            '--check-config',
            action='store_true', 
            help='Check bot configuration and exit',
        )

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
            self.stdout.write(self.style.SUCCESS('Debug mode enabled'))

        if options['check_config']:
            self.check_configuration()
            return

        self.stdout.write(self.style.SUCCESS('Starting OxiWord Telegram Bot...'))
        
        try:
            # Run the bot
            bot = OxiWordBotSimple()
            asyncio.run(bot.run_bot())
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nBot stopped by user (Ctrl+C)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fatal error: {e}'))
            logger.error(f'Bot crashed: {e}', exc_info=True)

    def check_configuration(self):
        """Check bot configuration"""
        from django.conf import settings
        
        self.stdout.write(self.style.SUCCESS('Checking OxiWord Bot Configuration...'))
        self.stdout.write('=' * 50)
        
        # Check bot token
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if token:
            masked_token = f"{token[:10]}...{token[-10:]}"
            self.stdout.write(f'✅ Bot Token: {masked_token}')
        else:
            self.stdout.write(self.style.ERROR('❌ Bot Token: Not configured'))
            
        # Check groups configuration
        groups = getattr(settings, 'TELEGRAM_GROUPS', {})
        if groups:
            self.stdout.write(f'✅ Groups Configured: {len(groups)}')
            for key, group in groups.items():
                name = group.get('name', 'Unknown')
                chat_id = group.get('chat_id', 'Missing')
                self.stdout.write(f'   • {key}: {name} ({chat_id})')
        else:
            self.stdout.write(self.style.ERROR('❌ Groups: Not configured'))
            
        # Check database connectivity
        try:
            from subscriptions.models import SignalSubscription
            count = SignalSubscription.objects.count()
            self.stdout.write(f'✅ Database: Connected ({count} subscriptions)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database: Error - {e}'))
            
        self.stdout.write('=' * 50)
        self.stdout.write('Configuration check complete!')