# Production Deployment Guide for Oxidane Platform

## Overview
This guide covers deploying Oxidane with Celery workers on cloud platforms (Render, Railway, Heroku, etc.) using Redis Cloud.

## Architecture
- **Web Server**: Django app (gunicorn)
- **Worker**: Celery worker for async tasks
- **Beat**: Celery beat for scheduled tasks
- **Broker**: Redis Cloud (TLS enabled)
- **Database**: PostgreSQL

## Prerequisites
1. Redis Cloud account: https://redis.com/try-free/
2. PostgreSQL database (provided by hosting platform)
3. Hosting platform account (Render/Railway/Heroku)

---

## 1. Redis Cloud Setup

### Create Redis Database
1. Go to https://redis.com/try-free/
2. Create a free account
3. Create a new database
4. Note your connection details:
   - **Redis URL**: `redis://default:password@host:port`
   - Example: `redis://default:abc123@redis-13905.c323.us-east-1-2.ec2.cloud.redislabs.com:13905`

### Security Settings
- TLS/SSL: **Enabled** (default)
- Default user: `default`
- Password: Auto-generated (save it!)

---

## 2. Environment Variables

Add these to your hosting platform:

```bash
# Django Core
SECRET_KEY=your-super-secret-key-here  # CRITICAL: Used for encrypting payment keys!
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (auto-provided by platform usually)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis Cloud
REDIS_URL=redis://default:your-password@redis-host:port

# Email (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=YourBotUsername

# AWS S3 (for media files)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Frontend URL
FRONTEND_URL=https://your-frontend.com
```

**⚠️ Important: Paystack Keys NOT Needed Here!**

Payment gateway keys (Paystack/Stripe) are managed through the **Django Admin Panel** via the `PaymentConfiguration` singleton model. Admin can update keys without redeploying. See `PAYMENT_CONFIG_PRODUCTION.md` for details.

---

## 3. Platform-Specific Setup

### Option A: Render (Recommended)

#### Create Services

**1. Web Service (Django)**
- **Name**: oxidane-web
- **Environment**: Python 3.11
- **Build Command**: 
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command**: 
  ```bash
  cd backend && gunicorn oxidane.wsgi:application --bind 0.0.0.0:$PORT
  ```
- **Plan**: Free or Starter

**2. Background Worker (Celery Worker)**
- **Name**: oxidane-worker
- **Environment**: Python 3.11
- **Build Command**: 
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command**: 
  ```bash
  cd backend && celery -A oxidane worker --loglevel=info
  ```
- **Plan**: Free or Starter
- **Health Check**: Disabled

**3. Background Worker (Celery Beat)**
- **Name**: oxidane-beat
- **Environment**: Python 3.11
- **Build Command**: 
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command**: 
  ```bash
  cd backend && celery -A oxidane beat --loglevel=info
  ```
- **Plan**: Free or Starter
- **Health Check**: Disabled

#### Environment Variables
Add all variables from section 2 to **each service** (Web, Worker, Beat).

---

### Option B: Railway

#### Setup with Procfile
Railway automatically detects the `Procfile` and creates services.

**1. Connect Repository**
- Link your GitHub repository
- Railway will detect Django project

**2. Add Redis**
- In Railway dashboard: **Add Service** → **Database** → **Redis**
- Copy the `REDIS_URL` from Railway dashboard (or use Redis Cloud)

**3. Configure Services**
Railway will create these from `Procfile`:
- `web`: Django app
- `worker`: Celery worker
- `beat`: Celery beat

**4. Environment Variables**
Add all variables from section 2 in Railway dashboard.

---

### Option C: Heroku

#### Setup
```bash
# Login
heroku login

# Create app
heroku create oxidane-platform

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis Cloud (use external Redis Cloud, not Heroku Redis)
# Set REDIS_URL manually

# Set environment variables
heroku config:set SECRET_KEY=xxx
heroku config:set DEBUG=False
heroku config:set REDIS_URL=redis://...
# ... add all other vars

# Deploy
git push heroku main

# Scale workers
heroku ps:scale web=1 worker=1 beat=1
```

---

## 4. Requirements File

Ensure `backend/requirements.txt` includes:

```txt
Django>=5.0.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.1
celery[redis]>=5.5.0
redis>=5.0.0
gunicorn>=21.2.0
psycopg2-binary>=2.9.9
django-cors-headers>=4.3.1
django-storages[s3]>=1.14.2
boto3>=1.34.0
python-dotenv>=1.0.0
requests>=2.31.0
Pillow>=10.2.0
pycryptodome>=3.19.0
```

---

## 5. Configure Payment Gateway (Post-Deployment)

After deployment, configure Paystack keys through Django Admin:

### Step 1: Create Superuser

**Render:**
- Go to service → Shell
- Run: `python manage.py createsuperuser`

**Railway:**
```bash
railway run python backend/manage.py createsuperuser
```

**Heroku:**
```bash
heroku run python backend/manage.py createsuperuser
```

### Step 2: Access Django Admin

1. Go to: `https://your-domain.com/admin/`
2. Login with superuser credentials
3. Navigate to: **Subscriptions** → **Payment Configurations**

### Step 3: Configure Paystack

**Click the single PaymentConfiguration row and set:**

```
✓ Paystack Enabled: YES
✓ Paystack Public Key: pk_live_xxxxxxxxxx (from Paystack dashboard)
✓ Paystack Secret Key: sk_live_xxxxxxxxxx (from Paystack dashboard)
✓ Paystack Webhook Secret: (optional, for webhook verification)

✓ Primary Provider: Paystack
✓ Test Mode: NO (for production)
✓ Supported Currencies: NGN, USD
```

**Click "Save"** - Keys are automatically:
- ✅ Validated (must start with pk_/sk_)
- ✅ Encrypted in database
- ✅ Used by all workers immediately (no restart needed!)

**📚 Detailed Guide:** See `PAYMENT_CONFIG_PRODUCTION.md` for complete instructions.

---

## 6. Verify Deployment

### Check Services are Running

**Render:**
- Web service: Should show "Live"
- Worker service: Should show "Live"
- Beat service: Should show "Live"

**Railway:**
```bash
railway logs --service web
railway logs --service worker
railway logs --service beat
```

**Heroku:**
```bash
heroku ps
# Should show: web.1, worker.1, beat.1 running
```

### Test Celery Connection

```bash
# SSH into web service (platform-specific)

# Render
curl https://oxidane-web.onrender.com/admin/

# Railway
railway run python backend/manage.py shell

# Heroku
heroku run python backend/manage.py shell

# Then in shell:
from celery import current_app
print(current_app.control.inspect().active())
```

### Test Payment Configuration

```bash
# In Django shell (from above)
from subscriptions.models import PaymentConfiguration

config = PaymentConfiguration.get_instance()
print(f"Paystack configured: {config.is_paystack_configured()}")
print(f"Test mode: {config.is_test_mode}")
print(f"Public key: {config.get_masked_paystack_public_key()}")
print(f"Secret key: {config.get_masked_paystack_secret_key()}")
```

### Test Task Processing

1. Make a test subscription purchase
2. Check worker logs for:
   ```
   [INFO] Activating subscription for payment ...
   [INFO] Adding user to Telegram groups
   [INFO] ✅ Sent single-use invite link
   [INFO] Payment receipt email sent
   ```

---

## 6. Monitoring & Logs

### View Logs

**Render:**
- Go to service → Logs tab
- Real-time streaming

**Railway:**
```bash
railway logs --service worker --tail
```

**Heroku:**
```bash
heroku logs --tail --ps worker
heroku logs --tail --ps beat
```

### Common Issues

**Issue: Worker not processing tasks**
- Check `REDIS_URL` is set correctly
- Verify Redis Cloud is accessible
- Check worker logs for connection errors
- Solution: Restart worker service

**Issue: "SSL: CERTIFICATE_VERIFY_FAILED"**
- Redis Cloud uses TLS
- Solution: Add to `settings.py`:
  ```python
  CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': 'CERT_NONE'}
  CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': 'CERT_NONE'}
  ```

**Issue: Tasks timeout**
- Default limit: 30 minutes
- For long tasks, increase in `celery.py`:
  ```python
  task_time_limit=60 * 60  # 1 hour
  ```

---

## 7. Scaling

### Auto-scaling Workers (Render)
- Go to service settings
- Enable auto-scaling
- Set min/max instances based on load

### Manual Scaling

**Render:**
- Service settings → Instance count

**Railway:**
- Settings → Replicas

**Heroku:**
```bash
heroku ps:scale worker=2 beat=1  # 2 workers, 1 beat
```

**Recommended:**
- Web: 1-3 instances
- Worker: 2-5 instances (handles more tasks)
- Beat: **Always 1** (only one scheduler needed)

---

## 8. Production Checklist

- [ ] Redis Cloud database created
- [ ] `REDIS_URL` added to environment variables
- [ ] All services deployed (web, worker, beat)
- [ ] Environment variables set on all services
- [ ] Database migrations applied
- [ ] Static files collected (if needed)
- [ ] Test purchase completes successfully
- [ ] Telegram invite sent within 5 seconds
- [ ] Email receipt sent within 10 seconds
- [ ] Scheduled tasks running (check logs at scheduled times)
- [ ] SSL certificates configured
- [ ] Custom domain connected (if applicable)
- [ ] Monitoring/alerts set up

---

## 9. Maintenance

### Update Code
```bash
# Commit changes
git add .
git commit -m "Update feature"
git push origin main

# Platform auto-deploys from GitHub
# Or manual deploy on Render/Railway dashboard
```

### Restart Services
**Render:** Service → Manual Deploy → Clear build cache & deploy

**Railway:** 
```bash
railway up
```

**Heroku:**
```bash
heroku restart
```

### View Active Tasks
```bash
# In Django shell
from celery import current_app
i = current_app.control.inspect()
print(i.active())      # Currently running
print(i.scheduled())   # Scheduled tasks
print(i.reserved())    # Reserved tasks
```

### Purge Queue (if needed)
```bash
# In Django shell
from oxidane.celery import app
app.control.purge()
```

---

## 10. Cost Estimation

### Free Tier (Dev/Testing)
- **Render**: Free web + 2 free background workers
- **Railway**: $5/month credit (sufficient for small apps)
- **Redis Cloud**: Free 30MB database
- **Total**: $0-5/month

### Production (Small Scale)
- **Render Starter**: $7/service × 3 = $21/month
- **Redis Cloud**: Free tier sufficient
- **PostgreSQL**: Included with platform
- **Total**: ~$21/month

### Production (Medium Scale)
- **Render Pro**: $25/service × 3 = $75/month
- **Redis Cloud Standard**: $7/month
- **Total**: ~$82/month

---

## Support

For issues:
1. Check service logs
2. Verify environment variables
3. Test Redis connection
4. Check Django migrations applied
5. Review this guide's troubleshooting section

**Quick health check:**
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
# Should return: PONG
```
