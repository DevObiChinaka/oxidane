# 🚀 PHASE 0.5 QUICK REFERENCE

**Status:** Ready to Begin  
**Date Started:** November 1, 2025  
**Estimated Duration:** 22 hours  
**Total Tasks:** 46  

---

## ✅ PREREQUISITES (ALL COMPLETE)

- ✅ PostgreSQL 18.0 configured (database: oxidane, user: oxidane, password: 1Halloween.)
- ✅ Redis Cloud configured (redis-13905.c323.us-east-1-2.ec2.redns.redis-cloud.com:13905)
- ✅ Branch 'mySaaS' created and pushed
- ✅ All dependencies installed
- ✅ Encryption key in .env: hLwK0race8TsEQFV8WySAOX7aWvCOqMgl8Nw5TopAFE=
- ✅ Django dev server running

---

## 🎯 STRATEGIC DECISIONS (FINALIZED)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Model Priority** | Option A (Waterfall) | All models first, then APIs, then UI |
| **Migration Timing** | Option B (Hard Cutover) | Remove old models immediately - no important data |
| **Feature Granularity** | Option B (Fine-grained) | 20+ specific features for flexibility |
| **Multi-Currency** | Option B (Auto-conversion) | USD base, auto-convert using live rates |
| **Setup Wizard** | Option A (Strict) | Block actions until setup complete |
| **Encryption** | Option B (Later) | Single key now, rotation in Phase 2 |
| **API Versioning** | Option B (Public only) | Version public APIs, not admin |
| **Testing** | Option A (TDD) | Write tests alongside each feature |

---

## 📋 TASK CHECKLIST (46 Tasks)

### **Phase 1: Models (6 hours)**
- [ ] 0.5.1: Create `Feature` model + tests
- [ ] 0.5.2: Create `SubscriptionPlan` model + tests
- [ ] 0.5.3: Create `Coupon` model + tests (replaces CouponCode)
- [ ] 0.5.4: Create `ReferralCode` model + tests
- [ ] 0.5.5: Create `Referral` model + tests
- [ ] 0.5.6: Create `TelegramConfiguration` model + tests (singleton)
- [ ] 0.5.7: Create `TelegramGroup` model + tests (replaces TelegramGroupManagement)
- [ ] 0.5.8: Create `PaymentConfiguration` model + tests (singleton)
- [ ] 0.5.9: Create `EmailConfiguration` model + tests (singleton)
- [ ] 0.5.10: Create `ExchangeRate` model + tests
- [ ] 0.5.11: Update `Subscription` model (add plan FK, referral FK, metadata) + tests

### **Phase 2: Infrastructure (3 hours)**
- [ ] 0.5.12: Create `backend/oxidane/encryption.py` + tests
- [ ] 0.5.13: Add encryption methods to models
- [ ] 0.5.14: Add helper methods (get_price, has_feature, is_valid, calculate_commission)
- [ ] 0.5.15: Create `backend/utils/singleton.py`
- [ ] 0.5.16: Create `backend/utils/exchange_rates.py` + Celery task

### **Phase 3: Migrations & Seeds (2 hours)**
- [ ] 0.5.17: Create migrations (remove PricingPlan/CouponCode/TelegramGroupManagement)
- [ ] 0.5.18: Create management command: `seed_features` (20+ features)
- [ ] 0.5.19: Create management command: `seed_default_plan`
- [ ] 0.5.20: Run migrations + seed commands

### **Phase 4: Admin APIs (5 hours)**
- [ ] 0.5.21: Plans API (GET/POST/PUT/DELETE `/api/admin/plans/`) + tests
- [ ] 0.5.22: Features API (GET/POST/PUT/DELETE `/api/admin/features/`) + tests
- [ ] 0.5.23: Coupons API (GET/POST/PUT/DELETE `/api/admin/coupons/`) + tests
- [ ] 0.5.24: Coupon usage stats API (GET `/api/admin/coupons/{id}/usage/`) + tests
- [ ] 0.5.25: Referral codes API (GET/POST `/api/admin/referrals/codes/`) + tests
- [ ] 0.5.26: Referral stats API (GET `/api/admin/referrals/stats/`) + tests
- [ ] 0.5.27: Telegram config API (GET/POST/PUT `/api/admin/telegram/config/`) + tests
- [ ] 0.5.28: Telegram groups API (GET/POST/PUT/DELETE `/api/admin/telegram/groups/`) + tests
- [ ] 0.5.29: Payment config API (GET/POST/PUT `/api/admin/payment/config/`) + tests
- [ ] 0.5.30: Email config API (GET/POST/PUT `/api/admin/email/config/`) + tests
- [ ] 0.5.31: Test email API (POST `/api/admin/email/test/`) + tests
- [ ] 0.5.32: Setup status API (GET `/api/admin/setup/status/`) + tests

### **Phase 5: Public APIs (2 hours)**
- [ ] 0.5.33: Public pricing API (GET `/api/v1/subscriptions/plans/?currency=NGN`) + tests
- [ ] 0.5.34: Validate coupon API (POST `/api/v1/subscriptions/validate-coupon/`) + tests
- [ ] 0.5.35: Validate referral API (POST `/api/v1/subscriptions/validate-referral/`) + tests
- [ ] 0.5.36: Plan upgrade/downgrade APIs + tests

### **Phase 6: Frontend (4 hours)**
- [ ] 0.5.37: Build `SetupDashboard.tsx` (5-step wizard)
- [ ] 0.5.38: Build `PlansPage.tsx` (USD base pricing, feature selectors)
- [ ] 0.5.39: Build `FeaturesPage.tsx` (category grouping, icon picker)
- [ ] 0.5.40: Build `CouponsPage.tsx` (usage stats, expiry warnings)
- [ ] 0.5.41: Build `ReferralsPage.tsx` (code generator, earnings dashboard)
- [ ] 0.5.42: Build `TelegramConfigPage.tsx` (bot config, test connection)
- [ ] 0.5.43: Build `PaymentConfigPage.tsx` (Paystack keys, currencies)
- [ ] 0.5.44: Build `EmailConfigPage.tsx` (SMTP settings, test email)
- [ ] 0.5.45: Update `/pricing` page (dynamic, currency selector)
- [ ] 0.5.46: Update checkout flow (coupon/referral input, validation)

---

## 🗂️ FILES TO CREATE/MODIFY

### **New Files to Create:**
```
backend/oxidane/encryption.py
backend/utils/__init__.py
backend/utils/singleton.py
backend/utils/exchange_rates.py
backend/subscriptions/management/commands/seed_features.py
backend/subscriptions/management/commands/seed_default_plan.py
backend/subscriptions/tests/test_feature_model.py
backend/subscriptions/tests/test_subscription_plan_model.py
backend/subscriptions/tests/test_coupon_model.py
backend/subscriptions/tests/test_referral_models.py
backend/subscriptions/tests/test_config_models.py
backend/subscriptions/tests/test_admin_apis.py
backend/subscriptions/tests/test_public_apis.py
frontend/src/app/admin/setup/page.tsx
frontend/src/app/admin/plans/page.tsx
frontend/src/app/admin/features/page.tsx
frontend/src/app/admin/coupons/page.tsx
frontend/src/app/admin/referrals/page.tsx
frontend/src/app/admin/telegram/page.tsx
frontend/src/app/admin/payment/page.tsx
frontend/src/app/admin/email/page.tsx
```

### **Existing Files to Modify:**
```
backend/subscriptions/models.py (add 12 new models)
backend/subscriptions/views.py (add admin + public APIs)
backend/subscriptions/serializers.py (add serializers for new models)
backend/subscriptions/urls.py (add new routes)
backend/oxidane/settings.py (add INSTALLED_APPS if needed)
frontend/src/app/pricing/page.tsx (update to fetch dynamic plans)
```

---

## 🔐 ENCRYPTION CONFIGURATION

**Current Status:** ✅ Encryption key already in .env

```bash
# In backend/.env
ENCRYPTION_KEY=hLwK0race8TsEQFV8WySAOX7aWvCOqMgl8Nw5TopAFE=
```

**Fields to Encrypt:**
- TelegramConfiguration: bot_token, webhook_secret
- TelegramGroup: invite_link
- PaymentConfiguration: public_key, secret_key, webhook_secret
- EmailConfiguration: smtp_password

**Usage:**
```python
from oxidane.encryption import encrypt_value, decrypt_value

# Saving
encrypted = encrypt_value("my_secret_token")
model.bot_token = encrypted

# Reading
plaintext = decrypt_value(model.bot_token)
```

---

## 🌍 EXCHANGE RATE CONFIGURATION

**API to Use:** https://api.exchangerate-api.com/v4/latest/USD (Free tier: 1500 req/month)

**Supported Currencies:**
- USD (base)
- NGN (Nigerian Naira)
- GBP (British Pound)
- EUR (Euro)

**Update Schedule:** Daily at 3:00 AM (Celery Beat task)

**Model:**
```python
class ExchangeRate(models.Model):
    currency = models.CharField(max_length=3, unique=True)  # NGN, GBP, EUR
    rate = models.DecimalField(max_digits=10, decimal_places=4)  # e.g., 1650.0000
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 📊 DEFAULT FEATURES TO SEED (20+)

### **Signals Category:**
- view_free_signals (📊)
- view_premium_signals (💎)
- view_vip_signals (👑)
- signal_notifications (🔔)
- signal_history (📈)

### **Telegram Category:**
- telegram_basic_group (💬)
- telegram_premium_group (🌟)
- telegram_vip_group (👑)

### **Courses Category:**
- view_free_courses (🎓)
- view_premium_courses (📚)
- download_course_materials (📥)
- course_certificates (🏆)

### **Support Category:**
- email_support (📧)
- priority_support (⚡)
- one_on_one_mentorship (🎯)

### **API Category:**
- api_access (🔌)
- api_advanced (⚙️)
- webhook_integrations (🔗)

### **Analytics Category:**
- basic_analytics (📊)
- advanced_analytics (📈)
- export_data (💾)

---

## 🧪 TESTING REQUIREMENTS

**Target Coverage:** 80%+

**Test Files to Create:**
- test_feature_model.py
- test_subscription_plan_model.py
- test_coupon_model.py
- test_referral_models.py
- test_config_models.py
- test_exchange_rate_model.py
- test_encryption.py
- test_singleton.py
- test_admin_apis.py
- test_public_apis.py

**Run Tests:**
```bash
cd backend
pytest subscriptions/tests/ -v --cov=subscriptions --cov-report=html
```

---

## 🚀 COMMANDS TO RUN

### **After Creating Models:**
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### **Seed Default Data:**
```bash
python manage.py seed_features
python manage.py seed_default_plan
```

### **Test Exchange Rates:**
```bash
python manage.py shell
>>> from utils.exchange_rates import get_live_rates, convert_price
>>> get_live_rates()
>>> convert_price(Decimal('100.00'), 'NGN')
```

### **Test Encryption:**
```bash
python manage.py shell
>>> from oxidane.encryption import encrypt_value, decrypt_value
>>> encrypted = encrypt_value("test_secret")
>>> decrypt_value(encrypted)
```

---

## ✅ SUCCESS CRITERIA

Phase 0.5 is complete when:
- [ ] All 12 models created with 80%+ test coverage
- [ ] Old models (PricingPlan, CouponCode, TelegramGroupManagement) removed
- [ ] 20+ features seeded in database
- [ ] Exchange rates update via Celery (can verify manually first)
- [ ] Admin can create plan with USD base price → auto-converts to NGN/GBP/EUR
- [ ] Setup wizard blocks admin dashboard until 100% complete
- [ ] All sensitive keys encrypted in database
- [ ] Public pricing page shows plans in user's selected currency
- [ ] Coupon/referral validation works at checkout
- [ ] Test email sends successfully from admin UI
- [ ] Telegram connection test works from admin UI
- [ ] All 46 tasks marked complete in todo list
- [ ] Migrations run without errors
- [ ] Test suite passes: `pytest backend/subscriptions/tests/`

---

## 📚 REFERENCE DOCUMENTS

- **ENTERPRISE_PLATFORM_ROADMAP.md** - Full 150-hour roadmap
- **PHASE_0.5_STRATEGY.md** - Complete implementation strategy
- **PHASE_0.5_ANALYSIS.md** - Pre-implementation analysis
- **CONTEXT_FOR_NEW_CHAT.md** - Context recovery guide
- **PROGRESS_TRACKER.md** - Daily progress tracking

---

## 🎯 NEXT TASK

**Task 0.5.1: Create Feature Model + Tests**

Start with:
```bash
cd backend
# Open subscriptions/models.py
# Add Feature model at the end of existing models
# Create subscriptions/tests/test_feature_model.py
```

**Model Requirements:**
- key (CharField, unique, max_length=100)
- name (CharField, max_length=200)
- description (TextField, blank=True)
- category (CharField with choices)
- icon (CharField, max_length=10, emoji)
- sort_order (IntegerField, default=0)
- is_active (BooleanField, default=True)
- timestamps (created_at, updated_at)

**Test Requirements:**
- Test creation
- Test uniqueness constraint on key
- Test string representation
- Test ordering
- Test category choices
- Test filtering by category
- Test active/inactive filtering

---

**Ready to begin! 🚀**
