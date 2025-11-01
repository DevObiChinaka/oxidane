"""
Update OTP and admin signin notification templates to be simple and professional
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

def create_or_update_template(template_type, name, subject, html_content, description, variables):
    """Create or update an email template"""
    template, created = EmailTemplate.objects.update_or_create(
        template_type=template_type,
        is_default=True,
        defaults={
            'name': name,
            'subject_template': subject,
            'html_content': html_content,
            'description': description,
            'available_variables': variables,
            'status': 'active',
        }
    )
    return template, created

# 1. Password Reset OTP Template (Simple & Professional)
password_reset_otp_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid #e5e5e5;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">Password Reset</h1>
                            <p style="margin: 8px 0 0; font-size: 14px; color: #666666;">{{company_name}}</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 24px; font-size: 15px; line-height: 24px; color: #333333;">Hello {{user_name}},</p>
                            
                            <p style="margin: 0 0 24px; font-size: 15px; line-height: 24px; color: #333333;">You requested to reset your password. Use the verification code below to complete the process:</p>
                            
                            <!-- OTP Code Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 32px;">
                                <tr>
                                    <td align="center" style="padding: 24px; background-color: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px;">
                                        <div style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #00B38F; font-family: 'Courier New', monospace;">{{otp_code}}</div>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0 0 16px; font-size: 14px; line-height: 22px; color: #666666;">This code will expire in <strong>10 minutes</strong>.</p>
                            
                            <p style="margin: 0 0 24px; font-size: 14px; line-height: 22px; color: #666666;">If you didn't request a password reset, please ignore this email and ensure your account is secure.</p>
                            
                            <!-- Security Notice -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 32px 0 0;">
                                <tr>
                                    <td style="padding: 16px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                                        <p style="margin: 0; font-size: 13px; line-height: 20px; color: #856404;">
                                            <strong>Security Tip:</strong> Never share this code with anyone. {{company_name}} staff will never ask for your verification code.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8f9fa; border-top: 1px solid #e5e5e5; text-align: center;">
                            <p style="margin: 0; font-size: 13px; line-height: 20px; color: #666666;">
                                This is an automated message from {{company_name}}.<br>
                                Please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

# 2. Admin Sign-in Notification (Simple & Professional)
admin_signin_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid #e5e5e5;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">Admin Login Notification</h1>
                            <p style="margin: 8px 0 0; font-size: 14px; color: #666666;">{{company_name}} Admin Portal</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 24px; font-size: 15px; line-height: 24px; color: #333333;">Hello {{user_name}},</p>
                            
                            <p style="margin: 0 0 24px; font-size: 15px; line-height: 24px; color: #333333;">A successful login to your admin account was detected.</p>
                            
                            <!-- Login Details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 32px; border: 1px solid #e5e5e5; border-radius: 6px;">
                                <tr>
                                    <td style="padding: 20px; background-color: #f8f9fa;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #666666; width: 120px;">Time:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a; font-weight: 500;">{{login_time}}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #666666;">IP Address:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a; font-weight: 500;">{{ip_address}}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #666666;">Location:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a; font-weight: 500;">{{location}}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #666666;">Device:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a; font-weight: 500;">{{device}}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0 0 24px; font-size: 14px; line-height: 22px; color: #666666;">If this was you, no action is needed.</p>
                            
                            <!-- Security Alert -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="padding: 16px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                                        <p style="margin: 0 0 12px; font-size: 13px; line-height: 20px; color: #856404;">
                                            <strong>Wasn't you?</strong>
                                        </p>
                                        <p style="margin: 0; font-size: 13px; line-height: 20px; color: #856404;">
                                            If you didn't make this login, please secure your account immediately by changing your password and reviewing your account activity.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8f9fa; border-top: 1px solid #e5e5e5; text-align: center;">
                            <p style="margin: 0; font-size: 13px; line-height: 20px; color: #666666;">
                                This is an automated security notification from {{company_name}}.<br>
                                Please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

# Update templates
print("🔄 Updating email templates...\n")

# 1. Check if password_reset template type exists, if not add it
template_types = dict(EmailTemplate.TEMPLATE_TYPES)
if 'password_reset_otp' not in template_types:
    print("⚠️  Note: 'password_reset_otp' template type not in model. Using 'password_reset' type.")
    template_type_to_use = 'password_reset'
else:
    template_type_to_use = 'password_reset_otp'

template1, created1 = create_or_update_template(
    template_type=template_type_to_use,
    name='Password Reset OTP - Simple & Professional',
    subject='Password Reset Code - {{company_name}}',
    html_content=password_reset_otp_html,
    description='Simple and professional password reset OTP email template',
    variables={
        'user_name': 'User\'s name',
        'otp_code': 'One-time password code',
        'company_name': 'Company name',
    }
)
print(f"{'✅ Created' if created1 else '🔄 Updated'}: Password Reset OTP Template")

template2, created2 = create_or_update_template(
    template_type='signin_notification',
    name='Admin Login Notification - Simple & Professional',
    subject='Admin Login Notification - {{company_name}}',
    html_content=admin_signin_html,
    description='Simple and professional admin login notification template',
    variables={
        'user_name': 'Admin user\'s name',
        'login_time': 'Time of login',
        'ip_address': 'IP address used',
        'location': 'Approximate location',
        'device': 'Device/browser information',
        'company_name': 'Company name',
    }
)
print(f"{'✅ Created' if created2 else '🔄 Updated'}: Admin Sign-in Notification Template")

print("\n✨ All templates updated successfully!")
print("\n📋 Template Details:")
print(f"   • Password Reset OTP: {template1.name}")
print(f"   • Admin Login: {template2.name}")
print("\n💡 Templates are now simple, professional, and easy to track in the admin panel.")
