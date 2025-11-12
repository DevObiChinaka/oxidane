"""
Test Telegram Polling System (No Webhooks)

This script manually triggers the Telegram update processor to test
the verification flow without needing Celery Beat running.

Usage:
    python test_telegram_polling.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.tasks import process_telegram_updates
from subscriptions.models import BillingProfile, TelegramConfiguration, User
from django.utils import timezone


def test_polling_system():
    """Test the Telegram polling verification system"""
    
    print("=" * 70)
    print("TELEGRAM POLLING VERIFICATION TEST")
    print("=" * 70)
    
    # 1. Check bot configuration
    print("\n1️⃣  Checking bot configuration...")
    config = TelegramConfiguration.get_instance()
    
    if not config.has_valid_token():
        print("   ❌ Bot token not configured!")
        print("   Please configure bot in admin panel first.")
        return
    
    print(f"   ✅ Bot configured: {config.bot_username}")
    
    # 2. Create test user and billing profile
    print("\n2️⃣  Creating test user...")
    user, created = User.objects.get_or_create(
        email='test_polling@example.com',
        defaults={'username': 'test_polling_user'}
    )
    
    billing_profile, created = BillingProfile.objects.get_or_create(user=user)
    
    # Reset verification status for testing
    billing_profile.telegram_verified = False
    billing_profile.save()
    
    print(f"   ✅ User: {user.email}")
    
    # 3. Generate verification code
    print("\n3️⃣  Generating verification code...")
    code = billing_profile.generate_verification_code()
    
    print(f"   ✅ Code: {code}")
    print(f"   ⏰ Expires: {billing_profile.verification_code_expires_at}")
    print(f"   🕒 Valid for: 5 minutes")
    
    # 4. Show instructions
    bot_username = config.bot_username.replace('@', '')
    deep_link = f'https://t.me/{bot_username}?start=VERIFY_{code}'
    
    print("\n4️⃣  Verification Instructions:")
    print("   " + "=" * 66)
    print(f"   📱 OPTION A: Click this link on your phone")
    print(f"      {deep_link}")
    print()
    print(f"   💬 OPTION B: Open @{config.bot_username} and type:")
    print(f"      {code}")
    print("   " + "=" * 66)
    
    # 5. Start polling
    print("\n5️⃣  Starting polling for updates...")
    print("   Press Ctrl+C to stop\n")
    
    import time
    poll_count = 0
    
    try:
        while not billing_profile.telegram_verified:
            poll_count += 1
            print(f"   [{poll_count}] Polling for updates...", end=' ')
            
            # Call the polling task
            result = process_telegram_updates()
            
            if result.get('success'):
                processed = result.get('processed', 0)
                if processed > 0:
                    print(f"✅ Processed {processed} update(s)")
                else:
                    print("⏳ No updates")
            else:
                print(f"❌ {result.get('message', 'Error')}")
            
            # Refresh billing profile from database
            billing_profile.refresh_from_db()
            
            if billing_profile.telegram_verified:
                print("\n" + "=" * 70)
                print("🎉 VERIFICATION SUCCESSFUL!")
                print("=" * 70)
                print(f"   User: {user.email}")
                print(f"   Telegram ID: {billing_profile.telegram_user_id}")
                print(f"   Telegram Username: @{billing_profile.telegram_username}")
                print("=" * 70)
                break
            
            # Wait 5 seconds before next poll
            time.sleep(5)
            
            # Safety timeout after 5 minutes (60 polls)
            if poll_count >= 60:
                print("\n⏱️  Timeout: Code expired after 5 minutes")
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Polling stopped by user")
        print(f"   Polled {poll_count} times")
        
        # Check final status
        billing_profile.refresh_from_db()
        if billing_profile.telegram_verified:
            print("   ✅ Verified!")
        else:
            print("   ❌ Not verified yet")


def test_direct_api_call():
    """Test direct Telegram API call to verify bot works"""
    
    print("\n" + "=" * 70)
    print("TESTING DIRECT TELEGRAM API CONNECTION")
    print("=" * 70)
    
    config = TelegramConfiguration.get_instance()
    
    if not config.has_valid_token():
        print("❌ Bot not configured")
        return
    
    try:
        import requests
        bot_token = config.decrypt_field('bot_token')
        
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print("✅ Bot API Connection Successful!")
                print(f"   ID: {bot_info.get('id')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   Name: {bot_info.get('first_name')}")
                print(f"   Can join groups: {bot_info.get('can_join_groups')}")
                return True
            else:
                print(f"❌ API Error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


if __name__ == '__main__':
    # First test API connection
    if not test_direct_api_call():
        print("\n⚠️  Fix bot configuration before testing polling")
        sys.exit(1)
    
    # Then test polling
    test_polling_system()
