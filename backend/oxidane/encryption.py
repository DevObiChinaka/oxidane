"""
Encryption utilities for sensitive data storage.

This module provides Fernet-based symmetric encryption for sensitive fields
like API keys, tokens, passwords, and other secrets stored in the database.

Phase: 0.5.12
Author: Development Team
Created: November 2, 2025
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import base64
import os
import logging

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Base exception for encryption-related errors."""
    pass


class EncryptionKeyError(EncryptionError):
    """Exception raised when encryption key is invalid or missing."""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    
    Uses Fernet symmetric encryption (AES 128-bit in CBC mode with HMAC).
    Requires ENCRYPTION_KEY in Django settings.
    
    Example:
        >>> from oxidane.encryption import encryption_service
        >>> encrypted = encryption_service.encrypt("my-api-key")
        >>> decrypted = encryption_service.decrypt(encrypted)
        >>> assert decrypted == "my-api-key"
    """
    
    def __init__(self):
        """Initialize the encryption service with key from settings."""
        self._fernet = None
        self._initialize_key()
    
    def _initialize_key(self):
        """
        Initialize the Fernet cipher with key from settings.
        
        Raises:
            EncryptionKeyError: If ENCRYPTION_KEY is not set or invalid
        """
        encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
        
        if not encryption_key:
            raise EncryptionKeyError(
                "ENCRYPTION_KEY not found in settings. "
                "Generate one with: python manage.py generate_encryption_key"
            )
        
        try:
            # Ensure key is bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode('utf-8')
            
            self._fernet = Fernet(encryption_key)
            logger.debug("Encryption service initialized successfully")
            
        except Exception as e:
            raise EncryptionKeyError(
                f"Invalid ENCRYPTION_KEY in settings: {str(e)}. "
                "Generate a new one with: python manage.py generate_encryption_key"
            )
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            str: Base64-encoded encrypted string
            
        Raises:
            EncryptionError: If encryption fails
            
        Example:
            >>> encrypted = encryption_service.encrypt("secret-key")
            >>> print(encrypted)  # 'gAAAAA...'
        """
        if not plaintext:
            return ""
        
        try:
            # Convert to bytes if string
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            # Encrypt and return as string
            encrypted_bytes = self._fernet.encrypt(plaintext)
            return encrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: The encrypted string to decrypt
            
        Returns:
            str: Decrypted plaintext string
            
        Raises:
            EncryptionError: If decryption fails (wrong key, corrupted data)
            
        Example:
            >>> decrypted = encryption_service.decrypt('gAAAAA...')
            >>> print(decrypted)  # 'secret-key'
        """
        if not ciphertext:
            return ""
        
        try:
            # Convert to bytes if string
            if isinstance(ciphertext, str):
                ciphertext = ciphertext.encode('utf-8')
            
            # Decrypt and return as string
            decrypted_bytes = self._fernet.decrypt(ciphertext)
            return decrypted_bytes.decode('utf-8')
            
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or wrong key")
            raise EncryptionError(
                "Failed to decrypt data: Invalid token or encryption key changed. "
                "Data may be corrupted or encrypted with a different key."
            )
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data to encrypt
            fields: List of field names to encrypt
            
        Returns:
            dict: New dictionary with specified fields encrypted
            
        Example:
            >>> data = {'api_key': 'secret', 'name': 'Test'}
            >>> encrypted = encryption_service.encrypt_dict(data, ['api_key'])
            >>> encrypted['api_key']  # 'gAAAAA...'
            >>> encrypted['name']  # 'Test'
        """
        encrypted_data = data.copy()
        
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(encrypted_data[field])
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt
            
        Returns:
            dict: New dictionary with specified fields decrypted
            
        Example:
            >>> data = {'api_key': 'gAAAAA...', 'name': 'Test'}
            >>> decrypted = encryption_service.decrypt_dict(data, ['api_key'])
            >>> decrypted['api_key']  # 'secret'
            >>> decrypted['name']  # 'Test'
        """
        decrypted_data = data.copy()
        
        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except EncryptionError:
                    # If decryption fails, leave as-is (might be unencrypted legacy data)
                    logger.warning(f"Failed to decrypt field '{field}', leaving as-is")
        
        return decrypted_data
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            str: Base64-encoded encryption key
            
        Example:
            >>> key = EncryptionService.generate_key()
            >>> print(key)  # 'abcd1234...'
        """
        return Fernet.generate_key().decode('utf-8')
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be encrypted.
        
        Args:
            value: String to check
            
        Returns:
            bool: True if value looks like Fernet-encrypted data
            
        Note:
            This is a heuristic check based on Fernet token format.
            False positives are possible but unlikely.
        """
        if not value or not isinstance(value, str):
            return False
        
        # Fernet tokens start with 'gAAAAA' when base64-encoded
        # and have a minimum length
        if not value.startswith('gAAAAA') or len(value) < 60:
            return False
        
        # Try to decrypt - if it works, it's encrypted
        try:
            self.decrypt(value)
            return True
        except EncryptionError:
            return False


# Global singleton instance
encryption_service = EncryptionService()


# Convenience functions for common use cases
def encrypt_field(value: str) -> str:
    """
    Encrypt a single field value.
    
    Args:
        value: String to encrypt
        
    Returns:
        str: Encrypted string
    """
    return encryption_service.encrypt(value)


def decrypt_field(value: str) -> str:
    """
    Decrypt a single field value.
    
    Args:
        value: Encrypted string
        
    Returns:
        str: Decrypted string
    """
    return encryption_service.decrypt(value)


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.
    
    Returns:
        str: Base64-encoded encryption key
    """
    return EncryptionService.generate_key()
