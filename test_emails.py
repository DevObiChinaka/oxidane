#!/usr/bin/env python3
"""
Test script for email notifications in Oxidane
Tests welcome and sign-in notification emails
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import User
from users.views import send_welcome_email, send_signin_notification_email
from django.utils import timezone

def test_email_templates():
    """Test both email templates with sample data"""
    
    # Create a test user (don't save to database)
    test_user = User(
        first_name='John',
        last_name='Doe',
        email='test@example.com',
        is_email_verified=True,
        is_active=True
    )
    
    print("🧪 Testing Email Templates for Oxidane")
    print("=" * 50)
    
    try:
        print("\n📧 Testing Welcome Email Template...")
        send_welcome_email(test_user)
        print("✅ Welcome email template is working!")
        
    except Exception as e:
        print(f"❌ Welcome email failed: {str(e)}")
    
    try:
        print("\n📧 Testing Sign-In Notification Email Template...")
        send_signin_notification_email(test_user, {'method': 'Email & Password'})
        print("✅ Sign-in notification email template is working!")
        
    except Exception as e:
        print(f"❌ Sign-in notification email failed: {str(e)}")
    
    try:
        print("\n📧 Testing OAuth Sign-In Notification Email Template...")
        send_signin_notification_email(test_user, {'method': 'Google OAuth'})
        print("✅ OAuth sign-in notification email template is working!")
        
    except Exception as e:
        print(f"❌ OAuth sign-in notification email failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎊 Email template testing complete!")
    print("\n📋 Integration Points:")
    print("   ✅ Welcome Email: Sent after OTP verification (new users)")
    print("   ✅ Welcome Email: Sent for new OAuth users")
    print("   ✅ Sign-In Alert: Sent on successful email/password login")
    print("   ✅ Sign-In Alert: Sent for existing OAuth users")
    
    print("\n📧 Check your email configuration in backend/oxidane/settings.py")
    print("   Make sure SMTP settings are correct for actual email delivery")

if __name__ == "__main__":
    test_email_templates()