# Email Automation System
# Automatic email triggering based on user actions and events

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from datetime import timedelta
from .models import User
from .email_service import EmailTemplateService
import logging

logger = logging.getLogger(__name__)


class EmailAutomationService:
    """Service class for handling automatic email triggers"""
    
    def __init__(self):
        self.email_service = EmailTemplateService()
    
    def trigger_welcome_email(self, user):
        """Send welcome email when user completes registration"""
        try:
            result = self.email_service.send_email(
                template_type='welcome',
                recipient_email=user.email,
                user=user,
                test_mode=False
            )
            if result:
                logger.info(f"Welcome email sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send welcome email to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
            return False
    
    def trigger_verification_email(self, user, otp_code=None):
        """Send email verification template"""
        try:
            custom_vars = {}
            if otp_code:
                custom_vars['verification_code'] = otp_code
                custom_vars['otp_code'] = otp_code  # Also add as otp_code for consistency
                frontend_url = getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')
                custom_vars['verification_url'] = f"{frontend_url}/verify?email={user.email}&code={otp_code}"
            
            result = self.email_service.send_email(
                template_type='user_login_otp',  # Use existing OTP template for registration too
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Verification email sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send verification email to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {str(e)}")
            return False
    
    def trigger_password_reset_email(self, user, reset_token=None, reset_otp=None):
        """Send password reset email"""
        try:
            custom_vars = {}
            if reset_token:
                custom_vars['reset_token'] = reset_token
                frontend_url = getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')
                custom_vars['reset_url'] = f"{frontend_url}/reset-password?token={reset_token}"
            if reset_otp:
                custom_vars['reset_code'] = reset_otp
            
            result = self.email_service.send_email(
                template_type='password_reset',
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Password reset email sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send password reset email to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending password reset email to {user.email}: {str(e)}")
            return False
    
    def trigger_login_notification(self, user, login_details=None):
        """Send login notification email"""
        try:
            custom_vars = {
                'login_time': timezone.now().strftime('%B %d, %Y at %I:%M %p UTC'),
                'login_method': login_details.get('method', 'Email & Password') if login_details else 'Email & Password',
                'ip_address': login_details.get('ip_address', 'Unknown') if login_details else 'Unknown',
                'device': login_details.get('device', 'Unknown Device') if login_details else 'Unknown Device'
            }
            
            result = self.email_service.send_email(
                template_type='signin_notification',
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Login notification sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send login notification to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending login notification to {user.email}: {str(e)}")
            return False
    
    def trigger_subscription_success_email(self, user, subscription_details=None):
        """Send subscription success email"""
        try:
            custom_vars = {}
            if subscription_details:
                custom_vars.update({
                    'subscription_plan': subscription_details.get('plan_type', 'Premium Plan'),
                    'subscription_amount': subscription_details.get('amount_paid', 0),
                    'subscription_start': subscription_details.get('subscription_start', ''),
                    'subscription_end': subscription_details.get('subscription_end', ''),
                    'payment_reference': subscription_details.get('paystack_reference', ''),
                })
            
            result = self.email_service.send_email(
                template_type='subscription_success',
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Subscription success email sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send subscription success email to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending subscription success email to {user.email}: {str(e)}")
            return False
    
    def trigger_payment_failed_email(self, user, payment_details=None):
        """Send payment failed email"""
        try:
            custom_vars = {}
            if payment_details:
                custom_vars.update({
                    'payment_amount': payment_details.get('amount', 0),
                    'payment_reference': payment_details.get('reference', ''),
                    'failure_reason': payment_details.get('failure_reason', 'Payment processing failed'),
                    'retry_url': payment_details.get('retry_url', f"{getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')}/subscription"),
                })
            
            result = self.email_service.send_email(
                template_type='payment_failed',
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Payment failed email sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send payment failed email to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending payment failed email to {user.email}: {str(e)}")
            return False
    
    def trigger_subscription_renewal_reminder(self, user, subscription_details=None):
        """Send subscription renewal reminder"""
        try:
            custom_vars = {}
            if subscription_details:
                custom_vars.update({
                    'subscription_plan': subscription_details.get('plan_type', 'Premium Plan'),
                    'expiry_date': subscription_details.get('subscription_end', ''),
                    'days_remaining': subscription_details.get('days_remaining', 0),
                    'renewal_url': subscription_details.get('renewal_url', f"{getattr(settings, 'FRONTEND_URL', 'https://oxiworldforexacademy.com')}/subscription/renew"),
                    'subscription_amount': subscription_details.get('amount_paid', 0),
                })
            
            result = self.email_service.send_email(
                template_type='renewal_reminder',
                recipient_email=user.email,
                user=user,
                custom_vars=custom_vars,
                test_mode=False
            )
            if result:
                logger.info(f"Subscription renewal reminder sent to {user.email}")
                return True
            else:
                logger.warning(f"Failed to send subscription renewal reminder to {user.email}")
                return False
        except Exception as e:
            logger.error(f"Error sending subscription renewal reminder to {user.email}: {str(e)}")
            return False


# Initialize the automation service
automation_service = EmailAutomationService()

# Django Signals for Automatic Email Triggers

@receiver(post_save, sender=User)
def handle_user_creation(sender, instance, created, **kwargs):
    """
    Automatically send welcome email when a new user is created and verified
    """
    if created and instance.is_email_verified and instance.is_active:
        logger.info(f"New verified user created: {instance.email}")
        automation_service.trigger_welcome_email(instance)

@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """
    Send login notification email (optional - can be disabled for frequent logins)
    """
    # Check if this is the user's first login after registration
    if user.last_login is None or (
        user.last_login and 
        timezone.now() - user.last_login > timedelta(days=7)
    ):
        # Only send notification for first login or after 7+ days
        login_details = {
            'method': 'Email & Password',  # Can be enhanced to detect OAuth
            'ip_address': get_client_ip(request),
            'device': request.META.get('HTTP_USER_AGENT', 'Unknown Device')[:100]
        }
        automation_service.trigger_login_notification(user, login_details)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Helper functions for manual triggering

def send_welcome_email(user, test_mode=False):
    """
    Wrapper function for sending welcome emails
    Uses the new template system instead of hardcoded HTML
    """
    if test_mode:
        return EmailTemplateService().send_email(
            template_type='welcome',
            recipient_email=user.email,
            user=user,
            test_mode=True
        )
    else:
        return automation_service.trigger_welcome_email(user)

def send_verification_email(user, otp_code=None, test_mode=False):
    """
    Wrapper function for sending verification emails using email_verification template
    """
    from django.conf import settings
    
    custom_vars = {}
    
    # If OTP code is provided, include it
    if otp_code:
        custom_vars['verification_code'] = otp_code
        custom_vars['otp_code'] = otp_code
        custom_vars['otp'] = otp_code  # For compatibility
    
    # Generate verification URL if needed
    if not test_mode and hasattr(user, 'generate_email_verification_token'):
        token = user.generate_email_verification_token()
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={token}"
        custom_vars['verification_url'] = verification_url
    elif not custom_vars.get('verification_url'):
        # Provide a default verification URL for OTP-based verification
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        custom_vars['verification_url'] = f"{frontend_url}/verify-email"
    
    # Use email_verification template
    return EmailTemplateService().send_email(
        template_type='email_verification',
        recipient_email=user.email,
        user=user,
        custom_vars=custom_vars,
        test_mode=test_mode
    )

def send_password_reset_email(user, reset_token=None, reset_otp=None, test_mode=False):
    """
    Wrapper function for sending password reset emails
    """
    if test_mode:
        custom_vars = {}
        if reset_token:
            custom_vars['reset_token'] = reset_token
        if reset_otp:
            custom_vars['reset_code'] = reset_otp
        return EmailTemplateService().send_email(
            template_type='password_reset',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        return automation_service.trigger_password_reset_email(user, reset_token, reset_otp)

def send_login_notification(user, login_details=None, test_mode=False):
    """
    Wrapper function for sending login notifications
    """
    if test_mode:
        custom_vars = {
            'login_time': timezone.now().strftime('%B %d, %Y at %I:%M %p UTC'),
            'login_method': login_details.get('method', 'Email & Password') if login_details else 'Email & Password',
        }
        return EmailTemplateService().send_email(
            template_type='signin_notification',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        return automation_service.trigger_login_notification(user, login_details)

def send_subscription_success_email(user, subscription_details=None, test_mode=False):
    """
    Wrapper function for sending subscription success emails
    """
    if test_mode:
        custom_vars = {}
        if subscription_details:
            custom_vars.update({
                'subscription_plan': subscription_details.get('plan_type', 'Premium Plan'),
                'subscription_amount': subscription_details.get('amount_paid', 0),
            })
        return EmailTemplateService().send_email(
            template_type='subscription_success',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        return automation_service.trigger_subscription_success_email(user, subscription_details)

def send_payment_failed_email(user, payment_details=None, test_mode=False):
    """
    Wrapper function for sending payment failed emails
    """
    if test_mode:
        custom_vars = {}
        if payment_details:
            custom_vars.update({
                'payment_amount': payment_details.get('amount', 0),
                'failure_reason': payment_details.get('failure_reason', 'Payment processing failed'),
            })
        return EmailTemplateService().send_email(
            template_type='payment_failed',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        return automation_service.trigger_payment_failed_email(user, payment_details)

def send_subscription_renewal_reminder(user, subscription_details=None, test_mode=False):
    """
    Wrapper function for sending subscription renewal reminders
    """
    if test_mode:
        custom_vars = {}
        if subscription_details:
            custom_vars.update({
                'subscription_plan': subscription_details.get('plan_type', 'Premium Plan'),
                'days_remaining': subscription_details.get('days_remaining', 0),
            })
        return EmailTemplateService().send_email(
            template_type='renewal_reminder',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        return automation_service.trigger_subscription_renewal_reminder(user, subscription_details)

# ==============================
# MENTORSHIP EMAIL FUNCTIONS
# ==============================

def send_mentorship_welcome_email(user, mentorship_subscription, test_mode=False):
    """
    Send welcome email for mentorship subscription
    """
    if test_mode:
        custom_vars = {
            'plan_name': 'Premium Mentorship',
            'plan_type': 'mentorship_premium',
            'subscription_end': '90 days from now',
            'telegram_username': '@testuser',
            'sessions_included': 3,
            'premium_content_access': True,
            'duration_months': 3
        }
        return EmailTemplateService().send_email(
            template_type='mentorship_welcome',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        custom_vars = {
            'plan_name': mentorship_subscription.mentorship_plan.name,
            'plan_type': mentorship_subscription.mentorship_plan.plan_type,
            'subscription_end': mentorship_subscription.subscription_end.strftime("%B %d, %Y") if mentorship_subscription.subscription_end else "N/A",
            'telegram_username': mentorship_subscription.telegram_username,
            'sessions_included': mentorship_subscription.mentorship_plan.one_on_one_sessions,
            'premium_content_access': mentorship_subscription.mentorship_plan.premium_content_access,
            'duration_months': 3
        }
        return EmailTemplateService().send_email(
            template_type='mentorship_welcome',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=False
        )

def send_mentorship_expiry_reminder(user, mentorship_subscription, test_mode=False):
    """
    Send mentorship expiry reminder email
    """
    if test_mode:
        custom_vars = {
            'plan_name': 'Premium Mentorship',
            'expiry_date': '7 days from now',
            'days_remaining': 7,
            'sessions_remaining': 1
        }
        return EmailTemplateService().send_email(
            template_type='mentorship_expiry_reminder',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        custom_vars = {
            'plan_name': mentorship_subscription.mentorship_plan.name,
            'expiry_date': mentorship_subscription.subscription_end.strftime("%B %d, %Y") if mentorship_subscription.subscription_end else "N/A",
            'days_remaining': mentorship_subscription.days_remaining,
            'sessions_remaining': mentorship_subscription.sessions_remaining
        }
        return EmailTemplateService().send_email(
            template_type='mentorship_expiry_reminder',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=False
        )

def send_session_confirmation_email(user, session, test_mode=False):
    """
    Send 1-on-1 session confirmation email
    """
    if test_mode:
        custom_vars = {
            'session_type': 'Virtual',
            'scheduled_datetime': 'Tomorrow at 3:00 PM',
            'duration_minutes': 60,
            'meeting_link': 'https://zoom.us/j/123456789',
            'physical_location': '',
            'phone_number': '',
            'session_id': '12345'
        }
        return EmailTemplateService().send_email(
            template_type='session_confirmation',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=True
        )
    else:
        custom_vars = {
            'session_type': session.session_type.title(),
            'scheduled_datetime': session.scheduled_datetime.strftime("%B %d, %Y at %I:%M %p"),
            'duration_minutes': session.duration_minutes,
            'meeting_link': session.meeting_link,
            'physical_location': session.physical_location,
            'phone_number': session.phone_number,
            'session_id': str(session.id)
        }
        return EmailTemplateService().send_email(
            template_type='session_confirmation',
            recipient_email=user.email,
            user=user,
            custom_vars=custom_vars,
            test_mode=False
        )

def send_admin_session_notification(session, admin_email='admin@oxidane.com', test_mode=False):
    """
    Send admin notification for physical 1-on-1 sessions
    """
    if test_mode:
        custom_vars = {
            'user_name': 'Test User',
            'user_email': 'test@example.com',
            'session_type': 'Physical',
            'scheduled_datetime': 'Tomorrow at 3:00 PM',
            'duration_minutes': 60,
            'physical_location': 'Office Location',
            'phone_number': '+1234567890',
            'session_id': '12345',
            'plan_name': 'Premium Mentorship'
        }
    else:
        custom_vars = {
            'user_name': f"{session.mentorship_subscription.user.first_name} {session.mentorship_subscription.user.last_name}".strip(),
            'user_email': session.mentorship_subscription.user.email,
            'session_type': session.session_type.title(),
            'scheduled_datetime': session.scheduled_datetime.strftime("%B %d, %Y at %I:%M %p"),
            'duration_minutes': session.duration_minutes,
            'physical_location': session.physical_location,
            'phone_number': session.phone_number,
            'session_id': str(session.id),
            'plan_name': session.mentorship_subscription.mentorship_plan.name
        }
    
    # Create a temporary user object for admin email
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_user = User(email=admin_email, first_name='Admin')
    
    return EmailTemplateService().send_email(
        template_type='admin_session_notification',
        recipient_email=admin_email,
        user=admin_user,
        custom_vars=custom_vars,
        test_mode=test_mode
    )