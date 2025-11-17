"""Check subscription data for debugging"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import Subscription
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.filter(email='obbinachidera123@gmail.com').first()

if not user:
    print("User not found!")
else:
    print(f"User: {user.email}")
    
    # Check ALL subscriptions
    all_subs = Subscription.objects.filter(billing_profile__user=user)
    print(f"\nAll Subscriptions ({all_subs.count()}):")
    for s in all_subs:
        print(f"\n  Plan: {s.plan.name if s.plan else 'No Plan'}")
        print(f"  Status: {s.status}")
        print(f"  Amount Paid: {s.amount_paid} {s.currency}")
        print(f"  Plan Base Price: {s.plan.base_price if s.plan else 0}")
        print(f"  Billing Period: {s.plan.billing_period if s.plan else 'N/A'}")
        print(f"  Start Date: {s.start_date}")
        print(f"  End Date: {s.end_date}")
        print(f"  Auto Renew: {s.auto_renew}")
        
        # Check features
        if s.plan:
            features = s.plan.features.all()
            print(f"  Features ({features.count()}):")
            for f in features:
                print(f"    - {f.name} (category: {f.category})")
    
    # Check active subscriptions
    active_subs = Subscription.objects.filter(billing_profile__user=user, status='active')
    print(f"\n\nActive Subscriptions ({active_subs.count()}):")
