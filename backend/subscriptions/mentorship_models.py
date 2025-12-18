# Mentorship System Models
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta

class MentorshipPlan(models.Model):
    """Mentorship subscription plans with premium content access"""
    PLAN_TYPES = [
        ('mentorship_basic', 'Basic Mentorship'),
        ('mentorship_premium', 'Premium Mentorship + 1-on-1'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('NGN', 'Nigerian Naira'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=100, help_text="Display name for users")
    description = models.TextField(help_text="Plan description and features")
    
    # Pricing (3-month duration)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for 3-month mentorship")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Plan features
    premium_content_access = models.BooleanField(default=True, help_text="Access to premium courses")
    telegram_group_access = models.BooleanField(default=True, help_text="Access to mentorship Telegram group")
    one_on_one_sessions = models.PositiveIntegerField(default=0, help_text="Number of 1-on-1 sessions included")
    session_duration_minutes = models.PositiveIntegerField(default=60, help_text="Duration of each 1-on-1 session")
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Features list for display
    features_list = models.JSONField(default=list, help_text="List of plan features")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'price']
        
    def __str__(self):
        return f"{self.name} - {self.currency} {self.price}"

class MentorshipSubscription(models.Model):
    """User mentorship subscriptions with 3-month duration"""
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('verified', 'Payment Verified'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    TELEGRAM_STATUS = [
        ('not_added', 'Not Added to Group'),
        ('pending_add', 'Pending Addition'),
        ('added', 'Added to Group'),
        ('removed', 'Removed from Group'),
        ('failed_add', 'Failed to Add'),
    ]
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_subscriptions')
    
    # Plan details
    mentorship_plan = models.ForeignKey(MentorshipPlan, on_delete=models.PROTECT)
    
    # Payment information
    paystack_reference = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Subscription period (3 months)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    subscription_status = models.CharField(max_length=10, choices=SUBSCRIPTION_STATUS, default='active')
    
    # Telegram integration
    telegram_username = models.CharField(max_length=100, help_text="User's Telegram username")
    telegram_group_name = models.CharField(max_length=100, default='OxiWorld_Mentorship')
    telegram_status = models.CharField(max_length=15, choices=TELEGRAM_STATUS, default='not_added')
    telegram_added_at = models.DateTimeField(null=True, blank=True)
    telegram_removal_scheduled = models.DateTimeField(null=True, blank=True, help_text="When to remove from group")
    
    # 1-on-1 Session tracking
    sessions_used = models.PositiveIntegerField(default=0)
    sessions_remaining = models.PositiveIntegerField(default=0)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Internal admin notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mentorship_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['payment_status', '-created_at']),
            models.Index(fields=['subscription_status']),
            models.Index(fields=['subscription_start', 'subscription_end']),
            models.Index(fields=['telegram_status']),
            models.Index(fields=['telegram_removal_scheduled']),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.mentorship_plan.name} - {self.subscription_status}"
    
    @property
    def is_active(self):
        """Check if mentorship is currently active"""
        if self.payment_status != 'verified':
            return False
        if self.subscription_status != 'active':
            return False
        if not self.subscription_end:
            return False
        return timezone.now() <= self.subscription_end
    
    @property
    def days_remaining(self):
        """Get days remaining in mentorship"""
        if not self.is_active:
            return 0
        delta = self.subscription_end - timezone.now()
        return max(0, delta.days)
    
    def mark_payment_verified(self):
        """Mark payment as verified and set 3-month subscription dates"""
        self.payment_status = 'verified'
        self.payment_verified_at = timezone.now()
        self.subscription_start = timezone.now()
        
        # Set end date to 3 months (90 days)
        self.subscription_end = self.subscription_start + timedelta(days=90)
        
        # Schedule telegram removal 1 day after expiry
        self.telegram_removal_scheduled = self.subscription_end + timedelta(days=1)
        
        # Set available sessions based on plan
        self.sessions_remaining = self.mentorship_plan.one_on_one_sessions
        
        # Mark for Telegram addition
        self.telegram_status = 'pending_add'
        self.subscription_status = 'active'
        self.save()
        
        # Grant premium content access
        self.grant_premium_access()
        
        # Create Telegram management task
        self.create_telegram_task('add')
    
    def grant_premium_access(self):
        """Grant access to all premium courses"""
        from courses.models import Course, CourseAccess
        
        premium_courses = Course.objects.filter(course_type='premium', status='published')
        
        for course in premium_courses:
            CourseAccess.objects.get_or_create(
                user=self.user,
                course=course,
                defaults={
                    'access_expires_at': self.subscription_end,
                    'download_enabled': True
                }
            )
    
    def revoke_premium_access(self):
        """Revoke premium course access when subscription ends"""
        from courses.models import CourseAccess
        
        CourseAccess.objects.filter(
            user=self.user,
            access_expires_at=self.subscription_end
        ).delete()
    
    def create_telegram_task(self, action_type):
        """Create telegram management task"""
        MentorshipTelegramTask.objects.create(
            mentorship_subscription=self,
            action_type=action_type,
            telegram_username=self.telegram_username,
            telegram_group=self.telegram_group_name,
            scheduled_for=timezone.now() if action_type == 'add' else self.telegram_removal_scheduled
        )
    
    def schedule_expiry_tasks(self):
        """Schedule tasks for subscription expiry"""
        if self.subscription_end:
            # Create telegram removal task
            self.create_telegram_task('remove')
            
            # Mark subscription as expired
            self.subscription_status = 'expired'
            self.save()
    
    def use_session(self):
        """Use one 1-on-1 session"""
        if self.sessions_remaining > 0:
            self.sessions_remaining -= 1
            self.sessions_used += 1
            self.save()
            return True
        return False

class OneOnOneSession(models.Model):
    """Track 1-on-1 mentorship sessions"""
    SESSION_TYPES = [
        ('virtual', 'Virtual Meeting'),
        ('physical', 'Physical Meeting'),
        ('phone', 'Phone Call'),
    ]
    
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentorship_subscription = models.ForeignKey(MentorshipSubscription, on_delete=models.CASCADE, related_name='sessions')
    
    # Session details
    session_type = models.CharField(max_length=10, choices=SESSION_TYPES, default='virtual')
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Location/meeting info
    meeting_link = models.URLField(blank=True, help_text="Zoom/Meet link for virtual sessions")
    physical_location = models.TextField(blank=True, help_text="Address for physical meetings")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Phone number for call sessions")
    
    # Status and notes
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default='scheduled')
    session_notes = models.TextField(blank=True, help_text="Notes from the session")
    admin_notes = models.TextField(blank=True, help_text="Internal admin notes")
    
    # Admin notification flags
    admin_notified = models.BooleanField(default=False, help_text="Has admin been notified of this session?")
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_datetime']
        indexes = [
            models.Index(fields=['mentorship_subscription', '-scheduled_datetime']),
            models.Index(fields=['session_type', 'status']),
            models.Index(fields=['scheduled_datetime']),
            models.Index(fields=['admin_notified']),
        ]
        
    def __str__(self):
        return f"{self.mentorship_subscription.user.email} - {self.session_type} - {self.scheduled_datetime}"
    
    def mark_completed(self, notes=""):
        """Mark session as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.session_notes = notes
        self.save()
    
    def send_admin_notification(self):
        """Send notification to admin about upcoming/new session"""
        if not self.admin_notified and self.session_type == 'physical':
            # TODO: Send email to admin about physical session
            self.admin_notified = True
            self.notification_sent_at = timezone.now()
            self.save()

class MentorshipTelegramTask(models.Model):
    """Queue system for Telegram group management for mentorship"""
    ACTION_TYPES = [
        ('add', 'Add User to Mentorship Group'),
        ('remove', 'Remove User from Mentorship Group'),
    ]
    
    ACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentorship_subscription = models.ForeignKey(MentorshipSubscription, on_delete=models.CASCADE)
    
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    telegram_username = models.CharField(max_length=100)
    telegram_group = models.CharField(max_length=100, default='OxiWorld_Mentorship')
    
    # Scheduling
    scheduled_for = models.DateTimeField(help_text="When to execute this task")
    
    status = models.CharField(max_length=10, choices=ACTION_STATUS, default='pending')
    error_message = models.TextField(blank=True, help_text="Error details if task failed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentorship_telegram_tasks')
    
    class Meta:
        ordering = ['scheduled_for', 'created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['action_type', 'status']),
            models.Index(fields=['mentorship_subscription']),
        ]
        
    def __str__(self):
        return f"{self.action_type.title()} @{self.telegram_username} - {self.status}"
    
    @property
    def is_due(self):
        """Check if task is due for execution"""
        return self.scheduled_for <= timezone.now() and self.status == 'pending'

class MentorshipAnalytics(models.Model):
    """Analytics for mentorship program"""
    date = models.DateField(unique=True)
    
    # Subscription metrics
    new_mentorship_subscriptions = models.PositiveIntegerField(default=0)
    active_mentorship_subscriptions = models.PositiveIntegerField(default=0)
    expired_mentorship_subscriptions = models.PositiveIntegerField(default=0)
    
    # Revenue metrics
    mentorship_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Session metrics
    sessions_scheduled = models.PositiveIntegerField(default=0)
    sessions_completed = models.PositiveIntegerField(default=0)
    sessions_cancelled = models.PositiveIntegerField(default=0)
    
    # Content access metrics
    premium_content_views = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Mentorship Analytics - {self.date}"