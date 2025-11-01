"""
Check all subscriptions in the database
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import SignalSubscription, MentorshipSubscription
from django.utils import timezone

User = get_user_model()

print("=" * 80)
print("📊 SUBSCRIPTION DATABASE CHECK")
print("=" * 80)

# Check all users with subscriptions
print("\n👥 USERS WITH SUBSCRIPTIONS:")
print("-" * 80)

for user in User.objects.all():
    signal_count = SignalSubscription.objects.filter(user=user).count()
    mentorship_count = MentorshipSubscription.objects.filter(user=user).count()
    
    if signal_count > 0 or mentorship_count > 0:
        print(f"\n📧 {user.email} (ID: {user.id})")
        print(f"   Username: {user.username}")
        print(f"   Signal Subscriptions: {signal_count}")
        print(f"   Mentorship Subscriptions: {mentorship_count}")

# Check chiderachinaka06 specifically
print("\n" + "=" * 80)
print("🔍 CHECKING chiderachinaka06 ACCOUNT")
print("=" * 80)

try:
    chidera = User.objects.get(email='chiderachinaka06@gmail.com')
    print(f"\n✅ User found:")
    print(f"   Email: {chidera.email}")
    print(f"   Username: {chidera.username}")
    print(f"   ID: {chidera.id}")
    print(f"   Is Active: {chidera.is_active}")
    
    # Check Signal Subscriptions
    print(f"\n📡 SIGNAL SUBSCRIPTIONS:")
    print("-" * 80)
    signal_subs = SignalSubscription.objects.filter(user=chidera)
    
    if signal_subs.exists():
        for sub in signal_subs:
            print(f"\n   Subscription ID: {sub.id}")
            print(f"   Plan Type: {sub.plan_type}")
            print(f"   Amount Paid: ${sub.amount_paid}")
            print(f"   Payment Status: {sub.payment_status}")
            print(f"   Reference: {sub.paystack_reference}")
            
            if sub.pricing_plan:
                print(f"   Pricing Plan: {sub.pricing_plan.name}")
            else:
                print(f"   Pricing Plan: None")
            
            if sub.subscription_start:
                print(f"   Start Date: {sub.subscription_start}")
                print(f"   End Date: {sub.subscription_end}")
                
                # Check if active
                is_active = (
                    sub.payment_status == 'verified' and
                    sub.subscription_end and
                    timezone.now() <= sub.subscription_end
                )
                print(f"   Is Active: {is_active}")
                
                if is_active:
                    days_left = (sub.subscription_end - timezone.now()).days
                    print(f"   Days Remaining: {days_left}")
            else:
                print(f"   Start Date: Not set")
                print(f"   End Date: Not set")
            
            print(f"   Auto Renewal: {sub.auto_renewal}")
            print(f"   Telegram Username: {sub.telegram_username}")
            print(f"   Telegram Status: {sub.telegram_status}")
            print(f"   Created: {sub.created_at}")
    else:
        print("   ❌ No signal subscriptions found")
    
    # Check Mentorship Subscriptions
    print(f"\n📚 MENTORSHIP SUBSCRIPTIONS:")
    print("-" * 80)
    mentorship_subs = MentorshipSubscription.objects.filter(user=chidera)
    
    if mentorship_subs.exists():
        for sub in mentorship_subs:
            print(f"\n   Subscription ID: {sub.id}")
            print(f"   Plan: {sub.mentorship_plan.name if sub.mentorship_plan else 'None'}")
            print(f"   Amount Paid: ${sub.amount_paid}")
            print(f"   Payment Status: {sub.payment_status}")
            print(f"   Subscription Status: {sub.subscription_status}")
            print(f"   Reference: {sub.paystack_reference}")
            
            if sub.subscription_start:
                print(f"   Start Date: {sub.subscription_start}")
                print(f"   End Date: {sub.subscription_end}")
                print(f"   Is Active: {sub.is_active}")
                
                if sub.is_active:
                    print(f"   Days Remaining: {sub.days_remaining}")
            else:
                print(f"   Start Date: Not set")
                print(f"   End Date: Not set")
            
            print(f"   Telegram Username: {sub.telegram_username}")
            print(f"   Created: {sub.created_at}")
    else:
        print("   ❌ No mentorship subscriptions found")

except User.DoesNotExist:
    print("\n❌ User 'chiderachinaka06@gmail.com' not found!")
    print("\n📋 Available users:")
    for user in User.objects.all()[:10]:
        print(f"   - {user.email} ({user.username})")

print("\n" + "=" * 80)
print("📊 TOTAL COUNTS")
print("=" * 80)
print(f"Total Signal Subscriptions: {SignalSubscription.objects.count()}")
print(f"Total Mentorship Subscriptions: {MentorshipSubscription.objects.count()}")
print(f"Total Users: {User.objects.count()}")
print("=" * 80)
