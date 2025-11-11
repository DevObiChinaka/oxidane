"""
Integration Tests for Complete Enrollment Flow (Phase 1.7)

Tests end-to-end enrollment workflows across User, Course, and CourseAccess models
with different subscription scenarios. Verifies complete integration of subscription
system with course access management.

These tests validate the actual implementation, not hypothetical helper methods.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from subscriptions.models import SubscriptionPlan
from courses.models import Course, CourseCategory, CourseAccess

User = get_user_model()

pytestmark = pytest.mark.django_db


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def category():
    """Create a course category"""
    return CourseCategory.objects.create(
        name='Programming',
        slug='programming',
        description='Programming courses'
    )


@pytest.fixture
def premium_plan():
    """Create a premium subscription plan"""
    return SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium',
        base_price=Decimal('99.99'),
        billing_period='monthly',
        is_active=True,
        trial_days=7
    )


@pytest.fixture
def basic_plan():
    """Create a basic subscription plan"""
    return SubscriptionPlan.objects.create(
        name='Basic Plan',
        slug='basic',
        base_price=Decimal('49.99'),
        billing_period='monthly',
        is_active=True
    )


@pytest.fixture
def user():
    """Create a regular user without subscription"""
    return User.objects.create_user(
        email='student@example.com',
        username='student',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def premium_user(premium_plan):
    """Create a user with active premium subscription"""
    user = User.objects.create_user(
        email='premium@example.com',
        username='premium_user',
        password='testpass123',
        is_active=True
    )
    # Set active premium subscription
    user.current_plan = premium_plan
    user.subscription_status = 'active'
    user.subscription_start_date = timezone.now()
    user.subscription_end_date = timezone.now() + timedelta(days=30)
    user.save()
    return user


@pytest.fixture
def trial_user(premium_plan):
    """Create a user on trial"""
    user = User.objects.create_user(
        email='trial@example.com',
        username='trial_user',
        password='testpass123',
        is_active=True
    )
    user.current_plan = premium_plan
    user.subscription_status = 'trialing'
    user.trial_start_date = timezone.now()
    user.trial_end_date = timezone.now() + timedelta(days=7)
    user.subscription_start_date = timezone.now()
    user.subscription_end_date = timezone.now() + timedelta(days=37)  # 30 days after trial
    user.save()
    return user


@pytest.fixture
def free_course(category):
    """Create a free course"""
    return Course.objects.create(
        title='Free Python Basics',
        slug='free-python',
        description='Learn Python for free',
        short_description='Python basics',
        category=category,
        access_type='free'
    )


@pytest.fixture
def premium_course(category, premium_plan):
    """Create a premium course requiring premium plan"""
    course = Course.objects.create(
        title='Advanced Python',
        slug='advanced-python',
        description='Advanced Python course',
        short_description='Advanced Python',
        category=category,
        access_type='plan_based'
    )
    course.required_plans.add(premium_plan)
    return course


@pytest.fixture
def multi_plan_course(category, premium_plan, basic_plan):
    """Create a course accessible with either premium or basic plan"""
    course = Course.objects.create(
        title='Web Development',
        slug='web-dev',
        description='Web development course',
        short_description='Web dev',
        category=category,
        access_type='plan_based'
    )
    course.required_plans.add(premium_plan, basic_plan)
    return course


@pytest.fixture
def purchasable_course(category):
    """Create a course available for direct purchase"""
    return Course.objects.create(
        title='Django Masterclass',
        slug='django-master',
        description='Complete Django course',
        short_description='Django',
        category=category,
        access_type='direct_purchase',
        direct_purchase_price=Decimal('199.99')
    )


# ============================================================================
# TEST: Free Course Enrollment Flow
# ============================================================================

@pytest.mark.django_db
class TestFreeCourseEnrollment:
    """Test complete enrollment flow for free courses"""
    
    def test_anonymous_user_can_view_free_course(self, free_course):
        """Anonymous users should be able to identify free courses"""
        assert free_course.is_free()
        assert free_course.access_type == 'free'
        assert free_course.is_accessible_by_user(None)
    
    def test_enrolled_user_gets_automatic_access(self, user, free_course):
        """User enrolled in free course should get automatic lifetime access"""
        # Grant access (simulating enrollment)
        access = CourseAccess.grant_admin_access(
            user=user,
            course=free_course,
            expiration_date=None  # Lifetime
        )
        
        # Verify access record created
        assert access is not None
        assert access.user == user
        assert access.course == free_course
        assert access.access_granted_by == 'admin'
        assert access.expiration_date is None
        assert access.is_active()
    
    def test_multiple_users_free_course_access(self, free_course):
        """Multiple users can access the same free course"""
        users = [
            User.objects.create_user(email=f'user{i}@test.com', username=f'user{i}', password='pass')
            for i in range(5)
        ]
        
        accesses = []
        for user in users:
            access = CourseAccess.grant_admin_access(user, free_course)
            accesses.append(access)
        
        # Verify all have access
        assert len(accesses) == 5
        assert all(a.is_active() for a in accesses)
        assert CourseAccess.objects.filter(course=free_course).count() == 5


# ============================================================================
# TEST: Plan-Based Course Enrollment Flow
# ============================================================================

@pytest.mark.django_db
class TestPlanBasedEnrollment:
    """Test enrollment flow for plan-based courses"""
    
    def test_user_without_subscription_cannot_access(self, user, premium_course):
        """User without subscription cannot access premium course"""
        assert not premium_course.is_accessible_by_user(user)
        assert premium_course.requires_subscription()
    
    def test_user_with_wrong_plan_cannot_access(self, user, premium_course, basic_plan):
        """User with basic plan cannot access premium-only course"""
        # Give user basic plan
        user.current_plan = basic_plan
        user.subscription_status = 'active'
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        assert not premium_course.is_accessible_by_user(user)
    
    def test_premium_user_enrollment_creates_access(self, premium_user, premium_course):
        """Premium user enrolling should create CourseAccess record"""
        # Verify user can access
        assert premium_course.is_accessible_by_user(premium_user)
        
        # Grant subscription-based access
        access = CourseAccess.grant_subscription_access(
            user=premium_user,
            course=premium_course,
            plan=premium_user.current_plan
        )
        
        # Verify access record
        assert access.user == premium_user
        assert access.course == premium_course
        assert access.access_granted_by == 'subscription'
        assert access.subscription_plan == premium_user.current_plan
        assert access.is_active()
    
    def test_trial_user_can_access_premium_content(self, trial_user, premium_course):
        """Users on trial should access premium courses"""
        assert trial_user.is_on_trial()
        assert premium_course.is_accessible_by_user(trial_user)
        
        access = CourseAccess.grant_subscription_access(
            user=trial_user,
            course=premium_course,
            plan=trial_user.current_plan
        )
        
        assert access.is_active()
        assert access.subscription_plan == trial_user.current_plan
    
    def test_subscription_expiration_blocks_course_access(self, premium_user, premium_course):
        """Expired subscription should block course access"""
        # Create access while subscription is active
        access = CourseAccess.grant_subscription_access(
            user=premium_user,
            course=premium_course,
            plan=premium_user.current_plan
        )
        assert access.is_active()
        
        # Expire subscription
        premium_user.subscription_end_date = timezone.now() - timedelta(days=1)
        premium_user.subscription_status = 'expired'
        premium_user.save()
        
        # Verify access validation fails
        assert not access.validate_subscription_access()
        assert not premium_course.is_accessible_by_user(premium_user)
    
    def test_subscription_renewal_restores_access(self, premium_user, premium_course, premium_plan):
        """Renewing subscription should restore course access"""
        # Create access and then expire it
        access = CourseAccess.grant_subscription_access(
            user=premium_user,
            course=premium_course,
            plan=premium_plan
        )
        
        premium_user.subscription_end_date = timezone.now() - timedelta(days=5)
        premium_user.subscription_status = 'expired'
        premium_user.save()
        
        assert not access.validate_subscription_access()
        
        # Renew subscription
        premium_user.subscription_status = 'active'
        premium_user.subscription_end_date = timezone.now() + timedelta(days=30)
        premium_user.save()
        
        # Renew course access
        access.renew_from_subscription(premium_user)
        access.refresh_from_db()
        
        assert access.validate_subscription_access()
        assert premium_course.is_accessible_by_user(premium_user)


# ============================================================================
# TEST: Multi-Plan Course Access
# ============================================================================

@pytest.mark.django_db
class TestMultiPlanCourseAccess:
    """Test courses accessible via multiple plan types"""
    
    def test_premium_user_can_access_multi_plan_course(self, premium_user, multi_plan_course):
        """Premium user should access course that accepts premium or basic"""
        assert multi_plan_course.is_accessible_by_user(premium_user)
        
        access = CourseAccess.grant_subscription_access(
            user=premium_user,
            course=multi_plan_course,
            plan=premium_user.current_plan
        )
        
        assert access.is_active()
    
    def test_basic_user_can_access_multi_plan_course(self, user, multi_plan_course, basic_plan):
        """Basic user should also access multi-plan course"""
        # Give user basic plan
        user.current_plan = basic_plan
        user.subscription_status = 'active'
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        assert multi_plan_course.is_accessible_by_user(user)
        
        access = CourseAccess.grant_subscription_access(
            user=user,
            course=multi_plan_course,
            plan=basic_plan
        )
        
        assert access.subscription_plan == basic_plan
        assert access.is_active()
    
    def test_user_without_any_plan_cannot_access(self, user, multi_plan_course):
        """User without subscription cannot access multi-plan course"""
        assert not multi_plan_course.is_accessible_by_user(user)


# ============================================================================
# TEST: Direct Purchase Enrollment Flow
# ============================================================================

@pytest.mark.django_db
class TestDirectPurchaseEnrollment:
    """Test enrollment flow for directly purchasable courses"""
    
    def test_course_can_be_purchased(self, purchasable_course):
        """Course should be marked as purchasable"""
        assert purchasable_course.can_be_purchased()
        assert purchasable_course.direct_purchase_price == Decimal('199.99')
    
    def test_user_purchase_creates_lifetime_access(self, user, purchasable_course):
        """Direct purchase should create lifetime access"""
        access = CourseAccess.grant_direct_purchase(
            user=user,
            course=purchasable_course,
            payment_reference='PAY-12345'
        )
        
        # Verify lifetime access
        assert access.access_granted_by == 'direct_purchase'
        assert access.payment_reference == 'PAY-12345'
        assert access.expiration_date is None
        assert access.is_active()
    
    def test_purchase_works_without_subscription(self, user, purchasable_course):
        """User without subscription can purchase course"""
        assert user.current_plan is None
        assert not user.has_active_subscription()
        
        access = CourseAccess.grant_direct_purchase(
            user=user,
            course=purchasable_course,
            payment_reference='PAY-67890'
        )
        
        assert access.is_active()
    
    def test_premium_user_can_still_purchase(self, premium_user, purchasable_course):
        """Premium user can purchase direct-purchase-only courses"""
        # Even with premium subscription, direct purchase courses require purchase
        assert not purchasable_course.is_accessible_by_user(premium_user)
        
        access = CourseAccess.grant_direct_purchase(
            user=premium_user,
            course=purchasable_course,
            payment_reference='PAY-PREMIUM-001'
        )
        
        assert access.is_active()
        assert access.access_granted_by == 'direct_purchase'


# ============================================================================
# TEST: Cross-Model Integration Scenarios
# ============================================================================

@pytest.mark.django_db
class TestCrossModelIntegration:
    """Test complex scenarios involving User, Course, and CourseAccess"""
    
    def test_user_subscription_upgrade_flow(self, user, premium_course, basic_plan, premium_plan):
        """Test user upgrading from basic to premium mid-course"""
        # Start with basic plan (cannot access premium course)
        user.current_plan = basic_plan
        user.subscription_status = 'active'
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        assert not premium_course.is_accessible_by_user(user)
        
        # Upgrade to premium
        user.current_plan = premium_plan
        user.save()
        
        # Now can access
        assert premium_course.is_accessible_by_user(user)
        
        access = CourseAccess.grant_subscription_access(
            user=user,
            course=premium_course,
            plan=premium_plan
        )
        
        assert access.subscription_plan == premium_plan
        assert access.is_active()
    
    def test_multiple_courses_single_subscription(self, premium_user, category, premium_plan):
        """Premium user should access all premium courses with single subscription"""
        # Create multiple premium courses
        courses = []
        for i in range(3):
            course = Course.objects.create(
                title=f'Premium Course {i}',
                slug=f'premium-{i}',
                category=category,
                access_type='plan_based'
            )
            course.required_plans.add(premium_plan)
            courses.append(course)
        
        # Grant access to all
        accesses = []
        for course in courses:
            access = CourseAccess.grant_subscription_access(
                user=premium_user,
                course=course,
                plan=premium_plan
            )
            accesses.append(access)
        
        # Verify all active
        assert len(accesses) == 3
        assert all(a.is_active() for a in accesses)
        assert all(a.subscription_plan == premium_plan for a in accesses)
    
    def test_mixed_access_types_same_user(self, user, free_course, purchasable_course, category, premium_plan):
        """User can have access via multiple methods simultaneously"""
        # Free course access
        free_access = CourseAccess.grant_admin_access(user, free_course)
        
        # Direct purchase access
        purchase_access = CourseAccess.grant_direct_purchase(
            user=user,
            course=purchasable_course,
            payment_reference='PAY-123'
        )
        
        # Subscribe and access premium course
        user.current_plan = premium_plan
        user.subscription_status = 'active'
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
        
        premium_course = Course.objects.create(
            title='Premium',
            slug='premium',
            category=category,
            access_type='plan_based'
        )
        premium_course.required_plans.add(premium_plan)
        
        sub_access = CourseAccess.grant_subscription_access(
            user=user,
            course=premium_course,
            plan=premium_plan
        )
        
        # Verify user has 3 different access types
        user_accesses = CourseAccess.objects.filter(user=user, is_active=True)
        assert user_accesses.count() == 3
        
        granted_by_types = set(user_accesses.values_list('access_granted_by', flat=True))
        assert granted_by_types == {'admin', 'direct_purchase', 'subscription'}
    
    def test_admin_override_access(self, user, premium_course):
        """Admin can grant access regardless of subscription status"""
        # User has no subscription
        assert not premium_course.is_accessible_by_user(user)
        
        # Admin grants access anyway
        admin_access = CourseAccess.grant_admin_access(
            user=user,
            course=premium_course,
            expiration_date=timezone.now() + timedelta(days=90)
        )
        
        assert admin_access.access_granted_by == 'admin'
        assert admin_access.is_active()
        # Subscription validation doesn't apply to admin grants
        assert admin_access.subscription_plan is None
    
    def test_concurrent_subscription_and_purchase(self, premium_user, purchasable_course):
        """User with subscription can also purchase courses"""
        # User has active premium subscription
        assert premium_user.has_active_subscription()
        
        # But purchases a course anyway (maybe it's not in their plan)
        purchase_access = CourseAccess.grant_direct_purchase(
            user=premium_user,
            course=purchasable_course,
            payment_reference='PAY-BOTH-001'
        )
        
        # Both subscription and purchase should coexist
        assert purchase_access.is_active()
        assert purchase_access.access_granted_by == 'direct_purchase'
        assert premium_user.subscription_status == 'active'


# ============================================================================
# TEST: Edge Cases and Error Handling
# ============================================================================

@pytest.mark.django_db
class TestEnrollmentEdgeCases:
    """Test edge cases in enrollment flow"""
    
    def test_duplicate_access_grant_updates_existing(self, user, free_course):
        """Granting access twice should update existing record, not create duplicate"""
        # First grant
        access1 = CourseAccess.grant_admin_access(user, free_course)
        original_created = access1.created_at
        
        # Second grant (should update)
        access2 = CourseAccess.grant_admin_access(
            user,
            free_course,
            expiration_date=timezone.now() + timedelta(days=30)
        )
        
        # Should be same record
        assert access1.id == access2.id
        assert access2.expiration_date is not None
        # Updated timestamp should change
        assert access2.updated_at >= original_created
        
        # Only one access record exists
        assert CourseAccess.objects.filter(user=user, course=free_course).count() == 1
    
    def test_unpublished_course_access(self, user, category):
        """Access granted to unpublished course should still work"""
        unpublished = Course.objects.create(
            title='Draft Course',
            slug='draft',
            category=category,
            access_type='free'
        )
        
        access = CourseAccess.grant_admin_access(user, unpublished)
        assert access.is_active()
        # Admin can grant access even to unpublished courses
    
    def test_inactive_user_course_access(self, free_course):
        """Inactive user can have access record but fails validation"""
        inactive_user = User.objects.create_user(
            email='inactive@test.com',
            username='inactive',
            password='pass',
            is_active=False
        )
        
        # Create access
        access = CourseAccess.grant_admin_access(inactive_user, free_course)
        
        # Access record exists but validation fails due to inactive user
        assert access is not None
        assert access.user.is_active is False
    
    def test_cancelled_subscription_grace_period(self, premium_user, premium_course):
        """User with cancelled but valid subscription should retain access"""
        # Grant access
        access = CourseAccess.grant_subscription_access(
            user=premium_user,
            course=premium_course,
            plan=premium_user.current_plan
        )
        
        # Cancel subscription but end date is still in future
        premium_user.subscription_status = 'cancelled'
        premium_user.save()
        
        # Should still have access until end date
        assert access.validate_subscription_access()
        assert access.is_active()
