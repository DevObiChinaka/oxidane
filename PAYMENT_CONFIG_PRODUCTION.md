# Managing PaymentConfiguration Singleton in Production

## Overview

Your `PaymentConfiguration` model is a **singleton** - there's only ONE instance in the database that stores all payment gateway settings (Paystack & Stripe API keys, webhook secrets, etc.).

The admin can update these settings through the Django admin panel, and the changes are automatically encrypted and used by all payment services.

---

## How It Works

### Singleton Pattern
```python
# Only ONE instance exists
config = PaymentConfiguration.get_instance()

# Auto-creates if doesn't exist
# Always returns the same instance
```

### Security Features
- ✅ **Secret keys encrypted** in database (using Fernet encryption)
- ✅ **Keys masked** in API responses (`sk_test_***cdef`)
- ✅ **Auto-decryption** when services need them
- ✅ **Validation** ensures correct key formats
- ✅ **Audit trail** tracks who modified settings

---

## Production Setup

### Step 1: Initial Database Migration

After deploying to production, run migrations to create the table:

```bash
python manage.py migrate subscriptions
```

This creates the `PaymentConfiguration` table with one row.

### Step 2: Create Superuser (if not exists)

```bash
python manage.py createsuperuser
```

### Step 3: Access Django Admin

1. Go to: `https://your-domain.com/admin/`
2. Login with superuser credentials
3. Navigate to: **Subscriptions** → **Payment Configurations**

### Step 4: Configure Payment Settings

#### Paystack Settings (Primary for NGN)
```
✓ Paystack Enabled: YES
✓ Paystack Public Key: pk_live_xxxxxxxxxx
✓ Paystack Secret Key: sk_live_xxxxxxxxxx
✓ Paystack Webhook Secret: whsec_xxxxxxxxxx
```

#### General Settings
```
✓ Primary Provider: Paystack
✓ Test Mode: NO (for production)
✓ Supported Currencies: NGN, USD
```

**Important:** Enter the LIVE keys (sk_live_*, pk_live_*), not test keys!

---

## Database vs Environment Variables

### Current Setup (Database Singleton) ✅

**Advantages:**
- ✅ Admin can update keys without redeploying
- ✅ Keys encrypted in database
- ✅ No need to restart services when keys change
- ✅ Built-in validation and masking
- ✅ Audit trail (who changed what)

**How it works:**
```python
# PaystackService automatically loads from database
service = PaystackService()
# service.secret_key is auto-loaded and decrypted
```

### Alternative: Environment Variables (Not Recommended)

**Disadvantages:**
- ❌ Requires code deployment to change keys
- ❌ Keys visible in plain text in .env
- ❌ Need to restart all services
- ❌ No audit trail
- ❌ Admin can't manage settings

---

## Production Deployment Flow

### Initial Deployment

1. **Deploy Code**
   ```bash
   git push origin main
   # Platform auto-deploys (Render/Railway/Heroku)
   ```

2. **Run Migrations**
   ```bash
   # Render: Automatically runs
   # Railway: Add to build command
   # Heroku: heroku run python backend/manage.py migrate
   ```

3. **Create Superuser**
   ```bash
   # Render: Use Shell from dashboard
   # Railway: railway run python backend/manage.py createsuperuser
   # Heroku: heroku run python backend/manage.py createsuperuser
   ```

4. **Configure Payment Keys via Admin**
   - Go to admin panel
   - Update PaymentConfiguration
   - Save (keys auto-encrypt)

### Updating Payment Keys

**Scenario:** Need to rotate Paystack keys

1. **Login to Django Admin**
   - `https://your-domain.com/admin/`

2. **Edit Payment Configuration**
   - Subscriptions → Payment Configurations
   - Click the single row (ID: 1)

3. **Update Keys**
   - Enter new Paystack Secret Key: `sk_live_newkey123`
   - Enter new Paystack Public Key: `pk_live_newkey123`
   - Click "Save"

4. **Keys Automatically:**
   - ✅ Validated (must start with sk_/pk_)
   - ✅ Encrypted in database
   - ✅ Used by all workers immediately (no restart needed!)

**That's it!** No code deployment, no service restart required.

---

## Environment Variables (Still Needed)

While payment keys are in database, you still need these environment variables:

### Required for All Deployments

```bash
# Django Core
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database (auto-provided by platform)
DATABASE_URL=postgresql://...

# Redis Cloud
REDIS_URL=redis://default:password@host:port

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=YourBotUsername

# AWS S3
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxx
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1

# Frontend URL
FRONTEND_URL=https://your-frontend.vercel.app
```

### Optional (Fallback Only)

```bash
# Only if you want env var fallback (not recommended)
PAYSTACK_SECRET_KEY=sk_live_xxx  # Database takes priority
PAYSTACK_PUBLIC_KEY=pk_live_xxx  # Database takes priority
```

**Note:** The code prioritizes database config over env vars.

---

## How Services Load Configuration

### Automatic Loading

```python
# subscriptions/payment_service.py
class PaystackService:
    def __init__(self):
        config = PaymentConfiguration.get_instance()
        
        # Auto-decrypt if encrypted
        if config.paystack_secret_key.startswith('gAAAAA'):
            self.secret_key = config.decrypt_field('paystack_secret_key')
        else:
            self.secret_key = config.paystack_secret_key
        
        self.public_key = config.paystack_public_key
        self.is_enabled = config.paystack_enabled
```

### Used Throughout Codebase

```python
# In payment views
service = PaystackService()  # Auto-loads from database
response = service.initialize_payment(...)

# In tasks
config = PaymentConfiguration.get_instance()
if config.is_paystack_configured():
    service = PaystackService()
    # Process payment
```

---

## Security Best Practices

### 1. Encryption Key

The encryption key is in `settings.py`:

```python
# backend/oxidane/settings.py
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key')
```

**Critical:** Set `SECRET_KEY` environment variable in production!

```bash
# Generate a secure key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Add to environment variables:
```bash
SECRET_KEY=django-insecure-xyz123...
```

### 2. Admin Panel Access

- ✅ Only superusers can access payment configuration
- ✅ Use strong admin passwords
- ✅ Enable 2FA on admin account (recommended)
- ✅ Review audit trail regularly

### 3. Database Backups

Payment config is in database, so:
- ✅ Enable automated backups (Render/Railway/Heroku provide this)
- ✅ Test restore process
- ✅ Backup before changing keys

### 4. Key Rotation

Rotate keys periodically:
1. Generate new keys in Paystack dashboard
2. Update PaymentConfiguration via admin
3. Old keys immediately stop working
4. No downtime (atomic update)

---

## Troubleshooting

### Issue: "Paystack not configured"

**Check:**
```bash
# SSH into production
python manage.py shell

from subscriptions.models import PaymentConfiguration
config = PaymentConfiguration.get_instance()

print(f"Paystack enabled: {config.paystack_enabled}")
print(f"Has public key: {bool(config.paystack_public_key)}")
print(f"Has secret key: {bool(config.paystack_secret_key)}")
print(f"Is configured: {config.is_paystack_configured()}")
```

**Fix:**
- Ensure keys are set in Django admin
- Verify keys start with `pk_` and `sk_`

### Issue: "Decryption failed"

**Cause:** `SECRET_KEY` environment variable changed

**Fix:**
1. If you changed `SECRET_KEY`, old encrypted values are unrecoverable
2. Re-enter payment keys in Django admin
3. **Never change SECRET_KEY in production** unless necessary

### Issue: "Test keys in production"

**Check:**
```bash
python manage.py shell

from subscriptions.models import PaymentConfiguration
config = PaymentConfiguration.get_instance()

print(f"Test mode: {config.is_test_mode}")
print(f"Public key: {config.paystack_public_key[:15]}")
# Should show: pk_live_... (not pk_test_...)
```

**Fix:**
- Set `is_test_mode` to False
- Replace `pk_test_*` with `pk_live_*`
- Replace `sk_test_*` with `sk_live_*`

---

## API Access (Frontend/Admin)

### Admin API Endpoint

```
GET /api/admin/payment/config/
PATCH /api/admin/payment/config/{id}/
```

**Response includes masked keys:**
```json
{
  "id": 1,
  "paystack_public_key_masked": "pk_live_***cdef",
  "paystack_secret_key_masked": "sk_live_***xyz",
  "paystack_enabled": true,
  "is_test_mode": false,
  "primary_provider": "paystack"
}
```

**Update keys:**
```json
PATCH /api/admin/payment/config/1/
{
  "paystack_public_key_write": "pk_live_newkey123",
  "paystack_secret_key_write": "sk_live_newkey456",
  "is_test_mode": false
}
```

### Security

- ✅ Only admin users can access
- ✅ Actual keys never sent to client (masked)
- ✅ Separate write-only fields for updating
- ✅ Auto-encryption on save

---

## Comparison: Database vs Environment Variables

| Feature | Database Singleton | Environment Variables |
|---------|-------------------|----------------------|
| Admin can update | ✅ Yes (via UI) | ❌ No (needs deployment) |
| Requires restart | ❌ No (instant) | ✅ Yes (all services) |
| Encryption | ✅ Encrypted | ❌ Plain text |
| Audit trail | ✅ Yes | ❌ No |
| Validation | ✅ Built-in | ❌ Manual |
| Key masking | ✅ Automatic | ❌ Manual |
| Recommended | ✅ **Best for production** | ⚠️ Dev only |

---

## Migration Guide (If Using Env Vars Currently)

If you're currently using environment variables, migrate to database:

### Step 1: Run migrations
```bash
python manage.py migrate subscriptions
```

### Step 2: Copy keys to database

```bash
python manage.py shell
```

```python
from subscriptions.models import PaymentConfiguration
import os

config = PaymentConfiguration.get_instance()
config.paystack_public_key = os.getenv('PAYSTACK_PUBLIC_KEY')
config.paystack_secret_key = os.getenv('PAYSTACK_SECRET_KEY')
config.paystack_enabled = True
config.is_test_mode = False
config.primary_provider = 'paystack'
config.save()

# Encrypt secrets
config.encrypt_field('paystack_secret_key')

print("✅ Keys migrated to database")
```

### Step 3: Remove from environment variables

```bash
# Remove these from platform dashboard:
# PAYSTACK_SECRET_KEY
# PAYSTACK_PUBLIC_KEY
```

### Step 4: Verify

```bash
python manage.py shell
```

```python
from subscriptions.payment_service import PaystackService

service = PaystackService()
print(f"✅ Service loaded from database")
print(f"Enabled: {service.is_enabled}")
print(f"Has secret key: {bool(service.secret_key)}")
```

---

## Production Checklist

- [ ] Migrations applied (`python manage.py migrate`)
- [ ] Superuser created
- [ ] Django admin accessible
- [ ] PaymentConfiguration singleton created
- [ ] Paystack LIVE keys entered (pk_live_*, sk_live_*)
- [ ] Test mode = False
- [ ] Primary provider = Paystack
- [ ] Supported currencies = NGN, USD
- [ ] Keys validated and encrypted
- [ ] Test purchase completes successfully
- [ ] Webhook configured in Paystack dashboard
- [ ] SECRET_KEY environment variable set (for encryption)
- [ ] Database backups enabled

---

## Summary

**Your current setup is PERFECT for production!**

✅ Payment keys stored in database (encrypted)  
✅ Admin can update via Django admin panel  
✅ No code deployment needed to change keys  
✅ No service restart required  
✅ Built-in security and validation  

**Just ensure:**
1. `SECRET_KEY` environment variable is set (for encryption)
2. Admin configures keys via Django admin after deployment
3. Database backups enabled

**No additional configuration needed!** 🎉
