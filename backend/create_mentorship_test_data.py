#!/usr/bin/env python
"""Create test mentorship data"""
import os
import django
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.utils import timezone
from subscriptions.models import MentorshipPlan, MentorshipSubscription
from users.models import User

print("Creating test mentorship data...")

# Create Mentorship Plans
plans_data = [
    {
        'plan_type': 'mentorship_basic',
        'name': 'Basic Mentorship',
        'description': 'Access to premium courses and mentorship community for 3 months',
        'price': Decimal('299.00'),
        'currency': 'USD',
        'premium_content_access': True,
        'telegram_group_access': True,
        'one_on_one_sessions': 0,
        'session_duration_minutes': 0,
        'is_active': True,
        'is_featured': False,
        'sort_order': 1,
        'features_list': [
            'Access to all premium courses',
            'Private Telegram mentorship group',
            'Weekly Q&A sessions',
            'Trading resources library',
            '3 months of support'
        ]
    },
    {
        'plan_type': 'mentorship_premium',
        'name': 'Premium Mentorship + 1-on-1',
        'description': 'Complete mentorship with personal 1-on-1 sessions',
        'price': Decimal('799.00'),
        'currency': 'USD',
        'premium_content_access': True,
        'telegram_group_access': True,
        'one_on_one_sessions': 3,
        'session_duration_minutes': 60,
        'is_active': True,
        'is_featured': True,
        'sort_order': 0,
        'features_list': [
            'Everything in Basic plan',
            '3 personal 1-on-1 sessions (60 min each)',
            'Direct access to mentor',
            'Personalized trading strategy',
            'Portfolio review and feedback',
            'Priority support'
        ]
    }
]

created_plans = []
for plan_data in plans_data:
    plan, created = MentorshipPlan.objects.get_or_create(
        plan_type=plan_data['plan_type'],
        defaults=plan_data
    )
    created_plans.append(plan)
    status = "✓ Created" if created else "✓ Already exists"
    print(f"{status}: {plan.name} - ${plan.price}")

# Create test subscriptions if there are users
users = User.objects.filter(is_active=True)[:3]
if users:
    print(f"\nCreating subscriptions for {len(users)} users...")
    
    for i, user in enumerate(users):
        # Alternate between plans
        plan = created_plans[i % len(created_plans)]
        
        # Check if subscription already exists
        existing = MentorshipSubscription.objects.filter(
            user=user,
            mentorship_plan=plan
        ).first()
        
        if not existing:
            now = timezone.now()
            subscription = MentorshipSubscription.objects.create(
                user=user,
                mentorship_plan=plan,
                paystack_reference=f'TEST_MENTOR_{user.id}_{now.timestamp()}',
                amount_paid=plan.price,
                currency=plan.currency,
                payment_status='verified',
                payment_verified_at=now,
                subscription_start=now,
                subscription_end=now + timedelta(days=90),  # 3 months
                subscription_status='active',
                telegram_username=f'@{user.username}',
                telegram_status='added' if i % 2 == 0 else 'pending_add',
                telegram_added_at=now if i % 2 == 0 else None,
                sessions_used=0 if plan.one_on_one_sessions == 0 else i,
                sessions_remaining=plan.one_on_one_sessions - (0 if plan.one_on_one_sessions == 0 else i),
            )
            print(f"  ✓ Created subscription for {user.email} - {plan.name}")
        else:
            print(f"  ✓ Subscription already exists for {user.email}")
else:
    print("\n⚠ No users found. Create users first to test subscriptions.")

print("\n✅ Done! Check the admin panel to see the data.")
