"""
Management command to create system-critical email templates
These emails are auto-active and cannot be deleted/deactivated by admins
"""
from django.core.management.base import BaseCommand
from users.models import EmailTemplate


class Command(BaseCommand):
    help = 'Creates system-critical email templates that are always active'

    SYSTEM_EMAIL_TEMPLATES = {
        'email_verification': {
            'name': 'Email Verification',
            'description': 'Sent when user needs to verify their email address',
            'subject_template': 'Verify Your OxiWorld Account - Action Required',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #1E40AF; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .verify-button { background: #1E40AF; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Verify Your Email</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Secure your OxiWorld account</p>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">To complete your OxiWorld account setup, please verify your email address by clicking the button below.</p>
      
      <a href="{{verification_url}}" class="verify-button" style="display: block; text-align: center; text-decoration: none; color: white;">Verify Email Address</a>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If the button doesn't work, copy and paste this link:<br>
      <span style="word-break: break-all; color: #1E40AF;">{{verification_url}}</span></p>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">This link expires in 24 hours for security.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

To complete your OxiWorld account setup, please verify your email address.

Verification link: {{verification_url}}

This link expires in 24 hours for security.

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'user.email': "User's email address",
                'verification_url': "Email verification URL",
            }
        },
        
        'password_reset': {
            'name': 'Password Reset Request',
            'description': 'Sent when user requests password reset',
            'subject_template': 'Reset Your OxiWorld Password - Expires in 1 Hour',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #DC2626; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .reset-button { background: #DC2626; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Password Reset Request</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Secure your account</p>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We received a request to reset your password. Click the button below to create a new password.</p>
      
      <a href="{{reset_url}}" class="reset-button" style="display: block; text-align: center; text-decoration: none; color: white;">Reset Password</a>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If the button doesn't work, copy and paste this link:<br>
      <span style="word-break: break-all; color: #DC2626;">{{reset_url}}</span></p>
      
      <p style="font-size: 14px; line-height: 1.6; color: #991B1B;"><strong>This reset link expires in 1 hour for security.</strong></p>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If you didn't request this, please ignore this email.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Stay secure,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

We received a request to reset your OxiWorld password.

Reset your password: {{reset_url}}

This link expires in 1 hour for security.

If you didn't request this, please ignore this email.

Stay secure,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'user.email': "User's email address",
                'reset_url': "Password reset URL",
            }
        },
        
        'signin_notification': {
            'name': 'New Sign-in Alert',
            'description': 'Security notification for new device sign-in',
            'subject_template': 'New Sign-in to Your OxiWorld Account',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #1E40AF; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .info-box { background: #F0F9FF; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">New Sign-in Detected</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We detected a new sign-in to your OxiWorld account.</p>
      
      <div class="info-box">
        <p style="margin: 5px 0; color: #374151;"><strong>Date & Time:</strong> {{signin_datetime}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Device:</strong> {{device}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Location:</strong> {{location}}</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If this was you, no action needed. If not, please secure your account immediately.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Stay secure,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

New Sign-in Detected

Date & Time: {{signin_datetime}}
Device: {{device}}
Location: {{location}}

If this was you, no action needed. If not, please secure your account immediately.

Stay secure,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'signin_datetime': "Sign-in date and time",
                'device': "Device information",
                'location': "Approximate location",
            }
        },
        
        'payment_success': {
            'name': 'Payment Confirmation',
            'description': 'Sent when payment is successfully processed',
            'subject_template': 'Payment Successful - {{amount}} {{currency}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .amount { font-size: 32px; font-weight: bold; color: #10B981; text-align: center; margin: 20px 0; }
    .details-box { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Payment Successful</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your payment has been processed successfully.</p>
      
      <div class="amount">{{currency}} {{amount}}</div>
      
      <div class="details-box">
        <p style="margin: 5px 0; color: #374151;"><strong>Transaction ID:</strong> {{gateway_reference}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Date:</strong> {{paid_at}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Payment Method:</strong> {{payment_method}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Description:</strong> {{description}}</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for your payment!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Payment Successful

Amount: {{currency}} {{amount}}

Transaction ID: {{gateway_reference}}
Date: {{paid_at}}
Payment Method: {{payment_method}}
Description: {{description}}

Thank you for your payment!

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'amount': "Payment amount",
                'currency': "Currency code",
                'gateway_reference': "Payment transaction ID",
                'paid_at': "Payment date",
                'payment_method': "Payment method",
                'description': "Payment description",
            }
        },
        
        'payment_failed': {
            'name': 'Payment Failed',
            'description': 'Sent when payment fails and requires action',
            'subject_template': 'Payment Failed - Action Required',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #EF4444; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .details-box { background: #FEF2F2; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .retry-button { background: #EF4444; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Payment Failed</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We were unable to process your payment. Please update your payment method to continue.</p>
      
      <div class="details-box">
        <p style="margin: 5px 0; color: #DC2626;"><strong>Amount:</strong> {{currency}} {{amount}}</p>
        <p style="margin: 5px 0; color: #DC2626;"><strong>Date:</strong> {{failed_date}}</p>
        <p style="margin: 5px 0; color: #DC2626;"><strong>Reason:</strong> {{failure_reason}}</p>
      </div>
      
      <a href="{{update_payment_url}}" class="retry-button" style="display: block; text-align: center; text-decoration: none; color: white;">Update Payment Method</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If you need assistance, please contact support.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Payment Failed

We were unable to process your payment.

Amount: {{currency}} {{amount}}
Date: {{failed_date}}
Reason: {{failure_reason}}

Update your payment method: {{update_payment_url}}

If you need assistance, please contact support.

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'amount': "Payment amount",
                'currency': "Currency code",
                'failed_date': "Failure date",
                'failure_reason': "Failure reason",
                'update_payment_url': "Payment update URL",
            }
        },

        'payment_refunded': {
            'name': 'Payment Refunded',
            'description': 'Sent when payment refund is processed',
            'subject_template': 'Refund Processed - {{amount}} {{currency}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #3B82F6; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .amount { font-size: 32px; font-weight: bold; color: #3B82F6; text-align: center; margin: 20px 0; }
    .details-box { background: #F0F9FF; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Refund Processed</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your refund has been processed successfully.</p>
      
      <div class="amount">{{currency}} {{amount}}</div>
      
      <div class="details-box">
        <p style="margin: 5px 0; color: #374151;"><strong>Refund ID:</strong> {{refund_id}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Original Transaction:</strong> {{original_transaction_id}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Refund Date:</strong> {{refund_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Reason:</strong> {{refund_reason}}</p>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">The refund will appear in your account within 3-5 business days.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Refund Processed

Amount: {{currency}} {{amount}}

Refund ID: {{refund_id}}
Original Transaction: {{original_transaction_id}}
Refund Date: {{refund_date}}
Reason: {{refund_reason}}

The refund will appear in your account within 3-5 business days.

Thank you,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'amount': "Refund amount",
                'currency': "Currency code",
                'refund_id': "Refund ID",
                'original_transaction_id': "Original transaction ID",
                'refund_date': "Refund date",
                'refund_reason': "Refund reason",
            }
        },
        
        'subscription_success': {
            'name': 'Subscription Activated',
            'description': 'Sent when subscription payment is successful',
            'subject_template': 'Welcome to {{plan_type}} - Subscription Active',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .plan-box { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;">Subscription Activated</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Welcome to OxiWorld Premium</p>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your subscription has been activated successfully!</p>
      
      <div class="plan-box">
        <p style="margin: 5px 0; color: #374151;"><strong>Plan:</strong> {{plan.name}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Amount:</strong> {{currency}} {{amount}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Next Billing:</strong> {{next_billing_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Status:</strong> Active</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for subscribing to OxiWorld!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Subscription Activated

Your subscription has been activated successfully!

Plan: {{plan.name}}
Amount: {{currency}} {{amount}}
Next Billing: {{next_billing_date}}
Status: Active

Thank you for subscribing to OxiWorld!

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'plan.name': "Subscription plan name",
                'amount': "Subscription amount",
                'currency': "Currency code",
                'next_billing_date': "Next billing date",
            }
        },
        
        'subscription_expiry': {
            'name': 'Subscription Expiring Soon',
            'description': 'Warning about upcoming subscription expiration',
            'subject_template': 'Your {{plan.name}} Subscription Expires Soon',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #F59E0B; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .countdown { font-size: 32px; font-weight: bold; color: #F59E0B; text-align: center; margin: 20px 0; }
    .renew-button { background: #F59E0B; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Subscription Expiring Soon</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your {{plan.name}} subscription will expire soon.</p>
      
      <div class="countdown">{{days_remaining}} Days Left</div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Renew now to continue enjoying premium features.</p>
      
      <a href="{{renewal_url}}" class="renew-button" style="display: block; text-align: center; text-decoration: none; color: white;">Renew Subscription</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Subscription Expiring Soon

Your {{plan.name}} subscription will expire in {{days_remaining}} days.

Renew now: {{renewal_url}}

Thank you,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'plan.name': "Subscription plan name",
                'days_remaining': "Days until expiration",
                'renewal_url': "Renewal URL",
            }
        },
        
        'subscription_renewal': {
            'name': 'Subscription Renewed',
            'description': 'Confirmation of subscription renewal',
            'subject_template': 'Subscription Renewed - {{plan.name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .renewal-box { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;">Subscription Renewed</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Thank you for staying with us</p>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your subscription has been renewed successfully!</p>
      
      <div class="renewal-box">
        <p style="margin: 5px 0; color: #374151;"><strong>Plan:</strong> {{plan.name}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Renewal Date:</strong> {{renewal_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Next Billing:</strong> {{next_billing_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Amount:</strong> {{currency}} {{amount}}</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for your continued support!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Subscription Renewed

Your subscription has been renewed successfully!

Plan: {{plan.name}}
Renewal Date: {{renewal_date}}
Next Billing: {{next_billing_date}}
Amount: {{currency}} {{amount}}

Thank you for your continued support!

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'plan.name': "Subscription plan name",
                'renewal_date': "Renewal date",
                'next_billing_date': "Next billing date",
                'amount': "Renewal amount",
                'currency': "Currency code",
            }
        },
        
        'telegram_added': {
            'name': 'Telegram Group Access Granted',
            'description': 'Notification when user is added to Telegram group',
            'subject_template': 'Welcome to {{group_name}} Telegram Group',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #0088CC; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .join-button { background: #0088CC; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Telegram Access Granted</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">You've been granted access to the OxiWorld Telegram group: <strong>{{group_name}}</strong></p>
      
      <a href="{{join_url}}" class="join-button" style="display: block; text-align: center; text-decoration: none; color: white;">Join Telegram Group</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome to the community!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Telegram Access Granted

You've been granted access to: {{group_name}}

Join now: {{join_url}}

Welcome to the community!

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'group_name': "Telegram group name",
                'join_url': "Join URL",
            }
        },
        
        'telegram_removed': {
            'name': 'Telegram Group Access Removed',
            'description': 'Notification when user is removed from Telegram group',
            'subject_template': 'Telegram Access Update - {{group_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #6B7280; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .info-box { background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Telegram Access Update</h1>
    </div>
    <div class="content">
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your access to the Telegram group <strong>{{group_name}}</strong> has been updated.</p>
      
      <div class="info-box">
        <p style="margin: 0; color: #374151;"><strong>Reason:</strong> {{removal_reason}}</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If you have questions, please contact support.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
    </div>
  </div>
</body>
</html>''',
            'text_content': '''Hi {{user.first_name}},

Telegram Access Update

Your access to {{group_name}} has been updated.

Reason: {{removal_reason}}

If you have questions, please contact support.

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.''',
            'available_variables': {
                'user.first_name': "User's first name",
                'group_name': "Telegram group name",
                'removal_reason': "Removal reason",
            }
        },
    }

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        
        self.stdout.write(self.style.WARNING('Creating system email templates...'))
        
        for template_type, template_data in self.SYSTEM_EMAIL_TEMPLATES.items():
            # Check if template already exists
            existing_template = EmailTemplate.objects.filter(
                template_type=template_type,
                is_system_email=True
            ).first()
            
            if existing_template:
                self.stdout.write(
                    self.style.WARNING(f'  - {template_type}: Already exists, skipping')
                )
                continue
            
            # Create new system email template
            template = EmailTemplate.objects.create(
                name=template_data['name'],
                template_type=template_type,
                description=template_data['description'],
                subject_template=template_data['subject_template'],
                html_content=template_data['html_content'],
                text_content=template_data['text_content'],
                available_variables=template_data['available_variables'],
                status='active',  # Always active
                is_default=True,  # Default for this type
                is_system_email=True,  # Protected
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Created: {template_data["name"]} ({template_type})')
            )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} system email template(s)')
        )
        
        if created_count == 0:
            self.stdout.write(
                self.style.WARNING('All system email templates already exist')
            )
