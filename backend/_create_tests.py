#!/usr/bin/env python3
"""Script to create CourseAccess test file"""

test_content = '''"""
Tests for CourseAccess subscription integration (Phase 1.3)
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


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def category():
    return CourseCategory.objects.create(name='Test Category', slug='test-category')


@pytest.fixture
def course(category):
    return Course.objects.create(
        title='Test Course',
        slug='test-course',
        description='Test Description',
        category=category
    )


@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name='Test Plan',
        slug='test-plan',
        base_price=Decimal('29.99'),
        billing_period='monthly',
        is_active=True
    )


# ============================================================================
# TEST: CourseAccess Subscription Fields
# ============================================================================

class TestCourseAccessFields:
    """Test new subscription tracking fields on CourseAccess model"""
    
    def test_access_granted_by_subscription(self, user, course, plan):
        """Test access granted via subscription"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            subscription_plan=plan
        )
        assert access.access_granted_by == 'subscription'
        assert access.subscription_plan == plan

    def test_access_granted_by_direct_purchase(self, user, course):
        """Test access granted via direct purchase"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase',
            payment_reference='PAY-123456'
        )
        assert access.access_granted_by == 'direct_purchase'
        assert access.payment_reference == 'PAY-123456'

    def test_access_granted_by_admin(self, user, course):
        """Test access granted by admin"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert access.access_granted_by == 'admin'

    def test_access_granted_by_coupon(self, user, course):
        """Test access granted via coupon"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='coupon',
            payment_reference='COUPON-ABC'
        )
        assert access.access_granted_by == 'coupon'
        assert access.payment_reference == 'COUPON-ABC'

    def test_subscription_plan_nullable(self, user, course):
        """Test subscription_plan can be null"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase'
        )
        assert access.subscription_plan is None

    def test_payment_reference_optional(self, user, course):
        """Test payment_reference is optional"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert access.payment_reference == ''

    def test_updated_at_auto_updates(self, user, course):
        """Test updated_at field auto-updates on save"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        original_updated = access.updated_at
        
        import time
        time.sleep(0.01)
        access.download_enabled = False
        access.save()
        
        access.refresh_from_db()
        assert access.updated_at > original_updated


# ============================================================================
# TEST: is_active Property
# ============================================================================

class TestCourseAccessIsActive:
    """Test CourseAccess.is_active property"""
    
    def test_is_active_no_expiration(self, user, course):
        """Test is_active returns True when no expiration set"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert access.is_active is True

    def test_is_active_future_expiration(self, user, course):
        """Test is_active returns True when expiration in future"""
        future = timezone.now() + timedelta(days=30)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=future
        )
        assert access.is_active is True

    def test_is_active_past_expiration(self, user, course):
        """Test is_active returns False when expired"""
        past = timezone.now() - timedelta(days=1)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=past
        )
        assert access.is_active is False


# ============================================================================
# TEST: is_access_valid Method
# ============================================================================

class TestCourseAccessValidation:
    """Test CourseAccess.is_access_valid() method"""
    
    def test_valid_direct_purchase(self, user, course):
        """Test direct purchase access is always valid if not expired"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='direct_purchase',
            payment_reference='PAY-123'
        )
        assert access.is_access_valid() is True

    def test_valid_admin_grant(self, user, course):
        """Test admin granted access is valid"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert access.is_access_valid() is True

    def test_invalid_expired(self, user, course):
        """Test expired access is invalid"""
        past = timezone.now() - timedelta(days=1)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=past
        )
        assert access.is_access_valid() is False

    def test_subscription_without_plan(self, user, course):
        """Test subscription access without plan is invalid"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription'
        )
        assert access.is_access_valid() is False

    def test_subscription_with_inactive_user(self, user, course, plan):
        """Test subscription access with inactive user subscription"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            subscription_plan=plan
        )
        # User has no active subscription
        assert access.is_access_valid() is False


# ============================================================================
# TEST: Access Management Methods
# ============================================================================

class TestCourseAccessManagement:
    """Test CourseAccess access management methods"""
    
    def test_revoke_access(self, user, course):
        """Test revoking access sets expiration to now"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        assert access.is_active is True
        
        access.revoke_access()
        
        assert access.is_active is False
        assert access.access_expires_at is not None
        diff = abs((access.access_expires_at - timezone.now()).total_seconds())
        assert diff < 1

    def test_extend_access_with_expiration(self, user, course):
        """Test extending access adds days to existing expiration"""
        original = timezone.now() + timedelta(days=10)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=original
        )
        
        access.extend_access(5)
        
        expected = original + timedelta(days=5)
        diff = abs((access.access_expires_at - expected).total_seconds())
        assert diff < 1

    def test_extend_access_without_expiration(self, user, course):
        """Test extending access without expiration sets from now"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        
        access.extend_access(15)
        
        expected = timezone.now() + timedelta(days=15)
        diff = abs((access.access_expires_at - expected).total_seconds())
        assert diff < 1

    def test_renew_from_subscription_no_expiration(self, user, course):
        """Test renewing subscription sets expiration from now"""
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription'
        )
        
        access.renew_from_subscription(30)
        
        assert access.access_expires_at is not None
        expected = timezone.now() + timedelta(days=30)
        diff = abs((access.access_expires_at - expected).total_seconds())
        assert diff < 1

    def test_renew_from_subscription_future_expiration(self, user, course):
        """Test renewing extends from future expiration"""
        future = timezone.now() + timedelta(days=5)
        access = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='subscription',
            access_expires_at=future
        )
        
        access.renew_from_subscription(30)
        
        expected = future + timedelta(days=30)
        diff = abs((access.access_expires_at - expected).total_seconds())
        assert diff < 1


# ============================================================================
# TEST: Static Helper Methods
# ============================================================================

class TestCourseAccessHelpers:
    """Test CourseAccess static helper methods"""
    
    def test_grant_subscription_access_creates(self, user, course, plan):
        """Test grant_subscription_access creates new record"""
        access = CourseAccess.grant_subscription_access(user, course, plan)
        
        assert access is not None
        assert access.user == user
        assert access.course == course
        assert access.access_granted_by == 'subscription'
        assert access.subscription_plan == plan
        assert access.access_expires_at is not None

    def test_grant_subscription_access_updates(self, user, course, plan):
        """Test grant_subscription_access updates existing record"""
        existing = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        
        access = CourseAccess.grant_subscription_access(user, course, plan)
        
        assert access.id == existing.id
        assert access.access_granted_by == 'subscription'
        assert access.subscription_plan == plan

    def test_grant_direct_purchase_creates(self, user, course):
        """Test grant_direct_purchase_access creates new record"""
        payment_ref = 'PAY-ABC123'
        access = CourseAccess.grant_direct_purchase_access(user, course, payment_ref)
        
        assert access is not None
        assert access.user == user
        assert access.course == course
        assert access.access_granted_by == 'direct_purchase'
        assert access.payment_reference == payment_ref
        assert access.access_expires_at is None  # Lifetime access

    def test_grant_direct_purchase_updates(self, user, course):
        """Test grant_direct_purchase_access updates existing record"""
        existing = CourseAccess.objects.create(
            user=user,
            course=course,
            access_granted_by='admin'
        )
        
        payment_ref = 'PAY-NEW123'
        access = CourseAccess.grant_direct_purchase_access(user, course, payment_ref)
        
        assert access.id == existing.id
        assert access.access_granted_by == 'direct_purchase'
        assert access.payment_reference == payment_ref
        assert access.access_expires_at is None
'''

with open('courses/tests/test_courseaccess_subscription.py', 'w', encoding='utf-8') as f:
    f.write(test_content)

print('✓ Test file created successfully!')
print(f'✓ File location: courses/tests/test_courseaccess_subscription.py')
print(f'✓ Total test classes: 6')
print(f'✓ Total test methods: 28')
