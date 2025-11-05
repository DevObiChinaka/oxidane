"""
Comprehensive Test Suite for SubscriptionPlan API Endpoints (Phase 0.5 - Task 0.5.21)

Tests cover:
- Public access (list, retrieve) - AllowAny permission
- Admin-only operations (create, update, delete) - IsAdmin permission
- Filtering (billing_period, is_active, is_featured)
- Search (name, description)
- Ordering (base_price, name, created_at)
- Custom actions (activate, deactivate, clone) - IsAdmin permission
- Edge cases and error handling

Total: 30+ tests
"""

import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from subscriptions.models import SubscriptionPlan, Feature

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def regular_user(db):
    """Create a regular user (non-staff)"""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user (staff)"""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def feature(db):
    """Create a test feature"""
    return Feature.objects.create(
        key='test_feature',
        name='Test Feature',
        description='A test feature for plans',
        category='signals',  # Valid category from CATEGORY_CHOICES
        icon='✨',
        is_active=True
    )


@pytest.fixture
def active_plan(db, feature):
    """Create an active subscription plan"""
    plan = SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium-plan',
        description='A premium subscription plan',
        base_price=Decimal('29.99'),
        billing_period='monthly',
        trial_days=7,
        limits={'lessons': 100, 'storage': 5000},
        is_active=True,
        is_featured=True,
        sort_order=1
    )
    plan.features.add(feature)
    return plan


@pytest.fixture
def inactive_plan(db):
    """Create an inactive subscription plan"""
    return SubscriptionPlan.objects.create(
        name='Basic Plan',
        slug='basic-plan',
        description='A basic subscription plan',
        base_price=Decimal('9.99'),
        billing_period='monthly',
        trial_days=0,
        is_active=False,
        is_featured=False,
        sort_order=2
    )


@pytest.fixture
def yearly_plan(db):
    """Create a yearly subscription plan"""
    return SubscriptionPlan.objects.create(
        name='Yearly Plan',
        slug='yearly-plan',
        description='Annual subscription with discount',
        base_price=Decimal('299.99'),
        billing_period='yearly',
        trial_days=14,
        is_active=True,
        is_featured=False,
        sort_order=3
    )


# ============================================================================
# Test Class 1: Public Access (AllowAny)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanPublicAccess:
    """Test public access to list and retrieve endpoints"""
    
    def test_unauthenticated_can_list_active_plans(self, api_client, active_plan, inactive_plan):
        """Unauthenticated users can list active plans"""
        url = '/api/plans/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1  # Only active plan visible
        assert response.data['results'][0]['name'] == 'Premium Plan'
    
    def test_unauthenticated_can_retrieve_active_plan(self, api_client, active_plan):
        """Unauthenticated users can retrieve active plan details"""
        url = f'/api/plans/{active_plan.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(active_plan.id)
        assert response.data['name'] == 'Premium Plan'
    
    def test_unauthenticated_cannot_retrieve_inactive_plan(self, api_client, inactive_plan):
        """Unauthenticated users cannot retrieve inactive plans"""
        url = f'/api/plans/{inactive_plan.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_regular_user_can_list_active_plans(self, api_client, regular_user, active_plan, inactive_plan):
        """Regular authenticated users can list active plans"""
        api_client.force_authenticate(user=regular_user)
        url = '/api/plans/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1  # Only active plan
    
    def test_regular_user_cannot_see_inactive_plans(self, api_client, regular_user, inactive_plan):
        """Regular users cannot see inactive plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{inactive_plan.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Class 2: Admin List & Retrieve
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanAdminAccess:
    """Test admin access to list and retrieve endpoints"""
    
    def test_admin_can_list_all_plans(self, api_client, admin_user, active_plan, inactive_plan):
        """Admins can list all plans (active and inactive)"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2  # Both active and inactive
    
    def test_admin_can_retrieve_inactive_plan(self, api_client, admin_user, inactive_plan):
        """Admins can retrieve inactive plan details"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{inactive_plan.id}/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(inactive_plan.id)
        assert response.data['is_active'] is False


# ============================================================================
# Test Class 3: Create Operations (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanCreate:
    """Test plan creation (admin only)"""
    
    def test_unauthenticated_cannot_create_plan(self, api_client):
        """Unauthenticated users cannot create plans"""
        url = '/api/plans/'
        data = {
            'name': 'New Plan',
            'base_price': '19.99',
            'billing_period': 'monthly'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_create_plan(self, api_client, regular_user):
        """Regular users cannot create plans"""
        api_client.force_authenticate(user=regular_user)
        url = '/api/plans/'
        data = {
            'name': 'New Plan',
            'base_price': '19.99',
            'billing_period': 'monthly'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_create_plan_success(self, api_client, admin_user):
        """Admins can create new plans"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/'
        data = {
            'name': 'Enterprise Plan',
            'description': 'For large organizations',
            'base_price': '99.99',
            'billing_period': 'monthly',
            'trial_days': 14,
            'is_active': True,
            'is_featured': False
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Enterprise Plan'
        assert response.data['base_price'] == '99.99'
        assert response.data['is_active'] is True
    
    def test_create_plan_without_required_fields_fails(self, api_client, admin_user):
        """Creating plan without required fields fails"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/'
        data = {
            'name': 'Incomplete Plan'
            # Missing base_price and billing_period
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'base_price' in str(response.data) or 'billing_period' in str(response.data)
    
    def test_create_plan_with_negative_price_fails(self, api_client, admin_user):
        """Creating plan with negative price fails"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/'
        data = {
            'name': 'Invalid Plan',
            'base_price': '-10.00',
            'billing_period': 'monthly'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Test Class 4: Update Operations (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanUpdate:
    """Test plan update operations (admin only)"""
    
    def test_regular_user_cannot_update_plan(self, api_client, regular_user, active_plan):
        """Regular users cannot update plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{active_plan.id}/'
        data = {'name': 'Updated Plan Name'}
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_update_plan(self, api_client, admin_user, active_plan):
        """Admins can update plan details"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/'
        data = {'name': 'Premium Plus Plan', 'base_price': '34.99'}
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Premium Plus Plan'
        assert response.data['base_price'] == '34.99'
    
    def test_admin_can_full_update_plan(self, api_client, admin_user, active_plan):
        """Admins can perform full PUT update"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/'
        data = {
            'name': 'Completely New Plan',
            'description': 'New description',
            'base_price': '49.99',
            'billing_period': 'quarterly',
            'trial_days': 30,
            'is_active': True,
            'is_featured': True
        }
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Completely New Plan'
        assert response.data['billing_period'] == 'quarterly'


# ============================================================================
# Test Class 5: Delete Operations (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanDelete:
    """Test plan deletion (admin only)"""
    
    def test_regular_user_cannot_delete_plan(self, api_client, regular_user, active_plan):
        """Regular users cannot delete plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{active_plan.id}/'
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_delete_plan(self, api_client, admin_user, inactive_plan):
        """Admins can delete plans"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{inactive_plan.id}/'
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Verify deletion
        assert not SubscriptionPlan.objects.filter(id=inactive_plan.id).exists()
    
    def test_delete_nonexistent_plan(self, api_client, admin_user):
        """Deleting non-existent plan returns 404"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/99999999-9999-9999-9999-999999999999/'
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Class 6: Filtering
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanFiltering:
    """Test filtering functionality"""
    
    def test_filter_by_billing_period(self, api_client, active_plan, yearly_plan):
        """Filter plans by billing period"""
        url = '/api/plans/?billing_period=yearly'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['billing_period'] == 'yearly'
    
    def test_filter_by_is_featured(self, api_client, active_plan, yearly_plan):
        """Filter featured plans"""
        url = '/api/plans/?is_featured=true'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['is_featured'] is True
    
    def test_filter_by_is_active(self, api_client, admin_user, active_plan, inactive_plan):
        """Admin filters plans by active status"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/?is_active=false'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['is_active'] is False


# ============================================================================
# Test Class 7: Search
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanSearch:
    """Test search functionality"""
    
    def test_search_by_name(self, api_client, active_plan, yearly_plan):
        """Search plans by name"""
        url = '/api/plans/?search=Yearly'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert 'Yearly' in response.data['results'][0]['name']
    
    def test_search_by_description(self, api_client, yearly_plan):
        """Search plans by description"""
        url = '/api/plans/?search=Annual'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert 'Annual' in response.data['results'][0]['description']
    
    def test_search_no_results(self, api_client, active_plan):
        """Search with no results returns empty list"""
        url = '/api/plans/?search=NonExistentPlan'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0


# ============================================================================
# Test Class 8: Ordering
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanOrdering:
    """Test ordering functionality"""
    
    def test_order_by_price_ascending(self, api_client, active_plan, yearly_plan):
        """Order plans by price (ascending)"""
        url = '/api/plans/?ordering=base_price'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        prices = [Decimal(item['base_price']) for item in response.data['results']]
        assert prices == sorted(prices)
    
    def test_order_by_price_descending(self, api_client, active_plan, yearly_plan):
        """Order plans by price (descending)"""
        url = '/api/plans/?ordering=-base_price'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        prices = [Decimal(item['base_price']) for item in response.data['results']]
        assert prices == sorted(prices, reverse=True)
    
    def test_order_by_name(self, api_client, active_plan, yearly_plan):
        """Order plans by name"""
        url = '/api/plans/?ordering=name'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        names = [item['name'] for item in response.data['results']]
        assert names == sorted(names)


# ============================================================================
# Test Class 9: Pagination
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanPagination:
    """Test pagination (20 per page)"""
    
    def test_pagination_default_page_size(self, api_client, admin_user):
        """Test default pagination (20 plans per page)"""
        api_client.force_authenticate(user=admin_user)
        
        # Create 25 plans
        for i in range(25):
            SubscriptionPlan.objects.create(
                name=f'Plan {i}',
                base_price=Decimal('10.00'),
                billing_period='monthly',
                is_active=True
            )
        
        url = '/api/plans/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20  # First page
        
        # Check page 2
        url_page2 = '/api/plans/?page=2'
        response_page2 = api_client.get(url_page2)
        assert len(response_page2.data['results']) == 5  # Remaining plans
    
    def test_pagination_custom_page_size(self, api_client, active_plan, yearly_plan):
        """Test custom page size parameter"""
        url = '/api/plans/?page_size=1'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


# ============================================================================
# Test Class 10: Activate Action (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanActivateAction:
    """Test activate custom action"""
    
    def test_regular_user_cannot_activate_plan(self, api_client, regular_user, inactive_plan):
        """Regular users cannot activate plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{inactive_plan.id}/activate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_activate_inactive_plan(self, api_client, admin_user, inactive_plan):
        """Admins can activate inactive plans"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{inactive_plan.id}/activate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True
        
        # Verify database change
        inactive_plan.refresh_from_db()
        assert inactive_plan.is_active is True
    
    def test_activate_already_active_plan_fails(self, api_client, admin_user, active_plan):
        """Activating already active plan returns error"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/activate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already active' in response.data['error'].lower()


# ============================================================================
# Test Class 11: Deactivate Action (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanDeactivateAction:
    """Test deactivate custom action"""
    
    def test_regular_user_cannot_deactivate_plan(self, api_client, regular_user, active_plan):
        """Regular users cannot deactivate plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{active_plan.id}/deactivate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_deactivate_active_plan(self, api_client, admin_user, active_plan):
        """Admins can deactivate active plans"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/deactivate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False
        
        # Verify database change
        active_plan.refresh_from_db()
        assert active_plan.is_active is False
    
    def test_deactivate_already_inactive_plan_fails(self, api_client, admin_user, inactive_plan):
        """Deactivating already inactive plan returns error"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{inactive_plan.id}/deactivate/'
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already inactive' in response.data['error'].lower()


# ============================================================================
# Test Class 12: Clone Action (Admin Only)
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanCloneAction:
    """Test clone custom action"""
    
    def test_regular_user_cannot_clone_plan(self, api_client, regular_user, active_plan):
        """Regular users cannot clone plans"""
        api_client.force_authenticate(user=regular_user)
        url = f'/api/plans/{active_plan.id}/clone/'
        data = {'name': 'Cloned Plan'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_clone_plan_success(self, api_client, admin_user, active_plan):
        """Admins can clone plans with new name"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/clone/'
        data = {'name': 'Premium Plan Copy'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Premium Plan Copy'
        assert response.data['base_price'] == str(active_plan.base_price)
        assert response.data['billing_period'] == active_plan.billing_period
        assert response.data['is_active'] is False  # Clones start inactive
        assert '(Cloned)' in response.data['description']
        
        # Verify new plan exists in database
        assert SubscriptionPlan.objects.filter(name='Premium Plan Copy').exists()
    
    def test_clone_without_name_fails(self, api_client, admin_user, active_plan):
        """Cloning without name fails"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/clone/'
        data = {}  # No name provided
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Name is required' in response.data['error']
    
    def test_clone_with_custom_slug(self, api_client, admin_user, active_plan):
        """Clone with custom slug"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/clone/'
        data = {
            'name': 'Premium Copy',
            'slug': 'premium-copy-2024'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['slug'] == 'premium-copy-2024'
    
    def test_clone_copies_features(self, api_client, admin_user, active_plan, feature):
        """Cloned plan inherits features from source"""
        api_client.force_authenticate(user=admin_user)
        url = f'/api/plans/{active_plan.id}/clone/'
        data = {'name': 'Feature Copy Plan'}
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify features were copied
        cloned_plan = SubscriptionPlan.objects.get(name='Feature Copy Plan')
        assert cloned_plan.features.count() == active_plan.features.count()
        assert list(cloned_plan.features.all()) == list(active_plan.features.all())


# ============================================================================
# Test Class 13: Edge Cases
# ============================================================================


@pytest.mark.django_db
class TestSubscriptionPlanEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_retrieve_nonexistent_plan(self, api_client):
        """Retrieving non-existent plan returns 404"""
        url = '/api/plans/99999999-9999-9999-9999-999999999999/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_empty_plans(self, api_client):
        """Listing when no active plans exist returns empty"""
        url = '/api/plans/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['results'] == []
    
    def test_create_plan_with_duplicate_slug_auto_generates_new(self, api_client, admin_user, active_plan):
        """Creating plan with same name auto-generates unique slug"""
        api_client.force_authenticate(user=admin_user)
        url = '/api/plans/'
        data = {
            'name': 'Premium Plan',  # Same name as active_plan
            'base_price': '39.99',
            'billing_period': 'monthly'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['slug'] != active_plan.slug  # Different slug auto-generated
