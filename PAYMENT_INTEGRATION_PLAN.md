# 💳 PAYMENT INTEGRATION PLAN
**Date:** November 10, 2025  
**Priority:** CRITICAL - Blocking Launch  
**Timeline:** 2-3 weeks (Nov 11 - Dec 1)

---

## 🎯 GOAL

Enable users to purchase subscriptions via Paystack (Nigerian market) or Stripe (International), with automatic subscription activation and Telegram group access.

### Success Criteria:
- ✅ User selects plan on `/pricing`
- ✅ User completes payment via Paystack or Stripe
- ✅ Payment verified via webhook
- ✅ Subscription activated automatically
- ✅ User granted access to courses in plan
- ✅ **User automatically added to Telegram groups**
- ✅ Email receipt sent
- ✅ Invoice generated and available for download

---

## 📋 ARCHITECTURE OVERVIEW

### Flow Diagram:
```
1. User clicks "Subscribe" on /pricing
   ↓
2. Frontend sends POST /api/payments/initialize/
   ↓
3. Backend creates Payment record (status: pending)
   ↓
4. Backend calls Paystack/Stripe API to create checkout
   ↓
5. Frontend redirects user to payment page
   ↓
6. User completes payment
   ↓
7. Paystack/Stripe sends webhook to backend
   ↓
8. Backend verifies webhook signature
   ↓
9. Backend updates Payment (status: completed)
   ↓
10. Backend triggers Celery task: activate_subscription.delay()
    ↓
11. Celery task activates subscription:
    - Creates/updates Subscription record
    - Updates User.current_plan, subscription_status
    - Grants course access (CourseAccess records)
    - Triggers Telegram add task
    - Triggers email task
    ↓
12. Celery task: add_user_to_telegram_groups.delay()
    - Uses TelegramConfiguration.bot_token
    - Adds user to TelegramGroup chat_ids linked to plan
    - Sends welcome message
    ↓
13. Celery task: send_payment_receipt_email.delay()
    - Sends email with receipt
    - Includes invoice PDF link
    ↓
14. Frontend redirects to /billing/success
    - Shows success message
    - Displays subscription details
    - Shows Telegram group links
```

---

## 🛠️ IMPLEMENTATION PHASES

### PHASE 1: Backend Payment Services (Week 1: Nov 11-15)

#### Task 1.1: Paystack Integration Service (2 days)
**File:** `backend/payments/services/paystack_service.py`

**Methods:**
```python
class PaystackService:
    def __init__(self):
        self.config = PaymentConfiguration.objects.first()
        self.secret_key = self.config.paystack_secret_key
        self.base_url = "https://api.paystack.co"
    
    def initialize_transaction(self, email, amount, plan_slug, callback_url):
        """Initialize Paystack transaction"""
        # POST to /transaction/initialize
        # Returns: authorization_url, reference
        
    def verify_transaction(self, reference):
        """Verify payment status"""
        # GET /transaction/verify/:reference
        # Returns: status, amount, customer, metadata
        
    def verify_webhook_signature(self, payload, signature):
        """Verify webhook came from Paystack"""
        # Compare HMAC hash using webhook_secret
        
    def create_customer(self, email, first_name, last_name):
        """Create Paystack customer"""
        # POST to /customer
        # Returns: customer_code
```

**Tests:** 15 tests
- Test initialize transaction
- Test verify transaction (success/failed)
- Test webhook signature verification (valid/invalid)
- Test customer creation
- Test error handling (network errors, API errors)

#### Task 1.2: Stripe Integration Service (2 days)
**File:** `backend/payments/services/stripe_service.py`

**Methods:**
```python
import stripe

class StripeService:
    def __init__(self):
        self.config = PaymentConfiguration.objects.first()
        stripe.api_key = self.config.stripe_secret_key
    
    def create_checkout_session(self, email, amount, plan_slug, success_url, cancel_url):
        """Create Stripe Checkout Session"""
        # stripe.checkout.Session.create()
        # Returns: session_id, url
        
    def verify_session(self, session_id):
        """Verify checkout session completed"""
        # stripe.checkout.Session.retrieve()
        # Returns: payment_status, customer, subscription
        
    def handle_webhook(self, payload, sig_header):
        """Verify and process Stripe webhook"""
        # stripe.Webhook.construct_event()
        # Returns: event object
        
    def create_customer(self, email, name):
        """Create Stripe customer"""
        # stripe.Customer.create()
        # Returns: customer_id
```

**Tests:** 12 tests
- Test create checkout session
- Test verify session (paid/unpaid)
- Test webhook event verification
- Test customer creation
- Test error handling

#### Task 1.3: Payment Models (1 day)
**File:** `backend/payments/models.py`

**Models:**
```python
class Payment(models.Model):
    """Track all payment transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('paystack', 'Paystack'),
        ('stripe', 'Stripe'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey('subscriptions.Subscription', null=True, blank=True)
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Gateway References
    gateway_reference = models.CharField(max_length=255, unique=True)
    gateway_customer_id = models.CharField(max_length=255, blank=True)
    
    # Metadata
    plan_slug = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class Invoice(models.Model):
    """Generated invoices for payments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    
    invoice_number = models.CharField(max_length=50, unique=True)  # INV-2025-00001
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_invoice_number(self):
        # Format: INV-YYYY-NNNNN
        year = timezone.now().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year}'
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        self.invoice_number = f'INV-{year}-{new_num:05d}'
```

**Migration:** `0001_payment_invoice.py`

**Tests:** 15 tests
- Test Payment creation
- Test Payment status transitions
- Test Invoice number generation
- Test unique constraints

---

### PHASE 2: Backend Payment APIs (Week 1-2: Nov 16-20)

#### Task 2.1: Payment API Endpoints (3 days)
**File:** `backend/payments/views.py`

**Endpoints:**

1. **POST `/api/payments/initialize/`** - Initialize payment
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    """
    Initialize payment for a subscription plan.
    
    Request Body:
    {
        "plan_slug": "basic-monthly",
        "gateway": "paystack",  # or "stripe"
        "currency": "NGN"  # optional, defaults to user preference
    }
    
    Response:
    {
        "payment_id": "uuid",
        "authorization_url": "https://checkout.paystack.com/...",
        "reference": "ref_123456"
    }
    """
    # 1. Get plan by slug
    # 2. Get user's billing profile
    # 3. Calculate amount (with exchange rate if needed)
    # 4. Create Payment record (status: pending)
    # 5. Call Paystack/Stripe service to initialize
    # 6. Return authorization URL
```

2. **POST `/api/payments/verify/`** - Verify payment (frontend callback)
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify payment after user returns from gateway.
    
    Request Body:
    {
        "reference": "ref_123456",  # Paystack reference
        "session_id": "cs_123456"   # Stripe session_id
    }
    
    Response:
    {
        "status": "completed",
        "subscription_id": "uuid",
        "message": "Payment successful! Your subscription is now active."
    }
    """
    # 1. Call gateway service to verify
    # 2. Update Payment status
    # 3. Trigger activation (may already be done via webhook)
    # 4. Return status
```

3. **POST `/api/payments/webhook/paystack/`** - Paystack webhook
```python
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def paystack_webhook(request):
    """
    Handle Paystack webhook events.
    
    Events:
    - charge.success: Payment completed
    - charge.failed: Payment failed
    """
    # 1. Verify webhook signature
    # 2. Get event type
    # 3. Get payment reference
    # 4. Trigger activation task (if charge.success)
    # 5. Update Payment status
```

4. **POST `/api/payments/webhook/stripe/`** - Stripe webhook
```python
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    Events:
    - checkout.session.completed: Payment completed
    - payment_intent.succeeded: Payment succeeded
    """
    # Similar to Paystack webhook
```

5. **GET `/api/payments/history/`** - Payment history
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """
    Get user's payment history.
    
    Response:
    {
        "payments": [
            {
                "id": "uuid",
                "amount": "50.00",
                "currency": "USD",
                "status": "completed",
                "plan_name": "Basic Plan",
                "created_at": "2025-11-10T12:00:00Z",
                "invoice_url": "/api/payments/{id}/invoice/"
            }
        ]
    }
    """
```

6. **GET `/api/payments/{id}/invoice/`** - Download invoice PDF
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_invoice(request, payment_id):
    """
    Download invoice PDF for a payment.
    """
    # 1. Get Payment
    # 2. Get or generate Invoice
    # 3. Return PDF file
```

**URLs:** `backend/payments/urls.py`
```python
urlpatterns = [
    path('initialize/', initialize_payment),
    path('verify/', verify_payment),
    path('webhook/paystack/', paystack_webhook),
    path('webhook/stripe/', stripe_webhook),
    path('history/', payment_history),
    path('<uuid:payment_id>/invoice/', download_invoice),
]
```

**Tests:** 18 tests
- Test initialize payment (Paystack + Stripe)
- Test verify payment
- Test webhooks (valid signature, invalid signature)
- Test payment history
- Test invoice download

---

### PHASE 3: Celery Tasks & Subscription Activation (Week 2: Nov 21-22)

#### Task 3.1: Celery App Setup (1 day)
**File:** `backend/oxidane/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')

app = Celery('oxidane')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**File:** `backend/oxidane/__init__.py`
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

#### Task 3.2: Payment Tasks (1 day)
**File:** `backend/payments/tasks.py`

```python
from celery import shared_task
from django.utils import timezone
from .models import Payment, Invoice
from subscriptions.models import Subscription, SubscriptionPlan, BillingProfile
from users.models import User
from courses.models import CourseAccess

@shared_task(bind=True, max_retries=3)
def activate_subscription(self, payment_id):
    """
    Activate subscription after successful payment.
    
    Steps:
    1. Get Payment record
    2. Get SubscriptionPlan
    3. Create or update Subscription
    4. Update User subscription fields
    5. Grant course access
    6. Trigger Telegram add task
    7. Trigger email task
    8. Generate invoice
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        plan = SubscriptionPlan.objects.get(slug=payment.plan_slug)
        user = payment.user
        billing_profile = user.billing_profile
        
        # 1. Create/update Subscription
        subscription, created = Subscription.objects.update_or_create(
            billing_profile=billing_profile,
            plan=plan,
            defaults={
                'status': 'active',
                'start_date': timezone.now(),
                'end_date': calculate_end_date(plan.billing_period),
                'auto_renew': True,
            }
        )
        
        # 2. Update Payment
        payment.subscription = subscription
        payment.mark_completed()
        
        # 3. Update User fields
        user.current_plan = plan
        user.subscription_status = 'active'
        user.subscription_start_date = subscription.start_date
        user.subscription_end_date = subscription.end_date
        user.save()
        
        # 4. Grant course access
        for course in plan.courses.all():
            CourseAccess.objects.get_or_create(
                user=user,
                course=course,
                defaults={'access_granted_by': 'subscription'}
            )
        
        # 5. Trigger Telegram add
        if billing_profile.telegram_verified:
            add_user_to_telegram_groups.delay(user.id, plan.id)
        
        # 6. Send email
        send_payment_receipt_email.delay(payment.id)
        
        # 7. Generate invoice
        generate_invoice.delay(payment.id)
        
        return f"Subscription activated: {subscription.id}"
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_payment_receipt_email(payment_id):
    """Send payment receipt email"""
    # Use EmailConfiguration to send email
    # Template: payment_receipt.html
    # Include: amount, plan name, invoice link


@shared_task
def generate_invoice(payment_id):
    """Generate invoice PDF"""
    # Use reportlab or weasyprint to generate PDF
    # Save to Invoice model
```

#### Task 3.3: Telegram Tasks (1 day)
**File:** `backend/subscriptions/tasks.py`

```python
from celery import shared_task
import telegram
from .models import TelegramConfiguration, TelegramGroup
from users.models import User
from subscriptions.models import SubscriptionPlan

@shared_task(bind=True, max_retries=3)
def add_user_to_telegram_groups(self, user_id, plan_id):
    """
    Add user to all Telegram groups linked to their subscription plan.
    
    Steps:
    1. Get TelegramConfiguration (bot_token)
    2. Get user's telegram_user_id from BillingProfile
    3. Get all TelegramGroups linked to the plan
    4. For each group, add user
    5. Send welcome message
    """
    try:
        config = TelegramConfiguration.objects.first()
        
        if not config or not config.is_enabled or not config.auto_add_enabled:
            return "Telegram auto-add is disabled"
        
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        billing_profile = user.billing_profile
        
        if not billing_profile.telegram_verified:
            return "User has not verified Telegram"
        
        bot = telegram.Bot(token=config.bot_token)
        
        # Get groups linked to this plan
        groups = plan.telegram_groups.filter(is_active=True)
        
        added_groups = []
        for group in groups:
            try:
                # Add user to group
                bot.unban_chat_member(
                    chat_id=group.chat_id,
                    user_id=billing_profile.telegram_user_id
                )
                
                # Send invite link via DM (if group is private)
                if group.invite_link:
                    bot.send_message(
                        chat_id=billing_profile.telegram_user_id,
                        text=f"✅ You've been granted access to {group.name}!\n\n"
                             f"Join here: {group.invite_link}\n\n"
                             f"{config.welcome_message}"
                    )
                
                added_groups.append(group.name)
                
            except Exception as e:
                # Log error but continue with other groups
                print(f"Failed to add user to {group.name}: {e}")
        
        return f"Added to groups: {', '.join(added_groups)}"
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=3)
def remove_user_from_telegram_groups(self, user_id, plan_id):
    """
    Remove user from Telegram groups when subscription expires.
    """
    # Similar logic to add, but uses bot.ban_chat_member()
```

**Tests:** 20 tests
- Test activate_subscription task
- Test subscription creation
- Test user field updates
- Test course access grants
- Test Telegram add trigger
- Test email trigger
- Test invoice generation
- Test error handling and retries
- Test Telegram add/remove
- Test bot token validation

---

### PHASE 4: Frontend Payment Integration (Week 2-3: Nov 23-28)

#### Task 4.1: Checkout Page (2 days)
**File:** `frontend/src/app/billing/page.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import PaystackButton from './components/PaystackButton';
import StripeCheckout from './components/StripeCheckout';

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const planSlug = searchParams.get('plan');
  const router = useRouter();
  
  const [plan, setPlan] = useState(null);
  const [gateway, setGateway] = useState('paystack');
  const [loading, setLoading] = useState(false);
  
  // Fetch plan details
  // Display plan summary
  // Show payment gateway selector
  // Handle payment initialization
  
  const handlePayment = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/payments/initialize/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan_slug: planSlug,
          gateway: gateway,
        }),
      });
      
      const data = await response.json();
      
      if (gateway === 'paystack') {
        // Redirect to Paystack
        window.location.href = data.authorization_url;
      } else if (gateway === 'stripe') {
        // Redirect to Stripe Checkout
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      console.error('Payment initialization failed:', error);
    }
  };
  
  return (
    // Checkout UI
  );
}
```

#### Task 4.2: Payment Success/Failure Pages (1 day)
**Files:**
- `frontend/src/app/billing/success/page.tsx`
- `frontend/src/app/billing/failed/page.tsx`

Success page shows:
- ✅ Payment successful message
- Subscription details
- Telegram group access info
- "Go to Dashboard" button

#### Task 4.3: Payment History UI (1 day)
**File:** `frontend/src/app/billing/history/page.tsx`

- List all payments
- Show status badges
- Download invoice button
- Filter by date, status

#### Task 4.4: Subscription Management UI (2 days)
**File:** `frontend/src/app/subscriptions/page.tsx`

- Current subscription display
- Cancel subscription button
- Upgrade/downgrade options
- Payment method management
- Next billing date
- Auto-renew toggle

**Tests (Frontend):** E2E tests with Cypress/Playwright
- Test checkout flow
- Test Paystack payment (sandbox)
- Test Stripe payment (test mode)
- Test success page display
- Test payment history

---

## 🔧 CELERY DEPLOYMENT

### Development:
```bash
# Terminal 1: Start Celery worker
celery -A oxidane worker -l info

# Terminal 2: Start Celery beat (for scheduled tasks)
celery -A oxidane beat -l info

# Terminal 3: Django server
python manage.py runserver
```

### Production (Heroku/Railway):
```yaml
# Procfile
web: gunicorn oxidane.wsgi
worker: celery -A oxidane worker -l info
beat: celery -A oxidane beat -l info
```

---

## 📊 TESTING STRATEGY

### Backend Tests: 105 total
- Paystack service: 15 tests
- Stripe service: 12 tests
- Payment models: 15 tests
- Payment APIs: 18 tests
- Celery tasks: 20 tests
- Integration tests: 25 tests

### Integration Tests:
**File:** `backend/tests/test_payment_flow_integration.py`

```python
def test_full_paystack_payment_flow():
    """
    Test complete payment flow:
    1. Initialize payment
    2. Simulate Paystack webhook
    3. Verify subscription activated
    4. Verify course access granted
    5. Verify Telegram task triggered
    6. Verify email sent
    """

def test_full_stripe_payment_flow():
    """Similar to Paystack test"""

def test_failed_payment():
    """Test handling of failed payments"""

def test_webhook_duplicate_prevention():
    """Ensure duplicate webhooks don't double-activate"""
```

---

## 🚀 DEPLOYMENT CHECKLIST

### Backend:
- [ ] Create Paystack test account
- [ ] Create Stripe test account
- [ ] Admin enters API keys in `/admin/payment`
- [ ] Admin enters Telegram bot token in `/admin/telegram`
- [ ] Set up webhook URLs in Paystack dashboard
- [ ] Set up webhook URLs in Stripe dashboard
- [ ] Deploy Celery worker
- [ ] Deploy Celery beat
- [ ] Verify Redis connection

### Frontend:
- [ ] Add Paystack public key to environment variables
- [ ] Add Stripe publishable key to environment variables
- [ ] Test checkout flow in staging
- [ ] Test webhook delivery

---

## 📝 ADMIN CONFIGURATION GUIDE

### Step 1: Get Paystack API Keys
1. Go to https://dashboard.paystack.com/
2. Sign up/login
3. Navigate to Settings → API Keys & Webhooks
4. Copy:
   - Public Key (pk_test_...)
   - Secret Key (sk_test_...)
5. Create webhook: `https://yourdomain.com/api/payments/webhook/paystack/`
6. Copy Webhook Secret

### Step 2: Get Stripe API Keys
1. Go to https://dashboard.stripe.com/
2. Sign up/login
3. Navigate to Developers → API keys
4. Copy:
   - Publishable Key (pk_test_...)
   - Secret Key (sk_test_...)
5. Navigate to Developers → Webhooks
6. Add endpoint: `https://yourdomain.com/api/payments/webhook/stripe/`
7. Select events: `checkout.session.completed`, `payment_intent.succeeded`
8. Copy Webhook Secret (whsec_...)

### Step 3: Configure Platform
1. Go to `/admin/payment`
2. Enter all API keys
3. Select primary provider (Paystack or Stripe)
4. Toggle test mode ON (for testing)
5. Save

### Step 4: Configure Telegram
1. Go to `/admin/telegram`
2. Enter bot token from @BotFather
3. Toggle "Auto-add enabled" ON
4. Enter welcome message
5. Save

### Step 5: Link Telegram Groups to Plans
1. Go to `/admin/telegram` → Groups tab
2. Add each Telegram group:
   - Name: "VIP Signals Group"
   - Chat ID: Get from bot
   - Invite Link: Get from group settings
3. Save
4. Go to `/admin/plans`
5. Edit each plan
6. Select linked Telegram groups
7. Save

---

## 🎯 SUCCESS METRICS

After implementation, we should be able to:
- ✅ Process payments via Paystack (Nigerian users)
- ✅ Process payments via Stripe (International users)
- ✅ Automatically activate subscriptions on payment
- ✅ Automatically grant course access
- ✅ Automatically add users to Telegram groups
- ✅ Send email receipts
- ✅ Generate invoices
- ✅ Handle webhook duplicates gracefully
- ✅ Retry failed operations (Celery)
- ✅ Display payment history to users
- ✅ Allow subscription cancellation
- ✅ Support currency conversion

---

## 🔐 SECURITY CONSIDERATIONS

### Payment Security:
- ✅ Never store raw card data (use Paystack/Stripe tokenization)
- ✅ Verify webhook signatures (prevent spoofing)
- ✅ Use HTTPS for all payment endpoints
- ✅ Encrypt API keys in database
- ✅ Use CSRF protection on webhooks
- ✅ Rate limit payment endpoints

### Telegram Security:
- ✅ Verify user owns Telegram account before auto-add
- ✅ Encrypt bot token in database
- ✅ Rate limit bot API calls
- ✅ Handle bot errors gracefully

---

**NEXT:** Ready to start implementation. Begin with **Task 1.1: Paystack Integration Service**.
