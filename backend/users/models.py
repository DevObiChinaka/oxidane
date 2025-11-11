from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
import secrets
import random
import json
from datetime import timedelta

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
    
    # Subscription Integration (Phase 1.1)
    SUBSCRIPTION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('trialing', 'Trial Period'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('none', 'No Subscription'),
    ]
    
    current_plan = models.ForeignKey(
        'subscriptions.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribed_users',
        help_text='Current active subscription plan'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='none',
        db_index=True,
        help_text='Current subscription status'
    )
    subscription_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the current subscription period started'
    )
    subscription_end_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='When the current subscription period ends'
    )
    trial_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the trial period ends (if in trial)'
    )
    trial_used = models.BooleanField(
        default=False,
        help_text='Whether user has already used their trial period'
    )
    
    # Usage tracking
    usage_stats = models.JSONField(
        default=dict,
        blank=True,
        help_text='Track feature usage (e.g., {"signals_viewed": 10, "courses_enrolled": 2})'
    )
    
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

    # ========================================================================
    # Subscription Helper Methods (Phase 1.1)
    # ========================================================================
    
    def has_feature(self, feature_key):
        """
        Check if user has access to a specific feature based on their subscription plan.
        
        Args:
            feature_key (str): The unique key of the feature to check (e.g., 'view_premium_signals')
        
        Returns:
            bool: True if user has access to the feature, False otherwise
        
        Examples:
            >>> user.has_feature('view_premium_signals')
            True
            >>> user.has_feature('telegram_vip_group')
            False
        """
        # No plan = no premium features
        if not self.current_plan:
            return False
        
        # Check if subscription is active
        if not self.is_subscription_active():
            return False
        
        # Check if plan has the feature
        return self.current_plan.features.filter(
            key=feature_key,
            is_active=True
        ).exists()
    
    def can_access_course(self, course):
        """
        Check if user can access a specific course based on their subscription plan.
        
        Args:
            course: Course model instance
        
        Returns:
            bool: True if user can access the course, False otherwise
        
        Note:
            This method will be fully implemented in Task 1.3 when Enrollment model is created.
            For now, it provides basic plan-based access control.
        """
        # Check if course is free (will work with both old and new models)
        if hasattr(course, 'access_type') and course.access_type == 'free':
            return True
        
        # Backward compatibility: check old course_type field
        if hasattr(course, 'course_type') and course.course_type == 'free':
            return True
        
        # Check if user's plan grants access
        if not self.current_plan or not self.is_subscription_active():
            return False
        
        # If course has required_plans (will be added in Task 1.2)
        if hasattr(course, 'required_plans'):
            required_plans = course.required_plans.all()
            if not required_plans.exists():
                # No specific plans required = accessible to any paid plan
                return True
            # Check if user's plan is in required plans
            return required_plans.filter(id=self.current_plan.id).exists()
        
        # Default: premium courses require active subscription
        return True
    
    def get_plan_limits(self):
        """
        Get usage limits from the user's current subscription plan.
        
        Returns:
            dict: Plan limits (e.g., {"max_signals": 100, "max_courses": 5}) or empty dict
        
        Examples:
            >>> user.get_plan_limits()
            {'max_signals': 100, 'max_courses': 5, 'max_telegram_groups': 3}
        """
        if not self.current_plan:
            return {}
        
        return self.current_plan.limits or {}
    
    def is_subscription_active(self):
        """
        Check if user's subscription is currently active.
        
        Returns:
            bool: True if subscription is active or in trial period
        
        Note:
            Active means: status is 'active' or 'trialing' AND hasn't expired
        """
        if self.subscription_status not in ['active', 'trialing']:
            return False
        
        # Check trial period
        if self.subscription_status == 'trialing':
            if not self.trial_end_date:
                return False
            return timezone.now() < self.trial_end_date
        
        # Check subscription end date
        if self.subscription_status == 'active':
            if not self.subscription_end_date:
                # Lifetime or no end date = always active
                return True
            return timezone.now() < self.subscription_end_date
        
        return False
    
    def get_accessible_courses(self):
        """
        Get all courses the user can currently access.
        
        Returns:
            QuerySet: Course objects the user can access
        
        Note:
            This method will be fully implemented in Task 1.3 when Enrollment model is created.
            For now, it returns free courses only.
        """
        from courses.models import Course
        
        # For now, return free courses only
        # Full implementation will be added in Task 1.3 with Enrollment model
        if hasattr(Course, 'access_type'):
            return Course.objects.filter(access_type='free')
        else:
            # Backward compatibility
            return Course.objects.filter(course_type='free')
    
    def start_trial(self, plan):
        """
        Start a trial period for a subscription plan.
        
        Args:
            plan: SubscriptionPlan instance
        
        Returns:
            bool: True if trial started successfully
        
        Raises:
            ValueError: If user has already used their trial
        """
        if self.trial_used:
            raise ValueError("User has already used their trial period")
        
        if plan.trial_days <= 0:
            raise ValueError("This plan does not offer a trial period")
        
        self.current_plan = plan
        self.subscription_status = 'trialing'
        self.subscription_start_date = timezone.now()
        self.trial_end_date = timezone.now() + timedelta(days=plan.trial_days)
        self.trial_used = True
        self.save()
        
        return True
    
    def activate_subscription(self, plan, duration_days=None):
        """
        Activate a paid subscription for a plan.
        
        Args:
            plan: SubscriptionPlan instance
            duration_days (int, optional): Duration in days. If None, use plan's billing period
        
        Returns:
            bool: True if activated successfully
        """
        self.current_plan = plan
        self.subscription_status = 'active'
        self.subscription_start_date = timezone.now()
        
        # Calculate end date based on billing period or custom duration
        if duration_days:
            self.subscription_end_date = timezone.now() + timedelta(days=duration_days)
        elif plan.billing_period == 'lifetime':
            self.subscription_end_date = None  # No end date
        else:
            # Calculate based on billing period
            period_days = {
                'weekly': 7,
                'monthly': 30,
                'quarterly': 90,
                'yearly': 365,
            }
            days = period_days.get(plan.billing_period, 30)
            self.subscription_end_date = timezone.now() + timedelta(days=days)
        
        # Clear trial if it was active
        if self.subscription_status == 'trialing':
            self.trial_end_date = None
        
        self.save()
        return True
    
    def cancel_subscription(self):
        """
        Cancel the user's subscription.
        Subscription remains active until end date.
        
        Returns:
            bool: True if cancelled successfully
        """
        if self.subscription_status in ['active', 'trialing', 'past_due']:
            self.subscription_status = 'cancelled'
            self.save()
            return True
        return False
    
    def track_usage(self, feature_key, increment=1):
        """
        Track usage of a feature.
        
        Args:
            feature_key (str): Feature being used (e.g., 'signals_viewed')
            increment (int): Amount to increment (default: 1)
        """
        if not self.usage_stats:
            self.usage_stats = {}
        
        current_value = self.usage_stats.get(feature_key, 0)
        self.usage_stats[feature_key] = current_value + increment
        self.save(update_fields=['usage_stats', 'updated_at'])
    
    def reset_usage_stats(self):
        """Reset all usage statistics to zero."""
        self.usage_stats = {}
        self.save(update_fields=['usage_stats', 'updated_at'])

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
