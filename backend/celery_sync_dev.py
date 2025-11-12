"""
Settings override to make Celery tasks run synchronously when Celery is not available.
Add this to the end of settings.py for development.
"""

# Development: Run Celery tasks synchronously (inline) instead of async
# This allows the app to work without Celery worker running
# Remove this in production when using real Celery workers

import os

if os.getenv('USE_SYNC_TASKS', 'False') == 'True':
    # Make all Celery tasks execute synchronously
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    print("⚠️  WARNING: Celery tasks running synchronously (CELERY_TASK_ALWAYS_EAGER=True)")
    print("   This is fine for development but NOT for production!")
    print("   Set USE_SYNC_TASKS=False or remove this when deploying.")
