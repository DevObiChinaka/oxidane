"""Remove migration 0023 from database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.db.migrations.recorder import MigrationRecorder

deleted = MigrationRecorder.Migration.objects.filter(
    app='subscriptions',
    name='0023_cleanup_model_state'
).delete()

print(f"Removed {deleted[0]} migration records from database")
