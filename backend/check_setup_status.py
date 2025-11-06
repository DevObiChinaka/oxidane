import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import (
    TelegramConfiguration, PaymentConfiguration, EmailConfiguration,
    SubscriptionPlan, Feature, TelegramGroup
)

User = get_user_model()

# Check admin user
try:
    admin = User.objects.get(email='admin@oxidane.com')
    print(f"Admin user: {admin.email}")
    print(f"Is staff: {admin.is_staff}")
    print(f"Is superuser: {admin.is_superuser}")
except User.DoesNotExist:
    print("Admin user not found!")

print("\n" + "="*60)
print("SETUP STATUS CHECK")
print("="*60)

# Check Telegram Configuration
telegram_config = TelegramConfiguration.get_instance()
print(f"\n1. TELEGRAM CONFIGURATION:")
print(f"   - Has bot token: {bool(telegram_config.bot_token)}")
print(f"   - Is enabled: {telegram_config.is_enabled}")
print(f"   - Configured: {bool(telegram_config.bot_token and telegram_config.is_enabled)}")

# Check Payment Configuration
payment_config = PaymentConfiguration.get_instance()
print(f"\n2. PAYMENT CONFIGURATION:")
print(f"   - Paystack configured: {bool(payment_config.paystack_secret_key)}")
print(f"   - Stripe configured: {bool(payment_config.stripe_secret_key)}")
print(f"   - Configured: {bool(payment_config.paystack_secret_key or payment_config.stripe_secret_key)}")

# Check Email Configuration
email_config = EmailConfiguration.get_instance()
print(f"\n3. EMAIL CONFIGURATION:")
print(f"   - Is configured: {email_config.is_configured()}")
print(f"   - Has host: {bool(email_config.smtp_host)}")
print(f"   - Has credentials: {bool(email_config.smtp_username and email_config.smtp_password)}")

# Check Database Content
plans_count = SubscriptionPlan.objects.filter(is_active=True).count()
features_count = Feature.objects.count()
groups_count = TelegramGroup.objects.filter(is_active=True).count()

print(f"\n4. DATABASE CONTENT:")
print(f"   - Active plans: {plans_count}")
print(f"   - Features: {features_count}")
print(f"   - Active groups: {groups_count}")
print(f"   - Ready: {plans_count > 0}")

# Calculate completion
checks = [
    bool(telegram_config.bot_token and telegram_config.is_enabled),
    bool(payment_config.paystack_secret_key or payment_config.stripe_secret_key),
    email_config.is_configured(),
    plans_count > 0
]

completed_checks = sum(checks)
total_checks = len(checks)
completion_percentage = int((completed_checks / total_checks) * 100)
setup_complete = completion_percentage == 100

print("\n" + "="*60)
print(f"SETUP COMPLETE: {setup_complete}")
print(f"COMPLETION: {completion_percentage}% ({completed_checks}/{total_checks} checks)")
print("="*60)

if not setup_complete:
    print("\n❌ Missing configurations:")
    if not checks[0]:
        print("   - Telegram bot not configured")
    if not checks[1]:
        print("   - No payment gateway configured")
    if not checks[2]:
        print("   - Email/SMTP not configured")
    if not checks[3]:
        print("   - No active subscription plans")
