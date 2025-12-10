#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import User, Subscription, Payment
from django.utils import timezone

email = "ambflye@gmail.com"

print(f"\n=== Checking Telegram Invite Status for {email} ===\n")

try:
    user = User.objects.get(email=email)
    print(f"✓ User found: {user.first_name} {user.last_name}")
    print(f"  User ID: {user.id}")
    print(f"  Joined: {user.date_joined}")
    print(f"  Telegram User ID: {user.telegram_user_id or 'Not set'}")
    
    # Check subscriptions
    subscriptions = Subscription.objects.filter(
        billing_profile__user=user
    ).order_by('-created_at')
    
    print(f"\n--- Subscriptions ({subscriptions.count()}) ---")
    for sub in subscriptions:
        print(f"\n  Subscription ID: {sub.id}")
        print(f"  Plan: {sub.plan.name}")
        print(f"  Status: {sub.status}")
        print(f"  Created: {sub.created_at}")
        print(f"  Start: {sub.start_date}")
        print(f"  End: {sub.end_date}")
        print(f"  Is Active: {sub.is_active}")
    
    # Check payments
    payments = Payment.objects.filter(
        billing_profile__user=user
    ).order_by('-created_at')
    
    print(f"\n--- Payments ({payments.count()}) ---")
    for payment in payments:
        print(f"\n  Payment ID: {payment.id}")
        print(f"  Amount: {payment.currency} {payment.total_amount}")
        print(f"  Status: {payment.status}")
        print(f"  Gateway: {payment.payment_gateway}")
        print(f"  Reference: {payment.gateway_reference}")
        print(f"  Created: {payment.created_at}")
        print(f"  Paid At: {payment.paid_at or 'N/A'}")
    
    # Check Telegram groups
    print("\n--- Checking Telegram Group Membership ---")
    from subscriptions.models import TelegramGroup
    
    groups = TelegramGroup.objects.filter(associated_plans__in=[sub.plan for sub in subscriptions])
    print(f"\nExpected Telegram Groups ({groups.count()}):")
    for group in groups:
        print(f"  - {group.name} (ID: {group.chat_id})")
        print(f"    Invite Link: {group.invite_link or 'Not set'}")
    
    print("\n" + "="*60)
    print("To check if Telegram invite was sent, check Celery logs:")
    print("journalctl -u oxidane-celery.service | grep -i 'ambflye\\|telegram.*invite'")
    print("="*60)
    
except User.DoesNotExist:
    print(f"✗ User with email {email} not found")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
