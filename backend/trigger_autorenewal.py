"""
Manually trigger auto-renewal processing for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import process_auto_renewals

print("\n" + "="*80)
print("MANUALLY TRIGGERING AUTO-RENEWAL TASK")
print("="*80 + "\n")

result = process_auto_renewals()

print("\n" + "="*80)
print("RESULT:")
print("="*80)
print(result)
print()
