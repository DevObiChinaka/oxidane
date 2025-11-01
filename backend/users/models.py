from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
import secrets
import random
import json

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_expires = models.DateTimeField(blank=True, null=True)
    email_verification_otp = models.CharField(max_length=6, blank=True, null=True)
    email_verification_otp_expires = models.DateTimeField(blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    password_reset_otp = models.CharField(max_length=6, blank=True, null=True)
    password_reset_otp_expires = models.DateTimeField(blank=True, null=True)
    telegram_user_id = models.BigIntegerField(null=True, blank=True, unique=True, help_text="Telegram user ID for bot operations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def generate_email_verification_otp(self):
        """Generate a 6-digit OTP for email verification"""
        self.email_verification_otp = str(random.randint(100000, 999999))
        self.email_verification_otp_expires = timezone.now() + timezone.timedelta(minutes=10)
        self.save()
        return self.email_verification_otp

    def verify_email_otp(self, otp):
        """Verify email with OTP and activate account"""
        if (self.email_verification_otp == otp and 
            self.email_verification_otp_expires and 
            timezone.now() < self.email_verification_otp_expires):
            self.is_email_verified = True
            self.is_active = True  # Activate account after verification
            self.email_verification_otp = None
            self.email_verification_otp_expires = None
            self.save()
            return True
        return False

    def generate_password_reset_otp(self):
        """Generate a 6-digit OTP for password reset"""
        self.password_reset_otp = str(random.randint(100000, 999999))
        self.password_reset_otp_expires = timezone.now() + timezone.timedelta(minutes=10)
        self.save()
        return self.password_reset_otp

    def verify_password_reset_otp(self, otp):
        """Verify password reset OTP"""
        if (self.password_reset_otp == otp and 
            self.password_reset_otp_expires and 
            timezone.now() < self.password_reset_otp_expires):
            return True
        return False

    def generate_email_verification_token(self):
        """Generate a secure token for email verification"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        """Generate a secure token for password reset"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        return self.password_reset_token

    def verify_email(self, token):
        """Verify email with token"""
        if (self.email_verification_token == token and 
            self.email_verification_expires and 
            timezone.now() < self.email_verification_expires):
            self.is_email_verified = True
            self.email_verification_token = None
            self.email_verification_expires = None
            self.save()
            return True
        return False

    def reset_password(self, token, new_password):
        """Reset password with token"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            timezone.now() < self.password_reset_expires):
            from django.contrib.auth.hashers import make_password
            self.password = make_password(new_password)
            self.password_reset_token = None
            self.password_reset_expires = None
            self.save()
            return True
        return False

class OAuthProvider(models.Model):
    PROVIDER_CHOICES = [
        ('google', 'Google'),
        # Facebook and Twitter removed for simplicity
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauth_providers')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=100)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['provider', 'provider_user_id']
    
    def __str__(self):
        return f"{self.user.email} - {self.provider}"


class EmailTemplate(models.Model):
    """Email template model for dynamic email management"""
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('subscription_success', 'Subscription Success'),
        ('subscription_expiry', 'Subscription Expiry Warning'),
        ('subscription_renewal', 'Subscription Renewal'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('payment_refunded', 'Payment Refunded'),
        ('renewal_reminder', 'Renewal Reminder'),
        ('telegram_added', 'Telegram Group Added'),
        ('telegram_removed', 'Telegram Group Removed'),
        ('signin_notification', 'Sign-in Notification'),
        ('password_reset', 'Password Reset'),
        ('email_verification', 'Email Verification'),
        ('custom', 'Custom Template'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Template name for identification")
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, help_text="Type of email template")
    subject_template = models.CharField(max_length=200, help_text="Email subject with variables like {{user.name}}")
    html_content = models.TextField(help_text="HTML email content with variables")
    text_content = models.TextField(blank=True, help_text="Plain text version (optional)")
    
    # Template metadata
    description = models.TextField(blank=True, help_text="Description of when this template is used")
    available_variables = models.JSONField(default=dict, help_text="Available variables for this template")
    
    # Template settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_default = models.BooleanField(default=False, help_text="Default template for this type")
    
    # Email settings
    from_email = models.EmailField(blank=True, help_text="Override default from email")
    from_name = models.CharField(max_length=100, blank=True, help_text="From name for email")
    
    # Analytics
    sent_count = models.PositiveIntegerField(default=0, help_text="Number of emails sent using this template")
    last_used = models.DateTimeField(blank=True, null=True, help_text="Last time this template was used")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_templates')
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [('template_type', 'is_default')]  # Only one default per type
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def get_default_variables(self):
        """Get default variables based on template type"""
        base_variables = {
            'user.first_name': 'User\'s first name',
            'user.last_name': 'User\'s last name', 
            'user.email': 'User\'s email address',
            'company_name': 'Company name (OxiWorld)',
            'current_date': 'Current date',
            'support_email': 'Support email address',
        }
        
        type_specific_variables = {
            'subscription_success': {
                'subscription.plan_type': 'Subscription plan type',
                'subscription.amount': 'Subscription amount',
                'subscription.start_date': 'Subscription start date',
                'subscription.end_date': 'Subscription end date',
                'telegram_group': 'Telegram group name',
            },
            'payment_success': {
                'payment.amount': 'Payment amount',
                'payment.reference': 'Payment reference',
                'payment.date': 'Payment date',
            },
            'renewal_reminder': {
                'days_remaining': 'Days until expiry',
                'renewal_link': 'Renewal link',
            }
        }
        
        variables = base_variables.copy()
        if self.template_type in type_specific_variables:
            variables.update(type_specific_variables[self.template_type])
        
        return variables
    
    def save(self, *args, **kwargs):
        # Set default variables if not set
        if not self.available_variables:
            self.available_variables = self.get_default_variables()
        
        # If this is set as default, remove default from others of same type
        if self.is_default:
            EmailTemplate.objects.filter(
                template_type=self.template_type, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_template_for_type(cls, template_type):
        """Get the default template for a specific type"""
        return cls.objects.filter(
            template_type=template_type,
            status='active',
            is_default=True
        ).first() or cls.objects.filter(
            template_type=template_type,
            status='active'
        ).first()


class EmailLog(models.Model):
    """Log of sent emails for tracking and analytics"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, related_name='email_logs')
    recipient_email = models.EmailField()
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_emails')
    
    # Email content (at time of sending)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Sending details
    from_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    variables_used = models.JSONField(default=dict, help_text="Variables that were substituted")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.status}"


class UserPreferences(models.Model):
    """User notification and preference settings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Email notification preferences
    email_login = models.BooleanField(default=True, help_text="Notify on login")
    course_updates = models.BooleanField(default=True, help_text="Notify about course updates")
    subscription_renewal = models.BooleanField(default=True, help_text="Notify before subscription renewal")
    promotional_emails = models.BooleanField(default=False, help_text="Receive promotional emails")
    signal_alerts = models.BooleanField(default=True, help_text="Receive trading signal notifications")
    
    # Additional preferences can be added here
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
