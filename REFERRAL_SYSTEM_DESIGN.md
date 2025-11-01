# 🎯 Referral System Design - Discount-Based with Credits

## Overview
The Oxidane platform uses a **discount-based referral system** where both referrers and referees benefit through price reductions, NOT cash payments.

## System Architecture

### Core Principle
- **Referees** get immediate 10% discount when signing up with a code
- **Referrers** earn 5% discount credits for every 10 successful referrals
- **Credits are single-use** (cannot be stacked for one subscription)
- **Credits can be used multiple times** (one per subscription/renewal)

---

## 📊 Models

### 1. ReferralCode (Existing - Task 0.5.4)
Stores referral codes owned by users.

**Key Fields:**
- `code` - Unique referral code (e.g., "JOHN2024")
- `referrer` - User who owns this code
- `referrer_discount_type/value` - Discount type for referrer
- `referee_discount_type/value` - Discount for new users
- `max_uses` - Usage limits
- `is_active` - Active status

### 2. Referral (Simplified - Task 0.5.5)
Tracks each successful referral conversion.

**Key Fields:**
- `referral_code` - FK to ReferralCode used
- `referrer` - User who referred
- `referee` - User who was referred
- `subscription` - Subscription created
- `original_amount` - Price before discount
- `referee_discount_percent` - Discount % applied (default 10%)
- `referee_discount_amount` - Discount in currency
- `final_amount` - Price after discount
- `status` - completed/cancelled
- `conversion_date` - When referral occurred

**Removed Fields (Commission System):**
- ❌ `commission_rate`
- ❌ `commission_earned`
- ❌ `commission_paid`
- ❌ `commission_currency`
- ❌ `paid_date`

**Key Methods:**
- `mark_as_cancelled(reason)` - Cancel a referral
- `check_and_award_credit()` - Auto-award credit every 10 referrals
- `get_status_display_color()` - UI color coding

### 3. ReferralCredit (NEW)
Tracks discount credits earned by referrers.

**Key Fields:**
- `user` - Who earned this credit
- `credit_percentage` - Discount % (typically 5%)
- `earned_from_referral` - OneToOne FK to triggering Referral
- `is_used` - Has been redeemed?
- `used_on_subscription` - Where it was applied
- `earned_date` - When earned
- `used_date` - When redeemed
- `expires_at` - Optional expiry date

**Key Methods:**
- `use_credit(subscription)` - Redeem this credit
- `is_expired()` - Check if expired
- `is_available()` - Check if available for use

---

## 🔄 Business Logic Flow

### Scenario 1: New User Signs Up with Referral Code

```python
# 1. User B uses User A's code "JOHN2024"
referral_code = ReferralCode.objects.get(code='JOHN2024', is_active=True)

# 2. Apply 10% discount to User B immediately
original_price = 100.00
discount_percent = 10.00
discount_amount = original_price * (discount_percent / 100)  # $10.00
final_price = original_price - discount_amount  # $90.00

# 3. Create Referral record
referral = Referral.objects.create(
    referral_code=referral_code,
    referrer=user_a,  # John
    referee=user_b,   # New user
    subscription=subscription,
    original_amount=100.00,
    referee_discount_percent=10.00,
    referee_discount_amount=10.00,
    final_amount=90.00,
    status='completed'
)

# 4. Check if User A should earn a credit (auto-triggered in save())
# If this is User A's 10th, 20th, 30th... referral:
# - Create ReferralCredit with 5% discount
# - Credit is available for User A to use on next subscription
```

### Scenario 2: Referrer Uses Earned Credit

```python
# User A has 50 successful referrals = 5 credits (5% each)
available_credits = ReferralCredit.objects.filter(
    user=user_a,
    is_used=False,
    expires_at__gt=timezone.now()  # or is null
).order_by('earned_date')

# User A subscribes to a $200/month plan
subscription_price = 200.00

# Apply ONE credit (cannot stack!)
if available_credits.exists():
    credit = available_credits.first()
    discount_percent = credit.use_credit(subscription)  # 5%
    discount_amount = subscription_price * (discount_percent / 100)  # $10.00
    final_price = subscription_price - discount_amount  # $190.00
    
    # Credit is marked as used, User A still has 4 credits remaining
    # for future subscriptions/renewals
```

---

## ⚠️ Anti-Abuse Mechanisms

### 1. **Single-Use Credits**
- Credits cannot be stacked (no 25% discount from 5 credits)
- Maximum discount per transaction: 5% (or 10% for referee)
- Prevents system from losing too much revenue

### 2. **Credit Earning Rate**
- Requires 10 successful conversions per credit
- Encourages quality referrals over quantity
- Sustainable for business model

### 3. **Validation Rules**
- Referrer must own the referral code
- No self-referrals allowed
- All amounts must be non-negative
- Final amount cannot exceed original amount

### 4. **Optional Expiry**
- Credits can have expiration dates
- Prevents indefinite credit accumulation
- Can be configured per business needs

---

## 📈 Example Calculations

### Example 1: User with 50 Referrals

**Referrals Made:** 50 successful conversions  
**Credits Earned:** 5 × 5% discount credits  
**Total Potential Savings:** 5 separate 5% discounts

**Usage:**
- Month 1: Subscribe $200 plan → Use 1 credit → Pay $190 (save $10)
- Month 2: Renew $200 plan → Use 1 credit → Pay $190 (save $10)
- Month 3: Renew $200 plan → Use 1 credit → Pay $190 (save $10)
- Month 4: Renew $200 plan → Use 1 credit → Pay $190 (save $10)
- Month 5: Renew $200 plan → Use 1 credit → Pay $190 (save $10)

**Total Saved:** $50 over 5 months

### Example 2: If Stacking Was Allowed (We Don't Do This!)

**Problem Scenario:**
- User has 5 credits (25% total if stacked)
- $200 plan → $150 with 25% discount
- Business loses $50 in one transaction
- Not sustainable!

**Our Solution:**
- User has 5 credits (5% each, single-use)
- $200 plan → $190 with ONE 5% discount
- Business loses $10 per transaction
- Spread over 5 transactions = $50 total
- Much more sustainable!

---

## 🎨 Admin Interface Features

### Referral Admin
- View all referral conversions
- Filter by status, date, currency
- See discount applied to referee
- Export to CSV
- Cancel referrals if needed

### ReferralCredit Admin
- View all earned credits
- Filter by used/unused, expired
- See which referral earned each credit
- Track where credits were used
- Export credit history

---

## 🚀 Future Enhancements

### Possible Improvements:
1. **Dynamic Credit Values**
   - 5% for 10 referrals
   - 7.5% for 50 referrals
   - 10% for 100 referrals

2. **Credit Expiry Policies**
   - Credits expire after 6 months
   - Or after 12 months of inactivity

3. **Tier-Based Rewards**
   - Bronze: 5% credits
   - Silver: 7.5% credits
   - Gold: 10% credits

4. **Referral Leaderboard**
   - Top referrers get bonus credits
   - Monthly competitions

5. **Referral Analytics Dashboard**
   - Track conversion rates
   - Monitor credit usage patterns
   - Identify top referrers

---

## 📝 Summary

✅ **Discount-Based** - No cash payments  
✅ **Credit System** - Earn 5% credits every 10 referrals  
✅ **Single-Use** - Cannot stack credits  
✅ **Multi-Use** - Can use credits multiple times (one at a time)  
✅ **Anti-Abuse** - Sustainable for business  
✅ **Win-Win** - Rewards active users without breaking the bank  

This system provides meaningful rewards for referrers while maintaining healthy profit margins for the business. 🎯
