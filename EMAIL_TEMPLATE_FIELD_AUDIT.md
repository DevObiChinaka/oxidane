# Email Template Field Audit Report

## Purpose
This audit verifies that all variables used in system email templates match actual database model fields. This ensures emails will render correctly in production.

---

## Database Model Fields Reference

### User Model (`users.models.User`)
**Inherits from AbstractUser, available fields:**
- `first_name` ✅
- `last_name` ✅
- `email` ✅
- `username` ✅
- `telegram_user_id` ✅ (BigIntegerField, nullable)

**Custom fields:**
- `avatar` (URLField, nullable)
- `is_email_verified` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `last_login` (DateTime, nullable)

### BillingProfile Model (`subscriptions.models.BillingProfile`)
- `telegram_user_id` ✅ (CharField)
- `telegram_username` ✅ (CharField)
- `telegram_verified` (Boolean)
- `telegram_verified_at` (DateTime, nullable)
- `country` (CharField, 2-letter ISO code)
- `currency_preference` (CharField)

### Subscription Model (`subscriptions.models.Subscription`)
- `status` ✅ (active, cancelled, expired, suspended, pending)
- `start_date` ✅ (DateTime)
- `end_date` ✅ (DateTime)
- `amount_paid` ✅ (Decimal)
- `currency` ✅ (CharField)
- `auto_renew` (Boolean)
- `next_billing_date` ✅ (DateTime, nullable)
- `plan` (FK to SubscriptionPlan)

### SubscriptionPlan Model
- `name` (CharField - e.g., "Premium Signals")
- `plan_type` ⚠️ **NOT IN MODEL** - Need to verify this field exists
- `billing_period` (weekly, monthly, quarterly, yearly, lifetime)

---

## Email Template Variable Audit

### ✅ 1. Email Verification (`email_verification`)
**Variables used:**
- `{{user.first_name}}` ✅ Maps to `User.first_name`
- `{{user.email}}` ✅ Maps to `User.email`
- `{{verification_url}}` ✅ Generated dynamically (token-based)

**Status:** ✅ **ALL FIELDS VALID**

---

### ✅ 2. Password Reset (`password_reset`)
**Variables used:**
- `{{user.first_name}}` ✅ Maps to `User.first_name`
- `{{reset_url}}` ✅ Generated dynamically (token-based)

**Status:** ✅ **ALL FIELDS VALID**

---

### ✅ 3. Sign-in Notification (`signin_notification`)
**Variables used:**
- `{{user.first_name}}` ✅ Maps to `User.first_name`
- `{{signin_datetime}}` ✅ Generated from `timezone.now()`
- `{{device}}` ⚠️ **Requires User-Agent parsing**
- `{{location}}` ⚠️ **Requires IP geolocation**

**Status:** ⚠️ **NEEDS IMPLEMENTATION**
- `device` and `location` are not stored in database
- Must be generated from request headers and IP address
- Recommend: Parse `request.META['HTTP_USER_AGENT']` for device
- Recommend: Use IP geolocation service for location

---

### ⚠️ 4. Payment Success (`payment_success`)
**Variables used:**
- `{{user.first_name}}` ✅ Maps to `User.first_name`
- `{{amount}}` ⚠️ Maps to `Subscription.amount_paid` OR `Payment.amount`
- `{{currency}}` ✅ Maps to `Subscription.currency`
- `{{transaction_id}}` ❌ **NO TRANSACTION MODEL EXISTS**
- `{{payment_date}}` ⚠️ Maps to `Subscription.created_at` OR `Payment.created_at`
- `{{payment_method}}` ⚠️ Maps to `Subscription.payment_method.name`
- `{{description}}` ⚠️ Should be `Subscription.plan.name`

**Status:** ❌ **CRITICAL ISSUES**
- No `Transaction` or `Payment` model exists in codebase
- `transaction_id` cannot be populated without Payment model
- Need to create Payment model with: id, amount, currency, transaction_id, payment_date, payment_method, description

**Recommendation:**
Create `Payment` model:
```python
class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    description = models.TextField()
```

---

### ⚠️ 5. Payment Failed (`payment_failed`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{amount}}` ⚠️ Needs Payment model
- `{{currency}}` ✅
- `{{failed_date}}` ⚠️ Needs Payment.created_at
- `{{failure_reason}}` ❌ **Needs Payment.error_message field**
- `{{update_payment_url}}` ✅ Generated dynamically

**Status:** ❌ **BLOCKED** - Requires Payment model

---

### ⚠️ 6. Payment Refunded (`payment_refunded`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{amount}}` ⚠️ Needs Payment/Refund model
- `{{currency}}` ✅
- `{{refund_id}}` ❌ **Needs Refund model**
- `{{original_transaction_id}}` ❌ **Needs Payment model**
- `{{refund_date}}` ❌ **Needs Refund.created_at**
- `{{refund_reason}}` ❌ **Needs Refund.reason field**

**Status:** ❌ **BLOCKED** - Requires Payment and Refund models

---

### ⚠️ 7. Subscription Activated (`subscription_activated`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{plan_type}}` ❌ **NO plan_type FIELD IN SubscriptionPlan**
- `{{amount}}` ✅ Maps to `Subscription.amount_paid`
- `{{currency}}` ✅ Maps to `Subscription.currency`
- `{{next_billing_date}}` ✅ Maps to `Subscription.next_billing_date`

**Status:** ⚠️ **FIELD MISMATCH**
- `plan_type` should be `plan.name` or `plan.billing_period`
- Need to verify SubscriptionPlan model has plan_type field

**Fix:** Change template to use `{{plan.name}}` or add plan_type field to SubscriptionPlan

---

### ⚠️ 8. Subscription Expiring (`subscription_expiry`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{plan_type}}` ❌ Should be `{{plan.name}}`
- `{{days_remaining}}` ✅ Can calculate from `Subscription.end_date`
- `{{renewal_url}}` ✅ Generated dynamically

**Status:** ⚠️ **FIELD MISMATCH** - Same as #7

---

### ⚠️ 9. Subscription Renewed (`subscription_renewal`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{plan_type}}` ❌ Should be `{{plan.name}}`
- `{{renewal_date}}` ✅ Maps to `Subscription.created_at` or `Subscription.start_date`
- `{{next_billing_date}}` ✅ Maps to `Subscription.next_billing_date`
- `{{amount}}` ✅ Maps to `Subscription.amount_paid`
- `{{currency}}` ✅ Maps to `Subscription.currency`

**Status:** ⚠️ **FIELD MISMATCH** - Same as #7

---

### ⚠️ 10. Telegram Added (`telegram_added`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{group_name}}` ⚠️ Needs TelegramGroup.name
- `{{telegram_username}}` ✅ Maps to `BillingProfile.telegram_username`
- `{{group_link}}` ⚠️ Needs TelegramGroup.invite_link

**Status:** ⚠️ **NEEDS TelegramGroup MODEL VERIFICATION**

---

### ⚠️ 11. Telegram Removed (`telegram_removed`)
**Variables used:**
- `{{user.first_name}}` ✅
- `{{group_name}}` ⚠️ Needs TelegramGroup.name
- `{{removal_reason}}` ⚠️ Needs to be passed as parameter
- `{{removal_date}}` ✅ Generated from `timezone.now()`

**Status:** ⚠️ **NEEDS TelegramGroup MODEL VERIFICATION**

---

## Summary of Issues

### 🔴 Critical Issues (Blocking Production)
1. **No Payment model** - payment_success, payment_failed, payment_refunded templates cannot work
   - Missing: transaction_id, payment_date, payment_method, description, failure_reason
   - **Action Required:** Create Payment model with full transaction tracking

2. **No Refund model** - payment_refunded template cannot work
   - Missing: refund_id, original_transaction_id, refund_date, refund_reason
   - **Action Required:** Create Refund model

### ⚠️ High Priority Issues
3. **plan_type field missing** - Used in 3 subscription templates
   - **Fix:** Either add `plan_type` field to SubscriptionPlan model OR
   - **Fix:** Update templates to use `{{plan.name}}` instead

4. **device and location not tracked** - signin_notification incomplete
   - **Fix:** Add User-Agent parsing for device info
   - **Fix:** Add IP geolocation for location info

### ℹ️ Medium Priority Issues
5. **TelegramGroup model** - Verify invite_link and name fields exist
   - **Action:** Check TelegramGroup model has required fields

---

## Recommended Actions

### Immediate (Before Production)
1. ✅ **Audit all templates** - Done
2. ❌ **Create Payment model** with proper fields
3. ❌ **Create Refund model** if refunds are supported
4. ⚠️ **Fix plan_type references** - Update templates or add field
5. ⚠️ **Add device/location tracking** for signin notifications

### Testing Checklist
- [ ] Test email_verification with real User object
- [ ] Test password_reset with real User object
- [ ] Test signin_notification (verify device/location work)
- [ ] **BLOCKED:** Test payment_success (needs Payment model)
- [ ] **BLOCKED:** Test payment_failed (needs Payment model)
- [ ] **BLOCKED:** Test payment_refunded (needs Payment/Refund models)
- [ ] Test subscription_activated (verify plan_type works)
- [ ] Test subscription_expiry (verify days_remaining calculation)
- [ ] Test subscription_renewal (verify all fields)
- [ ] Test telegram_added (verify TelegramGroup fields)
- [ ] Test telegram_removed (verify TelegramGroup fields)

---

## Email Service Updates Needed

### `email_service.py` must be updated to:
1. Accept Payment object for payment-related emails
2. Accept Subscription object for subscription emails
3. Parse User-Agent for device info
4. Perform IP geolocation for location info
5. Calculate days_remaining from end_date
6. Map plan.name to plan_type variable

### Example Variable Mapping:
```python
context = {
    'user': user,
    'plan_type': subscription.plan.name,  # FIX: map plan.name to plan_type
    'amount': subscription.amount_paid,
    'currency': subscription.currency,
    'next_billing_date': subscription.next_billing_date,
    # Payment emails (NEEDS Payment model):
    # 'transaction_id': payment.transaction_id,
    # 'payment_date': payment.created_at,
    # 'payment_method': payment.payment_method,
}
```

---

## Conclusion

**Current Status:** 🔴 **NOT PRODUCTION READY**

**Blockers:**
1. No Payment model (blocks 3 critical templates)
2. No Refund model (blocks 1 template)
3. plan_type field mismatch (breaks 3 templates)

**Recommendation:** 
- Create Payment and Refund models immediately
- Fix plan_type references in templates
- Add device/location tracking for enhanced security notifications
- Run comprehensive integration tests before production deployment
