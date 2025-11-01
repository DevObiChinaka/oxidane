# Course and content management models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

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
    video_file = models.FileField(upload_to='lesson_videos/', null=True, blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube/Vimeo URL")
    youtube_video_id = models.CharField(max_length=20, blank=True)
    
    # Lesson settings
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=0)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False, help_text="Can be viewed by non-premium users")
    
    # Additional resources
    lesson_notes = models.TextField(blank=True, help_text="PDF notes or additional text content")
    downloadable_resources = models.FileField(upload_to='lesson_resources/', null=True, blank=True)
    
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
    """Track which users have access to which premium courses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    access_granted_at = models.DateTimeField(auto_now_add=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    download_enabled = models.BooleanField(default=True, help_text="Can download lessons for offline viewing")
    
    class Meta:
        unique_together = ['user', 'course']
        
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    
    @property
    def is_active(self):
        if self.access_expires_at:
            return timezone.now() <= self.access_expires_at
        return True

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