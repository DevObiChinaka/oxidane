#!/usr/bin/env python3
"""
Email Configuration Troubleshooter for Oxidane
Diagnoses and fixes email delivery issues
"""

import os
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import django
from pathlib import Path

# Add backend to path and setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')

def test_smtp_connection():
    """Test direct SMTP connection without Django"""
    
    # Read credentials from .env file
    env_file = Path('backend/.env')
    if not env_file.exists():
        print("❌ .env file not found in backend/")
        return False
    
    env_content = env_file.read_text()
    email_user = None
    email_password = None
    
    for line in env_content.split('\n'):
        if line.startswith('EMAIL_HOST_USER='):
            email_user = line.split('=', 1)[1].strip()
        elif line.startswith('EMAIL_HOST_PASSWORD='):
            email_password = line.split('=', 1)[1].strip()
    
    if not email_user or not email_password:
        print("❌ Email credentials not found in .env file")
        return False
    
    print(f"📧 Testing SMTP connection for: {email_user}")
    
    try:
        # Test Gmail SMTP connection
        print("🔗 Connecting to Gmail SMTP server...")
        
        # Create SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS encryption
        
        print("🔐 Attempting login...")
        server.login(email_user, email_password)
        
        print("✅ SMTP connection successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Common fixes:")
        print("   1. Enable 2-Factor Authentication in Google Account")
        print("   2. Generate App Password (not regular password)")
        print("   3. Use App Password in EMAIL_HOST_PASSWORD")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Possible issues:")
        print("   1. Firewall blocking port 587")
        print("   2. Network connectivity issues")
        print("   3. Gmail SMTP temporarily unavailable")
        return False

def test_django_email():
    """Test Django email configuration"""
    
    try:
        django.setup()
        from django.core.mail import send_mail
        from django.conf import settings
        
        print("\n📧 Testing Django email configuration...")
        
        # Check Django settings
        print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"   EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
        
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("❌ Django email credentials not configured")
            return False
        
        # Try sending test email
        print("📤 Sending test email...")
        
        send_mail(
            subject='🧪 OxY Fx Email Test',
            message='This is a test email from your Oxidane application.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to self
            fail_silently=False,
        )
        
        print("✅ Django email test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Django email test failed: {e}")
        return False

def suggest_fixes():
    """Suggest common fixes for email issues"""
    
    print("\n🔧 EMAIL TROUBLESHOOTING GUIDE:")
    print("=" * 50)
    
    print("\n1. 🔐 GMAIL APP PASSWORD SETUP:")
    print("   a. Go to https://myaccount.google.com/")
    print("   b. Security → 2-Step Verification → Enable it")
    print("   c. Security → App passwords → Generate new")
    print("   d. Select 'Mail' and copy the 16-character password")
    print("   e. Use this in EMAIL_HOST_PASSWORD (not your Gmail password)")
    
    print("\n2. 🌐 NETWORK/FIREWALL ISSUES:")
    print("   a. Check if port 587 is blocked by firewall")
    print("   b. Try different network (mobile hotspot)")
    print("   c. Check antivirus SMTP blocking")
    
    print("\n3. 🔄 ALTERNATIVE EMAIL BACKENDS:")
    print("   a. For development testing:")
    print("      EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
    print("   b. For file-based testing:")
    print("      EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'")
    
    print("\n4. 📧 ALTERNATIVE EMAIL SERVICES:")
    print("   a. SendGrid (free tier available)")
    print("   b. Mailgun (free tier available)")  
    print("   c. Amazon SES (pay-per-use)")

def main():
    """Main troubleshooting function"""
    
    print("🔍 OXIDANE EMAIL TROUBLESHOOTER")
    print("=" * 40)
    
    # Test direct SMTP connection
    smtp_works = test_smtp_connection()
    
    if smtp_works:
        # Test Django integration
        django_works = test_django_email()
        
        if django_works:
            print("\n🎉 EMAIL SYSTEM FULLY WORKING!")
            print("   Your registration emails should now be delivered.")
        else:
            print("\n⚠️  SMTP works but Django config has issues")
            suggest_fixes()
    else:
        print("\n❌ SMTP CONNECTION FAILED")
        suggest_fixes()
    
    print(f"\n💡 QUICK FIX FOR DEVELOPMENT:")
    print("   Add this to backend/oxidane/settings.py for console output:")
    print("   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")

if __name__ == "__main__":
    main()