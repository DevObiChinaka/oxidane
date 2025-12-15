#!/usr/bin/env python
"""
Test script to diagnose Celery Beat startup issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
sys.path.insert(0, '/var/www/oxidane/backend')
django.setup()

print("✓ Django setup successful")

try:
    from celery import Celery
    print("✓ Celery imported")
    
    app = Celery('oxidane')
    print("✓ Celery app created")
    
    app.config_from_object('django.conf:settings', namespace='CELERY')
    print("✓ Celery config loaded")
    print(f"  Broker: {app.conf.broker_url}")
    
    # Test Redis connection
    from kombu import Connection
    print("\nTesting Redis connection...")
    conn = Connection(app.conf.broker_url)
    conn.connect()
    print("✓ Redis connection successful")
    conn.release()
    
    # Test loading beat schedule
    print("\nTesting beat schedule...")
    from celery.beat import PersistentScheduler
    from celery.apps.beat import Beat
    
    beat = Beat(app=app, loglevel='INFO')
    print("✓ Beat instance created")
    
    scheduler = beat.Service(app=app)
    print("✓ Beat service created")
    
    # Try to get the scheduler
    print("\nAttempting to get scheduler...")
    sched = scheduler.get_scheduler()
    print(f"✓ Scheduler obtained: {type(sched).__name__}")
    
    # Try to setup the scheduler
    print("\nAttempting to setup scheduler...")
    sched.setup_schedule()
    print("✓ Scheduler setup successful!")
    
    # Check the schedule
    print(f"\nScheduled tasks: {len(sched.schedule)} tasks")
    for name, entry in list(sched.schedule.items())[:5]:
        print(f"  - {name}: {entry.schedule}")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed!")
