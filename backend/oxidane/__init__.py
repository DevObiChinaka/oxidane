"""
Oxidane Django Project Package
Initializes Celery app when Django starts
"""

# Import Celery app to ensure it's always imported when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
