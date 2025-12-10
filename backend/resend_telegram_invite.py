#!/usr/bin/env python
"""
Manually resend Telegram invite to a specific user
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import User, Subscription
from subscriptions.tasks import add_user_to_telegram_groups
from django.core.cache import cache

# User email
user_email = "ambflye@gmail.com"

print(f"\n=== Resending Telegram Invite to {user_email} ===\n")

try:
    # Get user
    user = User.objects.get(email=user_email)
    print(f"✓ User found: {user.first_name} {user.last_name}")
    print(f"  User ID: {user.id}")
    
    # Get active subscription
    active_sub = Subscription.objects.filter(
        billing_profile__user=user,
        status='active'
    ).first()
    
    if not active_sub:
        print("✗ No active subscription found")
        sys.exit(1)
    
    print(f"✓ Active subscription: {active_sub.plan.name}")
    print(f"  Plan ID: {active_sub.plan.id}")
    
    # Clear the cache to allow resending
    cache_key = f"telegram_invite_sent:{user.id}:{active_sub.plan.id}"
    cache.delete(cache_key)
    print(f"✓ Cleared cache: {cache_key}")
    
    # Trigger the task
    print("\n📤 Sending Telegram invite...")
    result = add_user_to_telegram_groups.delay(str(user.id), str(active_sub.plan.id))
    
    print(f"✅ Task queued: {result.id}")
    print("\nCheck Celery logs to confirm delivery:")
    print("journalctl -u oxidane-celery.service -f")
    
except User.DoesNotExist:
    print(f"✗ User not found: {user_email}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
