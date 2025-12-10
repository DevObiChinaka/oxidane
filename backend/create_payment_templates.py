#!/usr/bin/env python
"""
Create all payment-related email templates
Includes: payment_success, payment_failed, payment_refunded, subscription templates
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from users.models import EmailTemplate

def create_payment_templates():
    """Create all payment-related email templates"""
    
    print("Creating payment-related email templates...")
    
    # 1. Payment Success / Receipt Template
    payment_success_template, created = EmailTemplate.objects.update_or_create(
        template_type='payment_success',
        name='Payment Receipt',
        defaults={
            'subject_template': 'Payment Receipt - {{invoice_number}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Payment Receipt</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 650px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #000856 0%, #00B38F 100%); padding: 40px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Payment Successful!</h1>
        <p style="color: #e0e0e0; margin: 12px 0 0 0; font-size: 16px;">Thank you for your payment</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background: #f0fdf4; border: 2px solid #00B38F; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#00B38F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h2 style="color: #000856; margin: 0; font-size: 22px;">Hi {{user.first_name}}!</h2>
            <p style="color: #666; margin: 10px 0 0 0; font-size: 15px;">Your payment has been processed successfully</p>
        </div>

        <!-- Payment Summary Box -->
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 25px; margin: 30px 0;">
            <h3 style="color: #000856; margin: 0 0 20px 0; font-size: 18px; border-bottom: 2px solid #00B38F; padding-bottom: 10px;">Payment Details</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Invoice Number:</td>
                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #000856;">{{invoice_number}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Payment Date:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{payment_date}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Payment Method:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{payment_method}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Reference:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333; font-family: monospace; font-size: 13px;">{{payment_reference}}</td>
                </tr>
                <tr style="border-top: 2px solid #e5e7eb;">
                    <td style="padding: 15px 0 10px 0; color: #666; font-size: 14px;">Plan:</td>
                    <td style="padding: 15px 0 10px 0; text-align: right; font-weight: bold; color: #000856;">{{plan_name}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Subscription Period:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333; font-size: 13px;">{{subscription_start}} - {{subscription_end}}</td>
                </tr>
            </table>
            
            <div style="margin-top: 25px; padding-top: 20px; border-top: 2px solid #e5e7eb;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #666; font-size: 14px;">Amount:</td>
                        <td style="padding: 8px 0; text-align: right; color: #333;">{{payment_amount}}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666; font-size: 14px;">Processing Fee:</td>
                        <td style="padding: 8px 0; text-align: right; color: #333;">{{processing_fee}}</td>
                    </tr>
                    <tr style="border-top: 2px solid #000856;">
                        <td style="padding: 15px 0 0 0; color: #000856; font-size: 16px; font-weight: bold;">Total Paid:</td>
                        <td style="padding: 15px 0 0 0; text-align: right; font-size: 20px; font-weight: bold; color: #00B38F;">{{total_amount}}</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <a href="{{dashboard_url}}" style="display: inline-block; background: #00B38F; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">View Dashboard</a>
        </div>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="margin: 0; font-size: 13px; color: #92400e;">
                <strong>📧 Keep this email:</strong> This serves as your official payment receipt for tax and accounting purposes.
            </p>
        </div>

        <p style="font-size: 14px; color: #666; margin: 25px 0 10px 0;">
            Need help? Contact our support team anytime.
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
        <p style="margin: 5px 0;">This is an automated receipt. Please do not reply to this email.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Email sent after successful payment with receipt details'
        }
    )
    print(f"✓ Payment Success template {'created' if created else 'updated'}")

    # 2. Payment Failed Template
    payment_failed_template, created = EmailTemplate.objects.update_or_create(
        template_type='payment_failed',
        name='Payment Failed Notification',
        defaults={
            'subject_template': 'Payment Failed - Action Required',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Payment Failed</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: #dc2626; padding: 35px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 26px;">Payment Failed</h1>
        <p style="color: #fee2e2; margin: 10px 0 0 0; font-size: 15px;">We couldn't process your payment</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background: #fef2f2; border: 2px solid #dc2626; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h2 style="color: #000856; margin: 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        </div>

        <p style="font-size: 15px; color: #555; margin-bottom: 20px;">
            We attempted to process your payment for <strong>{{plan_name}}</strong>, but unfortunately it failed.
        </p>

        <!-- Failure Details -->
        <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #666; font-size: 14px;">Reason:</td>
                    <td style="padding: 8px 0; text-align: right; color: #dc2626; font-weight: bold;">{{failure_reason}}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666; font-size: 14px;">Amount:</td>
                    <td style="padding: 8px 0; text-align: right; color: #333;">{{payment_amount}}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666; font-size: 14px;">Attempted:</td>
                    <td style="padding: 8px 0; text-align: right; color: #333;">{{payment_date}}</td>
                </tr>
            </table>
        </div>

        <!-- Common Solutions -->
        <div style="background: #f9fafb; border-left: 4px solid #3b82f6; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <h3 style="color: #000856; margin: 0 0 15px 0; font-size: 16px;">Common Solutions:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 1.8;">
                <li>Verify your card has sufficient funds</li>
                <li>Check your card's expiry date</li>
                <li>Ensure your billing address is correct</li>
                <li>Contact your bank to authorize international payments</li>
                <li>Try a different payment method</li>
            </ul>
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <a href="{{retry_payment_url}}" style="display: inline-block; background: #00B38F; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">Try Again</a>
        </div>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <p style="font-size: 13px; color: #666; margin: 20px 0 0 0; text-align: center;">
            Need help? Contact our support team at <a href="mailto:{{support_email}}" style="color: #00B38F; text-decoration: none;">{{support_email}}</a>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Email sent when payment fails with reasons and retry options'
        }
    )
    print(f"✓ Payment Failed template {'created' if created else 'updated'}")

    # 3. Payment Refunded Template
    payment_refunded_template, created = EmailTemplate.objects.update_or_create(
        template_type='payment_refunded',
        name='Payment Refund Confirmation',
        defaults={
            'subject_template': 'Refund Processed - {{refund_amount}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Refund Processed</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: #0891b2; padding: 35px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 26px;">Refund Processed</h1>
        <p style="color: #cffafe; margin: 10px 0 0 0; font-size: 15px;">Your refund has been initiated</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <h2 style="color: #000856; margin: 0 0 15px 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            We've processed your refund request. The funds will be returned to your original payment method.
        </p>

        <!-- Refund Details -->
        <div style="background: #ecfeff; border: 1px solid #a5f3fc; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #000856; margin: 0 0 20px 0; font-size: 18px; border-bottom: 2px solid #0891b2; padding-bottom: 10px;">Refund Details</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Refund Amount:</td>
                    <td style="padding: 10px 0; text-align: right; font-size: 18px; font-weight: bold; color: #0891b2;">{{refund_amount}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Original Payment:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{original_amount}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Refund Reference:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333; font-family: monospace; font-size: 13px;">{{refund_reference}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Processed Date:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{refund_date}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Reason:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{refund_reason}}</td>
                </tr>
            </table>
        </div>

        <!-- Timeline Info -->
        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <h4 style="color: #92400e; margin: 0 0 10px 0; font-size: 15px;">⏱️ What happens next?</h4>
            <p style="margin: 0; font-size: 14px; color: #78350f; line-height: 1.7;">
                Refunds typically take <strong>5-10 business days</strong> to appear in your account, depending on your bank or card issuer. You'll see the credit as "{{company_name}} Refund" on your statement.
            </p>
        </div>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <p style="font-size: 14px; color: #666; margin: 20px 0 0 0;">
            If you don't see the refund after 10 business days, please contact your bank or reach out to our support team.
        </p>

        <p style="font-size: 13px; color: #999; margin: 15px 0 0 0; text-align: center;">
            Questions? Email us at <a href="mailto:{{support_email}}" style="color: #0891b2; text-decoration: none;">{{support_email}}</a>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Email sent when a refund is processed for a payment'
        }
    )
    print(f"✓ Payment Refunded template {'created' if created else 'updated'}")

    # 4. Subscription Success Template
    subscription_success_template, created = EmailTemplate.objects.update_or_create(
        template_type='subscription_success',
        name='Subscription Activated',
        defaults={
            'subject_template': 'Welcome to {{plan_name}} - Subscription Activated!',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Activated</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #000856 0%, #00B38F 100%); padding: 40px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Welcome Aboard!</h1>
        <p style="color: #e0e0e0; margin: 12px 0 0 0; font-size: 16px;">Your subscription is now active</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <h2 style="color: #000856; margin: 0 0 15px 0; font-size: 22px;">Hi {{user.first_name}}! 👋</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Congratulations! Your <strong>{{plan_name}}</strong> subscription is now active and ready to use.
        </p>

        <!-- Subscription Details -->
        <div style="background: #f0fdf4; border: 2px solid #00B38F; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #000856; margin: 0 0 20px 0; font-size: 18px;">Your Subscription</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Plan:</td>
                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #000856; font-size: 16px;">{{plan_name}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Start Date:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{subscription_start}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">End Date:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{subscription_end}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Status:</td>
                    <td style="padding: 10px 0; text-align: right;"><span style="background: #00B38F; color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold;">ACTIVE</span></td>
                </tr>
            </table>
        </div>

        <!-- What's Included -->
        <div style="margin: 30px 0;">
            <h3 style="color: #000856; margin: 0 0 15px 0; font-size: 18px;">What's Included:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 2;">
                <li>✅ Access to all premium courses</li>
                <li>✅ Exclusive Telegram community access</li>
                <li>✅ Priority support</li>
                <li>✅ Monthly live Q&A sessions</li>
                <li>✅ Downloadable resources</li>
            </ul>
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <a href="{{dashboard_url}}" style="display: inline-block; background: #00B38F; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">Start Learning Now</a>
        </div>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <div style="background: #f9fafb; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <h4 style="color: #000856; margin: 0 0 10px 0; font-size: 15px;">💡 Pro Tips:</h4>
            <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 13px; line-height: 1.8;">
                <li>Join our Telegram group to connect with other learners</li>
                <li>Complete your profile to personalize your experience</li>
                <li>Check out the "Getting Started" course first</li>
            </ul>
        </div>

        <p style="font-size: 14px; color: #666; margin: 25px 0 0 0; text-align: center;">
            Questions? We're here to help! Contact us at <a href="mailto:{{support_email}}" style="color: #00B38F; text-decoration: none;">{{support_email}}</a>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Welcome email sent when subscription is successfully activated'
        }
    )
    print(f"✓ Subscription Success template {'created' if created else 'updated'}")

    # 5. Subscription Expiry Warning Template
    subscription_expiry_template, created = EmailTemplate.objects.update_or_create(
        template_type='subscription_expiry',
        name='Subscription Expiring Soon',
        defaults={
            'subject_template': 'Your Subscription Expires in {{days_remaining}} Days',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Expiring</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: #f59e0b; padding: 35px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 26px;">⏰ Subscription Expiring Soon</h1>
        <p style="color: #fef3c7; margin: 10px 0 0 0; font-size: 15px;">Don't lose access to your courses</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <h2 style="color: #000856; margin: 0 0 15px 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            Your <strong>{{plan_name}}</strong> subscription will expire in <strong style="color: #f59e0b;">{{days_remaining}} days</strong>.
        </p>

        <!-- Expiry Notice -->
        <div style="background: #fffbeb; border: 2px solid #f59e0b; border-radius: 8px; padding: 25px; margin: 25px 0; text-align: center;">
            <div style="font-size: 48px; font-weight: bold; color: #f59e0b; margin-bottom: 10px;">{{days_remaining}}</div>
            <div style="color: #92400e; font-size: 16px; font-weight: bold;">Days Remaining</div>
            <div style="color: #78350f; font-size: 14px; margin-top: 10px;">Expires on {{subscription_end}}</div>
        </div>

        <p style="font-size: 15px; color: #555; margin: 25px 0;">
            Renew now to continue enjoying:
        </p>

        <ul style="margin: 0 0 25px 0; padding-left: 20px; color: #666; font-size: 14px; line-height: 2;">
            <li>✅ Unlimited access to all courses</li>
            <li>✅ Telegram community membership</li>
            <li>✅ Live Q&A sessions and workshops</li>
            <li>✅ New content added regularly</li>
        </ul>

        <!-- Action Button -->
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <a href="{{renewal_url}}" style="display: inline-block; background: #00B38F; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">Renew Now</a>
        </div>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        
        <p style="font-size: 13px; color: #999; margin: 20px 0 0 0; text-align: center;">
            Questions about renewal? Contact us at <a href="mailto:{{support_email}}" style="color: #00B38F; text-decoration: none;">{{support_email}}</a>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Reminder email sent when subscription is about to expire'
        }
    )
    print(f"✓ Subscription Expiry template {'created' if created else 'updated'}")

    # 6. Renewal Reminder Template
    renewal_reminder_template, created = EmailTemplate.objects.update_or_create(
        template_type='renewal_reminder',
        name='Subscription Renewal Reminder',
        defaults={
            'subject_template': 'Renewal Reminder - {{plan_name}}',
            'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Renewal Reminder</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: #000856; padding: 35px 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 26px;">Time to Renew</h1>
        <p style="color: #e0e0e0; margin: 10px 0 0 0; font-size: 15px;">Keep your learning journey going</p>
    </div>
    
    <!-- Main Content -->
    <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        
        <h2 style="color: #000856; margin: 0 0 15px 0; font-size: 20px;">Hi {{user.first_name}},</h2>
        
        <p style="font-size: 15px; color: #555; margin-bottom: 25px;">
            It's time to renew your <strong>{{plan_name}}</strong> subscription to maintain uninterrupted access.
        </p>

        <!-- Renewal Info -->
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Current Plan:</td>
                    <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #000856;">{{plan_name}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Renewal Amount:</td>
                    <td style="padding: 10px 0; text-align: right; font-size: 18px; font-weight: bold; color: #00B38F;">{{renewal_amount}}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; color: #666; font-size: 14px;">Next Billing Date:</td>
                    <td style="padding: 10px 0; text-align: right; color: #333;">{{next_billing_date}}</td>
                </tr>
            </table>
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin: 35px 0 25px 0;">
            <a href="{{renewal_url}}" style="display: inline-block; background: #00B38F; color: white; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">Renew Subscription</a>
        </div>

        <p style="font-size: 13px; color: #666; margin: 20px 0; text-align: center;">
            Or manage your subscription settings in your <a href="{{dashboard_url}}" style="color: #00B38F; text-decoration: none;">dashboard</a>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; padding: 25px 20px; color: #999; font-size: 12px;">
        <p style="margin: 5px 0;">© {{current_year}} {{company_name}}. All rights reserved.</p>
    </div>
</body>
</html>
''',
            
            'status': 'active',
            'description': 'Reminder email for subscription renewal'
        }
    )
    print(f"✓ Renewal Reminder template {'created' if created else 'updated'}")

    print("\n✅ All payment-related email templates created successfully!")
    print("\nCreated/Updated templates:")
    print("  1. payment_success - Payment Receipt")
    print("  2. payment_failed - Payment Failed Notification")
    print("  3. payment_refunded - Payment Refund Confirmation")
    print("  4. subscription_success - Subscription Activated")
    print("  5. subscription_expiry - Subscription Expiring Soon")
    print("  6. renewal_reminder - Subscription Renewal Reminder")
    print("\nYou can view and customize these templates in the Django admin.")

if __name__ == '__main__':
    create_payment_templates()
