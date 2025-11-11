"""
Tests for subscription-based course enrollment logic.

Tests verify that enrollment properly handles:
- Free courses (auto-enroll)
- Plan-based courses (check active subscription)
- Deprecated access types (reject enrollment)
- Authentication requirements
- Helpful error messages guiding users to /pricing
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import Course, CourseAccess, CourseProgress
from subscriptions.models import SubscriptionPlan, Subscription
from datetime import timedelta
from django.utils import timezone
from django.test import Client

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestFreeCoursesEnrollment:
    """Test enrollment in free courses"""
    
    def test_free_course_enrollment_success(self):
        """Free course should allow enrollment without subscription"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['enrolled'] is True
        assert data['message'] == 'Successfully enrolled in course'
        
        # Verify CourseAccess created
        assert CourseAccess.objects.filter(user=user, course=course).exists()
        
        # Verify CourseProgress created
        assert CourseProgress.objects.filter(user=user, course=course).exists()
    
    def test_free_course_already_enrolled(self):
        """Enrolling in free course twice should return 'Already enrolled'"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        # Pre-create enrollment
        CourseAccess.objects.create(user=user, course=course)
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['enrolled'] is True
        assert data['message'] == 'Already enrolled'


class TestPlanBasedEnrollment:
    """Test enrollment in plan-based courses with subscription checking"""
    
    def test_plan_based_enrollment_with_active_subscription(self):
        """User with active subscription should be able to enroll"""
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
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create active subscription (using billing_profile)
        from subscriptions.models import BillingProfile
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
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['enrolled'] is True
        assert data['message'] == 'Successfully enrolled in course'
        
        # Verify access granted
        assert CourseAccess.objects.filter(user=user, course=course).exists()
        assert CourseProgress.objects.filter(user=user, course=course).exists()
    
    def test_plan_based_enrollment_without_subscription(self):
        """User without subscription should be rejected with helpful message"""
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
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data['requires_subscription'] is True
        assert 'Pro Plan' in data['required_plans']
        assert '/pricing' in data['message']
        assert 'Subscription required' in data['error']
        
        # Verify no access granted
        assert not CourseAccess.objects.filter(user=user, course=course).exists()
    
    def test_plan_based_enrollment_with_inactive_subscription(self):
        """User with inactive subscription should be rejected"""
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
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create INACTIVE subscription
        from subscriptions.models import BillingProfile
        billing_profile = BillingProfile.objects.get(user=user)
        
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='cancelled',  # Not 'active'
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            amount_paid=99.00,
            currency='USD'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data['requires_subscription'] is True
        
        # Verify no access granted
        assert not CourseAccess.objects.filter(user=user, course=course).exists()
    
    def test_plan_based_enrollment_wrong_plan(self):
        """User with subscription to wrong plan should be rejected"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create two plans
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            base_price=49.00,
            billing_period='monthly'
        )
        
        pro_plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        # Course requires Pro Plan
        course = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(pro_plan)
        
        # User has Basic Plan subscription
        from subscriptions.models import BillingProfile
        billing_profile = BillingProfile.objects.get(user=user)
        
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,  # Wrong plan!
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=49.00,
            currency='USD'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data['requires_subscription'] is True
        assert 'Pro Plan' in data['required_plans']
        assert 'Basic Plan' not in data['required_plans']
    
    def test_plan_based_enrollment_multiple_plans(self):
        """Course available in multiple plans - any should work"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create multiple plans
        basic_plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            base_price=49.00,
            billing_period='monthly'
        )
        
        pro_plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        # Course available in both plans
        course = Course.objects.create(
            title='Multi-Plan Course',
            slug='multi-plan-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(basic_plan, pro_plan)
        
        # User has Basic Plan (should work)
        from subscriptions.models import BillingProfile
        billing_profile = BillingProfile.objects.get(user=user)
        
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=basic_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=49.00,
            currency='USD'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['enrolled'] is True




class TestEnrollmentAuthentication:
    """Test authentication requirements for enrollment"""
    
    def test_enrollment_without_auth_token(self):
        """Enrollment without auth token should return 401"""
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        client = Client()
        response = client.post(f'/api/courses/{course.slug}/enroll/')
        
        assert response.status_code == 401
        data = response.json()
        assert 'Authentication required' in data['error']
    
    def test_enrollment_with_invalid_token(self):
        """Enrollment with invalid token should return 401"""
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION='Bearer invalid_token_xyz'
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'Invalid or expired token' in data['error']


class TestEnrollmentEdgeCases:
    """Test edge cases in enrollment logic"""
    
    def test_enrollment_in_draft_course(self):
        """Cannot enroll in draft (unpublished) courses"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Draft Course',
            slug='draft-course',
            status='draft',  # Not published
            access_type='free'
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'Course not found' in data['error']
    
    def test_enrollment_nonexistent_course(self):
        """Enrolling in non-existent course returns 404"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        client = Client()
        response = client.post(
            '/api/courses/nonexistent-slug/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'Course not found' in data['error']
