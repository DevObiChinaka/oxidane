"""Test if payment receipt email is being sent"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Payment, EmailConfiguration
from subscriptions.tasks import send_payment_receipt_email
from django.conf import settings

print("="*80)
print("PAYMENT RECEIPT EMAIL TEST")
print("="*80)

# Check email configuration
print("\n[1] Checking Email Configuration...")
try:
    email_config = EmailConfiguration.get_instance()
    print(f"   Email Configuration Found:")
    print(f"   - SMTP Host: {email_config.smtp_host}")
    print(f"   - SMTP Port: {email_config.smtp_port}")
    print(f"   - From Email: {email_config.from_email}")
    print(f"   - Is Configured: {email_config.is_configured()}")
    print(f"   - Is Enabled: {email_config.is_enabled}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check Django email settings
print("\n[2] Checking Django Email Settings...")
print(f"   - EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   - EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
print(f"   - EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
print(f"   - EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
print(f"   - DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Check for successful payments
print("\n[3] Looking for Successful Payments...")
successful_payments = Payment.objects.filter(status='success').order_by('-created_at')[:5]

if successful_payments.exists():
    print(f"   Found {successful_payments.count()} recent successful payment(s)")
    
    for payment in successful_payments:
        print(f"\n   Payment ID: {payment.id}")
        print(f"   User: {payment.billing_profile.user.email}")
        print(f"   Amount: {payment.currency} {payment.total_amount}")
        print(f"   Date: {payment.paid_at or payment.created_at}")
        print(f"   Status: {payment.status}")
        
        # Test sending email
        print(f"\n   Testing email send for this payment...")
        try:
            result = send_payment_receipt_email(str(payment.id))
            print(f"   Result: {result}")
            if result.get('success'):
                print(f"   ✅ Email sent successfully to {result.get('recipient')}")
            else:
                print(f"   ❌ Email failed: {result.get('error')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        
        break  # Only test first payment
else:
    print("   No successful payments found")
    print("   Creating a test scenario would require a full payment flow")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
