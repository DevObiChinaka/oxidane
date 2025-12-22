"""
Investigate why auto-renewal failed for Weekly Signals subscription
"""
import os
import django
from datetime import datetime, timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Subscription, SubscriptionPlan, BillingProfile
from django.contrib.auth import get_user_model

User = get_user_model()

def investigate_autorenewal():
    print("\n" + "="*80)
    print("AUTO-RENEWAL INVESTIGATION")
    print("="*80)
    
    # Get the user
    user = User.objects.filter(email='derachinaka@gmail.com').first()
    if not user:
        print("❌ User not found!")
        return
    
    print(f"\n📧 User: {user.email}")
    print(f"👤 User ID: {user.id}")
    
    # Get billing profile
    billing_profile = BillingProfile.objects.filter(user=user).first()
    if not billing_profile:
        print("❌ No billing profile found!")
        return
    
    print(f"💳 Billing Profile ID: {billing_profile.id}")
    
    # Get all subscriptions for this user
    user_subs = Subscription.objects.filter(billing_profile=billing_profile).order_by('-created_at')
    
    print(f"\n📊 Total Subscriptions: {user_subs.count()}")
    print("\n" + "-"*80)
    
    for idx, sub in enumerate(user_subs, 1):
        print(f"\n{idx}. Subscription ID: {sub.id}")
        print(f"   Plan: {sub.plan.name if sub.plan else 'N/A'}")
        print(f"   Status: {sub.status}")
        print(f"   Auto Renew: {sub.auto_renew}")
        print(f"   Start: {sub.start_date}")
        print(f"   End: {sub.end_date}")
        print(f"   Next Billing: {sub.next_billing_date}")
        print(f"   Created: {sub.created_at}")
        print(f"   Updated: {sub.updated_at}")
        
        # Check if this was the Weekly Signals that should have renewed
        if sub.plan and sub.plan.name == "Weekly Signals":
            print(f"\n   🔍 WEEKLY SIGNALS DETAILS:")
            print(f"   - Payment Method: {sub.payment_method}")
            if sub.payment_method:
                print(f"   - Payment Method Type: {sub.payment_method.payment_type}")
                print(f"   - Payment Method Active: {sub.payment_method.is_active}")
                if hasattr(sub.payment_method, 'authorization_code'):
                    print(f"   - Authorization Code: {sub.payment_method.authorization_code}")
            print(f"   - Currency: {sub.currency}")
            print(f"   - Amount Paid: {sub.amount_paid}")
            print(f"   - Metadata: {sub.metadata}")
            
            # Check if end_date was today
            if sub.end_date:
                time_diff = datetime.now(timezone.utc) - sub.end_date
                print(f"   - Time since end_date: {time_diff}")
                print(f"   - Should have renewed: {sub.auto_renew and time_diff.total_seconds() > 0}")
    
    print("\n" + "-"*80)
    
    # Check for Weekly Signals subscription plan
    weekly_signals = SubscriptionPlan.objects.filter(name="Weekly Signals").first()
    if weekly_signals:
        print(f"\n📋 Weekly Signals Plan Config:")
        print(f"   - ID: {weekly_signals.id}")
        print(f"   - Name: {weekly_signals.name}")
        print(f"   - Duration Days: {weekly_signals.duration_days}")
        print(f"   - Is Active: {weekly_signals.is_active}")
        print(f"   - NGN Price: {weekly_signals.price_ngn}")
        print(f"   - USD Price: {weekly_signals.price_usd}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    investigate_autorenewal()
