# Production Celery Configuration
# This file contains the Celery settings for production deployment

from kombu import Queue
import os

# Broker Configuration (Redis Cloud)
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# SSL Configuration for Redis Cloud
CELERY_BROKER_USE_SSL = {
    'ssl_cert_reqs': 'CERT_NONE'  # Redis Cloud uses TLS
}
CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': 'CERT_NONE'
}

# Connection Settings
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_POOL_LIMIT = 10

# Task Settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Result Settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_RESULT_PERSISTENT = False

# Queue Configuration
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = (
    Queue('default', routing_key='task.#'),
    Queue('high_priority', routing_key='high.#'),
)

# Schedule for Periodic Tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-expired-subscriptions': {
        'task': 'subscriptions.tasks.check_expired_subscriptions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'process-auto-renewals': {
        'task': 'subscriptions.tasks.process_auto_renewals',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight UTC
    },
    'send-renewal-reminders': {
        'task': 'subscriptions.tasks.send_renewal_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM UTC
    },
    'update-exchange-rates': {
        'task': 'subscriptions.tasks.update_exchange_rates',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

# Logging
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'

# Timezone
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Task Routing
CELERY_TASK_ROUTES = {
    'subscriptions.tasks.add_user_to_telegram_groups': {'queue': 'high_priority'},
    'subscriptions.tasks.send_payment_receipt_email': {'queue': 'high_priority'},
}
