#!/usr/bin/env python
"""
Manually send Telegram invite directly (without queuing)
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
user_email = "obinnachiderachinaka@gmail.com"

print(f"\n=== Sending Telegram Invite to {user_email} (Direct Execution) ===\n")

try:
    # Get user
    user = User.objects.get(email=user_email)
    print(f"✓ User found: {user.first_name} {user.last_name}")
    
    # Get active subscription
    active_sub = Subscription.objects.filter(
        billing_profile__user=user,
        status='active'
    ).first()
    
    if not active_sub:
        print("✗ No active subscription found")
        sys.exit(1)
    
    print(f"✓ Active subscription: {active_sub.plan.name}")
    
    # Clear the cache
    cache_key = f"telegram_invite_sent:{user.id}:{active_sub.plan.id}"
    cache.delete(cache_key)
    print(f"✓ Cleared cache")
    
    # Execute task directly (synchronously, no queue)
    print("\n📤 Sending Telegram invite (direct execution)...")
    
    # Call the task's run method directly
    result = add_user_to_telegram_groups.run(str(user.id), str(active_sub.plan.id))
    
    print(f"\n✅ Result: {result}")
    print("\nTelegram invite sent directly!")
    
except User.DoesNotExist:
    print(f"✗ User not found: {user_email}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
