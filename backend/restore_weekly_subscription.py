#!/usr/bin/env python
"""Restore the Weekly Signals subscription that was overwritten"""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Subscription, Payment, SubscriptionPlan
from django.utils import timezone

user_email = 'obbinachidera123@gmail.com'

# Find the payment that created the Weekly Signals subscription
weekly_payments = Payment.objects.filter(
    billing_profile__user__email=user_email,
    status='success'
).order_by('created_at')

print("Looking for Weekly Signals payment...")
for p in weekly_payments:
    print(f"{p.created_at} | Ref: {p.gateway_reference} | Activation: {p.activation_status}")

# Get the Weekly Signals plan
weekly_plan = SubscriptionPlan.objects.filter(
    name__icontains='Weekly',
    billing_period='weekly'
).first()

if not weekly_plan:
    print("\nERROR: Could not find Weekly Signals plan")
    exit(1)

print(f"\nFound plan: {weekly_plan.name} ({weekly_plan.billing_period})")

# Find the payment for weekly plan - it's likely one of the early completed ones
# Let's check payment reference "qq9g75is39wqg3p" which was completed
target_payment = Payment.objects.get(gateway_reference='qq9g75is39wqg3p')
print(f"\nTarget payment: {target_payment.gateway_reference}")
print(f"  Amount: {target_payment.currency} {target_payment.amount}")
print(f"  Created: {target_payment.created_at}")
print(f"  Current subscription: {target_payment.subscription.plan.name if target_payment.subscription else 'None'}")

# Create new subscription for Weekly Signals
start_date = target_payment.created_at
end_date = start_date + timedelta(days=7)

new_subscription = Subscription.objects.create(
    billing_profile=target_payment.billing_profile,
    plan=weekly_plan,
    status='active',
    start_date=start_date,
    end_date=end_date,
    amount_paid=target_payment.amount,
    currency=target_payment.currency,
    auto_renew=True,
    payment_method=target_payment.payment_method,
    next_billing_date=end_date
)

print(f"\n✅ Created new Weekly Signals subscription:")
print(f"  ID: {new_subscription.id}")
print(f"  Plan: {new_subscription.plan.name}")
print(f"  Start: {new_subscription.start_date}")
print(f"  End: {new_subscription.end_date}")

# Link the payment to this subscription
target_payment.subscription = new_subscription
target_payment.save()

print(f"\n✅ Linked payment {target_payment.gateway_reference} to new subscription")

# Verify both subscriptions exist
all_subs = Subscription.objects.filter(
    billing_profile__user__email=user_email
).order_by('created_at')

print(f"\n\nAll subscriptions now:")
for s in all_subs:
    print(f"  {s.plan.name} ({s.plan.billing_period}) | Status: {s.status} | Ends: {s.end_date}")
