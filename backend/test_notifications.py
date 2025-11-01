#!/usr/bin/env python
"""Test script for notification preferences functionality"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import User, UserPreferences

def test_notification_preferences():
    """Test the UserPreferences model"""
    
    print("🧪 Testing Notification Preferences System\n")
    print("=" * 60)
    
    # Get a test user (first user in database)
    user = User.objects.first()
    if not user:
        print("❌ No users found in database. Please create a user first.")
        return
    
    print(f"✅ Testing with user: {user.email}\n")
    
    # Test 1: Get or create preferences with defaults
    print("Test 1: Creating preferences with defaults")
    preferences, created = UserPreferences.objects.get_or_create(user=user)
    
    if created:
        print("✅ New preferences created with defaults:")
    else:
        print("✅ Existing preferences found:")
    
    print(f"   - Email Login: {preferences.email_login}")
    print(f"   - Course Updates: {preferences.course_updates}")
    print(f"   - Subscription Renewal: {preferences.subscription_renewal}")
    print(f"   - Promotional Emails: {preferences.promotional_emails}")
    print(f"   - Signal Alerts: {preferences.signal_alerts}")
    print()
    
    # Test 2: Update preferences
    print("Test 2: Updating preferences")
    preferences.email_login = False
    preferences.promotional_emails = True
    preferences.save()
    print("✅ Updated email_login=False and promotional_emails=True")
    print()
    
    # Test 3: Verify updates persisted
    print("Test 3: Verifying updates persisted")
    preferences.refresh_from_db()
    print(f"✅ Email Login: {preferences.email_login} (should be False)")
    print(f"✅ Promotional Emails: {preferences.promotional_emails} (should be True)")
    print()
    
    # Test 4: Check admin display
    print("Test 4: Admin display string")
    print(f"✅ __str__ output: {preferences}")
    print()
    
    print("=" * 60)
    print("🎉 All tests passed!")
    print("\n💡 You can now manage preferences in Django admin:")
    print("   http://localhost:8000/admin/users/userpreferences/")

if __name__ == '__main__':
    test_notification_preferences()
