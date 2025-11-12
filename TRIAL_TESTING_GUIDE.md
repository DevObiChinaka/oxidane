# Trial Subscription Testing Guide

## Quick Test Scenarios

### Scenario 1: Regular Subscription (No Trial)

**Setup:**
1. Admin: Create/Edit plan with `trial_days = 0`

**User Flow:**
1. Navigate to `/pricing`
2. Select plan **without trial badge**
3. Click "Get Started" button
4. Verify checkout page shows:
   - ❌ No trial banner
   - ✅ "Base Price" label
   - ✅ "Total Amount" with full price
   - ✅ Processing fee visible
5. Complete payment on Paystack
6. Verify success page shows:
   - ✅ "Payment Successful! 🎉"
   - ❌ No trial countdown banner
   - ✅ "Your subscription is now active"

### Scenario 2: Trial Subscription (7-Day Trial)

**Setup:**
1. Admin: Create/Edit plan with `trial_days = 7`

**User Flow:**
1. Navigate to `/pricing`
2. Select plan **with "7-Day Trial" badge**
3. Click "Start Free Trial" button
4. Verify checkout page shows:
   - ✅ Blue trial information banner
   - ✅ "Price After Trial" label
   - ✅ "Due Today: $0.00"
   - ✅ "Free for 7 days" subtitle
   - ❌ No processing fee
5. Complete payment on Paystack (card authorized, not charged)
6. Verify success page shows:
   - ✅ "Trial Started! 🎉"
   - ✅ Blue trial countdown banner
   - ✅ "Free Trial Active - 7 Days Remaining"
   - ✅ Trial end date displayed
   - ✅ "After that, you'll be charged..." message

### Scenario 3: Currency Conversion with Trial

**User Flow:**
1. Select currency: NGN
2. Select plan with trial
3. Verify checkout shows:
   - ✅ Exchange rate displayed
   - ✅ "Price After Trial" in NGN
   - ✅ "Due Today: ₦0.00"
4. Complete trial signup
5. Verify success banner shows NGN amount

### Scenario 4: Coupon with Trial

**User Flow:**
1. Select trial plan
2. Enter coupon code
3. Verify:
   - ✅ Discount applied to "Price After Trial"
   - ✅ "Due Today" still $0.00
   - ✅ Trial banner explains discounted amount will be charged

## Backend Verification

### Check Trial Created Correctly

```python
python manage.py shell

from subscriptions.models import Subscription

# Get most recent subscription
sub = Subscription.objects.latest('created_at')

# Verify trial fields
print(f"Is Trial: {sub.is_trial}")  # Should be True
print(f"Amount Paid: {sub.amount_paid}")  # Should be 0.00
print(f"Trial End Date: {sub.trial_end_date}")
print(f"Days Remaining: {sub.days_until_trial_end}")
```

### Check Authorization Code Saved

```python
from subscriptions.models import PaymentMethod

# Get payment method
pm = PaymentMethod.objects.filter(
    billing_profile=sub.billing_profile
).latest('created_at')

print(f"Authorization Code: {pm.gateway_authorization_code}")
print(f"Card Last 4: {pm.card_last4}")
print(f"Is Reusable: {pm.is_reusable}")  # Should be True
```

### Check Celery Task Scheduled

```bash
# View scheduled tasks
celery -A oxidane inspect scheduled

# Look for process_trial_endings task
```

## API Testing

### Test My Subscriptions Endpoint

```bash
# Get auth token
TOKEN="your_user_auth_token"

# Fetch subscriptions
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/subscriptions/my-subscriptions/
```

**Expected Response:**
```json
{
  "subscriptions": [
    {
      "id": "uuid",
      "plan_name": "Premium Plan",
      "status": "active",
      "is_trial": true,
      "trial_end_date": "2025-12-08T00:00:00Z",
      "days_until_trial_end": 7,
      "plan_base_price": 29.99,
      "currency": "USD",
      "auto_renew": true
    }
  ],
  "stats": {
    "active_count": 1,
    "total_monthly_cost": 29.99
  }
}
```

## Paystack Dashboard Checks

1. **Payment Amount:** Should be $0.00 (or ₦0.00)
2. **Status:** Should be "success" with authorization
3. **Authorization Code:** Should be visible in response
4. **Reusable:** Should be true
5. **Last 4 Digits:** Card ending saved

## Database Queries

### Count Trial Subscriptions

```sql
SELECT COUNT(*) 
FROM subscriptions_subscription 
WHERE is_trial = TRUE AND status = 'active';
```

### View Expiring Trials

```sql
SELECT 
    u.email,
    s.trial_end_date,
    EXTRACT(DAY FROM (s.trial_end_date - NOW())) as days_remaining
FROM subscriptions_subscription s
JOIN users_user u ON s.billing_profile_id = (
    SELECT id FROM subscriptions_billingprofile 
    WHERE user_id = u.id
)
WHERE s.is_trial = TRUE 
  AND s.status = 'active'
ORDER BY s.trial_end_date;
```

### Check Authorization Codes

```sql
SELECT 
    pm.gateway_authorization_code,
    pm.card_last4,
    pm.is_default,
    pm.is_reusable,
    u.email
FROM subscriptions_paymentmethod pm
JOIN subscriptions_billingprofile bp ON pm.billing_profile_id = bp.id
JOIN users_user u ON bp.user_id = u.id
WHERE pm.is_active = TRUE;
```

## Expected Behavior Timeline

### Day 0 (Trial Start)
- ✅ Trial subscription created (`is_trial=True`)
- ✅ `trial_end_date` set to 7 days from now
- ✅ `amount_paid = $0.00`
- ✅ Authorization code saved
- ✅ Telegram groups added

### Day 1-6 (During Trial)
- ✅ Subscription status: "active"
- ✅ `days_until_trial_end` decreases daily
- ✅ User has full access

### Day 7 (Trial End Day)
- ✅ Celery task `process_trial_endings` runs at 3 AM
- ✅ `process_trial_conversion` charges saved card
- ✅ If successful:
  - `is_trial = False`
  - `amount_paid = $29.99`
  - `end_date` extended by billing period
- ✅ If failed:
  - Retry 3 times (5 min intervals)
  - Send email notification
  - Mark subscription for review

### Day 8+ (Post-Trial)
- ✅ Regular paid subscription
- ✅ Auto-renewal active (if enabled)
- ✅ `is_trial = False`

## Error Scenarios

### Card Authorization Fails
**What Happens:**
- Payment fails at Paystack
- No subscription created
- User redirected to failure page
- Can retry payment

### Trial Conversion Fails
**What Happens:**
- Celery task retries 3 times
- Email sent to user
- Subscription remains trial but inactive
- Admin notified

### No Authorization Code
**What Happens:**
- Trial created but cannot convert
- Manual intervention required
- Contact support

## UI Screenshots Checklist

Before deployment, capture these screenshots:

### Pricing Page
- [ ] Regular plan card (no trial badge)
- [ ] Trial plan card (with trial badge)
- [ ] "Start Free Trial" button

### Checkout Page
- [ ] Trial information banner (blue)
- [ ] "Price After Trial" label
- [ ] "Due Today: $0.00"
- [ ] Exchange rate with trial (NGN)

### Success Page
- [ ] "Trial Started! 🎉" header
- [ ] Trial countdown banner
- [ ] Days remaining display
- [ ] Trial end date

### Dashboard (Future)
- [ ] Trial indicator badge
- [ ] Days remaining countdown
- [ ] "Manage Trial" button

## Performance Checks

### Page Load Times
- [ ] Pricing page loads < 2s
- [ ] Checkout page loads < 1.5s
- [ ] Success page loads < 2s

### API Response Times
- [ ] `/api/v1/subscriptions/plans/` < 500ms
- [ ] `/api/payments/initialize/` < 800ms
- [ ] `/api/subscriptions/my-subscriptions/` < 400ms

### Celery Task Processing
- [ ] `process_trial_endings` completes < 5 min
- [ ] `process_trial_conversion` per subscription < 10s

## Monitoring & Alerts

### Metrics to Track
1. **Trial Sign-ups:** Count per day/week
2. **Trial Conversion Rate:** Percentage converting to paid
3. **Authorization Failures:** Failed card authorizations
4. **Conversion Failures:** Failed trial-to-paid conversions
5. **Trial Cancellations:** Users canceling during trial

### Alert Triggers
- Conversion failure rate > 10%
- Authorization failure rate > 5%
- Trial conversion task fails
- Database errors in trial creation

## Production Deployment Checklist

- [ ] Backend changes deployed
- [ ] Frontend changes deployed
- [ ] Celery beat running
- [ ] `process_trial_endings` task scheduled
- [ ] Paystack test mode tested
- [ ] Currency conversion working
- [ ] Email templates updated
- [ ] Admin can create trial plans
- [ ] Monitoring dashboards configured
- [ ] Error alerting set up
- [ ] Documentation updated
- [ ] Team trained on trial flow

## Rollback Plan

If issues occur:

1. **Frontend Only:** Revert frontend deployment (backend still works)
2. **Backend Only:** 
   - Stop Celery beat
   - Revert backend deployment
   - Manually handle any in-progress trials
3. **Full Rollback:**
   - Revert both frontend and backend
   - Disable trial plans in admin
   - Communicate with affected users

## Support Documentation

### User FAQs

**Q: When will I be charged?**
A: You won't be charged today. Your card is authorized (not charged) to start your free trial. After X days, you'll be charged automatically unless you cancel.

**Q: How do I cancel my trial?**
A: Go to Dashboard → Subscriptions → Cancel Subscription. You can cancel anytime before the trial ends.

**Q: Will I get a reminder before being charged?**
A: Yes, we'll email you 3 days before your trial ends.

**Q: What if my payment fails after trial?**
A: We'll retry 3 times. If unsuccessful, your subscription will be paused and you'll receive an email to update payment.

## Success Criteria

✅ **Functional:**
- Trials create with $0 payment
- Cards authorized successfully
- Automatic conversion works
- All UI shows trial info

✅ **Performance:**
- Page loads under target times
- API responses fast
- Celery tasks complete on time

✅ **User Experience:**
- Clear trial messaging
- No confusion about charges
- Smooth checkout flow
- Helpful success page

✅ **Technical:**
- No errors in logs
- Database queries optimized
- API endpoints stable
- Monitoring working

## Contact & Support

For issues during testing:
1. Check this guide first
2. Review error logs
3. Test in isolation (disable other features)
4. Document steps to reproduce
5. Contact development team with logs

---

**Last Updated:** December 1, 2025
**Version:** 1.0
**Status:** Ready for Testing
