"""
Test Celery in Production Mode
===============================
This script helps you verify that Celery is running properly
with a real worker (not eager mode).

BEFORE RUNNING:
1. Set USE_CELERY_EAGER=False in .env (or remove the line)
2. Start Redis: wsl sudo service redis-server start (or Docker)
3. Start Celery worker in another terminal:
   celery -A oxidane worker --pool=solo -l info

THEN RUN: python test_celery_production_mode.py
"""

import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings
from subscriptions.tasks import send_payment_receipt_email
from subscriptions.models import Payment

def check_configuration():
    """Verify Celery is configured for production mode"""
    print("=" * 60)
    print("CELERY CONFIGURATION CHECK")
    print("=" * 60)
    
    eager_mode = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    broker_url = getattr(settings, 'CELERY_BROKER_URL', 'Not set')
    
    print(f"✓ CELERY_TASK_ALWAYS_EAGER: {eager_mode}")
    print(f"✓ CELERY_BROKER_URL: {broker_url}")
    
    if eager_mode:
        print("\n" + "=" * 60)
        print("⚠️  WARNING: EAGER MODE IS ENABLED!")
        print("=" * 60)
        print("Tasks will run synchronously (blocking).")
        print("\nTo test production mode:")
        print("1. Edit .env and set: USE_CELERY_EAGER=False")
        print("2. Or remove the USE_CELERY_EAGER line entirely")
        print("3. Restart Django server")
        print("4. Re-run this script")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n✅ Production mode is ENABLED")
        print("   Tasks will be queued and processed by Celery worker")
        print()

def check_redis():
    """Check if Redis is accessible"""
    print("=" * 60)
    print("REDIS CONNECTION CHECK")
    print("=" * 60)
    
    try:
        import redis
        from celery import current_app
        
        # Get Redis connection from Celery
        broker_url = current_app.conf.broker_url
        print(f"Broker URL: {broker_url}")
        
        # Try to connect
        r = redis.from_url(broker_url)
        r.ping()
        print("✅ Redis is running and accessible!")
        
        # Check queue length
        queue_length = r.llen('celery')
        print(f"Current queue length: {queue_length} tasks")
        print()
        return True
        
    except ImportError:
        print("❌ redis-py not installed")
        print("   Install with: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("\nMake sure Redis is running:")
        print("  WSL: wsl sudo service redis-server start")
        print("  Docker: docker run -d -p 6379:6379 redis:alpine")
        print("  Windows: redis-server.exe")
        return False

def check_celery_worker():
    """Check if Celery worker is running"""
    print("=" * 60)
    print("CELERY WORKER CHECK")
    print("=" * 60)
    
    try:
        from celery import current_app
        
        # Try to ping workers
        inspect = current_app.control.inspect(timeout=3.0)
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active worker(s):")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
            print()
            return True
        else:
            print("❌ No Celery workers found!")
            print("\nStart a worker in another terminal:")
            print("  cd C:\\Users\\user\\OneDrive\\Desktop\\Oxidane\\backend")
            print("  celery -A oxidane worker --pool=solo -l info")
            return False
            
    except Exception as e:
        print(f"❌ Cannot communicate with Celery: {e}")
        print("\nMake sure Celery worker is running!")
        return False

def test_async_task():
    """Queue a task and check if it gets processed"""
    print("=" * 60)
    print("ASYNC TASK EXECUTION TEST")
    print("=" * 60)
    
    # Get a successful payment
    payment = Payment.objects.filter(status__in=['completed', 'success']).first()
    
    if not payment:
        print("❌ No successful payments found in database")
        print("   Create a test payment first")
        return False
    
    print(f"📧 Queuing email task for payment: {payment.id}")
    print(f"   Recipient: {payment.billing_profile.user.email}")
    
    # Queue the task (async)
    result = send_payment_receipt_email.delay(payment.id)
    task_id = result.id
    
    print(f"✅ Task queued successfully!")
    print(f"   Task ID: {task_id}")
    print(f"\n👀 Watch your Celery worker terminal for execution...")
    print(f"   You should see:")
    print(f"   [INFO] Task subscriptions.tasks.send_payment_receipt_email[{task_id}] received")
    print()
    
    # Monitor task status
    print("Monitoring task status (will check for 15 seconds)...")
    for i in range(15):
        status = result.status
        print(f"   [{i+1}s] Status: {status}")
        
        if status == 'SUCCESS':
            print(f"\n✅ Task completed successfully!")
            print(f"   Result: {result.result}")
            print()
            return True
        elif status == 'FAILURE':
            print(f"\n❌ Task failed!")
            print(f"   Error: {result.result}")
            return False
        
        time.sleep(1)
    
    # Check final status
    final_status = result.status
    if final_status == 'PENDING':
        print(f"\n⚠️  Task still PENDING after 15 seconds")
        print(f"   This means the task is queued but not picked up by worker")
        print(f"\n   Common causes:")
        print(f"   1. Celery worker not running")
        print(f"   2. Worker not connected to same Redis instance")
        print(f"   3. Task registered in wrong Celery app")
        return False
    elif final_status == 'SUCCESS':
        print(f"\n✅ Task completed!")
        return True
    else:
        print(f"\n⚠️  Task status: {final_status}")
        return False

def main():
    print("\n" + "=" * 60)
    print("CELERY PRODUCTION MODE TEST")
    print("=" * 60)
    print()
    
    # Step 1: Check configuration
    check_configuration()
    
    # Step 2: Check Redis
    redis_ok = check_redis()
    if not redis_ok:
        print("\n❌ Fix Redis connection first, then re-run this script")
        sys.exit(1)
    
    # Step 3: Check worker
    worker_ok = check_celery_worker()
    if not worker_ok:
        print("\n❌ Start Celery worker first, then re-run this script")
        sys.exit(1)
    
    # Step 4: Test task execution
    task_ok = test_async_task()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Configuration: ✅ Production mode")
    print(f"Redis:         {'✅ Connected' if redis_ok else '❌ Failed'}")
    print(f"Worker:        {'✅ Running' if worker_ok else '❌ Not found'}")
    print(f"Task Execution: {'✅ Success' if task_ok else '❌ Failed'}")
    print("=" * 60)
    
    if redis_ok and worker_ok and task_ok:
        print("\n🎉 SUCCESS! Celery is working in production mode!")
        print("\nYour setup:")
        print("  ✓ Redis is running")
        print("  ✓ Celery worker is processing tasks")
        print("  ✓ Tasks execute asynchronously")
        print("  ✓ Emails are sent by worker (not Django)")
        print("\nThis is exactly how it will work in production! 🚀")
    else:
        print("\n⚠️  Some checks failed. Fix issues above and re-run.")

if __name__ == '__main__':
    main()
