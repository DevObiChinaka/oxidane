from django.core.management.base import BaseCommand
from subscriptions.tasks import add_user_to_telegram_groups
from subscriptions.models import User, SubscriptionPlan


class Command(BaseCommand):
    help = 'Manually add user to Telegram groups for their active subscription'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='User email')
        parser.add_argument('--plan', type=str, help='Plan name')

    def handle(self, *args, **options):
        email = options.get('email') or 'derachinaka@gmail.com'
        plan_name = options.get('plan') or 'Weekly Signals'
        
        try:
            user = User.objects.get(email=email)
            plan = SubscriptionPlan.objects.get(name=plan_name)
            
            self.stdout.write(f'User: {user.email} (ID: {user.id})')
            self.stdout.write(f'Plan: {plan.name} (ID: {plan.id})')
            self.stdout.write(f'Telegram ID: {user.billing_profile.telegram_user_id}')
            
            # Queue the task
            result = add_user_to_telegram_groups.delay(user.id, plan.id)
            
            self.stdout.write(self.style.SUCCESS(f'Task queued: {result.id}'))
            self.stdout.write('Check Celery logs for result')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User not found: {email}'))
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Plan not found: {plan_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
