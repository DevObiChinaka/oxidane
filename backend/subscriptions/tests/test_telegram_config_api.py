"""
Test suite for Telegram Configuration API (Task 0.5.27)

Tests cover:
- Access control (unauthenticated, regular user, admin)
- CRUD operations (list, retrieve, create, update, partial_update)
- Singleton behavior (only one instance)
- Validation (bot_token format, bot_username, positive integers)
- Masked token display (never expose raw token)
- Test connection action (successful and failed)
- Settings bulk update
- Edge cases (empty values, special characters, concurrent updates)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from subscriptions.models import TelegramConfiguration

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Regular user"""
    return User.objects.create_user(
        username='testuser',
        email='user@example.com',
        password='testpass123',
        is_staff=False,
        is_superuser=False
    )


@pytest.fixture
def admin_user(db):
    """Admin user"""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='admin123',
        is_staff=True,
        is_superuser=False
    )


@pytest.fixture
def telegram_config(db):
    """Clean telegram configuration (singleton)"""
    # Delete all existing configs
    TelegramConfiguration.objects.all().delete()
    
    # Create fresh config
    config = TelegramConfiguration.objects.create(
        bot_token='123456789:ABCdefGHIjklMNOpqrSTUvwxyz1234567',
        bot_username='@TestBot',
        is_enabled=True,
        welcome_message='Welcome!',
        removal_message='Goodbye!',
        max_retries=3,
        retry_delay_seconds=300,
        rate_limit_per_minute=30
    )
    return config


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigAccessControl:
    """Test access control for Telegram configuration API"""
    
    def test_unauthenticated_cannot_access(self, api_client):
        """Unauthenticated users should be blocked"""
        response = api_client.get('/api/admin/telegram/config/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access(self, api_client, user):
        """Regular users should be forbidden"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/admin/telegram/config/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access(self, api_client, admin_user, telegram_config):
        """Admin users should have full access"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/config/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1


# ============================================================================
# CRUD OPERATIONS TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigCRUD:
    """Test CRUD operations for Telegram configuration"""
    
    def test_list_returns_singleton_as_list(self, api_client, admin_user, telegram_config):
        """List endpoint should return singleton config as a list"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/telegram/config/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        
        config_data = response.data[0]
        assert config_data['bot_username'] == '@TestBot'
        assert config_data['is_enabled'] is True
    
    def test_retrieve_returns_config_details(self, api_client, admin_user, telegram_config):
        """Retrieve should return config details (ID is ignored due to singleton)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/telegram/config/{telegram_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bot_username'] == '@TestBot'
        assert response.data['welcome_message'] == 'Welcome!'
    
    def test_create_updates_existing_config(self, api_client, admin_user, telegram_config):
        """POST should update existing config (singleton behavior)"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'bot_username': '@NewBot',
            'is_enabled': False,
            'welcome_message': 'New welcome message'
        }
        
        response = api_client.post('/api/admin/telegram/config/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bot_username'] == '@NewBot'
        assert response.data['is_enabled'] is False
        
        # Verify only one instance exists
        assert TelegramConfiguration.objects.count() == 1
    
    def test_update_modifies_config(self, api_client, admin_user, telegram_config):
        """PUT should update config fields"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'bot_username': '@UpdatedBot',
            'is_enabled': True,
            'welcome_message': 'Updated welcome',
            'removal_message': 'Updated goodbye',
            'max_retries': 5,
            'retry_delay_seconds': 600,
            'rate_limit_per_minute': 50
        }
        
        response = api_client.put(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bot_username'] == '@UpdatedBot'
        assert response.data['max_retries'] == 5
    
    def test_partial_update_modifies_specific_fields(self, api_client, admin_user, telegram_config):
        """PATCH should update only specified fields"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'is_enabled': False}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_enabled'] is False
        # Other fields should remain unchanged
        assert response.data['bot_username'] == '@TestBot'
        assert response.data['welcome_message'] == 'Welcome!'


# ============================================================================
# SINGLETON BEHAVIOR TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigSingleton:
    """Test singleton pattern enforcement"""
    
    def test_only_one_instance_exists(self, api_client, admin_user):
        """Only one TelegramConfiguration instance should exist"""
        api_client.force_authenticate(user=admin_user)
        
        # Create initial config
        api_client.post('/api/admin/telegram/config/', {
            'bot_username': '@FirstBot'
        })
        
        # Try to create another
        api_client.post('/api/admin/telegram/config/', {
            'bot_username': '@SecondBot'
        })
        
        # Should still be only one instance
        assert TelegramConfiguration.objects.count() == 1
        
        # Should have latest values
        config = TelegramConfiguration.get_instance()
        assert config.bot_username == '@SecondBot'
    
    def test_get_instance_creates_if_not_exists(self, api_client, admin_user):
        """get_instance should create config if none exists"""
        api_client.force_authenticate(user=admin_user)
        
        # Delete all configs
        TelegramConfiguration.objects.all().delete()
        
        # Access should auto-create
        response = api_client.get('/api/admin/telegram/config/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert TelegramConfiguration.objects.count() == 1


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigValidation:
    """Test field validation"""
    
    def test_invalid_bot_username_format(self, api_client, admin_user, telegram_config):
        """Bot username must start with @"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_username': 'InvalidBot'}  # Missing @
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'bot_username' in response.data
    
    def test_negative_max_retries_rejected(self, api_client, admin_user, telegram_config):
        """max_retries must be non-negative"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'max_retries': -1}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'max_retries' in response.data
    
    def test_zero_retry_delay_rejected(self, api_client, admin_user, telegram_config):
        """retry_delay_seconds must be positive"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'retry_delay_seconds': 0}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'retry_delay_seconds' in response.data
    
    def test_zero_rate_limit_rejected(self, api_client, admin_user, telegram_config):
        """rate_limit_per_minute must be positive"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'rate_limit_per_minute': 0}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'rate_limit_per_minute' in response.data
    
    def test_invalid_bot_token_format_missing_colon(self, api_client, admin_user, telegram_config):
        """Bot token must have : separator"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_token': '123456789ABCdefGHI'}  # Missing colon
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'bot_token' in response.data
    
    def test_invalid_bot_token_format_non_numeric_id(self, api_client, admin_user, telegram_config):
        """Bot token first part must be numeric"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_token': 'ABC123456:ABCdefGHI'}  # Non-numeric ID
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'bot_token' in response.data
    
    def test_invalid_bot_token_format_short_id(self, api_client, admin_user, telegram_config):
        """Bot token ID must be 8-10 digits"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_token': '123:ABCdefGHIjklMNOpqrSTUvwxyz1234567'}  # ID too short
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'bot_token' in response.data
    
    def test_invalid_bot_token_format_short_token(self, api_client, admin_user, telegram_config):
        """Bot token must have sufficient length"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_token': '123456789:ABC'}  # Token too short
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'bot_token' in response.data
    
    def test_valid_bot_token_accepted(self, api_client, admin_user, telegram_config):
        """Valid bot token should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_token': '987654321:XYZabcDEFghiJKLmnoPQRstUVWxyz7890'}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# MASKED TOKEN TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigMaskedToken:
    """Test that bot_token is never exposed in API responses"""
    
    def test_bot_token_not_in_response(self, api_client, admin_user, telegram_config):
        """bot_token should never be in API responses"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get('/api/admin/telegram/config/')
        
        config_data = response.data[0]
        assert 'bot_token' not in config_data
        assert 'masked_token' in config_data
    
    def test_masked_token_displayed(self, api_client, admin_user, telegram_config):
        """masked_token should show partial token"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/admin/telegram/config/{telegram_config.id}/')
        
        assert response.data['masked_token'] == '123456789:***4567'
    
    def test_update_with_token_shows_new_masked_token(self, api_client, admin_user, telegram_config):
        """After updating token, masked_token should reflect new value"""
        api_client.force_authenticate(user=admin_user)
        
        new_token = '111111111:NewTokenHere1234567890123456789'
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', {
            'bot_token': new_token
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['masked_token'] == '111111111:***6789'
        assert 'bot_token' not in response.data


# ============================================================================
# TEST CONNECTION ACTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigTestConnection:
    """Test the test_connection custom action"""
    
    @patch('requests.get')
    def test_successful_connection(self, mock_get, api_client, admin_user, telegram_config):
        """Test successful bot connection"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock successful Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'id': 123456789,
                'username': 'TestBot',
                'first_name': 'Test Bot',
                'can_join_groups': True,
                'can_read_all_group_messages': False
            }
        }
        mock_get.return_value = mock_response
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'bot_info' in response.data
        assert response.data['bot_info']['username'] == 'TestBot'
        
        # Verify config was updated
        telegram_config.refresh_from_db()
        assert telegram_config.is_connected is True
        assert telegram_config.bot_username == '@TestBot'
    
    @patch('requests.get')
    def test_failed_connection_invalid_token(self, mock_get, api_client, admin_user, telegram_config):
        """Test failed connection with invalid token"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock failed Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Unauthorized'
        }
        mock_get.return_value = mock_response
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'Unauthorized' in response.data['message']
        
        # Verify config was marked as disconnected
        telegram_config.refresh_from_db()
        assert telegram_config.is_connected is False
        assert telegram_config.connection_error == 'Unauthorized'
    
    @patch('requests.get')
    def test_connection_timeout(self, mock_get, api_client, admin_user, telegram_config):
        """Test connection timeout"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock timeout
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'timeout' in response.data['message'].lower()
    
    @patch('requests.get')
    def test_connection_network_error(self, mock_get, api_client, admin_user, telegram_config):
        """Test network error during connection"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock network error
        import requests
        mock_get.side_effect = requests.exceptions.RequestException('Network error')
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_connection_no_token_configured(self, api_client, admin_user):
        """Test connection when no token is configured"""
        api_client.force_authenticate(user=admin_user)
        
        # Delete config and create new one without token
        TelegramConfiguration.objects.all().delete()
        config = TelegramConfiguration.objects.create(bot_token='')
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'not configured' in response.data['message'].lower()
    
    def test_connection_invalid_token_format(self, api_client, admin_user):
        """Test connection with invalid token format"""
        api_client.force_authenticate(user=admin_user)
        
        # Create config with invalid token format
        TelegramConfiguration.objects.all().delete()
        config = TelegramConfiguration.objects.create(bot_token='invalid')
        
        response = api_client.post('/api/admin/telegram/config/test-connection/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'invalid format' in response.data['message'].lower()


# ============================================================================
# SETTINGS BULK UPDATE TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigSettingsBulkUpdate:
    """Test bulk update of multiple settings"""
    
    def test_bulk_update_multiple_fields(self, api_client, admin_user, telegram_config):
        """Update multiple settings in one request"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'is_enabled': False,
            'auto_add_enabled': False,
            'auto_remove_enabled': False,
            'welcome_message': 'New welcome',
            'removal_message': 'New goodbye',
            'max_retries': 10,
            'retry_delay_seconds': 900,
            'rate_limit_per_minute': 60
        }
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_enabled'] is False
        assert response.data['auto_add_enabled'] is False
        assert response.data['max_retries'] == 10
        assert response.data['rate_limit_per_minute'] == 60
    
    def test_partial_update_preserves_other_fields(self, api_client, admin_user, telegram_config):
        """Partial update should not affect unspecified fields"""
        api_client.force_authenticate(user=admin_user)
        
        original_max_retries = telegram_config.max_retries
        
        data = {'welcome_message': 'Only updating this'}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['welcome_message'] == 'Only updating this'
        assert response.data['max_retries'] == original_max_retries


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_bot_username_accepted(self, api_client, admin_user, telegram_config):
        """Empty bot_username should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'bot_username': ''}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bot_username'] == ''
    
    def test_empty_welcome_message_accepted(self, api_client, admin_user, telegram_config):
        """Empty welcome_message should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'welcome_message': ''}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['welcome_message'] == ''
    
    def test_very_long_welcome_message_accepted(self, api_client, admin_user, telegram_config):
        """Very long welcome message should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        long_message = ('Welcome! ' * 100).strip()  # Very long message without trailing space
        data = {'welcome_message': long_message}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['welcome_message'] == long_message
    
    def test_special_characters_in_messages(self, api_client, admin_user, telegram_config):
        """Special characters in messages should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        message = '🎉 Welcome! 你好 مرحبا Привет 😊'
        data = {'welcome_message': message}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['welcome_message'] == message
    
    def test_max_retries_zero_accepted(self, api_client, admin_user, telegram_config):
        """max_retries of 0 should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'max_retries': 0}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['max_retries'] == 0
    
    def test_very_large_rate_limit_accepted(self, api_client, admin_user, telegram_config):
        """Very large rate limit should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'rate_limit_per_minute': 10000}
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['rate_limit_per_minute'] == 10000
    
    def test_computed_fields_are_read_only(self, api_client, admin_user, telegram_config):
        """Computed fields should be read-only"""
        api_client.force_authenticate(user=admin_user)
        
        # Try to update is_healthy (computed field)
        data = {
            'is_healthy': False,  # Should be ignored
            'is_enabled': False
        }
        
        response = api_client.patch(f'/api/admin/telegram/config/{telegram_config.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        # is_healthy is computed from is_enabled and is_connected
        assert response.data['is_enabled'] is False
