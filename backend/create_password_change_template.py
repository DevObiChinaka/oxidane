#!/usr/bin/env python
"""
Create password change notification email template
Clean design matching the signin notification style
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

def create_password_changed_template():
    """Create clean password change notification template"""
    
    template, created = EmailTemplate.objects.get_or_create(
        template_type='password_changed',
        name='Password Changed Notification',
        defaults={
            'subject_template': 'Password Changed - {{company_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Changed - {{company_name}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{{company_name}}</h1>
        <p style="color: #e0e0e0; margin: 8px 0 0 0; font-size: 14px;">Password Changed Notification</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #000856; margin-top: 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Your account password was successfully changed.
        </p>

        <!-- Change Details Box -->
        <div style="background: #f8f9fa; border-left: 4px solid #00B38F; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: #333;"><strong>Change details:</strong></p>
            <table style="width: 100%; font-size: 14px; color: #555;">
                <tr>
                    <td style="padding: 5px 0; width: 100px;"><strong>Time:</strong></td>
                    <td style="padding: 5px 0;">{{change_time}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Account:</strong></td>
                    <td style="padding: 5px 0;">{{user.email}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>IP Address:</strong></td>
                    <td style="padding: 5px 0;">{{change_ip}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Device:</strong></td>
                    <td style="padding: 5px 0;">{{device}}</td>
                </tr>
            </table>
        </div>

        <!-- Success Message -->
        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px; color: #155724;">
                <strong>✓ Password Updated</strong><br>
                If this was you, no action is needed. Your new password is now active.
            </p>
        </div>

        <!-- Security Warning -->
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px; color: #856404;">
                <strong>⚠ Didn't change your password?</strong><br>
                If you did not make this change, your account may be compromised. Please:
            </p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px; font-size: 14px; color: #856404;">
                <li>Reset your password immediately</li>
                <li>Review your account security</li>
                <li>Contact support: {{support_email}}</li>
            </ul>
        </div>

        <!-- Dashboard Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{dashboard_url}}" style="background: #00B38F; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">
                Go to Dashboard
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
Password Changed - {{company_name}}

Hi {{user.first_name}},

Your account password was successfully changed.

Change details:
Time: {{change_time}}
Account: {{user.email}}
IP Address: {{change_ip}}
Device: {{device}}

✓ Password Updated
If this was you, no action is needed. Your new password is now active.

⚠ Didn't change your password?
If you did not make this change, your account may be compromised. Please:
• Reset your password immediately
• Review your account security
• Contact support: {{support_email}}

© {{current_year}} {{company_name}}
This is an automated security notification.
            ''',
            'description': 'Notification sent when user or admin changes their password',
            'status': 'active',
            'is_default': True,
            'available_variables': {
                'user.first_name': 'User first name',
                'user.email': 'User email address',
                'change_time': 'Timestamp of password change',
                'change_ip': 'IP address where change was made',
                'device': 'Device type used for change',
                'company_name': 'Company name',
                'support_email': 'Support contact email',
                'dashboard_url': 'Dashboard URL',
                'current_year': 'Current year',
            }
        }
    )
    
    if created:
        print("✅ Created: Password Changed Notification template")
    else:
        print("ℹ️  Updated: Password Changed Notification template")
    
    print("\n" + "="*60)
    print("✨ Password Change Notification Template Ready!")
    print("="*60)
    print("\nTemplate details:")
    print(f"  Type: password_changed")
    print(f"  Name: {template.name}")
    print(f"  Status: {template.status}")
    print(f"  Style: Clean design matching signin notifications")
    print("\nThis template will be sent when users change their password")
    print("for security notification purposes.")
    print("="*60 + "\n")

if __name__ == '__main__':
    create_password_changed_template()
