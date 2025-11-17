"""
Create Email Change OTP Template
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

# First, add the new template type to the model choices (done manually in migrations)
# For now, use 'custom' type or update the TEMPLATE_TYPES

# Create email change verification template
template, created = EmailTemplate.objects.get_or_create(
    name='Email Change Verification',
    defaults={
        'template_type': 'custom',
        'subject_template': 'Email Change Verification Code - OxiWorld',
        'html_content': '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #00B38F; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .otp-code { background: #F1F5F9; border: 2px dashed #00B38F; padding: 20px; text-align: center; margin: 25px 0; border-radius: 8px; }
    .otp-number { font-size: 32px; font-weight: 700; color: #00B38F; letter-spacing: 8px; font-family: monospace; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
    .warning { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin: 20px 0; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Email Change Verification</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Confirm your email address change</p>
    </div>
    <div class="content">
      <p style="font-size: 16px; color: #1E293B;">Hello {{user.first_name}},</p>
      
      <p style="font-size: 16px; color: #475569; line-height: 1.6;">
        You requested to change your email address. To confirm this change, please use the verification code below:
      </p>
      
      <div class="otp-code">
        <p style="margin: 0 0 10px; font-size: 14px; color: #64748B;">Your Verification Code</p>
        <div class="otp-number">{{otp_code}}</div>
        <p style="margin: 10px 0 0; font-size: 12px; color: #64748B;">This code will expire in 10 minutes</p>
      </div>
      
      <div class="warning">
        <p style="margin: 0; font-size: 14px; color: #92400E;">
          <strong>⚠️ Security Notice:</strong> If you did not request this email change, please ignore this message and your account will remain secure.
        </p>
      </div>
      
      <p style="font-size: 14px; color: #64748B; margin-top: 30px;">
        Need help? Contact our support team at support@oxidane.com
      </p>
    </div>
    <div class="footer">
      <p style="margin: 0 0 10px;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 0;">Professional Trading Education Platform</p>
    </div>
  </div>
</body>
</html>''',
        'text_content': '''Hello {{user.first_name}},

You requested to change your email address.

Your verification code is: {{otp_code}}

This code will expire in 10 minutes.

If you did not request this change, please ignore this email and your account will remain secure.

Need help? Contact our support team at support@oxidane.com

© 2025 OxiWorld. All rights reserved.
Professional Trading Education Platform''',
        'status': 'active',
        'is_system_email': True,
        'from_email': 'noreply@oxidane.com',
        'from_name': 'OxiWorld Security',
        'description': 'Sent when user requests to change their email address',
        'available_variables': {
            'user.first_name': 'User first name',
            'otp_code': '6-digit verification code'
        }
    }
)

if created:
    print("✅ Email change verification template created successfully!")
else:
    print("ℹ️  Email change verification template already exists. Updating...")
    template.html_content = EmailTemplate.objects.get(template_type='email_change_verification').html_content
    template.save()
    print("✅ Template updated!")

print(f"\nTemplate Type: {template.template_type}")
print(f"Subject: {template.subject_template}")
print(f"Variables needed: user.first_name, otp_code")
