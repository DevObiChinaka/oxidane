#!/usr/bin/env python
"""
Check recent payments and Telegram invites
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Payment, User
from django.utils import timezone
from datetime import timedelta

print("\n=== Recent Payments (Last 2 Hours) ===\n")

# Get payments from last 2 hours
two_hours_ago = timezone.now() - timedelta(hours=2)
recent_payments = Payment.objects.filter(
    created_at__gte=two_hours_ago,
    status='success'
).select_related('billing_profile__user', 'subscription__plan').order_by('-created_at')

for payment in recent_payments[:5]:
    user = payment.billing_profile.user
    print(f"Payment: {payment.gateway_reference}")
    print(f"  User: {user.email} ({user.first_name} {user.last_name})")
    print(f"  Amount: {payment.currency} {payment.total_amount}")
    print(f"  Time: {payment.paid_at or payment.created_at}")
    if payment.subscription:
        print(f"  Plan: {payment.subscription.plan.name}")
        print(f"  Subscription Status: {payment.subscription.status}")
    
    # Check telegram info
    profile = payment.billing_profile
    print(f"  Telegram Username: {profile.telegram_username or 'Not set'}")
    print(f"  Telegram User ID: {profile.telegram_user_id or 'Not set'}")
    print()
