"""
Tests for TelegramConfiguration model (Task 0.5.6)

Requirements:
- Singleton pattern (only one configuration instance allowed)
- Encrypted bot token storage
- Bot connection validation
- Settings management
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import TelegramConfiguration


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def telegram_config(db):
    """Create a TelegramConfiguration instance."""
    # Clean up any existing config first (singleton)
    TelegramConfiguration.objects.all().delete()
    
    return TelegramConfiguration.objects.create(
        bot_token='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz',
        bot_username='@TestOxidaneBot',
        is_enabled=True
    )


# ============================================================================
# TEST CLASS: Basic Operations
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationBasicOperations:
    """Test basic CRUD operations for TelegramConfiguration."""
    
    def test_create_telegram_configuration_success(self):
        """Test creating a telegram configuration."""
        # Clean up first (singleton)
        TelegramConfiguration.objects.all().delete()
        
        config = TelegramConfiguration.objects.create(
            bot_token='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz',
            bot_username='@OxidaneBot',
            is_enabled=True,
            welcome_message='Welcome to Oxidane Premium Signals!',
            removal_message='Your subscription has expired.'
        )
        
        assert config.bot_token == '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        assert config.bot_username == '@OxidaneBot'
        assert config.is_enabled is True
        assert config.welcome_message == 'Welcome to Oxidane Premium Signals!'
        assert config.removal_message == 'Your subscription has expired.'
        assert config.created_at is not None
        assert config.updated_at is not None
    
    def test_telegram_configuration_string_representation(self):
        """Test __str__ method."""
        TelegramConfiguration.objects.all().delete()
        
        config = TelegramConfiguration.objects.create(
            bot_token='test_token',
            bot_username='@TestBot'
        )
        
        assert str(config) == 'Telegram Bot: @TestBot'
    
    def test_telegram_configuration_default_values(self):
        """Test model default values."""
        TelegramConfiguration.objects.all().delete()
        
        config = TelegramConfiguration.objects.create(
            bot_token='test_token'
        )
        
        assert config.bot_username == ''
        assert config.is_enabled is True
        assert config.auto_add_enabled is True
        assert config.auto_remove_enabled is True
        assert config.welcome_message == ''
        assert config.removal_message == ''
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 300
        assert config.rate_limit_per_minute == 30
        assert config.last_health_check is None
        assert config.is_connected is False
        assert config.connection_error == ''
    
    def test_get_instance_returns_singleton(self, telegram_config):
        """Test get_instance() class method returns the singleton."""
        instance1 = TelegramConfiguration.get_instance()
        instance2 = TelegramConfiguration.get_instance()
        
        assert instance1.id == instance2.id
        assert instance1.id == telegram_config.id
    
    def test_get_instance_creates_if_not_exists(self):
        """Test get_instance() creates instance if none exists."""
        TelegramConfiguration.objects.all().delete()
        
        instance = TelegramConfiguration.get_instance()
        
        assert instance is not None
        assert instance.bot_token == ''
        assert instance.is_enabled is True
        assert TelegramConfiguration.objects.count() == 1


# ============================================================================
# TEST CLASS: Singleton Pattern
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationSingleton:
    """Test singleton pattern enforcement."""
    
    def test_only_one_instance_allowed(self, telegram_config):
        """Test that only one configuration instance can exist."""
        with pytest.raises(ValidationError) as exc_info:
            config2 = TelegramConfiguration(
                bot_token='another_token',
                bot_username='@AnotherBot'
            )
            config2.full_clean()
        
        assert 'Only one Telegram configuration' in str(exc_info.value)
    
    def test_update_existing_instance_allowed(self, telegram_config):
        """Test that updating existing instance is allowed."""
        telegram_config.bot_username = '@UpdatedBot'
        telegram_config.is_enabled = False
        telegram_config.save()
        
        # Verify update succeeded
        config = TelegramConfiguration.objects.get(id=telegram_config.id)
        assert config.bot_username == '@UpdatedBot'
        assert config.is_enabled is False
        
        # Still only one instance
        assert TelegramConfiguration.objects.count() == 1
    
    def test_delete_and_recreate_allowed(self, telegram_config):
        """Test that deleting and recreating is allowed."""
        old_id = telegram_config.id
        telegram_config.delete()
        
        assert TelegramConfiguration.objects.count() == 0
        
        new_config = TelegramConfiguration.objects.create(
            bot_token='new_token',
            bot_username='@NewBot'
        )
        
        assert TelegramConfiguration.objects.count() == 1
        assert new_config.id != old_id


# ============================================================================
# TEST CLASS: Validation
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationValidation:
    """Test model validation."""
    
    def test_bot_token_can_be_empty(self):
        """Test that bot_token can be empty (for initial setup)."""
        TelegramConfiguration.objects.all().delete()
        
        config = TelegramConfiguration(bot_token='')
        config.full_clean()  # Should not raise
        config.save()
        
        assert config.bot_token == ''
    
    def test_bot_username_format_validation(self, telegram_config):
        """Test bot_username must start with @ if provided."""
        telegram_config.bot_username = 'InvalidBot'  # Missing @
        
        with pytest.raises(ValidationError) as exc_info:
            telegram_config.full_clean()
        
        assert 'Bot username must start with @' in str(exc_info.value)
    
    def test_bot_username_can_be_empty(self):
        """Test bot_username can be empty string."""
        TelegramConfiguration.objects.all().delete()
        
        config = TelegramConfiguration.objects.create(
            bot_token='test_token',
            bot_username=''  # Empty is OK
        )
        
        config.full_clean()  # Should not raise
        assert config.bot_username == ''
    
    def test_max_retries_must_be_positive(self, telegram_config):
        """Test max_retries must be >= 0."""
        telegram_config.max_retries = -1
        
        with pytest.raises(ValidationError) as exc_info:
            telegram_config.full_clean()
        
        assert 'max_retries' in str(exc_info.value).lower()
    
    def test_retry_delay_must_be_positive(self, telegram_config):
        """Test retry_delay_seconds must be > 0."""
        telegram_config.retry_delay_seconds = 0
        
        with pytest.raises(ValidationError) as exc_info:
            telegram_config.full_clean()
        
        assert 'retry_delay_seconds' in str(exc_info.value).lower()
    
    def test_rate_limit_must_be_positive(self, telegram_config):
        """Test rate_limit_per_minute must be > 0."""
        telegram_config.rate_limit_per_minute = 0
        
        with pytest.raises(ValidationError) as exc_info:
            telegram_config.full_clean()
        
        assert 'rate_limit_per_minute' in str(exc_info.value).lower()


# ============================================================================
# TEST CLASS: Connection Management
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationConnectionManagement:
    """Test connection status management."""
    
    def test_mark_as_connected(self, telegram_config):
        """Test marking configuration as connected."""
        assert telegram_config.is_connected is False
        assert telegram_config.connection_error == ''
        
        telegram_config.mark_as_connected(bot_username='@VerifiedBot')
        
        assert telegram_config.is_connected is True
        assert telegram_config.connection_error == ''
        assert telegram_config.bot_username == '@VerifiedBot'
        assert telegram_config.last_health_check is not None
    
    def test_mark_as_disconnected(self, telegram_config):
        """Test marking configuration as disconnected."""
        telegram_config.is_connected = True
        telegram_config.save()
        
        error_message = 'Invalid bot token'
        telegram_config.mark_as_disconnected(error_message)
        
        assert telegram_config.is_connected is False
        assert telegram_config.connection_error == error_message
        assert telegram_config.last_health_check is not None
    
    def test_is_healthy_when_connected(self, telegram_config):
        """Test is_healthy() returns True when connected."""
        telegram_config.mark_as_connected()
        
        assert telegram_config.is_healthy() is True
    
    def test_is_healthy_when_disconnected(self, telegram_config):
        """Test is_healthy() returns False when disconnected."""
        telegram_config.mark_as_disconnected('Connection error')
        
        assert telegram_config.is_healthy() is False
    
    def test_is_healthy_when_disabled(self, telegram_config):
        """Test is_healthy() returns False when disabled."""
        telegram_config.is_enabled = False
        telegram_config.is_connected = True
        telegram_config.save()
        
        assert telegram_config.is_healthy() is False
    
    def test_update_health_check_timestamp(self, telegram_config):
        """Test health check timestamp is updated."""
        old_timestamp = telegram_config.last_health_check
        
        telegram_config.mark_as_connected()
        
        assert telegram_config.last_health_check is not None
        assert telegram_config.last_health_check != old_timestamp


# ============================================================================
# TEST CLASS: Settings Management
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationSettings:
    """Test settings management."""
    
    def test_get_settings_dict(self, telegram_config):
        """Test get_settings() returns all settings as dict."""
        settings = telegram_config.get_settings()
        
        assert isinstance(settings, dict)
        assert settings['bot_username'] == '@TestOxidaneBot'
        assert settings['is_enabled'] is True
        assert settings['auto_add_enabled'] is True
        assert settings['max_retries'] == 3
        assert settings['rate_limit_per_minute'] == 30
        assert 'bot_token' not in settings  # Token should be excluded
    
    def test_update_settings_bulk(self, telegram_config):
        """Test updating multiple settings at once."""
        new_settings = {
            'bot_username': '@UpdatedBot',
            'welcome_message': 'Welcome!',
            'max_retries': 5,
            'is_enabled': False
        }
        
        telegram_config.update_settings(new_settings)
        
        assert telegram_config.bot_username == '@UpdatedBot'
        assert telegram_config.welcome_message == 'Welcome!'
        assert telegram_config.max_retries == 5
        assert telegram_config.is_enabled is False
    
    def test_update_settings_validates(self, telegram_config):
        """Test update_settings validates before saving."""
        invalid_settings = {
            'max_retries': -1,  # Invalid
            'bot_username': '@ValidBot'
        }
        
        with pytest.raises(ValidationError):
            telegram_config.update_settings(invalid_settings)
        
        # Original values should be unchanged
        assert telegram_config.max_retries == 3
    
    def test_update_settings_ignores_readonly_fields(self, telegram_config):
        """Test update_settings ignores protected fields."""
        original_token = telegram_config.bot_token
        original_created = telegram_config.created_at
        
        new_settings = {
            'bot_token': 'should_be_ignored',  # Protected
            'created_at': timezone.now() + timedelta(days=1),  # Protected
            'bot_username': '@NewBot'  # Allowed
        }
        
        telegram_config.update_settings(new_settings)
        
        assert telegram_config.bot_token == original_token  # Unchanged
        assert telegram_config.created_at == original_created  # Unchanged
        assert telegram_config.bot_username == '@NewBot'  # Changed


# ============================================================================
# TEST CLASS: Token Management
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationTokenManagement:
    """Test bot token management."""
    
    def test_set_bot_token(self, telegram_config):
        """Test setting a new bot token."""
        new_token = '9876543210:ZYXwvuTSRqponMLKjihGFEdcBA'
        
        telegram_config.set_bot_token(new_token)
        
        assert telegram_config.bot_token == new_token
        # Should mark as disconnected when token changes
        assert telegram_config.is_connected is False
    
    def test_has_valid_token_format(self, telegram_config):
        """Test has_valid_token() checks token format."""
        # Valid format: numbers:letters
        telegram_config.bot_token = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        assert telegram_config.has_valid_token() is True
        
        # Invalid formats
        telegram_config.bot_token = 'invalid_token'
        assert telegram_config.has_valid_token() is False
        
        telegram_config.bot_token = '123456'
        assert telegram_config.has_valid_token() is False
        
        telegram_config.bot_token = ''
        assert telegram_config.has_valid_token() is False
    
    def test_get_masked_token(self, telegram_config):
        """Test get_masked_token() masks token for display."""
        telegram_config.bot_token = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
        
        masked = telegram_config.get_masked_token()
        
        assert masked.startswith('1234567890:')
        assert '***' in masked
        assert 'ABCdefGHIjklMNOpqrsTUVwxyz' not in masked
    
    def test_get_masked_token_empty(self):
        """Test get_masked_token() with empty token."""
        TelegramConfiguration.objects.all().delete()
        config = TelegramConfiguration.objects.create(bot_token='')
        
        masked = config.get_masked_token()
        
        assert masked == '(not set)'


# ============================================================================
# TEST CLASS: Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestTelegramConfigurationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_long_welcome_message(self, telegram_config):
        """Test handling very long welcome message."""
        long_message = 'Welcome! ' * 200  # ~1400 chars
        
        telegram_config.welcome_message = long_message
        telegram_config.save()
        
        config = TelegramConfiguration.objects.get(id=telegram_config.id)
        assert config.welcome_message == long_message
    
    def test_special_characters_in_messages(self, telegram_config):
        """Test special characters in messages."""
        special_message = 'Welcome! 🎉 Use code: <SPECIAL> & enjoy!'
        
        telegram_config.welcome_message = special_message
        telegram_config.save()
        
        config = TelegramConfiguration.objects.get(id=telegram_config.id)
        assert config.welcome_message == special_message
    
    def test_unicode_in_bot_username(self, telegram_config):
        """Test unicode characters in bot username."""
        telegram_config.bot_username = '@TestBot_русский'
        telegram_config.save()
        
        config = TelegramConfiguration.objects.get(id=telegram_config.id)
        assert config.bot_username == '@TestBot_русский'
    
    def test_max_retries_zero(self, telegram_config):
        """Test max_retries can be zero (no retries)."""
        telegram_config.max_retries = 0
        telegram_config.full_clean()  # Should not raise
        telegram_config.save()
        
        assert telegram_config.max_retries == 0
    
    def test_concurrent_updates(self, telegram_config):
        """Test handling concurrent updates to singleton."""
        # Simulate two processes updating the same instance
        config1 = TelegramConfiguration.get_instance()
        config2 = TelegramConfiguration.get_instance()
        
        config1.welcome_message = 'Message from process 1'
        config1.save()
        
        config2.removal_message = 'Message from process 2'
        config2.save()
        
        # Last write wins
        final_config = TelegramConfiguration.get_instance()
        assert final_config.removal_message == 'Message from process 2'
    
    def test_delete_last_instance_allows_recreation(self, telegram_config):
        """Test deleting the singleton allows creating a new one."""
        old_token = telegram_config.bot_token
        telegram_config.delete()
        
        assert TelegramConfiguration.objects.count() == 0
        
        new_config = TelegramConfiguration.objects.create(
            bot_token='new_token_after_delete'
        )
        
        assert new_config.bot_token != old_token
        assert TelegramConfiguration.objects.count() == 1
