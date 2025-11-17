#!/usr/bin/env python
"""Check user's subscriptions"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Subscription, Payment

user_email = 'obbinachidera123@gmail.com'

print(f"Checking subscriptions for: {user_email}\n")
print("="*70)

# All subscriptions
subs = Subscription.objects.filter(
    billing_profile__user__email=user_email
).order_by('-created_at')

print(f"\nTotal subscriptions: {subs.count()}\n")

for i, s in enumerate(subs, 1):
    print(f"{i}. {s.plan.name} ({s.plan.billing_period})")
    print(f"   Status: {s.status}")
    print(f"   Created: {s.created_at}")
    print(f"   Start: {s.start_date}")
    print(f"   End: {s.end_date}")
    print(f"   ID: {s.id}")
    print()

# Check recent payments
print("="*70)
print("\nRecent Payments:\n")

payments = Payment.objects.filter(
    billing_profile__user__email=user_email
).order_by('-created_at')[:5]

for i, p in enumerate(payments, 1):
    print(f"{i}. {p.currency} {p.total_amount}")
    print(f"   Plan: {p.subscription.plan.name if p.subscription else 'N/A'}")
    print(f"   Status: {p.status}")
    print(f"   Activation: {p.activation_status}")
    print(f"   Created: {p.created_at}")
    print(f"   Reference: {p.gateway_reference}")
    print()
