#!/usr/bin/env python
"""Check mentorship data in the database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import MentorshipPlan, MentorshipSubscription, OneOnOneSession
from users.models import User

print("=" * 60)
print("MENTORSHIP DATA CHECK")
print("=" * 60)

print(f"\n📊 Mentorship Plans: {MentorshipPlan.objects.count()}")
for plan in MentorshipPlan.objects.all():
    print(f"  - {plan.name} ({plan.plan_type}) - ${plan.price}")

print(f"\n👥 Mentorship Subscriptions: {MentorshipSubscription.objects.count()}")
for sub in MentorshipSubscription.objects.all()[:5]:
    print(f"  - {sub.user.email} - {sub.mentorship_plan.name} - {sub.subscription_status}")

print(f"\n📅 One-on-One Sessions: {OneOnOneSession.objects.count()}")
for session in OneOnOneSession.objects.all()[:5]:
    print(f"  - {session.mentorship_subscription.user.email} - {session.session_type} - {session.status}")

print("\n" + "=" * 60)
