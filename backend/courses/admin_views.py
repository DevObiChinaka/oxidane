# Course management views for admin dashboard
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Course, Lesson, CourseProgress, LessonProgress
from .serializers import CourseSerializer, LessonSerializer, CourseListSerializer
from .analytics import CourseAnalyticsService
from users.permissions import IsAdmin

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_dashboard_metrics(request):
    """Get admin dashboard overview metrics"""
    
    # Try to get cached metrics first
    cache_key = f"admin_metrics_{timezone.now().date()}"
    cached_metrics = cache.get(cache_key)
    
    if cached_metrics:
        return Response(cached_metrics)
    
    # Calculate fresh metrics
    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(status='published').count()
    draft_courses = Course.objects.filter(status='draft').count()
    
    total_lessons = Lesson.objects.count()
    
    # User statistics
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(is_staff=True).count()
    
    # Course engagement stats
    total_enrollments = CourseProgress.objects.count()
    active_learners = CourseProgress.objects.values('user').distinct().count()
    completed_courses = CourseProgress.objects.filter(completion_percentage=100).count()
    avg_completion_rate = CourseProgress.objects.aggregate(
        avg_completion=models.Avg('completion_percentage')
    )['avg_completion'] or 0
    
    # Recent activity (last 7 days)
    week_ago = timezone.now() - timezone.timedelta(days=7)
    recent_signups = User.objects.filter(created_at__gte=week_ago).count()
    recent_completions = CourseProgress.objects.filter(
        completed_at__gte=week_ago
    ).count()
    
    metrics = {
        'users': {
            'total': total_users,
            'verified': verified_users,
            'active': active_users,
            'admins': admin_users,
            'recent_signups': recent_signups,
        },
        'courses': {
            'total': total_courses,
            'published': published_courses,
            'draft': draft_courses,
        },
        'content': {
            'total_lessons': total_lessons,
            'avg_lessons_per_course': round(total_lessons / max(total_courses, 1), 1),
        },
        'engagement': {
            'total_enrollments': total_enrollments,
            'active_learners': active_learners,
            'completed_courses': completed_courses,
            'avg_completion_rate': round(avg_completion_rate, 1),
            'recent_completions': recent_completions,
        }
    }
    
    # Cache for 30 minutes
    cache.set(cache_key, metrics, 60 * 30)
    
    return Response(metrics)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_courses(request):
    """List all courses or create new course"""
    
    if request.method == 'GET':
        # Get query parameters
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        course_type = request.GET.get('type', '')
        page = int(request.GET.get('page', 1))
        
        # Build query
        courses = Course.objects.all().order_by('-created_at')
        
        # Apply filters
        if search:
            courses = courses.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        if status_filter:
            courses = courses.filter(status=status_filter)
            
        if course_type:
            courses = courses.filter(course_type=course_type)
        
        # Add lesson counts
        courses = courses.annotate(
            lesson_count=Count('lessons'),
            total_duration_calc=Sum('lessons__duration')
        )
        
        # Pagination
        paginator = Paginator(courses, 20)
        page_courses = paginator.get_page(page)
        
        serializer = CourseListSerializer(page_courses, many=True)
        
        return Response({
            'courses': serializer.data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_courses': paginator.count,
                'has_next': page_courses.has_next(),
                'has_previous': page_courses.has_previous(),
            }
        })
    
    elif request.method == 'POST':
        # Create new course
        print(f"🔍 Course Creation - Received data: {request.data}")
        print(f"🔍 Course Creation - Data type: {type(request.data)}")
        print(f"🔍 Course Creation - Data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'No keys'}")
        
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ Course serializer validation passed")
            course = serializer.save()
            print(f"✅ Course created successfully: {course.title} (ID: {course.id})")
            return Response(
                CourseSerializer(course).data, 
                status=status.HTTP_201_CREATED
            )
        else:
            print(f"❌ Course serializer validation failed:")
            print(f"❌ Errors: {serializer.errors}")
            # Check for non-field errors if they exist
            if hasattr(serializer, 'errors') and 'non_field_errors' in serializer.errors:
                print(f"❌ Non-field errors: {serializer.errors['non_field_errors']}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_course_detail(request, course_id):
    """Get, update, or delete a specific course"""
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'GET':
        serializer = CourseSerializer(course)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        print(f"🔄 Course Update Request - ID: {course_id}")
        print(f"🔄 Request data received: {request.data}")
        print(f"🔄 Course instance: {course.title} (ID: {course.id})")
        
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            print(f"✅ Serializer validation passed")
            course = serializer.save()
            print(f"✅ Course updated successfully: {course.title}")
            
            # Clear cache when course is updated
            cache.delete(f"admin_metrics_{timezone.now().date()}")
            
            return Response(CourseSerializer(course).data)
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        course.delete()
        cache.delete(f"admin_metrics_{timezone.now().date()}")
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_course_lessons(request, course_id):
    """List lessons for a course or add new lesson"""
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'GET':
        lessons = course.lessons.all().order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response({
            'course': {
                'id': course.id,
                'title': course.title,
            },
            'lessons': serializer.data
        })
    
    elif request.method == 'POST':
        try:
            # Add lesson to course
            # Don't use copy() with file uploads as it causes pickle issues
            data = request.data
            if isinstance(data, dict):
                # Create a new dict to avoid mutating request.data
                data = dict(data)
            data['course'] = course.id
            
            print(f"📝 Creating lesson with data keys: {list(data.keys())}")
            print(f"📝 Raw data received: {dict(data)}")
            print(f"📝 Request content type: {request.content_type}")
            print(f"📝 Video source: {data.get('video_source', 'upload')}")
            print(f"📝 Title: {data.get('title', 'No title')}")
            print(f"📝 Duration: {data.get('duration', 'No duration')} (type: {type(data.get('duration'))})")
            print(f"📝 Video file in request.FILES: {'video_file' in request.FILES}")
            if 'video_file' in request.FILES:
                video_file = request.FILES['video_file']
                print(f"📝 Video file details: {video_file.name}, {video_file.size} bytes, {video_file.content_type}")
            
            serializer = LessonSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                lesson = serializer.save()
                print(f"✅ Lesson created successfully: {lesson.id}")
                print(f"✅ Video file saved: {lesson.video_file.url if lesson.video_file else 'No file'}")
                return Response(
                    LessonSerializer(lesson, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                print(f"❌ Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Exception in lesson creation: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Internal server error during lesson creation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_lesson_detail(request, lesson_id):
    """Update or delete a specific lesson"""
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.method == 'PUT':
        print(f"📝 Updating lesson {lesson_id}")
        print(f"📝 Request content type: {request.content_type}")
        print(f"📝 Data keys: {list(request.data.keys())}")
        print(f"📝 Video file in request.FILES: {'video_file' in request.FILES}")
        
        if 'video_file' in request.FILES:
            video_file = request.FILES['video_file']
            print(f"📝 Updating with video file: {video_file.name}, {video_file.size} bytes")
        
        serializer = LessonSerializer(lesson, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            lesson = serializer.save()
            print(f"✅ Lesson updated successfully")
            print(f"✅ Video file: {lesson.video_file.url if lesson.video_file else 'No file'}")
            return Response(LessonSerializer(lesson, context={'request': request}).data)
        
        print(f"❌ Update validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_course_publish(request, course_id):
    """Publish or unpublish a course"""
    
    course = get_object_or_404(Course, id=course_id)
    action = request.data.get('action')  # 'publish' or 'unpublish'
    
    if action == 'publish':
        course.status = 'published'
        if not course.published_at:
            course.published_at = timezone.now()
        course.save()
        
        return Response({
            'message': f'Course "{course.title}" published successfully',
            'status': course.status
        })
    
    elif action == 'unpublish':
        course.status = 'draft'
        course.save()
        
        return Response({
            'message': f'Course "{course.title}" unpublished',
            'status': course.status
        })
    
    return Response(
        {'error': 'Invalid action. Use "publish" or "unpublish"'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_course_analytics(request, course_id):
    """Get analytics for a specific course"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Enrollment stats
    total_enrollments = CourseProgress.objects.filter(course=course).count()
    completed_enrollments = CourseProgress.objects.filter(
        course=course, 
        completion_percentage=100
    ).count()
    
    # Completion rate
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = (completed_enrollments / total_enrollments) * 100
    
    # Average progress
    avg_progress = CourseProgress.objects.filter(course=course).aggregate(
        avg_progress=models.Avg('completion_percentage')
    )['avg_progress'] or 0
    
    # Lesson-by-lesson analytics
    lesson_analytics = []
    for lesson in course.lessons.all().order_by('order'):
        lesson_completions = LessonProgress.objects.filter(
            lesson=lesson, 
            completed=True
        ).count()
        
        lesson_analytics.append({
            'lesson_id': lesson.id,
            'title': lesson.title,
            'order': lesson.order,
            'completions': lesson_completions,
            'completion_rate': (lesson_completions / max(total_enrollments, 1)) * 100
        })
    
    return Response({
        'course': {
            'id': course.id,
            'title': course.title,
            'type': course.course_type,
        },
        'stats': {
            'total_enrollments': total_enrollments,
            'completed_enrollments': completed_enrollments,
            'completion_rate': round(completion_rate, 1),
            'avg_progress': round(avg_progress, 1),
        },
        'lesson_analytics': lesson_analytics
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_lessons_list(request):
    """Get all lessons across all courses"""
    
    lessons = Lesson.objects.select_related('course').all().order_by('-created_at')
    
    # Apply filters
    course_id = request.GET.get('course')
    if course_id:
        lessons = lessons.filter(course_id=course_id)
    
    search = request.GET.get('search')
    if search:
        lessons = lessons.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(course__title__icontains=search)
        )
    
    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginated_lessons = paginator.paginate_queryset(lessons, request)
    
    serializer = LessonSerializer(paginated_lessons, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])  
def admin_course_analytics(request):
    """Get comprehensive course analytics data for dashboard"""
    
    # Check for cached data (30-minute cache for optimal refresh rate)
    cache_key = f"course_analytics_{timezone.now().strftime('%Y%m%d_%H%M')}"  # Cache by hour and minute
    cached_analytics = cache.get(cache_key)
    
    if cached_analytics:
        return Response(cached_analytics)
    
    try:
        # Get comprehensive analytics data
        analytics_data = CourseAnalyticsService.get_dashboard_analytics()
        
        # Cache for 30 minutes (optimal refresh rate)
        cache.set(cache_key, analytics_data, 60 * 30)
        
        return Response(analytics_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )