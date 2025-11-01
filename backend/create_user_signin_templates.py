#!/usr/bin/env python
"""
Create simple email templates for user sign-in verification and notification
Clean, minimal design focusing on functionality
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

def create_user_signin_templates():
    """Create clean, simple user signin templates"""
    
    # 1. User Login OTP Verification Template
    user_login_otp_template, created = EmailTemplate.objects.get_or_create(
        template_type='user_login_otp',
        name='User Login OTP Verification',
        defaults={
            'subject_template': 'Sign-In Verification Code - {{company_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sign-In Verification - {{company_name}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{{company_name}}</h1>
        <p style="color: #e0e0e0; margin: 8px 0 0 0; font-size: 14px;">Sign-In Verification</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #000856; margin-top: 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Please use this verification code to complete your sign-in:
        </p>

        <!-- OTP Code -->
        <div style="background: #f5f5f5; border: 2px solid #00B38F; border-radius: 8px; padding: 25px; text-align: center; margin: 30px 0;">
            <div style="font-size: 36px; font-weight: bold; color: #000856; letter-spacing: 8px; font-family: 'Courier New', monospace;">{{otp_code}}</div>
            <p style="color: #666; font-size: 13px; margin: 10px 0 0 0;">Valid for 10 minutes</p>
        </div>

        <p style="font-size: 14px; color: #666; margin: 25px 0 10px 0;">
            <strong>Security tips:</strong>
        </p>
        <ul style="font-size: 14px; color: #666; margin: 0; padding-left: 20px;">
            <li>Never share this code with anyone</li>
            <li>Our team will never ask for your verification code</li>
            <li>If you didn't request this, please secure your account</li>
        </ul>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="font-size: 13px; color: #999; margin: 0;">
            <strong>Sign-in details:</strong><br>
            Time: {{login_time}}<br>
            IP Address: {{login_ip}}
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
        <p style="margin: 5px 0;">This is an automated security message.</p>
    </div>
</body>
</html>
            ''',
            'text_content': '''
Sign-In Verification Code - {{company_name}}

Hi {{user.first_name}},

Please use this verification code to complete your sign-in:

{{otp_code}}

This code is valid for 10 minutes.

Security tips:
• Never share this code with anyone
• Our team will never ask for your verification code
• If you didn't request this, please secure your account

Sign-in details:
Time: {{login_time}}
IP Address: {{login_ip}}

© {{current_year}} {{company_name}}
This is an automated security message.
            ''',
            'description': 'Simple OTP verification email sent when users log in',
            'status': 'active',
            'is_default': True,
            'available_variables': {
                'user.first_name': 'User first name',
                'user.email': 'User email address',
                'otp_code': 'Six-digit verification code',
                'login_time': 'Login attempt timestamp',
                'login_ip': 'IP address of login attempt',
                'company_name': 'Company name',
                'current_year': 'Current year',
            }
        }
    )
    
    if created:
        print("✅ Created: User Login OTP Verification template")
    else:
        print("ℹ️  Updated: User Login OTP Verification template")

    # 2. User Sign-In Notification Template
    user_signin_notification_template, created = EmailTemplate.objects.get_or_create(
        template_type='user_signin_notification',
        name='User Sign-In Notification',
        defaults={
            'subject_template': 'New Sign-In to Your Account - {{company_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sign-In Notification - {{company_name}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{{company_name}}</h1>
        <p style="color: #e0e0e0; margin: 8px 0 0 0; font-size: 14px;">Account Sign-In Notification</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #000856; margin-top: 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Your account was successfully accessed.
        </p>

        <!-- Sign-in Details Box -->
        <div style="background: #f8f9fa; border-left: 4px solid #00B38F; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: #333;"><strong>Sign-in details:</strong></p>
            <table style="width: 100%; font-size: 14px; color: #555;">
                <tr>
                    <td style="padding: 5px 0; width: 100px;"><strong>Time:</strong></td>
                    <td style="padding: 5px 0;">{{login_time}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Method:</strong></td>
                    <td style="padding: 5px 0;">{{signin_method}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Email:</strong></td>
                    <td style="padding: 5px 0;">{{user.email}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>IP Address:</strong></td>
                    <td style="padding: 5px 0;">{{login_ip}}</td>
                </tr>
            </table>
        </div>

        <!-- Success Message -->
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px; color: #155724;">
                <strong>✓ Secure Access</strong><br>
                If this was you, no action is needed.
            </p>
        </div>

        <!-- Warning Message -->
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px; color: #856404;">
                <strong>⚠ Didn't sign in?</strong><br>
                If this wasn't you, please immediately:
            </p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px; font-size: 14px; color: #856404;">
                <li>Change your password</li>
                <li>Contact support: {{support_email}}</li>
                <li>Review your account security</li>
            </ul>
        </div>

        <!-- Dashboard Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{dashboard_url}}" style="background: #00B38F; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">
                View Dashboard
            </a>
        </div>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
        <p style="margin: 5px 0;">This is an automated security notification.</p>
    </div>
</body>
</html>
            ''',
            'text_content': '''
New Sign-In to Your Account - {{company_name}}

Hi {{user.first_name}},

Your account was successfully accessed.

Sign-in details:
• Time: {{login_time}}
• Method: {{signin_method}}
• Email: {{user.email}}
• IP Address: {{login_ip}}

✓ If this was you, no action is needed.

⚠ Didn't sign in?
If this wasn't you, please immediately:
• Change your password
• Contact support: {{support_email}}
• Review your account security

Dashboard: {{dashboard_url}}

© {{current_year}} {{company_name}}
This is an automated security notification.
            ''',
            'description': 'Simple notification email sent after successful user sign-in',
            'status': 'active',
            'is_default': True,
            'available_variables': {
                'user.first_name': 'User first name',
                'user.email': 'User email address',
                'login_time': 'Sign-in timestamp',
                'login_ip': 'IP address of sign-in',
                'signin_method': 'Sign-in method used',
                'dashboard_url': 'Dashboard URL',
                'support_email': 'Support email address',
                'company_name': 'Company name',
                'current_year': 'Current year',
            }
        }
    )
    
    if created:
        print("✅ Created: User Sign-In Notification template")
    else:
        print("ℹ️  Updated: User Sign-In Notification template")

    print("\n" + "="*60)
    print("✨ User Sign-In Email Templates Setup Complete!")
    print("="*60)
    print("\nTemplates created:")
    print("1. User Login OTP Verification (user_login_otp)")
    print("2. User Sign-In Notification (user_signin_notification)")
    print("\nThese templates use minimal design and can be managed via admin panel.")

if __name__ == '__main__':
    create_user_signin_templates()
