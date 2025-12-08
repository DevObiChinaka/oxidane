from django.core.management.base import BaseCommand
from subscriptions.models import Payment, Subscription, User
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check recent payment and subscription status'

    def handle(self, *args, **options):
        # Get last successful payment
        payment = Payment.objects.filter(status='success').order_by('-created_at').first()
        
        if not payment:
            self.stdout.write(self.style.WARNING('No successful payments found'))
            return
        
        self.stdout.write('\n=== Last Successful Payment ===')
        self.stdout.write(f'Payment ID: {payment.id}')
        self.stdout.write(f'Amount: {payment.currency} {payment.amount}')
        self.stdout.write(f'Status: {payment.status}')
        self.stdout.write(f'Activation Status: {payment.activation_status}')
        self.stdout.write(f'Activation Attempts: {payment.activation_attempts}')
        self.stdout.write(f'Created: {payment.created_at}')
        
        if payment.subscription:
            sub = payment.subscription
            self.stdout.write('\n=== Associated Subscription ===')
            self.stdout.write(f'Subscription ID: {sub.id}')
            self.stdout.write(f'Plan: {sub.plan.name}')
            self.stdout.write(f'Status: {sub.status}')
            self.stdout.write(f'Start Date: {sub.start_date}')
            self.stdout.write(f'End Date: {sub.end_date}')
            self.stdout.write(f'Auto Renew: {sub.auto_renew}')
            
            # Check Telegram groups
            groups = sub.plan.telegram_groups.filter(is_active=True)
            self.stdout.write(f'\nTelegram Groups ({groups.count()}):')
            for group in groups:
                self.stdout.write(f'  - {group.name} ({group.chat_id})')
        else:
            self.stdout.write(self.style.WARNING('\nNo subscription linked to payment'))
        
        # Check user
        user = payment.billing_profile.user
        self.stdout.write('\n=== User Info ===')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Telegram User ID: {payment.billing_profile.telegram_user_id or "NOT SET"}')
        self.stdout.write(f'Telegram Username: {payment.billing_profile.telegram_username or "NOT SET"}')
        
        # Check for recent subscriptions
        recent_subs = Subscription.objects.filter(
            user=user,
            status='active'
        ).order_by('-created_at')
        
        self.stdout.write(f'\n=== Active Subscriptions ({recent_subs.count()}) ===')
        for sub in recent_subs[:5]:
            self.stdout.write(f'{sub.id} - {sub.plan.name} ({sub.start_date} to {sub.end_date})')
