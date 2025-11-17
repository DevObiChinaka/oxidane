"""
Redis Connection Management Guide
==================================

PROBLEM:
Redis Cloud free tier = 30 max connections
We were using: 100+ connections (3 Celery workers × 10 + cache × 50)

SOLUTION APPLIED:
✓ Reduced CELERY_BROKER_POOL_LIMIT: 10 → 2
✓ Reduced cache MAX_CONNECTIONS: 50 → 5
✓ Added CELERY_WORKER_MAX_TASKS_PER_CHILD: 50 (recycles workers)
✓ Killed duplicate Celery processes

NEW CONNECTION BREAKDOWN (for single user testing):
- 1 Celery worker: ~2-3 connections
- 1 Celery Beat: ~1-2 connections
- Django cache: ~5 connections
- Django app: ~2-3 connections
Total: ~10-13 connections (well under 30 limit)

BEST PRACTICES FOR TESTING:
============================

1. RUN ONLY ONE CELERY WORKER
   cd backend
   celery -A oxidane worker -l info -P solo
   
   Note: -P solo = single process (saves connections)

2. RUN CELERY BEAT SEPARATELY (if needed)
   celery -A oxidane beat -l info

3. STOP CELERY WHEN NOT TESTING
   powershell -ExecutionPolicy Bypass -File kill_celery.ps1

4. CHECK CURRENT CONNECTIONS
   python manage.py shell -c "from django_redis import get_redis_connection; r = get_redis_connection(); print(f'Connected clients: {r.client_list()}')"

5. MONITOR REDIS USAGE
   - Redis Cloud dashboard shows live connection count
   - Keep it under 25 to have buffer

WHEN TO USE CELERY:
===================
✓ Testing payments (need activation)
✓ Testing emails
✓ Testing Telegram group management
✓ Testing subscription renewals

WHEN TO STOP CELERY:
====================
✓ When just testing frontend
✓ When browsing dashboard/subscriptions
✓ When not actively testing payments
✓ Overnight/when not coding

CONNECTION ERRORS TO WATCH FOR:
================================
- "Redis connection refused"
- "Too many connections"
- "Max clients reached"
- Tasks stuck in "pending"

If you see these: Run kill_celery.ps1 and restart with single worker

PRODUCTION TIPS:
================
For production (when you upgrade Redis):
- Use Redis Standard/Premium (unlimited connections)
- Or use separate Redis instances (broker + cache)
- Or switch to RabbitMQ for Celery broker
"""

print(__doc__)
