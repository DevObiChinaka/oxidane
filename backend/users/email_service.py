# Email Template Service
# Advanced email template processing and sending

import re
from datetime import datetime
from django.core.mail import send_mail
from django.template import Context, Template
from django.conf import settings
from django.utils import timezone
from .models import EmailTemplate, EmailLog, User
import logging

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service class for processing and sending email templates"""
    
    def __init__(self):
        # Try to get email configuration from database (singleton)
        try:
            from subscriptions.models import EmailConfiguration
            email_config = EmailConfiguration.get_instance()
            
            if email_config.is_enabled and email_config.from_email:
                # Use database configuration
                self.default_from_email = email_config.from_email
                self.company_name = email_config.from_name or 'OxiWorld'
            else:
                # Fallback to settings.py
                self.default_from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@oxiworld.com')
                self.company_name = getattr(settings, 'COMPANY_NAME', 'OxiWorld')
        except Exception as e:
            # If EmailConfiguration doesn't exist or fails, use settings.py
            logger.warning(f"Could not load EmailConfiguration, using settings.py: {e}")
            self.default_from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@oxiworld.com')
            self.company_name = getattr(settings, 'COMPANY_NAME', 'OxiWorld')
        
        self.support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@oxiworld.com')
    
    def get_template(self, template_type, template_name=None):
        """Get active template for given type, optionally by name"""
        if template_name:
            # Get specific template by name and type
            template = EmailTemplate.objects.filter(
                template_type=template_type,
                name=template_name,
                status='active'
            ).first()
        else:
            # Get default template for type
            template = EmailTemplate.get_template_for_type(template_type)
            
        if not template:
            logger.warning(f"No active template found for type: {template_type}" + 
                         (f" with name: {template_name}" if template_name else ""))
            return None
        return template
    
    def prepare_variables(self, user=None, subscription=None, payment=None, custom_vars=None):
        """Prepare variables for template substitution"""
        variables = {
            'company_name': self.company_name,
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'support_email': self.support_email,
            'current_year': datetime.now().year,
        }
        
        # User variables
        if user:
            variables.update({
                'user.first_name': user.first_name or 'Valued Customer',
                'user.last_name': user.last_name or '',
                'user.full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'user.email': user.email,
                'user.username': user.username or user.email.split('@')[0],
            })
        
        # Subscription variables
        if subscription:
            variables.update({
                'subscription.plan_type': subscription.plan_type.title(),
                'subscription.amount': f"${subscription.amount_paid:.2f}",
                'subscription.currency': subscription.currency,
                'subscription.reference': subscription.paystack_reference,
                'subscription.start_date': subscription.subscription_start.strftime('%B %d, %Y') if subscription.subscription_start else '',
                'subscription.end_date': subscription.subscription_end.strftime('%B %d, %Y') if subscription.subscription_end else '',
                'subscription.status': subscription.payment_status.title(),
                'telegram_group': subscription.telegram_group_name or 'Premium Trading Group',
            })
            
            # Calculate days remaining
            if subscription.subscription_end:
                days_remaining = (subscription.subscription_end.date() - datetime.now().date()).days
                variables['days_remaining'] = max(0, days_remaining)
        
        # Payment variables
        if payment:
            variables.update({
                'payment.amount': f"${payment.get('amount', 0):.2f}",
                'payment.reference': payment.get('reference', ''),
                'payment.date': payment.get('date', datetime.now().strftime('%B %d, %Y')),
                'payment.status': payment.get('status', '').title(),
            })
        
        # Custom variables
        if custom_vars:
            variables.update(custom_vars)
        
        return variables
    
    def substitute_variables(self, content, variables):
        """Replace variables in content with actual values"""
        if not content:
            return content
            
        # Simple variable substitution using regex
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, f'{{{{{var_name}}}}}'))
        
        # Replace {{variable}} with actual values
        result = re.sub(r'\{\{([^}]+)\}\}', replace_var, content)
        return result
    
    def send_email(self, template_type, recipient_email, user=None, subscription=None, 
                   payment=None, custom_vars=None, test_mode=False, template_name=None):
        """Send email using template"""
        
        try:
            # Get template
            template = self.get_template(template_type, template_name)
            if not template:
                # Use fallback email instead of raising error
                logger.warning(f"No template found for type: {template_type}, using fallback")
                return self._send_fallback_email(
                    template_type=template_type,
                    recipient_email=recipient_email,
                    user=user,
                    custom_vars=custom_vars,
                    test_mode=test_mode
                )
            
            # Prepare variables
            variables = self.prepare_variables(user, subscription, payment, custom_vars)
            
            # Substitute variables in subject and content
            subject = self.substitute_variables(template.subject_template, variables)
            html_content = self.substitute_variables(template.html_content, variables)
            text_content = self.substitute_variables(template.text_content, variables) if template.text_content else None
            
            # Determine from email
            base_from_email = template.from_email or self.default_from_email
            from_name = template.from_name or self.company_name
            
            # Debug logging
            logger.info(f"Email formatting debug:")
            logger.info(f"  template.from_email: '{template.from_email}'")
            logger.info(f"  self.default_from_email: '{self.default_from_email}'")
            logger.info(f"  base_from_email: '{base_from_email}'")
            logger.info(f"  template.from_name: '{template.from_name}'")
            logger.info(f"  self.company_name: '{self.company_name}'")
            logger.info(f"  from_name: '{from_name}'")
            
            # Handle from email formatting
            if '<' in base_from_email and '>' in base_from_email:
                # Already formatted (e.g., "Name <email@domain.com>"), use as-is
                from_email = base_from_email
            elif from_name:
                # Plain email address, wrap with name
                from_email = f"{from_name} <{base_from_email}>"
            else:
                # Just use the email address
                from_email = base_from_email
                
            logger.info(f"  final from_email: '{from_email}'")
            
            # Create email log entry (only if not test mode)
            email_log = None
            if not test_mode:
                # Only assign recipient_user if it's a real Django User instance
                recipient_user = user if isinstance(user, User) else None
                
                email_log = EmailLog.objects.create(
                    template=template,
                    recipient_email=recipient_email,
                    recipient_user=recipient_user,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content or '',
                    from_email=from_email,
                    variables_used=variables,
                    status='pending'
                )
            
            # Send email (skip in test mode)
            if not test_mode:
                success = send_mail(
                    subject=subject,
                    message=text_content or self.html_to_text(html_content),
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    html_message=html_content,
                    fail_silently=False
                )
                
                if success and email_log:
                    email_log.status = 'sent'
                    email_log.sent_at = timezone.now()
                    email_log.save()
                    
                    # Update template usage stats
                    template.sent_count += 1
                    template.last_used = timezone.now()
                    template.save(update_fields=['sent_count', 'last_used'])
                elif email_log:
                    email_log.status = 'failed'
                    email_log.error_message = 'Failed to send email'
                    email_log.save()
            
            logger.info(f"Email {'sent' if not test_mode else 'preview generated'} successfully: {template_type} to {recipient_email}")
            
            return {
                'success': True,
                'email_log_id': str(email_log.id) if email_log else None,
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content or '',
                'variables_used': variables,
                'test_mode': test_mode
            }
            
        except Exception as e:
            logger.error(f"Failed to send email {template_type} to {recipient_email}: {str(e)}")
            
            # Create failed log entry (only if not test mode and user is valid)
            if not test_mode:
                recipient_user = user if isinstance(user, User) else None
                EmailLog.objects.create(
                    template=template if 'template' in locals() else None,
                    recipient_email=recipient_email,
                    recipient_user=recipient_user,
                    subject=subject if 'subject' in locals() else f"Failed {template_type}",
                    html_content=html_content if 'html_content' in locals() else '',
                    from_email=from_email if 'from_email' in locals() else self.default_from_email,
                    status='failed',
                    error_message=str(e),
                    variables_used=variables if 'variables' in locals() else {}
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def html_to_text(self, html_content):
        """Convert HTML to plain text for fallback"""
        # Simple HTML to text conversion
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _send_fallback_email(self, template_type, recipient_email, user=None, custom_vars=None, test_mode=False):
        """Send a fallback email when no template exists"""
        logger.info(f"Sending fallback email for type: {template_type}")
        
        # Prepare user info
        first_name = 'there'
        if user:
            first_name = user.first_name or user.username or 'there'
        
        # Build fallback subject and content based on template type
        if template_type in ['user_login_otp', 'email_verification']:
            otp_code = custom_vars.get('verification_code') or custom_vars.get('otp_code', '------')
            subject = f"🔐 {self.company_name} - Email Verification Code"
            
            html_content = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{subject}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h1 style="color: white; margin: 0;">🔐 {self.company_name}</h1>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333;">Hi {first_name}!</h2>
                    <p>Your verification code is:</p>
                    
                    <div style="background: #f8f9ff; border: 2px solid #667eea; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <h1 style="color: #667eea; font-size: 36px; margin: 0; letter-spacing: 8px; font-family: 'Courier New', monospace;">{otp_code}</h1>
                    </div>
                    
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <p>© {datetime.now().year} {self.company_name}. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
{subject}

Hi {first_name}!

Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

© {datetime.now().year} {self.company_name}. All rights reserved.
            """
        
        elif template_type == 'welcome':
            subject = f"🎉 Welcome to {self.company_name}!"
            
            html_content = f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{subject}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                    <h1 style="color: white; margin: 0;">🎉 Welcome to {self.company_name}!</h1>
                </div>
                
                <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333;">Hi {first_name}!</h2>
                    <p>Welcome to {self.company_name}! We're excited to have you on board.</p>
                    <p>Your account has been successfully created and verified.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                            Get Started →
                        </a>
                    </div>
                    
                    <p>If you have any questions, feel free to contact us at <a href="mailto:{self.support_email}">{self.support_email}</a>.</p>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
                    <p>© {datetime.now().year} {self.company_name}. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
{subject}

Hi {first_name}!

Welcome to {self.company_name}! We're excited to have you on board.

Your account has been successfully created and verified.

Get started: http://localhost:3000/dashboard

If you have any questions, feel free to contact us at {self.support_email}.

© {datetime.now().year} {self.company_name}. All rights reserved.
            """
        
        else:
            # Generic fallback
            subject = f"{self.company_name} - Notification"
            html_content = f"<p>Hi {first_name},</p><p>This is a notification from {self.company_name}.</p>"
            text_content = f"Hi {first_name},\n\nThis is a notification from {self.company_name}."
        
        # Send the email (skip in test mode)
        if not test_mode:
            try:
                # Format from_email properly
                # Check if default_from_email already has a name in it (e.g., "Name <email@domain.com>")
                if '<' in self.default_from_email and '>' in self.default_from_email:
                    # Already formatted, use as-is
                    from_email = self.default_from_email
                else:
                    # Just an email address, add company name
                    from_email = f"{self.company_name} <{self.default_from_email}>"
                
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    html_message=html_content,
                    fail_silently=False
                )
                logger.info(f"Fallback email sent successfully to {recipient_email}")
                return True
            except Exception as e:
                logger.error(f"Failed to send fallback email: {str(e)}")
                return False
        else:
            logger.info(f"Test mode: Fallback email preview generated")
            return True
    
    def preview_email(self, template_id, sample_data=None):
        """Preview email with sample data"""
        try:
            template = EmailTemplate.objects.get(id=template_id)
            
            # Use sample data or defaults
            if not sample_data:
                sample_data = {
                    'user': {
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john.doe@example.com'
                    },
                    'subscription': {
                        'plan_type': 'monthly',
                        'amount_paid': 99.00,
                        'currency': 'USD'
                    }
                }
            
            # Create User object for variable preparation
            sample_user = type('User', (), {
                'first_name': sample_data.get('user', {}).get('first_name', 'John'),
                'last_name': sample_data.get('user', {}).get('last_name', 'Doe'),
                'email': sample_data.get('user', {}).get('email', 'john.doe@example.com'),
                'username': 'johndoe'
            })()
            
            # Prepare variables
            variables = self.prepare_variables(user=sample_user, custom_vars=sample_data.get('custom', {}))
            
            # Generate preview
            subject = self.substitute_variables(template.subject_template, variables)
            html_content = self.substitute_variables(template.html_content, variables)
            
            return {
                'success': True,
                'subject': subject,
                'html_content': html_content,
                'variables_used': variables,
                'template_name': template.name
            }
            
        except EmailTemplate.DoesNotExist:
            return {
                'success': False,
                'error': 'Template not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions for common email types
def send_welcome_email(user, test_mode=False):
    """Send welcome email to new user"""
    service = EmailTemplateService()
    return service.send_email(
        template_type='welcome',
        recipient_email=user.email,
        user=user,
        test_mode=test_mode
    )


def send_subscription_success_email(user, subscription, test_mode=False):
    """Send subscription success email"""
    service = EmailTemplateService()
    return service.send_email(
        template_type='subscription_success',
        recipient_email=user.email,
        user=user,
        subscription=subscription,
        test_mode=test_mode
    )


def send_payment_failed_email(user, payment_details, test_mode=False):
    """Send payment failed email"""
    service = EmailTemplateService()
    return service.send_email(
        template_type='payment_failed',
        recipient_email=user.email,
        user=user,
        payment=payment_details,
        test_mode=test_mode
    )


def send_renewal_reminder_email(user, subscription, days_remaining, test_mode=False):
    """Send renewal reminder email"""
    service = EmailTemplateService()
    custom_vars = {
        'days_remaining': days_remaining,
        'renewal_link': f"https://oxiworld.com/renew/{subscription.id}"
    }
    return service.send_email(
        template_type='renewal_reminder',
        recipient_email=user.email,
        user=user,
        subscription=subscription,
        custom_vars=custom_vars,
        test_mode=test_mode
    )