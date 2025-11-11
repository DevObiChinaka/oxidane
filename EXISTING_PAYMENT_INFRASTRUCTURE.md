# 💳 EXISTING PAYMENT INFRASTRUCTURE REVIEW
**Date:** November 10, 2025  
**Purpose:** Document all existing payment-related code before implementing full integration

---

## 📦 WHAT ALREADY EXISTS

### ✅ 1. Payment Models (COMPLETE)

**Location:** `backend/subscriptions/models.py`

#### PaymentMethod Model (Lines 129-180)
```python
class PaymentMethod(models.Model):
    """Stored payment methods (tokenized, never raw card data)"""
    
    # Fields:
    - id (UUID)
    - billing_profile (FK to BillingProfile)
    - payment_type (card/bank/mobile_money)
    - gateway_authorization_code (Paystack authorization)
    - card_last4, card_brand, card_exp_month, card_exp_year
    - bank_name, account_name
    - is_default, is_active
    - created_at, last_used_at
```

#### Payment Model (Lines 516-594)
```python
class Payment(models.Model):
    """Payment transaction records"""
    
    # Fields:
    - id (UUID)
    - billing_profile (FK)
    - subscription (FK to Subscription, nullable)
    
    # Payment Details:
    - amount (base subscription amount)
    - processing_fee (gateway fee)
    - total_amount (amount + fee)
    - currency
    
    # Gateway Info:
    - payment_gateway (choices: 'paystack', 'manual')
    - gateway_reference (Paystack reference)
    - gateway_authorization_code (for recurring)
    
    # Status:
    - status (pending/processing/success/failed/refunded)
    - payment_method (FK to PaymentMethod)
    
    # Timestamps:
    - created_at, paid_at, failed_at, refunded_at
    
    # Additional:
    - failure_reason
    - gateway_response (JSONField - full response data)
    
    # Methods:
    - mark_as_paid()
    - mark_as_failed(reason)
```

**Status:** ✅ **COMPLETE** - Models are production-ready!

---

### ✅ 2. PaymentConfiguration Model (COMPLETE)

**Location:** `backend/subscriptions/models.py` (Lines 2348-2600+)

```python
class PaymentConfiguration(models.Model):
    """Singleton model for payment gateway configuration"""
    
    # Paystack Configuration:
    - paystack_public_key (pk_test_... or pk_live_...)
    - paystack_secret_key (sk_test_... or sk_live_...)
    - paystack_webhook_secret (for signature verification)
    - paystack_webhook_url (auto-generated)
    - paystack_enabled (Boolean)
    
    # Stripe Configuration:
    - stripe_publishable_key (pk_test_...)
    - stripe_secret_key (sk_test_...)
    - stripe_webhook_secret (whsec_...)
    - stripe_webhook_url
    - stripe_enabled (Boolean)
    
    # General Settings:
    - primary_provider (choices: 'paystack', 'stripe')
    - is_test_mode (Boolean)
    - supported_currencies (JSONField - ['NGN', 'USD', 'GBP', 'EUR'])
    
    # Methods:
    - get_instance() - Get singleton instance
    - is_paystack_configured() - Check if Paystack keys exist
    - is_stripe_configured() - Check if Stripe keys exist
    - has_any_provider_configured()
    - get_masked_paystack_public_key()
    - get_masked_paystack_secret_key()
    - get_masked_stripe_publishable_key()
    - get_masked_stripe_secret_key()
    - clean() - Validates key formats, enforces singleton
    - save() - Sets default currencies
```

**Status:** ✅ **COMPLETE** - Singleton pattern enforced, validation built-in!

---

### ⚠️ 3. Payment Services (PARTIAL - Needs Update)

**Location:** `backend/subscriptions/payment_service.py`

#### PaystackService Class
```python
class PaystackService:
    """Paystack Payment Gateway Integration"""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        # ❌ ISSUE: Reads from settings instead of PaymentConfiguration model
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
    
    # ✅ Methods Implemented:
    def initialize_payment(email, amount, reference, callback_url, metadata):
        """Initialize payment transaction"""
        - Converts amount to kobo (amount * 100)
        - POSTs to /transaction/initialize
        - Returns: authorization_url, access_code, reference
    
    def verify_payment(reference):
        """Verify payment status"""
        - GETs from /transaction/verify/{reference}
        - Returns: verified, amount, currency, customer_email, paid_at
    
    def verify_webhook_signature(request_body, signature):
        """Verify webhook signature using HMAC SHA512"""
        - Uses secret_key to compute signature
        - Compares with X-Paystack-Signature header
```

#### StripeService Class
```python
class StripeService:
    """Stripe Payment Gateway Integration"""
    
    def __init__(self):
        # ❌ ISSUE: Reads from settings instead of PaymentConfiguration model
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    # ❌ NOT IMPLEMENTED:
    def initialize_payment(...):
        return {'success': False, 'error': 'Stripe integration coming soon'}
    
    def verify_payment(...):
        return {'success': False, 'error': 'Stripe integration coming soon'}
```

#### PaymentService Class (Unified)
```python
class PaymentService:
    """Unified payment service for multiple gateways"""
    
    def __init__(self, gateway='paystack'):
        if gateway == 'paystack':
            self.provider = PaystackService()
        elif gateway == 'stripe':
            self.provider = StripeService()
    
    def initialize_payment(**kwargs):
        return self.provider.initialize_payment(**kwargs)
    
    def verify_payment(reference):
        return self.provider.verify_payment(reference)
```

**Status:** ⚠️ **NEEDS UPDATE**
- ✅ Paystack initialization works
- ✅ Paystack verification works
- ✅ Webhook signature verification works
- ❌ **CRITICAL:** Services read from settings, NOT from PaymentConfiguration model
- ❌ Stripe not implemented
- ❌ No create_customer() method

---

### ✅ 4. Payment Calculators (COMPLETE)

**Location:** `backend/subscriptions/payment_calculator.py` & `payment_utils.py`

```python
class PaymentCalculator:
    """Calculate payment amounts including gateway fees"""
    
    FEES = {
        'NGN': {
            'percentage': 0.015,  # 1.5%
            'fixed': 100,         # ₦100
            'cap': 2000,          # Max ₦2,000
        },
        'USD': {
            'percentage': 0.039,  # 3.9%
            'fixed': 0.50,        # $0.50
            'cap': None,
        },
        'GHS': {'percentage': 0.029, 'fixed': 0, 'cap': None},
        'ZAR': {'percentage': 0.029, 'fixed': 0, 'cap': None},
    }
    
    @classmethod
    def calculate_total_with_fees(base_amount, currency='NGN', pass_fee_to_customer=True):
        """
        Calculate total with fees
        
        Returns:
        {
            'base_amount': float,
            'processing_fee': float,
            'total_to_charge': float,
            'you_receive': float,
            'currency': str,
            'fee_passed_to_customer': bool,
            'fee_breakdown': str
        }
        """
```

**Status:** ✅ **COMPLETE** - Ready to use!

---

### ✅ 5. Payment Serializers (COMPLETE)

**Location:** `backend/subscriptions/serializers.py`

```python
class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serialize payment methods (cards, banks)"""
    # Line 36

class PaymentSerializer(serializers.ModelSerializer):
    """Serialize payment transactions"""
    # Line 78

class PaymentConfigurationSerializer(serializers.ModelSerializer):
    """Serialize PaymentConfiguration with masking"""
    # Line 1405
    
    # Read-only masked fields:
    - paystack_public_key_masked
    - paystack_secret_key_masked
    - stripe_publishable_key_masked
    - stripe_secret_key_masked
    
    # Write-only fields:
    - paystack_public_key_write
    - paystack_secret_key_write
    - stripe_publishable_key_write
    - stripe_secret_key_write
    
    # Validation methods:
    - validate_paystack_public_key_write()
    - validate_paystack_secret_key_write()
```

**Status:** ✅ **COMPLETE** - Includes key masking and validation!

---

### ✅ 6. Payment Admin Interface (COMPLETE)

**Location:** `backend/subscriptions/admin.py` (Line 1077+)

```python
@admin.register(PaymentConfiguration)
class PaymentConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for payment gateway configuration"""
    
    list_display = [
        'primary_provider_display',
        'mode_display',
        'paystack_status',
        'stripe_status',
        'currencies_display'
    ]
    
    fieldsets = [
        ('Core Configuration', {...}),
        ('Paystack Configuration', {...}),
        ('Stripe Configuration', {...}),
    ]
    
    # Custom display methods:
    - paystack_status(obj) - Shows ✅ Configured / ⚠️ Disabled / ❌ Not Configured
    - stripe_status(obj) - Same for Stripe
    - masked_paystack_public(obj)
    - masked_paystack_secret(obj)
    - masked_stripe_publishable(obj)
    - masked_stripe_secret(obj)
```

**Status:** ✅ **COMPLETE** - Admin can configure payments!

---

### ✅ 7. Payment Signals (COMPLETE)

**Location:** `backend/subscriptions/signals.py`

```python
# Signal definitions:
payment_received = Signal()  # Emitted on successful payment
payment_failed = Signal()    # Emitted on failed payment

# Signal handlers:
@receiver(payment_received)
def log_payment_received(sender, subscription, amount, payment_reference, **kwargs):
    """Log successful payment"""

@receiver(payment_received)
def update_revenue_analytics(sender, subscription, amount, payment_reference, **kwargs):
    """Update revenue tracking"""

@receiver(payment_failed)
def log_payment_failed(sender, subscription, amount, reason, **kwargs):
    """Log payment failure"""

@receiver(payment_failed)
def track_payment_failure(sender, subscription, amount, reason, **kwargs):
    """Track failure analytics"""

# Utility functions:
def emit_payment_received_signal(subscription, amount, payment_reference):
    """Emit payment_received signal"""

def emit_payment_failed_signal(subscription, amount, reason):
    """Emit payment_failed signal"""
```

**Status:** ✅ **COMPLETE** - Ready to use!

---

### ✅ 8. Email Templates (COMPLETE)

**Location:** `backend/users/models.py` & `email_service.py`

**Email Templates for Payments:**
- `payment_success` - Sent when payment is successful
- `payment_failed` - Sent when payment fails

**Email Service:**
```python
# users/email_service.py
def prepare_variables(user=None, subscription=None, payment=None, custom_vars=None):
    """
    Prepares variables for email templates
    
    Payment variables:
    - payment.amount
    - payment.reference
    - payment.date
    - payment.status
    """

def send_payment_failed_email(user, payment_details, test_mode=False):
    """Send payment failed email"""
```

**Email Automation:**
```python
# users/email_automation.py
def trigger_payment_failed_email(self, user, payment_details=None):
    """Trigger payment failed email with variables"""
```

**Status:** ✅ **COMPLETE** - Templates exist and tested!

---

## 🔴 WHAT'S MISSING

### 1. No Payment API Endpoints
**Need to Create:**
- `POST /api/payments/initialize/` - Initialize payment
- `POST /api/payments/verify/` - Verify payment
- `POST /api/payments/webhook/paystack/` - Paystack webhook
- `POST /api/payments/webhook/stripe/` - Stripe webhook
- `GET /api/payments/history/` - Payment history
- `GET /api/payments/{id}/invoice/` - Download invoice

**Location:** Need to create `backend/payments/views.py` and `backend/payments/urls.py`

### 2. Payment Service Needs Update
**Issues:**
- Services read from `settings.py` instead of `PaymentConfiguration` model
- Need to change:
  ```python
  # OLD:
  self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
  
  # NEW:
  config = PaymentConfiguration.get_instance()
  self.secret_key = config.paystack_secret_key
  ```

### 3. No Invoice Model
**Need to Create:**
```python
class Invoice(models.Model):
    payment = OneToOneField(Payment)
    invoice_number = CharField()  # INV-2025-00001
    invoice_pdf = FileField(upload_to='invoices/')
    created_at = DateTimeField()
```

### 4. No Celery Tasks
**Need to Create:**
- `activate_subscription.delay(payment_id)` - Activate subscription after payment
- `add_user_to_telegram_groups.delay(user_id, plan_id)` - Auto-add to Telegram
- `send_payment_receipt_email.delay(payment_id)` - Send email receipt
- `generate_invoice.delay(payment_id)` - Generate PDF invoice

### 5. Stripe Integration Not Implemented
**Need to Implement:**
- Stripe checkout session creation
- Stripe session verification
- Stripe webhook handling
- Customer creation

### 6. No Webhook Endpoints
**Need to Create:**
- Webhook signature verification middleware
- Event processing logic
- Idempotency handling (prevent duplicate processing)

---

## 🎯 INTEGRATION PLAN

### Phase 1: Update Existing Services (Day 1)
1. **Update PaystackService** to read from `PaymentConfiguration` model
2. **Implement StripeService** methods
3. **Add create_customer() method** to both services
4. **Test services** with sandbox keys

### Phase 2: Create API Endpoints (Days 2-3)
1. Create `backend/payments/` app directory
2. Create `views.py` with all payment endpoints
3. Create `urls.py` with routes
4. Wire up to main `urls.py`
5. Write tests for all endpoints

### Phase 3: Implement Celery Tasks (Day 4)
1. Create `backend/oxidane/celery.py` - Celery app
2. Create `backend/payments/tasks.py` - Payment tasks
3. Create `backend/subscriptions/tasks.py` - Telegram tasks
4. Test task execution

### Phase 4: Invoice Generation (Day 5)
1. Create Invoice model
2. Implement PDF generation (reportlab or weasyprint)
3. Add invoice download endpoint

### Phase 5: Frontend Integration (Days 6-10)
1. Build checkout page
2. Integrate Paystack.js
3. Integrate Stripe.js
4. Success/failure pages
5. Payment history UI

---

## ✅ GOOD NEWS

**What's Already Built:**
1. ✅ **Payment models** - Production-ready with all fields
2. ✅ **PaymentConfiguration** - Singleton model with validation
3. ✅ **PaymentCalculator** - Fee calculation logic complete
4. ✅ **PaystackService** - 80% implemented (just needs config update)
5. ✅ **Payment serializers** - Complete with masking
6. ✅ **Admin interface** - Can configure Paystack/Stripe keys
7. ✅ **Payment signals** - Event system ready
8. ✅ **Email templates** - Payment success/failed templates exist

**What This Means:**
- We're **NOT starting from scratch**!
- Core infrastructure is **80% complete**
- Main work is **API endpoints + Celery tasks + Stripe implementation**
- **Timeline reduced** from 3 weeks to **2 weeks** max!

---

## 🚀 UPDATED IMPLEMENTATION PLAN

### Week 1: Backend Services & APIs (Nov 11-15)
**Day 1-2:**
- Update PaystackService to use PaymentConfiguration model
- Implement StripeService fully
- Add create_customer() methods
- Test with sandbox keys

**Day 3-4:**
- Create payment API endpoints (6 endpoints)
- Webhook signature verification
- Test with Postman

**Day 5:**
- Create Invoice model
- Implement PDF generation
- Invoice download endpoint

### Week 2: Celery & Frontend (Nov 16-22)
**Day 1-2:**
- Set up Celery app
- Implement payment tasks
- Implement Telegram tasks
- Test end-to-end activation

**Day 3-5:**
- Build checkout page
- Integrate Paystack.js
- Integrate Stripe.js
- Success/failure pages
- Payment history UI

---

## 📊 INFRASTRUCTURE SCORE

| Component | Status | Completion |
|-----------|--------|------------|
| Payment Models | ✅ Complete | 100% |
| PaymentConfiguration | ✅ Complete | 100% |
| PaymentMethod Model | ✅ Complete | 100% |
| Payment Model | ✅ Complete | 100% |
| PaymentCalculator | ✅ Complete | 100% |
| PaystackService | ⚠️ Needs Update | 80% |
| StripeService | ❌ Not Implemented | 0% |
| Payment Serializers | ✅ Complete | 100% |
| Payment Admin | ✅ Complete | 100% |
| Payment Signals | ✅ Complete | 100% |
| Email Templates | ✅ Complete | 100% |
| API Endpoints | ❌ Missing | 0% |
| Celery Tasks | ❌ Missing | 0% |
| Invoice Model | ❌ Missing | 0% |
| **OVERALL** | **⚠️ Partial** | **60%** |

---

## 🎯 NEXT IMMEDIATE STEPS

1. **Update PaymentConfiguration Plan Document** - Reflect 60% existing infrastructure
2. **Update PaystackService** - Read from model, not settings
3. **Implement StripeService** - Full implementation
4. **Create Payment APIs** - 6 endpoints
5. **Celery Setup** - Tasks for activation + Telegram

**Estimated Time Saved:** ~1 week (because models, calculators, admin all exist!)

---

**CONCLUSION:** We have **60% of payment infrastructure already built**! Main gap is API endpoints and Celery tasks. With existing models and services, we can complete payment integration in **2 weeks instead of 3**! 🚀
