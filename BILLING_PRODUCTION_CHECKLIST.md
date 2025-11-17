# Billing Page - Production Readiness Checklist

## ✅ Fixed Issues (January 2025)

### 1. Width Issue - RESOLVED
- **Problem**: Billing page appeared narrower than subscriptions page
- **Root Cause**: Using `max-w-5xl` instead of `max-w-7xl`
- **Solution**: Updated container to match subscriptions page width
  ```tsx
  // Before: max-w-5xl
  // After:  max-w-7xl
  <div className="p-4 sm:p-6 lg:p-8 max-w-7xl">
  ```

### 2. Paystack Not Loading - RESOLVED
- **Problem**: "Payment system is loading" alert when clicking Update Card
- **Root Cause**: Paystack script not loaded in layout
- **Solution**: Added Paystack inline script to root layout
  ```tsx
  // Added to frontend/src/app/layout.tsx
  <script src="https://js.paystack.co/v1/inline.js"></script>
  ```

## 🧪 Testing Instructions

### Test Card Update Flow

1. **Navigate to Billing Page**
   - Go to `/billing`
   - Verify page width matches subscriptions page
   - Verify tabs render correctly

2. **Add First Card (if none exists)**
   - Click "Add Card" button
   - Paystack modal should open (no alert)
   - Use test card: `5060666666666666666`
   - CVV: `123`
   - Expiry: `12/25`
   - PIN: `1234`
   - Verify ₦50 charge successful
   - Card should save and display as "Primary"
   - Badge should show "Use for: All subscriptions"

3. **Update Existing Card**
   - Click "Update Card" button
   - Should show amber warning: "This will replace your current card and all subscriptions will use the new card"
   - Click "Continue"
   - Paystack modal opens
   - Use different test card: `4084084084084081`
   - Complete verification (₦50 charge)
   - Old card should be deactivated
   - New card should display as "Primary"
   - Verify ₦50 refund in Paystack dashboard

4. **Delete Card**
   - Click "Remove" button
   - Verify warning: "This will remove your payment method and disable auto-renewal on ALL subscriptions"
   - Confirm deletion
   - Card should be removed from display
   - "Add Card" button should appear
   - Check backend: All active subscriptions should have auto-renewal disabled

5. **Edge Cases**
   - Test declined card (use `5060666666666666666` with CVV `000`)
   - Test network error during save
   - Test rapid clicking of Update Card button
   - Test with multiple active subscriptions
   - Verify mobile responsiveness

## 🔧 Backend Verification

### Payment Method Enforcement

```bash
# Check only one active card per user
python backend/manage.py shell

from subscriptions.models import PaymentMethod, BillingProfile
from django.contrib.auth.models import User

# Get a test user
user = User.objects.get(email='test@example.com')
profile = user.billing_profile

# Should return max 1 active card
active_cards = PaymentMethod.objects.filter(
    billing_profile=profile,
    is_active=True
)
print(f"Active cards: {active_cards.count()}")  # Should be 0 or 1
```

### Subscription Auto-Renewal Check

```bash
# Verify subscriptions use the payment method
from subscriptions.models import Subscription

# Get user subscriptions
subs = Subscription.objects.filter(user=user, status='active')

for sub in subs:
    print(f"Subscription: {sub.plan.name}")
    print(f"Auto-renew: {sub.auto_renew}")
    print(f"Payment method: {sub.payment_method}")
    print("---")
```

## 🚀 Pre-Production Checklist

### Environment Variables
- [ ] `NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY` set to **LIVE** key (not test)
- [ ] Backend Paystack secret key set to **LIVE** key
- [ ] Webhook URL configured in Paystack dashboard
- [ ] Webhook secret configured in backend

### Security
- [ ] HTTPS enforced on production domain
- [ ] CORS settings allow only production domain
- [ ] Rate limiting enabled on `/payment-methods/save/` endpoint
- [ ] CSRF protection enabled
- [ ] JWT tokens secured

### Payment Flow
- [ ] Verification amount appropriate (₦50 or adjust for production)
- [ ] Refund automation working and tested
- [ ] Webhook endpoint secured with signature validation
- [ ] Error handling for:
  - Declined cards
  - Network failures
  - Duplicate charges
  - Webhook failures

### UI/UX
- [ ] Loading states during Paystack modal
- [ ] Error messages user-friendly
- [ ] Success confirmations clear
- [ ] Mobile responsive (test on actual devices)
- [ ] Consistent with design system (#000856 primary color)
- [ ] Tab navigation smooth
- [ ] Telegram verification flow tested

### Monitoring
- [ ] Logging enabled for payment operations
- [ ] Error tracking setup (Sentry/etc)
- [ ] Payment webhook logs monitored
- [ ] Refund automation logs checked
- [ ] Failed payment alerts configured

## 📊 Production Testing Scenarios

### Scenario 1: New User Journey
1. User signs up
2. Navigates to billing
3. No payment method → "Add Card" button shown
4. Adds first card
5. Card saved as Primary
6. Can subscribe to plans

### Scenario 2: Updating Card Mid-Subscription
1. User has active subscription with auto-renew
2. Current card expiring soon
3. Updates to new card
4. Old card deactivated
5. Subscription auto-renew continues with new card
6. Next renewal uses new card

### Scenario 3: Removing Last Payment Method
1. User has active subscriptions
2. Removes only payment method
3. Warning shown about auto-renewals
4. Card removed
5. All subscriptions: auto_renew = False
6. User can still access content until expiry
7. Must add new card to renew

### Scenario 4: Failed Card Addition
1. User tries to add invalid card
2. Paystack shows error
3. No charge made
4. Modal closes
5. User can retry with valid card
6. No orphaned records in database

## 🔍 Post-Deployment Verification

### Day 1 Checks
- [ ] Monitor webhook success rate (should be >95%)
- [ ] Check refund automation (₦50 charges refunded within 24hrs)
- [ ] Verify no duplicate active cards per user
- [ ] Test production Paystack keys working
- [ ] Monitor error logs for payment failures

### Week 1 Checks
- [ ] User feedback on billing page UX
- [ ] Subscription renewal success rate
- [ ] Card update success rate
- [ ] Mobile usage analytics
- [ ] Performance metrics (page load time)

## 🆘 Troubleshooting

### Issue: Paystack Modal Not Opening
**Check**: Console errors for Paystack script
**Solution**: Verify script loaded in Network tab, check public key

### Issue: Card Saved But Not Showing
**Check**: Backend logs for save_payment_method view
**Solution**: Verify webhook received, check is_active=True

### Issue: Multiple Active Cards
**Check**: Database query for active cards per user
**Solution**: Run cleanup script to deactivate old cards

### Issue: Refunds Not Processing
**Check**: Paystack dashboard for refund status
**Solution**: Verify webhook handler, check refund automation logic

## 📝 Notes

- **Single Card Policy**: Enforced at backend and UI level
- **Verification Charge**: ₦50 (₦0.50) charged and refunded
- **Card Updates**: Automatic replacement, old card deactivated
- **Subscription Impact**: All subscriptions use the single payment method
- **Auto-Renewal**: Disabled when last payment method removed

---

**Last Updated**: January 2025  
**Changes Made**: 
1. Fixed width issue (max-w-5xl → max-w-7xl)
2. Added Paystack script to root layout
3. Verified single payment method enforcement
4. Updated UI for card replacement warnings
