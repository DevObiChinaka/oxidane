"""
Management command to create default email templates
"""

from django.core.management.base import BaseCommand
from users.models import EmailTemplate


class Command(BaseCommand):
    help = 'Create default email templates for the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating default email templates...')
        
        templates = [
            {
                'name': 'Welcome Email',
                'template_type': 'welcome',
                'subject_template': 'Welcome to {{company_name}} - Your Forex Journey Begins! 🎉',
                'description': 'Welcome email sent to new users upon registration',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to {{company_name}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">🎉 Welcome to {{company_name}}!</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Your Forex Trading Journey Starts Now</p>
    </div>
    
    <div style="background: white; padding: 40px 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0; font-size: 24px; font-weight: 600;">🚀 Account Successfully Created!</h2>
        <p style="font-size: 16px; margin-bottom: 20px; color: #555;">Hi {{user.first_name}},</p>
        <p style="font-size: 16px; margin-bottom: 30px; color: #555;">Congratulations! Your {{company_name}} account has been successfully created. You're now part of our exclusive forex trading community.</p>
        
        <div style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); border: 2px solid #00B38F; padding: 30px; border-radius: 12px; text-align: center; margin: 30px 0;">
            <h3 style="margin: 0 0 20px 0; color: #00B38F; font-size: 20px; font-weight: 600;">🎯 What's Next?</h3>
            <div style="text-align: left; color: #333;">
                <p style="margin: 10px 0; font-size: 16px;">✅ <strong>Explore Free Courses:</strong> Access our comprehensive forex education library</p>
                <p style="margin: 10px 0; font-size: 16px;">✅ <strong>Live Market Data:</strong> Track real-time forex rates and market sessions</p>
                <p style="margin: 10px 0; font-size: 16px;">✅ <strong>Join the Community:</strong> Connect with fellow traders and mentors</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="https://oxiworld.com/courses" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; font-size: 16px;">Start Learning Now</a>
        </div>
        
        <p style="font-size: 14px; color: #666; text-align: center; margin-top: 30px;">
            Need help? Contact us at <a href="mailto:{{support_email}}" style="color: #667eea;">{{support_email}}</a>
        </p>
    </div>
</body>
</html>
                ''',
                'status': 'active',
                'is_default': True,
            },
            {
                'name': 'Subscription Success',
                'template_type': 'subscription_success',
                'subject_template': 'Welcome to {{subscription.plan_type}} Plan - Payment Confirmed! 💳✅',
                'description': 'Sent when subscription payment is successful',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Subscription Confirmed</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #00B38F 0%, #00D4AA 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">🎉 Payment Successful!</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Your {{subscription.plan_type}} subscription is now active</p>
    </div>
    
    <div style="background: white; padding: 40px 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0;">Hi {{user.first_name}},</h2>
        <p style="font-size: 16px; color: #555;">Great news! Your payment has been successfully processed and your subscription is now active.</p>
        
        <div style="background: #f8f9fa; border-left: 4px solid #00B38F; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
            <h3 style="margin: 0 0 15px 0; color: #00B38F;">📋 Subscription Details</h3>
            <p style="margin: 5px 0;"><strong>Plan:</strong> {{subscription.plan_type}}</p>
            <p style="margin: 5px 0;"><strong>Amount:</strong> {{subscription.amount}}</p>
            <p style="margin: 5px 0;"><strong>Reference:</strong> {{subscription.reference}}</p>
            <p style="margin: 5px 0;"><strong>Start Date:</strong> {{subscription.start_date}}</p>
            <p style="margin: 5px 0;"><strong>End Date:</strong> {{subscription.end_date}}</p>
        </div>
        
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%); border: 1px solid #2196f3; padding: 25px; border-radius: 10px; margin: 30px 0;">
            <h4 style="margin: 0 0 15px 0; color: #1976d2;">📱 Next Steps</h4>
            <p style="margin: 0 0 10px 0; color: #333;">You'll be added to our exclusive Telegram group: <strong>{{telegram_group}}</strong></p>
            <p style="margin: 0; color: #666; font-size: 14px;">Please allow up to 24 hours for group access activation.</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://oxiworld.com/dashboard" style="background: #00B38F; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Access Your Dashboard</a>
        </div>
        
        <p style="font-size: 14px; color: #666; text-align: center;">
            Questions? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
        </p>
    </div>
</body>
</html>
                ''',
                'status': 'active',
                'is_default': True,
            },
            {
                'name': 'Payment Failed',
                'template_type': 'payment_failed',
                'subject_template': 'Payment Issue - Let\'s Get This Resolved 🔄',
                'description': 'Sent when payment fails or is declined',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Payment Issue</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">⚠️ Payment Issue</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">We encountered a problem processing your payment</p>
    </div>
    
    <div style="background: white; padding: 40px 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0;">Hi {{user.first_name}},</h2>
        <p style="font-size: 16px; color: #555;">We're sorry, but we couldn't process your payment. Don't worry - this happens sometimes and is usually easy to resolve!</p>
        
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 30px 0;">
            <h3 style="margin: 0 0 15px 0; color: #856404;">💡 Common Solutions</h3>
            <ul style="margin: 0; padding-left: 20px; color: #856404;">
                <li>Check that your card details are correct</li>
                <li>Ensure your card has sufficient funds</li>
                <li>Try a different payment method</li>
                <li>Contact your bank if the issue persists</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://oxiworld.com/subscribe" style="background: #00B38F; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Try Again</a>
        </div>
        
        <p style="font-size: 14px; color: #666; text-align: center;">
            Need help? We're here for you: <a href="mailto:{{support_email}}">{{support_email}}</a>
        </p>
    </div>
</body>
</html>
                ''',
                'status': 'active',
                'is_default': True,
            },
            {
                'name': 'Renewal Reminder',
                'template_type': 'renewal_reminder',
                'subject_template': 'Your subscription expires in {{days_remaining}} days - Renew now! ⏰',
                'description': 'Sent to remind users to renew their subscription',
                'html_content': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Renewal Reminder</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); padding: 40px 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">⏰ Renewal Reminder</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">{{days_remaining}} days remaining on your subscription</p>
    </div>
    
    <div style="background: white; padding: 40px 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <h2 style="color: #333; margin-top: 0;">Hi {{user.first_name}},</h2>
        <p style="font-size: 16px; color: #555;">Your {{subscription.plan_type}} subscription will expire in <strong>{{days_remaining}} days</strong>. Don't miss out on continued access to our premium content!</p>
        
        <div style="background: #f8f9fa; border: 2px solid #f39c12; padding: 25px; border-radius: 10px; margin: 30px 0; text-align: center;">
            <h3 style="margin: 0 0 15px 0; color: #f39c12;">🎯 What You'll Keep With Renewal</h3>
            <div style="text-align: left; color: #333;">
                <p style="margin: 10px 0;">✅ Exclusive Telegram group access</p>
                <p style="margin: 10px 0;">✅ Premium trading signals</p>
                <p style="margin: 10px 0;">✅ Live market analysis</p>
                <p style="margin: 10px 0;">✅ 1-on-1 mentorship opportunities</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{renewal_link}}" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; font-size: 16px;">Renew Now</a>
        </div>
        
        <p style="font-size: 14px; color: #666; text-align: center;">
            Questions about renewal? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
        </p>
    </div>
</body>
</html>
                ''',
                'status': 'active',
                'is_default': True,
            }
        ]
        
        created_count = 0
        
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                is_default=True,
                defaults=template_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {template.name}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Exists: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Created {created_count} new email templates!')
        )
        
        if created_count == 0:
            self.stdout.write(
                self.style.WARNING('All default templates already exist.')
            )