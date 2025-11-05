"""
Tests for Telegram Group API (Phase 0.5 - Task 0.5.28)

Tests cover:
- Access control (admin-only)
- CRUD operations (list, retrieve, create, update, delete)
- M2M relationships with SubscriptionPlan
- sync_members action (Telegram API integration)
- test_access action (bot permissions check)
- Validation (chat_id format, member counts, etc.)
- Computed fields (has_capacity, is_healthy, etc.)
- Edge cases
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from subscriptions.models import TelegramGroup, SubscriptionPlan, TelegramConfiguration
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def api_client():
    """REST API client"""
    return APIClient()


@pytest.fixture
def user(db):
    """Regular user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Admin user"""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True
    )


@pytest.fixture
def subscription_plan(db):
    """Sample subscription plan"""
    from decimal import Decimal
    return SubscriptionPlan.objects.create(
        name='Premium Plan',
        slug='premium-plan',
        description='Premium access',
        base_price=Decimal('1000.00'),
        billing_period='monthly',
        is_active=True
    )


@pytest.fixture
def another_plan(db):
    """Another subscription plan"""
    from decimal import Decimal
    return SubscriptionPlan.objects.create(
        name='VIP Plan',
        slug='vip-plan',
        description='VIP access',
        base_price=Decimal('2000.00'),
        billing_period='monthly',
        is_active=True
    )


@pytest.fixture
def telegram_group(db, subscription_plan):
    """Clean telegram group with plan association"""
    # Delete all existing groups
    TelegramGroup.objects.all().delete()
    
    group = TelegramGroup.objects.create(
        name='Test Signals Group',
        chat_id='-1001234567890',
        group_key='test-signals',
        description='Test group for signals',
        is_active=True,
        member_count=42,
        max_members=100,
        auto_add_enabled=True,
        auto_remove_enabled=True,
        welcome_message='Welcome {{user_name}} to {{group_name}}!',
        can_send_messages=True,
        can_add_users=True,
        can_remove_users=True
    )
    group.associated_plans.add(subscription_plan)
    return group


@pytest.fixture
def telegram_config(db):
    """Telegram configuration with bot token"""
    config = TelegramConfiguration.get_instance()
    config.bot_token = '123456789:ABCdefGHIjklMNOpqrSTUvwxyz1234567890'
    config.bot_username = '@TestBot'
    config.is_enabled = True
    config.save()
    return config


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupAccessControl:
    """Test access control for Telegram Group API"""
    
    def test_unauthenticated_cannot_access(self, api_client, telegram_group):
        """Unauthenticated users cannot access groups"""
        response = api_client.get('/api/admin/telegram/groups/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access(self, api_client, user, telegram_group):
        """Regular users cannot access groups"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/admin/telegram/groups/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access(self, api_client, admin_user, telegram_group):
        """Admin users can access groups"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/groups/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# CRUD OPERATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupCRUD:
    """Test CRUD operations for Telegram Groups"""
    
    def test_list_groups(self, api_client, admin_user, telegram_group):
        """Test listing groups"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/groups/')
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        assert len(results) == 1
        assert results[0]['name'] == 'Test Signals Group'
    
    def test_retrieve_group(self, api_client, admin_user, telegram_group):
        """Test retrieving group details"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Signals Group'
        assert response.data['chat_id'] == '-1001234567890'
        assert response.data['member_count'] == 42
        assert response.data['has_capacity'] is True
    
    def test_create_group(self, api_client, admin_user, subscription_plan):
        """Test creating a new group"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'New VIP Group',
            'chat_id': '-1009876543210',
            'group_key': 'new-vip',
            'description': 'VIP members only',
            'is_active': True,
            'max_members': 50,
            'associated_plan_ids': [str(subscription_plan.id)]
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New VIP Group'
        assert len(response.data['associated_plans']) == 1
    
    def test_update_group(self, api_client, admin_user, telegram_group):
        """Test updating a group"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'Updated Group Name',
            'description': 'Updated description',
            'max_members': 150
        }
        
        response = api_client.patch(
            f'/api/admin/telegram/groups/{telegram_group.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Group Name'
        assert response.data['max_members'] == 150
    
    def test_delete_group(self, api_client, admin_user, telegram_group):
        """Test deleting a group"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.delete(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert TelegramGroup.objects.filter(id=telegram_group.id).count() == 0


# ============================================================================
# M2M PLAN ASSOCIATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupPlanAssociations:
    """Test M2M relationships with SubscriptionPlan"""
    
    def test_group_with_multiple_plans(self, api_client, admin_user, subscription_plan, another_plan):
        """Test creating group with multiple plan associations"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'Multi-Plan Group',
            'chat_id': '-1001111111111',
            'group_key': 'multi-plan',
            'associated_plan_ids': [str(subscription_plan.id), str(another_plan.id)]
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['associated_plans']) == 2
    
    def test_update_plan_associations(self, api_client, admin_user, telegram_group, another_plan):
        """Test updating plan associations"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'associated_plan_ids': [str(another_plan.id)]
        }
        
        response = api_client.patch(
            f'/api/admin/telegram/groups/{telegram_group.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['associated_plans']) == 1
        assert response.data['associated_plans'][0]['id'] == str(another_plan.id)
    
    def test_clear_plan_associations(self, api_client, admin_user, telegram_group):
        """Test clearing all plan associations"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'associated_plan_ids': []
        }
        
        response = api_client.patch(
            f'/api/admin/telegram/groups/{telegram_group.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['associated_plans']) == 0


# ============================================================================
# SYNC MEMBERS ACTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupSyncMembers:
    """Test sync_members action"""
    
    @patch('requests.post')
    def test_sync_members_success(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test successful member count sync"""
        # Mock Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': 55
        }
        mock_post.return_value = mock_response
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['old_count'] == 42
        assert response.data['new_count'] == 55
        assert response.data['difference'] == 13
    
    @patch('requests.post')
    def test_sync_members_bot_kicked(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test sync when bot is kicked from group"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert 'removed from group' in response.data['message'].lower()
    
    @patch('requests.post')
    def test_sync_members_invalid_token(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test sync with invalid bot token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_sync_members_no_token_configured(self, api_client, admin_user, telegram_group):
        """Test sync when bot token not configured"""
        # Clear bot token
        config = TelegramConfiguration.get_instance()
        config.bot_token = ''
        config.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'not configured' in response.data['message'].lower()
    
    @patch('requests.post')
    def test_sync_members_timeout(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test sync with connection timeout"""
        mock_post.side_effect = __import__('requests').exceptions.Timeout()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert response.data['success'] is False
    
    @patch('requests.post')
    def test_sync_members_network_error(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test sync with network error"""
        mock_post.side_effect = __import__('requests').exceptions.RequestException('Network error')
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/sync-members/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


# ============================================================================
# TEST ACCESS ACTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupTestAccess:
    """Test test_access action"""
    
    @patch('requests.post')
    def test_access_success(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test successful access check"""
        # Mock getChat response
        mock_chat_response = MagicMock()
        mock_chat_response.status_code = 200
        mock_chat_response.json.return_value = {
            'ok': True,
            'result': {
                'title': 'Test Signals Group',
                'type': 'supergroup',
                'username': 'testsignals'
            }
        }
        
        # Mock getChatMember response
        mock_member_response = MagicMock()
        mock_member_response.status_code = 200
        mock_member_response.json.return_value = {
            'ok': True,
            'result': {
                'status': 'administrator',
                'can_send_messages': True,
                'can_invite_users': True,
                'can_restrict_members': True
            }
        }
        
        mock_post.side_effect = [mock_chat_response, mock_member_response]
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/test-access/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['bot_status']['is_admin'] is True
    
    @patch('requests.post')
    def test_access_bot_not_member(self, mock_post, api_client, admin_user, telegram_group, telegram_config):
        """Test access when bot is not a member"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/telegram/groups/{telegram_group.id}/test-access/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupValidation:
    """Test validation for Telegram Groups"""
    
    def test_invalid_chat_id_format(self, api_client, admin_user):
        """Test chat_id must start with '-'"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'Invalid Group',
            'chat_id': '1234567890',  # Missing '-' prefix
            'group_key': 'invalid-group'
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'chat_id' in response.data
    
    def test_negative_max_members(self, api_client, admin_user):
        """Test max_members cannot be negative"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'Test Group',
            'chat_id': '-1001234567890',
            'group_key': 'test-group',
            'max_members': -10
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'max_members' in response.data
    
    def test_negative_sort_order(self, api_client, admin_user):
        """Test sort_order cannot be negative"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'Test Group',
            'chat_id': '-1001234567890',
            'group_key': 'test-group',
            'sort_order': -5
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# COMPUTED FIELDS TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupComputedFields:
    """Test computed fields"""
    
    def test_has_capacity_unlimited(self, api_client, admin_user, telegram_group):
        """Test has_capacity with unlimited capacity"""
        telegram_group.max_members = None
        telegram_group.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.data['has_capacity'] is True
        assert response.data['capacity_percentage'] is None
    
    def test_has_capacity_at_limit(self, api_client, admin_user, telegram_group):
        """Test has_capacity when at limit"""
        telegram_group.member_count = 100
        telegram_group.max_members = 100
        telegram_group.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.data['has_capacity'] is False
        assert response.data['capacity_percentage'] == 100.0
    
    def test_is_healthy(self, api_client, admin_user, telegram_group):
        """Test is_healthy computed field"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.data['is_healthy'] is True
        
        # Disable auto-add
        telegram_group.can_add_users = False
        telegram_group.save()
        
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        assert response.data['is_healthy'] is False
    
    def test_days_since_sync(self, api_client, admin_user, telegram_group):
        """Test days_since_sync computed field"""
        # No sync yet
        telegram_group.last_sync_at = None
        telegram_group.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.data['days_since_sync'] is None
        
        # Set sync to 5 days ago
        telegram_group.last_sync_at = timezone.now() - timedelta(days=5)
        telegram_group.save()
        
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        assert response.data['days_since_sync'] == 5


# ============================================================================
# EDGE CASES AND FILTERING TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramGroupEdgeCases:
    """Test edge cases and filtering"""
    
    def test_filter_by_is_active(self, api_client, admin_user, telegram_group):
        """Test filtering by is_active"""
        # Create inactive group
        TelegramGroup.objects.create(
            name='Inactive Group',
            chat_id='-1009999999999',
            group_key='inactive-group',
            is_active=False
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/groups/?is_active=true')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        assert len(results) == 1
        assert results[0]['is_active'] is True
    
    def test_search_by_name(self, api_client, admin_user, telegram_group):
        """Test searching by name"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/groups/?search=Signals')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        assert len(results) == 1
    
    def test_ordering_by_sort_order(self, api_client, admin_user, telegram_group):
        """Test ordering by sort_order"""
        # Create another group with higher sort order
        TelegramGroup.objects.create(
            name='ZZZ Group',
            chat_id='-1008888888888',
            group_key='zzz-group',
            sort_order=10
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/groups/?ordering=sort_order')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        assert results[0]['sort_order'] == 0  # telegram_group default
    
    def test_group_with_no_chat_id(self, api_client, admin_user):
        """Test creating group without chat_id (should fail)"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': 'No Chat ID Group',
            'group_key': 'no-chat-id'
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'chat_id' in response.data
    
    def test_group_with_emoji_in_name(self, api_client, admin_user):
        """Test group with emoji in name"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'name': '🚀 Signals Group 📈',
            'chat_id': '-1007777777777',
            'group_key': 'emoji-group'
        }
        
        response = api_client.post('/api/admin/telegram/groups/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '🚀 Signals Group 📈'
    
    def test_capacity_percentage_calculation(self, api_client, admin_user, telegram_group):
        """Test capacity percentage calculation"""
        telegram_group.member_count = 75
        telegram_group.max_members = 100
        telegram_group.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/groups/{telegram_group.id}/')
        
        assert response.data['capacity_percentage'] == 75.0
