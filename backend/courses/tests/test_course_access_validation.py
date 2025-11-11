"""
Tests for Course Access Validation (Phase 2, Task 2.3)

Tests verify that access control is properly enforced across all course endpoints:
- Course detail viewing
- Lesson access and progress tracking
- Enrolled courses listing
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

from courses.models import Course, CourseAccess, Lesson, LessonProgress, CourseProgress
from subscriptions.models import SubscriptionPlan, Subscription, BillingProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestCourseDetailAccess:
    """Test access validation for course detail endpoint"""
    
    def test_anonymous_can_view_free_course_details(self):
        """Anonymous users can view free course details but not lesson content"""
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='free'
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Lesson 1',
            slug='lesson-1',
            description='Full description',
            order=1,
            is_preview=False
        )
        
        client = Client()
        response = client.get(f'/api/courses/{course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == 'Free Course'
        assert data['access_type'] == 'free'
        
        # Check lesson - should not have full details
        lessons = data['lessons']
        assert len(lessons) == 1
        assert lessons[0]['title'] == 'Lesson 1'
        assert 'description' not in lessons[0]  # No access
    
    def test_enrolled_user_can_view_lesson_details(self):
        """Enrolled users can view full lesson details"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='free'
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Lesson 1',
            slug='lesson-1',
            description='Full description',
            order=1,
            is_preview=False
        )
        
        # Enroll user
        CourseAccess.objects.create(user=user, course=course)
        
        client = Client()
        response = client.get(
            f'/api/courses/{course.slug}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check lesson - should have full details
        lessons = data['lessons']
        assert len(lessons) == 1
        assert lessons[0]['title'] == 'Lesson 1'
        assert lessons[0]['description'] == 'Full description'
    
    def test_subscription_grants_access_to_plan_based_course(self):
        """User with active subscription can access plan-based course details"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create plan and course
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        lesson = Lesson.objects.create(
            course=course,
            title='Premium Lesson',
            slug='premium-lesson',
            description='Full description',
            order=1,
            is_preview=False
        )
        
        # Create active subscription
        billing_profile = BillingProfile.objects.get(user=user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=99.00,
            currency='USD'
        )
        
        client = Client()
        response = client.get(
            f'/api/courses/{course.slug}/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have access to lesson details
        lessons = data['lessons']
        assert len(lessons) == 1
        assert lessons[0]['description'] == 'Full description'
    
    def test_preview_lessons_visible_to_all(self):
        """Preview lessons should be visible even without access"""
        course = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        
        preview_lesson = Lesson.objects.create(
            course=course,
            title='Preview Lesson',
            slug='preview-lesson',
            description='Preview content',
            order=1,
            is_preview=True
        )
        
        locked_lesson = Lesson.objects.create(
            course=course,
            title='Locked Lesson',
            slug='locked-lesson',
            description='Locked content',
            order=2,
            is_preview=False
        )
        
        client = Client()
        response = client.get(f'/api/courses/{course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        
        lessons = data['lessons']
        assert len(lessons) == 2
        
        # Preview lesson should have full details
        preview = next(l for l in lessons if l['slug'] == 'preview-lesson')
        assert preview['description'] == 'Preview content'
        assert preview['is_preview'] is True
        
        # Locked lesson should not have full details
        locked = next(l for l in lessons if l['slug'] == 'locked-lesson')
        assert 'description' not in locked


class TestLessonProgressAccess:
    """Test access validation for lesson progress tracking"""
    
    def test_cannot_update_progress_without_access(self):
        """Users without access cannot update lesson progress"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Locked Lesson',
            slug='locked-lesson',
            order=1,
            is_preview=False
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/lessons/{lesson.id}/progress/',
            data={'is_completed': True, 'completion_percentage': 100},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert 'Access denied' in data['error']
    
    def test_can_update_progress_with_enrollment(self):
        """Enrolled users can update lesson progress"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='free'
        )
        
        lesson = Lesson.objects.create(
            course=course,
            title='Lesson 1',
            slug='lesson-1',
            order=1,
            is_preview=False
        )
        
        # Enroll user
        CourseAccess.objects.create(user=user, course=course)
        
        client = Client()
        response = client.post(
            f'/api/courses/lessons/{lesson.id}/progress/',
            data={'is_completed': True, 'completion_percentage': 100, 'time_spent': 300},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['lesson_progress']['completed'] is True
        assert data['lesson_progress']['completion_percentage'] == 100
    
    def test_can_update_preview_lesson_progress_without_access(self):
        """Users can track progress on preview lessons even without course access"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        
        preview_lesson = Lesson.objects.create(
            course=course,
            title='Preview Lesson',
            slug='preview-lesson',
            order=1,
            is_preview=True
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/lessons/{preview_lesson.id}/progress/',
            data={'is_completed': True, 'completion_percentage': 100, 'time_spent': 180},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True


class TestEnrolledCoursesAccess:
    """Test enrolled courses endpoint returns correct courses based on access"""
    
    def test_enrolled_courses_includes_explicit_enrollments(self):
        """Endpoint returns courses with explicit CourseAccess records"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course1 = Course.objects.create(
            title='Free Course 1',
            slug='free-course-1',
            description='Test',
            short_description='Test',
            status='published',
            access_type='free'
        )
        
        course2 = Course.objects.create(
            title='Free Course 2',
            slug='free-course-2',
            description='Test',
            short_description='Test',
            status='published',
            access_type='free'
        )
        
        # Enroll in course1 only
        CourseAccess.objects.create(user=user, course=course1)
        
        client = Client()
        response = client.get(
            '/api/courses/enrolled/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert data['courses'][0]['slug'] == 'free-course-1'
    
    def test_enrolled_courses_includes_subscription_courses(self):
        """Endpoint returns courses accessible via active subscription"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create plan with courses
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course1 = Course.objects.create(
            title='Pro Course 1',
            slug='pro-course-1',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        course1.required_plans.add(plan)
        
        course2 = Course.objects.create(
            title='Pro Course 2',
            slug='pro-course-2',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        course2.required_plans.add(plan)
        
        # Create active subscription
        billing_profile = BillingProfile.objects.get(user=user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=99.00,
            currency='USD'
        )
        
        client = Client()
        response = client.get(
            '/api/courses/enrolled/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        
        slugs = [c['slug'] for c in data['courses']]
        assert 'pro-course-1' in slugs
        assert 'pro-course-2' in slugs
    
    def test_enrolled_courses_no_duplicates(self):
        """Courses should not be duplicated if both enrolled and subscribed"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create plan with course
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Pro Course',
            slug='pro-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Both explicit enrollment AND subscription
        CourseAccess.objects.create(user=user, course=course)
        
        billing_profile = BillingProfile.objects.get(user=user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=99.00,
            currency='USD'
        )
        
        client = Client()
        response = client.get(
            '/api/courses/enrolled/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1  # Should not be duplicated
        assert data['courses'][0]['slug'] == 'pro-course'
    
    def test_enrolled_courses_excludes_inactive_subscriptions(self):
        """Cancelled/expired subscriptions should not grant access"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Pro Course',
            slug='pro-course',
            description='Test',
            short_description='Test',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create CANCELLED subscription
        billing_profile = BillingProfile.objects.get(user=user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='cancelled',  # Not active!
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            amount_paid=99.00,
            currency='USD'
        )
        
        client = Client()
        response = client.get(
            '/api/courses/enrolled/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0  # Cancelled subscription should not grant access
