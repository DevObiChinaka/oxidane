"""
Comprehensive Test Suite for Subscription API Endpoints (Phase 0.5 - Task 0.5.20)

Tests cover:
- Authentication & permissions (users vs admins)
- List operations with filtering
- Retrieve operations with permissions
- Create operations with validation
- Update operations (admin only)
- Delete operations (admin only)
- Cancel custom action
- Reactivate custom action
- Expiring soon custom action
- Statistics custom action (admin only)
- Edge cases and error handling

Total: 35+ tests
"""

import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from subscriptions.models import (
    Subscription, SubscriptionPlan, BillingProfile, Feature
)

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def regular_user(db):
    """Create a regular user"""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def other_user(db):
    """Create another regular user"""
    return User.objects.create_user(
        username='otheruser',
        email='otheruser@example.com',
        password='otherpass123'
    )


@pytest.fixture
def billing_profile(regular_user):
    """Create or get billing profile for regular user (signal may auto-create)"""
    profile, created = BillingProfile.objects.get_or_create(
        user=regular_user,
        defaults={
            'telegram_username': '@testuser',
            'country': 'US',
            'currency_preference': 'USD'
        }
    )
    return profile


@pytest.fixture
def other_billing_profile(other_user):
    """Create or get billing profile for other user (signal may auto-create)"""
    profile, created = BillingProfile.objects.get_or_create(
        user=other_user,
        defaults={
            'telegram_username': '@otheruser',
            'country': 'US',
            'currency_preference': 'USD'
        }
    )
    return profile


@pytest.fixture
def admin_billing_profile(admin_user):
    """Create or get billing profile for admin user (signal may auto-create)"""
    profile, created = BillingProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            'telegram_username': '@admin',
            'country': 'US',
            'currency_preference': 'USD'
        }
    )
    return profile


@pytest.fixture
def feature(db):
    """Create a test feature"""
    return Feature.objects.create(
        key='test_feature',
        name='Test Feature',
        description='A test feature',
        category='signals',
        icon='🚀',
        is_active=True
    )


@pytest.fixture
def subscription_plan(feature):
    """Create a test subscription plan"""
    plan = SubscriptionPlan.objects.create(
        name='Monthly Plan',
        slug='monthly-plan',
        description='Test monthly plan',
        base_price=Decimal('29.99'),
        billing_period='monthly',
        trial_days=0,
        is_active=True,
        is_featured=False
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def inactive_plan(feature):
    """Create an inactive subscription plan"""
    plan = SubscriptionPlan.objects.create(
        name='Inactive Plan',
        slug='inactive-plan',
        description='Test inactive plan',
        base_price=Decimal('39.99'),
        billing_period='monthly',
        trial_days=0,
        is_active=False,
        is_featured=False
    )
    return plan


@pytest.fixture
def active_subscription(billing_profile, subscription_plan):
    """Create an active subscription"""
    now = timezone.now()
    return Subscription.objects.create(
        billing_profile=billing_profile,
        plan=subscription_plan,
        status='active',
        start_date=now,
        end_date=now + timedelta(days=30),
        amount_paid=subscription_plan.base_price,
        currency='USD',
        auto_renew=True
    )


@pytest.fixture
def cancelled_subscription(billing_profile, subscription_plan):
    """Create a cancelled subscription"""
    now = timezone.now()
    return Subscription.objects.create(
        billing_profile=billing_profile,
        plan=subscription_plan,
        status='cancelled',
        start_date=now - timedelta(days=5),
        end_date=now + timedelta(days=25),
        amount_paid=subscription_plan.base_price,
        currency='USD',
        auto_renew=False,
        cancelled_at=now,
        cancellation_reason='User requested'
    )


@pytest.fixture
def expired_subscription(billing_profile, subscription_plan):
    """Create an expired subscription"""
    now = timezone.now()
    return Subscription.objects.create(
        billing_profile=billing_profile,
        plan=subscription_plan,
        status='expired',
        start_date=now - timedelta(days=60),
        end_date=now - timedelta(days=30),
        amount_paid=subscription_plan.base_price,
        currency='USD',
        auto_renew=False
    )


@pytest.fixture
def other_user_subscription(other_billing_profile, subscription_plan):
    """Create a subscription for another user"""
    now = timezone.now()
    return Subscription.objects.create(
        billing_profile=other_billing_profile,
        plan=subscription_plan,
        status='active',
        start_date=now,
        end_date=now + timedelta(days=30),
        amount_paid=subscription_plan.base_price,
        currency='USD',
        auto_renew=True
    )


# ==================== Authentication Tests ====================

@pytest.mark.django_db
class TestSubscriptionAuthentication:
    """Test authentication requirements for subscription endpoints"""
    
    def test_unauthenticated_list_access_denied(self, api_client):
        """Unauthenticated users cannot list subscriptions"""
        response = api_client.get('/api/subscriptions/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_unauthenticated_retrieve_access_denied(self, api_client, active_subscription):
        """Unauthenticated users cannot retrieve subscription details"""
        response = api_client.get(f'/api/subscriptions/{active_subscription.id}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authenticated_access_allowed(self, api_client, regular_user):
        """Authenticated users can access subscription endpoints"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/')
        assert response.status_code == status.HTTP_200_OK


# ==================== List Tests ====================

@pytest.mark.django_db
class TestSubscriptionList:
    """Test subscription list endpoint with filtering and permissions"""
    
    def test_list_own_subscriptions(self, api_client, regular_user, active_subscription):
        """Users can list their own subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(active_subscription.id)
    
    def test_list_does_not_show_other_users_subscriptions(
        self, api_client, regular_user, active_subscription, other_user_subscription
    ):
        """Users cannot see other users' subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(active_subscription.id)
    
    def test_list_admin_sees_all_subscriptions(
        self, api_client, admin_user, active_subscription, other_user_subscription
    ):
        """Admin users can see all subscriptions"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/subscriptions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2
    
    def test_list_filtering_by_status(
        self, api_client, regular_user, active_subscription, cancelled_subscription
    ):
        """Filter subscriptions by status"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/', {'status': 'active'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'active'
    
    def test_list_filtering_by_plan(
        self, api_client, regular_user, active_subscription, subscription_plan
    ):
        """Filter subscriptions by plan ID"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/', {'plan': str(subscription_plan.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert str(response.data['results'][0]['plan']) == str(subscription_plan.id)
    
    def test_list_search_by_email(
        self, api_client, admin_user, active_subscription, other_user_subscription
    ):
        """Search subscriptions by user email (admin only)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/subscriptions/', {'search': 'testuser@example.com'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_list_pagination(
        self, api_client, regular_user, billing_profile, subscription_plan
    ):
        """Test pagination with 10 items per page"""
        # Create 15 subscriptions
        now = timezone.now()
        for i in range(15):
            Subscription.objects.create(
                billing_profile=billing_profile,
                plan=subscription_plan,
                status='active',
                start_date=now,
                end_date=now + timedelta(days=30),
                amount_paid=subscription_plan.base_price,
                currency='USD'
            )
        
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert response.data['count'] == 15
        assert len(response.data['results']) == 10  # Page size


# ==================== Retrieve Tests ====================

@pytest.mark.django_db
class TestSubscriptionRetrieve:
    """Test subscription retrieve endpoint with permissions"""
    
    def test_retrieve_own_subscription(self, api_client, regular_user, active_subscription):
        """Users can retrieve their own subscription details"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f'/api/subscriptions/{active_subscription.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(active_subscription.id)
        assert 'plan_details' in response.data
        assert 'features' in response.data['plan_details']
    
    def test_retrieve_others_subscription_denied(
        self, api_client, regular_user, other_user_subscription
    ):
        """Users cannot retrieve other users' subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get(f'/api/subscriptions/{other_user_subscription.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_admin_can_see_any_subscription(
        self, api_client, admin_user, other_user_subscription
    ):
        """Admin users can retrieve any subscription"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/subscriptions/{other_user_subscription.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(other_user_subscription.id)
    
    def test_retrieve_nonexistent_subscription(self, api_client, regular_user):
        """Retrieving non-existent subscription returns 404"""
        api_client.force_authenticate(user=regular_user)
        import uuid
        fake_id = uuid.uuid4()
        response = api_client.get(f'/api/subscriptions/{fake_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Create Tests ====================

@pytest.mark.django_db
class TestSubscriptionCreate:
    """Test subscription create endpoint with validation"""
    
    def test_create_subscription_success(
        self, api_client, regular_user, billing_profile, subscription_plan
    ):
        """Users can create subscriptions for their own billing profile"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'billing_profile': billing_profile.id,
            'plan': str(subscription_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data['plan']) == str(subscription_plan.id)
        assert response.data['status'] == 'pending'
        assert 'start_date' in response.data
        assert 'end_date' in response.data
    
    def test_create_subscription_without_plan_fails(
        self, api_client, regular_user, billing_profile
    ):
        """Creating subscription without plan fails"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'billing_profile': billing_profile.id,
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'plan' in response.data
    
    def test_create_subscription_with_inactive_plan_fails(
        self, api_client, regular_user, billing_profile, inactive_plan
    ):
        """Creating subscription with inactive plan fails"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'billing_profile': billing_profile.id,
            'plan': str(inactive_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'plan' in response.data
    
    def test_create_subscription_without_billing_profile_fails(
        self, api_client, regular_user, subscription_plan
    ):
        """Creating subscription without billing profile fails"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'plan': str(subscription_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'billing_profile' in response.data
    
    def test_create_subscription_for_other_user_denied(
        self, api_client, regular_user, other_billing_profile, subscription_plan
    ):
        """Users cannot create subscriptions for other users' billing profiles"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'billing_profile': other_billing_profile.id,
            'plan': str(subscription_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'billing_profile' in response.data
    
    def test_create_duplicate_active_subscription_fails(
        self, api_client, regular_user, billing_profile, subscription_plan, active_subscription
    ):
        """Creating duplicate active subscription to same plan fails"""
        api_client.force_authenticate(user=regular_user)
        data = {
            'billing_profile': billing_profile.id,
            'plan': str(subscription_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
    
    def test_admin_can_create_subscription_for_any_user(
        self, api_client, admin_user, other_billing_profile, subscription_plan
    ):
        """Admin users can create subscriptions for any billing profile"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'billing_profile': other_billing_profile.id,
            'plan': str(subscription_plan.id),
            'auto_renew': True
        }
        response = api_client.post('/api/subscriptions/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['billing_profile'] == other_billing_profile.id


# ==================== Update Tests ====================

@pytest.mark.django_db
class TestSubscriptionUpdate:
    """Test subscription update endpoint (admin only)"""
    
    def test_update_own_subscription_denied(
        self, api_client, regular_user, active_subscription
    ):
        """Regular users cannot update their own subscriptions"""
        api_client.force_authenticate(user=regular_user)
        data = {'auto_renew': False}
        response = api_client.patch(f'/api/subscriptions/{active_subscription.id}/', data)
        
        # Permission denied because regular users have read-only access
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
    
    def test_update_admin_can_modify(
        self, api_client, admin_user, active_subscription
    ):
        """Admin users can update subscriptions"""
        api_client.force_authenticate(user=admin_user)
        data = {'auto_renew': False}
        response = api_client.patch(f'/api/subscriptions/{active_subscription.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['auto_renew'] is False
    
    def test_update_nonexistent_subscription(self, api_client, admin_user):
        """Updating non-existent subscription returns 404"""
        api_client.force_authenticate(user=admin_user)
        import uuid
        fake_id = uuid.uuid4()
        data = {'auto_renew': False}
        response = api_client.patch(f'/api/subscriptions/{fake_id}/', data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Delete Tests ====================

@pytest.mark.django_db
class TestSubscriptionDelete:
    """Test subscription delete endpoint (admin only)"""
    
    def test_delete_own_subscription_denied(
        self, api_client, regular_user, active_subscription
    ):
        """Regular users cannot delete their own subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.delete(f'/api/subscriptions/{active_subscription.id}/')
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
    
    def test_delete_admin_can_delete(
        self, api_client, admin_user, active_subscription
    ):
        """Admin users can delete subscriptions"""
        api_client.force_authenticate(user=admin_user)
        subscription_id = active_subscription.id
        response = api_client.delete(f'/api/subscriptions/{subscription_id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Subscription.objects.filter(id=subscription_id).exists()
    
    def test_delete_nonexistent_subscription(self, api_client, admin_user):
        """Deleting non-existent subscription returns 404"""
        api_client.force_authenticate(user=admin_user)
        import uuid
        fake_id = uuid.uuid4()
        response = api_client.delete(f'/api/subscriptions/{fake_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Cancel Action Tests ====================

@pytest.mark.django_db
class TestSubscriptionCancelAction:
    """Test subscription cancel custom action"""
    
    def test_cancel_own_subscription(
        self, api_client, regular_user, active_subscription
    ):
        """Users can cancel their own active subscriptions"""
        api_client.force_authenticate(user=regular_user)
        data = {'reason': 'No longer needed'}
        response = api_client.post(f'/api/subscriptions/{active_subscription.id}/cancel/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'subscription' in response.data
        assert response.data['subscription']['status'] == 'cancelled'
        assert response.data['subscription']['auto_renew'] is False
    
    def test_cancel_already_cancelled_subscription(
        self, api_client, regular_user, cancelled_subscription
    ):
        """Cancelling already cancelled subscription fails"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{cancelled_subscription.id}/cancel/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_cancel_with_reason(
        self, api_client, regular_user, active_subscription
    ):
        """Cancel subscription with custom reason"""
        api_client.force_authenticate(user=regular_user)
        data = {'reason': 'Too expensive'}
        response = api_client.post(f'/api/subscriptions/{active_subscription.id}/cancel/', data)
        
        assert response.status_code == status.HTTP_200_OK
        active_subscription.refresh_from_db()
        assert active_subscription.cancellation_reason == 'Too expensive'
    
    def test_cancel_others_subscription_denied(
        self, api_client, regular_user, other_user_subscription
    ):
        """Users cannot cancel other users' subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{other_user_subscription.id}/cancel/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cancel_expired_subscription_fails(
        self, api_client, regular_user, expired_subscription
    ):
        """Cannot cancel an expired subscription"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{expired_subscription.id}/cancel/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


# ==================== Reactivate Action Tests ====================

@pytest.mark.django_db
class TestSubscriptionReactivateAction:
    """Test subscription reactivate custom action"""
    
    def test_reactivate_cancelled_subscription(
        self, api_client, regular_user, cancelled_subscription
    ):
        """Users can reactivate their cancelled subscriptions"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{cancelled_subscription.id}/reactivate/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['subscription']['status'] == 'active'
        assert response.data['subscription']['auto_renew'] is True
        
        cancelled_subscription.refresh_from_db()
        assert cancelled_subscription.cancelled_at is None
        assert cancelled_subscription.cancellation_reason == ''
    
    def test_reactivate_active_subscription_fails(
        self, api_client, regular_user, active_subscription
    ):
        """Cannot reactivate an already active subscription"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{active_subscription.id}/reactivate/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_reactivate_expired_subscription_fails(
        self, api_client, regular_user, expired_subscription
    ):
        """Cannot reactivate an expired subscription"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{expired_subscription.id}/reactivate/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_reactivate_others_subscription_denied(
        self, api_client, regular_user, other_user_subscription
    ):
        """Users cannot reactivate other users' subscriptions"""
        # First cancel the other user's subscription
        other_user_subscription.cancel()
        
        api_client.force_authenticate(user=regular_user)
        response = api_client.post(f'/api/subscriptions/{other_user_subscription.id}/reactivate/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Expiring Soon Action Tests ====================

@pytest.mark.django_db
class TestSubscriptionExpiringSoonAction:
    """Test expiring_soon custom action"""
    
    def test_expiring_soon_default_7_days(
        self, api_client, regular_user, billing_profile, subscription_plan
    ):
        """Get subscriptions expiring within 7 days (default)"""
        now = timezone.now()
        # Create subscription expiring in 5 days
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=now - timedelta(days=25),
            end_date=now + timedelta(days=5),
            amount_paid=subscription_plan.base_price,
            currency='USD'
        )
        
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/expiring_soon/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_expiring_soon_custom_days(
        self, api_client, regular_user, billing_profile, subscription_plan
    ):
        """Get subscriptions expiring within custom number of days"""
        now = timezone.now()
        # Create subscription expiring in 15 days
        Subscription.objects.create(
            billing_profile=billing_profile,
            plan=subscription_plan,
            status='active',
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            amount_paid=subscription_plan.base_price,
            currency='USD'
        )
        
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/expiring_soon/', {'days': 20})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


# ==================== Statistics Action Tests ====================

@pytest.mark.django_db
class TestSubscriptionStatisticsAction:
    """Test statistics custom action (admin only)"""
    
    def test_statistics_admin_access(
        self, api_client, admin_user, active_subscription, cancelled_subscription, expired_subscription
    ):
        """Admin users can access subscription statistics"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/subscriptions/statistics/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_subscriptions' in response.data
        assert 'active_subscriptions' in response.data
        assert 'cancelled_subscriptions' in response.data
        assert 'expired_subscriptions' in response.data
        assert response.data['total_subscriptions'] >= 3
    
    def test_statistics_regular_user_denied(
        self, api_client, regular_user
    ):
        """Regular users cannot access statistics"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/subscriptions/statistics/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
