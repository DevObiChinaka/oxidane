import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.core.cache import cache
from subscriptions.models import TelegramConfiguration
import requests

print("="*60)
print("TELEGRAM POLLING DIAGNOSTICS")
print(f"Time: {datetime.now()}")
print("="*60)

# Check bot token
config = TelegramConfiguration.get_instance()
if not config.has_valid_token():
    print("\n❌ No valid bot token configured!")
    sys.exit(1)

print("\n✅ Bot token: Configured")

# Get bot info
bot_token = config.decrypt_field('bot_token')
try:
    response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
    bot_info = response.json()
    if bot_info.get('ok'):
        print(f"✅ Bot username: @{bot_info['result']['username']}")
    else:
        print(f"❌ Bot API error: {bot_info}")
except Exception as e:
    print(f"❌ Failed to connect to Telegram: {e}")
    sys.exit(1)

# Check webhook status
try:
    response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10)
    webhook_info = response.json()
    if webhook_info.get('ok'):
        result = webhook_info['result']
        if result.get('url'):
            print(f"\n⚠️  WEBHOOK IS SET: {result['url']}")
            print("   This prevents polling from working!")
            print(f"   Pending updates: {result.get('pending_update_count', 0)}")
        else:
            print(f"\n✅ Webhook: Not set (polling mode active)")
            print(f"   Pending updates: {result.get('pending_update_count', 0)}")
except Exception as e:
    print(f"❌ Failed to check webhook: {e}")

# Check current offset
offset_key = 'telegram_update_offset'
current_offset = cache.get(offset_key, 0)
print(f"\n✅ Current offset: {current_offset}")

# Get recent updates
try:
    params = {'offset': current_offset, 'timeout': 5}
    response = requests.get(
        f"https://api.telegram.org/bot{bot_token}/getUpdates",
        params=params,
        timeout=10
    )
    updates_data = response.json()
    
    if updates_data.get('ok'):
        updates = updates_data['result']
        print(f"\n📬 Available updates: {len(updates)}")
        
        if updates:
            print("\nLast 5 updates:")
            for update in updates[-5:]:
                update_id = update.get('update_id')
                if 'message' in update:
                    msg = update['message']
                    text = msg.get('text', '')
                    username = msg.get('from', {}).get('username', 'Unknown')
                    print(f"  - Update {update_id}: @{username} sent: {text}")
                elif 'callback_query' in update:
                    print(f"  - Update {update_id}: Callback query")
                else:
                    print(f"  - Update {update_id}: {list(update.keys())}")
    else:
        print(f"❌ Get updates failed: {updates_data}")
        
except Exception as e:
    print(f"❌ Failed to get updates: {e}")

# Check Celery Beat schedule
print("\n" + "="*60)
print("CELERY CONFIGURATION")
print("="*60)

from oxidane.celery import app
beat_schedule = app.conf.beat_schedule

if 'process-telegram-updates' in beat_schedule:
    task_config = beat_schedule['process-telegram-updates']
    print(f"\n✅ Task scheduled: {task_config['task']}")
    print(f"   Interval: {task_config['schedule']} seconds")
else:
    print("\n❌ Telegram polling task NOT in schedule!")

print("\n" + "="*60)
