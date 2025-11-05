"""
Comprehensive test suite for Referral Code API endpoints (Phase 0.5 - Task 0.5.25)

Tests cover:
- Access control (users vs admins)
- CRUD operations
- Code format validation
- Discount validation (referrer + referee)
- Date validation
- Usage limit validation
- Filtering, search, ordering, pagination
- Custom actions (validate, usage_stats, generate)
- Edge cases (expired codes, exhausted usage)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from subscriptions.models import ReferralCode

User = get_user_model()


@pytest.fixture
def api_client():
    """DRF API client for making requests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Regular user (non-admin)"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def other_user(db):
    """Another regular user"""
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Admin user with staff privileges"""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def active_referral_code(db, user):
    """Active referral code with standard settings"""
    return ReferralCode.objects.create(
        code='TESTREF2024',
        referrer=user,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('15.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00'),
        max_uses=100,
        current_uses=0,
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
        is_active=True,
        description='Test referral code'
    )


@pytest.fixture
def expired_referral_code(db, user):
    """Expired referral code"""
    return ReferralCode.objects.create(
        code='EXPIRED2023',
        referrer=user,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('10.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00'),
        valid_from=timezone.now() - timedelta(days=60),
        valid_until=timezone.now() - timedelta(days=30),
        is_active=True
    )


@pytest.fixture
def exhausted_referral_code(db, user):
    """Exhausted referral code (max uses reached)"""
    return ReferralCode.objects.create(
        code='EXHAUSTED',
        referrer=user,
        referrer_discount_type='fixed',
        referee_discount_type='fixed',
        referrer_discount_value=Decimal('10.00'),
        referee_discount_value=Decimal('5.00'),
        max_uses=10,
        current_uses=10,
        is_active=True
    )


@pytest.fixture
def inactive_referral_code(db, user):
    """Inactive referral code"""
    return ReferralCode.objects.create(
        code='INACTIVE',
        referrer=user,
        referrer_discount_type='percentage',
        referrer_discount_value=Decimal('10.00'),
        referee_discount_type='percentage',
        referee_discount_value=Decimal('10.00'),
        is_active=False
    )


@pytest.mark.django_db
class TestReferralCodeAccessControl:
    """Test access control and permissions"""
    
    def test_unauthenticated_cannot_list_codes(self, api_client):
        """Unauthenticated users cannot list referral codes"""
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_can_list_own_codes(self, api_client, user, active_referral_code):
        """Users can list their own referral codes"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_user_cannot_see_others_codes(self, api_client, user, other_user, active_referral_code):
        """Users cannot see other users' referral codes"""
        # Create code for other user
        ReferralCode.objects.create(
            code='OTHERCODE',
            referrer=other_user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1  # Only own code
        assert response.data['results'][0]['code'] == 'TESTREF2024'
    
    def test_admin_can_see_all_codes(self, api_client, admin_user, user, other_user, active_referral_code):
        """Admins can see all referral codes"""
        # Create code for another user
        ReferralCode.objects.create(
            code='OTHERCODE',
            referrer=other_user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2  # See both codes


@pytest.mark.django_db
class TestReferralCodeCreate:
    """Test referral code creation"""
    
    def test_user_can_create_referral_code(self, api_client, user):
        """Users can create referral codes"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'MYNEWCODE',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '15.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00',
            'max_uses': 50
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'MYNEWCODE'
        assert response.data['referrer'] == user.id
    
    def test_create_with_fixed_discounts(self, api_client, user):
        """Create referral code with fixed discounts"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'FIXED10',
            'referrer_discount_type': 'fixed',
            'referrer_discount_value': '20.00',
            'referee_discount_type': 'fixed',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['referrer_discount_type'] == 'fixed'
    
    def test_create_normalizes_code_to_uppercase(self, api_client, user):
        """Code is normalized to uppercase"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'lowercase',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'LOWERCASE'
    
    def test_create_with_duplicate_code_fails(self, api_client, user, active_referral_code):
        """Cannot create referral code with duplicate code"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'TESTREF2024',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_with_invalid_code_format_fails(self, api_client, user):
        """Cannot create referral code with invalid format"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'INVALID@CODE!',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_with_short_code_fails(self, api_client, user):
        """Code must be at least 3 characters"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'AB',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_with_referrer_percentage_over_100_fails(self, api_client, user):
        """Referrer percentage discount cannot exceed 100%"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'OVER100',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '150.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_with_referee_percentage_over_100_fails(self, api_client, user):
        """Referee percentage discount cannot exceed 100%"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'OVER100',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '150.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_with_invalid_date_range_fails(self, api_client, user):
        """valid_until must be after valid_from"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'BADDATE',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00',
            'valid_from': '2024-12-01T00:00:00Z',
            'valid_until': '2024-11-01T00:00:00Z'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReferralCodeRetrieve:
    """Test referral code retrieval"""
    
    def test_user_can_retrieve_own_code(self, api_client, user, active_referral_code):
        """Users can retrieve their own referral codes"""
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/referrals/codes/{active_referral_code.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'TESTREF2024'
    
    def test_user_cannot_retrieve_others_code(self, api_client, other_user, active_referral_code):
        """Users cannot retrieve other users' referral codes"""
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f'/api/referrals/codes/{active_referral_code.id}/')
        # 404 is returned because queryset filtering removes it before permission check (better for security)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_admin_can_retrieve_any_code(self, api_client, admin_user, active_referral_code):
        """Admins can retrieve any referral code"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/referrals/codes/{active_referral_code.id}/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_retrieve_nonexistent_code_returns_404(self, api_client, user):
        """Retrieving nonexistent code returns 404"""
        api_client.force_authenticate(user=user)
        fake_id = '00000000-0000-0000-0000-000000000000'
        response = api_client.get(f'/api/referrals/codes/{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestReferralCodeUpdate:
    """Test referral code updates"""
    
    def test_user_can_update_own_code(self, api_client, user, active_referral_code):
        """Users can update their own referral codes"""
        api_client.force_authenticate(user=user)
        data = {'description': 'Updated description'}
        response = api_client.patch(f'/api/referrals/codes/{active_referral_code.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated description'
    
    def test_user_cannot_update_others_code(self, api_client, other_user, active_referral_code):
        """Users cannot update other users' referral codes"""
        api_client.force_authenticate(user=other_user)
        data = {'description': 'Hacked!'}
        response = api_client.patch(f'/api/referrals/codes/{active_referral_code.id}/', data, format='json')
        # 404 is returned because queryset filtering removes it before permission check
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_code_is_immutable_after_creation(self, api_client, user, active_referral_code):
        """Code cannot be changed after creation"""
        api_client.force_authenticate(user=user)
        data = {'code': 'NEWCODE'}
        response = api_client.patch(f'/api/referrals/codes/{active_referral_code.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        # Code should not change
        active_referral_code.refresh_from_db()
        assert active_referral_code.code == 'TESTREF2024'


@pytest.mark.django_db
class TestReferralCodeDelete:
    """Test referral code deletion"""
    
    def test_user_can_delete_own_code(self, api_client, user, active_referral_code):
        """Users can delete their own referral codes"""
        api_client.force_authenticate(user=user)
        response = api_client.delete(f'/api/referrals/codes/{active_referral_code.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ReferralCode.objects.filter(id=active_referral_code.id).exists()
    
    def test_user_cannot_delete_others_code(self, api_client, other_user, active_referral_code):
        """Users cannot delete other users' referral codes"""
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(f'/api/referrals/codes/{active_referral_code.id}/')
        # 404 is returned because queryset filtering removes it before permission check
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestReferralCodeFiltering:
    """Test filtering capabilities"""
    
    def test_filter_by_is_active(self, api_client, user, active_referral_code, inactive_referral_code):
        """Filter referral codes by is_active"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_active'] is True
    
    def test_filter_by_referrer(self, api_client, admin_user, user, other_user, active_referral_code):
        """Filter referral codes by referrer (admin only)"""
        ReferralCode.objects.create(
            code='OTHERCODE',
            referrer=other_user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/referrals/codes/?referrer={user.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['referrer'] == user.id


@pytest.mark.django_db
class TestReferralCodeSearch:
    """Test search functionality"""
    
    def test_search_by_code(self, api_client, user, active_referral_code):
        """Search referral codes by code"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?search=TESTREF')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_search_by_username(self, api_client, user, active_referral_code):
        """Search referral codes by referrer username"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?search=testuser')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_search_no_results(self, api_client, user):
        """Search with no results"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?search=NONEXISTENT')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestReferralCodeOrdering:
    """Test ordering capabilities"""
    
    def test_order_by_created_at_descending(self, api_client, user):
        """Order referral codes by created_at descending (default)"""
        # Create multiple codes
        ReferralCode.objects.create(
            code='CODE1',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        ReferralCode.objects.create(
            code='CODE2',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00')
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_200_OK
        # CODE2 should be first (most recent)
        assert response.data['results'][0]['code'] == 'CODE2'
    
    def test_order_by_current_uses(self, api_client, user):
        """Order referral codes by usage count"""
        code1 = ReferralCode.objects.create(
            code='LOW_USAGE',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            current_uses=5
        )
        code2 = ReferralCode.objects.create(
            code='HIGH_USAGE',
            referrer=user,
            referrer_discount_type='percentage',
            referrer_discount_value=Decimal('10.00'),
            referee_discount_type='percentage',
            referee_discount_value=Decimal('10.00'),
            current_uses=50
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?ordering=current_uses')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['code'] == 'LOW_USAGE'


@pytest.mark.django_db
class TestReferralCodePagination:
    """Test pagination"""
    
    def test_pagination_default_page_size(self, api_client, user):
        """Default page size is 20"""
        # Create 25 referral codes
        for i in range(25):
            ReferralCode.objects.create(
                code=f'CODE{i:02d}',
                referrer=user,
                referrer_discount_type='percentage',
                referrer_discount_value=Decimal('10.00'),
                referee_discount_type='percentage',
                referee_discount_value=Decimal('10.00')
            )
        
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['count'] == 25
    
    def test_pagination_custom_page_size(self, api_client, user):
        """Can customize page size via query param"""
        # Create 15 referral codes
        for i in range(15):
            ReferralCode.objects.create(
                code=f'CODE{i:02d}',
                referrer=user,
                referrer_discount_type='percentage',
                referrer_discount_value=Decimal('10.00'),
                referee_discount_type='percentage',
                referee_discount_value=Decimal('10.00')
            )
        
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/referrals/codes/?page_size=5')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5


@pytest.mark.django_db
class TestReferralCodeValidateAction:
    """Test validate custom action"""
    
    def test_validate_active_code_success(self, api_client, user, active_referral_code):
        """Validate an active referral code"""
        api_client.force_authenticate(user=user)
        data = {'code': 'TESTREF2024'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        assert 'referral_code' in response.data
    
    def test_validate_with_amount_returns_discounts(self, api_client, user, active_referral_code):
        """Validate with amount returns discount calculations"""
        api_client.force_authenticate(user=user)
        data = {'code': 'TESTREF2024', 'amount': '100.00'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        assert 'referrer_discount_details' in response.data
        assert 'referee_discount_details' in response.data
        # Check referrer discount (15%)
        assert response.data['referrer_discount_details']['discount_amount'] == 15.0
        assert response.data['referrer_discount_details']['final_price'] == 85.0
        # Check referee discount (10%)
        assert response.data['referee_discount_details']['discount_amount'] == 10.0
        assert response.data['referee_discount_details']['final_price'] == 90.0
    
    def test_validate_expired_code_fails(self, api_client, user, expired_referral_code):
        """Validate expired referral code returns invalid"""
        api_client.force_authenticate(user=user)
        data = {'code': 'EXPIRED2023'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'expired' in response.data['message'].lower()
    
    def test_validate_exhausted_code_fails(self, api_client, user, exhausted_referral_code):
        """Validate exhausted referral code returns invalid"""
        api_client.force_authenticate(user=user)
        data = {'code': 'EXHAUSTED'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'usage limit' in response.data['message'].lower()
    
    def test_validate_inactive_code_fails(self, api_client, user, inactive_referral_code):
        """Validate inactive referral code returns invalid"""
        api_client.force_authenticate(user=user)
        data = {'code': 'INACTIVE'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False
        assert 'not active' in response.data['message'].lower()
    
    def test_validate_nonexistent_code_returns_404(self, api_client, user):
        """Validate nonexistent code returns 404"""
        api_client.force_authenticate(user=user)
        data = {'code': 'NONEXISTENT'}
        response = api_client.post('/api/referrals/codes/validate/', data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestReferralCodeUsageStatsAction:
    """Test usage_stats custom action"""
    
    def test_get_usage_stats(self, api_client, user, active_referral_code):
        """Get detailed usage statistics"""
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/referrals/codes/{active_referral_code.id}/usage_stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'stats' in response.data
        stats = response.data['stats']
        assert 'total_uses' in stats
        assert 'remaining_uses' in stats
        assert 'usage_percentage' in stats
        assert 'is_exhausted' in stats
        assert 'is_expired' in stats
        assert stats['total_uses'] == 0
        assert stats['remaining_uses'] == 100
    
    def test_get_usage_alias_endpoint(self, api_client, user, active_referral_code):
        """Test the /usage/ alias endpoint"""
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/referrals/codes/{active_referral_code.id}/usage/')
        assert response.status_code == status.HTTP_200_OK
        assert 'stats' in response.data


@pytest.mark.django_db
class TestReferralCodeGenerateAction:
    """Test generate custom action"""
    
    def test_user_can_generate_code(self, api_client, user):
        """Users can generate new referral codes"""
        api_client.force_authenticate(user=user)
        data = {
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '15.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/generate/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'referral_code' in response.data
        assert 'message' in response.data
        # Code should be auto-generated with username
        assert 'TESTUSER' in response.data['referral_code']['code']
    
    def test_generate_with_custom_settings(self, api_client, user):
        """Generate code with custom settings"""
        api_client.force_authenticate(user=user)
        data = {
            'referrer_discount_type': 'fixed',
            'referrer_discount_value': '20.00',
            'referee_discount_type': 'fixed',
            'referee_discount_value': '10.00',
            'max_uses': 25,
            'description': 'My special code'
        }
        response = api_client.post('/api/referrals/codes/generate/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['referral_code']['referrer_discount_type'] == 'fixed'
        assert response.data['referral_code']['max_uses'] == 25


@pytest.mark.django_db
class TestReferralCodeEdgeCases:
    """Test edge cases and unusual scenarios"""
    
    def test_code_with_unlimited_uses(self, api_client, user):
        """Referral code with no max_uses (unlimited)"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'UNLIMITED',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
            # max_uses omitted (null/unlimited)
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['max_uses'] is None
        assert response.data['remaining_uses'] is None  # Unlimited
    
    def test_code_with_zero_referrer_discount(self, api_client, user):
        """Referral code with 0% referrer discount (only referee gets discount)"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'ONLYREFEREE',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '0.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '10.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_code_with_100_percent_referee_discount(self, api_client, user):
        """Referral code with 100% referee discount (free for referee)"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'FREEFORREFEREE',
            'referrer_discount_type': 'percentage',
            'referrer_discount_value': '10.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '100.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_code_with_mixed_discount_types(self, api_client, user):
        """Referral code with different discount types for referrer and referee"""
        api_client.force_authenticate(user=user)
        data = {
            'code': 'MIXED',
            'referrer_discount_type': 'fixed',
            'referrer_discount_value': '15.00',
            'referee_discount_type': 'percentage',
            'referee_discount_value': '20.00'
        }
        response = api_client.post('/api/referrals/codes/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['referrer_discount_type'] == 'fixed'
        assert response.data['referee_discount_type'] == 'percentage'
