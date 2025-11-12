"""
Check email configuration and test payment receipt email sending
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import EmailConfiguration, Payment
from subscriptions.tasks import send_payment_receipt_email
from django.contrib.auth import get_user_model

User = get_user_model()

def check_email_configuration():
    """Check if email is properly configured"""
    
    print("=" * 70)
    print("EMAIL CONFIGURATION CHECK")
    print("=" * 70)
    
    try:
        email_config = EmailConfiguration.get_instance()
        
        print(f"\n✓ Email Configuration Found")
        print(f"  - SMTP Host: {email_config.smtp_host or 'Not set'}")
        print(f"  - SMTP Port: {email_config.smtp_port or 'Not set'}")
        print(f"  - From Email: {email_config.from_email or 'Not set'}")
        print(f"  - Use TLS: {email_config.use_tls}")
        print(f"  - From Name: {email_config.from_name or 'Not set'}")
        
        if email_config.is_configured():
            print(f"\n✅ Email is CONFIGURED")
        else:
            print(f"\n⚠️  Email is NOT fully configured")
            print(f"   Missing fields:")
            if not email_config.smtp_host:
                print("   - SMTP Host")
            if not email_config.smtp_port:
                print("   - SMTP Port")
            if not email_config.smtp_username:
                print("   - SMTP Username")
            if not email_config.smtp_password:
                print("   - SMTP Password")
            if not email_config.from_email:
                print("   - From Email")
        
    except Exception as e:
        print(f"\n❌ Error getting email configuration: {e}")
    
    print("\n" + "=" * 70)

def check_recent_payments():
    """Check recent successful payments"""
    
    print("\nRECENT SUCCESSFUL PAYMENTS")
    print("=" * 70)
    
    # Get recent successful payments
    recent_payments = Payment.objects.filter(
        status='success'
    ).select_related(
        'billing_profile__user',
        'subscription__plan'
    ).order_by('-paid_at')[:5]
    
    if not recent_payments.exists():
        print("\n⚠️  No successful payments found")
        return None
    
    print(f"\n✓ Found {recent_payments.count()} recent successful payment(s)\n")
    
    for i, payment in enumerate(recent_payments, 1):
        print(f"{i}. Payment ID: {payment.id}")
        print(f"   User: {payment.billing_profile.user.email}")
        print(f"   Amount: {payment.currency} {payment.total_amount}")
        print(f"   Date: {payment.paid_at or payment.created_at}")
        print(f"   Reference: {payment.gateway_reference}")
        if payment.subscription:
            print(f"   Plan: {payment.subscription.plan.name if payment.subscription.plan else 'N/A'}")
        print()
    
    print("=" * 70)
    return recent_payments.first()

def test_send_receipt_email(payment):
    """Test sending receipt email for a payment"""
    
    print("\nTEST SENDING PAYMENT RECEIPT EMAIL")
    print("=" * 70)
    
    if not payment:
        print("\n⚠️  No payment to test with")
        return
    
    print(f"\n📧 Testing email for payment: {payment.id}")
    print(f"   Recipient: {payment.billing_profile.user.email}")
    
    try:
        # Call the task directly (not async)
        result = send_payment_receipt_email(payment.id)
        
        print(f"\n✅ Email sending result:")
        print(f"   {result}")
        
        if result.get('success'):
            print(f"\n✅ Email sent successfully!")
            print(f"   Subject: {result.get('subject')}")
            print(f"   Recipient: {result.get('recipient')}")
        else:
            print(f"\n❌ Email failed to send:")
            print(f"   Error: {result.get('error')}")
        
    except Exception as e:
        print(f"\n❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)

def check_celery_status():
    """Check if Celery is running"""
    
    print("\nCELERY STATUS CHECK")
    print("=" * 70)
    
    try:
        from celery import current_app
        
        # Try to inspect Celery
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print(f"\n✅ Celery is RUNNING")
            print(f"   Workers: {len(stats)}")
            for worker_name in stats.keys():
                print(f"   - {worker_name}")
        else:
            print(f"\n⚠️  Celery workers not detected")
            print("   Start Celery with: celery -A oxidane worker -l info")
    
    except Exception as e:
        print(f"\n⚠️  Could not connect to Celery: {e}")
        print("   Make sure Celery is running:")
        print("   celery -A oxidane worker -l info")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PAYMENT EMAIL DIAGNOSTIC TOOL")
    print("=" * 70)
    
    # 1. Check email configuration
    check_email_configuration()
    
    # 2. Check Celery status
    check_celery_status()
    
    # 3. Check recent payments
    recent_payment = check_recent_payments()
    
    # 4. Offer to send test email
    if recent_payment:
        print("\n" + "=" * 70)
        print("TEST EMAIL SENDING")
        print("=" * 70)
        
        response = input(f"\nDo you want to send a test receipt email to {recent_payment.billing_profile.user.email}? (y/n): ")
        
        if response.lower() == 'y':
            test_send_receipt_email(recent_payment)
        else:
            print("\n⏭️  Skipped test email sending")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\nNEXT STEPS:")
    print("1. Ensure email configuration is complete in Django admin")
    print("2. Start Celery worker if not running: celery -A oxidane worker -l info")
    print("3. Check Celery logs for email sending errors")
    print("4. Verify SMTP credentials are correct")
    print("=" * 70 + "\n")
