"""
Test that Celery eager mode works and emails are sent synchronously
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Payment
from subscriptions.tasks import send_payment_receipt_email

def test_eager_mode():
    """Test that eager mode sends emails synchronously"""
    
    print("=" * 70)
    print("TESTING CELERY EAGER MODE")
    print("=" * 70)
    
    # Check if eager mode is enabled
    from django.conf import settings
    eager_enabled = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    
    print(f"\n✓ CELERY_TASK_ALWAYS_EAGER: {eager_enabled}")
    
    if not eager_enabled:
        print("\n⚠️  Eager mode is NOT enabled!")
        print("   Add USE_CELERY_EAGER=True to your .env file")
        return
    
    print("\n✅ Eager mode is ENABLED - tasks will run synchronously")
    
    # Get a recent successful payment
    payment = Payment.objects.filter(status='success').order_by('-paid_at').first()
    
    if not payment:
        print("\n⚠️  No successful payments found to test with")
        return
    
    print(f"\n📧 Testing email for payment: {payment.id}")
    print(f"   Recipient: {payment.billing_profile.user.email}")
    print(f"\n🔄 Calling send_payment_receipt_email.delay()...")
    print("   (In eager mode, this will execute immediately, not queue)")
    
    # This will execute synchronously in eager mode
    result = send_payment_receipt_email.delay(payment.id)
    
    print(f"\n✅ Task completed synchronously!")
    print(f"   Result: {result}")
    print(f"\n📬 Email should have been sent to: {payment.billing_profile.user.email}")
    
    print("\n" + "=" * 70)
    print("HOW IT WORKS IN EAGER MODE:")
    print("=" * 70)
    print("""
    Without Celery Worker:
    - .delay() queues task in Redis ❌ (never executes)
    
    With Eager Mode Enabled:
    - .delay() executes immediately ✅ (blocks until complete)
    - Email sent during the request
    - No Celery worker needed
    
    Production Setup:
    - Disable eager mode (USE_CELERY_EAGER=False)
    - Run Celery worker
    - Tasks execute asynchronously
    """)
    print("=" * 70)

if __name__ == '__main__':
    test_eager_mode()
