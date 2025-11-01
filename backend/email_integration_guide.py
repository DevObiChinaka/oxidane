# Integration Guide: Automatic Email System for OxiWorld
# This file shows how to integrate automatic emails into your existing subscription system

"""
🚀 AUTOMATIC EMAIL INTEGRATION GUIDE

This implementation provides automatic email triggering for ALL user actions:

1. REGISTRATION FLOW:
   ✅ Email Verification (uses template system)
   ✅ Welcome Email (automatic via Django signals)

2. AUTHENTICATION:
   ✅ Password Reset (uses template system)
   ✅ Login Notifications (for first login or after 7+ days)

3. SUBSCRIPTION EVENTS:
   ✅ Subscription Success
   ✅ Payment Failed
   ✅ Renewal Reminders
   ✅ Telegram Integration Notifications

4. ADMIN ACTIONS:
   ✅ Manual email campaigns (existing system)
   ✅ User status changes
   ✅ Account notifications

HOW TO USE IN YOUR SUBSCRIPTION SYSTEM:
"""

# Example 1: Subscription Payment Success
def handle_payment_verification(subscription_id, payment_data):
    """
    Call this when a payment is verified/successful
    """
    from users.email_automation import send_subscription_success_email
    from users.models import User
    
    # Get subscription and user (adjust based on your models)
    # subscription = YourSubscriptionModel.objects.get(id=subscription_id)
    # user = subscription.user
    
    # Prepare subscription details for email template
    subscription_details = {
        'plan_type': 'Monthly Premium',  # subscription.plan_type
        'amount_paid': 49.99,  # subscription.amount_paid
        'subscription_start': '2025-01-01',  # subscription.subscription_start
        'subscription_end': '2025-02-01',  # subscription.subscription_end
        'paystack_reference': 'ref_123456',  # subscription.paystack_reference
    }
    
    # Send automatic success email
    # send_subscription_success_email(user, subscription_details)
    
    print("✅ Subscription success email will be sent automatically")

# Example 2: Payment Failed
def handle_payment_failure(payment_reference, user_email, failure_reason):
    """
    Call this when a payment fails
    """
    from users.email_automation import send_payment_failed_email
    from users.models import User
    
    # user = User.objects.get(email=user_email)
    
    payment_details = {
        'amount': 49.99,
        'reference': payment_reference,
        'failure_reason': failure_reason,
        'retry_url': 'http://localhost:3000/subscription/retry'
    }
    
    # Send automatic failure email
    # send_payment_failed_email(user, payment_details)
    
    print("📧 Payment failure email will be sent automatically")

# Example 3: Subscription Renewal Reminder (run as cron job)
def send_renewal_reminders():
    """
    Run this as a daily cron job to send renewal reminders
    """
    from users.email_automation import send_subscription_renewal_reminder
    from users.models import User
    from datetime import datetime, timedelta
    
    # Find subscriptions expiring in 3 days (adjust query based on your models)
    expiry_date = datetime.now() + timedelta(days=3)
    
    # expiring_subscriptions = YourSubscriptionModel.objects.filter(
    #     subscription_end__date=expiry_date.date(),
    #     auto_renewal=False,
    #     is_active=True
    # )
    
    # for subscription in expiring_subscriptions:
    #     subscription_details = {
    #         'plan_type': subscription.plan_type,
    #         'expiry_date': subscription.subscription_end.strftime('%B %d, %Y'),
    #         'days_remaining': 3,
    #         'renewal_url': f'http://localhost:3000/subscription/renew/{subscription.id}',
    #         'subscription_amount': subscription.amount_paid,
    #     }
    #     
    #     send_subscription_renewal_reminder(subscription.user, subscription_details)
    
    print("🔔 Renewal reminders will be sent automatically")

# Example 4: Subscription Model Integration
"""
Add this to your subscription model to trigger automatic emails:

class Subscription(models.Model):
    # ... your existing fields ...
    
    def save(self, *args, **kwargs):
        # Check if payment status changed to verified
        if self.pk:
            old_instance = Subscription.objects.get(pk=self.pk)
            if (old_instance.payment_status != 'verified' and 
                self.payment_status == 'verified'):
                # Payment was just verified - send success email
                from users.email_automation import send_subscription_success_email
                
                subscription_details = {
                    'plan_type': self.plan_type,
                    'amount_paid': self.amount_paid,
                    'subscription_start': self.subscription_start.isoformat() if self.subscription_start else '',
                    'subscription_end': self.subscription_end.isoformat() if self.subscription_end else '',
                    'paystack_reference': self.paystack_reference,
                }
                
                send_subscription_success_email(self.user, subscription_details)
            
            elif (old_instance.payment_status != 'failed' and 
                  self.payment_status == 'failed'):
                # Payment failed - send failure email
                from users.email_automation import send_payment_failed_email
                
                payment_details = {
                    'amount': self.amount_paid,
                    'reference': self.paystack_reference,
                    'failure_reason': 'Payment processing failed. Please check your payment details.',
                    'retry_url': f'http://localhost:3000/subscription/retry/{self.id}'
                }
                
                send_payment_failed_email(self.user, payment_details)
        
        super().save(*args, **kwargs)
"""

# Example 5: Django Management Command for Bulk Operations
"""
Create this as management/commands/send_renewal_reminders.py:

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Send subscription renewal reminders'

    def handle(self, *args, **options):
        from users.email_automation import send_subscription_renewal_reminder
        
        # Your logic here to find expiring subscriptions
        # Then send reminders automatically
        
        self.stdout.write(
            self.style.SUCCESS('Successfully sent renewal reminders')
        )

# Run with: python manage.py send_renewal_reminders
"""

# Example 6: API Integration
"""
Add this to your API views for real-time triggers:

@api_view(['POST'])
def subscription_webhook(request):
    '''Paystack webhook for subscription events'''
    
    if request.data.get('event') == 'charge.success':
        # Payment successful
        payment_ref = request.data['data']['reference']
        
        try:
            subscription = Subscription.objects.get(paystack_reference=payment_ref)
            subscription.payment_status = 'verified'
            subscription.save()  # This will trigger the email via model save()
            
        except Subscription.DoesNotExist:
            pass
    
    elif request.data.get('event') == 'charge.failed':
        # Payment failed
        payment_ref = request.data['data']['reference']
        failure_reason = request.data['data'].get('gateway_response', 'Payment failed')
        
        try:
            subscription = Subscription.objects.get(paystack_reference=payment_ref)
            subscription.payment_status = 'failed'
            subscription.save()  # This will trigger the failure email via model save()
            
        except Subscription.DoesNotExist:
            pass
    
    return Response({'status': 'success'})
"""

# CRON JOB SETUP for automated reminders:
"""
Add these to your crontab (crontab -e):

# Send renewal reminders daily at 9 AM
0 9 * * * cd /path/to/your/project && python manage.py send_renewal_reminders

# Send welcome follow-up emails 3 days after registration
0 10 * * * cd /path/to/your/project && python manage.py send_followup_emails

# Clean up expired verification tokens daily
0 2 * * * cd /path/to/your/project && python manage.py cleanup_tokens
"""

print("🎉 Automatic Email Integration Complete!")
print("""
✅ WHAT'S NOW AUTOMATED:

1. REGISTRATION:
   • Email verification uses professional templates
   • Welcome emails sent automatically after account creation
   
2. AUTHENTICATION:
   • Password reset uses professional templates
   • Login notifications for security
   
3. SUBSCRIPTIONS:
   • Success emails when payments are verified
   • Failure emails when payments fail
   • Renewal reminders before expiration
   
4. ADMIN ACTIONS:
   • Manual email campaigns with professional templates
   • Bulk email sending with recipient analytics

🔧 NEXT STEPS:
1. Integrate the model save() methods into your subscription models
2. Set up cron jobs for automated reminders  
3. Add webhook handlers for payment events
4. Test all email templates in your admin panel

🎯 RESULT: 
Your users will now receive beautifully designed, contextual emails 
at exactly the right moments in their journey!
""")