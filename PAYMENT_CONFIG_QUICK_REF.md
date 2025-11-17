# Payment Configuration - Quick Reference

## What You Need to Know

### 🔑 Where Payment Keys Are Stored

**NOT in environment variables!**  
**NOT in .env file!**  
**NOT in code!**

✅ **Stored in DATABASE** (PaymentConfiguration table)  
✅ **Managed via Django Admin Panel**  
✅ **Encrypted automatically**  

---

## Production Setup (3 Simple Steps)

### 1. Deploy Your App
```bash
# Push to GitHub
git push origin main

# Platform auto-deploys
# Migrations run automatically
```

### 2. Create Admin User
```bash
# Run in production shell:
python manage.py createsuperuser
```

### 3. Configure Paystack (Django Admin)
1. Go to: `https://your-domain.com/admin/`
2. Login with admin credentials
3. **Subscriptions** → **Payment Configurations**
4. Enter:
   - Paystack Public Key: `pk_live_xxx`
   - Paystack Secret Key: `sk_live_xxx`
   - Test Mode: **NO**
5. Click **Save**

**Done!** All payment processing now uses these keys.

---

## Key Benefits

| Feature | How It Works |
|---------|-------------|
| **Update Keys** | Django admin → No deployment needed |
| **Security** | Encrypted in database, masked in API |
| **Restart** | Not needed - changes apply instantly |
| **Audit Trail** | Tracks who changed what |
| **Validation** | Auto-validates key formats |

---

## Environment Variables Needed

```bash
# CRITICAL: Used to encrypt payment keys in database
SECRET_KEY=your-django-secret-key

# Other required vars
REDIS_URL=redis://...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
TELEGRAM_BOT_TOKEN=...
```

**NOT needed:** `PAYSTACK_SECRET_KEY`, `PAYSTACK_PUBLIC_KEY`

---

## How Code Loads Keys

```python
# Automatic loading (you don't need to change anything)
service = PaystackService()  # Auto-loads from database
service.initialize_payment(...)  # Uses database keys
```

---

## Updating Keys (Zero Downtime)

1. **Get new keys** from Paystack dashboard
2. **Login to Django admin** (`/admin/`)
3. **Update PaymentConfiguration**
4. **Click Save**

✅ All services use new keys immediately  
✅ No deployment  
✅ No restart  
✅ No downtime  

---

## Troubleshooting

### "Paystack not configured"

**Check in Django shell:**
```python
from subscriptions.models import PaymentConfiguration
config = PaymentConfiguration.get_instance()
print(f"Configured: {config.is_paystack_configured()}")
```

**Fix:** Enter keys in Django admin

### "Decryption failed"

**Cause:** `SECRET_KEY` environment variable changed

**Fix:** Re-enter payment keys in Django admin

### Keys not working

**Check:**
1. Test mode = False
2. Using `pk_live_*` and `sk_live_*` (not test keys)
3. Keys entered correctly (no extra spaces)

---

## Security Checklist

- [x] `SECRET_KEY` environment variable set (CRITICAL!)
- [x] Only admin users can access payment config
- [x] Keys encrypted in database
- [x] Keys masked in API responses
- [x] Database backups enabled

---

## See Also

- **Complete Guide:** `PAYMENT_CONFIG_PRODUCTION.md`
- **Deployment Guide:** `PRODUCTION_DEPLOYMENT.md`
- **Quick Start:** `DEPLOYMENT_SUMMARY.md`

---

**Remember:** Payment keys are in the DATABASE, not environment variables! 🎯
