"""
Tests for Email Send Test API (Task 0.5.31)

Tests the send_test_email action that sends a test email to verify SMTP configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from subscriptions.models import EmailConfiguration

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create regular user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
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
    """Create email configuration with full SMTP settings."""
    config = EmailConfiguration.get_instance()
    config.smtp_host = 'smtp.gmail.com'
    config.smtp_port = 587
    config.use_tls = True
    config.use_ssl = False
    config.smtp_username = 'test@gmail.com'
    config.smtp_password = 'testpass123'
    config.from_email = 'noreply@oxidane.com'
    config.from_name = 'Oxidane Platform'
    config.is_enabled = True
    config.save()
    return config


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestSendTestEmailAccessControl:
    """Test access control for send test email endpoint"""
    
    def test_unauthenticated_cannot_send_test_email(self, api_client, email_config):
        """Unauthenticated users cannot send test emails"""
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_send_test_email(self, api_client, user, email_config):
        """Regular users cannot send test emails"""
        api_client.force_authenticate(user=user)
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_send_test_email(self, api_client, admin_user, email_config):
        """Admin users can send test emails"""
        api_client.force_authenticate(user=admin_user)
        
        with patch('django.core.mail.send_mail') as mock_send:
            mock_send.return_value = 1
            
            response = api_client.post(
                f'/api/admin/email/config/{email_config.id}/send-test/',
                {'recipient': 'test@example.com'},
                format='json'
            )
            
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestSendTestEmailValidation:
    """Test validation for send test email"""
    
    def test_missing_recipient_rejected(self, api_client, admin_user, email_config):
        """Test email send fails without recipient"""
        api_client.force_authenticate(user=admin_user)
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'recipient' in response.data['message'].lower()
    
    def test_invalid_recipient_email_rejected(self, api_client, admin_user, email_config):
        """Test email send fails with invalid email address"""
        api_client.force_authenticate(user=admin_user)
        
        invalid_emails = [
            'not-an-email',
            'missing@domain',
            '@nodomain.com',
            'spaces in@email.com',
            'double@@domain.com'
        ]
        
        for invalid_email in invalid_emails:
            response = api_client.post(
                f'/api/admin/email/config/{email_config.id}/send-test/',
                {'recipient': invalid_email},
                format='json'
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'invalid email' in response.data['message'].lower()
    
    def test_incomplete_config_rejected(self, api_client, admin_user):
        """Test email send fails with incomplete configuration"""
        api_client.force_authenticate(user=admin_user)
        
        # Create incomplete config
        config = EmailConfiguration.get_instance()
        config.smtp_host = ''  # Missing host
        config.save()
        
        response = api_client.post(
            f'/api/admin/email/config/{config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'incomplete' in response.data['message'].lower()


# ============================================================================
# SUCCESSFUL SEND TESTS
# ============================================================================

@pytest.mark.django_db
class TestSendTestEmailSuccess:
    """Test successful email sending"""
    
    @patch('django.core.mail.send_mail')
    def test_successful_email_send(self, mock_send_mail, api_client, admin_user, email_config):
        """Test successful test email send"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'sent successfully' in response.data['message'].lower()
        assert response.data['recipient'] == 'test@example.com'
        assert 'from_email' in response.data
        
        # Verify send_mail was called
        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args[1]
        assert call_kwargs['recipient_list'] == ['test@example.com']
        assert 'Test Email' in call_kwargs['subject']
    
    @patch('django.core.mail.send_mail')
    def test_email_includes_config_details(self, mock_send_mail, api_client, admin_user, email_config):
        """Test that test email includes configuration details"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check email content
        call_kwargs = mock_send_mail.call_args[1]
        message_body = call_kwargs['message']
        
        assert 'smtp.gmail.com' in message_body
        assert '587' in message_body
        assert 'TLS' in message_body or 'SSL' in message_body
    
    @patch('django.core.mail.send_mail')
    def test_from_email_includes_from_name(self, mock_send_mail, api_client, admin_user, email_config):
        """Test that from_email includes from_name when set"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check from_email format
        from_email = response.data['from_email']
        assert 'Oxidane Platform' in from_email
        assert 'noreply@oxidane.com' in from_email


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.django_db
class TestSendTestEmailErrors:
    """Test error handling during email send"""
    
    @patch('django.core.mail.send_mail')
    def test_authentication_failure(self, mock_send_mail, api_client, admin_user, email_config):
        """Test email send fails with authentication error"""
        api_client.force_authenticate(user=admin_user)
        
        import smtplib
        mock_send_mail.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'authentication' in response.data['message'].lower()
    
    @patch('django.core.mail.send_mail')
    def test_smtp_error(self, mock_send_mail, api_client, admin_user, email_config):
        """Test email send fails with SMTP error"""
        api_client.force_authenticate(user=admin_user)
        
        import smtplib
        mock_send_mail.side_effect = smtplib.SMTPException('SMTP error occurred')
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False
        assert 'smtp error' in response.data['message'].lower()
    
    @patch('django.core.mail.send_mail')
    def test_connection_timeout(self, mock_send_mail, api_client, admin_user, email_config):
        """Test email send fails with connection timeout"""
        api_client.force_authenticate(user=admin_user)
        
        mock_send_mail.side_effect = TimeoutError('Connection timeout')
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert response.data['success'] is False
        assert 'timeout' in response.data['message'].lower()
    
    @patch('django.core.mail.send_mail')
    def test_unexpected_error(self, mock_send_mail, api_client, admin_user, email_config):
        """Test email send handles unexpected errors"""
        api_client.force_authenticate(user=admin_user)
        
        mock_send_mail.side_effect = Exception('Unexpected error')
        
        response = api_client.post(
            f'/api/admin/email/config/{email_config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False
        assert 'failed to send' in response.data['message'].lower()


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

@pytest.mark.django_db
class TestSendTestEmailEdgeCases:
    """Test edge cases for send test email"""
    
    @patch('django.core.mail.send_mail')
    def test_send_to_multiple_special_domains(self, mock_send_mail, api_client, admin_user, email_config):
        """Test sending to various email domains"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        test_emails = [
            'test@gmail.com',
            'user@company.co.uk',
            'admin@subdomain.example.org',
            'info+tag@domain.com'
        ]
        
        for email in test_emails:
            response = api_client.post(
                f'/api/admin/email/config/{email_config.id}/send-test/',
                {'recipient': email},
                format='json'
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['recipient'] == email
    
    @patch('django.core.mail.send_mail')
    def test_send_with_empty_from_name(self, mock_send_mail, api_client, admin_user):
        """Test sending with empty from_name still works"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        # Create config without from_name
        config = EmailConfiguration.get_instance()
        config.smtp_host = 'smtp.gmail.com'
        config.smtp_port = 587
        config.use_tls = True
        config.smtp_username = 'test@gmail.com'
        config.smtp_password = 'testpass123'
        config.from_email = 'noreply@oxidane.com'
        config.from_name = ''  # Empty
        config.save()
        
        response = api_client.post(
            f'/api/admin/email/config/{config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # From email should be just the email without name
        from_email = response.data['from_email']
        assert 'noreply@oxidane.com' in from_email
    
    @patch('django.core.mail.send_mail')
    def test_send_with_ssl_instead_of_tls(self, mock_send_mail, api_client, admin_user):
        """Test sending with SSL configuration"""
        api_client.force_authenticate(user=admin_user)
        mock_send_mail.return_value = 1
        
        # Configure for SSL
        config = EmailConfiguration.get_instance()
        config.smtp_host = 'smtp.gmail.com'
        config.smtp_port = 465
        config.use_tls = False
        config.use_ssl = True
        config.smtp_username = 'test@gmail.com'
        config.smtp_password = 'testpass123'
        config.from_email = 'noreply@oxidane.com'
        config.from_name = 'Oxidane'
        config.save()
        
        response = api_client.post(
            f'/api/admin/email/config/{config.id}/send-test/',
            {'recipient': 'test@example.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
