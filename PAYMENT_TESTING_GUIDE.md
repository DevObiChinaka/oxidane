# Payment Flow Testing Guide

## Overview
This guide covers all payment flow test cases without waiting for actual subscription periods.

---

## Test Scripts Available

### 1. `test_auto_renewal.py` - Auto-Renewal Testing
**Purpose**: Test subscription auto-renewal without waiting a week/month

**Usage**:
```bash
cd /var/www/oxidane/backend
sudo -u oxidane /var/www/oxidane/venv/bin/python test_auto_renewal.py
```

**Test Cases**:
- ✅ Auto-renewal with valid payment method
- ❌ Auto-renewal with expired payment method
- ❌ Auto-renewal with insufficient funds
- ✅ Successful renewal extends subscription
- ❌ Failed renewal disables auto-renew after max retries

### 2. `test_expiration.py` - Expiration & Telegram Removal
**Purpose**: Test subscription expiration and Telegram group removal

**Usage**:
```bash
cd /var/www/oxidane/backend
sudo -u oxidane /var/www/oxidane/venv/bin/python test_expiration.py
```

**Test Cases**:
- ✅ Expired subscription status changes to 'expired'
- ✅ User removed from Telegram groups on expiration
- ✅ User subscription_status updated
- ✅ Multiple telegram groups handled correctly

### 3. `fix_affected_user.py` - Manual Recovery
**Purpose**: Fix users affected by Celery Beat downtime

**Usage**:
```bash
cd /var/www/oxidane/backend
sudo -u oxidane /var/www/oxidane/venv/bin/python fix_affected_user.py
```

**Options**:
- **Option 1 - Extend**: Give grace period, charge at next billing date
- **Option 2 - Charge Now**: Attempt immediate payment
- **Option 3 - Reset**: Fresh start with new dates

---

## Complete Payment Flow Test Cases

### Test Case 1: New Subscription Purchase
**Goal**: Test initial subscription payment

**Steps**:
1. Create new user account
2. Select a plan (weekly for quick testing)
3. Complete Paystack payment
4. Verify:
   - ✅ Payment status = 'verified'
   - ✅ Subscription status = 'active'
   - ✅ User added to Telegram groups
   - ✅ `auto_renew = True`
   - ✅ `next_billing_date` set correctly
   - ✅ Payment method saved with authorization_code

**Check Database**:
```python
python manage.py shell
>>> from subscriptions.models import Subscription, Payment
>>> sub = Subscription.objects.filter(billing_profile__user__email='test@email.com').first()
>>> sub.status  # Should be 'active'
>>> sub.payment_method  # Should exist
>>> sub.payment_method.gateway_authorization_code  # Should have value
```

---

### Test Case 2: Auto-Renewal Success
**Goal**: Test successful automatic renewal

**Steps**:
1. Use `test_auto_renewal.py`
2. Select an active subscription
3. Set `next_billing_date` to today
4. Trigger renewal manually
5. Verify:
   - ✅ Payment charged successfully
   - ✅ Subscription extended by billing period
   - ✅ `next_billing_date` updated
   - ✅ User remains in Telegram groups
   - ✅ New Payment record created

**Command**:
```bash
python test_auto_renewal.py
# Choose option 2, then option 3 for specific subscription
```

---

### Test Case 3: Auto-Renewal Failure - Payment Declined
**Goal**: Test renewal failure with declined card

**Steps**:
1. Use Paystack test card that will decline: `5060 6666 6666 6666 6666`
2. Or manually invalidate payment method in database
3. Set `next_billing_date` to today
4. Trigger renewal
5. Verify:
   - ❌ Payment fails
   - ⏳ Task retries (3 times with 5-minute delays)
   - ❌ After max retries: `auto_renew = False`
   - ⚠️ Subscription still active until `end_date`
   - 📧 TODO: Email notification sent (if implemented)

**Simulate**:
```python
python manage.py shell
>>> from subscriptions.models import Subscription
>>> sub = Subscription.objects.get(id='subscription_id')
>>> sub.payment_method.is_active = False
>>> sub.payment_method.save()
# Now trigger renewal - it will fail
```

---

### Test Case 4: Subscription Expiration
**Goal**: Test expiration when auto-renew fails or is disabled

**Steps**:
1. Use `test_expiration.py`
2. Set subscription `end_date` to yesterday
3. Run expiration check
4. Verify:
   - ✅ Status changes to 'expired'
   - ✅ User removed from Telegram groups
   - ✅ `user.subscription_status = 'expired'`
   - ✅ Moved to "Inactive Subscriptions" tab

**Command**:
```bash
python test_expiration.py
# Choose option 2 to expire, then option 3 to run check
```

---

### Test Case 5: Manual Renewal (Re-subscribe)
**Goal**: Test user manually renewing after expiration

**Steps**:
1. Expire a subscription (Test Case 4)
2. User goes to pricing page
3. User selects same plan
4. Completes payment
5. Verify:
   - ✅ New Subscription created OR existing extended
   - ✅ Payment processed
   - ✅ User re-added to Telegram groups
   - ✅ Status back to 'active'

---

### Test Case 6: Payment Method Update
**Goal**: Test updating saved payment method

**Steps**:
1. User has active subscription
2. Navigate to payment methods
3. Add new card via Paystack
4. Verify:
   - ✅ New PaymentMethod created
   - ✅ New authorization_code saved
   - ✅ Old card can be removed
   - ✅ Subscription uses new payment method

---

### Test Case 7: Webhook Payment Verification
**Goal**: Test Paystack webhook handling

**Steps**:
1. Make payment
2. Paystack sends webhook
3. Verify webhook handler:
   - ✅ Payment status updated
   - ✅ Subscription activated
   - ✅ User added to groups
   - ✅ Idempotency (duplicate webhooks ignored)

**Test Webhook Locally**:
```bash
curl -X POST http://localhost:8000/api/payments/webhook/ \
  -H "Content-Type: application/json" \
  -H "x-paystack-signature: test_signature" \
  -d '{...webhook_payload...}'
```

---

### Test Case 8: Coupon Application
**Goal**: Test payment with discount coupon

**Steps**:
1. Create coupon in admin
2. Apply during checkout
3. Complete payment
4. Verify:
   - ✅ Discount applied
   - ✅ Correct amount charged
   - ✅ Coupon usage incremented
   - ✅ Subscription active

---

### Test Case 9: Trial Period (If Enabled)
**Goal**: Test trial to paid conversion

**Steps**:
1. User signs up with trial
2. Trial period ends
3. Auto-charge triggered
4. Verify:
   - ✅ Charged at trial end
   - ✅ Converted to paid
   - ✅ Subscription continues

**Note**: You mentioned trials are disabled, but test if needed later.

---

### Test Case 10: Refund/Cancellation
**Goal**: Test subscription cancellation

**Steps**:
1. Cancel active subscription
2. Verify:
   - ⏳ Remains active until `end_date`
   - ❌ `auto_renew = False`
   - 📧 Cancellation email sent
   - ✅ No charge at next billing
   - ✅ Expires naturally at end_date

---

## Answering Your Questions

### Q1: "When next would my system try to renew the plan since it's tagged inactive?"

**Answer**: 
**NEVER** - Once a subscription is marked `inactive` or `expired`, the auto-renewal system **will not** attempt to renew it again.

**Why?**
The `process_auto_renewals` task only processes subscriptions that are:
```python
status='active'
auto_renew=True
next_billing_date__date=today
```

**Solution for Affected User**:
Use `fix_affected_user.py` with one of three options:

1. **Option 1 - Extend (Recommended)**:
   - Reactivates subscription
   - Gives grace period
   - Sets next billing date to future
   - Will auto-renew normally at that date

2. **Option 2 - Charge Now**:
   - Attempts immediate payment
   - If successful, subscription continues
   - If fails, user needs to update payment

3. **Option 3 - Reset**:
   - Fresh start
   - New billing cycle begins

---

### Q2: "How do I resolve the user whose plan didn't renew?"

**Steps**:
```bash
# 1. SSH to server
ssh root@169.255.57.172

# 2. Navigate to backend
cd /var/www/oxidane/backend

# 3. Run fix script
sudo -u oxidane /var/www/oxidane/venv/bin/python fix_affected_user.py

# 4. Choose option 1 (find affected users)
# 5. Select the user
# 6. Choose recovery option:
#    - Option 1: Extend (give them grace period)
#    - Option 2: Charge now (if payment method valid)
#    - Option 3: Reset (fresh start)
```

**Recommended**: Use **Option 1 (Extend)** for affected users
- Shows goodwill (not their fault Beat was down)
- Extends subscription for one billing period
- They'll be charged at next renewal automatically
- Re-adds them to Telegram groups immediately

---

### Q3: "Test cases without waiting one week?"

**All test scripts manipulate dates**:
- `test_auto_renewal.py` - Sets `next_billing_date` to TODAY
- `test_expiration.py` - Sets `end_date` to YESTERDAY
- You can test entire flows in minutes, not weeks!

---

## Quick Test Session Example

```bash
# Terminal 1 - Watch Celery worker logs
ssh root@169.255.57.172 "journalctl -u oxidane-celery.service -f"

# Terminal 2 - Run tests
ssh root@169.255.57.172
cd /var/www/oxidane/backend

# Test auto-renewal
sudo -u oxidane /var/www/oxidane/venv/bin/python test_auto_renewal.py
# Select subscription, set to today, trigger renewal

# Test expiration
sudo -u oxidane /var/www/oxidane/venv/bin/python test_expiration.py
# Expire subscription, run check, verify Telegram removal

# Fix affected user
sudo -u oxidane /var/www/oxidane/venv/bin/python fix_affected_user.py
# Find user, select recovery option
```

---

## Important Notes

1. **Use Weekly Plans** for faster testing (7 days vs 30 days)
2. **Celery Worker Must Be Running** for async tasks (Telegram, emails)
3. **Check Logs** for detailed task execution
4. **Database Changes Are Real** - test on staging first if available
5. **Paystack Test Mode** - Use test API keys for safe testing

---

## Next Steps

1. ✅ Upload test scripts to server
2. ✅ Fix affected user(s) using `fix_affected_user.py`
3. ✅ Run through each test case systematically
4. ✅ Document any issues found
5. ✅ Monitor Celery Beat logs for next 24 hours

Let me know which test case you want to start with!
