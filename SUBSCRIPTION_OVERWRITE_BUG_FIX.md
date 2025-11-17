# Subscription Overwrite Bug - Fixed ✅

## Issue
When purchasing a new subscription plan (Lifetime Mentorship), it overwrote the existing subscription (Weekly Signals) instead of creating a separate subscription.

## Root Cause
**File:** `backend/subscriptions/views/payment_views.py`  
**Lines:** 624 and 834

The payment callback views were using:
```python
Subscription.objects.update_or_create(
    billing_profile=billing_profile,  # ❌ WRONG - matches ANY subscription
    defaults={'plan': plan, ...}
)
```

This would find ANY existing subscription for that billing profile and update it with the new plan, regardless of what plan it was.

## Fix Applied
Changed both locations to:
```python
Subscription.objects.update_or_create(
    billing_profile=billing_profile,
    plan=plan,  # ✅ Now matches both billing_profile AND plan
    defaults={'status': 'active', ...}  # plan moved to lookup
)
```

Now it will only update a subscription if it's for the SAME plan. Different plans will create new subscriptions.

## Data Recovery
Restored the Weekly Signals subscription from payment `qq9g75is39wqg3p`:
- **Subscription ID:** `642ab1ca-785b-461a-8de9-29d3353d9786`
- **Plan:** Weekly Signals (weekly)
- **Start:** 2025-11-17 05:10:19
- **End:** 2025-11-24 05:10:19
- **Status:** Active

## Verification
User now has 2 active subscriptions:
1. ✅ Weekly Signals (weekly) - Expires Nov 24, 2025
2. ✅ Mentorship (lifetime) - Expires Oct 24, 2125

## Behavior After Fix
- **Same plan renewal:** Updates existing subscription (extends dates)
- **Different plan:** Creates NEW subscription (multi-subscription support)
- **Recurring limit:** Still enforced (max 1 recurring, unlimited lifetime)

## Testing Needed
1. Purchase a different plan → Should create 2nd subscription ✅
2. Renew same plan → Should update existing subscription dates
3. Try to buy 2nd recurring plan → Should show error about recurring limit
