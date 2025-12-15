"""
Delete subscription for a specific user
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import User
from subscriptions.models import Subscription, BillingProfile

# Get user email from command line or use default
email = sys.argv[1] if len(sys.argv) > 1 else 'derachinaka@gmail.com'

try:
    user = User.objects.get(email=email)
    print(f"\n{'='*70}")
    print(f"USER: {user.email}")
    print(f"{'='*70}\n")
    
    # Get user's billing profile
    billing_profile = BillingProfile.objects.filter(user=user).first()
    
    if not billing_profile:
        print("❌ No billing profile found for this user")
        sys.exit(0)
    
    subs = Subscription.objects.filter(billing_profile=billing_profile)
    
    if not subs.exists():
        print("❌ No subscriptions found for this user")
        sys.exit(0)
    
    print(f"Found {subs.count()} subscription(s):\n")
    
    for sub in subs:
        print(f"📋 Subscription ID: {sub.id}")
        print(f"   Plan: {sub.plan.name if sub.plan else 'None'}")
        print(f"   Status: {sub.status}")
        print(f"   Start: {sub.start_date}")
        print(f"   End: {sub.end_date}")
        print(f"   Auto-renew: {sub.auto_renew}")
        print(f"   Payment Method: {sub.payment_method or 'None'}")
        print()
    
    # Confirm deletion
    confirm = input(f"⚠️  Delete ALL {subs.count()} subscription(s)? (yes/no): ")
    
    if confirm.lower() == 'yes':
        deleted_count = subs.count()
        subs.delete()
        print(f"\n✅ Successfully deleted {deleted_count} subscription(s) for {user.email}")
    else:
        print("\n❌ Deletion cancelled")
        
except User.DoesNotExist:
    print(f"❌ User not found: {email}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
