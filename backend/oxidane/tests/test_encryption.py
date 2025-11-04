"""
Tests for encryption utilities (Phase 0.5.12)

Tests Fernet-based encryption/decryption for sensitive data.
"""

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from oxidane.encryption import (
    EncryptionService, 
    EncryptionError, 
    EncryptionKeyError,
    encryption_service,
    encrypt_field,
    decrypt_field,
    generate_encryption_key
)
from cryptography.fernet import Fernet


class TestEncryptionService:
    """Test the EncryptionService class."""
    
    def test_encryption_service_initialization(self):
        """Test that encryption service initializes properly."""
        service = EncryptionService()
        assert service._fernet is not None
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption."""
        service = EncryptionService()
        
        original = "my-secret-api-key"
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string returns empty string."""
        service = EncryptionService()
        
        encrypted = service.encrypt("")
        assert encrypted == ""
    
    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string."""
        service = EncryptionService()
        
        decrypted = service.decrypt("")
        assert decrypted == ""
    
    def test_encrypt_unicode_string(self):
        """Test encrypting Unicode characters."""
        service = EncryptionService()
        
        original = "Hëllö Wörld 🌍 こんにちは"
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_long_string(self):
        """Test encrypting very long strings."""
        service = EncryptionService()
        
        original = "x" * 10000  # 10KB string
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_decrypt_invalid_token_raises_error(self):
        """Test that decrypting invalid data raises EncryptionError."""
        service = EncryptionService()
        
        with pytest.raises(EncryptionError) as exc_info:
            service.decrypt("invalid-encrypted-data")
        
        assert "Invalid token" in str(exc_info.value)
    
    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decrypting with wrong key raises EncryptionError."""
        # Encrypt with one key
        service1 = EncryptionService()
        encrypted = service1.encrypt("secret")
        
        # Try to decrypt with different key
        original_key = settings.ENCRYPTION_KEY
        try:
            settings.ENCRYPTION_KEY = Fernet.generate_key()
            service2 = EncryptionService()
            
            with pytest.raises(EncryptionError) as exc_info:
                service2.decrypt(encrypted)
            
            assert "Invalid token" in str(exc_info.value)
        finally:
            settings.ENCRYPTION_KEY = original_key
    
    def test_encrypt_dict_with_fields(self):
        """Test encrypting specific fields in a dictionary."""
        service = EncryptionService()
        
        data = {
            'api_key': 'secret-key-123',
            'name': 'Test User',
            'password': 'my-password'
        }
        
        encrypted = service.encrypt_dict(data, ['api_key', 'password'])
        
        # Check that specified fields are encrypted
        assert encrypted['api_key'] != 'secret-key-123'
        assert encrypted['password'] != 'my-password'
        
        # Check that other fields are unchanged
        assert encrypted['name'] == 'Test User'
    
    def test_decrypt_dict_with_fields(self):
        """Test decrypting specific fields in a dictionary."""
        service = EncryptionService()
        
        data = {
            'api_key': 'secret-key-123',
            'name': 'Test User',
            'password': 'my-password'
        }
        
        encrypted = service.encrypt_dict(data, ['api_key', 'password'])
        decrypted = service.decrypt_dict(encrypted, ['api_key', 'password'])
        
        # Check that fields are decrypted correctly
        assert decrypted['api_key'] == 'secret-key-123'
        assert decrypted['password'] == 'my-password'
        assert decrypted['name'] == 'Test User'
    
    def test_decrypt_dict_with_invalid_field_continues(self):
        """Test that decrypt_dict continues on error (legacy data)."""
        service = EncryptionService()
        
        data = {
            'api_key': 'invalid-encrypted-data',
            'name': 'Test User'
        }
        
        # Should not raise error, just leave field as-is
        decrypted = service.decrypt_dict(data, ['api_key'])
        assert decrypted['api_key'] == 'invalid-encrypted-data'
    
    def test_generate_key_creates_valid_key(self):
        """Test that generate_key creates a valid Fernet key."""
        key = EncryptionService.generate_key()
        
        # Should be base64-encoded and 44 characters long
        assert isinstance(key, str)
        assert len(key) == 44
        
        # Should be a valid Fernet key
        Fernet(key.encode('utf-8'))  # Will raise error if invalid
    
    def test_is_encrypted_detects_encrypted_data(self):
        """Test that is_encrypted correctly identifies encrypted data."""
        service = EncryptionService()
        
        encrypted = service.encrypt("secret")
        assert service.is_encrypted(encrypted) is True
    
    def test_is_encrypted_detects_plaintext(self):
        """Test that is_encrypted returns False for plaintext."""
        service = EncryptionService()
        
        assert service.is_encrypted("plaintext") is False
        assert service.is_encrypted("") is False
        assert service.is_encrypted(None) is False
    
    def test_is_encrypted_detects_short_string(self):
        """Test that is_encrypted returns False for short strings."""
        service = EncryptionService()
        
        # Even if starts with 'gAAAAA', too short to be valid
        assert service.is_encrypted("gAAAAA") is False


class TestConvenienceFunctions:
    """Test the convenience wrapper functions."""
    
    def test_encrypt_field_function(self):
        """Test the encrypt_field convenience function."""
        original = "secret-value"
        encrypted = encrypt_field(original)
        
        assert encrypted != original
        assert encrypted.startswith('gAAAAA')
    
    def test_decrypt_field_function(self):
        """Test the decrypt_field convenience function."""
        original = "secret-value"
        encrypted = encrypt_field(original)
        decrypted = decrypt_field(encrypted)
        
        assert decrypted == original
    
    def test_generate_encryption_key_function(self):
        """Test the generate_encryption_key convenience function."""
        key = generate_encryption_key()
        
        assert isinstance(key, str)
        assert len(key) == 44
        
        # Should be valid Fernet key
        Fernet(key.encode('utf-8'))


class TestEncryptionServiceSingleton:
    """Test the global encryption_service singleton."""
    
    def test_encryption_service_singleton_works(self):
        """Test that the global singleton instance works."""
        original = "test-secret"
        encrypted = encryption_service.encrypt(original)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == original


class TestEncryptionKeyConfiguration:
    """Test encryption key configuration and error handling."""
    
    def test_missing_encryption_key_raises_error(self, monkeypatch):
        """Test that missing ENCRYPTION_KEY raises EncryptionKeyError."""
        # Remove ENCRYPTION_KEY from settings
        monkeypatch.delattr(settings, 'ENCRYPTION_KEY', raising=False)
        
        with pytest.raises(EncryptionKeyError) as exc_info:
            EncryptionService()
        
        assert "ENCRYPTION_KEY not found" in str(exc_info.value)
    
    def test_invalid_encryption_key_raises_error(self, monkeypatch):
        """Test that invalid ENCRYPTION_KEY raises EncryptionKeyError."""
        # Set invalid key
        monkeypatch.setattr(settings, 'ENCRYPTION_KEY', 'invalid-key')
        
        with pytest.raises(EncryptionKeyError) as exc_info:
            EncryptionService()
        
        assert "Invalid ENCRYPTION_KEY" in str(exc_info.value)


class TestEncryptionFormats:
    """Test encryption format and compatibility."""
    
    def test_encrypted_format_is_fernet_compatible(self):
        """Test that encrypted data follows Fernet format."""
        service = EncryptionService()
        
        encrypted = service.encrypt("test")
        
        # Fernet tokens are base64-encoded and start with 'gAAAAA'
        assert encrypted.startswith('gAAAAA')
        assert len(encrypted) >= 60  # Minimum Fernet token size
    
    def test_encryption_is_deterministic_false(self):
        """Test that encrypting same value twice gives different results."""
        service = EncryptionService()
        
        value = "same-value"
        encrypted1 = service.encrypt(value)
        encrypted2 = service.encrypt(value)
        
        # Should be different (Fernet uses random IV)
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert service.decrypt(encrypted1) == value
        assert service.decrypt(encrypted2) == value
    
    def test_encryption_includes_timestamp(self):
        """Test that Fernet encryption includes timestamp."""
        service = EncryptionService()
        
        encrypted = service.encrypt("test")
        
        # Fernet tokens include timestamp, so re-encrypting
        # should give different result even immediately
        import time
        time.sleep(0.1)
        
        encrypted2 = service.encrypt("test")
        assert encrypted != encrypted2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_encrypt_none_value(self):
        """Test behavior with None value."""
        service = EncryptionService()
        
        # None is falsy, so encrypt returns empty string
        result = service.encrypt(None)
        assert result == ""
    
    def test_encrypt_numeric_value(self):
        """Test encrypting numeric values raises EncryptionError."""
        service = EncryptionService()
        
        # Numbers should be converted to string first by caller
        # Trying to encrypt a number raises EncryptionError
        with pytest.raises(EncryptionError):
            service.encrypt(12345)
    
    def test_decrypt_corrupted_data(self):
        """Test decrypting corrupted encrypted data."""
        service = EncryptionService()
        
        encrypted = service.encrypt("test")
        # Corrupt the data
        corrupted = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(EncryptionError):
            service.decrypt(corrupted)
    
    def test_encrypt_bytes_input(self):
        """Test encrypting bytes input."""
        service = EncryptionService()
        
        original_bytes = b"byte-string"
        encrypted = service.encrypt(original_bytes)
        decrypted = service.decrypt(encrypted)
        
        # Should decrypt back to string
        assert decrypted == "byte-string"


@pytest.mark.integration
class TestEncryptionIntegration:
    """Integration tests for encryption with Django models."""
    
    def test_encrypt_model_field_workflow(self):
        """Test typical workflow of encrypting/decrypting model field."""
        # Simulate saving encrypted field
        api_key = "sk-test-1234567890"
        encrypted_key = encrypt_field(api_key)
        
        # Simulate retrieving from database
        retrieved_key = decrypt_field(encrypted_key)
        
        assert retrieved_key == api_key
    
    def test_batch_encrypt_decrypt_workflow(self):
        """Test encrypting multiple fields in batch."""
        service = EncryptionService()
        
        config_data = {
            'api_key': 'key-123',
            'api_secret': 'secret-456',
            'webhook_url': 'https://example.com/webhook',
            'name': 'My Config'
        }
        
        # Encrypt sensitive fields
        sensitive_fields = ['api_key', 'api_secret']
        encrypted = service.encrypt_dict(config_data, sensitive_fields)
        
        # Non-sensitive fields unchanged
        assert encrypted['webhook_url'] == config_data['webhook_url']
        assert encrypted['name'] == config_data['name']
        
        # Sensitive fields encrypted
        assert encrypted['api_key'] != config_data['api_key']
        assert encrypted['api_secret'] != config_data['api_secret']
        
        # Decrypt back
        decrypted = service.decrypt_dict(encrypted, sensitive_fields)
        assert decrypted == config_data
