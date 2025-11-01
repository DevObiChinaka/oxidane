#!/usr/bin/env python3
"""
Gmail App Password Setup and Email Test for Oxidane
Step-by-step guide to get real email sending working
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def check_current_credentials():
    """Check current email credentials in .env file"""
    
    env_file = Path('backend/.env')
    if not env_file.exists():
        print("❌ .env file not found in backend/")
        return None, None
    
    print("📁 Reading current credentials from backend/.env...")
    env_content = env_file.read_text()
    
    email_user = None
    email_password = None
    
    for line in env_content.split('\n'):
        if line.startswith('EMAIL_HOST_USER='):
            email_user = line.split('=', 1)[1].strip()
            print(f"   📧 EMAIL_HOST_USER: {email_user}")
        elif line.startswith('EMAIL_HOST_PASSWORD='):
            email_password = line.split('=', 1)[1].strip()
            print(f"   🔑 EMAIL_HOST_PASSWORD: {'***' + email_password[-4:] if email_password else 'NOT SET'}")
    
    return email_user, email_password

def test_gmail_connection(email_user, email_password):
    """Test Gmail SMTP connection with different configurations"""
    
    print(f"\n🔗 Testing Gmail SMTP connection for: {email_user}")
    
    # Test configurations to try
    test_configs = [
        {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "name": "TLS (587)"},
        {"host": "smtp.gmail.com", "port": 465, "use_ssl": True, "name": "SSL (465)"},
        {"host": "smtp.gmail.com", "port": 25, "use_tls": True, "name": "TLS (25)"},
    ]
    
    for config in test_configs:
        try:
            print(f"\n🧪 Trying {config['name']}...")
            
            if config.get('use_ssl'):
                # SSL connection
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['host'], config['port'], context=context)
            else:
                # TLS connection
                server = smtplib.SMTP(config['host'], config['port'])
                if config.get('use_tls'):
                    server.starttls()
            
            print("   🔐 Attempting authentication...")
            server.login(email_user, email_password)
            
            print(f"   ✅ SUCCESS with {config['name']}!")
            server.quit()
            return config
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
            if "Application-specific password required" in str(e):
                print("   💡 You need to use an App Password, not your regular Gmail password!")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
    
    return None

def send_test_email(email_user, email_password, config):
    """Send a test email using the working configuration"""
    
    try:
        print(f"\n📤 Sending test email using {config['name']}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f'OxY Fx <{email_user}>'
        msg['To'] = email_user  # Send to self
        msg['Subject'] = '🧪 OxY Fx Email Test - Success!'
        
        body = f"""
🎉 SUCCESS! Your OxY Fx email configuration is working!

✅ SMTP Configuration:
   • Host: {config['host']}
   • Port: {config['port']}
   • Security: {config['name']}
   • From: {email_user}

🚀 Your registration emails will now be delivered successfully!

This test email was sent from your Oxidane application.

© 2025 Oxidane Forex Academy
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        if config.get('use_ssl'):
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(config['host'], config['port'], context=context)
        else:
            server = smtplib.SMTP(config['host'], config['port'])
            if config.get('use_tls'):
                server.starttls()
        
        server.login(email_user, email_password)
        server.sendmail(email_user, email_user, msg.as_string())
        server.quit()
        
        print("   ✅ Test email sent successfully!")
        print(f"   📬 Check your inbox: {email_user}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to send test email: {e}")
        return False

def setup_app_password_guide():
    """Show step-by-step Gmail App Password setup"""
    
    print("\n" + "="*60)
    print("🔐 GMAIL APP PASSWORD SETUP GUIDE")
    print("="*60)
    
    print("\n📋 Follow these exact steps:")
    
    print("\n1. 🌐 Go to Google Account Settings:")
    print("   https://myaccount.google.com/")
    
    print("\n2. 🔒 Enable 2-Step Verification:")
    print("   • Click 'Security' in left sidebar")
    print("   • Find '2-Step Verification' section")
    print("   • Click 'Turn on' if not already enabled")
    print("   • Follow the setup process")
    
    print("\n3. 🔑 Generate App Password:")
    print("   • Still in 'Security' section")
    print("   • Find 'App passwords' (only appears after 2-FA is enabled)")
    print("   • Click 'App passwords'")
    print("   • Select app: 'Mail'")
    print("   • Select device: 'Other (custom name)'")
    print("   • Enter name: 'OxY Fx Django'")
    print("   • Click 'Generate'")
    
    print("\n4. 📝 Copy the App Password:")
    print("   • Google will show a 16-character password like: 'abcd efgh ijkl mnop'")
    print("   • Copy this EXACTLY (spaces don't matter)")
    print("   • This replaces your regular Gmail password")
    
    print("\n5. 🔄 Update your .env file:")
    print("   • Open: backend/.env")
    print("   • Update: EMAIL_HOST_PASSWORD=your-16-char-app-password")
    print("   • Save the file")
    
    print("\n6. 🚀 Restart Django:")
    print("   • Stop Django server (Ctrl+C)")
    print("   • Run: python manage.py runserver")
    print("   • Test registration again")
    
    print("\n" + "="*60)

def main():
    """Main email setup and test function"""
    
    print("🚀 REAL EMAIL SETUP FOR OXIDANE")
    print("="*40)
    
    # Check current credentials
    email_user, email_password = check_current_credentials()
    
    if not email_user or not email_password:
        print("\n❌ Email credentials not configured properly")
        setup_app_password_guide()
        return
    
    # Test connection
    working_config = test_gmail_connection(email_user, email_password)
    
    if working_config:
        print(f"\n🎉 SMTP CONNECTION SUCCESSFUL!")
        
        # Send test email
        if send_test_email(email_user, email_password, working_config):
            print("\n✅ REAL EMAIL SENDING IS WORKING!")
            print("   Your registration emails will now be delivered to users' inboxes.")
            
            print("\n🔄 Update Django settings.py if needed:")
            if working_config['port'] != 587:
                print(f"   EMAIL_PORT = {working_config['port']}")
            if working_config.get('use_ssl'):
                print("   EMAIL_USE_SSL = True")
                print("   EMAIL_USE_TLS = False")
        else:
            print("\n⚠️  SMTP works but email sending failed")
    
    else:
        print("\n❌ SMTP CONNECTION FAILED")
        print("\n🔍 Most likely causes:")
        print("   1. Using regular Gmail password instead of App Password")
        print("   2. 2-Factor Authentication not enabled")
        print("   3. App Password not generated correctly")
        print("   4. Network/firewall still blocking")
        
        setup_app_password_guide()
        
        print("\n💡 Alternative solutions:")
        print("   • Try mobile hotspot (bypass network restrictions)")
        print("   • Use different email provider (Outlook, Yahoo)")
        print("   • Use email service (SendGrid, Mailgun)")

if __name__ == "__main__":
    main()