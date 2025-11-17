# Subscription Display Fixes - Nov 17, 2025

## Issues Fixed

### 1. Lifetime Plan Showing as "RECURRING" ❌ → ✅
**Problem:**  
Frontend was checking `billing_cycle !== 'one_time' && !is_lifetime`, but lifetime plans have `billing_cycle === 'lifetime'`, so they passed the recurring check.

**Fix:**  
Updated recurring detection to explicitly exclude `'lifetime'`:
```typescript
const hasActiveRecurring = activeSubscriptions.some(sub => 
  sub.billing_cycle !== 'one_time' && 
  sub.billing_cycle !== 'lifetime' &&  // ← Added
  !sub.is_lifetime
);
```

### 2. Wrong Currency Displayed ❌ → ✅
**Problem:**  
User paid in NGN (₦43,142.43 for Weekly, ₦359,520.25 for Mentorship) but frontend was showing plan base price in USD, resulting in:
- Weekly: $30.00/week (should be ₦43,142.43/week)
- Mentorship: $250.00 one-time (should be ₦359,520.25 one-time)

**Fix:**  
- Backend now returns `amount` (what user paid) and `currency` (what they paid in)
- Frontend displays `amount` in user's payment currency
- Currency toggle converts between NGN ↔ USD
- Default currency set to what user paid in (NGN for this user)

### 3. Plan Price Showing $0.00 ❌ → ✅
**Problem:**  
Frontend was using `plan_base_price` (USD) but converting it incorrectly, resulting in $0.00.

**Fix:**  
Changed conversion logic to use actual `amount` paid:
```typescript
const convertSubscriptionAmounts = () => {
  subscriptions.forEach(sub => {
    const paidAmount = sub.amount || 0;
    const paidCurrency = sub.currency || 'USD';
    
    // Convert between currencies
    if (paidCurrency === displayCurrency) {
      converted[sub.id] = paidAmount;  // No conversion
    } else if (paidCurrency === 'NGN' && displayCurrency === 'USD') {
      converted[sub.id] = paidAmount / conversionRate;
    } else if (paidCurrency === 'USD' && displayCurrency === 'NGN') {
      converted[sub.id] = paidAmount * conversionRate;
    }
  });
};
```

### 4. Lifetime Plans Counted in Monthly Cost ❌ → ✅
**Problem:**  
Backend was adding lifetime plans to `total_monthly_cost` calculation.

**Fix:**  
Excluded lifetime plans from monthly cost:
```python
# Only add recurring plans to monthly cost
if is_active and sub.plan and sub.plan.billing_period != 'lifetime':
    # Calculate monthly equivalent
```

## Current Display

**Weekly Signals:**
- Shows: ₦43,142.43/week
- Type: RECURRING
- Paid in: NGN
- Toggle to USD: ~$26.15/week

**Mentorship:**
- Shows: ₦359,520.25 one-time
- Type: LIFETIME
- Paid in: NGN
- Toggle to USD: ~$217.89 one-time

## Files Modified

1. **backend/subscriptions/user_views.py**
   - Fixed monthly cost calculation to exclude lifetime plans
   - Use actual paid amounts instead of plan base prices
   - Return `monthly_cost_currency` in stats

2. **frontend/src/app/subscriptions/page.tsx**
   - Fixed lifetime plan detection (3 locations)
   - Changed conversion to use `amount` and `currency` from subscription
   - Set default currency to user's payment currency
   - Removed redundant "You paid" line
   - Added currency toggle hint

## Testing Checklist

- [x] Lifetime plan shows "LIFETIME" badge, not "RECURRING"
- [x] Weekly plan shows correct NGN price per week
- [x] Lifetime plan shows correct NGN one-time price
- [x] Currency toggle works (NGN ↔ USD)
- [x] Default currency is NGN (what user paid in)
- [x] Monthly cost only includes recurring plans
- [ ] Purchase new plan → verify prices still show correctly
- [ ] Currency conversion rates update properly
