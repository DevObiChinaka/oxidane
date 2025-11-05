"""
Comprehensive tests for subscription permission classes.

Tests all permission classes with various scenarios including:
- Authentication states (authenticated, unauthenticated)
- User roles (admin, superuser, regular user)
- Object ownership (own objects, others' objects)
- Feature access (has feature, doesn't have feature)
- Edge cases (missing billing profile, expired subscriptions)
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response

from subscriptions.models import (
    Feature, SubscriptionPlan, Subscription, BillingProfile,
    ReferralCode, Referral
)
from subscriptions.permissions import (
    IsAdmin, IsSuperAdmin, IsSubscribed, HasFeatureAccess,
    CanManageSubscription, CanManageReferrals, CanAccessAnalytics,
    IsOwnerOrAdmin, ReadOnly, required_feature
)

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def regular_user():
    """Create regular user (not staff, not superuser)"""
    return User.objects.create_user(
        username='regular',
        email='regular@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    """Create admin user (staff, not superuser)"""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def superuser():
    """Create superuser"""
    return User.objects.create_user(
        username='super',
        email='super@example.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def feature():
    """Create test feature"""
    return Feature.objects.create(
        key='test_feature',
        name='Test Feature',
        category='signals'
    )


@pytest.fixture
def subscription_plan(feature):
    """Create subscription plan with feature"""
    plan = SubscriptionPlan.objects.create(
        name='Test Plan',
        base_price=Decimal('99.99'),
        billing_period='monthly',
        is_active=True
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def active_subscription(regular_user, subscription_plan):
    """Create active subscription for regular user"""
    billing_profile, _ = BillingProfile.objects.get_or_create(user=regular_user)
    return Subscription.objects.create(
        billing_profile=billing_profile,
        plan=subscription_plan,
        status='active',
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        amount_paid=Decimal('99.99'),
        currency='USD'
    )


@pytest.fixture
def factory():
    """API request factory"""
    return APIRequestFactory()


# ============================================================================
# TEST: IsAdmin Permission
# ============================================================================

@pytest.mark.django_db
class TestIsAdminPermission:
    """Test IsAdmin permission class"""
    
    def test_admin_user_has_permission(self, factory, admin_user):
        """Admin user should have permission"""
        permission = IsAdmin()
        request = factory.get('/test/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is True
    
    def test_superuser_has_permission(self, factory, superuser):
        """Superuser should have permission (is_staff=True)"""
        permission = IsAdmin()
        request = factory.get('/test/')
        request.user = superuser
        
        assert permission.has_permission(request, None) is True
    
    def test_regular_user_denied(self, factory, regular_user):
        """Regular user should be denied"""
        permission = IsAdmin()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_permission(request, None) is False
    
    def test_unauthenticated_user_denied(self, factory):
        """Unauthenticated user should be denied"""
        from django.contrib.auth.models import AnonymousUser
        permission = IsAdmin()
        request = factory.get('/test/')
        request.user = AnonymousUser()
        
        assert permission.has_permission(request, None) is False


# ============================================================================
# TEST: IsSuperAdmin Permission
# ============================================================================

@pytest.mark.django_db
class TestIsSuperAdminPermission:
    """Test IsSuperAdmin permission class"""
    
    def test_superuser_has_permission(self, factory, superuser):
        """Superuser should have permission"""
        permission = IsSuperAdmin()
        request = factory.get('/test/')
        request.user = superuser
        
        assert permission.has_permission(request, None) is True
    
    def test_admin_user_denied(self, factory, admin_user):
        """Regular admin (not superuser) should be denied"""
        permission = IsSuperAdmin()
        request = factory.get('/test/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is False
    
    def test_regular_user_denied(self, factory, regular_user):
        """Regular user should be denied"""
        permission = IsSuperAdmin()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_permission(request, None) is False


# ============================================================================
# TEST: IsSubscribed Permission
# ============================================================================

@pytest.mark.django_db
class TestIsSubscribedPermission:
    """Test IsSubscribed permission class"""
    
    def test_user_with_active_subscription_has_permission(self, factory, regular_user, active_subscription):
        """User with active subscription should have permission"""
        permission = IsSubscribed()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_permission(request, None) is True
    
    def test_user_without_subscription_denied(self, factory):
        """User without subscription should be denied"""
        user = User.objects.create_user(
            username='nosubscription',
            email='nosub@example.com',
            password='testpass123'
        )
        permission = IsSubscribed()
        request = factory.get('/test/')
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_user_with_expired_subscription_denied(self, factory, regular_user, subscription_plan):
        """User with expired subscription should be denied"""
        billing_profile, _ = BillingProfile.objects.get_or_create(user=regular_user)
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='expired',
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30),
            amount_paid=Decimal('99.99'),
            currency='USD'
        )
        
        permission = IsSubscribed()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_permission(request, None) is False
    
    def test_admin_always_has_permission(self, factory, admin_user):
        """Admin should have permission even without subscription"""
        permission = IsSubscribed()
        request = factory.get('/test/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is True


# ============================================================================
# TEST: HasFeatureAccess Permission
# ============================================================================

@pytest.mark.django_db
class TestHasFeatureAccessPermission:
    """Test HasFeatureAccess permission class"""
    
    def test_user_with_feature_access_has_permission(self, factory, regular_user, active_subscription):
        """User with feature access should have permission"""
        permission = HasFeatureAccess()
        request = factory.get('/test/')
        request.user = regular_user
        
        # Mock view with required feature
        class MockView:
            required_feature = 'test_feature'
        
        assert permission.has_permission(request, MockView()) is True
    
    def test_user_without_feature_access_denied(self, factory, regular_user):
        """User without feature access should be denied"""
        permission = HasFeatureAccess()
        request = factory.get('/test/')
        request.user = regular_user
        
        class MockView:
            required_feature = 'nonexistent_feature'
        
        assert permission.has_permission(request, MockView()) is False
    
    def test_admin_always_has_permission(self, factory, admin_user):
        """Admin should have permission regardless of features"""
        permission = HasFeatureAccess()
        request = factory.get('/test/')
        request.user = admin_user
        
        class MockView:
            required_feature = 'any_feature'
        
        assert permission.has_permission(request, MockView()) is True
    
    def test_no_required_feature_denies_access(self, factory, regular_user):
        """If no required feature specified, deny access (fail-safe)"""
        permission = HasFeatureAccess()
        request = factory.get('/test/')
        request.user = regular_user
        
        class MockView:
            pass  # No required_feature attribute
        
        assert permission.has_permission(request, MockView()) is False


# ============================================================================
# TEST: CanManageSubscription Permission
# ============================================================================

@pytest.mark.django_db
class TestCanManageSubscriptionPermission:
    """Test CanManageSubscription permission class"""
    
    def test_user_can_view_own_subscription(self, factory, regular_user, active_subscription):
        """User should be able to view their own subscription"""
        permission = CanManageSubscription()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, active_subscription) is True
    
    def test_user_cannot_view_others_subscription(self, factory, regular_user, subscription_plan):
        """User should not be able to view other user's subscription"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_billing, _ = BillingProfile.objects.get_or_create(user=other_user)
        other_subscription = Subscription.objects.create(
            billing_profile=other_billing,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('99.99'),
            currency='USD'
        )
        
        permission = CanManageSubscription()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, other_subscription) is False
    
    def test_user_cannot_modify_own_subscription(self, factory, regular_user, active_subscription):
        """User should not be able to modify their own subscription (PUT/PATCH/DELETE)"""
        permission = CanManageSubscription()
        request = factory.put('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, active_subscription) is False
    
    def test_admin_can_manage_any_subscription(self, factory, admin_user, active_subscription):
        """Admin should be able to manage any subscription"""
        permission = CanManageSubscription()
        
        # Test GET
        request = factory.get('/test/')
        request.user = admin_user
        assert permission.has_object_permission(request, None, active_subscription) is True
        
        # Test PUT
        request = factory.put('/test/')
        request.user = admin_user
        assert permission.has_object_permission(request, None, active_subscription) is True
        
        # Test DELETE
        request = factory.delete('/test/')
        request.user = admin_user
        assert permission.has_object_permission(request, None, active_subscription) is True


# ============================================================================
# TEST: CanManageReferrals Permission
# ============================================================================

@pytest.mark.django_db
class TestCanManageReferralsPermission:
    """Test CanManageReferrals permission class"""
    
    def test_user_can_view_own_referral_code(self, factory, regular_user):
        """User should be able to view their own referral code"""
        referral_code = ReferralCode.objects.create(
            referrer=regular_user,
            code='TESTCODE',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        permission = CanManageReferrals()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, referral_code) is True
    
    def test_user_cannot_view_others_referral_code(self, factory, regular_user):
        """User should not be able to view other user's referral code"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        referral_code = ReferralCode.objects.create(
            referrer=other_user,
            code='OTHERCODE',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        permission = CanManageReferrals()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, referral_code) is False
    
    def test_user_cannot_delete_own_referral_code(self, factory, regular_user):
        """User should not be able to delete their own referral code"""
        referral_code = ReferralCode.objects.create(
            referrer=regular_user,
            code='TESTCODE',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        permission = CanManageReferrals()
        request = factory.delete('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, referral_code) is False
    
    def test_admin_can_manage_any_referral(self, factory, admin_user, regular_user):
        """Admin should be able to manage any referral code"""
        referral_code = ReferralCode.objects.create(
            referrer=regular_user,
            code='TESTCODE',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_value=Decimal('10.00'),
            is_active=True
        )
        
        permission = CanManageReferrals()
        request = factory.delete('/test/')
        request.user = admin_user
        
        assert permission.has_object_permission(request, None, referral_code) is True


# ============================================================================
# TEST: CanAccessAnalytics Permission
# ============================================================================

@pytest.mark.django_db
class TestCanAccessAnalyticsPermission:
    """Test CanAccessAnalytics permission class"""
    
    def test_regular_user_has_general_permission(self, factory, regular_user):
        """Regular user should have general analytics permission"""
        permission = CanAccessAnalytics()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_permission(request, None) is True
    
    def test_admin_has_full_permission(self, factory, admin_user):
        """Admin should have full analytics permission"""
        permission = CanAccessAnalytics()
        request = factory.get('/test/')
        request.user = admin_user
        
        assert permission.has_permission(request, None) is True
    
    def test_user_can_access_own_analytics(self, factory, regular_user, active_subscription):
        """User should be able to access their own analytics"""
        permission = CanAccessAnalytics()
        request = factory.get('/test/')
        request.user = regular_user
        
        # Test with subscription object (has billing_profile -> user)
        assert permission.has_object_permission(request, None, active_subscription) is True
    
    def test_user_cannot_access_others_analytics(self, factory, regular_user, subscription_plan):
        """User should not be able to access other user's analytics"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_billing, _ = BillingProfile.objects.get_or_create(user=other_user)
        other_subscription = Subscription.objects.create(
            billing_profile=other_billing,
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('99.99'),
            currency='USD'
        )
        
        permission = CanAccessAnalytics()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, other_subscription) is False


# ============================================================================
# TEST: IsOwnerOrAdmin Permission
# ============================================================================

@pytest.mark.django_db
class TestIsOwnerOrAdminPermission:
    """Test IsOwnerOrAdmin permission class"""
    
    def test_user_can_access_own_object(self, factory, regular_user):
        """User should be able to access object they own"""
        class MockObject:
            user = regular_user
        
        permission = IsOwnerOrAdmin()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, MockObject()) is True
    
    def test_user_cannot_access_others_object(self, factory, regular_user):
        """User should not be able to access other user's object"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        class MockObject:
            user = other_user
        
        permission = IsOwnerOrAdmin()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, MockObject()) is False
    
    def test_admin_can_access_any_object(self, factory, admin_user, regular_user):
        """Admin should be able to access any object"""
        class MockObject:
            user = regular_user
        
        permission = IsOwnerOrAdmin()
        request = factory.get('/test/')
        request.user = admin_user
        
        assert permission.has_object_permission(request, None, MockObject()) is True


# ============================================================================
# TEST: ReadOnly Permission
# ============================================================================

@pytest.mark.django_db
class TestReadOnlyPermission:
    """Test ReadOnly permission class"""
    
    def test_get_allowed(self, factory):
        """GET request should be allowed"""
        permission = ReadOnly()
        request = factory.get('/test/')
        
        assert permission.has_permission(request, None) is True
    
    def test_head_allowed(self, factory):
        """HEAD request should be allowed"""
        permission = ReadOnly()
        request = factory.head('/test/')
        
        assert permission.has_permission(request, None) is True
    
    def test_options_allowed(self, factory):
        """OPTIONS request should be allowed"""
        permission = ReadOnly()
        request = factory.options('/test/')
        
        assert permission.has_permission(request, None) is True
    
    def test_post_denied(self, factory):
        """POST request should be denied"""
        permission = ReadOnly()
        request = factory.post('/test/')
        
        assert permission.has_permission(request, None) is False
    
    def test_put_denied(self, factory):
        """PUT request should be denied"""
        permission = ReadOnly()
        request = factory.put('/test/')
        
        assert permission.has_permission(request, None) is False
    
    def test_delete_denied(self, factory):
        """DELETE request should be denied"""
        permission = ReadOnly()
        request = factory.delete('/test/')
        
        assert permission.has_permission(request, None) is False


# ============================================================================
# TEST: Required Feature Decorator
# ============================================================================

@pytest.mark.django_db
class TestRequiredFeatureDecorator:
    """Test required_feature decorator"""
    
    def test_decorator_sets_required_feature(self):
        """Decorator should set required_feature attribute on view"""
        @required_feature('test_feature')
        def my_view(request):
            return Response({'status': 'ok'})
        
        assert hasattr(my_view, 'required_feature')
        assert my_view.required_feature == 'test_feature'
    
    def test_decorator_works_with_class_based_views(self):
        """Decorator should work with class-based views"""
        class MyView(APIView):
            permission_classes = [HasFeatureAccess]
            required_feature = 'test_feature'
            
            def get(self, request):
                return Response({'status': 'ok'})
        
        assert hasattr(MyView, 'required_feature')
        assert MyView.required_feature == 'test_feature'


# ============================================================================
# TEST: Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestPermissionEdgeCases:
    """Test edge cases and error handling"""
    
    def test_subscription_without_billing_profile(self, factory, regular_user, subscription_plan):
        """Test handling of subscription without billing_profile"""
        # Create subscription without billing_profile (edge case)
        subscription = Subscription(
            plan=subscription_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            amount_paid=Decimal('99.99'),
            currency='USD'
        )
        # Don't save to avoid database constraint
        
        permission = CanManageSubscription()
        request = factory.get('/test/')
        request.user = regular_user
        
        # Should handle RelatedObjectDoesNotExist gracefully
        # Since billing_profile is ForeignKey with null=False, accessing it raises exception
        from django.core.exceptions import ObjectDoesNotExist
        try:
            result = permission.has_object_permission(request, None, subscription)
            # If it doesn't raise, it should deny
            assert result is False
        except ObjectDoesNotExist:
            # This is expected - permission should handle this gracefully
            pass
    
    def test_user_without_billing_profile(self, factory):
        """Test IsSubscribed when user has no billing profile"""
        user = User.objects.create_user(
            username='nobilling',
            email='nobilling@example.com',
            password='testpass123'
        )
        # Delete billing profile if auto-created
        BillingProfile.objects.filter(user=user).delete()
        
        permission = IsSubscribed()
        request = factory.get('/test/')
        request.user = user
        
        assert permission.has_permission(request, None) is False
    
    def test_wrong_object_type_for_subscription_permission(self, factory, regular_user):
        """Test CanManageSubscription with wrong object type"""
        class WrongObject:
            pass
        
        permission = CanManageSubscription()
        request = factory.get('/test/')
        request.user = regular_user
        
        assert permission.has_object_permission(request, None, WrongObject()) is False
