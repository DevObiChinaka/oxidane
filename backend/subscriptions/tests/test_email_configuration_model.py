"""
Comprehensive tests for EmailConfiguration model (Phase 0.5, Task 0.5.9).

Test-Driven Development approach: Write tests FIRST, then implement model.
Target: 50+ comprehensive tests covering all functionality.

Test Categories:
1. Singleton Pattern (6 tests)
2. Basic Operations (8 tests)
3. Validation (10 tests)
4. Connection Testing (8 tests)
5. Security/Encryption (6 tests)
6. Settings Management (6 tests)
7. Edge Cases (6 tests)
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import smtplib

from subscriptions.models import EmailConfiguration

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    return User.objects.create_user(
        email="admin@oxidane.com",
        password="adminpass123",
        is_staff=True,
        is_superuser=True
    )


# ============================================================================
# CATEGORY 1: SINGLETON PATTERN (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigurationSingleton:
    """Test singleton pattern for EmailConfiguration."""

    def test_get_instance_creates_if_not_exists(self):
        """Test that get_instance() creates instance if none exists."""
        # Delete any existing instances
        EmailConfiguration.objects.all().delete()
        
        config = EmailConfiguration.get_instance()
        
        assert config is not None
        assert config.id is not None
        assert EmailConfiguration.objects.count() == 1

    def test_get_instance_returns_same_instance(self):
        """Test that get_instance() returns the same instance."""
        config1 = EmailConfiguration.get_instance()
        config2 = EmailConfiguration.get_instance()
        
        assert config1.id == config2.id

    def test_only_one_instance_allowed(self):
        """Test that creating a second instance raises error."""
        EmailConfiguration.get_instance()
        
        with pytest.raises(ValidationError):
            config = EmailConfiguration()
            config.save()

    def test_update_existing_instance_allowed(self):
        """Test that updating the existing instance works."""
        config = EmailConfiguration.get_instance()
        
        config.smtp_host = "smtp.updated.com"
        config.save()
        
        retrieved = EmailConfiguration.get_instance()
        assert retrieved.smtp_host == "smtp.updated.com"

    def test_delete_and_recreate_allowed(self):
        """Test that deleting and recreating is allowed."""
        config = EmailConfiguration.get_instance()
        old_id = config.id
        
        config.delete()
        
        new_config = EmailConfiguration.get_instance()
        assert new_config.id != old_id

    def test_string_representation(self):
        """Test __str__ method."""
        config = EmailConfiguration.get_instance()
        assert str(config) == "Email Configuration"


# ============================================================================
# CATEGORY 2: BASIC OPERATIONS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigurationBasicOperations:
    """Test basic CRUD operations."""

    def test_create_email_configuration_with_defaults(self):
        """Test creating configuration with default values."""
        config = EmailConfiguration.get_instance()
        
        assert config.id is not None
        assert config.smtp_host == ""
        assert config.smtp_port == 587
        assert config.use_tls is True
        assert config.use_ssl is False
        assert config.smtp_username == ""
        assert config.smtp_password == ""
        assert config.from_email == ""
        assert config.from_name == "OxiWorld"
        assert config.is_enabled is False
        assert config.created_at is not None
        assert config.updated_at is not None

    def test_update_smtp_settings(self):
        """Test updating SMTP host and port."""
        config = EmailConfiguration.get_instance()
        
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 465
        config.use_ssl = True
        config.use_tls = False
        config.save()
        
        config.refresh_from_db()
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 465
        assert config.use_ssl is True
        assert config.use_tls is False

    def test_update_credentials(self):
        """Test updating email credentials."""
        config = EmailConfiguration.get_instance()
        
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.save()
        
        config.refresh_from_db()
        assert config.smtp_username == "test@example.com"
        assert config.smtp_password == "password123"

    def test_update_from_info(self):
        """Test updating from email and name."""
        config = EmailConfiguration.get_instance()
        
        config.from_email = "noreply@oxiworld.com"
        config.from_name = "OxiWorld Academy"
        config.save()
        
        config.refresh_from_db()
        assert config.from_email == "noreply@oxiworld.com"
        assert config.from_name == "OxiWorld Academy"

    def test_toggle_enabled_status(self):
        """Test enabling/disabling email system."""
        config = EmailConfiguration.get_instance()
        
        config.is_enabled = True
        config.save()
        
        config.refresh_from_db()
        assert config.is_enabled is True

    def test_update_connection_status(self):
        """Test updating connection status."""
        config = EmailConfiguration.get_instance()
        
        config.is_connected = True
        config.connection_error = None
        config.save()
        
        config.refresh_from_db()
        assert config.is_connected is True
        assert config.connection_error is None

    def test_set_connection_error(self):
        """Test setting connection error message."""
        config = EmailConfiguration.get_instance()
        
        config.is_connected = False
        config.connection_error = "Authentication failed"
        config.save()
        
        config.refresh_from_db()
        assert config.is_connected is False
        assert config.connection_error == "Authentication failed"

    def test_timestamps_update(self):
        """Test that updated_at changes on save."""
        config = EmailConfiguration.get_instance()
        original_updated = config.updated_at
        
        import time
        time.sleep(0.1)
        
        config.smtp_host = "smtp.updated.com"
        config.save()
        
        assert config.updated_at > original_updated


# ============================================================================
# CATEGORY 3: VALIDATION (10 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigurationValidation:
    """Test validation logic."""

    def test_smtp_port_range_validation(self):
        """Test SMTP port must be in valid range."""
        config = EmailConfiguration.get_instance()
        
        # Valid ports
        config.smtp_port = 25
        config.full_clean()  # Should not raise
        
        config.smtp_port = 587
        config.full_clean()  # Should not raise
        
        config.smtp_port = 465
        config.full_clean()  # Should not raise

    def test_smtp_port_negative_fails(self):
        """Test negative port number fails validation."""
        config = EmailConfiguration.get_instance()
        config.smtp_port = -1
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'smtp_port' in str(exc_info.value)

    def test_smtp_port_too_large_fails(self):
        """Test port number above 65535 fails."""
        config = EmailConfiguration.get_instance()
        config.smtp_port = 70000
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'smtp_port' in str(exc_info.value)

    def test_from_email_format_validation(self):
        """Test from_email must be valid email format."""
        config = EmailConfiguration.get_instance()
        
        # Valid email
        config.from_email = "noreply@oxiworld.com"
        config.full_clean()  # Should not raise
        
        # Invalid email
        config.from_email = "invalid-email"
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'from_email' in str(exc_info.value)

    def test_smtp_username_allows_various_formats(self):
        """Test smtp_username accepts email and non-email formats (e.g., API keys)."""
        config = EmailConfiguration.get_instance()
        
        # Valid email format
        config.smtp_username = "user@example.com"
        config.full_clean()  # Should not raise
        
        # API key format (e.g., SendGrid)
        config.smtp_username = "apikey"
        config.full_clean()  # Should not raise
        
        # Custom username
        config.smtp_username = "smtp-user-123"
        config.full_clean()  # Should not raise
        
        # Empty username should fail (if required by other validation)
        config.smtp_username = ""
        # Note: CharField with blank=True allows empty, so no validation error expected

    def test_cannot_enable_both_tls_and_ssl(self):
        """Test cannot have both TLS and SSL enabled."""
        config = EmailConfiguration.get_instance()
        
        config.use_tls = True
        config.use_ssl = True
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'Cannot enable both TLS and SSL' in str(exc_info.value)

    def test_tls_or_ssl_required(self):
        """Test that at least TLS or SSL must be enabled."""
        config = EmailConfiguration.get_instance()
        
        config.use_tls = False
        config.use_ssl = False
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'TLS or SSL' in str(exc_info.value)

    def test_from_name_length_limit(self):
        """Test from_name has reasonable length limit."""
        config = EmailConfiguration.get_instance()
        
        # Valid length
        config.from_name = "OxiWorld Academy"
        config.full_clean()  # Should not raise
        
        # Too long
        config.from_name = "A" * 300
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        assert 'from_name' in str(exc_info.value)

    def test_connection_error_max_length(self):
        """Test connection_error has max length."""
        config = EmailConfiguration.get_instance()
        
        # Valid length
        config.connection_error = "Authentication failed"
        config.save()  # Should not raise
        
        # Very long error (should truncate or fail)
        long_error = "Error: " * 200
        config.connection_error = long_error
        config.save()
        config.refresh_from_db()
        assert len(config.connection_error) <= 500

    def test_empty_credentials_allowed(self):
        """Test that empty credentials are allowed (for initial setup)."""
        config = EmailConfiguration.get_instance()
        
        config.smtp_username = ""
        config.smtp_password = ""
        config.full_clean()  # Should not raise


# ============================================================================
# CATEGORY 4: CONNECTION TESTING (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConnectionTesting:
    """Test connection testing functionality."""

    @patch('smtplib.SMTP')
    def test_test_connection_success_tls(self, mock_smtp):
        """Test successful TLS connection test."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 587
        config.use_tls = True
        config.use_ssl = False
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.save()
        
        # Mock successful connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = config.test_connection()
        
        assert result['success'] is True
        assert 'Successfully connected' in result['message']
        
        config.refresh_from_db()
        assert config.is_connected is True
        assert config.connection_error is None

    @patch('smtplib.SMTP_SSL')
    def test_test_connection_success_ssl(self, mock_smtp_ssl):
        """Test successful SSL connection test."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 465
        config.use_tls = False
        config.use_ssl = True
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.save()
        
        # Mock successful connection
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        result = config.test_connection()
        
        assert result['success'] is True
        assert 'Successfully connected' in result['message']

    @patch('smtplib.SMTP')
    def test_test_connection_authentication_failure(self, mock_smtp):
        """Test connection test with authentication failure."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 587
        config.use_tls = True
        config.use_ssl = False
        config.smtp_username = "test@example.com"
        config.smtp_password = "wrong_password"
        config.save()
        
        # Mock authentication error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = config.test_connection()
        
        assert result['success'] is False
        assert 'Authentication failed' in result['message']
        
        config.refresh_from_db()
        assert config.is_connected is False
        assert 'Authentication failed' in config.connection_error

    @patch('smtplib.SMTP')
    def test_test_connection_network_error(self, mock_smtp):
        """Test connection test with network error."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.invalid.com"
        config.smtp_port = 587
        config.use_tls = True
        config.use_ssl = False
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.save()
        
        # Mock connection error
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, b'Service not available')
        
        result = config.test_connection()
        
        assert result['success'] is False
        assert 'Failed to connect' in result['message'] or 'Connection error' in result['message']

    def test_test_connection_requires_credentials(self):
        """Test that connection test requires credentials."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 587
        config.smtp_username = ""
        config.smtp_password = ""
        config.save()
        
        result = config.test_connection()
        
        assert result['success'] is False
        assert 'credentials' in result['message'].lower() or 'username' in result['message'].lower()

    def test_test_connection_requires_host(self):
        """Test that connection test requires host."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = ""
        config.smtp_port = 587
        config.save()
        
        result = config.test_connection()
        
        assert result['success'] is False
        assert 'host' in result['message'].lower()

    @patch('smtplib.SMTP')
    def test_mark_as_connected(self, mock_smtp):
        """Test mark_as_connected method."""
        config = EmailConfiguration.get_instance()
        
        config.mark_as_connected()
        
        assert config.is_connected is True
        assert config.connection_error is None

    @patch('smtplib.SMTP')
    def test_mark_as_disconnected(self, mock_smtp):
        """Test mark_as_disconnected method."""
        config = EmailConfiguration.get_instance()
        
        config.mark_as_disconnected("Test error")
        
        assert config.is_connected is False
        assert config.connection_error == "Test error"


# ============================================================================
# CATEGORY 5: SECURITY/ENCRYPTION (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailSecurity:
    """Test security and password masking."""

    def test_get_masked_password_empty(self):
        """Test masking empty password."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = ""
        
        masked = config.get_masked_password()
        assert masked == "(not set)"

    def test_get_masked_password_short(self):
        """Test masking short password."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = "abc"
        
        masked = config.get_masked_password()
        assert masked == "***"

    def test_get_masked_password_normal(self):
        """Test masking normal length password."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = "mypassword123"
        
        masked = config.get_masked_password()
        assert masked.startswith("***")
        assert masked.endswith("23")
        assert len(masked) == 5  # 3 stars + last 2 chars

    def test_get_masked_password_very_long(self):
        """Test masking very long password."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = "a" * 100
        
        masked = config.get_masked_password()
        assert masked.startswith("***")
        assert masked.endswith("aa")

    def test_is_configured_false_without_credentials(self):
        """Test is_configured returns False without credentials."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_username = ""
        config.smtp_password = ""
        
        assert config.is_configured() is False

    def test_is_configured_true_with_credentials(self):
        """Test is_configured returns True with all credentials."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 587
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.from_email = "noreply@example.com"
        
        assert config.is_configured() is True


# ============================================================================
# CATEGORY 6: SETTINGS MANAGEMENT (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailSettingsManagement:
    """Test settings getter/setter methods."""

    def test_get_settings_dict(self):
        """Test getting all settings as dictionary."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 465
        config.smtp_username = "test@example.com"
        config.from_email = "noreply@example.com"
        config.from_name = "OxiWorld"
        config.use_ssl = True
        config.use_tls = False
        config.save()
        
        settings = config.get_settings()
        
        assert settings['smtp_host'] == "smtp.gmail.com"
        assert settings['smtp_port'] == 465
        assert settings['smtp_username'] == "test@example.com"
        assert settings['from_email'] == "noreply@example.com"
        assert settings['from_name'] == "OxiWorld"
        assert settings['use_ssl'] is True
        assert settings['use_tls'] is False
        assert 'smtp_password' in settings
        assert settings['is_enabled'] is False

    def test_update_settings_bulk(self):
        """Test updating multiple settings at once."""
        config = EmailConfiguration.get_instance()
        
        new_settings = {
            'smtp_host': 'smtp.updated.com',
            'smtp_port': 465,
            'use_ssl': True,
            'use_tls': False,
            'from_name': 'Updated Name'
        }
        
        config.update_settings(new_settings)
        
        config.refresh_from_db()
        assert config.smtp_host == 'smtp.updated.com'
        assert config.smtp_port == 465
        assert config.use_ssl is True
        assert config.from_name == 'Updated Name'

    def test_update_settings_ignores_readonly(self):
        """Test that update_settings ignores readonly fields."""
        config = EmailConfiguration.get_instance()
        original_id = config.id
        original_created = config.created_at
        
        config.update_settings({
            'id': 'should-be-ignored',
            'created_at': 'should-be-ignored',
            'smtp_host': 'smtp.updated.com'
        })
        
        config.refresh_from_db()
        assert config.id == original_id
        assert config.created_at == original_created
        assert config.smtp_host == 'smtp.updated.com'

    def test_update_settings_validates(self):
        """Test that update_settings validates data."""
        config = EmailConfiguration.get_instance()
        
        with pytest.raises(ValidationError):
            config.update_settings({
                'smtp_port': -1  # Invalid port
            })

    def test_get_smtp_settings_for_django(self):
        """Test getting SMTP settings in Django format."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "smtp.gmail.com"
        config.smtp_port = 465
        config.smtp_username = "test@example.com"
        config.smtp_password = "password123"
        config.use_ssl = True
        config.use_tls = False
        config.from_email = "noreply@example.com"
        config.save()
        
        django_settings = config.get_smtp_settings_for_django()
        
        assert django_settings['EMAIL_BACKEND'] == 'django.core.mail.backends.smtp.EmailBackend'
        assert django_settings['EMAIL_HOST'] == "smtp.gmail.com"
        assert django_settings['EMAIL_PORT'] == 465
        assert django_settings['EMAIL_HOST_USER'] == "test@example.com"
        assert django_settings['EMAIL_HOST_PASSWORD'] == "password123"
        assert django_settings['EMAIL_USE_SSL'] is True
        assert django_settings['EMAIL_USE_TLS'] is False
        assert django_settings['DEFAULT_FROM_EMAIL'] == "noreply@example.com"

    def test_update_settings_rollback_on_error(self):
        """Test that settings rollback on validation error."""
        config = EmailConfiguration.get_instance()
        config.smtp_host = "original.com"
        config.smtp_port = 587
        config.save()
        
        try:
            config.update_settings({
                'smtp_host': 'updated.com',
                'smtp_port': -1  # This will fail validation
            })
        except ValidationError:
            pass
        
        config.refresh_from_db()
        # Should still have original values
        assert config.smtp_host == "original.com"
        assert config.smtp_port == 587


# ============================================================================
# CATEGORY 7: EDGE CASES (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigurationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_smtp_host(self):
        """Test handling very long SMTP host."""
        config = EmailConfiguration.get_instance()
        
        long_host = "smtp." + "a" * 240 + ".com"  # Max 255 chars
        config.smtp_host = long_host
        config.save()
        
        config.refresh_from_db()
        assert len(config.smtp_host) <= 255

    def test_special_characters_in_password(self):
        """Test password with special characters."""
        config = EmailConfiguration.get_instance()
        
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        config.smtp_password = special_password
        config.save()
        
        config.refresh_from_db()
        assert config.smtp_password == special_password

    def test_unicode_in_from_name(self):
        """Test from_name with unicode characters."""
        config = EmailConfiguration.get_instance()
        
        unicode_name = "OxiWorld 🌍 Academy"
        config.from_name = unicode_name
        config.save()
        
        config.refresh_from_db()
        assert config.from_name == unicode_name

    def test_connection_error_truncation(self):
        """Test that very long error messages are truncated."""
        config = EmailConfiguration.get_instance()
        
        very_long_error = "Error: " + "x" * 1000
        config.connection_error = very_long_error
        config.save()
        
        config.refresh_from_db()
        assert len(config.connection_error) <= 500

    def test_concurrent_updates(self):
        """Test handling concurrent updates to singleton."""
        config1 = EmailConfiguration.get_instance()
        config2 = EmailConfiguration.get_instance()
        
        config1.smtp_host = "smtp1.com"
        config1.save()
        
        config2.smtp_host = "smtp2.com"
        config2.save()
        
        final = EmailConfiguration.get_instance()
        # Last save should win
        assert final.smtp_host == "smtp2.com"

    def test_from_email_case_insensitive(self):
        """Test from_email is stored in lowercase."""
        config = EmailConfiguration.get_instance()
        
        config.from_email = "NoReply@OXIWORLD.COM"
        config.save()
        
        config.refresh_from_db()
        assert config.from_email == "noreply@oxiworld.com"


# ============================================================================
# SUMMARY
# ============================================================================
"""
EMAIL CONFIGURATION MODEL TEST SUMMARY:
========================================

CATEGORY 1: Singleton Pattern (6 tests)
- get_instance creates/returns singleton
- Only one instance allowed
- Update existing allowed
- Delete and recreate allowed

CATEGORY 2: Basic Operations (8 tests)
- Create with defaults
- Update SMTP settings
- Update credentials
- Update from info
- Toggle enabled status
- Update connection status
- Set connection error
- Timestamps update

CATEGORY 3: Validation (10 tests)
- SMTP port range validation
- From email format validation
- Username email format validation
- Cannot enable both TLS and SSL
- TLS or SSL required
- From name length limit
- Connection error max length
- Empty credentials allowed

CATEGORY 4: Connection Testing (8 tests)
- Test connection success (TLS)
- Test connection success (SSL)
- Authentication failure handling
- Network error handling
- Requires credentials
- Requires host
- Mark as connected/disconnected

CATEGORY 5: Security/Encryption (6 tests)
- Password masking (empty, short, normal, long)
- is_configured checks

CATEGORY 6: Settings Management (6 tests)
- Get settings dict
- Update settings bulk
- Ignore readonly fields
- Validate on update
- Get Django-format settings
- Rollback on error

CATEGORY 7: Edge Cases (6 tests)
- Very long host
- Special characters in password
- Unicode in from_name
- Error message truncation
- Concurrent updates
- Case insensitive email

TOTAL: 50 TESTS
===============
All categories comprehensive, following TDD best practices.
"""


# ============================================================================
# CATEGORY 8: ENCRYPTION METHODS (Task 0.5.13) (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestEmailConfigurationEncryption:
    """Test encryption methods for sensitive fields."""

    def test_encrypt_field_smtp_password(self):
        """Test encrypting SMTP password."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = 'mypassword123'
        config.save()
        
        # Encrypt the field
        config.encrypt_field('smtp_password')
        
        # Reload from database
        config.refresh_from_db()
        
        # Field should be encrypted (starts with gAAAAA)
        assert config.smtp_password.startswith('gAAAAA')
        assert 'mypassword123' not in config.smtp_password
    
    def test_decrypt_field_smtp_password(self):
        """Test decrypting SMTP password."""
        config = EmailConfiguration.get_instance()
        original_password = 'mypassword123'
        config.smtp_password = original_password
        config.save()
        
        # Encrypt then decrypt
        config.encrypt_field('smtp_password')
        decrypted = config.decrypt_field('smtp_password')
        
        assert decrypted == original_password
    
    def test_encrypt_field_invalid_field_raises_error(self):
        """Test encrypting invalid field raises ValueError."""
        config = EmailConfiguration.get_instance()
        
        with pytest.raises(ValueError) as exc_info:
            config.encrypt_field('smtp_host')  # Not encryptable
        
        assert 'not encryptable' in str(exc_info.value)
    
    def test_decrypt_field_invalid_field_raises_error(self):
        """Test decrypting invalid field raises ValueError."""
        config = EmailConfiguration.get_instance()
        
        with pytest.raises(ValueError) as exc_info:
            config.decrypt_field('from_email')  # Not encryptable
        
        assert 'not encryptable' in str(exc_info.value)
    
    def test_encrypt_field_empty_value_does_nothing(self):
        """Test encrypting empty field does nothing."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = ''
        config.save()
        
        # Should not raise error
        config.encrypt_field('smtp_password')
        
        assert config.smtp_password == ''
    
    def test_decrypt_field_empty_value_returns_empty_string(self):
        """Test decrypting empty field returns empty string."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = ''
        config.save()
        
        decrypted = config.decrypt_field('smtp_password')
        
        assert decrypted == ""
    
    def test_encrypt_field_already_encrypted_skips(self):
        """Test encrypting already encrypted field skips re-encryption."""
        config = EmailConfiguration.get_instance()
        config.smtp_password = 'mypassword123'
        config.save()
        
        # Encrypt once
        config.encrypt_field('smtp_password')
        encrypted_value = config.smtp_password
        
        # Encrypt again (should skip)
        config.encrypt_field('smtp_password')
        
        # Value should not change
        assert config.smtp_password == encrypted_value
    
    def test_decrypt_field_plaintext_returns_as_is(self):
        """Test decrypting plaintext field returns it as-is."""
        config = EmailConfiguration.get_instance()
        plaintext = 'mypassword123'
        config.smtp_password = plaintext
        config.save()
        
        # Decrypt without encrypting first
        decrypted = config.decrypt_field('smtp_password')
        
        # Should return plaintext as-is
        assert decrypted == plaintext
