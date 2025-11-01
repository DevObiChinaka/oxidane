# 💳 Billing & Subscription System Architecture

## Executive Summary

This document outlines the **secure, scalable, and industry-standard** approach for implementing billing, payment processing, and subscription management for Oxidane platform.

---

## 🎯 Current State Analysis

### What We Have ✅
1. **PricingPlan Model** - Well-structured pricing system with multiple plan types
2. **SignalSubscription Model** - Handles subscriptions with payment tracking
3. **Telegram Integration** - Stores telegram_username for group access
4. **Coupon System** - Discount codes and promotional pricing
5. **Basic Payment Flow** - Using Paystack references

### What Needs Improvement ⚠️
1. **No Payment Method Storage** - Can't save cards for recurring payments
2. **Manual Recurring Billing** - No automatic subscription renewals
3. **Limited Payment Security** - No tokenization system
4. **UI/UX Issues** - Subscriptions page looks like pricing page
5. **No Billing History** - Users can't see past payments
6. **No Payment Method Management** - Can't add/remove cards

---

## 🏦 Industry-Standard Payment Architecture

### **CRITICAL: Never Store Raw Card Data**

Top companies (Netflix, Stripe, Amazon, Shopify) follow these principles:

#### ✅ **What You SHOULD Store:**
```python
# Payment Method Token (Safe to store)
{
    "payment_method_id": "pm_1234567890",  # Stripe/Paystack token
    "last4": "4242",                        # Last 4 digits only
    "card_brand": "visa",                   # visa, mastercard, etc.
    "exp_month": 12,
    "exp_year": 2025,
    "is_default": True,
    "billing_address": {...}                # Optional
}
```

#### ❌ **What You SHOULD NEVER Store:**
- Full card numbers
- CVV/CVC codes
- Unencrypted card data
- Raw bank account details

---

## 📐 Recommended Database Schema

### **1. BillingProfile Model**
```python
class BillingProfile(models.Model):
    """User's billing profile - one per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='billing_profile')
    
    # Stripe/Paystack Customer ID (NOT card details!)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    paystack_customer_code = models.CharField(max_length=100, blank=True)
    
    # Telegram for bot access
    telegram_username = models.CharField(max_length=100, blank=True)
    telegram_user_id = models.BigIntegerField(null=True, blank=True)  # Telegram numeric ID
    telegram_verified = models.BooleanField(default=False)
    
    # Billing contact
    billing_email = models.EmailField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO country code
    postal_code = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Billing Profile: {self.user.email}"
```

### **2. PaymentMethod Model**
```python
class PaymentMethod(models.Model):
    """Stored payment methods (tokenized)"""
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Account'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    CARD_BRANDS = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('verve', 'Verve'),
        ('amex', 'American Express'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Payment gateway tokens (SAFE to store)
    stripe_payment_method_id = models.CharField(max_length=100, blank=True)
    paystack_authorization_code = models.CharField(max_length=100, blank=True)
    
    # Card display info (NOT sensitive)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='card')
    card_brand = models.CharField(max_length=20, choices=CARD_BRANDS, blank=True)
    last4 = models.CharField(max_length=4, help_text="Last 4 digits only")
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    
    # Bank info (for bank payments)
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=100, blank=True)
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-last_used']
    
    def __str__(self):
        return f"{self.card_brand} •••• {self.last4}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default per user
        if self.is_default:
            PaymentMethod.objects.filter(
                billing_profile=self.billing_profile,
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)
```

### **3. Subscription Model (Enhanced)**
```python
class Subscription(models.Model):
    """Unified subscription model"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('trialing', 'Trial Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    pricing_plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT)
    
    # Billing
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    
    # Subscription lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    
    # Renewal
    auto_renew = models.BooleanField(default=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Telegram access
    telegram_groups_granted = models.JSONField(default=list)  # ['signals', 'vip']
    telegram_access_granted = models.BooleanField(default=False)
    
    # Trial
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_active(self):
        """Check if subscription is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.current_period_start <= now <= self.current_period_end
        )
    
    def days_remaining(self):
        """Get days until renewal/expiry"""
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
```

### **4. Payment Model (Transaction History)**
```python
class Payment(models.Model):
    """Payment transaction history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_GATEWAYS = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, related_name='payments')
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Discount applied
    coupon = models.ForeignKey(CouponCode, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Gateway details
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAYS)
    gateway_transaction_id = models.CharField(max_length=100)  # Paystack reference, Stripe payment intent
    payment_method_used = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Receipt
    receipt_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.currency} {self.final_amount} ({self.status})"
```

---

## 🔐 Security Best Practices

### **1. PCI-DSS Compliance**
- ✅ Use Stripe/Paystack hosted payment pages
- ✅ Never transmit card data through your server
- ✅ Use payment gateway SDKs with tokenization
- ✅ Store only tokens, never raw card data

### **2. Data Encryption**
```python
# Django settings
DATABASES = {
    'default': {
        'OPTIONS': {
            'sslmode': 'require',  # Force SSL for database
        }
    }
}

# Environment variables for keys
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')  # Never commit to git
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY')
```

### **3. Webhook Validation**
```python
# Always validate webhook signatures
def verify_paystack_webhook(request):
    signature = request.headers.get('X-Paystack-Signature')
    payload = request.body
    
    computed_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    
    return signature == computed_signature
```

---

## 🎨 UI/UX Structure

### **Current Issue: Subscriptions Page = Pricing Page**

**Problem:** Your "Subscriptions" link goes to `/pricing`, which shows plan options (for new subscriptions), not active subscriptions.

### **Recommended Structure:**

#### **1. /pricing - Pricing Plans Page** (Public)
- Shows available plans
- Subscribe/Upgrade buttons
- For NEW subscriptions

#### **2. /billing - Billing Management** (Authenticated)
```
/billing (Main hub)
  ├── /billing/subscriptions     → Active subscriptions list
  ├── /billing/payment-methods    → Saved cards/payment methods
  ├── /billing/history           → Payment history/invoices
  └── /billing/settings          → Telegram, email, address
```

#### **3. Dashboard Sidebar Update:**
```tsx
// Replace "Subscriptions" link
<button onClick={() => router.push('/pricing')}>
  <span>Plans & Pricing</span>     // For browsing plans
</button>

<button onClick={() => router.push('/billing')}>
  <span>Billing</span>              // For managing subscriptions
</button>
```

---

## 📱 Page Designs

### **1. /billing (Main Page)**

```
╔══════════════════════════════════════════════════════════╗
║  💳 Billing & Subscriptions                              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📊 ACTIVE SUBSCRIPTIONS                                 ║
║  ┌────────────────────────────────────────────────┐    ║
║  │ 🚀 VIP Signals - Monthly                       │    ║
║  │ Status: Active ●                               │    ║
║  │ Renews: Dec 15, 2025                          │    ║
║  │ $49.99/month                                   │    ║
║  │ [Manage] [Cancel]                              │    ║
║  └────────────────────────────────────────────────┘    ║
║                                                          ║
║  💳 PAYMENT METHODS                                      ║
║  ┌────────────────────────────────────────────────┐    ║
║  │ Visa •••• 4242   Exp: 12/25   [Default]       │    ║
║  │ [Edit] [Remove]                                │    ║
║  └────────────────────────────────────────────────┘    ║
║  [+ Add Payment Method]                                 ║
║                                                          ║
║  📄 RECENT INVOICES                                      ║
║  Dec 1, 2025  -  $49.99  -  Paid  -  [Download]        ║
║  Nov 1, 2025  -  $49.99  -  Paid  -  [Download]        ║
║                                                          ║
║  📱 TELEGRAM INTEGRATION                                 ║
║  Username: @yourhandle   ✓ Verified                     ║
║  [Change Telegram]                                       ║
╚══════════════════════════════════════════════════════════╝
```

### **2. /billing/payment-methods**

```
╔══════════════════════════════════════════════════════════╗
║  💳 Payment Methods                                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  ┌─────────────────────────────────────────────┐       ║
║  │ 💳 Visa •••• 4242                            │       ║
║  │ Expires: 12/2025                             │       ║
║  │ ⭐ Default payment method                    │       ║
║  │ Last used: Dec 1, 2025                       │       ║
║  │ [Set as Default] [Remove]                    │       ║
║  └─────────────────────────────────────────────┘       ║
║                                                          ║
║  ┌─────────────────────────────────────────────┐       ║
║  │ 💳 Mastercard •••• 5678                      │       ║
║  │ Expires: 08/2026                             │       ║
║  │ Last used: Never                             │       ║
║  │ [Set as Default] [Remove]                    │       ║
║  └─────────────────────────────────────────────┘       ║
║                                                          ║
║  [+ Add New Payment Method]                             ║
║                                                          ║
║  🔒 Your payment information is securely stored         ║
║  by Stripe/Paystack. We never see your full card.      ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🔄 Payment Flow

### **Adding Payment Method (Secure)**

```
User clicks "Add Payment Method"
        ↓
Frontend loads Stripe/Paystack SDK
        ↓
Payment form appears (hosted by gateway)
        ↓
User enters card → Sent directly to gateway (NOT your server)
        ↓
Gateway returns token (pm_xxxxx)
        ↓
Your backend saves token + display info (last4, brand)
        ↓
Success! Card saved for future use
```

### **Subscription Payment (Recurring)**

```
Subscription renewal date arrives
        ↓
Cron job/Celery task triggers
        ↓
Backend fetches: user + subscription + payment_method
        ↓
Call Paystack/Stripe API with token
        ↓
Payment processed (user never enters card again!)
        ↓
Create Payment record
        ↓
Update subscription.current_period_end
        ↓
Send email receipt
```

---

## 🤖 Telegram Integration Strategy

### **Current Approach:**
- Store `telegram_username` in subscription model
- Bot needs username to add to groups

### **Problem:**
- Usernames can change
- Not all users have usernames
- Can't verify it's the correct user

### **Recommended Approach:**

1. **Store Telegram User ID (Numeric)**
```python
telegram_user_id = models.BigIntegerField(unique=True, null=True)
telegram_username = models.CharField(max_length=100, blank=True)
```

2. **Verification Flow:**
```
User subscribes → Shown unique code (e.g., OXI-4721)
        ↓
User opens Telegram bot
        ↓
User sends: /verify OXI-4721
        ↓
Bot validates code + captures telegram_user_id
        ↓
Backend marks: telegram_verified = True
        ↓
Bot automatically adds to appropriate groups
```

**Benefits:**
- ✅ Can't spoof (user ID is immutable)
- ✅ Works without username
- ✅ Automatic group management
- ✅ Can remove from groups when subscription expires

---

## 📊 Database Migration Plan

Since you already have subscriptions in production:

### **Phase 1: Add New Models (Non-Breaking)**
```bash
# Create new models without touching existing ones
python manage.py makemigrations
python manage.py migrate
```

### **Phase 2: Data Migration**
```python
# Migrate existing SignalSubscription to new Subscription model
def migrate_existing_subscriptions():
    for old_sub in SignalSubscription.objects.filter(payment_status='verified'):
        # Create BillingProfile
        profile, _ = BillingProfile.objects.get_or_create(
            user=old_sub.user,
            defaults={'telegram_username': old_sub.telegram_username}
        )
        
        # Create new Subscription
        Subscription.objects.create(
            user=old_sub.user,
            pricing_plan=old_sub.pricing_plan,
            current_period_start=old_sub.subscription_start,
            current_period_end=old_sub.subscription_end,
            status='active' if old_sub.subscription_end > timezone.now() else 'expired',
            auto_renew=old_sub.auto_renewal,
        )
```

### **Phase 3: Deprecate Old Models**
- Keep old models for historical data
- Use new models for all new subscriptions

---

## 🎯 Recommended Tech Stack

### **Payment Gateways (Choose One or Both)**

1. **Stripe** (Global, best for international)
   - ✅ Best documentation
   - ✅ Strong fraud detection
   - ✅ Automatic recurring billing
   - ✅ Customer portal (users manage own subscriptions)
   - 💰 2.9% + $0.30 per transaction

2. **Paystack** (Africa-focused)
   - ✅ Local payment methods (Naira, Mobile Money)
   - ✅ Good for Nigerian market
   - ✅ Recurring billing support
   - 💰 1.5% + ₦100 per transaction (Nigeria)

### **Implementation:**
```python
# Support both simultaneously
if user.country == 'NG':
    gateway = 'paystack'
else:
    gateway = 'stripe'
```

---

## 📝 Implementation Checklist

### **Backend:**
- [ ] Create BillingProfile model
- [ ] Create PaymentMethod model
- [ ] Create Payment (transaction history) model
- [ ] Enhance Subscription model
- [ ] Integrate Stripe/Paystack SDK
- [ ] Create webhook handlers
- [ ] Build recurring billing system (Celery)
- [ ] Migrate existing subscriptions

### **Frontend:**
- [ ] Create /billing main page
- [ ] Create /billing/subscriptions page
- [ ] Create /billing/payment-methods page
- [ ] Create /billing/history page
- [ ] Integrate Stripe Elements / Paystack Popup
- [ ] Update sidebar navigation
- [ ] Create payment method add/remove flows

### **Security:**
- [ ] Environment variables for API keys
- [ ] Webhook signature validation
- [ ] SSL/TLS enforcement
- [ ] Rate limiting on payment endpoints

---

## 💡 Quick Wins

**What you can implement TODAY:**

1. **Create BillingProfile model** - Store telegram info separately
2. **Rename "Subscriptions" to "Billing"** in sidebar
3. **Create /billing page** - Show active subscriptions
4. **Add "Upgrade" button** - Link to /pricing from billing page

---

## 🚀 Next Steps

**Let's discuss:**

1. Do you want to use Stripe, Paystack, or both?
2. Should we migrate existing subscriptions or run parallel systems?
3. Want me to start building the new models?
4. Should we create the billing pages first or backend first?

This architecture follows Netflix, Spotify, and SaaS companies' best practices. Your data will be secure, PCI-compliant, and scalable! 🎉
