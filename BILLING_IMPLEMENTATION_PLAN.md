# 🚀 Billing System Implementation Plan

## Overview
Implementing secure billing system with Paystack, automatic renewals, and Telegram verification.

---

## 📋 Phase 1: Backend Models & Verification (Week 1)

### Step 1.1: Create Billing Models
**File:** `backend/subscriptions/billing_models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid
import random
from datetime import timedelta

User = get_user_model()

class BillingProfile(models.Model):
    """User's billing profile - one per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='billing_profile')
    
    # Paystack Customer
    paystack_customer_code = models.CharField(max_length=100, blank=True)
    
    # Telegram (for bot access)
    telegram_user_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    telegram_verified = models.BooleanField(default=False)
    telegram_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Verification code (temporary)
    verification_code = models.CharField(max_length=20, blank=True)
    verification_code_expires = models.DateTimeField(null=True, blank=True)
    
    # Billing contact
    billing_email = models.EmailField(blank=True)
    
    # Address (optional but useful)
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default='NG')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_profiles'
        verbose_name = 'Billing Profile'
        verbose_name_plural = 'Billing Profiles'
    
    def __str__(self):
        return f"Billing: {self.user.email}"
    
    def generate_verification_code(self):
        """Generate unique verification code for Telegram"""
        code = f"OXI-{random.randint(1000, 9999)}"
        self.verification_code = code
        self.verification_code_expires = timezone.now() + timedelta(hours=24)
        self.save()
        return code
    
    def verify_telegram(self, telegram_user_id, telegram_username):
        """Mark Telegram as verified"""
        self.telegram_user_id = telegram_user_id
        self.telegram_username = telegram_username.replace('@', '')  # Remove @ if present
        self.telegram_verified = True
        self.telegram_verified_at = timezone.now()
        self.verification_code = ''
        self.verification_code_expires = None
        self.save()
        return True
    
    def is_verification_code_valid(self, code):
        """Check if verification code is valid"""
        if not self.verification_code or not self.verification_code_expires:
            return False
        
        if self.verification_code != code:
            return False
        
        if timezone.now() > self.verification_code_expires:
            return False
        
        return True


class PaymentMethod(models.Model):
    """Stored payment methods (tokenized via Paystack)"""
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('verve', 'Verve'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_profile = models.ForeignKey(BillingProfile, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Paystack authorization code (SAFE to store - this is a token)
    authorization_code = models.CharField(max_length=100, unique=True)
    
    # Card display info (NOT sensitive)
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    last4 = models.CharField(max_length=4)
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    bank = models.CharField(max_length=100, blank=True)
    
    # Paystack metadata
    signature = models.CharField(max_length=100)
    reusable = models.BooleanField(default=True)
    country_code = models.CharField(max_length=2, default='NG')
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-last_used']
    
    def __str__(self):
        return f"{self.card_type} •••• {self.last4}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default per billing profile
        if self.is_default:
            PaymentMethod.objects.filter(
                billing_profile=self.billing_profile,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if card is expired"""
        now = timezone.now()
        return (self.exp_year < now.year or 
                (self.exp_year == now.year and self.exp_month < now.month))


class Subscription(models.Model):
    """Unified subscription model"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('trialing', 'Trial Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_subscriptions')
    pricing_plan = models.ForeignKey('PricingPlan', on_delete=models.PROTECT)
    
    # Billing
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Subscription lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    
    # Renewal
    auto_renew = models.BooleanField(default=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Telegram access
    telegram_groups_granted = models.JSONField(default=list)  # ['signals', 'vip']
    telegram_access_granted = models.BooleanField(default=False)
    telegram_access_granted_at = models.DateTimeField(null=True, blank=True)
    
    # Trial (optional)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['current_period_end']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.pricing_plan.name} ({self.status})"
    
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
    
    def cancel(self, immediately=False, reason=''):
        """Cancel subscription"""
        self.cancellation_reason = reason
        self.canceled_at = timezone.now()
        
        if immediately:
            self.status = 'canceled'
            self.current_period_end = timezone.now()
            self.auto_renew = False
        else:
            # Cancel at end of period
            self.cancel_at_period_end = True
            self.auto_renew = False
        
        self.save()
        return True


class Payment(models.Model):
    """Payment transaction history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPES = [
        ('subscription', 'Subscription Payment'),
        ('renewal', 'Subscription Renewal'),
        ('upgrade', 'Plan Upgrade'),
        ('refund', 'Refund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, related_name='payments')
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    
    # Discount/Coupon
    coupon = models.ForeignKey('CouponCode', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Paystack details
    paystack_reference = models.CharField(max_length=100, unique=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    authorization_code = models.CharField(max_length=100, blank=True)
    
    payment_method_used = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='subscription')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Receipt
    receipt_url = models.URLField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['paystack_reference']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.currency} {self.final_amount} ({self.status})"
```

### Step 1.2: Create Migration
```bash
cd backend
python manage.py makemigrations subscriptions
python manage.py migrate
```

### Step 1.3: Create Auto-Create Signal
**File:** `backend/subscriptions/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .billing_models import BillingProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_billing_profile(sender, instance, created, **kwargs):
    """Automatically create billing profile for new users"""
    if created:
        BillingProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_billing_profile(sender, instance, **kwargs):
    """Ensure billing profile exists"""
    if not hasattr(instance, 'billing_profile'):
        BillingProfile.objects.create(user=instance)
```

**Register in:** `backend/subscriptions/apps.py`
```python
class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        import subscriptions.signals  # Import signals
```

---

## 📋 Phase 2: Telegram Verification (Week 1)

### Step 2.1: Verification API Endpoints
**File:** `backend/subscriptions/telegram_views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .billing_models import BillingProfile

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_verification_code(request):
    """Generate Telegram verification code"""
    user = request.user
    billing_profile = user.billing_profile
    
    # Generate code
    code = billing_profile.generate_verification_code()
    
    return Response({
        'verification_code': code,
        'expires_in': '24 hours',
        'bot_username': 'OxidaneBot',  # Your actual bot username
        'instructions': [
            'Open Telegram',
            f'Search for @OxidaneBot',
            f'Send: /verify {code}',
            'Wait for confirmation'
        ]
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def telegram_verification_status(request):
    """Check if Telegram is verified"""
    billing_profile = request.user.billing_profile
    
    return Response({
        'verified': billing_profile.telegram_verified,
        'telegram_username': billing_profile.telegram_username,
        'telegram_user_id': billing_profile.telegram_user_id,
        'verified_at': billing_profile.telegram_verified_at,
    })

@api_view(['POST'])
def verify_telegram_callback(request):
    """
    Called by Telegram bot when user verifies
    Secure this with bot secret token!
    """
    # Verify request is from your bot
    bot_secret = request.headers.get('X-Bot-Secret')
    if bot_secret != settings.TELEGRAM_BOT_SECRET:
        return Response({'error': 'Unauthorized'}, status=401)
    
    verification_code = request.data.get('verification_code')
    telegram_user_id = request.data.get('telegram_user_id')
    telegram_username = request.data.get('telegram_username')
    
    # Find billing profile with this code
    try:
        billing_profile = BillingProfile.objects.get(verification_code=verification_code)
    except BillingProfile.DoesNotExist:
        return Response({'error': 'Invalid verification code'}, status=400)
    
    # Check code is valid
    if not billing_profile.is_verification_code_valid(verification_code):
        return Response({'error': 'Verification code expired or invalid'}, status=400)
    
    # Verify telegram
    billing_profile.verify_telegram(telegram_user_id, telegram_username)
    
    return Response({
        'success': True,
        'user_email': billing_profile.user.email,
        'message': 'Telegram verified successfully!'
    })
```

### Step 2.2: Bot Command Handler
**File:** `backend/oxiword_bot.py` (update existing)

```python
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import requests
import os

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /verify command"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide verification code\n"
            "Usage: /verify OXI-1234"
        )
        return
    
    verification_code = context.args[0].upper()
    user = update.effective_user
    
    # Send to backend
    response = requests.post(
        f"{os.getenv('BACKEND_URL')}/api/billing/telegram/verify-callback/",
        json={
            'verification_code': verification_code,
            'telegram_user_id': user.id,
            'telegram_username': user.username or '',
        },
        headers={'X-Bot-Secret': os.getenv('TELEGRAM_BOT_SECRET')}
    )
    
    if response.status_code == 200:
        data = response.json()
        await update.message.reply_text(
            f"✅ Verification successful!\n\n"
            f"Your Telegram account is now linked to {data['user_email']}\n"
            f"You can now subscribe to premium plans."
        )
    else:
        await update.message.reply_text(
            "❌ Verification failed. Please check your code or generate a new one."
        )

# Add to bot handlers
application.add_handler(CommandHandler("verify", verify_command))
```

---

## 📋 Phase 3: Paystack Integration (Week 2)

### Step 3.1: Install Dependencies
```bash
pip install pypaystack2
```

### Step 3.2: Paystack Service
**File:** `backend/subscriptions/paystack_service.py`

```python
from pypaystack import Transaction, Customer, Subscription as PaystackSubscription
from django.conf import settings
from decimal import Decimal

class PaystackService:
    def __init__(self):
        self.transaction = Transaction(authorization_key=settings.PAYSTACK_SECRET_KEY)
        self.customer = Customer(authorization_key=settings.PAYSTACK_SECRET_KEY)
    
    def initialize_payment(self, email, amount, reference, metadata=None):
        """Initialize payment and return payment URL"""
        response = self.transaction.initialize(
            reference=reference,
            amount=int(amount * 100),  # Convert to kobo
            email=email,
            metadata=metadata or {},
            channels=['card', 'bank', 'ussd', 'mobile_money']
        )
        
        if response['status']:
            return {
                'authorization_url': response['data']['authorization_url'],
                'access_code': response['data']['access_code'],
                'reference': response['data']['reference']
            }
        else:
            raise Exception(response['message'])
    
    def verify_payment(self, reference):
        """Verify payment was successful"""
        response = self.transaction.verify(reference=reference)
        
        if response['status']:
            return response['data']
        else:
            raise Exception(response['message'])
    
    def charge_authorization(self, authorization_code, email, amount, reference):
        """Charge saved card (for recurring billing)"""
        response = self.transaction.charge(
            reference=reference,
            authorization_code=authorization_code,
            email=email,
            amount=int(amount * 100)
        )
        
        if response['status']:
            return response['data']
        else:
            raise Exception(response['message'])
```

### Step 3.3: Subscription Payment Flow
**File:** `backend/subscriptions/payment_views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .billing_models import BillingProfile, Payment, Subscription
from .paystack_service import PaystackService
import uuid

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_subscription_payment(request):
    """Start subscription payment flow"""
    user = request.user
    billing_profile = user.billing_profile
    
    # Check Telegram verification
    if not billing_profile.telegram_verified:
        return Response({
            'error': 'telegram_not_verified',
            'message': 'Please verify your Telegram account first',
            'verification_required': True
        }, status=400)
    
    plan_id = request.data.get('plan_id')
    pricing_plan = PricingPlan.objects.get(id=plan_id)
    
    # Create payment record
    reference = f"sub_{uuid.uuid4().hex[:12]}"
    payment = Payment.objects.create(
        user=user,
        amount=pricing_plan.current_price,
        currency=pricing_plan.currency,
        final_amount=pricing_plan.current_price,
        paystack_reference=reference,
        payment_type='subscription',
        status='pending',
        metadata={
            'plan_id': str(plan_id),
            'plan_name': pricing_plan.name
        }
    )
    
    # Initialize Paystack payment
    paystack = PaystackService()
    payment_data = paystack.initialize_payment(
        email=user.email,
        amount=pricing_plan.current_price,
        reference=reference,
        metadata={
            'user_id': str(user.id),
            'plan_id': str(plan_id),
            'payment_id': str(payment.id)
        }
    )
    
    payment.paystack_access_code = payment_data['access_code']
    payment.save()
    
    return Response({
        'payment_url': payment_data['authorization_url'],
        'reference': reference,
        'amount': pricing_plan.current_price,
        'currency': pricing_plan.currency
    })
```

---

## 📋 Phase 4: Frontend Billing Pages (Week 2-3)

### Step 4.1: Update Sidebar
```tsx
// Change "Subscriptions" to "Billing"
<button onClick={() => router.push('/billing')}>
  <CreditCardIcon />
  <span>Billing</span>
</button>
```

### Step 4.2: Create Billing Pages Structure
```
frontend/src/app/billing/
  ├── page.tsx                    # Main billing hub
  ├── subscriptions/page.tsx      # Active subscriptions list
  ├── payment-methods/page.tsx    # Saved cards
  ├── history/page.tsx            # Payment history
  └── components/
      ├── TelegramVerification.tsx
      └── PaymentMethodCard.tsx
```

---

## 🤖 Summary Answers

### Your Questions:

1. **Telegram Username vs ID:**
   - Store BOTH (username for display, ID for reliability)
   - Try ID first, fallback to username search
   - Best of both worlds ✅

2. **Paystack Only:** Perfect! Lower fees, local support ✅

3. **Migration:** Yes, new structure for all future subscriptions ✅

4. **Build Order:** Backend models → Payment integration → Frontend ✅

5. **Verification:** Require before subscription, store in BillingProfile ✅

6. **Telegram Field Location:** Put in BillingProfile (not Profile) ✅

7. **Auto-Renewal:** Yes, with unsubscribe option ✅

8. **Whop Gateway:** Nice but expensive (3% extra). Stick with Paystack for now.

---

## 🎯 Next Steps

Ready to start implementing? Say the word and I'll:

1. Create the billing_models.py file
2. Create the migration
3. Set up Paystack service
4. Build Telegram verification endpoints
5. Create frontend billing pages

Let's build this! 🚀
