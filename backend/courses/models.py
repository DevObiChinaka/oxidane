# Course and content management models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid
from .validators import (
    validate_video_file_size, 
    validate_video_file_type,
    validate_resource_file_size,
    validate_resource_file_type
)

User = get_user_model()


class CourseCategory(models.Model):
    """Categories for organizing courses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
    
    def __str__(self):
        return self.name
    
    @property
    def course_count(self):
        return self.courses.filter(status='published').count()


class Course(models.Model):
    COURSE_TYPES = [
        ('free', 'Free Course'),
        ('premium', 'Premium Course'),
    ]
    
    ACCESS_TYPES = [
        ('free', 'Free - Available to all users'),
        ('plan_based', 'Plan-based - Requires specific subscription plan'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120, help_text="Full course title for display (max 120 chars)")
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for course cards")
    
    # Category
    category = models.ForeignKey(
        CourseCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='courses',
        help_text="Course category for organization"
    )
    
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES, default='free')
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, default='beginner')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Phase 1.2: Subscription Integration Fields
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES,
        default='free',
        help_text='How users can access this course'
    )
    required_plans = models.ManyToManyField(
        'subscriptions.SubscriptionPlan',
        related_name='courses',
        blank=True,
        help_text='Subscription plans that grant access to this course (for plan_based access)'
    )
    
    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO optimized title (max 60 chars) - auto-generated if empty")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (max 160 chars)")
    keywords = models.CharField(max_length=200, blank=True, help_text="SEO keywords, comma separated")
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    trailer_video_url = models.URLField(blank=True, help_text="YouTube trailer video URL")
    
    # Course settings
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes", default=0)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate meta_title if not provided
        if not self.meta_title and self.title:
            self.meta_title = self.get_seo_title()
        
        # Phase 1.2: Sync access_type with course_type for backward compatibility
        # Only sync if access_type hasn't been explicitly set
        if not self.pk or self.access_type == 'free':  # New course or default value
            self.sync_access_type_with_course_type()
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_seo_title(self):
        """Generate SEO-optimized title from the display title"""
        if not self.title:
            return ''
        
        # Create a shortened version for SEO
        base_suffix = " | OxiWorld Academy"
        max_title_length = 60 - len(base_suffix)
        
        if len(self.title) <= max_title_length:
            return f"{self.title}{base_suffix}"
        else:
            # Truncate at word boundary
            truncated = self.title[:max_title_length-3]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            return f"{truncated}...{base_suffix}"
    
    @property
    def display_title(self):
        """Return the full display title"""
        return self.title
    
    @property
    def seo_title(self):
        """Return the SEO title, generating one if not set"""
        return self.meta_title or self.get_seo_title()
    
    @property
    def total_lessons(self):
        return self.lessons.count()
    
    @property
    def total_duration(self):
        return self.lessons.aggregate(
            total=models.Sum('duration')
        )['total'] or 0
    
    # Phase 1.2: Subscription Integration Methods
    
    def is_accessible_by_user(self, user):
        """
        Check if a user can access this course based on subscription/purchase.
        
        Args:
            user: User instance to check access for
            
        Returns:
            bool: True if user can access the course, False otherwise
        """
        if not user or not user.is_authenticated:
            # Anonymous users can only access free courses
            return self.access_type == 'free'
        
        # Check access based on access_type
        if self.access_type == 'free':
            return True
        
        elif self.access_type == 'plan_based':
            # User needs an active subscription with one of the required plans
            if not user.current_plan or not user.is_subscription_active():
                return False
            
            # Check if user's plan is in the required plans
            required_plan_ids = self.required_plans.values_list('id', flat=True)
            return user.current_plan.id in required_plan_ids
        
        return False
    
    def get_required_plan_names(self):
        """
        Get list of plan names that grant access to this course.
        
        Returns:
            list: List of plan names, or empty list if not plan_based
        """
        if self.access_type != 'plan_based':
            return []
        
        return list(self.required_plans.values_list('name', flat=True))
    
    def sync_access_type_with_course_type(self):
        """
        Sync the new access_type field with the legacy course_type field.
        This maintains backward compatibility during the migration period.
        
        Called automatically in save() if access_type is not explicitly set.
        """
        if self.course_type == 'free':
            self.access_type = 'free'
        elif self.course_type == 'premium':
            # Premium courses default to plan_based
            self.access_type = 'plan_based'
    
    def is_free(self):
        """Check if this is a free course"""
        return self.access_type == 'free'
    
    def requires_subscription(self):
        """Check if this course requires an active subscription"""
        return self.access_type == 'plan_based'

class Lesson(models.Model):
    VIDEO_SOURCES = [
        ('upload', 'Uploaded Video'),
        ('youtube', 'YouTube Video'),
        ('vimeo', 'Vimeo Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    
    # Video content
    video_source = models.CharField(max_length=10, choices=VIDEO_SOURCES, default='upload')
    video_file = models.FileField(
        upload_to='lesson_videos/', 
        null=True, 
        blank=True,
        validators=[validate_video_file_size, validate_video_file_type],
        help_text='Max 500MB. Formats: MP4, MOV, AVI, WebM. For longer videos, use YouTube or Vimeo.'
    )
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo URL")
    youtube_video_id = models.CharField(max_length=20, blank=True)
    
    # Lesson settings
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=0)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False, help_text="Can be viewed by non-premium users")
    
    # Additional resources
    lesson_notes = models.TextField(blank=True, help_text="PDF notes or additional text content")
    downloadable_resources = models.FileField(
        upload_to='lesson_resources/', 
        null=True, 
        blank=True,
        validators=[validate_resource_file_size, validate_resource_file_type],
        help_text='Max 50MB. Formats: PDF, Office docs, images, ZIP archives.'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'slug']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Extract YouTube video ID from URL
        if self.video_source == 'youtube' and self.video_url:
            import re
            youtube_regex = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)'
            match = re.search(youtube_regex, self.video_url)
            if match:
                self.youtube_video_id = match.group(1)
        
        super().save(*args, **kwargs)

class CourseAccess(models.Model):
    """
    Track which users have access to which courses.
    Integrates with subscription system to manage course access via plans or direct purchase.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    # Access tracking
    access_granted_at = models.DateTimeField(auto_now_add=True)
    access_expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='When access expires. Null = lifetime access'
    )
    
    # Phase 1.3: Subscription Integration Fields
    access_granted_by = models.CharField(
        max_length=20,
        choices=[
            ('subscription', 'Subscription Plan'),
            ('admin', 'Admin Grant'),
            ('coupon', 'Coupon/Promotion'),
        ],
        default='admin',
        help_text='How this access was granted'
    )
    subscription_plan = models.ForeignKey(
        'subscriptions.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Plan that granted access (if access_granted_by=subscription)'
    )
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text='Payment ID or transaction reference'
    )
    
    # Settings
    download_enabled = models.BooleanField(
        default=True, 
        help_text="Can download lessons for offline viewing"
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'access_granted_by']),
            models.Index(fields=['subscription_plan']),
        ]
        verbose_name = 'Course Access'
        verbose_name_plural = 'Course Access Records'
        
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    
    @property
    def is_active(self):
        """Check if access is currently valid"""
        if self.access_expires_at:
            return timezone.now() <= self.access_expires_at
        return True
    
    # Phase 1.3: Subscription Integration Methods
    
    def is_access_valid(self):
        """
        Comprehensive access validation including subscription status.
        
        Returns:
            bool: True if user should have access, False otherwise
        """
        # Check basic expiration
        if not self.is_active:
            return False
        
        # If granted by subscription, verify subscription is still active
        if self.access_granted_by == 'subscription':
            if not self.subscription_plan:
                return False
            
            # Check if user still has an active subscription with this plan
            if not self.user.current_plan:
                return False
            
            if self.user.current_plan.id != self.subscription_plan.id:
                return False
            
            if not self.user.is_subscription_active():
                return False
        
        return True
    
    def renew_from_subscription(self, duration_days=None):
        """
        Renew access based on user's current subscription.
        Called when subscription is renewed or changed.
        
        Args:
            duration_days: Optional duration in days. If None, uses subscription duration.
            
        Returns:
            bool: True if renewed successfully
        """
        if not self.user.current_plan:
            return False
        
        if self.access_granted_by != 'subscription':
            return False
        
        # Update subscription plan reference
        self.subscription_plan = self.user.current_plan
        
        # Calculate new expiration
        if duration_days is not None:
            from datetime import timedelta
            self.access_expires_at = timezone.now() + timedelta(days=duration_days)
        elif self.user.subscription_end_date:
            # Match subscription end date
            self.access_expires_at = self.user.subscription_end_date
        else:
            # Lifetime subscription
            self.access_expires_at = None
        
        self.save()
        return True
    
    def revoke_access(self):
        """
        Revoke access by setting expiration to now.
        
        Returns:
            bool: True if revoked successfully
        """
        from datetime import timedelta
        self.access_expires_at = timezone.now() - timedelta(seconds=1)
        self.save()
        return True
    
    def extend_access(self, days):
        """
        Extend access by specified number of days.
        
        Args:
            days: Number of days to extend
            
        Returns:
            bool: True if extended successfully
        """
        from datetime import timedelta
        
        if self.access_expires_at:
            # Extend from current expiration
            self.access_expires_at += timedelta(days=days)
        else:
            # Set expiration from now
            self.access_expires_at = timezone.now() + timedelta(days=days)
        
        self.save()
        return True
    
    @staticmethod
    def grant_subscription_access(user, course, plan):
        """
        Grant course access based on subscription plan.
        
        Args:
            user: User instance
            course: Course instance
            plan: SubscriptionPlan instance
            
        Returns:
            CourseAccess: Created or updated access record
        """
        access, created = CourseAccess.objects.update_or_create(
            user=user,
            course=course,
            defaults={
                'access_granted_by': 'subscription',
                'subscription_plan': plan,
                'access_expires_at': user.subscription_end_date,
            }
        )
        return access

class LessonProgress(models.Model):
    """Track user progress through lessons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completion_percentage = models.PositiveIntegerField(default=0, help_text="0-100")
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    last_watched_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'lesson']
        
    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} ({self.completion_percentage}%)"
    
    def mark_complete(self):
        self.completed = True
        self.completion_percentage = 100
        self.completed_at = timezone.now()
        self.save()

class CourseProgress(models.Model):
    """Track overall course completion for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completion_percentage = models.PositiveIntegerField(default=0, help_text="0-100")
    lessons_completed = models.PositiveIntegerField(default=0)
    total_time_spent = models.PositiveIntegerField(default=0, help_text="Total time in seconds")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    certificate_generated = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'course']
        
    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.completion_percentage}%)"
    
    def update_progress(self):
        """Calculate and update course completion based on lesson progress"""
        lesson_progresses = LessonProgress.objects.filter(
            user=self.user, 
            lesson__course=self.course
        )
        
        total_lessons = self.course.total_lessons
        completed_lessons = lesson_progresses.filter(completed=True).count()
        
        if total_lessons > 0:
            self.completion_percentage = int((completed_lessons / total_lessons) * 100)
            self.lessons_completed = completed_lessons
            
            if self.completion_percentage == 100 and not self.completed_at:
                self.completed_at = timezone.now()
                
        self.total_time_spent = lesson_progresses.aggregate(
            total=models.Sum('time_spent')
        )['total'] or 0
        
        self.save()


class VideoAccessLog(models.Model):
    """Track video access tokens for secure streaming"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_access_logs')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='access_logs')
    access_token = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_accessed = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    access_count = models.PositiveIntegerField(default=0, help_text="Number of times this token was used")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['access_token']),
            models.Index(fields=['user', 'lesson']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} - {self.access_token[:8]}..."
    
    def is_valid(self):
        """Check if token is still valid"""
        return self.is_active and timezone.now() < self.expires_at
    
    def increment_access(self):
        """Increment access count and update last accessed time"""
        self.access_count += 1
        self.save(update_fields=['access_count', 'last_accessed'])
