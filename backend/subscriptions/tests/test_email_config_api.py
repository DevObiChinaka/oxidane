"""
Tests for Email Configuration API (Phase 0.5 - Task 0.5.30)

Tests cover:
- Access control (unauthenticated, regular user, admin)
- CRUD operations (list, retrieve, create, update, partial_update)
- Singleton behavior (only one instance)
- Validation (SMTP settings, TLS/SSL, port, email format)
- Masked password display (never expose raw password)
- Test connection action (successful and failed)
- Edge cases (empty values, special characters, encryption)
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import smtplib

from subscriptions.models import EmailConfiguration

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client for testing."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create regular user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_staff=False
    )


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True
    )


@pytest.fixture
def email_config(db):
    """Create email configuration with SMTP settings."""
    config = EmailConfiguration.get_instance()
    config.smtp_host = 'smtp.gmail.com'
    config.smtp_port = 587
    config.use_tls = True
    config.use_ssl = False
    config.smtp_username = 'test@gmail.com'
    config.smtp_password = 'testpassword123'
    config.from_email = 'noreply@oxidane.com'
    config.from_name = 'OxiWorld'
    config.is_enabled = True
    config.save()
    return config


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigAccessControl:
    """Test access control for Email Configuration API"""
    
    def test_unauthenticated_cannot_access(self, api_client):
        """Unauthenticated users should be blocked"""
        response = api_client.get('/api/admin/email/config/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access(self, api_client, user):
        """Regular users should be forbidden"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/admin/email/config/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access(self, api_client, admin_user):
        """Admin users should have full access"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/email/config/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# CRUD TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigCRUD:
    """Test CRUD operations for Email Configuration"""
    
    def test_list_returns_singleton_as_list(self, api_client, admin_user, email_config):
        """List endpoint should return singleton config as a list"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/email/config/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]['smtp_host'] == 'smtp.gmail.com'
    
    def test_retrieve_returns_config_details(self, api_client, admin_user, email_config):
        """Retrieve should return config details (ID is ignored due to singleton)"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['smtp_host'] == 'smtp.gmail.com'
        assert response.data['smtp_port'] == 587
        assert response.data['use_tls'] is True
        assert 'masked_smtp_password' in response.data
        assert 'smtp_password' not in response.data  # Raw password never exposed
    
    def test_create_updates_existing_config(self, api_client, admin_user):
        """POST should update existing config (singleton behavior)"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.sendgrid.net',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'apikey',
            'smtp_password_write': 'SG.abc123xyz',
            'from_email': 'noreply@oxidane.com',
            'from_name': 'Oxidane Platform',
            'is_enabled': True
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['smtp_host'] == 'smtp.sendgrid.net'
        assert response.data['smtp_username'] == 'apikey'
        assert 'smtp_password_write' not in response.data
        assert 'masked_smtp_password' in response.data
    
    def test_update_modifies_config(self, api_client, admin_user, email_config):
        """PUT should update config fields"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.mailgun.org',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'postmaster@oxidane.com',
            'smtp_password_write': 'newpassword456',
            'from_email': 'hello@oxidane.com',
            'from_name': 'Oxidane Team',
            'is_enabled': True
        }
        
        response = api_client.put(
            f'/api/admin/email/config/{email_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['smtp_host'] == 'smtp.mailgun.org'
        assert response.data['from_email'] == 'hello@oxidane.com'
    
    def test_partial_update_modifies_specific_fields(self, api_client, admin_user, email_config):
        """PATCH should update only specified fields"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'from_name': 'Oxidane Support',
            'is_enabled': False
        }
        
        response = api_client.patch(
            f'/api/admin/email/config/{email_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['from_name'] == 'Oxidane Support'
        assert response.data['is_enabled'] is False
        # Other fields should remain unchanged
        assert response.data['smtp_host'] == 'smtp.gmail.com'


# ============================================================================
# SINGLETON TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigSingleton:
    """Test singleton pattern enforcement"""
    
    def test_only_one_instance_exists(self, email_config):
        """Only one EmailConfiguration instance should exist"""
        assert EmailConfiguration.objects.count() == 1
        
        # Trying to get instance again should return same one
        config2 = EmailConfiguration.get_instance()
        assert config2.id == email_config.id
    
    def test_get_instance_creates_if_not_exists(self, db):
        """get_instance should create config if none exists"""
        # Delete all instances
        EmailConfiguration.objects.all().delete()
        assert EmailConfiguration.objects.count() == 0
        
        # Get instance should create one
        config = EmailConfiguration.get_instance()
        assert config is not None
        assert EmailConfiguration.objects.count() == 1


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigValidation:
    """Test field validation"""
    
    def test_invalid_smtp_port_rejected(self, api_client, admin_user):
        """Invalid SMTP port should be rejected"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 99999,  # Invalid port
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'smtp_port' in str(response.data)
    
    def test_negative_smtp_port_rejected(self, api_client, admin_user):
        """Negative SMTP port should be rejected"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': -1,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_both_tls_and_ssl_rejected(self, api_client, admin_user):
        """Cannot enable both TLS and SSL"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': True,  # Both enabled - invalid
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'use_ssl' in str(response.data) or 'use_tls' in str(response.data)
    
    def test_neither_tls_nor_ssl_rejected(self, api_client, admin_user):
        """Either TLS or SSL must be enabled"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': False,
            'use_ssl': False,  # Both disabled - invalid
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_smtp_username_rejected(self, api_client, admin_user):
        """Empty SMTP username should be rejected"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': '   ',  # Empty/whitespace
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'smtp_username' in str(response.data)
    
    def test_empty_smtp_host_rejected(self, api_client, admin_user):
        """Empty SMTP host should be rejected"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': '   ',  # Whitespace only
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_valid_config_accepted(self, api_client, admin_user):
        """Valid configuration should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'noreply@oxidane.com',
            'from_name': 'OxiWorld',
            'is_enabled': True
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# MASKED PASSWORD TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigMaskedPassword:
    """Test that SMTP password is never exposed"""
    
    def test_password_not_in_response(self, api_client, admin_user, email_config):
        """smtp_password should never be in API responses"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert 'smtp_password' not in response.data
        assert 'smtp_password_write' not in response.data
    
    def test_masked_password_displayed(self, api_client, admin_user, email_config):
        """masked_smtp_password should show partial password"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert 'masked_smtp_password' in response.data
        masked = response.data['masked_smtp_password']
        assert masked.startswith('***')
        assert len(masked) >= 3
    
    def test_update_with_password_shows_new_masked_password(self, api_client, admin_user, email_config):
        """After updating password, masked_password should reflect new value"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'smtp_password_write': 'newpassword999'}
        
        response = api_client.patch(
            f'/api/admin/email/config/{email_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'masked_smtp_password' in response.data
        # Password should be updated
        email_config.refresh_from_db()
        assert email_config.get_masked_password() == response.data['masked_smtp_password']


# ============================================================================
# TEST CONNECTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigTestConnection:
    """Test the test_connection custom action"""
    
    @patch('smtplib.SMTP')
    def test_successful_connection_tls(self, mock_smtp, api_client, admin_user, email_config):
        """Test successful TLS connection"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock SMTP connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'smtp.gmail.com' in response.data['message']
        assert response.data['host'] == 'smtp.gmail.com'
        assert response.data['port'] == 587
        assert response.data['encryption'] == 'TLS'
    
    @patch('smtplib.SMTP_SSL')
    def test_successful_connection_ssl(self, mock_smtp_ssl, api_client, admin_user, email_config):
        """Test successful SSL connection"""
        api_client.force_authenticate(user=admin_user)
        
        # Configure for SSL
        email_config.smtp_port = 465
        email_config.use_tls = False
        email_config.use_ssl = True
        email_config.save()
        
        # Mock SMTP_SSL connection
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['encryption'] == 'SSL'
    
    def test_connection_without_host_fails(self, api_client, admin_user, email_config):
        """Test connection fails when host is not configured"""
        api_client.force_authenticate(user=admin_user)
        
        email_config.smtp_host = ''
        email_config.save()
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'host' in response.data['message'].lower()
    
    def test_connection_without_credentials_fails(self, api_client, admin_user, email_config):
        """Test connection fails when credentials are missing"""
        api_client.force_authenticate(user=admin_user)
        
        email_config.smtp_username = ''
        email_config.smtp_password = ''
        email_config.save()
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'credentials' in response.data['message'].lower()
    
    @patch('smtplib.SMTP')
    def test_connection_authentication_failure(self, mock_smtp, api_client, admin_user, email_config):
        """Test connection fails with authentication error"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock authentication failure
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'authentication' in response.data['message'].lower()
    
    @patch('smtplib.SMTP')
    def test_connection_timeout(self, mock_smtp, api_client, admin_user, email_config):
        """Test connection timeout handling"""
        api_client.force_authenticate(user=admin_user)
        
        # Mock connection timeout
        mock_smtp.side_effect = TimeoutError('Connection timeout')
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/test-connection/'
        )
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert response.data['success'] is False
        assert 'timeout' in response.data['message'].lower()


# ============================================================================
# COMPUTED FIELDS TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigComputedFields:
    """Test computed fields"""
    
    def test_is_configured_true(self, api_client, admin_user, email_config):
        """is_configured should be True when all required fields set"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert response.data['is_configured'] is True
    
    def test_is_configured_false_missing_host(self, api_client, admin_user, email_config):
        """is_configured should be False when host missing"""
        api_client.force_authenticate(user=admin_user)
        
        email_config.smtp_host = ''
        email_config.save()
        
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert response.data['is_configured'] is False
    
    def test_connection_status_field(self, api_client, admin_user, email_config):
        """connection_status should return status info"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.get(f'/api/admin/email/config/{email_config.id}/')
        
        assert 'connection_status' in response.data
        assert 'is_connected' in response.data['connection_status']
        assert 'last_test_at' in response.data['connection_status']


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_from_name_accepted(self, api_client, admin_user):
        """Empty from_name should be accepted (optional field)"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
            'from_name': '',  # Empty
            'is_enabled': True
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_ssl_port_465_accepted(self, api_client, admin_user):
        """SSL with port 465 should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 465,
            'use_tls': False,
            'use_ssl': True,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_tls_port_587_accepted(self, api_client, admin_user):
        """TLS with port 587 should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_disable_email_sending(self, api_client, admin_user, email_config):
        """Can disable email sending"""
        api_client.force_authenticate(user=admin_user)
        
        data = {'is_enabled': False}
        
        response = api_client.patch(
            f'/api/admin/email/config/{email_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_enabled'] is False
    
    def test_special_characters_in_from_name(self, api_client, admin_user):
        """Special characters in from_name should be accepted"""
        api_client.force_authenticate(user=admin_user)
        
        data = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'use_ssl': False,
            'smtp_username': 'test@gmail.com',
            'smtp_password_write': 'password123',
            'from_email': 'test@oxidane.com',
            'from_name': 'OxiWorld™ Support 💬',
        }
        
        response = api_client.post('/api/admin/email/config/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['from_name'] == 'OxiWorld™ Support 💬'
