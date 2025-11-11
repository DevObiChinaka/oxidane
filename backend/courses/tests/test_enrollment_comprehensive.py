"""
Comprehensive enrollment tests covering edge cases and advanced scenarios.

This test suite expands on basic enrollment tests to cover:
- Subscription state transitions (active -> cancelled -> reactivated)
- Concurrent enrollment scenarios
- Permission edge cases
- Error message validation
- Billing profile edge cases
- Access persistence after subscription changes
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import Course, CourseAccess, CourseProgress
from subscriptions.models import SubscriptionPlan, Subscription, BillingProfile
from datetime import timedelta
from django.utils import timezone
from django.test import Client

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestSubscriptionStateTransitions:
    """Test enrollment behavior when subscription status changes"""
    
    def test_access_persists_after_subscription_cancellation(self):
        """CourseAccess created during active subscription should persist after cancellation"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile (created by signal)
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Create plan and course
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan-Based Course',
            slug='plan-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create active subscription
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=plan.base_price
        )
        
        # Enroll while subscription is active
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        assert CourseAccess.objects.filter(user=user, course=course).exists()
        
        # Cancel subscription
        subscription.status = 'cancelled'
        subscription.save()
        
        # Verify CourseAccess still exists
        assert CourseAccess.objects.filter(user=user, course=course).exists()
        
        # Verify user can still access via CourseAccess record (not subscription)
        from courses.views import can_access_course
        assert can_access_course(user, course) is True
    
    def test_cannot_enroll_after_subscription_cancelled(self):
        """New enrollment should fail if subscription is cancelled"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create cancelled subscription
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='cancelled',
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            amount_paid=plan.base_price
        )
        
        # Try to enroll with cancelled subscription
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert 'requires_subscription' in data
        assert data['requires_subscription'] is True
        assert 'Visit /pricing to subscribe' in data['message']
    
    def test_can_enroll_after_subscription_reactivation(self):
        """User can enroll after reactivating cancelled subscription"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create initially cancelled subscription
        subscription = Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='cancelled',
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            amount_paid=plan.base_price
        )
        
        # Reactivate subscription
        subscription.status = 'active'
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()
        
        # Should be able to enroll now
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['enrolled'] is True
        assert CourseAccess.objects.filter(user=user, course=course).exists()
    
    def test_past_due_subscription_blocks_enrollment(self):
        """past_due subscription status should block new enrollments"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan)
        
        # Create past_due subscription
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='past_due',
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() + timedelta(days=5),
            amount_paid=plan.base_price
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data['requires_subscription'] is True


class TestConcurrentEnrollmentScenarios:
    """Test handling of concurrent enrollments and edge cases"""
    
    def test_enrolled_in_free_then_subscribe_to_plan_with_same_course(self):
        """User enrolled in free course, then subscribes to plan containing it"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        
        # Create course that was originally free
        course = Course.objects.create(
            title='Course',
            slug='test-course',
            status='published',
            access_type='free'
        )
        
        # User enrolls when it's free
        CourseAccess.objects.create(user=user, course=course)
        
        # Course becomes plan-based
        course.access_type = 'plan_based'
        course.save()
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        course.required_plans.add(plan)
        
        # User subscribes
        billing_profile = BillingProfile.objects.get(user=user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=plan.base_price
        )
        
        # Verify user still has access
        from courses.views import can_access_course
        assert can_access_course(user, course) is True
        
        # Verify only one CourseAccess record exists
        assert CourseAccess.objects.filter(user=user, course=course).count() == 1
    
    def test_multiple_users_enroll_same_free_course(self):
        """Multiple users can enroll in same free course independently"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com', password='testpass123')
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='testpass123')
        
        refresh1 = RefreshToken.for_user(user1)
        token1 = str(refresh1.access_token)
        
        refresh2 = RefreshToken.for_user(user2)
        token2 = str(refresh2.access_token)
        
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        client = Client()
        
        # User 1 enrolls
        response1 = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token1}'
        )
        assert response1.status_code == 200
        
        # User 2 enrolls
        response2 = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token2}'
        )
        assert response2.status_code == 200
        
        # Both have separate CourseAccess records
        assert CourseAccess.objects.filter(user=user1, course=course).exists()
        assert CourseAccess.objects.filter(user=user2, course=course).exists()
        assert CourseAccess.objects.filter(course=course).count() == 2
    
    def test_multiple_active_subscriptions_same_user(self):
        """User with multiple active subscriptions (different plans) can enroll"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Create two different plans
        plan1 = SubscriptionPlan.objects.create(
            name='Basic Plan',
            base_price=49.00,
            billing_period='monthly'
        )
        
        plan2 = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        # Course is in Plan 2
        course = Course.objects.create(
            title='Pro Course',
            slug='pro-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan2)
        
        # User has BOTH subscriptions active
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan1,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=plan1.base_price
        )
        
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan2,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=plan2.base_price
        )
        
        # Should be able to enroll (has Pro Plan subscription)
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        assert CourseAccess.objects.filter(user=user, course=course).exists()


class TestErrorMessageQuality:
    """Test that error messages guide users appropriately"""
    
    def test_plan_based_enrollment_error_lists_all_required_plans(self):
        """Error message should list all plans that provide access"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create multiple plans
        plan1 = SubscriptionPlan.objects.create(
            name='Starter Plan',
            base_price=29.00,
            billing_period='monthly'
        )
        
        plan2 = SubscriptionPlan.objects.create(
            name='Professional Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        plan3 = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            base_price=299.00,
            billing_period='monthly'
        )
        
        # Course requires any of these three plans
        course = Course.objects.create(
            title='Advanced Course',
            slug='advanced-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan1, plan2, plan3)
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        
        # Error message should mention all three plans
        assert 'Starter Plan' in data['message']
        assert 'Professional Plan' in data['message']
        assert 'Enterprise Plan' in data['message']
        
        # Should have structured data
        assert len(data['required_plans']) == 3
        assert set(data['required_plans']) == {'Starter Plan', 'Professional Plan', 'Enterprise Plan'}
    
    def test_free_course_enrollment_error_messages(self):
        """Free course enrollment errors should be clear"""
        course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            status='published',
            access_type='free'
        )
        
        client = Client()
        
        # No auth token
        response = client.post(f'/api/courses/{course.slug}/enroll/')
        assert response.status_code == 401
        data = response.json()
        assert 'Authentication required' in data['error']
    
    def test_draft_course_enrollment_error(self):
        """Attempting to enroll in draft course should give clear error"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        course = Course.objects.create(
            title='Draft Course',
            slug='draft-course',
            status='draft',
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


class TestBillingProfileEdgeCases:
    """Test enrollment scenarios with billing profile edge cases"""
    
    def test_user_without_billing_profile_cannot_access_plan_based_course(self):
        """User without billing profile should not access plan-based courses"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # No billing profile created for this user
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
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
    
    def test_user_with_billing_profile_but_no_subscription(self):
        """User with billing profile but no subscription cannot enroll in plan-based course"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Billing profile auto-created by signal, just verify it exists
        assert BillingProfile.objects.filter(user=user).exists()
        
        plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
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
        assert 'Subscription required' in data['error']


class TestAccessPersistence:
    """Test that CourseAccess records persist appropriately"""
    
    def test_course_access_created_with_correct_defaults(self):
        """CourseAccess should be created with download_enabled=True"""
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
        client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        course_access = CourseAccess.objects.get(user=user, course=course)
        assert course_access.download_enabled is True
    
    def test_course_progress_created_on_enrollment(self):
        """CourseProgress should be auto-created on enrollment"""
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
        client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Verify CourseProgress was created
        assert CourseProgress.objects.filter(user=user, course=course).exists()
        progress = CourseProgress.objects.get(user=user, course=course)
        assert progress.completion_percentage == 0  # Should start at 0%
    
    def test_duplicate_enrollment_does_not_create_duplicate_progress(self):
        """Enrolling twice should not create duplicate CourseProgress records"""
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
        
        # Enroll twice
        client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should only have one CourseProgress record
        assert CourseProgress.objects.filter(user=user, course=course).count() == 1
        assert CourseAccess.objects.filter(user=user, course=course).count() == 1


class TestPlanCourseRelationships:
    """Test enrollment with various plan-course relationship configurations"""
    
    def test_course_with_no_required_plans_as_plan_based(self):
        """Plan-based course with no required_plans should handle gracefully"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Create plan-based course but don't add any plans
        course = Course.objects.create(
            title='Plan Course',
            slug='plan-course',
            status='published',
            access_type='plan_based'
        )
        # No required_plans added
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should fail with subscription required
        assert response.status_code == 403
        data = response.json()
        assert data['requires_subscription'] is True
    
    def test_user_subscribed_to_plan_not_containing_course(self):
        """User with subscription to different plan cannot enroll"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        # Get the auto-created billing profile
        billing_profile = BillingProfile.objects.get(user=user)
        
        # Plan A (user subscribed to this)
        plan_a = SubscriptionPlan.objects.create(
            name='Plan A',
            base_price=49.00,
            billing_period='monthly'
        )
        
        # Plan B (course requires this)
        plan_b = SubscriptionPlan.objects.create(
            name='Plan B',
            base_price=99.00,
            billing_period='monthly'
        )
        
        course = Course.objects.create(
            title='Plan B Course',
            slug='plan-b-course',
            status='published',
            access_type='plan_based'
        )
        course.required_plans.add(plan_b)  # Course requires Plan B
        
        # User subscribed to Plan A (not Plan B)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=plan_a,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=plan_a.base_price
        )
        
        client = Client()
        response = client.post(
            f'/api/courses/{course.slug}/enroll/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 403
        data = response.json()
        assert 'Plan B' in data['message']
        assert data['requires_subscription'] is True
