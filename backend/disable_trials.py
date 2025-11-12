#!/usr/bin/env python
"""
Script to disable trials across all subscription plans.
Part of trial removal strategy - Phase 1: Database Update

This script:
1. Updates all SubscriptionPlan records to trial_days=0
2. Reports current trial status before and after
3. Keeps database fields intact for backward compatibility
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import SubscriptionPlan, Subscription
from django.db.models import Count, Q

def main():
    print("=" * 70)
    print("TRIAL REMOVAL - PHASE 1: DATABASE UPDATE")
    print("=" * 70)
    print()
    
    # Report current state
    print("📊 CURRENT STATE")
    print("-" * 70)
    
    all_plans = SubscriptionPlan.objects.all()
    trial_plans = all_plans.filter(trial_days__gt=0)
    no_trial_plans = all_plans.filter(trial_days=0)
    
    print(f"Total Plans: {all_plans.count()}")
    print(f"  - Plans with trials (trial_days > 0): {trial_plans.count()}")
    print(f"  - Plans without trials (trial_days = 0): {no_trial_plans.count()}")
    print()
    
    if trial_plans.exists():
        print("Plans currently offering trials:")
        for plan in trial_plans:
            print(f"  • {plan.name} - {plan.trial_days} days trial (${plan.base_price}/{plan.billing_period})")
    else:
        print("  ✓ No plans currently offer trials")
    print()
    
    # Report existing trial subscriptions
    print("📊 EXISTING TRIAL SUBSCRIPTIONS")
    print("-" * 70)
    
    active_trials = Subscription.objects.filter(
        is_trial=True,
        status='active'
    )
    
    all_trials = Subscription.objects.filter(is_trial=True)
    
    print(f"Total trial subscriptions ever created: {all_trials.count()}")
    print(f"Active trial subscriptions: {active_trials.count()}")
    
    if active_trials.exists():
        print("\nActive trials (will continue to convert normally):")
        for sub in active_trials[:5]:  # Show first 5
            user_email = sub.billing_profile.user.email if sub.billing_profile and sub.billing_profile.user else 'N/A'
            print(f"  • User: {user_email} | Plan: {sub.plan.name} | Ends: {sub.trial_end_date}")
        if active_trials.count() > 5:
            print(f"  ... and {active_trials.count() - 5} more")
    else:
        print("  ✓ No active trial subscriptions")
    print()
    
    # Confirm action
    print("🔄 ACTION TO BE TAKEN")
    print("-" * 70)
    print("Will update ALL plans to trial_days=0")
    print("This will prevent NEW trial subscriptions from being created.")
    print()
    print("✅ BACKWARD COMPATIBILITY:")
    print("  - Database fields (trial_days, is_trial, trial_end_date) will remain")
    print("  - Existing trial subscriptions will continue to work")
    print("  - Trial conversion tasks will continue to function")
    print("  - Users with active trials will convert to paid normally")
    print()
    
    # Get confirmation
    response = input("Proceed with update? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("\n❌ Update cancelled by user")
        return
    
    print()
    print("🔧 UPDATING PLANS...")
    print("-" * 70)
    
    # Perform update
    updated_count = SubscriptionPlan.objects.all().update(trial_days=0)
    
    print(f"✓ Updated {updated_count} plan(s) to trial_days=0")
    print()
    
    # Verify update
    print("✅ VERIFICATION")
    print("-" * 70)
    
    plans_after = SubscriptionPlan.objects.all()
    trial_plans_after = plans_after.filter(trial_days__gt=0)
    no_trial_plans_after = plans_after.filter(trial_days=0)
    
    print(f"Total Plans: {plans_after.count()}")
    print(f"  - Plans with trials (trial_days > 0): {trial_plans_after.count()}")
    print(f"  - Plans without trials (trial_days = 0): {no_trial_plans_after.count()}")
    print()
    
    if trial_plans_after.count() == 0:
        print("✅ SUCCESS: All plans now have trial_days=0")
        print("✅ New subscriptions will be paid (with optional coupon discounts)")
        print("✅ Existing trial subscriptions remain unaffected")
    else:
        print("⚠️ WARNING: Some plans still have trial_days > 0")
        for plan in trial_plans_after:
            print(f"  • {plan.name} - {plan.trial_days} days")
    
    print()
    print("=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)
    print()
    print("📋 NEXT STEPS:")
    print("  1. Phase 2: Update backend payment logic (payment_views.py)")
    print("  2. Phase 3: Update frontend UI (remove trial badges/messaging)")
    print("  3. Phase 4: Update admin interface (hide trial_days field)")
    print("  4. Phase 5: Test payment flow and existing trial conversions")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
