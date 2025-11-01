#!/usr/bin/env python
"""
Create initial pricing plans for the simplified structure:
- Mentorship (one-time, lifetime access)
- Signals (weekly, monthly, VIP)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import PricingPlan
from decimal import Decimal

def create_pricing_plans():
    print("Creating simplified pricing plans...")
    
    # 1. MENTORSHIP - One-time payment for lifetime course access
    mentorship_plan, created = PricingPlan.objects.update_or_create(
        plan_type='mentorship',
        defaults={
            'plan_category': 'mentorship',
            'billing_cycle': 'one_time',
            'name': 'Mentorship Program',
            'description': 'One-time payment for lifetime access to all premium courses. Includes mentorship group access and 1-on-1 session opportunities (arranged offline).',
            'price': Decimal('799.00'),
            'currency': 'USD',
            'duration_days': None,  # Lifetime access
            'gives_course_access': True,
            'gives_signals_access': False,
            'telegram_group_key': 'mentorship',
            'is_active': True,
            'is_featured': True,
            'sort_order': 1,
            'features_list': [
                'Lifetime access to all premium courses',
                'Access to mentorship Telegram group',
                '1-on-1 mentorship sessions (arranged offline)',
                'Course completion certificates',
                'Lifetime course updates',
                'No recurring fees',
            ],
            'call_to_action': 'Get Lifetime Access'
        }
    )
    status = "Created" if created else "Updated"
    print(f"✓ {status}: {mentorship_plan.name} - ${mentorship_plan.price}")
    
    # 2. WEEKLY SIGNALS
    weekly_plan, created = PricingPlan.objects.update_or_create(
        plan_type='signals_weekly',
        defaults={
            'plan_category': 'signals',
            'billing_cycle': 'weekly',
            'name': 'Weekly Signals',
            'description': 'Access to forex trading signals for 7 days. Perfect for trying out the service.',
            'price': Decimal('29.00'),
            'currency': 'USD',
            'duration_days': 7,
            'gives_course_access': False,
            'gives_signals_access': True,
            'telegram_group_key': 'signals',
            'is_active': True,
            'is_featured': False,
            'sort_order': 2,
            'features_list': [
                '7 days of trading signals',
                'Access to signals Telegram group',
                'Real-time trade alerts',
                'Market analysis updates',
                'Entry and exit points',
            ],
            'call_to_action': 'Subscribe Weekly'
        }
    )
    status = "Created" if created else "Updated"
    print(f"✓ {status}: {weekly_plan.name} - ${weekly_plan.price}/week")
    
    # 3. MONTHLY SIGNALS
    monthly_plan, created = PricingPlan.objects.update_or_create(
        plan_type='signals_monthly',
        defaults={
            'plan_category': 'signals',
            'billing_cycle': 'monthly',
            'name': 'Monthly Signals',
            'description': 'Access to forex trading signals for 30 days. Best value for regular traders.',
            'price': Decimal('99.00'),
            'currency': 'USD',
            'duration_days': 30,
            'gives_course_access': False,
            'gives_signals_access': True,
            'telegram_group_key': 'signals',
            'is_active': True,
            'is_featured': True,
            'sort_order': 3,
            'features_list': [
                '30 days of trading signals',
                'Access to signals Telegram group',
                'Real-time trade alerts',
                'Market analysis updates',
                'Entry and exit points',
                'Better value than weekly',
            ],
            'call_to_action': 'Subscribe Monthly'
        }
    )
    status = "Created" if created else "Updated"
    print(f"✓ {status}: {monthly_plan.name} - ${monthly_plan.price}/month")
    
    # 4. VIP SIGNALS - Premium tier
    vip_plan, created = PricingPlan.objects.update_or_create(
        plan_type='vip_monthly',
        defaults={
            'plan_category': 'signals',
            'billing_cycle': 'monthly',
            'name': 'VIP Signals',
            'description': 'Premium trading signals with exclusive VIP group access. Includes trade bias and educational insights.',
            'price': Decimal('299.00'),
            'currency': 'USD',
            'duration_days': 30,
            'gives_course_access': False,
            'gives_signals_access': True,
            'telegram_group_key': 'vip',
            'is_active': True,
            'is_featured': True,
            'sort_order': 4,
            'features_list': [
                '30 days of premium VIP signals',
                'Access to exclusive VIP Telegram group',
                'Priority real-time trade alerts',
                'Detailed trade bias and analysis',
                'Educational trading tips',
                'Market sentiment updates',
                'VIP-only market insights',
            ],
            'call_to_action': 'Go VIP'
        }
    )
    status = "Created" if created else "Updated"
    print(f"✓ {status}: {vip_plan.name} - ${vip_plan.price}/month")
    
    print("\n✅ All pricing plans created successfully!")
    print("\nSummary:")
    print("=" * 60)
    print(f"{'Plan Type':<30} {'Price':<15} {'Access':<15}")
    print("=" * 60)
    print(f"{'Mentorship (Lifetime)':<30} ${mentorship_plan.price:<14} Courses")
    print(f"{'Weekly Signals':<30} ${weekly_plan.price}/week{'':<6} Signals")
    print(f"{'Monthly Signals':<30} ${monthly_plan.price}/month{'':<5} Signals")
    print(f"{'VIP Signals':<30} ${vip_plan.price}/month{'':<5} VIP Group")
    print("=" * 60)

if __name__ == '__main__':
    create_pricing_plans()
