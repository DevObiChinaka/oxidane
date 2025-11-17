"""
Simple Telegram polling script
Runs process_telegram_updates task every 10 seconds
Use this as a workaround when Celery Beat isn't working
"""
import os
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import process_telegram_updates

print("🤖 Starting Telegram polling service...")
print("📡 Will check for new messages every 10 seconds")
print("Press Ctrl+C to stop\n")

try:
    while True:
        try:
            # Queue the task asynchronously
            result = process_telegram_updates.delay()
            print(f"✅ Task queued: {result.id}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait 10 seconds before next poll
        time.sleep(10)
except KeyboardInterrupt:
    print("\n\n👋 Telegram polling stopped")
