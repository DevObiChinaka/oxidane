import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.telegram_service import TelegramService

# Initialize service
ts = TelegramService()

# Get recent updates
print("Fetching recent Telegram updates...")
updates = ts.get_updates()

print(f"\nTotal updates received: {len(updates)}")
print("\n" + "="*60)

# Show last 5 updates
if updates:
    print("\nLast 5 updates:")
    for update in updates[-5:]:
        update_id = update.get('update_id')
        
        # Check for message
        if 'message' in update:
            msg = update['message']
            user = msg.get('from', {})
            text = msg.get('text', '')
            chat_id = msg.get('chat', {}).get('id')
            date = msg.get('date')
            
            print(f"\nUpdate ID: {update_id}")
            print(f"From: {user.get('first_name')} {user.get('last_name', '')} (@{user.get('username', 'N/A')})")
            print(f"User ID: {user.get('id')}")
            print(f"Chat ID: {chat_id}")
            print(f"Message: {text}")
            print(f"Date: {date}")
        
        # Check for callback query
        elif 'callback_query' in update:
            cb = update['callback_query']
            user = cb.get('from', {})
            data = cb.get('data')
            
            print(f"\nUpdate ID: {update_id}")
            print(f"Callback from: {user.get('first_name')} (@{user.get('username', 'N/A')})")
            print(f"Data: {data}")
else:
    print("\nNo updates found!")

print("\n" + "="*60)
