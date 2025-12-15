"""
Restore Weekly Signals subscription for auto-renewal test
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.utils import timezone
from users.models import User
from subscriptions.models import Subscription, BillingProfile, SubscriptionPlan, PaymentMethod

# Get user
user = User.objects.get(email='derachinaka@gmail.com')
billing_profile = BillingProfile.objects.get(user=user)

# Get Weekly Signals plan
weekly_plan = SubscriptionPlan.objects.get(name='Weekly Signals')

# Get the Verve payment method
payment_method = PaymentMethod.objects.filter(
    billing_profile=billing_profile,
    is_active=True
).first()

if not payment_method:
    print("❌ No active payment method found")
    sys.exit(1)

# Create subscription ending today at 23:59 UTC for auto-renewal test
today = timezone.now().date()
end_datetime = timezone.make_aware(datetime.combine(today, datetime.max.time()))

# Start date: 7 days ago (original purchase)
start_date = timezone.now() - timedelta(days=8)

subscription = Subscription.objects.create(
    billing_profile=billing_profile,
    plan=weekly_plan,
    status='active',
    start_date=start_date,
    end_date=end_datetime,
    next_billing_date=end_datetime,
    auto_renew=True,  # Enable auto-renewal for testing
    payment_method=payment_method,
    currency='NGN',
    amount_paid=weekly_plan.get_price_in_currency('NGN')
)

print(f"\n{'='*70}")
print(f"✅ RESTORED WEEKLY SIGNALS SUBSCRIPTION")
print(f"{'='*70}\n")
print(f"User: {user.email}")
print(f"Plan: {subscription.plan.name}")
print(f"Status: {subscription.status}")
print(f"Start: {subscription.start_date}")
print(f"End: {subscription.end_date} (TODAY at 23:59 UTC)")
print(f"Next Billing: {subscription.next_billing_date}")
print(f"Auto-renew: {subscription.auto_renew} ✓")
print(f"Payment Method: {payment_method.card_type} ****{payment_method.last_four_digits}")
print(f"\n🎯 Ready for auto-renewal test at 2 AM UTC tomorrow!")
