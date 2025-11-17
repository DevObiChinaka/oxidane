"""Enable Email Configuration"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import EmailConfiguration

email_config = EmailConfiguration.get_instance()
print(f"Current status: is_enabled = {email_config.is_enabled}")

# Enable it
email_config.is_enabled = True
email_config.save()

print(f"Updated status: is_enabled = {email_config.is_enabled}")
print("\n✅ Email configuration is now ENABLED")
print("\nEmails will now be sent for:")
print("- Payment receipts")
print("- Subscription activations")
print("- Renewal reminders")
print("- Expiration notices")
