#!/usr/bin/env python
"""
Manually activate pending payments
This script will directly activate payments that are stuck in pending status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Payment
from subscriptions.tasks import activate_subscription

print("=" * 70)
print("ACTIVATING PENDING PAYMENTS")
print("=" * 70)

# Find payments that need activation
pending_payments = Payment.objects.filter(
    status='success',
    activation_status='pending'
).order_by('created_at')

print(f"\nFound {pending_payments.count()} pending payments\n")

if pending_payments.count() == 0:
    print("✅ No pending payments to activate!")
else:
    for i, payment in enumerate(pending_payments, 1):
        print(f"{i}. Processing payment: {payment.gateway_reference}")
        print(f"   User: {payment.billing_profile.user.email}")
        print(f"   Amount: {payment.currency} {payment.total_amount}")
        print(f"   Created: {payment.created_at}")
        
        try:
            # Call activation task directly (not .delay() since Celery might not be running)
            result = activate_subscription(payment.id)
            
            if result.get('success'):
                print(f"   ✅ Activated successfully!")
                if result.get('subscription_id'):
                    print(f"   📋 Subscription ID: {result['subscription_id']}")
            else:
                print(f"   ⚠️  Activation returned: {result}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print()

print("=" * 70)
print("ACTIVATION COMPLETE")
print("=" * 70)
