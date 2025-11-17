import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

# Delete old template if exists
EmailTemplate.objects.filter(name='Email Verification').delete()
print("🗑️  Deleted old Email Verification template")

# Create the Email Verification template
template = EmailTemplate.objects.create(
    name='Email Verification',
    template_type='custom',
    subject_template='Verify Your Email - OxiWorld',
    is_default=True,  # Make this the default custom template
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #00B38F 0%, #009975 100%); color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
        .content { background: white; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none; }
        .otp-box { background: #f9fafb; border: 2px solid #00B38F; border-radius: 8px; padding: 24px; text-align: center; margin: 30px 0; }
        .otp-code { font-size: 32px; font-weight: 700; color: #00B38F; letter-spacing: 8px; font-family: 'Courier New', monospace; margin: 10px 0; }
        .warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 20px 0; border-radius: 4px; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }
        .security-note { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 20px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Email Verification</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{{user.first_name}}</strong>,</p>
            
            <p>We received a request to verify your email address for your OxiWorld account.</p>
            
            <div class="otp-box">
                <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                <div class="otp-code">{{otp_code}}</div>
                <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 13px;">Enter this code to verify your email</p>
            </div>
            
            <div class="warning">
                <strong>⏰ Important:</strong> This verification code will expire in <strong>10 minutes</strong>.
            </div>
            
            <div class="security-note">
                <strong>🛡️ Security Notice:</strong> If you didn't request email verification, please ignore this email. Your account remains secure.
            </div>
            
            <p style="margin-top: 30px; color: #6b7280; font-size: 14px;">
                This is an automated message, please do not reply to this email.
            </p>
        </div>
        <div class="footer">
            <p>&copy; 2025 OxiWorld. All rights reserved.</p>
            <p>Building the future of learning.</p>
        </div>
    </div>
</body>
</html>''',
    text_content='''Hello {{user.first_name}},

We received a request to verify your email address for your OxiWorld account.

Your Verification Code: {{otp_code}}

This code will expire in 10 minutes.

If you didn't request email verification, please ignore this email.

Best regards,
OxiWorld Team''',
    status='active',
    is_system_email=True,
    description='Email template for verifying user email addresses with OTP code',
    available_variables={'user.first_name': "User's first name", 'otp_code': 'One-time verification code'}
)

print("✅ Email Verification template created successfully!")
print(f"\nTemplate Details:")
print(f"Name: {template.name}")
print(f"Type: {template.template_type}")
print(f"Subject: {template.subject_template}")
print(f"Status: {template.status}")
print(f"Available Variables: {template.available_variables}")
