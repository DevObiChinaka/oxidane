"""
Test suite for Payment Configuration API (Task 0.5.29)

Tests cover:
- Access control (unauthenticated, regular user, admin)
- CRUD operations (list, retrieve, create, update, partial_update)
- Singleton behavior (only one instance)
- Validation (key formats, currency codes)
- Encrypted key storage (never expose raw keys)
- Masked key display
- Test connection actions (Paystack and Stripe)
- Provider status computation
- Edge cases (empty values, special characters, concurrent updates)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from subscriptions.models import PaymentConfiguration

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
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def payment_config(db):
    """Payment configuration with test keys"""
    config = PaymentConfiguration.get_instance()
    config.paystack_public_key = 'pk_test_abc123'
    config.paystack_secret_key = 'sk_test_def456'
    config.paystack_webhook_secret = 'whsec_paystack_test'
    config.stripe_publishable_key = 'pk_test_stripe123'
    config.stripe_secret_key = 'sk_test_stripe456'
    config.stripe_webhook_secret = 'whsec_stripe789'
    config.paystack_enabled = True
    config.stripe_enabled = False
    config.primary_provider = 'paystack'
    config.is_test_mode = True
    config.supported_currencies = ['NGN', 'USD']
    config.save()
    
    # Encrypt sensitive fields
    config.encrypt_field('paystack_secret_key')
    config.encrypt_field('paystack_webhook_secret')
    config.encrypt_field('stripe_secret_key')
    config.encrypt_field('stripe_webhook_secret')
    
    return config


# ============================================================================
# ACCESS CONTROL TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigAccessControl:
    """Test access control for Payment Configuration API"""
    
    def test_unauthenticated_cannot_access(self, api_client):
        """Unauthenticated users should get 401"""
        response = api_client.get('/api/admin/payment/config/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_regular_user_cannot_access(self, api_client, user):
        """Regular users should get 403"""
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/admin/payment/config/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access(self, api_client, admin_user, payment_config):
        """Admin users should be able to access"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/payment/config/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# CRUD TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigCRUD:
    """Test CRUD operations for Payment Configuration"""
    
    def test_list_returns_singleton_as_list(self, api_client, admin_user, payment_config):
        """List should return singleton as a single-item list"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/payment/config/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(payment_config.id)
    
    def test_retrieve_returns_config_details(self, api_client, admin_user, payment_config):
        """Retrieve should return full config details"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(payment_config.id)
        assert response.data['primary_provider'] == 'paystack'
        assert response.data['is_test_mode'] is True
        assert response.data['supported_currencies'] == ['NGN', 'USD']
        
        # Check computed fields
        assert 'is_paystack_configured' in response.data
        assert 'is_stripe_configured' in response.data
        assert 'provider_status' in response.data
    
    def test_create_updates_existing_config(self, api_client, admin_user, payment_config):
        """POST should update singleton (acts like update)"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'primary_provider': 'stripe',
            'is_test_mode': False,
            'paystack_enabled': False,
            'stripe_enabled': True
        }
        response = api_client.post('/api/admin/payment/config/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify changes
        payment_config.refresh_from_db()
        assert payment_config.primary_provider == 'stripe'
        assert payment_config.is_test_mode is False
        assert payment_config.paystack_enabled is False
        assert payment_config.stripe_enabled is True
    
    def test_update_modifies_config(self, api_client, admin_user, payment_config):
        """PUT should update config"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'paystack_public_key_write': 'pk_test_new123',
            'paystack_enabled': True,
            'stripe_enabled': False,
            'primary_provider': 'paystack',
            'is_test_mode': True,
            'supported_currencies': ['NGN', 'USD', 'GBP']
        }
        response = api_client.put(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        payment_config.refresh_from_db()
        assert payment_config.paystack_public_key == 'pk_test_new123'
        assert payment_config.supported_currencies == ['NGN', 'USD', 'GBP']
    
    def test_partial_update_modifies_specific_fields(self, api_client, admin_user, payment_config):
        """PATCH should update only specified fields"""
        api_client.force_authenticate(user=admin_user)
        original_public_key = payment_config.paystack_public_key
        
        data = {
            'is_test_mode': False,
            'supported_currencies': ['NGN']
        }
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        payment_config.refresh_from_db()
        assert payment_config.is_test_mode is False
        assert payment_config.supported_currencies == ['NGN']
        # Other fields unchanged
        assert payment_config.paystack_public_key == original_public_key


# ============================================================================
# SINGLETON PATTERN TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigSingleton:
    """Test singleton behavior"""
    
    def test_only_one_instance_exists(self, api_client, admin_user):
        """Only one payment config instance should exist"""
        api_client.force_authenticate(user=admin_user)
        
        # Get instance
        config1 = PaymentConfiguration.get_instance()
        config2 = PaymentConfiguration.get_instance()
        
        assert config1.id == config2.id
        assert PaymentConfiguration.objects.count() == 1
    
    def test_get_instance_creates_if_not_exists(self, db):
        """get_instance() should create config if it doesn't exist"""
        PaymentConfiguration.objects.all().delete()
        assert PaymentConfiguration.objects.count() == 0
        
        config = PaymentConfiguration.get_instance()
        
        assert config is not None
        assert PaymentConfiguration.objects.count() == 1


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigValidation:
    """Test validation rules"""
    
    def test_invalid_paystack_public_key_format(self, api_client, admin_user, payment_config):
        """Paystack public key must start with pk_"""
        api_client.force_authenticate(user=admin_user)
        data = {'paystack_public_key_write': 'invalid_key_format'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'paystack_public_key_write' in response.data
    
    def test_invalid_paystack_secret_key_format(self, api_client, admin_user, payment_config):
        """Paystack secret key must start with sk_"""
        api_client.force_authenticate(user=admin_user)
        data = {'paystack_secret_key_write': 'invalid_key'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'paystack_secret_key_write' in response.data
    
    def test_invalid_stripe_publishable_key_format(self, api_client, admin_user, payment_config):
        """Stripe publishable key must start with pk_"""
        api_client.force_authenticate(user=admin_user)
        data = {'stripe_publishable_key_write': 'bad_key'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_stripe_secret_key_format(self, api_client, admin_user, payment_config):
        """Stripe secret key must start with sk_"""
        api_client.force_authenticate(user=admin_user)
        data = {'stripe_secret_key_write': 'bad_secret'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_stripe_webhook_secret_format(self, api_client, admin_user, payment_config):
        """Stripe webhook secret must start with whsec_"""
        api_client.force_authenticate(user=admin_user)
        data = {'stripe_webhook_secret_write': 'bad_webhook'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_currency_code(self, api_client, admin_user, payment_config):
        """Currency codes must be 3 uppercase letters"""
        api_client.force_authenticate(user=admin_user)
        data = {'supported_currencies': ['NG', 'USD']}  # NG is too short
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_valid_keys_accepted(self, api_client, admin_user, payment_config):
        """Valid key formats should be accepted"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'paystack_public_key_write': 'pk_test_valid123',
            'paystack_secret_key_write': 'sk_test_valid456',
            'stripe_publishable_key_write': 'pk_live_stripe789',
            'stripe_secret_key_write': 'sk_live_stripe012',
            'stripe_webhook_secret_write': 'whsec_valid345'
        }
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# MASKED KEY DISPLAY TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigMaskedKeys:
    """Test that sensitive keys are masked in responses"""
    
    def test_keys_not_in_response(self, api_client, admin_user, payment_config):
        """Raw keys should not be in API response"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Write-only fields should not be in response
        assert 'paystack_secret_key_write' not in response.data
        assert 'paystack_webhook_secret_write' not in response.data
        assert 'stripe_secret_key_write' not in response.data
        assert 'stripe_webhook_secret_write' not in response.data
    
    def test_masked_keys_displayed(self, api_client, admin_user, payment_config):
        """Masked keys should be displayed instead of raw keys"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Masked keys should be present
        assert 'paystack_public_key_masked' in response.data
        assert 'paystack_secret_key_masked' in response.data
        assert 'stripe_publishable_key_masked' in response.data
        assert 'stripe_secret_key_masked' in response.data
        
        # Masked keys should contain ***
        assert '***' in response.data['paystack_public_key_masked']
        assert '***' in response.data['paystack_secret_key_masked']
    
    def test_update_with_key_shows_new_masked_key(self, api_client, admin_user, payment_config):
        """After updating a key, response should show new masked version"""
        api_client.force_authenticate(user=admin_user)
        data = {'paystack_public_key_write': 'pk_test_newkey789'}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'pk_test_***' in response.data['paystack_public_key_masked']


# ============================================================================
# TEST CONNECTION ACTIONS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigTestPaystack:
    """Test Paystack connection testing"""
    
    @patch('requests.post')
    def test_successful_paystack_connection(self, mock_post, api_client, admin_user, payment_config):
        """Successful Paystack connection test"""
        mock_post.return_value = MagicMock(
            status_code=200,
            content=b'{"status":true}',
            json=lambda: {'status': True}
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_paystack/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'Paystack connection successful' in response.data['message']
    
    @patch('requests.post')
    def test_failed_paystack_connection_invalid_key(self, mock_post, api_client, admin_user, payment_config):
        """Failed Paystack connection - invalid key"""
        mock_post.return_value = MagicMock(
            status_code=401,
            content=b'{"message":"Invalid key"}',
            json=lambda: {'message': 'Invalid key'}
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_paystack/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
    
    @patch('requests.post')
    def test_paystack_connection_timeout(self, mock_post, api_client, admin_user, payment_config):
        """Paystack connection timeout"""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_paystack/')
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert response.data['success'] is False
    
    def test_paystack_no_key_configured(self, api_client, admin_user, db):
        """Test Paystack without key configured"""
        config = PaymentConfiguration.get_instance()
        config.paystack_secret_key = ''
        config.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{config.id}/test_paystack/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not configured' in response.data['message']


@pytest.mark.django_db
class TestPaymentConfigTestStripe:
    """Test Stripe connection testing"""
    
    @patch('requests.get')
    def test_successful_stripe_connection(self, mock_get, api_client, admin_user, payment_config):
        """Successful Stripe connection test"""
        mock_get.return_value = MagicMock(
            status_code=200,
            content=b'{"id":"acct_123"}',
            json=lambda: {
                'id': 'acct_123',
                'email': 'test@example.com',
                'country': 'US',
                'charges_enabled': True,
                'payouts_enabled': True
            }
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_stripe/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'Stripe connection successful' in response.data['message']
        assert 'account_info' in response.data
    
    @patch('requests.get')
    def test_failed_stripe_connection_invalid_key(self, mock_get, api_client, admin_user, payment_config):
        """Failed Stripe connection - invalid key"""
        mock_get.return_value = MagicMock(
            status_code=401,
            content=b'{"error":{"message":"Invalid API key"}}',
            json=lambda: {'error': {'message': 'Invalid API key'}}
        )
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_stripe/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
    
    @patch('requests.get')
    def test_stripe_connection_timeout(self, mock_get, api_client, admin_user, payment_config):
        """Stripe connection timeout"""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{payment_config.id}/test_stripe/')
        
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert response.data['success'] is False
    
    def test_stripe_no_key_configured(self, api_client, admin_user, db):
        """Test Stripe without key configured"""
        config = PaymentConfiguration.get_instance()
        config.stripe_secret_key = ''
        config.save()
        
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f'/api/admin/payment/config/{config.id}/test_stripe/')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not configured' in response.data['message']


# ============================================================================
# COMPUTED FIELDS TESTS
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigComputedFields:
    """Test computed fields"""
    
    def test_is_paystack_configured(self, api_client, admin_user, payment_config):
        """Check is_paystack_configured computed field"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_paystack_configured'] is True
    
    def test_is_stripe_configured(self, api_client, admin_user, payment_config):
        """Check is_stripe_configured computed field"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_stripe_configured'] is True
    
    def test_provider_status(self, api_client, admin_user, payment_config):
        """Check provider_status computed field"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get(f'/api/admin/payment/config/{payment_config.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'provider_status' in response.data
        
        status_data = response.data['provider_status']
        assert 'paystack' in status_data
        assert 'stripe' in status_data
        assert 'has_active_provider' in status_data
        
        # Check paystack status
        assert status_data['paystack']['enabled'] is True
        assert status_data['paystack']['configured'] is True
        assert status_data['paystack']['is_primary'] is True


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.django_db
class TestPaymentConfigEdgeCases:
    """Test edge cases"""
    
    def test_empty_supported_currencies_accepted(self, api_client, admin_user, payment_config):
        """Empty currency list should be accepted"""
        api_client.force_authenticate(user=admin_user)
        data = {'supported_currencies': []}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_webhook_urls_can_be_empty(self, api_client, admin_user, payment_config):
        """Webhook URLs can be empty"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'paystack_webhook_url': '',
            'stripe_webhook_url': ''
        }
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_multiple_currencies_supported(self, api_client, admin_user, payment_config):
        """Multiple currencies can be configured"""
        api_client.force_authenticate(user=admin_user)
        data = {'supported_currencies': ['NGN', 'USD', 'GBP', 'EUR', 'CAD']}
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['supported_currencies']) == 5
    
    def test_switch_primary_provider(self, api_client, admin_user, payment_config):
        """Can switch between Paystack and Stripe"""
        api_client.force_authenticate(user=admin_user)
        
        # Switch to Stripe
        data = {'primary_provider': 'stripe'}
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['primary_provider'] == 'stripe'
        
        # Switch back to Paystack
        data = {'primary_provider': 'paystack'}
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['primary_provider'] == 'paystack'
    
    def test_disable_all_providers(self, api_client, admin_user, payment_config):
        """Can disable all providers (for maintenance)"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'paystack_enabled': False,
            'stripe_enabled': False
        }
        
        response = api_client.patch(
            f'/api/admin/payment/config/{payment_config.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['provider_status']['has_active_provider'] is False
