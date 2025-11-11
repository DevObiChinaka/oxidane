"""
Tests for Course Views with Subscription Integration (Phase 2)

Tests the updated list_courses and course_detail views to ensure they properly
expose subscription-related fields from Phase 1.
"""
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from courses.models import Course, CourseAccess, CourseCategory
from subscriptions.models import SubscriptionPlan, Feature
from users.models import User


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def category():
    """Create a course category"""
    return CourseCategory.objects.create(
        name="Trading Basics",
        slug="trading-basics",
        description="Learn the fundamentals"
    )


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(
        email="testuser@example.com",
        username="testuser",
        password="testpass123",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def premium_plan():
    """Create a premium subscription plan"""
    return SubscriptionPlan.objects.create(
        name="Premium Trading",
        slug="premium-trading",
        billing_period="lifetime",
        base_price=Decimal('99.99'),
        description="Full course access"
    )


@pytest.fixture
def basic_plan():
    """Create a basic subscription plan"""
    return SubscriptionPlan.objects.create(
        name="Basic Trading",
        slug="basic-trading",
        billing_period="monthly",
        base_price=Decimal('29.99'),
        description="Monthly signals"
    )


@pytest.fixture
def free_course(category):
    """Create a free course"""
    return Course.objects.create(
        title="Free Course",
        slug="free-course",
        short_description="A free course",
        description="Full description",
        category=category,
        course_type="free",
        difficulty_level="beginner",
        status="published",
        access_type="free"
    )


@pytest.fixture
def plan_based_course(category, premium_plan):
    """Create a plan-based course"""
    course = Course.objects.create(
        title="Premium Plan Course",
        slug="premium-plan-course",
        short_description="Requires premium plan",
        description="Full description",
        category=category,
        course_type="premium",
        difficulty_level="intermediate",
        status="published",
        access_type="plan_based"
    )
    course.required_plans.add(premium_plan)
    return course


@pytest.fixture
def multi_plan_course(category, premium_plan, basic_plan):
    """Create a course accessible with multiple plans"""
    course = Course.objects.create(
        title="Multi-Plan Course",
        slug="multi-plan-course",
        short_description="Accessible with multiple plans",
        description="Full description",
        category=category,
        course_type="premium",
        difficulty_level="advanced",
        status="published",
        access_type="plan_based"
    )
    course.required_plans.add(premium_plan, basic_plan)
    return course


@pytest.fixture
def draft_course(category):
    """Create a draft (unpublished) course"""
    return Course.objects.create(
        title="Draft Course",
        slug="draft-course",
        short_description="Not published yet",
        description="Full description",
        category=category,
        course_type="free",
        difficulty_level="beginner",
        status="draft",
        access_type="free"
    )


@pytest.fixture
def auth_token(user):
    """Generate JWT token for user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


# ============================================================================
# TEST: List Courses View - Subscription Field Exposure
# ============================================================================

@pytest.mark.django_db
class TestListCoursesSubscriptionFields:
    """Test that list_courses view exposes subscription integration fields"""
    
    def test_free_course_shows_correct_access_type(self, client, free_course):
        """Free courses should show access_type='free'"""
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        courses = data['courses']
        free = next(c for c in courses if c['slug'] == 'free-course')
        
        assert free['access_type'] == 'free'
        assert free['required_plans'] == []
    
    def test_plan_based_course_shows_required_plans(self, client, plan_based_course):
        """Plan-based courses should expose required_plans list"""
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        courses = data['courses']
        premium = next(c for c in courses if c['slug'] == 'premium-plan-course')
        
        assert premium['access_type'] == 'plan_based'
        assert len(premium['required_plans']) == 1
        assert premium['required_plans'][0]['name'] == "Premium Trading"
        assert premium['required_plans'][0]['base_price'] == "99.99"
    
    def test_multi_plan_course_shows_all_required_plans(self, client, multi_plan_course):
        """Courses with multiple plans should show all plans"""
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        courses = data['courses']
        multi = next(c for c in courses if c['slug'] == 'multi-plan-course')
        
        assert multi['access_type'] == 'plan_based'
        assert len(multi['required_plans']) == 2
        
        plan_names = [p['name'] for p in multi['required_plans']]
        assert "Premium Trading" in plan_names
        assert "Basic Trading" in plan_names
    
    def test_draft_courses_not_included_in_list(self, client, draft_course, free_course):
        """Draft courses should not appear in public course list"""
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have free course but not draft
        slugs = [c['slug'] for c in data['courses']]
        assert 'free-course' in slugs
        assert 'draft-course' not in slugs
    
    def test_list_includes_backward_compatible_fields(self, client, free_course):
        """Ensure backward compatibility - old fields still present"""
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        course = data['courses'][0]
        
        # Old fields should still be present
        assert 'id' in course
        assert 'title' in course
        assert 'course_type' in course
        assert 'is_enrolled' in course
        assert 'can_access' in course
        assert 'requires_subscription' in course


# ============================================================================
# TEST: Course Detail View - Subscription Field Exposure
# ============================================================================

@pytest.mark.django_db
class TestCourseDetailSubscriptionFields:
    """Test that course_detail view exposes subscription integration fields"""
    
    def test_free_course_detail_shows_access_type(self, client, free_course):
        """Free course detail should show access_type='free'"""
        response = client.get(f'/api/courses/{free_course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['access_type'] == 'free'
        assert data['required_plans'] == []
        assert data['is_accessible_by_user'] is False  # Not authenticated
    
    def test_plan_based_course_detail_shows_plans(self, client, plan_based_course):
        """Plan-based course detail should show full plan information"""
        response = client.get(f'/api/courses/{plan_based_course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['access_type'] == 'plan_based'
        assert len(data['required_plans']) == 1
        
        plan = data['required_plans'][0]
        assert plan['name'] == "Premium Trading"
        assert plan['base_price'] == "99.99"
        assert plan['billing_period'] == "lifetime"
        assert 'description' in plan
    
    def test_authenticated_user_sees_is_accessible(self, client, free_course, user, auth_token):
        """Authenticated users should see is_accessible_by_user field"""
        # Grant access to user
        CourseAccess.objects.create(
            user=user,
            course=free_course,
            access_granted_by='admin'
        )
        
        response = client.get(
            f'/api/courses/{free_course.slug}/',
            HTTP_AUTHORIZATION=f'Bearer {auth_token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['is_accessible_by_user'] is True
    
    def test_unauthenticated_user_not_accessible(self, client, plan_based_course):
        """Unauthenticated users should see is_accessible_by_user=False"""
        response = client.get(f'/api/courses/{plan_based_course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['is_accessible_by_user'] is False
    
    def test_detail_includes_backward_compatible_fields(self, client, free_course):
        """Ensure backward compatibility - old fields still present"""
        response = client.get(f'/api/courses/{free_course.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        
        # Old fields should still be present
        assert 'id' in data
        assert 'title' in data
        assert 'description' in data
        assert 'course_type' in data
        assert 'is_enrolled' in data
        assert 'can_access' in data
        assert 'requires_subscription' in data
        assert 'lessons' in data
        assert 'progress' in data
    
    def test_nonexistent_course_returns_404(self, client):
        """Requesting non-existent course should return 404"""
        response = client.get('/api/courses/nonexistent-slug/')
        
        assert response.status_code == 404
        assert 'error' in response.json()


# ============================================================================
# TEST: List View Performance
# ============================================================================

@pytest.mark.django_db
class TestListViewPerformance:
    """Test query optimization with subscription fields"""
    
    def test_multiple_courses_minimal_queries(
        self, client, free_course, plan_based_course, multi_plan_course
    ):
        """List view should use prefetch_related for efficiency"""
        # This test would ideally use django-debug-toolbar or assertNumQueries
        # For now, we just verify it works with multiple courses
        response = client.get('/api/courses/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['total'] == 3
        assert len(data['courses']) == 3
        
        # Verify all have subscription fields
        for course in data['courses']:
            assert 'access_type' in course
            assert 'required_plans' in course
