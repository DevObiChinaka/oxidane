"""
Tests for Course and CourseAccess Serializers with Subscription Integration

This test verifies that serializers correctly expose subscription-related fields.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIRequestFactory

from courses.models import Course, CourseAccess, CourseCategory
from courses.serializers import CourseSerializer, CourseListSerializer, CourseAccessSerializer
from subscriptions.models import SubscriptionPlan, Feature
from users.models import User


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.fixture
def category():
    return CourseCategory.objects.create(name='Test Category', slug='test-category')


@pytest.fixture
def user():
    return User.objects.create_user(
        email='testuser@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium-plan',
        billing_period='monthly',
        base_price=Decimal('29.99')
    )


@pytest.fixture
def course(category):
    return Course.objects.create(
        title='Test Course',
        slug='test-course',
        description='Test Description',
        short_description='Short desc',
        category=category,
        access_type='plan_based',
        direct_purchase_price=Decimal('99.99')
    )


@pytest.mark.django_db
class TestCourseSerializer:
    """Test CourseSerializer with subscription fields"""
    
    def test_serializer_includes_subscription_fields(self, course):
        """Test that serializer includes new subscription fields"""
        serializer = CourseSerializer(course)
        data = serializer.data
        
        # Check new subscription fields are present
        assert 'access_type' in data
        assert 'required_plans' in data
        assert 'required_plan_names' in data
        assert 'direct_purchase_price' in data
        assert 'is_accessible_by_user' in data
    
    def test_access_type_serialization(self, course):
        """Test that access_type is correctly serialized"""
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert data['access_type'] == 'plan_based'
    
    def test_direct_purchase_price_serialization(self, course):
        """Test that direct_purchase_price is correctly serialized"""
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert data['direct_purchase_price'] == '99.99'
    
    def test_required_plan_names_empty(self, course):
        """Test required_plan_names when no plans are assigned"""
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert data['required_plan_names'] == []
    
    def test_required_plan_names_with_plans(self, course, plan):
        """Test required_plan_names with assigned plans"""
        course.required_plans.add(plan)
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert 'Premium Plan' in data['required_plan_names']
    
    def test_required_plan_names_multiple_plans(self, course, plan):
        """Test required_plan_names with multiple plans"""
        plan2 = SubscriptionPlan.objects.create(
            name='Basic Plan',
            slug='basic-plan',
            billing_period='monthly',
            base_price=Decimal('19.99')
        )
        course.required_plans.add(plan, plan2)
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert len(data['required_plan_names']) == 2
        assert 'Premium Plan' in data['required_plan_names']
        assert 'Basic Plan' in data['required_plan_names']
    
    def test_is_accessible_by_user_free_course(self, category):
        """Test is_accessible_by_user for free course"""
        free_course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            description='Free',
            category=category,
            access_type='free'
        )
        serializer = CourseSerializer(free_course)
        data = serializer.data
        
        # Free course accessible without authentication
        assert data['is_accessible_by_user'] is True
    
    def test_is_accessible_by_user_with_request_context(self, course, user, api_factory):
        """Test is_accessible_by_user with authenticated user context"""
        # Create request with authenticated user
        request = api_factory.get('/')
        request.user = user
        
        # User doesn't have access initially
        serializer = CourseSerializer(course, context={'request': request})
        data = serializer.data
        
        assert data['is_accessible_by_user'] is False
    
    def test_backward_compatibility(self, course):
        """Test that existing fields are still present for backward compatibility"""
        serializer = CourseSerializer(course)
        data = serializer.data
        
        # Check that old fields still exist
        assert 'id' in data
        assert 'title' in data
        assert 'slug' in data
        assert 'description' in data
        assert 'course_type' in data
        assert 'difficulty_level' in data


@pytest.mark.django_db
class TestCourseListSerializer:
    """Test CourseListSerializer with subscription fields"""
    
    def test_serializer_includes_subscription_fields(self, course):
        """Test that list serializer includes subscription fields"""
        serializer = CourseListSerializer(course)
        data = serializer.data
        
        assert 'access_type' in data
        assert 'direct_purchase_price' in data
        assert 'required_plan_count' in data
    
    def test_required_plan_count_zero(self, course):
        """Test required_plan_count when no plans assigned"""
        serializer = CourseListSerializer(course)
        data = serializer.data
        
        assert data['required_plan_count'] == 0
    
    def test_required_plan_count_with_plans(self, course, plan):
        """Test required_plan_count with assigned plans"""
        course.required_plans.add(plan)
        serializer = CourseListSerializer(course)
        data = serializer.data
        
        assert data['required_plan_count'] == 1
    
    def test_required_plan_count_multiple_plans(self, course, plan):
        """Test required_plan_count with multiple plans"""
        plan2 = SubscriptionPlan.objects.create(
            name='Basic Plan',
            slug='basic-plan',
            billing_period='monthly',
            base_price=Decimal('19.99')
        )
        course.required_plans.add(plan, plan2)
        serializer = CourseListSerializer(course)
        data = serializer.data
        
        assert data['required_plan_count'] == 2


@pytest.mark.django_db
class TestCourseAccessSerializer:
    """Test CourseAccessSerializer with subscription fields"""
    
    def test_serializer_includes_subscription_fields(self, user, course):
        """Test that serializer includes new subscription fields"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        # Check new subscription fields are present
        assert 'access_granted_by' in data
        assert 'subscription_plan' in data
        assert 'subscription_plan_name' in data
        assert 'payment_reference' in data
        assert 'updated_at' in data
        assert 'is_access_valid' in data
    
    def test_access_granted_by_serialization(self, user, course):
        """Test that access_granted_by is correctly serialized"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription'
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['access_granted_by'] == 'subscription'
    
    def test_subscription_plan_name_null(self, user, course):
        """Test subscription_plan_name when plan is not assigned"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['subscription_plan_name'] is None
    
    def test_subscription_plan_name_with_plan(self, user, course, plan):
        """Test subscription_plan_name with assigned plan"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            subscription_plan=plan
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['subscription_plan_name'] == 'Premium Plan'
    
    def test_payment_reference_serialization(self, user, course):
        """Test payment_reference serialization"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase',
            payment_reference='PAY-12345'
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['payment_reference'] == 'PAY-12345'
    
    def test_is_access_valid_for_active_access(self, user, course):
        """Test is_access_valid for active access"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin',
            access_expires_at=timezone.now() + timedelta(days=30)
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['is_access_valid'] is True
    
    def test_is_access_valid_for_expired_access(self, user, course):
        """Test is_access_valid for expired access"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin',
            access_expires_at=timezone.now() - timedelta(days=1)
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['is_access_valid'] is False
    
    def test_is_access_valid_for_lifetime_access(self, user, course):
        """Test is_access_valid for lifetime access"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase'
            # No expiration = lifetime
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        assert data['is_access_valid'] is True
    
    def test_readonly_fields(self, user, course):
        """Test that critical fields are read-only"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        
        # Try to update read-only fields
        serializer = CourseAccessSerializer(
            access,
            data={
                'access_granted_by': 'subscription',
                'is_active': False,  # read-only
                'updated_at': timezone.now(),  # read-only
            },
            partial=True
        )
        
        assert serializer.is_valid()
        updated = serializer.save()
        
        # access_granted_by should be updated (not read-only)
        assert updated.access_granted_by == 'subscription'
    
    def test_backward_compatibility(self, user, course):
        """Test that existing fields are still present"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        serializer = CourseAccessSerializer(access)
        data = serializer.data
        
        # Check that old fields still exist
        assert 'id' in data
        assert 'user_email' in data
        assert 'course_title' in data
        assert 'access_granted_at' in data
        assert 'access_expires_at' in data
        assert 'is_active' in data


@pytest.mark.django_db
class TestSerializerIntegration:
    """Test serializers working together"""
    
    def test_course_with_access_records(self, course, user, plan):
        """Test course serialization with related access records"""
        # Add plan to course
        course.required_plans.add(plan)
        
        # Create access for user
        CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            subscription_plan=plan
        )
        
        # Serialize course
        serializer = CourseSerializer(course)
        data = serializer.data
        
        assert data['access_type'] == 'plan_based'
        assert len(data['required_plan_names']) == 1
        assert 'Premium Plan' in data['required_plan_names']
    
    def test_multiple_access_methods(self, course, plan):
        """Test course accessible via multiple methods"""
        course.access_type = 'plan_based'
        course.direct_purchase_price = Decimal('49.99')
        course.save()
        course.required_plans.add(plan)
        
        serializer = CourseSerializer(course)
        data = serializer.data
        
        # Course can be accessed via plan or direct purchase
        assert data['access_type'] == 'plan_based'
        assert data['direct_purchase_price'] == '49.99'
        assert len(data['required_plan_names']) == 1
