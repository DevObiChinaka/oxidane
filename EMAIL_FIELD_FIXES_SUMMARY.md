# Email Template Field Fixes - COMPLETED ✅

## Date: November 15, 2025
## Status: Templates Updated, Email Service Needs Update

---

## What Was Fixed

### 1. ✅ Subscription Email Templates (3 templates)
**Problem:** Templates used `{{plan_type}}` but SubscriptionPlan model doesn't have this field.
**Solution:** Changed all references to `{{plan.name}}`

**Files Updated:**
- `subscription_activated` - Changed plan_type → plan.name
- `subscription_expiry` - Changed plan_type → plan.name  
- `subscription_renewal` - Changed plan_type → plan.name

**Database Mapping:**
```python
# OLD (WRONG):
{{plan_type}}  # ❌ Field doesn't exist

# NEW (CORRECT):
{{plan.name}}  # ✅ Maps to Subscription.plan.name (SubscriptionPlan.name)
```

---

### 2. ✅ Payment Success Email Template
**Problem:** Used `{{transaction_id}}` and `{{payment_date}}` which don't match Payment model fields.
**Solution:** Changed to use actual Payment model field names.

**Changes:**
- `{{transaction_id}}` → `{{gateway_reference}}` (matches Payment.gateway_reference)
- `{{payment_date}}` → `{{paid_at}}` (matches Payment.paid_at)

**Database Mapping:**
```python
# Payment model fields:
gateway_reference  # Paystack reference/transaction ID
paid_at           # DateTime when payment was successful
failure_reason    # Text reason for failure
amount            # Decimal payment amount
currency          # 3-letter code (USD, NGN, etc.)
status            # pending, processing, success, failed, refunded
```

---

## Email Service Variable Mapping Required

The EmailTemplateService needs to be updated to map database fields to template variables. Here's what each template needs:

### Email Verification ✅
```python
context = {
    'user': user,  # Includes user.first_name, user.email
    'verification_url': f"{base_url}/verify-email/{token}",
}
```

### Password Reset ✅
```python
context = {
    'user': user,
    'reset_url': f"{base_url}/reset-password/{token}",
}
```

### Sign-in Notification ⚠️
```python
context = {
    'user': user,
    'signin_datetime': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
    'device': parse_user_agent(request.META.get('HTTP_USER_AGENT')),  # TODO: Implement
    'location': geolocate_ip(request.META.get('REMOTE_ADDR')),  # TODO: Implement
}
```

### Payment Success ✅
```python
context = {
    'user': payment.billing_profile.user,
    'amount': payment.amount,
    'currency': payment.currency,
    'gateway_reference': payment.gateway_reference,  # NEW: Was transaction_id
    'paid_at': payment.paid_at.strftime('%B %d, %Y'),  # NEW: Was payment_date
    'payment_method': payment.payment_method.name if payment.payment_method else 'Card',
    'description': payment.subscription.plan.name if payment.subscription else 'Subscription',
}
```

### Payment Failed ✅
```python
context = {
    'user': payment.billing_profile.user,
    'amount': payment.amount,
    'currency': payment.currency,
    'failed_date': payment.failed_at.strftime('%B %d, %Y'),
    'failure_reason': payment.failure_reason,
    'update_payment_url': f"{base_url}/billing/payment-methods",
}
```

### Subscription Activated ✅
```python
context = {
    'user': subscription.billing_profile.user,
    'plan': subscription.plan,  # NEW: Access plan.name in template
    'amount': subscription.amount_paid,
    'currency': subscription.currency,
    'next_billing_date': subscription.next_billing_date.strftime('%B %d, %Y'),
}
```

### Subscription Expiring ✅
```python
context = {
    'user': subscription.billing_profile.user,
    'plan': subscription.plan,  # NEW: Access plan.name in template
    'days_remaining': (subscription.end_date - timezone.now()).days,
    'renewal_url': f"{base_url}/billing/renew/{subscription.id}",
}
```

### Subscription Renewed ✅
```python
context = {
    'user': subscription.billing_profile.user,
    'plan': subscription.plan,  # NEW: Access plan.name in template
    'renewal_date': subscription.start_date.strftime('%B %d, %Y'),
    'next_billing_date': subscription.next_billing_date.strftime('%B %d, %Y'),
    'amount': subscription.amount_paid,
    'currency': subscription.currency,
}
```

### Telegram Added ⚠️
```python
context = {
    'user': user,
    'group_name': telegram_group.name,  # TelegramGroup.name
    'join_url': telegram_group.invite_link,  # TelegramGroup.invite_link
}
```

### Telegram Removed ⚠️
```python
context = {
    'user': user,
    'group_name': telegram_group.name,
    'removal_reason': reason,  # Passed as parameter
    'removal_date': timezone.now().strftime('%B %d, %Y'),
}
```

---

## Next Steps for Email Service

### 1. Update email_service.py Context Building
The service needs to build proper context objects for each template type:

```python
def send_email(self, template_type, recipient_email, user=None, **kwargs):
    # Get template
    template = EmailTemplate.objects.filter(
        template_type=template_type,
        status='active'
    ).first()
    
    # Build context based on template type
    if template_type == 'payment_success':
        payment = kwargs.get('payment')
        context = {
            'user': payment.billing_profile.user,
            'amount': payment.amount,
            'currency': payment.currency,
            'gateway_reference': payment.gateway_reference,
            'paid_at': payment.paid_at.strftime('%B %d, %Y'),
            'payment_method': payment.payment_method.name if payment.payment_method else 'Card',
            'description': payment.subscription.plan.name if payment.subscription else 'Subscription',
        }
    elif template_type == 'subscription_activated':
        subscription = kwargs.get('subscription')
        context = {
            'user': subscription.billing_profile.user,
            'plan': subscription.plan,  # Pass full object for plan.name
            'amount': subscription.amount_paid,
            'currency': subscription.currency,
            'next_billing_date': subscription.next_billing_date.strftime('%B %d, %Y') if subscription.next_billing_date else 'N/A',
        }
    # ... etc for each template type
```

### 2. Add Helper Functions
```python
def parse_user_agent(user_agent_string):
    """Parse User-Agent to extract device info"""
    # TODO: Use user-agents library
    pass

def geolocate_ip(ip_address):
    """Get approximate location from IP"""
    # TODO: Use geoip2 or similar
    pass
```

### 3. Update Template Rendering
Ensure Jinja2 can access nested object properties:
```python
from jinja2 import Template

# This should work:
# {{plan.name}} accesses subscription.plan.name
# {{user.first_name}} accesses user.first_name
```

---

## Testing Checklist

Before sending real emails, test each template with actual database objects:

- [ ] email_verification - Test with User object
- [ ] password_reset - Test with User object  
- [ ] signin_notification - Test with User + device/location (mock if needed)
- [ ] payment_success - Test with Payment object
- [ ] payment_failed - Test with failed Payment object
- [ ] payment_refunded - Test with refunded Payment object
- [ ] subscription_activated - Test with active Subscription object
- [ ] subscription_expiry - Test with expiring Subscription object
- [ ] subscription_renewal - Test with renewed Subscription object
- [ ] telegram_added - Test with TelegramGroup object
- [ ] telegram_removed - Test with TelegramGroup object

---

## Database Models Summary

### User (users.models.User)
- first_name, last_name, email, username ✅
- telegram_user_id ✅

### Payment (subscriptions.models.Payment)
- gateway_reference ✅ (was transaction_id)
- paid_at ✅ (was payment_date)
- failed_at, refunded_at ✅
- amount, currency ✅
- failure_reason ✅
- payment_method (FK) ✅

### Subscription (subscriptions.models.Subscription)
- plan (FK to SubscriptionPlan) ✅
- amount_paid, currency ✅
- start_date, end_date ✅
- next_billing_date ✅

### SubscriptionPlan (subscriptions.models.SubscriptionPlan)
- name ✅ (NOT plan_type)
- billing_period ✅
- base_price ✅

### TelegramGroup (subscriptions.models.TelegramGroup)
- name ✅
- invite_link ✅
- chat_id ✅

---

## Conclusion

✅ **Templates Fixed:** All system email templates now use correct database field names.

⚠️ **Email Service Update Required:** The EmailTemplateService needs to be updated to:
1. Map Payment model fields correctly
2. Pass full Subscription.plan object for plan.name access
3. Add device/location tracking for signin notifications
4. Build proper context for each template type

🔍 **Testing Required:** Send test emails for all 11 templates with real database objects to verify field mapping.
