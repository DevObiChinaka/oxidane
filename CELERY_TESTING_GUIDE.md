# Production-like Celery Testing Guide

## Quick Start: Test Celery Locally

### Step 1: Install Redis (Windows)

**Option A: WSL (Recommended)**
```powershell
# Install WSL if not already installed
wsl --install

# Inside WSL terminal:
sudo apt update
sudo apt install redis-server
sudo service redis-server start

# Verify Redis is running:
redis-cli ping
# Should return: PONG
```

**Option B: Windows Native Redis**
1. Download from: https://github.com/microsoftarchive/redis/releases
2. Download `Redis-x64-3.0.504.msi`
3. Install and start Redis service
4. Or run manually: `redis-server.exe`

**Option C: Docker (Easiest)**
```powershell
# Install Docker Desktop, then:
docker run -d -p 6379:6379 redis:alpine
```

### Step 2: Disable Eager Mode

Edit your `.env` file:
```bash
# Change this line:
USE_CELERY_EAGER=False

# Or comment it out:
# USE_CELERY_EAGER=True
```

### Step 3: Start Services in Separate Terminals

**Terminal 1: Redis (if not using service)**
```powershell
# WSL:
wsl
sudo service redis-server start

# Or Docker:
docker run -d -p 6379:6379 redis:alpine

# Or Windows Redis:
redis-server.exe
```

**Terminal 2: Django Development Server**
```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
python manage.py runserver
```

**Terminal 3: Celery Worker**
```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
celery -A oxidane worker --pool=solo -l info
```

**Terminal 4: Celery Beat (for scheduled tasks)**
```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
celery -A oxidane beat -l info
```

**Terminal 5: Flower (Optional - Web UI for monitoring)**
```powershell
cd C:\Users\user\OneDrive\Desktop\Oxidane\backend
pip install flower
celery -A oxidane flower --port=5555
# Visit: http://localhost:5555
```

---

## Testing Checklist

### 1. Verify Redis Connection
```powershell
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('Redis:', r.ping())"
# Should print: Redis: True
```

### 2. Verify Celery Worker is Running
In Celery worker terminal, you should see:
```
[2025-11-12 14:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-11-12 14:30:00,000: INFO/MainProcess] celery@YOUR-PC ready.
```

### 3. Test Task Execution
Create a test payment and watch the Celery terminal for task execution.

### 4. Monitor with Flower
Visit http://localhost:5555 to see:
- Active workers
- Task history
- Success/failure rates
- Task execution times

---

## What to Look For

### ✅ Success Indicators:

**In Celery Worker Terminal:**
```
[INFO] Task subscriptions.tasks.send_payment_receipt_email[xxx] received
[INFO] Sending payment receipt email for payment xxx
[INFO] Payment receipt email sent to user@example.com
[INFO] Task subscriptions.tasks.send_payment_receipt_email[xxx] succeeded in 3.2s
```

**In Django Terminal:**
```
Payment verification successful
Tasks queued for async processing
```

**In Redis:**
Tasks appear briefly, then disappear (means they were processed)

### ❌ Failure Indicators:

**No Worker Connected:**
```
Django runs fine but emails never send
Tasks pile up in Redis queue
```

**Redis Not Running:**
```
ConnectionError: Error 10061 connecting to localhost:6379
```

**Import Errors:**
```
[ERROR] Received unregistered task of type 'subscriptions.tasks...'
Solution: Restart Celery worker
```

---

## Common Issues & Solutions

### Issue 1: "Connection refused" when starting Celery
**Cause:** Redis not running
**Solution:** 
```powershell
# Check if Redis is running:
netstat -an | findstr 6379

# Start Redis (WSL):
wsl sudo service redis-server start
```

### Issue 2: Tasks not executing
**Cause:** Worker not running or wrong pool type
**Solution:**
```powershell
# Always use --pool=solo on Windows:
celery -A oxidane worker --pool=solo -l info
```

### Issue 3: "Unregistered task" error
**Cause:** Code changes not picked up
**Solution:** Restart Celery worker (Ctrl+C then restart)

### Issue 4: Tasks succeed but emails not sent
**Cause:** Email configuration issue
**Solution:** Check email settings in `.env`:
```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## Advanced Testing

### Test Specific Tasks Manually

Create this test file: `test_celery_tasks.py`
```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import (
    send_payment_receipt_email,
    add_user_to_telegram_groups,
    activate_subscription
)
from subscriptions.models import Payment

# Get a recent payment
payment = Payment.objects.filter(status='success').first()

if payment:
    print(f"Testing tasks for payment: {payment.id}")
    
    # Queue tasks (will be picked up by worker)
    result1 = send_payment_receipt_email.delay(payment.id)
    print(f"Email task queued: {result1.id}")
    
    result2 = activate_subscription.delay(payment.id)
    print(f"Activation task queued: {result2.id}")
    
    # Check task status
    import time
    time.sleep(5)  # Wait for tasks to complete
    
    print(f"Email task status: {result1.status}")
    print(f"Email task result: {result1.result}")
```

Run it:
```powershell
python test_celery_tasks.py
```

Then watch the Celery worker terminal to see tasks execute!

---

## Production Simulation: Docker Compose

Create `docker-compose.yml` for the most realistic setup:

```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: oxidane
      POSTGRES_USER: oxidane
      POSTGRES_PASSWORD: oxidane
    ports:
      - "5432:5432"
  
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    environment:
      - USE_CELERY_EAGER=False
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgres://oxidane:oxidane@db:5432/oxidane
  
  celery:
    build: .
    command: celery -A oxidane worker --pool=solo -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgres://oxidane:oxidane@db:5432/oxidane
  
  celery-beat:
    build: .
    command: celery -A oxidane beat -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  flower:
    build: .
    command: celery -A oxidane flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
```

Start everything:
```powershell
docker-compose up
```

This gives you a complete production-like environment! 🚀

---

## Performance Testing

### Load Test Email Sending

```python
# test_email_load.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import send_payment_receipt_email
from subscriptions.models import Payment

payment = Payment.objects.filter(status='success').first()

# Queue 100 emails
for i in range(100):
    send_payment_receipt_email.delay(payment.id)
    print(f"Queued email {i+1}/100")

print("\nWatch Celery worker process these tasks!")
print("Visit Flower at http://localhost:5555 to monitor")
```

---

## Troubleshooting Commands

```powershell
# Check Redis connection
redis-cli ping

# Check what's in Redis queue
redis-cli
> KEYS *
> LLEN celery

# Clear all tasks from queue
redis-cli FLUSHALL

# Check Celery worker status
celery -A oxidane inspect active
celery -A oxidane inspect stats
celery -A oxidane inspect scheduled

# Purge all tasks
celery -A oxidane purge
```

---

## Summary

**Quick Setup:**
1. Install Redis (Docker is easiest)
2. Set `USE_CELERY_EAGER=False` in `.env`
3. Run 4 terminals: Redis, Django, Celery Worker, Celery Beat
4. Test payment → watch Celery terminal for email task

**Success = You see tasks executing in Celery terminal, not Django terminal!**
