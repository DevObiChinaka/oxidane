"""
Course Views - Public and Authenticated Course API
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Course, Lesson, CourseAccess, CourseProgress, LessonProgress
from subscriptions.models import Subscription
from users.models import User
import json


def check_mentorship_access(user):
    """Check if user has active mentorship subscription"""
    try:
        subscription = Subscription.objects.filter(
            billing_profile__user=user,
            plan__plan_type='mentorship',
            status='active'
        ).first()
        
        if subscription and subscription.is_active():
            return True
        return False
    except Exception as e:
        print(f"Error checking mentorship access: {e}")
        return False


def can_access_course(user, course):
    """
    Check if user can access a course.
    
    Access rules:
    - Free courses: User must be enrolled (have CourseAccess record)
    - Plan-based courses: User must have active subscription that includes the course
    
    Args:
        user: User instance
        course: Course instance
        
    Returns:
        bool: True if user can access the course
    """
    # Check if user has CourseAccess record (explicit enrollment)
    has_course_access = CourseAccess.objects.filter(
        user=user,
        course=course
    ).exists()
    
    if has_course_access:
        return True
    
    # For plan-based courses, check if user has active subscription
    if course.access_type == 'plan_based':
        from subscriptions.models import Subscription
        
        # Check if user has active subscription to any plan that includes this course
        has_valid_subscription = Subscription.objects.filter(
            billing_profile__user=user,
            status='active',
            plan__courses=course
        ).exists()
        
        return has_valid_subscription
    
    # Free courses require explicit enrollment
    return False


@require_http_methods(["GET"])
def list_courses(request):
    """List all published courses"""
    try:
        # Get all published courses - Phase 2: optimized with prefetch
        courses = Course.objects.filter(
            status='published'
        ).prefetch_related(
            'required_plans'  # Prefetch for access_type == 'plan_based'
        ).order_by('order', 'created_at')
        
        # Check if user is authenticated to provide enrollment info
        user = None
        if request.headers.get('Authorization', '').startswith('Bearer '):
            try:
                token = request.headers.get('Authorization').split(' ')[1]
                access_token = AccessToken(token)
                user = User.objects.get(id=access_token['user_id'])
            except:
                pass
        
        # Build course list
        course_list = []
        for course in courses:
            # Check enrollment status
            is_enrolled = False
            can_access = False
            requires_subscription = False
            
            if user:
                # Check if user has access
                can_access = can_access_course(user, course)
                is_enrolled = CourseAccess.objects.filter(user=user, course=course).exists()
                
                # Plan-based courses require subscription if not enrolled
                if course.access_type == 'plan_based' and not can_access:
                    requires_subscription = True
            else:
                # Anonymous users need subscription for plan-based courses
                if course.access_type == 'plan_based':
                    requires_subscription = True
            
            # Get progress if enrolled
            progress_percentage = 0
            if user and is_enrolled:
                try:
                    progress = CourseProgress.objects.get(user=user, course=course)
                    progress_percentage = progress.completion_percentage
                except CourseProgress.DoesNotExist:
                    pass
            
            # Phase 2: Add subscription integration fields
            required_plans = []
            if course.access_type == 'plan_based':
                required_plans = [
                    {
                        'id': str(plan.id),
                        'name': plan.name,
                        'base_price': str(plan.base_price)
                    }
                    for plan in course.required_plans.all()
                ]
            
            course_list.append({
                'id': str(course.id),
                'title': course.title,
                'slug': course.slug,
                'short_description': course.short_description,
                'course_type': course.course_type,
                'difficulty_level': course.difficulty_level,
                'status': course.status,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'estimated_duration': course.estimated_duration,
                'total_lessons': course.total_lessons,
                'is_enrolled': is_enrolled,
                'can_access': can_access,
                'requires_subscription': requires_subscription,
                'progress_percentage': progress_percentage,
                # Phase 2: Subscription integration fields
                'access_type': course.access_type,
                'required_plans': required_plans,
            })
        
        return JsonResponse({
            'courses': course_list,
            'total': len(course_list)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def course_detail(request, slug):
    """Get detailed course information"""
    try:
        # Get course - Phase 2: optimized with prefetch
        try:
            course = Course.objects.prefetch_related('required_plans').get(
                slug=slug,
                status='published'
            )
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)
        
        # Check if user is authenticated
        user = None
        if request.headers.get('Authorization', '').startswith('Bearer '):
            try:
                token = request.headers.get('Authorization').split(' ')[1]
                access_token = AccessToken(token)
                user = User.objects.get(id=access_token['user_id'])
            except:
                pass
        
        # Check access
        is_enrolled = False
        can_access = False
        requires_subscription = False
        
        if user:
            can_access = can_access_course(user, course)
            is_enrolled = CourseAccess.objects.filter(user=user, course=course).exists()
            
            # Plan-based courses require subscription if not enrolled
            if course.access_type == 'plan_based' and not can_access:
                requires_subscription = True
        else:
            # Anonymous users need subscription for plan-based courses
            if course.access_type == 'plan_based':
                requires_subscription = True
        
        # Get lessons
        lessons = course.lessons.all().order_by('order')
        lesson_list = []
        
        for lesson in lessons:
            # Show lesson details if user has access (enrolled or subscription) or if it's a preview
            show_full_details = can_access or lesson.is_preview
            
            lesson_data = {
                'id': str(lesson.id),
                'title': lesson.title,
                'slug': lesson.slug,
                'order': lesson.order,
                'duration': lesson.duration,
                'is_preview': lesson.is_preview,
            }
            
            # Add full details if user has access
            if show_full_details:
                lesson_data.update({
                    'description': lesson.description,
                    'video_source': lesson.video_source,
                    'video_url': lesson.video_url,
                    'youtube_video_id': lesson.youtube_video_id,
                })
                
                # Add video_file_url for uploaded videos
                if lesson.video_source == 'upload' and lesson.video_file:
                    lesson_data['video_file_url'] = request.build_absolute_uri(lesson.video_file.url)
                
                # Add progress if user has access
                if user and can_access:
                    try:
                        progress = LessonProgress.objects.get(user=user, lesson=lesson)
                        lesson_data['completed'] = progress.completed
                        lesson_data['completion_percentage'] = progress.completion_percentage
                    except LessonProgress.DoesNotExist:
                        lesson_data['completed'] = False
                        lesson_data['completion_percentage'] = 0
            
            lesson_list.append(lesson_data)
        
        # Get progress if user has access
        progress_data = None
        if user and can_access:
            try:
                progress = CourseProgress.objects.get(user=user, course=course)
                progress_data = {
                    'completion_percentage': progress.completion_percentage,
                    'lessons_completed': progress.lessons_completed,
                    'total_time_spent': progress.total_time_spent,
                    'started_at': progress.started_at.isoformat(),
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                }
            except CourseProgress.DoesNotExist:
                pass
        
        # Phase 2: Get subscription info
        required_plans = []
        if course.access_type == 'plan_based':
            required_plans = [
                {
                    'id': str(plan.id),
                    'name': plan.name,
                    'base_price': str(plan.base_price),
                    'billing_period': plan.billing_period,
                    'description': plan.description
                }
                for plan in course.required_plans.all()
            ]
        
        return JsonResponse({
            'id': str(course.id),
            'title': course.title,
            'slug': course.slug,
            'description': course.description,
            'short_description': course.short_description,
            'course_type': course.course_type,
            'difficulty_level': course.difficulty_level,
            'thumbnail': course.thumbnail.url if course.thumbnail else None,
            'trailer_video_url': course.trailer_video_url,
            'estimated_duration': course.estimated_duration,
            'total_lessons': course.total_lessons,
            'is_enrolled': is_enrolled,
            'can_access': can_access,
            'requires_subscription': requires_subscription,
            'lessons': lesson_list,
            'progress': progress_data,
            'created_at': course.created_at.isoformat(),
            'published_at': course.published_at.isoformat() if course.published_at else None,
            # Phase 2: Subscription integration fields
            'access_type': course.access_type,
            'required_plans': required_plans,
            'is_accessible_by_user': course.is_accessible_by_user(user) if user else False,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def enroll_course(request, slug):
    """
    Enroll user in a course.
    - Free courses: Auto-enroll
    - Plan-based courses: Check if user has active subscription that includes this course
    """
    try:
        # Authenticate user
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Get course
        try:
            course = Course.objects.prefetch_related('required_plans').get(slug=slug, status='published')
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)
        
        # Handle based on access_type
        if course.access_type == 'free':
            # Free courses: Auto-enroll
            access, created = CourseAccess.objects.get_or_create(
                user=user,
                course=course,
                defaults={'download_enabled': True}
            )
            
            # Create course progress tracker
            CourseProgress.objects.get_or_create(
                user=user,
                course=course
            )
            
            return JsonResponse({
                'message': 'Successfully enrolled in course' if created else 'Already enrolled',
                'enrolled': True,
                'course': {
                    'id': str(course.id),
                    'title': course.title,
                    'slug': course.slug,
                }
            })
            
        elif course.access_type == 'plan_based':
            # Plan-based courses: Check active subscription
            from subscriptions.models import Subscription
            
            has_access = Subscription.objects.filter(
                billing_profile__user=user,
                status='active',
                plan__courses=course
            ).exists()
            
            if not has_access:
                # Get required plan names for helpful error message
                plan_names = list(course.required_plans.values_list('name', flat=True))
                
                return JsonResponse({
                    'error': 'Subscription required to access this course',
                    'requires_subscription': True,
                    'required_plans': plan_names,
                    'message': f'This course requires an active subscription to one of: {", ".join(plan_names)}. Visit /pricing to subscribe.'
                }, status=403)
            
            # User has valid subscription - grant access
            access, created = CourseAccess.objects.get_or_create(
                user=user,
                course=course,
                defaults={'download_enabled': True}
            )
            
            # Create course progress tracker
            CourseProgress.objects.get_or_create(
                user=user,
                course=course
            )
            
            return JsonResponse({
                'message': 'Successfully enrolled in course' if created else 'Already enrolled',
                'enrolled': True,
                'course': {
                    'id': str(course.id),
                    'title': course.title,
                    'slug': course.slug,
                }
            })
        
        # Unknown access_type
        return JsonResponse({
            'error': 'Invalid course access configuration',
            'message': 'This course has an invalid access type. Please contact support.'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def enrolled_courses(request):
    """
    Get list of courses user is enrolled in or has access to via subscription.
    
    Returns courses where user has:
    1. Explicit enrollment (CourseAccess record)
    2. Active subscription that includes the course
    """
    try:
        # Authenticate user
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        courses_list = []
        course_ids_added = set()
        
        # 1. Get explicitly enrolled courses (CourseAccess records)
        enrollments = CourseAccess.objects.filter(
            user=user,
            course__status='published'
        ).select_related('course')
        
        for enrollment in enrollments:
            course = enrollment.course
            course_ids_added.add(str(course.id))
            
            # Get progress
            progress_percentage = 0
            lessons_completed = 0
            total_lessons = course.total_lessons
            
            try:
                progress = CourseProgress.objects.get(user=user, course=course)
                progress_percentage = progress.completion_percentage
                lessons_completed = progress.lessons_completed
            except CourseProgress.DoesNotExist:
                pass
            
            courses_list.append({
                'id': str(course.id),
                'title': course.title,
                'slug': course.slug,
                'short_description': course.short_description,
                'course_type': course.course_type,
                'difficulty_level': course.difficulty_level,
                'thumbnail': course.thumbnail.url if course.thumbnail else None,
                'estimated_duration': course.estimated_duration,
                'total_lessons': total_lessons,
                'lessons_completed': lessons_completed,
                'progress_percentage': progress_percentage,
                'enrolled_at': enrollment.access_granted_at.isoformat(),
                'access_type': course.access_type,
            })
        
        # 2. Get courses accessible via active subscriptions
        active_subscriptions = Subscription.objects.filter(
            billing_profile__user=user,
            status='active'
        ).prefetch_related('plan__courses')
        
        for subscription in active_subscriptions:
            # Get all courses included in this subscription plan
            subscription_courses = subscription.plan.courses.filter(
                status='published'
            )
            
            for course in subscription_courses:
                # Skip if already added (via explicit enrollment)
                if str(course.id) in course_ids_added:
                    continue
                
                course_ids_added.add(str(course.id))
                
                # Get or create progress
                progress_percentage = 0
                lessons_completed = 0
                total_lessons = course.total_lessons
                
                try:
                    progress = CourseProgress.objects.get(user=user, course=course)
                    progress_percentage = progress.completion_percentage
                    lessons_completed = progress.lessons_completed
                except CourseProgress.DoesNotExist:
                    # Auto-create progress tracker for subscription-based access
                    CourseProgress.objects.create(user=user, course=course)
                
                courses_list.append({
                    'id': str(course.id),
                    'title': course.title,
                    'slug': course.slug,
                    'short_description': course.short_description,
                    'course_type': course.course_type,
                    'difficulty_level': course.difficulty_level,
                    'thumbnail': course.thumbnail.url if course.thumbnail else None,
                    'estimated_duration': course.estimated_duration,
                    'total_lessons': total_lessons,
                    'lessons_completed': lessons_completed,
                    'progress_percentage': progress_percentage,
                    'enrolled_at': None,  # Access via subscription, not explicit enrollment
                    'access_type': course.access_type,
                    'subscription_plan': subscription.plan.name,
                })
        
        return JsonResponse({
            'courses': courses_list,
            'total': len(courses_list),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_lesson_progress(request, lesson_id):
    """
    Update progress for a specific lesson
    POST /api/courses/lessons/<lesson_id>/progress/
    Body: {
        "is_completed": true,
        "completion_percentage": 100,
        "time_spent": 300
    }
    """
    try:
        # Authenticate user
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
        except Exception as e:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Get the lesson
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'Lesson not found'}, status=404)
        
        # Check if user has access to the course
        course = lesson.course
        has_access = can_access_course(user, course)
        
        if not has_access and not lesson.is_preview:
            return JsonResponse({'error': 'Access denied. Please enroll in this course first.'}, status=403)
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Get or create lesson progress
        lesson_progress, created = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={
                'completed': False,
                'completion_percentage': 0,
                'time_spent': 0
            }
        )
        
        # Update progress from request data
        if 'is_completed' in data:
            lesson_progress.completed = data['is_completed']
        if 'completion_percentage' in data:
            lesson_progress.completion_percentage = data['completion_percentage']
        if 'time_spent' in data:
            lesson_progress.time_spent += data.get('time_spent', 0)
        
        lesson_progress.save()
        
        # Update course progress
        course_progress, _ = CourseProgress.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                'completion_percentage': 0,
                'lessons_completed': 0
            }
        )
        course_progress.update_progress()
        
        return JsonResponse({
            'success': True,
            'lesson_progress': {
                'lesson_id': str(lesson.id),
                'completed': lesson_progress.completed,
                'completion_percentage': lesson_progress.completion_percentage,
                'time_spent': lesson_progress.time_spent
            },
            'course_progress': {
                'completion_percentage': course_progress.completion_percentage,
                'lessons_completed': course_progress.lessons_completed
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
