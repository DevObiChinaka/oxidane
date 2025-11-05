"""
Tests for Coupon API endpoints (Phase 0.5 - Task 0.5.23)

Test Coverage:
- Admin-only access control
- CRUD operations (create, retrieve, list, update, delete)
- Code format validation and normalization
- Discount validation (percentage/fixed)
- Date validation (valid_from < valid_until)
- Usage limit validation
- Filtering (by discount_type, is_active)
- Search (by code, description)
- Ordering (by created_at, current_uses, discount_value)
- Pagination (20 per page)
- Custom actions (validate, usage_stats, bulk_activate, bulk_deactivate)
- Edge cases (expired coupons, exhausted usage, invalid codes)
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from subscriptions.models import Coupon, SubscriptionPlan

User = get_user_model()


@pytest.fixture
def api_client():
    """Create an API client for testing"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_user(
        username='adminuser',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    """Create a regular non-admin user"""
    return User.objects.create_user(
        username='testuser',
        email='user@test.com',
        password='testpass123'
    )


@pytest.fixture
def active_coupon(db, admin_user):
    """Create an active percentage coupon"""
    return Coupon.objects.create(
        code='SAVE20',
        discount_type='percentage',
        discount_value=Decimal('20.00'),
        description='20% off coupon',
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
        max_uses=100,
        max_uses_per_user=1,
        is_active=True,
        created_by=admin_user
    )


@pytest.fixture
def fixed_coupon(db, admin_user):
    """Create an active fixed discount coupon"""
    return Coupon.objects.create(
        code='FIXED10',
        discount_type='fixed',
        discount_value=Decimal('10.00'),
        description='$10 off coupon',
        valid_from=timezone.now() - timedelta(days=1),
        max_uses=50,
        max_uses_per_user=2,
        is_active=True,
        created_by=admin_user
    )


@pytest.fixture
def expired_coupon(db, admin_user):
    """Create an expired coupon"""
    return Coupon.objects.create(
        code='EXPIRED',
        discount_type='percentage',
        discount_value=Decimal('15.00'),
        valid_from=timezone.now() - timedelta(days=30),
        valid_until=timezone.now() - timedelta(days=1),
        is_active=True,
        created_by=admin_user
    )


@pytest.fixture
def exhausted_coupon(db, admin_user):
    """Create a coupon with exhausted usage"""
    return Coupon.objects.create(
        code='EXHAUSTED',
        discount_type='percentage',
        discount_value=Decimal('25.00'),
        max_uses=10,
        current_uses=10,
        is_active=True,
        created_by=admin_user
    )


@pytest.fixture
def inactive_coupon(db, admin_user):
    """Create an inactive coupon"""
    return Coupon.objects.create(
        code='INACTIVE',
        discount_type='percentage',
        discount_value=Decimal('30.00'),
        is_active=False,
        created_by=admin_user
    )


@pytest.fixture
def subscription_plan(db):
    """Create a subscription plan for testing"""
    return SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium',
        billing_period='monthly',
        base_price=Decimal('99.00'),
        description='Premium features',
        is_active=True
    )


# ====================== ACCESS CONTROL TESTS ======================

@pytest.mark.django_db
class TestCouponAccessControl:
    """Test admin-only access to coupon endpoints"""
    
    def test_unauthenticated_cannot_list_coupons(self, api_client):
        """Unauthenticated users cannot list coupons"""
        response = api_client.get('/api/coupons/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_regular_user_cannot_list_coupons(self, api_client, regular_user):
        """Regular users cannot list coupons"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.get('/api/coupons/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_list_coupons(self, api_client, admin_user, active_coupon):
        """Admin users can list coupons"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_regular_user_cannot_create_coupon(self, api_client, regular_user):
        """Regular users cannot create coupons"""
        api_client.force_authenticate(user=regular_user)
        response = api_client.post('/api/coupons/', {
            'code': 'NEWCODE',
            'discount_type': 'percentage',
            'discount_value': 15
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ====================== CRUD OPERATIONS TESTS ======================

@pytest.mark.django_db
class TestCouponCreate:
    """Test coupon creation"""
    
    def test_admin_can_create_percentage_coupon(self, api_client, admin_user):
        """Admin can create a percentage discount coupon"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'SAVE30',
            'discount_type': 'percentage',
            'discount_value': 30,
            'description': '30% off',
            'max_uses': 100,
            'max_uses_per_user': 1,
            'is_active': True
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'SAVE30'
        assert response.data['discount_type'] == 'percentage'
        assert Decimal(response.data['discount_value']) == Decimal('30.00')
    
    def test_admin_can_create_fixed_coupon(self, api_client, admin_user):
        """Admin can create a fixed amount discount coupon"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'FIXED25',
            'discount_type': 'fixed',
            'discount_value': 25,
            'description': '$25 off',
            'is_active': True
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'FIXED25'
        assert response.data['discount_type'] == 'fixed'
    
    def test_create_coupon_without_required_fields_fails(self, api_client, admin_user):
        """Creating coupon without required fields fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
        assert 'discount_value' in response.data
    
    def test_create_coupon_with_duplicate_code_fails(self, api_client, admin_user, active_coupon):
        """Creating coupon with duplicate code fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'SAVE20',  # Duplicate
            'discount_type': 'percentage',
            'discount_value': 10
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
    
    def test_create_coupon_with_invalid_code_format_fails(self, api_client, admin_user):
        """Creating coupon with invalid characters in code fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'SAVE@20!',  # Invalid characters
            'discount_type': 'percentage',
            'discount_value': 20
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
    
    def test_create_coupon_normalizes_code_to_uppercase(self, api_client, admin_user):
        """Creating coupon normalizes code to uppercase"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'save15',  # Lowercase
            'discount_type': 'percentage',
            'discount_value': 15
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'SAVE15'
    
    def test_create_coupon_with_negative_discount_fails(self, api_client, admin_user):
        """Creating coupon with negative discount value fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'NEGATIVE',
            'discount_type': 'percentage',
            'discount_value': -10
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_coupon_with_percentage_over_100_fails(self, api_client, admin_user):
        """Creating percentage coupon > 100% fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'OVER100',
            'discount_type': 'percentage',
            'discount_value': 150
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_coupon_with_invalid_date_range_fails(self, api_client, admin_user):
        """Creating coupon with valid_until before valid_from fails"""
        api_client.force_authenticate(user=admin_user)
        now = timezone.now()
        response = api_client.post('/api/coupons/', {
            'code': 'BADDATE',
            'discount_type': 'percentage',
            'discount_value': 20,
            'valid_from': now,
            'valid_until': now - timedelta(days=1)  # Before valid_from
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCouponRetrieve:
    """Test coupon retrieval"""
    
    def test_admin_can_retrieve_coupon(self, api_client, admin_user, active_coupon):
        """Admin can retrieve coupon details"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/coupons/{active_coupon.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'SAVE20'
        assert 'discount_display' in response.data
        assert 'is_valid_now' in response.data
        assert 'usage_percentage' in response.data
    
    def test_retrieve_nonexistent_coupon_returns_404(self, api_client, admin_user):
        """Retrieving nonexistent coupon returns 404"""
        from uuid import uuid4
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/coupons/{uuid4()}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCouponList:
    """Test coupon listing"""
    
    def test_admin_can_list_all_coupons(self, api_client, admin_user, active_coupon, 
                                       fixed_coupon, inactive_coupon):
        """Admin can list all coupons including inactive"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_list_empty_coupons(self, api_client, admin_user):
        """Listing when no coupons exist returns empty list"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestCouponUpdate:
    """Test coupon updates"""
    
    def test_admin_can_update_coupon(self, api_client, admin_user, active_coupon):
        """Admin can update coupon fields"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(f'/api/coupons/{active_coupon.id}/', {
            'description': 'Updated description',
            'max_uses': 200
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated description'
        assert response.data['max_uses'] == 200
    
    def test_update_coupon_code_is_immutable(self, api_client, admin_user, active_coupon):
        """Updating coupon code is not allowed (immutable)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(f'/api/coupons/{active_coupon.id}/', {
            'code': 'NEWCODE'
        })
        # Should succeed but code shouldn't change
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'SAVE20'  # Original code


@pytest.mark.django_db
class TestCouponDelete:
    """Test coupon deletion"""
    
    def test_admin_can_delete_coupon(self, api_client, admin_user, active_coupon):
        """Admin can delete coupons"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(f'/api/coupons/{active_coupon.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Coupon.objects.filter(id=active_coupon.id).exists()


# ====================== FILTERING TESTS ======================

@pytest.mark.django_db
class TestCouponFiltering:
    """Test coupon filtering"""
    
    def test_filter_by_discount_type_percentage(self, api_client, admin_user, 
                                                 active_coupon, fixed_coupon):
        """Filter coupons by discount_type=percentage"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?discount_type=percentage')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['discount_type'] == 'percentage'
    
    def test_filter_by_discount_type_fixed(self, api_client, admin_user, 
                                           active_coupon, fixed_coupon):
        """Filter coupons by discount_type=fixed"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?discount_type=fixed')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['discount_type'] == 'fixed'
    
    def test_filter_by_is_active(self, api_client, admin_user, active_coupon, inactive_coupon):
        """Filter coupons by is_active status"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        assert all(coupon['is_active'] for coupon in response.data['results'])


# ====================== SEARCH TESTS ======================

@pytest.mark.django_db
class TestCouponSearch:
    """Test coupon search"""
    
    def test_search_by_code(self, api_client, admin_user, active_coupon, fixed_coupon):
        """Search coupons by code"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?search=SAVE')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['code'] == 'SAVE20'
    
    def test_search_by_description(self, api_client, admin_user, active_coupon):
        """Search coupons by description"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?search=20%')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_search_no_results(self, api_client, admin_user, active_coupon):
        """Search with no matches returns empty list"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?search=NONEXISTENT')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


# ====================== ORDERING TESTS ======================

@pytest.mark.django_db
class TestCouponOrdering:
    """Test coupon ordering"""
    
    def test_order_by_created_at_descending(self, api_client, admin_user, 
                                            active_coupon, fixed_coupon):
        """Order coupons by created_at (newest first - default)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?ordering=-created_at')
        assert response.status_code == status.HTTP_200_OK
        # Assuming fixed_coupon was created after active_coupon
        results = response.data['results']
        if len(results) >= 2:
            assert results[0]['created_at'] >= results[1]['created_at']
    
    def test_order_by_current_uses_ascending(self, api_client, admin_user, 
                                             active_coupon, exhausted_coupon):
        """Order coupons by current_uses (ascending)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?ordering=current_uses')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert results[0]['current_uses'] <= results[-1]['current_uses']
    
    def test_order_by_discount_value_descending(self, api_client, admin_user, 
                                                active_coupon, fixed_coupon):
        """Order coupons by discount_value (descending)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/coupons/?ordering=-discount_value')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        if len(results) >= 2:
            assert Decimal(results[0]['discount_value']) >= Decimal(results[1]['discount_value'])


# ====================== PAGINATION TESTS ======================

@pytest.mark.django_db
class TestCouponPagination:
    """Test coupon pagination"""
    
    def test_pagination_default_page_size(self, api_client, admin_user):
        """Default pagination is 20 per page"""
        api_client.force_authenticate(user=admin_user)
        # Create 25 coupons
        for i in range(25):
            Coupon.objects.create(
                code=f'CODE{i}',
                discount_type='percentage',
                discount_value=10,
                created_by=admin_user
            )
        response = api_client.get('/api/coupons/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['count'] == 25
    
    def test_pagination_custom_page_size(self, api_client, admin_user):
        """Can customize page size with query param"""
        api_client.force_authenticate(user=admin_user)
        # Create 15 coupons
        for i in range(15):
            Coupon.objects.create(
                code=f'CODE{i}',
                discount_type='percentage',
                discount_value=10,
                created_by=admin_user
            )
        response = api_client.get('/api/coupons/?page_size=5')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5


# ====================== CUSTOM ACTIONS TESTS ======================

@pytest.mark.django_db
class TestCouponValidateAction:
    """Test coupon validate custom action"""
    
    def test_validate_active_coupon_success(self, api_client, admin_user, active_coupon):
        """Validating an active, valid coupon succeeds"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'SAVE20'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        assert 'coupon' in response.data
    
    def test_validate_expired_coupon_fails(self, api_client, admin_user, expired_coupon):
        """Validating an expired coupon fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'EXPIRED'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'expired' in response.data['message'].lower()
    
    def test_validate_exhausted_coupon_fails(self, api_client, admin_user, exhausted_coupon):
        """Validating an exhausted coupon fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'EXHAUSTED'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'usage' in response.data['message'].lower()
    
    def test_validate_inactive_coupon_fails(self, api_client, admin_user, inactive_coupon):
        """Validating an inactive coupon fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'INACTIVE'
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'inactive' in response.data['message'].lower()
    
    def test_validate_nonexistent_coupon_returns_404(self, api_client, admin_user):
        """Validating a nonexistent coupon returns 404"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'NONEXISTENT'
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_validate_with_amount_returns_discount_details(self, api_client, admin_user, active_coupon):
        """Validating with amount returns discount calculation"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/validate/', {
            'code': 'SAVE20',
            'amount': 100.00
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        assert 'discount_details' in response.data
        assert response.data['discount_details']['original_price'] == 100.0
        assert response.data['discount_details']['discount_amount'] == 20.0
        assert response.data['discount_details']['final_price'] == 80.0


@pytest.mark.django_db
class TestCouponUsageStatsAction:
    """Test coupon usage_stats custom action"""
    
    def test_get_usage_stats(self, api_client, admin_user, active_coupon):
        """Get detailed usage statistics for a coupon"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/coupons/{active_coupon.id}/usage_stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'stats' in response.data
        stats = response.data['stats']
        assert 'total_uses' in stats
        assert 'remaining_uses' in stats
        assert 'usage_percentage' in stats
        assert 'is_exhausted' in stats
        assert 'is_expired' in stats
        assert 'is_valid' in stats
    
    def test_get_usage_alias_endpoint(self, api_client, admin_user, active_coupon):
        """Test the /usage/ alias endpoint (Task 0.5.24 specification)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/coupons/{active_coupon.id}/usage/')
        assert response.status_code == status.HTTP_200_OK
        assert 'stats' in response.data
        # Should return same data as usage_stats
        stats = response.data['stats']
        assert 'total_uses' in stats
        assert 'remaining_uses' in stats


@pytest.mark.django_db
class TestCouponBulkActions:
    """Test coupon bulk activate/deactivate"""
    
    def test_bulk_activate_coupons(self, api_client, admin_user, inactive_coupon):
        """Bulk activate multiple coupons"""
        api_client.force_authenticate(user=admin_user)
        # Create another inactive coupon
        coupon2 = Coupon.objects.create(
            code='INACTIVE2',
            discount_type='percentage',
            discount_value=15,
            is_active=False,
            created_by=admin_user
        )
        
        response = api_client.post('/api/coupons/bulk_activate/', {
            'ids': [str(inactive_coupon.id), str(coupon2.id)]
        }, format='json')
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        assert response.data['count'] == 2
        
        # Verify coupons are activated
        inactive_coupon.refresh_from_db()
        coupon2.refresh_from_db()
        assert inactive_coupon.is_active
        assert coupon2.is_active
    
    def test_bulk_deactivate_coupons(self, api_client, admin_user, active_coupon, fixed_coupon):
        """Bulk deactivate multiple coupons"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/bulk_deactivate/', {
            'ids': [str(active_coupon.id), str(fixed_coupon.id)]
        }, format='json')
        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        assert response.data['count'] == 2
        
        # Verify coupons are deactivated
        active_coupon.refresh_from_db()
        fixed_coupon.refresh_from_db()
        assert not active_coupon.is_active
        assert not fixed_coupon.is_active
    
    def test_bulk_actions_without_ids_fails(self, api_client, admin_user):
        """Bulk actions without IDs fail"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/bulk_activate/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_actions_with_invalid_ids_format_fails(self, api_client, admin_user):
        """Bulk actions with non-list IDs fail"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/bulk_activate/', {
            'ids': 'not-a-list'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ====================== EDGE CASES TESTS ======================

@pytest.mark.django_db
class TestCouponEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_coupon_with_no_max_uses_unlimited(self, api_client, admin_user):
        """Coupon with max_uses=None is unlimited"""
        api_client.force_authenticate(user=admin_user)
        # Omit max_uses field entirely (defaults to None/unlimited)
        response = api_client.post('/api/coupons/', {
            'code': 'UNLIMITED',
            'discount_type': 'percentage',
            'discount_value': 10
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['remaining_uses'] is None
    
    def test_coupon_with_zero_discount_value(self, api_client, admin_user):
        """Coupon with 0% discount is valid (edge case)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'ZERO',
            'discount_type': 'percentage',
            'discount_value': 0
        })
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_coupon_with_100_percent_discount(self, api_client, admin_user):
        """Coupon with 100% discount is valid"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'FREE',
            'discount_type': 'percentage',
            'discount_value': 100
        })
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_coupon_with_very_short_code_fails(self, api_client, admin_user):
        """Coupon with code < 3 characters fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'AB',  # Too short
            'discount_type': 'percentage',
            'discount_value': 10
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_coupon_with_max_uses_per_user_zero_fails(self, api_client, admin_user):
        """Coupon with max_uses_per_user=0 fails"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.post('/api/coupons/', {
            'code': 'ZEROPERUSER',
            'discount_type': 'percentage',
            'discount_value': 10,
            'max_uses_per_user': 0
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_validate_coupon_with_plan_applicability(self, api_client, admin_user, 
                                                     active_coupon, subscription_plan):
        """Validate coupon checks plan applicability"""
        api_client.force_authenticate(user=admin_user)
        # Coupon applies to all plans by default
        response = api_client.post('/api/coupons/validate/', {
            'code': 'SAVE20',
            'plan_id': str(subscription_plan.id)
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
