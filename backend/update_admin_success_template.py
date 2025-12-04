#!/usr/bin/env python
"""
Update admin success template to match user signin notification style
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

# Update the admin success template to match user style
try:
    template = EmailTemplate.objects.get(
        template_type='signin_notification',
        name='Admin Login Success - Welcome Back'
    )
    
    template.subject_template = 'Admin Login Successful - {{company_name}}'
    template.html_content = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Login Success - {{company_name}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{{company_name}}</h1>
        <p style="color: #e0e0e0; margin: 8px 0 0 0; font-size: 14px;">Admin Portal Login Success</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #000856; margin-top: 0; font-size: 20px;">Welcome back, {{user.first_name}}!</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            You have successfully logged into the admin portal.
        </p>

        <!-- Login Details Box -->
        <div style="background: #f8f9fa; border-left: 4px solid #00B38F; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: #333;"><strong>Session details:</strong></p>
            <table style="width: 100%; font-size: 14px; color: #555;">
                <tr>
                    <td style="padding: 5px 0; width: 120px;"><strong>Login Time:</strong></td>
                    <td style="padding: 5px 0;">{{login_time}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>Account:</strong></td>
                    <td style="padding: 5px 0;">{{user.email}}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0;"><strong>IP Address:</strong></td>
                    <td style="padding: 5px 0;">{{login_ip}}</td>
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
                <strong>✓ Secure Admin Access</strong><br>
                Your session is now active. If this was you, no action is needed.
            </p>
        </div>

        <!-- Security Warning -->
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px; color: #856404;">
                <strong>⚠ Security Reminder</strong>
            </p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px; font-size: 14px; color: #856404;">
                <li>Always log out when finished</li>
                <li>Never share your admin credentials</li>
                <li>Report suspicious activity immediately</li>
            </ul>
        </div>

        <!-- Dashboard Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{dashboard_url}}" style="background: #00B38F; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">
                Go to Admin Dashboard
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
    '''
    
    template.save()
    print("✅ Admin success template updated to match user signin notification style!")
    print("   - Removed colorful gradients")
    print("   - Using #000856 (dark blue) header")
    print("   - Using #00B38F (teal) accents")
    print("   - Clean, professional design")
    
except EmailTemplate.DoesNotExist:
    print("❌ Template not found. Please create it first using create_signin_templates.py")
except Exception as e:
    print(f"❌ Error: {e}")
