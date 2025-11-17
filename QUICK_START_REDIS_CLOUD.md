# Quick Start Guide - Testing with Redis Cloud

## Local Development with Redis Cloud

Even during development, you can use Redis Cloud instead of local Redis. This ensures your setup matches production exactly.

### Setup Steps

1. **Get Redis Cloud URL**
   - Go to https://redis.com/try-free/
   - Create free account (30MB free tier)
   - Create database
   - Copy connection URL: `redis://default:password@host:port`

2. **Update .env File**
   ```bash
   # In backend/.env
   REDIS_URL=redis://default:YOUR_PASSWORD@redis-xxxxx.c323.us-east-1-2.ec2.cloud.redislabs.com:13905
   ```

3. **Start Services Locally**
   
   **Terminal 1 - Django**
   ```powershell
   cd backend
   python manage.py runserver
   ```
   
   **Terminal 2 - Celery Worker**
   ```powershell
   cd backend
   celery -A oxidane worker --loglevel=info --pool=solo
   ```
   
   **Terminal 3 - Celery Beat** (optional, for scheduled tasks)
   ```powershell
   cd backend
   celery -A oxidane beat --loglevel=info
   ```

4. **Verify Connection**
   ```powershell
   python manage.py shell -c "from celery import current_app; print(current_app.control.inspect().stats())"
   ```
   
   Should show worker stats if connected successfully.

### Test Task Processing

1. Delete test subscriptions:
   ```powershell
   python manage.py shell -c "from django.contrib.auth import get_user_model; from subscriptions.models import Subscription, BillingProfile; User = get_user_model(); user = User.objects.get(email='obbinachidera123@gmail.com'); bp = BillingProfile.objects.get(user=user); Subscription.objects.filter(billing_profile=bp).delete(); print('✅ Deleted')"
   ```

2. Make test purchase via frontend

3. Watch Terminal 2 (worker) for:
   ```
   [INFO] Activating subscription for payment ...
   [INFO] Adding user to Telegram groups
   [INFO] ✅ Sent single-use invite link for TradeHub
   [INFO] Payment receipt email sent
   ```

### Production Deployment

When ready to deploy, follow: `PRODUCTION_DEPLOYMENT.md`

**Key differences in production:**
- No need to manually start workers - platform handles it
- Workers restart automatically on crash
- Scales horizontally (multiple workers)
- Logs centralized in platform dashboard

### Environment Variables Needed

**Development (.env file):**
```bash
REDIS_URL=redis://default:password@redis-host:port
PAYSTACK_SECRET_KEY=sk_test_xxx
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
TELEGRAM_BOT_TOKEN=your:token
```

**Production (Platform dashboard):**
Same as above, but with live keys:
- `PAYSTACK_SECRET_KEY=sk_live_xxx`
- `PAYSTACK_PUBLIC_KEY=pk_live_xxx`
- `DEBUG=False`
- `ALLOWED_HOSTS=your-domain.com`

### Troubleshooting

**"Connection refused" error:**
- Check `REDIS_URL` is correct
- Verify Redis Cloud database is active
- Test connection: `redis-cli -u $env:REDIS_URL ping`

**Tasks not processing:**
- Ensure worker is running (Terminal 2)
- Check worker logs for errors
- Verify Redis connection working

**SSL/TLS errors:**
- Already configured in settings.py
- Redis Cloud uses SSL by default
- Our config accepts self-signed certs

### Next Steps

1. ✅ Update `.env` with Redis Cloud URL
2. ✅ Test locally (3 terminals)
3. ✅ Verify tasks process automatically
4. ✅ Ready for production deployment!
