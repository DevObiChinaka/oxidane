from django.contrib import admin
from .models import Course, Lesson, CourseProgress, LessonProgress, CourseCategory


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'course_count', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'course_type', 
        'difficulty_level', 
        'status', 
        'estimated_duration',
        'order',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'category',
        'course_type', 
        'difficulty_level', 
        'status', 
        'created_at',
        'updated_at'
    ]
    search_fields = ['title', 'description', 'keywords']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'slug', 
                'description',
                'short_description',
                'category'
            )
        }),
        ('Course Settings', {
            'fields': (
                'course_type',
                'difficulty_level',
                'status',
                'estimated_duration',
                'order'
            )
        }),
        ('SEO & Metadata', {
            'fields': (
                'meta_title',
                'meta_description',
                'keywords'
            ),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': (
                'thumbnail',
                'trailer_video_url'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
                'published_at'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'course',
        'video_source',
        'order',
        'duration',
        'is_preview',
        'created_at'
    ]
    list_filter = [
        'video_source',
        'is_preview',
        'course__title',
        'created_at'
    ]
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order', 'title']
    readonly_fields = ['id', 'youtube_video_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'course',
                'title',
                'slug',
                'description'
            )
        }),
        ('Video Content', {
            'fields': (
                'video_source',
                'video_file',
                'video_url',
                'youtube_video_id'
            )
        }),
        ('Lesson Settings', {
            'fields': (
                'order',
                'duration',
                'is_preview'
            )
        }),
        ('Additional Resources', {
            'fields': (
                'lesson_notes',
                'downloadable_resources'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'id',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'course',
        'started_at',
        'completion_percentage',
        'lessons_completed',
        'completed_at'
    ]
    list_filter = [
        'started_at',
        'completed_at',
        'course__title',
        'certificate_generated'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'course__title'
    ]
    readonly_fields = [
        'id',
        'started_at',
        'completed_at'
    ]
    ordering = ['-started_at']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'lesson',
        'completed',
        'completion_percentage',
        'time_spent',
        'last_watched_at',
        'completed_at'
    ]
    list_filter = [
        'completed',
        'completed_at',
        'lesson__course__title',
        'last_watched_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'lesson__title',
        'lesson__course__title'
    ]
    readonly_fields = [
        'id',
        'last_watched_at',
        'completed_at'
    ]
    ordering = ['-last_watched_at']