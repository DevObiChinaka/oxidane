"""
Tests for CourseAccess Admin Interface

This test verifies that the CourseAccess admin interface works correctly
and displays subscription-related fields properly.
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from courses.models import Course, CourseAccess, CourseCategory
from courses.admin import CourseAccessAdmin, CourseAdmin
from subscriptions.models import SubscriptionPlan, Feature

User = get_user_model()


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def category():
    return CourseCategory.objects.create(name='Test Category', slug='test-category')


@pytest.fixture
def course(category):
    return Course.objects.create(
        title='Test Course',
        slug='test-course',
        description='Test Description',
        category=category,
        access_type='plan_based'
    )


@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name='Test Plan',
        slug='test-plan',
        billing_period='monthly',
        price=29.99
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        email='testuser@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.mark.django_db
class TestCourseAccessAdmin:
    """Test CourseAccess admin interface"""
    
    def test_admin_is_registered(self, admin_site):
        """Test that CourseAccess admin is registered"""
        from django.contrib import admin
        assert admin.site.is_registered(CourseAccess)
    
    def test_list_display_fields(self, admin_site):
        """Test that list_display contains expected fields"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        expected_fields = [
            'user_email',
            'course_title',
            'access_granted_by',
            'subscription_plan',
            'access_status',
            'access_granted_at',
            'expiration_display',
        ]
        assert admin_instance.list_display == expected_fields
    
    def test_list_filter_fields(self, admin_site):
        """Test that list_filter contains subscription fields"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        assert 'access_granted_by' in admin_instance.list_filter
        assert 'subscription_plan' in admin_instance.list_filter
    
    def test_search_fields(self, admin_site):
        """Test that search includes user and course fields"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        assert 'user__email' in admin_instance.search_fields
        assert 'course__title' in admin_instance.search_fields
        assert 'payment_reference' in admin_instance.search_fields
    
    def test_user_email_display(self, admin_site, user, course):
        """Test user_email display method"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert admin_instance.user_email(access) == user.email
    
    def test_course_title_display(self, admin_site, user, course):
        """Test course_title display method"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert admin_instance.course_title(access) == course.title
    
    def test_access_status_active(self, admin_site, user, course):
        """Test access_status display for active access"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin',
            access_expires_at=timezone.now() + timedelta(days=30)
        )
        result = admin_instance.access_status(access)
        assert '✓ Active' in result
        assert 'green' in result
    
    def test_access_status_expired(self, admin_site, user, course):
        """Test access_status display for expired access"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin',
            access_expires_at=timezone.now() - timedelta(days=1)
        )
        result = admin_instance.access_status(access)
        assert '✗ Expired' in result
        assert 'red' in result
    
    def test_expiration_display_lifetime(self, admin_site, user, course):
        """Test expiration_display for lifetime access"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase'
        )
        result = admin_instance.expiration_display(access)
        assert 'Lifetime' in result
    
    def test_expiration_display_with_date(self, admin_site, user, course):
        """Test expiration_display shows expiration date"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        future_date = timezone.now() + timedelta(days=30)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=future_date
        )
        result = admin_instance.expiration_display(access)
        assert future_date.strftime('%Y-%m-%d') in result
    
    def test_expiration_display_warning(self, admin_site, user, course):
        """Test expiration_display shows warning for soon-to-expire access"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        # Access expiring in 5 days
        future_date = timezone.now() + timedelta(days=5)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=future_date
        )
        result = admin_instance.expiration_display(access)
        assert 'orange' in result  # Warning color
        assert '5d left' in result or '4d left' in result  # Days remaining
    
    def test_readonly_fields(self, admin_site):
        """Test that critical fields are read-only"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        assert 'id' in admin_instance.readonly_fields
        assert 'access_granted_at' in admin_instance.readonly_fields
        assert 'updated_at' in admin_instance.readonly_fields
    
    def test_admin_actions_exist(self, admin_site):
        """Test that custom admin actions are registered"""
        admin_instance = CourseAccessAdmin(CourseAccess, admin_site)
        action_names = [action for action in admin_instance.actions]
        assert 'grant_admin_access' in action_names
        assert 'revoke_access' in action_names
        assert 'extend_access_30_days' in action_names
        assert 'extend_access_90_days' in action_names


@pytest.mark.django_db
class TestCourseAdmin:
    """Test Course admin interface updates"""
    
    def test_admin_is_registered(self):
        """Test that Course admin is registered"""
        from django.contrib import admin
        assert admin.site.is_registered(Course)
    
    def test_list_display_includes_access_type(self, admin_site):
        """Test that list_display includes access_type"""
        admin_instance = CourseAdmin(Course, admin_site)
        assert 'access_type' in admin_instance.list_display
    
    def test_list_filter_includes_access_type(self, admin_site):
        """Test that list_filter includes access_type"""
        admin_instance = CourseAdmin(Course, admin_site)
        assert 'access_type' in admin_instance.list_filter
    
    def test_filter_horizontal_for_required_plans(self, admin_site):
        """Test that required_plans uses horizontal filter widget"""
        admin_instance = CourseAdmin(Course, admin_site)
        assert 'required_plans' in admin_instance.filter_horizontal
    
    def test_subscription_fieldset_exists(self, admin_site):
        """Test that Subscription & Access Settings fieldset exists"""
        admin_instance = CourseAdmin(Course, admin_site)
        fieldset_names = [fieldset[0] for fieldset in admin_instance.fieldsets]
        assert 'Subscription & Access Settings' in fieldset_names
    
    def test_subscription_fields_in_fieldset(self, admin_site):
        """Test that subscription fields are in the fieldset"""
        admin_instance = CourseAdmin(Course, admin_site)
        subscription_fieldset = None
        for name, options in admin_instance.fieldsets:
            if name == 'Subscription & Access Settings':
                subscription_fieldset = options['fields']
                break
        
        assert subscription_fieldset is not None
        assert 'access_type' in subscription_fieldset
        assert 'required_plans' in subscription_fieldset
        assert 'direct_purchase_price' in subscription_fieldset


@pytest.mark.django_db
class TestUserAdmin:
    """Test User admin interface updates"""
    
    def test_admin_is_registered(self):
        """Test that User admin is registered"""
        from django.contrib import admin
        assert admin.site.is_registered(User)
    
    def test_list_display_includes_subscription_fields(self, admin_site):
        """Test that list_display includes subscription fields"""
        from users.admin import UserAdmin
        admin_instance = UserAdmin(User, admin_site)
        assert 'current_plan' in admin_instance.list_display
        assert 'subscription_status' in admin_instance.list_display
    
    def test_list_filter_includes_subscription_fields(self, admin_site):
        """Test that list_filter includes subscription fields"""
        from users.admin import UserAdmin
        admin_instance = UserAdmin(User, admin_site)
        assert 'subscription_status' in admin_instance.list_filter
        assert 'current_plan' in admin_instance.list_filter
    
    def test_subscription_fieldset_exists(self, admin_site):
        """Test that Subscription Information fieldset exists"""
        from users.admin import UserAdmin
        admin_instance = UserAdmin(User, admin_site)
        fieldset_names = [fieldset[0] for fieldset in admin_instance.fieldsets]
        assert 'Subscription Information' in fieldset_names
    
    def test_subscription_fields_readonly(self, admin_site):
        """Test that subscription date fields are read-only"""
        from users.admin import UserAdmin
        admin_instance = UserAdmin(User, admin_site)
        assert 'subscription_start_date' in admin_instance.readonly_fields
        assert 'subscription_end_date' in admin_instance.readonly_fields
        assert 'trial_end_date' in admin_instance.readonly_fields
    
    def test_custom_actions_exist(self, admin_site):
        """Test that custom actions are registered"""
        from users.admin import UserAdmin
        admin_instance = UserAdmin(User, admin_site)
        action_names = [action for action in admin_instance.actions if action != 'delete_selected']
        assert 'start_trial' in action_names
        assert 'cancel_subscription' in action_names
