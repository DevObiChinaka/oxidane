"""
Celery Configuration for Oxidane Project
Configures Celery with Redis broker and result backend

Created: November 10, 2025
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')

# Create Celery app
app = Celery('oxidane')

# Load configuration from Django settings
# Using 'CELERY_' prefix for all Celery settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
# Looks for tasks.py in each app
app.autodiscover_tasks()

# Configure periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    # NOTE: Telegram polling moved to separate telegram_poller.py script
    # Running it as a Beat task every few seconds was causing Beat to crash
    # Use: python telegram_poller.py & (in backend directory)
    
    # Check expired subscriptions every day at midnight
    'check-expired-subscriptions': {
        'task': 'subscriptions.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    
    # Process auto-renewals every day at 2 AM
    'process-auto-renewals': {
        'task': 'subscriptions.tasks.process_auto_renewals',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Send subscription renewal reminders
    'send-renewal-reminders': {
        'task': 'subscriptions.tasks.send_renewal_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    
    # Reconcile payments (find and retry failed activations)
    'reconcile-payments': {
        'task': 'subscriptions.tasks.reconcile_payments',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    
    # Example: Update exchange rates
    'update-exchange-rates': {
        'task': 'subscriptions.tasks.update_exchange_rates',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

# Task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
