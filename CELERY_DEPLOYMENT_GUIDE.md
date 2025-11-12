# Celery & Background Tasks Guide

## Understanding the Setup

### What Works WITHOUT Celery (Currently):
✅ **All synchronous operations:**
- User authentication
- Telegram account verification (direct DB update)
- Payment processing (subscription creation)
- API requests
- Admin operations

### What NEEDS Celery to Work:
❌ **Asynchronous background tasks:**
1. **Email sending** - Payment receipts, welcome emails
2. **Adding users to Telegram groups** - After payment
3. **Trial conversions** - Scheduled at 3 AM daily
4. **Auto-renewals** - Scheduled billing
5. **Subscription activations** - Post-payment processing

---

## Development Mode (Current Setup)

### Option 1: Eager Mode (Enabled by Default)
Tasks run **synchronously** (blocking) without needing Celery worker.

**Pros:**
- ✅ Works immediately, no setup needed
- ✅ All features functional
- ✅ Easy debugging

**Cons:**
- ⚠️ Emails block HTTP requests (slow)
- ⚠️ Not realistic for production testing

**How it works:**
- `.env` file has `USE_CELERY_EAGER=True`
- Tasks execute immediately in the same process
- No Celery worker needed

### Option 2: Real Celery (For Testing Production Behavior)
Run actual Celery worker for realistic testing.

**Required services:**
1. Redis (message broker)
2. Celery worker
3. Celery beat (for scheduled tasks)

**Start Celery:**
```powershell
# Terminal 1: Redis (if not running)
# Download from: https://github.com/microsoftarchive/redis/releases
redis-server

# Terminal 2: Django
python manage.py runserver

# Terminal 3: Celery Worker
celery -A oxidane worker --pool=solo -l info

# Terminal 4: Celery Beat (for scheduled tasks)
celery -A oxidane beat -l info
```

---

## Production Deployment

### Recommended: Managed Platform Workers

#### **Render.com** (Recommended)
```yaml
# render.yaml
services:
  # Web Service
  - type: web
    name: oxidane-api
    env: python
    region: oregon
    plan: starter
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn oxidane.wsgi:application --bind 0.0.0.0:$PORT"
    envVars:
      - key: USE_CELERY_EAGER
        value: "False"  # Use real Celery in production
      - key: REDIS_URL
        fromService:
          type: redis
          name: oxidane-redis
          property: connectionString
  
  # Celery Worker
  - type: worker
    name: oxidane-celery-worker
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A oxidane worker --pool=solo -l info"
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: oxidane-redis
          property: connectionString
  
  # Celery Beat (Scheduled Tasks)
  - type: worker
    name: oxidane-celery-beat
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A oxidane beat -l info"
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: oxidane-redis
          property: connectionString

  # Redis
  - type: redis
    name: oxidane-redis
    plan: starter
    ipAllowList: []
```

#### **Railway.app**
```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn oxidane.wsgi:application"
restartPolicyType = "on-failure"

# Add separate services in Railway dashboard:
# 1. Redis (from template)
# 2. Celery Worker: celery -A oxidane worker --pool=solo -l info
# 3. Celery Beat: celery -A oxidane beat -l info
```

#### **Heroku**
```yaml
# Procfile
web: gunicorn oxidane.wsgi:application
worker: celery -A oxidane worker --pool=solo -l info
beat: celery -A oxidane beat -l info

# app.json
{
  "name": "oxidane",
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    },
    "worker": {
      "quantity": 1,
      "size": "basic"
    },
    "beat": {
      "quantity": 1,
      "size": "basic"
    }
  },
  "addons": [
    "heroku-redis:mini"
  ]
}
```

### Alternative: VPS (DigitalOcean, AWS EC2, etc.)

Use **Supervisor** to manage processes:

```ini
# /etc/supervisor/conf.d/oxidane.conf
[program:oxidane-web]
command=/home/deploy/venv/bin/gunicorn oxidane.wsgi:application --bind 0.0.0.0:8000
directory=/home/deploy/oxidane/backend
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/oxidane/web.log

[program:oxidane-celery]
command=/home/deploy/venv/bin/celery -A oxidane worker --pool=solo -l info
directory=/home/deploy/oxidane/backend
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/oxidane/celery.log

[program:oxidane-beat]
command=/home/deploy/venv/bin/celery -A oxidane beat -l info
directory=/home/deploy/oxidane/backend
user=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/oxidane/beat.log
```

---

## Environment Variables for Production

```bash
# .env (Production)

# Disable eager mode
USE_CELERY_EAGER=False

# Redis (from hosting provider)
REDIS_URL=redis://red-xxxxx:6379/0

# Email
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-password

# Database
DATABASE_URL=postgres://user:pass@host:5432/db

# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Frontend
FRONTEND_URL=https://yourdomain.com
```

---

## Monitoring Celery in Production

### Check Worker Status:
```bash
celery -A oxidane inspect active
celery -A oxidane inspect stats
```

### View Task Queue:
```bash
celery -A oxidane inspect scheduled
```

### Monitor with Flower (Web UI):
```bash
pip install flower
celery -A oxidane flower --port=5555
# Visit: http://localhost:5555
```

---

## Cost Considerations

| Platform | Web | Worker | Beat | Redis | Total/Month |
|----------|-----|--------|------|-------|-------------|
| Render   | $7  | $7     | $7   | $7    | $28         |
| Railway  | $5  | $5     | $5   | $5    | $20         |
| Heroku   | $7  | $7     | $7   | $15   | $36         |
| DigitalOcean | $12 (Droplet includes all) | | | | $12 |

**Recommendation:** Start with **Railway** or **Render** for simplicity, move to VPS for cost optimization later.

---

## Summary

### For Development (Now):
- ✅ `USE_CELERY_EAGER=True` in `.env`
- ✅ No Celery worker needed
- ✅ All features work (emails send immediately)
- ⚠️ Slower (tasks block requests)

### For Production:
1. Set `USE_CELERY_EAGER=False`
2. Deploy separate Celery worker service
3. Deploy Celery beat service (for scheduled tasks)
4. Use managed Redis from hosting provider
5. Monitor with Flower or platform logs

The app will work perfectly in both modes! 🚀
