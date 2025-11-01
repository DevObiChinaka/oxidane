"""
Django management command to process subscription expiration and Telegram group management
Usage: python manage.py process_telegram_queue
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import SignalSubscription, TelegramGroupManagement
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process Telegram queue and handle subscription expirations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--check-expiring',
            type=int,
            default=3,
            help='Check subscriptions expiring in N days (default: 3)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        expiring_days = options['check_expiring']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            
        self.stdout.write(self.style.SUCCESS('Processing Telegram queue and subscriptions...'))
        
        # Process expiring subscriptions
        self.process_expiring_subscriptions(expiring_days, dry_run)
        
        # Process expired subscriptions (removal)
        self.process_expired_subscriptions(dry_run)
        
        # Process new subscriptions (additions)  
        self.process_new_subscriptions(dry_run)
        
        self.stdout.write(self.style.SUCCESS('Telegram queue processing complete!'))

    def process_expiring_subscriptions(self, days_ahead, dry_run):
        """Send warning emails for subscriptions expiring soon"""
        self.stdout.write('\n📧 Checking for expiring subscriptions...')
        
        target_date = timezone.now().date() + timedelta(days=days_ahead)
        
        expiring_subscriptions = SignalSubscription.objects.filter(
            subscription_end__date=target_date,
            payment_status='verified',
            telegram_status__in=['added', 'verified']
        )
        
        count = expiring_subscriptions.count()
        self.stdout.write(f'Found {count} subscriptions expiring in {days_ahead} days')
        
        if not dry_run and count > 0:
            # Import and use your existing email service
            try:
                from users.email_service import EmailTemplateService
                email_service = EmailTemplateService()
                
                sent_count = 0
                for subscription in expiring_subscriptions:
                    try:
                        # Send renewal reminder email
                        custom_vars = {
                            'subscription_end_date': subscription.subscription_end.strftime('%B %d, %Y'),
                            'days_remaining': days_ahead,
                            'renewal_url': 'https://oxiworld.com/renew'
                        }
                        
                        result = email_service.send_email(
                            template_type='renewal_reminder',
                            recipient_email=subscription.user.email,
                            user=subscription.user,
                            custom_vars=custom_vars
                        )
                        
                        if result['success']:
                            sent_count += 1
                            self.stdout.write(f'  ✅ Sent reminder to {subscription.user.email}')
                        else:
                            self.stdout.write(f'  ❌ Failed to send to {subscription.user.email}')
                            
                    except Exception as e:
                        self.stdout.write(f'  ❌ Error sending to {subscription.user.email}: {e}')
                        
                self.stdout.write(f'📧 Sent {sent_count}/{count} reminder emails')
                
            except ImportError:
                self.stdout.write(self.style.ERROR('❌ Email service not available'))
        elif dry_run and count > 0:
            for subscription in expiring_subscriptions:
                self.stdout.write(f'  📧 Would send reminder to {subscription.user.email}')

    def process_expired_subscriptions(self, dry_run):
        """Create removal tasks for expired subscriptions"""
        self.stdout.write('\n🚫 Processing expired subscriptions...')
        
        today = timezone.now().date()
        expired_subscriptions = SignalSubscription.objects.filter(
            subscription_end__date=today,
            payment_status='verified',
            telegram_status__in=['added', 'verified']
        )
        
        count = expired_subscriptions.count()
        self.stdout.write(f'Found {count} subscriptions expiring today')
        
        removal_tasks_created = 0
        
        for subscription in expired_subscriptions:
            if dry_run:
                self.stdout.write(f'  🚫 Would remove {subscription.telegram_username} from all groups')
                continue
                
            try:
                # Create removal task for each group
                from django.conf import settings
                groups = getattr(settings, 'TELEGRAM_GROUPS', {})
                
                for group_key, group_info in groups.items():
                    task, created = TelegramGroupManagement.objects.get_or_create(
                        signal_subscription=subscription,
                        action_type='remove',
                        telegram_username=subscription.telegram_username,
                        telegram_group=group_key,
                        defaults={
                            'status': 'pending'
                        }
                    )
                    
                    if created:
                        removal_tasks_created += 1
                        self.stdout.write(f'  ✅ Created removal task for {subscription.telegram_username} from {group_info["name"]}')
                
                # Update subscription status
                subscription.telegram_status = 'pending_removal'
                subscription.save()
                
            except Exception as e:
                self.stdout.write(f'  ❌ Error creating removal task for {subscription.telegram_username}: {e}')
        
        if not dry_run:
            self.stdout.write(f'🚫 Created {removal_tasks_created} removal tasks')

    def process_new_subscriptions(self, dry_run):
        """Create addition tasks for new verified subscriptions"""
        self.stdout.write('\n✅ Processing new subscriptions...')
        
        # Find verified subscriptions not yet added to Telegram
        new_subscriptions = SignalSubscription.objects.filter(
            payment_status='verified',
            telegram_status__in=['not_added', 'pending'],
            subscription_end__gt=timezone.now(),  # Still active
            telegram_username__isnull=False
        ).exclude(telegram_username='')
        
        count = new_subscriptions.count()
        self.stdout.write(f'Found {count} new subscriptions ready for Telegram access')
        
        addition_tasks_created = 0
        
        for subscription in new_subscriptions:
            if dry_run:
                self.stdout.write(f'  ✅ Would add {subscription.telegram_username} to appropriate groups')
                continue
                
            try:
                # Determine which groups user should access based on subscription
                plan_type = self.get_plan_type(subscription)
                group_access = self.get_group_access(plan_type)
                
                for group_key in group_access:
                    task, created = TelegramGroupManagement.objects.get_or_create(
                        signal_subscription=subscription,
                        action_type='add',
                        telegram_username=subscription.telegram_username,
                        telegram_group=group_key,
                        defaults={
                            'status': 'pending'
                        }
                    )
                    
                    if created:
                        addition_tasks_created += 1
                        from django.conf import settings
                        groups = getattr(settings, 'TELEGRAM_GROUPS', {})
                        group_name = groups.get(group_key, {}).get('name', group_key)
                        self.stdout.write(f'  ✅ Created addition task for {subscription.telegram_username} to {group_name}')
                
                # Update subscription status
                subscription.telegram_status = 'pending_add'
                subscription.save()
                
            except Exception as e:
                self.stdout.write(f'  ❌ Error creating addition task for {subscription.telegram_username}: {e}')
        
        if not dry_run:
            self.stdout.write(f'✅ Created {addition_tasks_created} addition tasks')

    def get_plan_type(self, subscription):
        """Determine plan type from subscription"""
        # Adjust this logic based on your subscription model
        if hasattr(subscription, 'plan_type'):
            return subscription.plan_type
        elif hasattr(subscription, 'amount_paid'):
            amount = float(subscription.amount_paid)
            if amount >= 99:  # VIP threshold
                return 'vip'
            elif amount >= 29:  # Premium threshold
                return 'premium'
            else:
                return 'basic'
        else:
            return 'basic'  # Default fallback

    def get_group_access(self, plan_type):
        """Get list of groups user should have access to"""
        group_access = {
            'basic': ['education_group'],  # Mentorship only
            'premium': ['education_group', 'premium_signals'],  # Mentorship + Signals
            'vip': ['education_group', 'premium_signals', 'vip_community']  # All groups
        }
        return group_access.get(plan_type, ['education_group'])