from rest_framework import serializers
from .models import Course, Lesson, CourseProgress, LessonProgress, CourseAccess
from django.utils.text import slugify
import re

class LessonSerializer(serializers.ModelSerializer):
    youtube_thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'title', 'slug', 'description', 'video_source', 
            'video_file', 'video_url', 'youtube_video_id', 
            'duration', 'order', 'is_preview', 'lesson_notes',
            'downloadable_resources', 'youtube_thumbnail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'youtube_video_id', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        """Normalize incoming data to handle various formats"""
        print(f"🔍 LessonSerializer received data type: {type(data)}")
        print(f"🔍 Data keys: {list(data.keys()) if hasattr(data, 'keys') else 'No keys method'}")
        
        # Create a normalized data dict
        normalized_data = {}
        
        for key, value in data.items():
            print(f"🔍 Processing {key}: {value} (type: {type(value)})")
            
            if key in ['title', 'slug', 'description', 'video_source', 'video_url', 'lesson_notes']:
                # Handle string fields that might come as arrays
                if isinstance(value, list) and len(value) > 0:
                    normalized_data[key] = value[0]  # Take first value
                    print(f"🔍 {key}: Array to string: {value} -> {value[0]}")
                else:
                    normalized_data[key] = value
                    print(f"🔍 {key}: Direct string: {value}")
                    
            elif key in ['duration', 'order']:
                # Handle integer fields
                if isinstance(value, list) and len(value) > 0:
                    try:
                        normalized_data[key] = int(value[0])
                        print(f"🔍 {key}: Array to int: {value} -> {int(value[0])}")
                    except (ValueError, TypeError):
                        normalized_data[key] = value[0]
                        print(f"🔍 {key}: Failed to convert to int: {value[0]}")
                else:
                    try:
                        normalized_data[key] = int(value) if value != '' else 0
                        print(f"🔍 {key}: Direct int conversion: {value} -> {normalized_data[key]}")
                    except (ValueError, TypeError):
                        normalized_data[key] = value
                        print(f"🔍 {key}: Keep as-is: {value}")
                        
            elif key == 'is_preview':
                # Handle boolean fields
                if isinstance(value, list) and len(value) > 0:
                    val = value[0]
                    if isinstance(val, str):
                        normalized_data[key] = val.lower() in ['true', '1', 'yes', 'on']
                    else:
                        normalized_data[key] = bool(val)
                    print(f"🔍 {key}: Array to bool: {value} -> {normalized_data[key]}")
                else:
                    if isinstance(value, str):
                        normalized_data[key] = value.lower() in ['true', '1', 'yes', 'on']
                    else:
                        normalized_data[key] = bool(value)
                    print(f"🔍 {key}: Direct to bool: {value} -> {normalized_data[key]}")
                    
            elif key in ['video_file', 'downloadable_resources']:
                # Handle file fields - extract from list if needed
                if isinstance(value, list) and len(value) > 0:
                    normalized_data[key] = value[0]  # Take first file
                    print(f"🔍 {key}: Array to file: {type(value[0])}")
                else:
                    normalized_data[key] = value
                    print(f"🔍 {key}: Direct file: {type(value)}")
                    
            else:
                # Handle other fields as-is
                normalized_data[key] = value
                print(f"🔍 {key}: Keep as-is (other): {type(value)}")
        
        print(f"🔍 Final normalized data: {normalized_data}")
        return super().to_internal_value(normalized_data)
    
    def get_youtube_thumbnail(self, obj):
        """Get YouTube thumbnail URL if video is from YouTube"""
        if obj.video_source == 'youtube' and obj.youtube_video_id:
            return f"https://img.youtube.com/vi/{obj.youtube_video_id}/maxresdefault.jpg"
        return None
    
    def validate_video_url(self, value):
        """Validate and extract YouTube video ID from URL"""
        if value and 'youtube' in value.lower():
            # Validate YouTube URL format
            youtube_regex = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)'
            if not re.search(youtube_regex, value):
                raise serializers.ValidationError("Invalid YouTube URL format")
        return value
    
    def validate(self, data):
        """Validate lesson data and handle file uploads safely"""
        # Auto-generate slug if not provided
        if 'slug' not in data or not data['slug']:
            data['slug'] = slugify(data['title'])
        
        # Validate video source requirements
        video_source = data.get('video_source', 'upload')
        
        if video_source == 'upload':
            # For uploaded videos, we need either a video file or existing file
            video_file = data.get('video_file')
            if not video_file and not (self.instance and self.instance.video_file):
                raise serializers.ValidationError({
                    'video_file': 'Video file is required for uploaded videos.'
                })
        
        elif video_source in ['youtube', 'vimeo']:
            # For external videos, we need a URL
            video_url = data.get('video_url')
            if not video_url:
                raise serializers.ValidationError({
                    'video_url': f'{video_source.title()} URL is required for {video_source} videos.'
                })
        
        return data
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error creating lesson: {str(e)}")
    
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error updating lesson: {str(e)}")

class CourseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for course lists in admin dashboard"""
    lesson_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'course_type',
            'difficulty_level', 'status', 'thumbnail', 'estimated_duration',
            'lesson_count', 'total_duration', 'enrollment_count', 
            'completion_rate', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_total_duration(self, obj):
        """Get total duration from annotation or calculate from property"""
        return getattr(obj, 'total_duration_calc', None) or obj.total_duration

    def get_enrollment_count(self, obj):
        """Get number of users enrolled in this course"""
        return CourseProgress.objects.filter(course=obj).count()
    
    def get_completion_rate(self, obj):
        """Calculate course completion rate"""
        total_enrollments = CourseProgress.objects.filter(course=obj).count()
        if total_enrollments == 0:
            return 0
        
        completed = CourseProgress.objects.filter(
            course=obj, 
            completion_percentage=100
        ).count()
        
        return round((completed / total_enrollments) * 100, 1)

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    slug = serializers.SlugField(required=False)  # Make slug optional for creation
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'course_type', 'difficulty_level', 'status', 'meta_title',
            'meta_description', 'keywords', 'thumbnail', 'trailer_video_url',
            'estimated_duration', 'order', 'lessons', 'lesson_count',
            'enrollment_count', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()
    
    def get_enrollment_count(self, obj):
        return CourseProgress.objects.filter(course=obj).count()
    
    def validate_slug(self, value):
        """Ensure slug is unique"""
        if self.instance:
            # Exclude current instance when updating
            if Course.objects.exclude(id=self.instance.id).filter(slug=value).exists():
                raise serializers.ValidationError("Course with this slug already exists.")
        else:
            if Course.objects.filter(slug=value).exists():
                raise serializers.ValidationError("Course with this slug already exists.")
        return value
    
    def create(self, validated_data):
        # Auto-generate slug if not provided
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Auto-generate slug if not provided and title changed
        if ('slug' not in validated_data or not validated_data['slug']) and 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        
        return super().update(instance, validated_data)

class CourseProgressSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_type = serializers.CharField(source='course.course_type', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = CourseProgress
        fields = [
            'id', 'user_email', 'course_title', 'course_type',
            'completion_percentage', 'lessons_completed', 'total_time_spent',
            'started_at', 'completed_at', 'certificate_generated'
        ]
        read_only_fields = ['id', 'started_at']

class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    course_title = serializers.CharField(source='lesson.course.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'user_email', 'lesson_title', 'course_title',
            'completed', 'completion_percentage', 'time_spent',
            'last_watched_at', 'completed_at'
        ]
        read_only_fields = ['id', 'last_watched_at']

class CourseAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_type = serializers.CharField(source='course.course_type', read_only=True)
    
    class Meta:
        model = CourseAccess
        fields = [
            'id', 'user_email', 'course_title', 'course_type',
            'access_granted_at', 'access_expires_at', 'download_enabled',
            'is_active'
        ]
        read_only_fields = ['id', 'access_granted_at', 'is_active']