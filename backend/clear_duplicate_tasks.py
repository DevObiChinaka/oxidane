#!/usr/bin/env python
"""
Clear specific queued Celery tasks from Redis
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

try:
    from celery.result import AsyncResult
    from oxidane.celery import app

    # Task IDs to revoke
    task_ids = [
        '9ec915c4-98ef-449d-86f3-fd3e996dee72',  # First queued task
        '38bb34d3-e862-4c09-a848-ec054b4ec80d',  # Second queued task
    ]

    print("\n=== Revoking Queued Tasks ===\n")

    for task_id in task_ids:
        try:
            result = AsyncResult(task_id, app=app)
            print(f"Task ID: {task_id}")
            print(f"  State: {result.state}")
            
            # Revoke the task (terminate=True kills it if running, otherwise just removes from queue)
            result.revoke(terminate=True)
            print(f"  ✅ Revoked\n")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()

    print("✅ Cleared first 2 queued tasks")
    print("The latest task (a2b8cab2-843d-4c4c-bb5c-6b1119ae1263) will still be processed")

except Exception as e:
    print(f"Fatal error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
