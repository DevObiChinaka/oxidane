"""
Management command to create OTP and admin login email templates
Simple, standard, and professional design
"""

from django.core.management.base import BaseCommand
from users.models import EmailTemplate


class Command(BaseCommand):
    help = 'Create OTP and admin login email templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating OTP and admin login email templates...')
        
        templates = [
            {
                'name': 'Password Reset OTP',
                'template_type': 'password_reset',
                'subject_template': 'Password Reset Code - {{company_name}}',
                'description': 'OTP code for password reset',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e5e5;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">{{company_name}}</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #1a1a1a;">Password Reset Request</h2>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                Hello {{user.first_name}},
                            </p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                You have requested to reset your password. Use the verification code below to complete the process:
                            </p>
                            
                            <!-- OTP Code Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 32px 0;">
                                <tr>
                                    <td style="background-color: #f8f9fa; border: 2px solid #e5e5e5; border-radius: 8px; padding: 32px; text-align: center;">
                                        <div style="font-size: 14px; font-weight: 500; color: #6b6b6b; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Verification Code
                                        </div>
                                        <div style="font-size: 36px; font-weight: 700; color: #1a1a1a; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                            {{otp_code}}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                This code will expire in <strong>10 minutes</strong>.
                            </p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                If you didn't request a password reset, please ignore this email and ensure your account is secure.
                            </p>
                            
                            <!-- Security Notice -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 24px 0;">
                                <tr>
                                    <td style="background-color: #fff8e6; border-left: 4px solid #ffb84d; padding: 16px; border-radius: 4px;">
                                        <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #856404;">
                                            <strong>Security Tip:</strong> Never share this code with anyone. {{company_name}} staff will never ask for your verification code.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; background-color: #f8f9fa; border-top: 1px solid #e5e5e5; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; line-height: 1.5; color: #6b6b6b;">
                                Best regards,<br>
                                <strong>{{company_name}} Security Team</strong>
                            </p>
                            <p style="margin: 16px 0 0 0; font-size: 12px; line-height: 1.5; color: #9b9b9b;">
                                This is an automated message. Please do not reply to this email.
                            </p>
                            <p style="margin: 8px 0 0 0; font-size: 12px; line-height: 1.5; color: #9b9b9b;">
                                © {{current_year}} {{company_name}}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
                ''',
                'text_content': '''
{{company_name}}
Password Reset Request

Hello {{user.first_name}},

You have requested to reset your password. Use the verification code below to complete the process:

VERIFICATION CODE: {{otp_code}}

This code will expire in 10 minutes.

If you didn't request a password reset, please ignore this email and ensure your account is secure.

SECURITY TIP: Never share this code with anyone. {{company_name}} staff will never ask for your verification code.

Best regards,
{{company_name}} Security Team

© {{current_year}} {{company_name}}. All rights reserved.
                ''',
                'available_variables': {
                    'user.first_name': 'User\'s first name',
                    'user.full_name': 'User\'s full name',
                    'user.email': 'User\'s email address',
                    'otp_code': 'One-time password code',
                    'company_name': 'Company name',
                    'current_year': 'Current year',
                    'support_email': 'Support email address',
                },
                'status': 'active',
                'is_default': True,
            },
            {
                'name': 'Admin Login Notification',
                'template_type': 'signin_notification',
                'subject_template': 'Admin Login Detected - {{company_name}}',
                'description': 'Notification sent when admin logs in',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login Notification</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 1px solid #e5e5e5;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1a1a1a;">{{company_name}}</h1>
                            <p style="margin: 8px 0 0 0; font-size: 13px; color: #6b6b6b; text-transform: uppercase; letter-spacing: 0.5px;">Admin Dashboard</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #1a1a1a;">Admin Login Detected</h2>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                Hello {{user.first_name}},
                            </p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                A new admin login was detected on your account. Here are the details:
                            </p>
                            
                            <!-- Login Details -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 24px 0;">
                                <tr>
                                    <td style="background-color: #f8f9fa; border: 1px solid #e5e5e5; border-radius: 8px; padding: 24px;">
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6b6b6b; width: 140px;">
                                                    <strong>Account:</strong>
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a;">
                                                    {{user.email}}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6b6b6b;">
                                                    <strong>Login Time:</strong>
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a;">
                                                    {{login_time}}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6b6b6b;">
                                                    <strong>IP Address:</strong>
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a;">
                                                    {{ip_address}}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6b6b6b;">
                                                    <strong>Location:</strong>
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a;">
                                                    {{location}}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6b6b6b;">
                                                    <strong>Device:</strong>
                                                </td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #1a1a1a;">
                                                    {{device}}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Notice -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 24px 0;">
                                <tr>
                                    <td style="background-color: #fff3f3; border-left: 4px solid #dc3545; padding: 16px; border-radius: 4px;">
                                        <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #721c24;">
                                            <strong>Was this you?</strong> If you didn't log in, please secure your account immediately by changing your password.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 24px 0 0 0; font-size: 15px; line-height: 1.6; color: #4a4a4a;">
                                For security reasons, we recommend enabling two-factor authentication on your admin account.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; background-color: #f8f9fa; border-top: 1px solid #e5e5e5; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; line-height: 1.5; color: #6b6b6b;">
                                Best regards,<br>
                                <strong>{{company_name}} Security Team</strong>
                            </p>
                            <p style="margin: 16px 0 0 0; font-size: 12px; line-height: 1.5; color: #9b9b9b;">
                                This is an automated security notification. Please do not reply to this email.
                            </p>
                            <p style="margin: 8px 0 0 0; font-size: 12px; line-height: 1.5; color: #9b9b9b;">
                                © {{current_year}} {{company_name}}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
                ''',
                'text_content': '''
{{company_name}} - Admin Dashboard
Admin Login Detected

Hello {{user.first_name}},

A new admin login was detected on your account. Here are the details:

Account: {{user.email}}
Login Time: {{login_time}}
IP Address: {{ip_address}}
Location: {{location}}
Device: {{device}}

WAS THIS YOU? If you didn't log in, please secure your account immediately by changing your password.

For security reasons, we recommend enabling two-factor authentication on your admin account.

Best regards,
{{company_name}} Security Team

This is an automated security notification.
© {{current_year}} {{company_name}}. All rights reserved.
                ''',
                'available_variables': {
                    'user.first_name': 'User\'s first name',
                    'user.full_name': 'User\'s full name',
                    'user.email': 'User\'s email address',
                    'login_time': 'Time of login',
                    'ip_address': 'IP address used',
                    'location': 'Approximate location',
                    'device': 'Device information',
                    'company_name': 'Company name',
                    'current_year': 'Current year',
                    'support_email': 'Support email address',
                },
                'status': 'active',
                'is_default': True,
            },
        ]
        
        for template_data in templates:
            template, created = EmailTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                name=template_data['name'],
                defaults=template_data
            )
            
            status = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{status} template: {template.name} ({template.template_type})')
            )
        
        self.stdout.write(self.style.SUCCESS('✅ All OTP and admin login templates created successfully!'))
