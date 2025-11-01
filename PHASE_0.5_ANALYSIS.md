# 📊 PHASE 0.5: DYNAMIC PLANS FOUNDATION - PRE-IMPLEMENTATION ANALYSIS

**Date:** November 1, 2025  
**Status:** Phase 0 Complete ✅ - Ready for Phase 0.5  
**Estimated Time:** 20 hours (40 tasks)  

---

## 🎯 PHASE GOALS

Transform the current hardcoded subscription system into a **fully dynamic, admin-configurable platform** where:

1. **Admins can create unlimited plans** via UI (no code changes)
2. **Features are granular & reusable** (e.g., "access_premium_signals", "telegram_vip_group")
3. **Multi-currency support** (NGN, USD, GBP, EUR)
4. **Everything is encrypted** (Telegram tokens, Paystack keys, SMTP passwords)
5. **Setup wizard guides new deployments** (onboarding flow)

---

## 📦 WHAT ALREADY EXISTS

### ✅ Current Models (10 existing):
1. **PricingPlan** - Basic plan structure (name, price, duration)
2. **CouponCode** - Discount codes with usage limits
3. **CouponUsage** - Tracks coupon redemptions
4. **SignalSubscription** - User subscriptions (STATUS: Active, Expired, Cancelled)
5. **PaymentTransaction** - Payment history
6. **TelegramGroupManagement** - Telegram group definitions
7. **BillingProfile** - User billing info (one per user)
8. **PaymentMethod** - Stored payment methods (cards, bank)
9. **Subscription** - Main subscription model (STATUS: active, cancelled, expired, pending)
10. **Payment** - Individual payment records

### ⚠️ Current Limitations:
- ❌ **Hardcoded features** - No feature flag system
- ❌ **Single currency** - Only NGN supported in pricing
- ❌ **Manual configuration** - Telegram/Payment settings in code
- ❌ **No referral system** - Can't track user referrals
- ❌ **No encryption** - Sensitive keys stored in plain text (.env)
- ❌ **No setup wizard** - Manual configuration required
- ❌ **Plans not linked to features** - No way to define "Premium gets X features"

---

## 🆕 WHAT NEEDS TO BE BUILT

### 📋 NEW MODELS TO CREATE (11 models):

#### 1. **Feature** (NEW)
```python
# Purpose: Define platform capabilities (e.g., "access_premium_signals", "telegram_vip_group")
# Fields: key (unique), name, description, category (signals/telegram/courses/api), icon, sort_order, is_active
# Why: Admins can create features, then assign them to plans (many-to-many)
```

#### 2. **SubscriptionPlan** (REPLACES PricingPlan)
```python
# Purpose: Admin-defined plans with multi-currency pricing
# Fields: name, description, features (M2M), telegram_groups (M2M), 
#         prices (JSONField: {"NGN": 10000, "USD": 25}), 
#         billing_period (monthly/quarterly/annual), trial_days, is_active, sort_order
# Why: Single source of truth for plan configuration
```

#### 3. **Update Subscription Model** (EXISTING - needs FK additions)
```python
# Add fields: 
#   - plan (FK to SubscriptionPlan) 
#   - referral (FK to Referral, nullable)
#   - metadata (JSONField for custom data)
# Why: Link subscriptions to new plan system + referral tracking
```

#### 4. **Coupon** (REPLACES CouponCode)
```python
# Purpose: More advanced discount system
# Fields: code (unique), discount_type (percentage/fixed), discount_value, 
#         currency (for fixed), max_uses, current_uses, 
#         valid_from, valid_until, applicable_plans (M2M), is_active
# Why: Support both % and fixed discounts, plan-specific coupons
```

#### 5. **CouponUsage** (ALREADY EXISTS - keep as is)
```python
# Purpose: Track who used which coupon
# Current: user, coupon, subscription, used_at
# Action: Migrate FK to new Coupon model
```

#### 6. **ReferralCode** (NEW)
```python
# Purpose: User referral codes (e.g., "JOHN25")
# Fields: user (FK), code (unique), discount_percentage, 
#         commission_percentage (referrer earnings), 
#         total_uses, total_earnings (decimal), is_active
# Why: Users earn money from referrals (e.g., 10% of referred subscriptions)
```

#### 7. **Referral** (NEW)
```python
# Purpose: Track individual referral transactions
# Fields: referrer (FK to User), referred_user (FK to User), 
#         referral_code (FK), subscription (FK), 
#         commission_amount, status (pending/paid), created_at
# Why: Detailed tracking for payout calculations
```

#### 8. **TelegramConfiguration** (NEW - SINGLETON)
```python
# Purpose: Centralized Telegram bot settings (encrypted)
# Fields: bot_token (encrypted), bot_username, webhook_url, 
#         webhook_secret (encrypted), is_configured, updated_at
# Methods: .get_config() (singleton), .decrypt_token(), .test_connection()
# Why: Move secrets from .env to database (encrypted), admin can update via UI
```

#### 9. **TelegramGroup** (REPLACES TelegramGroupManagement)
```python
# Purpose: Define Telegram groups linked to plans
# Fields: name, chat_id, invite_link (encrypted), group_type (premium/vip/education),
#         description, is_active
# Why: Admins can add/edit groups without code changes
```

#### 10. **PaymentConfiguration** (NEW - SINGLETON)
```python
# Purpose: Paystack settings (encrypted)
# Fields: public_key (encrypted), secret_key (encrypted), 
#         supported_currencies (JSONField: ["NGN", "USD"]), 
#         webhook_secret (encrypted), is_configured
# Methods: .get_config() (singleton), .decrypt_keys()
# Why: Multi-tenant support (each deployment has own keys)
```

#### 11. **EmailConfiguration** (NEW - SINGLETON)
```python
# Purpose: SMTP settings (encrypted)
# Fields: smtp_host, smtp_port, smtp_username, smtp_password (encrypted),
#         use_tls, from_email, from_name, is_configured
# Methods: .get_config() (singleton), .test_connection()
# Why: Admin can configure email without touching code
```

---

## 🔐 ENCRYPTION STRATEGY

### Why Encryption?
- **Security:** Prevent database breaches from exposing API keys
- **Compliance:** Meet data protection regulations
- **Multi-tenancy:** Each deployment has unique encrypted keys

### Implementation:
```python
# File: backend/oxidane/encryption.py
from cryptography.fernet import Fernet
import os

def get_cipher():
    key = os.getenv('ENCRYPTION_KEY')  # Already in .env
    return Fernet(key.encode())

def encrypt_value(plaintext: str) -> str:
    return get_cipher().encrypt(plaintext.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    return get_cipher().decrypt(ciphertext.encode()).decode()
```

### Models with Encryption:
- **TelegramConfiguration:** bot_token, webhook_secret
- **TelegramGroup:** invite_link
- **PaymentConfiguration:** public_key, secret_key, webhook_secret
- **EmailConfiguration:** smtp_password

---

## 🚀 IMPLEMENTATION BREAKDOWN (40 Tasks)

### **Phase 1: Models (Tasks 0.5.1 - 0.5.11)** [~6 hours]
- 0.5.1: Create `Feature` model
- 0.5.2: Create `SubscriptionPlan` model
- 0.5.3: Create `Coupon` model (replaces CouponCode)
- 0.5.4: Create `ReferralCode` model
- 0.5.5: Create `Referral` model
- 0.5.6: Create `TelegramConfiguration` model (singleton)
- 0.5.7: Create `TelegramGroup` model (replaces TelegramGroupManagement)
- 0.5.8: Create `PaymentConfiguration` model (singleton)
- 0.5.9: Create `EmailConfiguration` model (singleton)
- 0.5.10: Update `Subscription` model (add plan FK, referral FK)
- 0.5.11: Update `CouponUsage` model (point to new Coupon)

### **Phase 2: Infrastructure (Tasks 0.5.12 - 0.5.15)** [~3 hours]
- 0.5.12: Create encryption utilities (`backend/oxidane/encryption.py`)
- 0.5.13: Add encryption methods to models (`.encrypt_field()`, `.decrypt_field()`)
- 0.5.14: Add helper methods:
  - `SubscriptionPlan.get_price(currency)` - Get price in specific currency
  - `SubscriptionPlan.has_feature(feature_key)` - Check if plan includes feature
  - `TelegramConfiguration.get_config()` - Singleton getter
  - `Coupon.is_valid()` - Check if coupon can be used
  - `ReferralCode.calculate_commission(amount)` - Calculate referrer earnings
- 0.5.15: Create database migrations (`python manage.py makemigrations`)

### **Phase 3: Seed Data (Tasks 0.5.16 - 0.5.18)** [~2 hours]
- 0.5.16: Create management command: `seed_features` (create default features)
- 0.5.17: Create management command: `migrate_legacy_plans` (convert PricingPlan → SubscriptionPlan)
- 0.5.18: Run both commands + migrations

### **Phase 4: Admin APIs (Tasks 0.5.19 - 0.5.28)** [~5 hours]
- 0.5.19: Plans API (GET/POST/PUT/DELETE `/api/admin/plans/`)
- 0.5.20: Features API (GET/POST/PUT/DELETE `/api/admin/features/`)
- 0.5.21: Coupons API (GET/POST/PUT/DELETE `/api/admin/coupons/`)
- 0.5.22: Coupon usage stats API (GET `/api/admin/coupons/{id}/usage/`)
- 0.5.23: Telegram config API (GET/POST/PUT `/api/admin/telegram/config/`)
- 0.5.24: Telegram groups API (GET/POST/PUT/DELETE `/api/admin/telegram/groups/`)
- 0.5.25: Payment config API (GET/POST/PUT `/api/admin/payment/config/`)
- 0.5.26: Email config API (GET/POST/PUT `/api/admin/email/config/`)
- 0.5.27: Test email API (POST `/api/admin/email/test/`)
- 0.5.28: Setup status API (GET `/api/admin/setup/status/`) - Returns % complete

### **Phase 5: Public APIs (Tasks 0.5.29 - 0.5.31)** [~2 hours]
- 0.5.29: Public pricing API (GET `/api/subscriptions/plans/?currency=NGN`)
- 0.5.30: Validate coupon API (POST `/api/subscriptions/validate-coupon/`)
- 0.5.31: Plan upgrade/downgrade APIs

### **Phase 6: Frontend (Tasks 0.5.32 - 0.5.40)** [~4 hours]
- 0.5.32: Build `PlansPage.tsx` (multi-currency editor, feature selectors)
- 0.5.33: Build `FeaturesPage.tsx` (feature management by category)
- 0.5.34: Build `CouponsPage.tsx` (coupon creation, usage stats)
- 0.5.35: Build `TelegramConfigPage.tsx` (bot config, group CRUD, test connection)
- 0.5.36: Build `PaymentConfigPage.tsx` (Paystack keys, currency config)
- 0.5.37: Build `EmailConfigPage.tsx` (SMTP settings, test email)
- 0.5.38: Build `SetupDashboard.tsx` (onboarding wizard with checklist)
- 0.5.39: Update `/pricing` page (fetch plans dynamically, currency selector)
- 0.5.40: Update checkout flow (add coupon/referral code inputs)

---

## ⚠️ MIGRATION STRATEGY

### Data Migration Plan:
1. **Keep old models temporarily** (PricingPlan, CouponCode, TelegramGroupManagement)
2. **Create new models alongside** (SubscriptionPlan, Coupon, TelegramGroup)
3. **Run migration command** (`migrate_legacy_plans`) to copy data
4. **Update ForeignKeys** in Subscription/CouponUsage to point to new models
5. **Test thoroughly** (ensure no data loss)
6. **Deprecate old models** (mark as deprecated, remove in Phase 2)

### Backward Compatibility:
- Old API endpoints continue working (proxy to new models)
- Gradual frontend migration (new pages first, update old pages later)
- Database triggers to sync changes (temporary, during transition)

---

## 🎨 USER EXPERIENCE CHANGES

### For Admins:
**Before:** Edit code files, restart server, run migrations manually  
**After:** Click "Add Plan" → Fill form → Save (live immediately)

**Setup Flow:**
1. First login → Redirected to Setup Dashboard
2. Wizard shows 5 steps:
   - ✅ Configure Telegram Bot
   - ✅ Add Payment Provider
   - ✅ Set Email Settings
   - ✅ Create First Plan
   - ✅ Add Features
3. Each step has "Test Connection" button
4. Can skip and return later

### For Users:
**Before:** Fixed pricing in NGN only  
**After:** Currency selector (USD/NGN/GBP/EUR), prices convert automatically

**Referral Flow:**
1. User generates referral code from dashboard
2. Shares code with friends
3. Earns 10% commission on referred subscriptions
4. Commission tracked in real-time

---

## 🔍 QUESTIONS FOR ALIGNMENT

### 1. **Model Priority**
The roadmap lists 11 new models. Should we:
- **Option A:** Build all 11 models first, then APIs, then UI (waterfall)
- **Option B:** Build Feature → API → UI, then move to next model (iterative)
- **Your preference?**

### 2. **Migration Timing**
When should we deprecate old models (PricingPlan, CouponCode)?
- **Option A:** Keep both systems running in parallel (safer, more code)
- **Option B:** Hard cutover after Phase 0.5 complete (cleaner, riskier)
- **Your preference?**

### 3. **Feature Granularity**
How granular should features be?
- **Option A:** Coarse (e.g., "premium_access", "vip_access") - Simpler, less flexible
- **Option B:** Fine (e.g., "view_premium_signals", "download_course_videos", "telegram_vip_group") - More complex, more flexible
- **Your preference?**

### 4. **Multi-Currency Implementation**
Should currency conversion be:
- **Option A:** Manual (admin sets price per currency: NGN=10000, USD=25)
- **Option B:** Automatic (admin sets USD price, system auto-converts using live rates)
- **Your preference?**

### 5. **Setup Wizard Behavior**
Should incomplete setup:
- **Option A:** Block all admin actions until complete (strict onboarding)
- **Option B:** Show warnings but allow skipping (flexible)
- **Your preference?**

### 6. **Encryption Key Rotation**
Should we build key rotation now or later?
- **Option A:** Phase 0.5 includes key rotation feature (more secure, more time)
- **Option B:** Phase 0.5 uses single key, add rotation in Phase 2 (faster, adequate)
- **Your preference?**

### 7. **API Versioning**
The roadmap mentions `/api/v1/` for public APIs. Should we:
- **Option A:** Version all APIs from the start (`/api/v1/admin/plans/`)
- **Option B:** Only version public APIs, keep admin unversioned
- **Your preference?**

### 8. **Testing Strategy**
For Phase 0.5, should we:
- **Option A:** Build tests alongside each feature (TDD approach)
- **Option B:** Build all features first, then comprehensive test suite
- **Your preference?**

---

## 📊 SUCCESS CRITERIA

Phase 0.5 is complete when:
- [ ] Admin can create a plan with 3 features via UI
- [ ] Admin can configure Telegram bot without touching .env
- [ ] Public pricing page shows plans in 2+ currencies
- [ ] User can apply coupon code at checkout
- [ ] User can generate referral code and see earnings
- [ ] Setup wizard shows 100% progress
- [ ] All sensitive keys are encrypted in database
- [ ] Zero hardcoded plans/features in code
- [ ] All 40 tasks marked complete
- [ ] Database migrations run without errors

---

## 🚦 READY TO PROCEED?

**Current State:** Phase 0 ✅ Complete (PostgreSQL, Redis, dependencies installed)  
**Next Step:** Start Phase 0.5 (pending your alignment on questions above)  

**Estimated Timeline:**
- Models + Infrastructure: 11 hours (Tasks 0.5.1-0.5.15)
- APIs: 7 hours (Tasks 0.5.16-0.5.31)
- Frontend: 4 hours (Tasks 0.5.32-0.5.40)
- **Total:** 22 hours (can be done in 3 days with focused work)

**Dependencies:**
- ✅ PostgreSQL configured
- ✅ Redis configured
- ✅ Encryption key in .env
- ✅ Branch created (mySaaS)
- ✅ All packages installed

**Blockers:** None - ready to start immediately after alignment discussion

---

**Please review the questions above and let me know your preferences so we can proceed with a clear, aligned strategy! 🚀**
