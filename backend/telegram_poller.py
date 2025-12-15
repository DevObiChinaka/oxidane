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
            # Run the task directly (synchronously) - no Redis needed
            # This is fine since we have a dedicated poller process
            result = process_telegram_updates()
            if result:
                print(f"✅ Processed updates: {result}")
            else:
                print("✓ No new messages")
        except Exception as e:
            print(f"❌ Error: {e}")
            # On error, wait a bit longer before retrying
            time.sleep(5)
        
        # Wait 10 seconds before next poll
        time.sleep(10)
except KeyboardInterrupt:
    print("\n\n👋 Telegram polling stopped")
