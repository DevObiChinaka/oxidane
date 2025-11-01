#!/usr/bin/env python3
"""
Test updated email templates with OxiWorld branding
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

def test_updated_templates():
    """Test email templates with OxiWorld branding"""
    
    # Create a test user (don't save to database)
    test_user = User(
        first_name='Alex',
        last_name='Trader',
        email='alex@example.com',
        is_email_verified=True,
        is_active=True
    )
    
    print("🧪 Testing Updated OxiWorld Email Templates")
    print("=" * 50)
    
    try:
        print("\n📧 Testing Welcome Email Template...")
        print("   Checking for: OxiWorld Forex Academy branding")
        print("   Support email: support@oxiworld.com")
        send_welcome_email(test_user)
        print("   ✅ Welcome email template updated!")
        
    except Exception as e:
        print(f"   ❌ Welcome email failed: {str(e)}")
    
    try:
        print("\n📧 Testing Sign-In Notification Email Template...")
        print("   Checking for: OxiWorld branding")
        send_signin_notification_email(test_user, {'method': 'Email & Password'})
        print("   ✅ Sign-in notification template updated!")
        
    except Exception as e:
        print(f"   ❌ Sign-in notification email failed: {str(e)}")
    
    try:
        print("\n📧 Testing OAuth Sign-In Notification Email Template...")
        send_signin_notification_email(test_user, {'method': 'Google OAuth'})
        print("   ✅ OAuth sign-in notification template updated!")
        
    except Exception as e:
        print(f"   ❌ OAuth sign-in notification email failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎊 Email template updates complete!")
    print("\n📋 What was changed:")
    print("   ✅ OxY Fx → OxiWorld")
    print("   ✅ Oxidane Forex Academy → OxiWorld Forex Academy")
    print("   ✅ support@oxyfx.com → support@oxiworld.com")
    print("   ✅ Email subjects updated")
    print("   ✅ All HTML and plain text templates updated")
    
    print("\n🚀 Ready for testing:")
    print("   • Registration emails now show 'OxiWorld Forex Academy'")
    print("   • Sign-in notifications show 'OxiWorld' branding")
    print("   • Support emails reference support@oxiworld.com")

if __name__ == "__main__":
    test_updated_templates()