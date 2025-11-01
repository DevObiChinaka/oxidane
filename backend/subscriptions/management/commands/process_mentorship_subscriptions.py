# Management command for processing mentorship subscriptions
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from subscriptions.mentorship_models import (
    MentorshipSubscription, MentorshipTelegramTask
)
from users.email_automation import send_mentorship_expiry_reminder
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process mentorship subscriptions - check expiry, send reminders, manage Telegram groups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making actual changes (preview mode)',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send expiry reminders to users',
        )
        parser.add_argument(
            '--process-telegram',
            action='store_true',
            help='Process Telegram group tasks',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_reminders = options['send_reminders']
        process_telegram = options['process_telegram']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        # Process expired subscriptions
        self.process_expired_subscriptions(dry_run)
        
        # Send expiry reminders
        if send_reminders:
            self.send_expiry_reminders(dry_run)
        
        # Process Telegram tasks
        if process_telegram:
            self.process_telegram_tasks(dry_run)
        
        self.stdout.write(self.style.SUCCESS('✅ Mentorship processing completed'))
    
    def process_expired_subscriptions(self, dry_run=False):
        """Find and process expired mentorship subscriptions"""
        self.stdout.write('🔍 Checking for expired mentorship subscriptions...')
        
        now = timezone.now()
        
        # Find active subscriptions that have expired
        expired_subscriptions = MentorshipSubscription.objects.filter(
            subscription_status='active',
            subscription_end__lte=now
        )
        
        count = expired_subscriptions.count()
        if count == 0:
            self.stdout.write('   ℹ️  No expired subscriptions found')
            return
        
        self.stdout.write(f'   📋 Found {count} expired subscription(s)')
        
        for subscription in expired_subscriptions:
            self.stdout.write(f'   📅 Expiring: {subscription.user.email} (ended {subscription.subscription_end})')
            
            if not dry_run:
                # Mark subscription as expired
                subscription.subscription_status = 'expired'
                subscription.save()
                
                # Revoke premium content access
                subscription.revoke_premium_access()
                
                # Schedule Telegram removal if not already scheduled
                if subscription.telegram_status in ['added', 'pending_add']:
                    subscription.create_telegram_task('remove')
                    subscription.telegram_status = 'pending_removal'
                    subscription.save()
                
                self.stdout.write(f'   ✅ Processed expiry for {subscription.user.email}')
            else:
                self.stdout.write(f'   🔍 [DRY RUN] Would expire subscription for {subscription.user.email}')
    
    def send_expiry_reminders(self, dry_run=False):
        """Send expiry reminders to users"""
        self.stdout.write('📧 Checking for users needing expiry reminders...')
        
        now = timezone.now()
        
        # Find subscriptions expiring in 7 days
        reminder_date = now + timedelta(days=7)
        
        subscriptions_to_remind = MentorshipSubscription.objects.filter(
            subscription_status='active',
            subscription_end__date=reminder_date.date(),
            # Add a field to track if reminder was sent to avoid duplicates
            # reminder_sent=False  # You may want to add this field
        )
        
        count = subscriptions_to_remind.count()
        if count == 0:
            self.stdout.write('   ℹ️  No users need expiry reminders today')
            return
        
        self.stdout.write(f'   📋 Found {count} user(s) needing expiry reminders')
        
        for subscription in subscriptions_to_remind:
            self.stdout.write(f'   📧 Sending reminder to: {subscription.user.email}')
            
            if not dry_run:
                try:
                    send_mentorship_expiry_reminder(subscription.user, subscription)
                    # You may want to add a field to track reminder sending
                    # subscription.reminder_sent = True
                    # subscription.save()
                    self.stdout.write(f'   ✅ Reminder sent to {subscription.user.email}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Failed to send reminder to {subscription.user.email}: {str(e)}')
                    )
            else:
                self.stdout.write(f'   🔍 [DRY RUN] Would send reminder to {subscription.user.email}')
    
    def process_telegram_tasks(self, dry_run=False):
        """Process pending Telegram group management tasks"""
        self.stdout.write('📱 Processing Telegram group tasks...')
        
        now = timezone.now()
        
        # Find due tasks
        due_tasks = MentorshipTelegramTask.objects.filter(
            status='pending',
            scheduled_for__lte=now
        )
        
        count = due_tasks.count()
        if count == 0:
            self.stdout.write('   ℹ️  No due Telegram tasks found')
            return
        
        self.stdout.write(f'   📋 Found {count} due Telegram task(s)')
        
        for task in due_tasks:
            action_desc = f"{task.action_type} @{task.telegram_username} from {task.telegram_group}"
            self.stdout.write(f'   📱 Processing: {action_desc}')
            
            if not dry_run:
                # Here you would integrate with your Telegram bot
                # For now, we'll mark them as pending manual processing
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  Manual action required: {action_desc}')
                )
                self.stdout.write(
                    f'      Subscription ID: {task.mentorship_subscription.id}'
                )
                self.stdout.write(
                    f'      User: {task.mentorship_subscription.user.email}'
                )
                self.stdout.write(
                    f'      Action: {task.action_type.upper()} from {task.telegram_group}'
                )
            else:
                self.stdout.write(f'   🔍 [DRY RUN] Would process: {action_desc}')
        
        # Show summary of all pending tasks
        all_pending = MentorshipTelegramTask.objects.filter(status='pending').count()
        if all_pending > 0:
            self.stdout.write(
                self.style.WARNING(f'   📊 Total pending Telegram tasks: {all_pending}')
            )
            self.stdout.write(
                '   💡 Run with --process-telegram flag to handle these tasks'
            )
            self.stdout.write(
                '   💡 Use the admin panel to manually mark tasks as completed'
            )