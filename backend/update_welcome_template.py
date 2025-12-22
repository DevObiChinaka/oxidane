#!/usr/bin/env python
"""
Update welcome email template to match signin template styling
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

# Updated welcome template with consistent styling
welcome_html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to {{company_name}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{{company_name}}</h1>
        <p style="color: #e0e0e0; margin: 8px 0 0 0; font-size: 14px;">Welcome to Your Forex Journey</p>
    </div>

    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        
        <!-- Welcome Message -->
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background: #00B38F; color: white; width: 60px; height: 60px; line-height: 60px; border-radius: 50%; font-size: 30px; margin-bottom: 15px;">
                🎉
            </div>
            <h2 style="color: #000856; margin: 10px 0; font-size: 22px;">Welcome, {{user.first_name}}!</h2>
            <p style="color: #666; font-size: 15px; margin: 5px 0;">Your account has been successfully created</p>
        </div>

        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Congratulations! You're now part of the {{company_name}} community. We're excited to help you master forex trading.
        </p>

        <!-- What's Next Section -->
        <div style="background: #f5f5f5; border-left: 4px solid #00B38F; padding: 20px; margin: 25px 0; border-radius: 4px;">
            <h3 style="color: #000856; margin: 0 0 15px 0; font-size: 18px;">🎯 What's Next?</h3>
            
            <div style="margin: 12px 0;">
                <strong style="color: #000856;">✓ Explore Free Courses</strong>
                <p style="margin: 5px 0 0 20px; color: #666; font-size: 14px;">Access our comprehensive forex education library</p>
            </div>
            
            <div style="margin: 12px 0;">
                <strong style="color: #000856;">✓ Live Market Data</strong>
                <p style="margin: 5px 0 0 20px; color: #666; font-size: 14px;">Track real-time forex rates and market sessions</p>
            </div>
            
            <div style="margin: 12px 0;">
                <strong style="color: #000856;">✓ Join the Community</strong>
                <p style="margin: 5px 0 0 20px; color: #666; font-size: 14px;">Connect with fellow traders and mentors</p>
            </div>
        </div>

        <!-- CTA Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://oxiworldforexacademy.com/courses" style="display: inline-block; background: #00B38F; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 15px;">
                Start Learning Now →
            </a>
        </div>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

        <!-- Account Info -->
        <div style="background: #f9f9f9; padding: 15px; border-radius: 6px; margin: 20px 0;">
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Email:</strong> {{user.email}}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Account Created:</strong> {{current_date}}</p>
        </div>

        <p style="font-size: 13px; color: #999; margin: 20px 0 0 0;">
            Need help getting started? Contact us at <a href="mailto:{{support_email}}" style="color: #00B38F; text-decoration: none;">{{support_email}}</a>
        </p>
    </div>

    <!-- Footer -->
    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
        <p style="margin: 5px 0;">You're receiving this because you created an account with us.</p>
    </div>
</body>
</html>
'''

welcome_text = '''
Welcome to {{company_name}}!

Hi {{user.first_name}},

Congratulations! Your account has been successfully created. We're excited to help you master forex trading.

WHAT'S NEXT?

✓ Explore Free Courses
  Access our comprehensive forex education library

✓ Live Market Data
  Track real-time forex rates and market sessions

✓ Join the Community
  Connect with fellow traders and mentors

Get started: https://oxiworldforexacademy.com/courses

ACCOUNT DETAILS:
Email: {{user.email}}
Account Created: {{current_date}}

Need help? Contact us at {{support_email}}

© {{current_year}} {{company_name}}
'''

print("Updating welcome email template...")

template = EmailTemplate.objects.get(template_type='welcome')
template.html_content = welcome_html
template.text_content = welcome_text
template.save()

print("✅ Welcome email template updated successfully!")
print(f"   Template: {template.name}")
print(f"   Type: {template.template_type}")
print(f"   Status: {template.status}")
