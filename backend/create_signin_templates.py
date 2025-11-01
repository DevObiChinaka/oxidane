#!/usr/bin/env python
"""
Create signin notification email templates that match existing style
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

def create_matching_signin_templates():
    """Create signin notification templates matching existing style"""
    
    # Admin OTP Login Template (matches existing style)
    admin_otp_template, created = EmailTemplate.objects.get_or_create(
        template_type='signin_notification',
        name='Admin Login OTP - Security Alert',
        defaults={
            'subject_template': '🔐 Admin Login OTP - {{company_name}} Security',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Login OTP - {{company_name}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">🔐 Admin Login Verification</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">{{company_name}} Admin Portal Security</p>
    </div>

    <div style="background: white; padding: 40px 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0; font-size: 24px; font-weight: 600;">Hello {{user.first_name}},</h2>
        
        <p style="font-size: 16px; margin-bottom: 25px;">
            A login request has been made for your admin account. Please use the verification code below to complete the login:
        </p>

        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border: 3px solid #dc3545; border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0;">
            <div style="font-size: 40px; font-weight: 800; color: #dc3545; letter-spacing: 8px; margin-bottom: 10px;">{{otp_code}}</div>
            <p style="color: #666; font-size: 14px; margin: 0;"><strong>⏰ Expires in 10 minutes</strong></p>
        </div>

        <div style="background: #fff3cd; border-left: 5px solid #ffc107; padding: 20px; margin: 30px 0; border-radius: 8px;">
            <h3 style="color: #856404; margin-top: 0; font-size: 18px;">🛡️ Security Alert</h3>
            <ul style="color: #856404; margin: 0; padding-left: 20px;">
                <li>Login attempt at: <strong>{{login_time}}</strong></li>
                <li>From IP address: <strong>{{login_ip}}</strong></li>
                <li>If this wasn't you, change your password immediately</li>
                <li>Never share your OTP with anyone</li>
            </ul>
        </div>
    </div>

    <div style="background: #343a40; padding: 30px; border-radius: 15px; text-align: center; color: white;">
        <p style="margin: 0; font-size: 12px; opacity: 0.8;">Questions? Contact us at {{support_email}} | © {{current_year}} {{company_name}}</p>
    </div>
</body>
</html>
            ''',
            'text_content': '''
🔐 Admin Login OTP - {{company_name}} Security

Hello {{user.first_name}},

A login request has been made for your admin account. 

Your verification code is: {{otp_code}}

⏰ This code expires in 10 minutes.

🛡️ Security Alert:
- Login attempt at: {{login_time}}
- From IP address: {{login_ip}}
- If this wasn't you, change your password immediately
- Never share your OTP with anyone

This is an automated security notification from {{company_name}}.
Questions? Contact us at {{support_email}}

© {{current_year}} {{company_name}}
            ''',
            'description': 'Professional OTP email sent for admin login verification with security details',
            'status': 'active',
            'is_default': True,
            'available_variables': {
                'user.first_name': 'Admin first name',
                'user.email': 'Admin email address',
                'otp_code': 'Six-digit verification code',
                'login_time': 'Formatted time of login attempt',
                'login_ip': 'IP address of login attempt',
                'company_name': 'Company name (OxiWorld)',
                'support_email': 'Support contact email',
                'current_year': 'Current year'
            }
        }
    )

    # Admin Successful Login Template
    admin_success_template, created2 = EmailTemplate.objects.get_or_create(
        template_type='signin_notification',
        name='Admin Login Success - Welcome Back',
        defaults={
            'subject_template': '✅ Admin Login Successful - Welcome Back to {{company_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Login Success - {{company_name}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">✅ Welcome Back!</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">{{company_name}} Admin Portal</p>
    </div>

    <div style="background: white; padding: 40px 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0; font-size: 24px; font-weight: 600;">Hello {{user.first_name}},</h2>
        
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border: 2px solid #28a745; border-radius: 12px; padding: 25px; text-align: center; margin: 30px 0;">
            <h3 style="color: #155724; margin: 0 0 10px 0; font-size: 20px;">🎉 Login Successful!</h3>
            <p style="color: #155724; margin: 0; font-size: 14px;">Session started at {{login_time}}</p>
        </div>

        <div style="background: #f8f9fa; border-radius: 10px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #333; margin-top: 0; font-size: 18px;">📊 Session Details</h3>
            <div style="display: grid; gap: 10px;">
                <div><strong>Account:</strong> {{user.email}}</div>
                <div><strong>Login Time:</strong> {{login_time}}</div>
                <div><strong>IP Address:</strong> {{login_ip}}</div>
                <div><strong>Session Duration:</strong> 24 hours</div>
            </div>
        </div>

        <div style="background: #e3f2fd; border-left: 5px solid #2196f3; padding: 20px; margin: 25px 0; border-radius: 8px;">
            <h3 style="color: #1565c0; margin-top: 0; font-size: 16px;">🛡️ Security Reminders</h3>
            <ul style="color: #1565c0; margin: 0; padding-left: 20px; font-size: 14px;">
                <li>Always log out when finished</li>
                <li>Never share your admin credentials</li>
                <li>Report suspicious activity immediately</li>
            </ul>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <a href="{{admin_dashboard_url}}" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">
                Go to Admin Dashboard 🚀
            </a>
        </div>
    </div>

    <div style="background: #343a40; padding: 30px; border-radius: 15px; text-align: center; color: white;">
        <p style="margin: 0 0 10px 0; font-size: 14px;">If this wasn't you, secure your account at {{support_email}}</p>
        <p style="margin: 0; font-size: 12px; opacity: 0.8;">© {{current_year}} {{company_name}} - Automated Security Notification</p>
    </div>
</body>
</html>
            ''',
            'text_content': '''
✅ Admin Login Successful - Welcome Back to {{company_name}}

Hello {{user.first_name}},

🎉 Login Successful!
Session started at {{login_time}}

📊 Session Details:
- Account: {{user.email}}
- Login Time: {{login_time}}
- IP Address: {{login_ip}}  
- Session Duration: 24 hours

🛡️ Security Reminders:
- Always log out when finished
- Never share your admin credentials
- Report suspicious activity immediately

Admin Dashboard: {{admin_dashboard_url}}

If this wasn't you, secure your account at {{support_email}}

© {{current_year}} {{company_name}} - Automated Security Notification
            ''',
            'description': 'Welcoming email sent after successful admin login with session details',
            'status': 'active',
            'is_default': False,
            'available_variables': {
                'user.first_name': 'Admin first name',
                'user.email': 'Admin email address',
                'login_time': 'Formatted time of successful login',
                'login_ip': 'IP address of login',
                'admin_dashboard_url': 'URL to admin dashboard',
                'company_name': 'Company name (OxiWorld)',
                'support_email': 'Support contact email',
                'current_year': 'Current year'
            }
        }
    )

    print("✅ Signin notification templates created successfully!")
    print(f"📧 Admin OTP Template: {'Created' if created else 'Already exists'}")
    print(f"📧 Admin Success Template: {'Created' if created2 else 'Already exists'}")
    print("\n🎨 Templates match existing professional style!")
    
    # Show template count
    all_templates = EmailTemplate.objects.all().count()
    signin_templates = EmailTemplate.objects.filter(template_type='signin_notification').count()
    print(f"\n📈 Total templates: {all_templates}")
    print(f"🔐 Signin templates: {signin_templates}")
    
    return admin_otp_template, admin_success_template

if __name__ == "__main__":
    create_matching_signin_templates()