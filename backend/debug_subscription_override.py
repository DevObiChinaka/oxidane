#!/usr/bin/env python
"""Check what happened with the latest payment"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Subscription, Payment

user_email = 'obbinachidera123@gmail.com'

print(f"Investigating subscription override issue...\n")
print("="*70)

# Get the latest payment (Mentorship)
latest_payment = Payment.objects.filter(
    billing_profile__user__email=user_email,
    status='success'
).order_by('-created_at').first()

print(f"\nLatest Payment:")
print(f"  Reference: {latest_payment.gateway_reference}")
print(f"  Plan: {latest_payment.subscription.plan.name if latest_payment.subscription else 'None'}")
print(f"  Status: {latest_payment.status}")
print(f"  Activation: {latest_payment.activation_status}")
print(f"  Subscription ID: {latest_payment.subscription.id if latest_payment.subscription else 'None'}")

# Get the subscription
if latest_payment.subscription:
    sub = latest_payment.subscription
    print(f"\nSubscription Details:")
    print(f"  ID: {sub.id}")
    print(f"  Plan: {sub.plan.name} ({sub.plan.billing_period})")
    print(f"  Created: {sub.created_at}")
    print(f"  Updated: {sub.updated_at}")
    print(f"  Status: {sub.status}")
    
    # Check all payments linked to this subscription
    all_payments = Payment.objects.filter(subscription=sub).order_by('created_at')
    print(f"\nAll Payments linked to this subscription:")
    for p in all_payments:
        print(f"  - {p.created_at.strftime('%H:%M:%S')} | {p.gateway_reference} | {p.status} | Activation: {p.activation_status}")

# Check all subscriptions for user
all_subs = Subscription.objects.filter(
    billing_profile__user__email=user_email
).order_by('created_at')

print(f"\n\nAll Subscriptions for user:")
for s in all_subs:
    print(f"  {s.id} | {s.plan.name} | {s.status} | Created: {s.created_at} | Updated: {s.updated_at}")
