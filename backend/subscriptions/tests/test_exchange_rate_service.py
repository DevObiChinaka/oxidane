"""
Tests for ExchangeRateService

Tests cover:
- API integration (with mocked responses)
- Rate fetching and updating
- Error handling and retry logic
- Currency conversion
- Staleness detection
- Statistics and utilities
"""

from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
import json

import pytest
import requests
from django.utils import timezone
from django.core.exceptions import ValidationError

from subscriptions.models import ExchangeRate
from subscriptions.services import ExchangeRateService
from subscriptions.services.exchange_rate_service import (
    ExchangeRateServiceError,
    APIConnectionError,
    APIResponseError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def service():
    """Create ExchangeRateService instance"""
    return ExchangeRateService()


@pytest.fixture
def sample_api_response():
    """Sample API response from exchangerate-api.io"""
    return {
        'base': 'USD',
        'rates': {
            'EUR': 0.85,
            'GBP': 0.73,
            'NGN': 411.50,
            'JPY': 110.25,
            'CAD': 1.25
        },
        'date': '2025-11-04',
        'time_last_updated': 1699084800
    }


@pytest.fixture
def sample_fixer_response():
    """Sample API response from fixer.io"""
    return {
        'success': True,
        'timestamp': 1699084800,
        'base': 'EUR',
        'date': '2025-11-04',
        'rates': {
            'USD': 1.18,
            'GBP': 0.86,
            'NGN': 485.00,
            'JPY': 130.00,
            'CAD': 1.47
        }
    }


@pytest.fixture
def clear_exchange_rates(db):
    """Clear all exchange rates before test"""
    ExchangeRate.objects.all().delete()
    yield
    ExchangeRate.objects.all().delete()


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestServiceInitialization:
    """Test service initialization"""
    
    def test_default_initialization(self):
        """Test service initializes with default settings"""
        service = ExchangeRateService()
        
        assert service.base_currency == 'USD'
        assert service.DEFAULT_TIMEOUT == 10
        assert service.MAX_RETRIES == 3
        assert service.session is not None
    
    def test_custom_base_currency(self):
        """Test service initializes with custom base currency"""
        service = ExchangeRateService(base_currency='EUR')
        assert service.base_currency == 'EUR'
    
    def test_base_currency_normalized_to_uppercase(self):
        """Test base currency is normalized to uppercase"""
        service = ExchangeRateService(base_currency='gbp')
        assert service.base_currency == 'GBP'


# ============================================================================
# API FETCH TESTS (EXCHANGERATE-API.IO)
# ============================================================================

@pytest.mark.django_db
class TestExchangeRateAPIFetching:
    """Test fetching rates from exchangerate-api.io"""
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_success(self, mock_get, service, sample_api_response):
        """Test successful rate fetching"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        rates = service.fetch_rates_from_exchangerate_api('USD')
        
        assert len(rates) == 5
        assert rates['EUR'] == Decimal('0.85')
        assert rates['GBP'] == Decimal('0.73')
        assert rates['NGN'] == Decimal('411.50')
        assert all(isinstance(v, Decimal) for v in rates.values())
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_with_default_base(self, mock_get, service, sample_api_response):
        """Test fetching rates uses service default base currency"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        rates = service.fetch_rates_from_exchangerate_api()
        
        # Should use service's base_currency (USD)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'USD' in call_args[0][0]  # URL contains USD
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_missing_rates_key(self, mock_get, service):
        """Test handling of invalid API response (missing 'rates' key)"""
        mock_response = Mock()
        mock_response.json.return_value = {'base': 'USD', 'error': 'some error'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="missing 'rates' key"):
            service.fetch_rates_from_exchangerate_api('USD')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_invalid_rate_value(self, mock_get, service):
        """Test handling of invalid rate values (skips invalid, keeps valid)"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'base': 'USD',
            'rates': {
                'EUR': 0.85,
                'GBP': 'invalid',  # Invalid rate
                'NGN': 411.50
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        rates = service.fetch_rates_from_exchangerate_api('USD')
        
        # Should skip GBP but keep EUR and NGN
        assert len(rates) == 2
        assert 'EUR' in rates
        assert 'NGN' in rates
        assert 'GBP' not in rates
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_timeout(self, mock_get, service):
        """Test handling of API timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(APIConnectionError, match="Timeout"):
            service.fetch_rates_from_exchangerate_api('USD')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_connection_error(self, mock_get, service):
        """Test handling of connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")
        
        with pytest.raises(APIConnectionError, match="Connection error"):
            service.fetch_rates_from_exchangerate_api('USD')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_http_error(self, mock_get, service):
        """Test handling of HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="HTTP error 404"):
            service.fetch_rates_from_exchangerate_api('USD')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_invalid_json(self, mock_get, service):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="Invalid JSON"):
            service.fetch_rates_from_exchangerate_api('USD')


# ============================================================================
# API FETCH TESTS (FIXER.IO)
# ============================================================================

@pytest.mark.django_db
class TestFixerAPIFetching:
    """Test fetching rates from fixer.io"""
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_from_fixer_success(self, mock_get, service, sample_fixer_response):
        """Test successful rate fetching from fixer.io"""
        mock_response = Mock()
        mock_response.json.return_value = sample_fixer_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        rates = service.fetch_rates_from_fixer('EUR', api_key='test_key')
        
        assert len(rates) == 5
        assert rates['USD'] == Decimal('1.18')
        assert rates['GBP'] == Decimal('0.86')
    
    def test_fetch_from_fixer_no_api_key(self, service):
        """Test fixer.io requires API key"""
        with pytest.raises(ValueError, match="API key is required"):
            service.fetch_rates_from_fixer('EUR')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_from_fixer_api_error(self, mock_get, service):
        """Test handling of fixer.io API error response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': False,
            'error': {
                'code': 101,
                'info': 'Invalid API key'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with pytest.raises(APIResponseError, match="Invalid API key"):
            service.fetch_rates_from_fixer('EUR', api_key='invalid_key')


# ============================================================================
# RETRY LOGIC TESTS
# ============================================================================

@pytest.mark.django_db
class TestRetryLogic:
    """Test retry logic for failed requests"""
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    @patch('subscriptions.services.exchange_rate_service.time.sleep')  # Mock sleep to speed up tests
    def test_retry_success_after_failures(self, mock_sleep, mock_get, service, sample_api_response):
        """Test successful fetch after retries"""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.ConnectionError()
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = sample_api_response
        mock_response_success.raise_for_status = Mock()
        
        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectionError(),
            mock_response_success
        ]
        
        rates = service.fetch_rates_with_retry('USD')
        
        assert len(rates) == 5
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    @patch('subscriptions.services.exchange_rate_service.time.sleep')
    def test_retry_all_attempts_fail(self, mock_sleep, mock_get, service):
        """Test all retry attempts fail"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(ExchangeRateServiceError, match="Failed to fetch rates after 3 attempts"):
            service.fetch_rates_with_retry('USD')
        
        assert mock_get.call_count == 3  # MAX_RETRIES
        assert mock_sleep.call_count == 2  # Sleep between retries (not after last)


# ============================================================================
# UPDATE METHODS TESTS
# ============================================================================

@pytest.mark.django_db
class TestRateUpdateMethods:
    """Test rate update methods"""
    
    def test_update_single_rate(self, service, clear_exchange_rates):
        """Test updating a single exchange rate"""
        rate_obj = service.update_rate('USD', 'EUR', Decimal('0.85'))
        
        assert rate_obj.base_currency == 'USD'
        assert rate_obj.target_currency == 'EUR'
        assert rate_obj.rate == Decimal('0.85')
        
        # Verify in database
        db_rate = ExchangeRate.objects.get(
            base_currency='USD',
            target_currency='EUR'
        )
        assert db_rate.rate == Decimal('0.85')
    
    def test_update_rate_normalizes_currency_codes(self, service, clear_exchange_rates):
        """Test currency codes are normalized to uppercase"""
        rate_obj = service.update_rate('usd', 'eur', Decimal('0.85'))
        
        assert rate_obj.base_currency == 'USD'
        assert rate_obj.target_currency == 'EUR'
    
    def test_update_rate_overwrites_existing(self, service, clear_exchange_rates):
        """Test updating existing rate overwrites it"""
        # Create initial rate
        service.update_rate('USD', 'EUR', Decimal('0.85'))
        
        # Update with new rate
        rate_obj = service.update_rate('USD', 'EUR', Decimal('0.90'))
        
        assert rate_obj.rate == Decimal('0.90')
        
        # Verify only one record exists
        assert ExchangeRate.objects.filter(
            base_currency='USD',
            target_currency='EUR'
        ).count() == 1
    
    def test_bulk_update_rates(self, service, clear_exchange_rates):
        """Test bulk updating multiple rates"""
        rates_dict = {
            'EUR': Decimal('0.85'),
            'GBP': Decimal('0.73'),
            'NGN': Decimal('411.50')
        }
        
        results = service.bulk_update_rates('USD', rates_dict)
        
        assert len(results) == 3
        
        # Verify all rates in database
        for currency, rate in rates_dict.items():
            db_rate = ExchangeRate.objects.get(
                base_currency='USD',
                target_currency=currency
            )
            assert db_rate.rate == rate
    
    def test_bulk_update_overwrites_existing(self, service, clear_exchange_rates):
        """Test bulk update overwrites existing rates"""
        # Create initial rates
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.80')
        )
        
        # Bulk update with new rates
        rates_dict = {
            'EUR': Decimal('0.85'),  # Overwrites existing
            'GBP': Decimal('0.73')   # Creates new
        }
        
        service.bulk_update_rates('USD', rates_dict)
        
        # Verify EUR was updated
        eur_rate = ExchangeRate.objects.get(
            base_currency='USD',
            target_currency='EUR'
        )
        assert eur_rate.rate == Decimal('0.85')
        
        # Verify total count
        assert ExchangeRate.objects.filter(base_currency='USD').count() == 2


# ============================================================================
# FETCH AND UPDATE INTEGRATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestFetchAndUpdate:
    """Test the main fetch_and_update_rates method"""
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_success(self, mock_get, service, sample_api_response, clear_exchange_rates):
        """Test successful fetch and update"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        success = service.fetch_and_update_rates('USD')
        
        assert success is True
        
        # Verify rates in database
        assert ExchangeRate.objects.filter(base_currency='USD').count() == 5
        
        eur_rate = ExchangeRate.objects.get(
            base_currency='USD',
            target_currency='EUR'
        )
        assert eur_rate.rate == Decimal('0.85')
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_uses_default_base(self, mock_get, service, sample_api_response, clear_exchange_rates):
        """Test fetch and update uses service default base currency"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        success = service.fetch_and_update_rates()  # No base specified
        
        assert success is True
        assert ExchangeRate.objects.filter(base_currency='USD').exists()
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_skips_if_not_stale(self, mock_get, service, clear_exchange_rates):
        """Test fetch and update skips if rates are not stale"""
        # Create fresh rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        success = service.fetch_and_update_rates('USD', force_update=False)
        
        assert success is True
        # Should not have called API
        mock_get.assert_not_called()
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_force_update(self, mock_get, service, sample_api_response, clear_exchange_rates):
        """Test force_update bypasses staleness check"""
        # Create fresh rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        success = service.fetch_and_update_rates('USD', force_update=True)
        
        assert success is True
        # Should have called API even though rate is fresh
        mock_get.assert_called_once()
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_api_failure(self, mock_get, service, clear_exchange_rates):
        """Test fetch and update handles API failure gracefully"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        success = service.fetch_and_update_rates('USD')
        
        assert success is False
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_and_update_empty_response(self, mock_get, service, clear_exchange_rates):
        """Test fetch and update handles empty rates"""
        mock_response = Mock()
        mock_response.json.return_value = {'base': 'USD', 'rates': {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        success = service.fetch_and_update_rates('USD')
        
        assert success is False


# ============================================================================
# QUERY METHODS TESTS
# ============================================================================

@pytest.mark.django_db
class TestQueryMethods:
    """Test query methods"""
    
    def test_get_current_rates(self, service, clear_exchange_rates):
        """Test getting current rates for a base currency"""
        # Create test rates
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.73')
        )
        
        rates = service.get_current_rates('USD')
        
        assert len(rates) == 2
        assert rates['EUR'] == Decimal('0.85')
        assert rates['GBP'] == Decimal('0.73')
    
    def test_get_rate_between_currencies(self, service, clear_exchange_rates):
        """Test getting rate between two currencies"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        rate = service.get_rate('USD', 'EUR')
        assert rate == Decimal('0.85')
    
    def test_get_rate_nonexistent(self, service, clear_exchange_rates):
        """Test getting nonexistent rate returns None"""
        rate = service.get_rate('USD', 'XYZ')
        assert rate is None
    
    def test_convert_amount(self, service, clear_exchange_rates):
        """Test converting amount between currencies"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        result = service.convert_amount(
            Decimal('100'),
            'USD',
            'EUR'
        )
        
        assert result == Decimal('85.0')
    
    def test_convert_amount_with_rounding(self, service, clear_exchange_rates):
        """Test converting amount with rounding"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.8567')
        )
        
        result = service.convert_amount(
            Decimal('100'),
            'USD',
            'EUR',
            round_result=True
        )
        
        assert result == Decimal('85.67')
    
    def test_get_supported_currencies(self, service, clear_exchange_rates):
        """Test getting list of supported currencies"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.73')
        )
        ExchangeRate.objects.create(
            base_currency='EUR',
            target_currency='GBP',
            rate=Decimal('0.86')
        )
        
        currencies = service.get_supported_currencies()
        
        assert currencies == {'USD', 'EUR', 'GBP'}
    
    def test_is_currency_supported(self, service, clear_exchange_rates):
        """Test checking if currency is supported"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        assert service.is_currency_supported('USD') is True
        assert service.is_currency_supported('EUR') is True
        assert service.is_currency_supported('XYZ') is False


# ============================================================================
# STALENESS DETECTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestStalenessDetection:
    """Test staleness detection methods"""
    
    def test_get_stale_rates(self, service, clear_exchange_rates):
        """Test getting stale rates"""
        # Create old rate (25 hours ago)
        old_time = timezone.now() - timedelta(hours=25)
        old_rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        ExchangeRate.objects.filter(pk=old_rate.pk).update(last_updated=old_time)
        
        # Create fresh rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.73')
        )
        
        stale_rates = service.get_stale_rates(hours=24)
        
        assert len(stale_rates) == 1
        assert stale_rates[0].target_currency == 'EUR'
    
    def test_needs_update_no_rates(self, service, clear_exchange_rates):
        """Test needs_update returns True when no rates exist"""
        assert service.needs_update() is True
    
    def test_needs_update_stale_rates(self, service, clear_exchange_rates):
        """Test needs_update returns True when rates are stale"""
        old_time = timezone.now() - timedelta(hours=25)
        old_rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        ExchangeRate.objects.filter(pk=old_rate.pk).update(last_updated=old_time)
        
        assert service.needs_update(hours=24) is True
    
    def test_needs_update_fresh_rates(self, service, clear_exchange_rates):
        """Test needs_update returns False when rates are fresh"""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        assert service.needs_update(hours=24) is False
    
    def test_get_rate_age(self, service, clear_exchange_rates):
        """Test getting age of a specific rate"""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        
        age = service.get_rate_age('USD', 'EUR')
        
        assert isinstance(age, timedelta)
        assert age.total_seconds() < 10  # Should be very recent
    
    def test_get_rate_age_nonexistent(self, service, clear_exchange_rates):
        """Test getting age of nonexistent rate returns None"""
        age = service.get_rate_age('USD', 'XYZ')
        assert age is None


# ============================================================================
# STATISTICS TESTS
# ============================================================================

@pytest.mark.django_db
class TestStatistics:
    """Test statistics method"""
    
    def test_get_statistics_no_rates(self, service, clear_exchange_rates):
        """Test statistics with no rates"""
        stats = service.get_statistics()
        
        assert stats['total_rates'] == 0
        assert stats['base_currencies'] == []
        assert stats['supported_currencies'] == []
        assert stats['oldest_rate'] is None
        assert stats['newest_rate'] is None
    
    def test_get_statistics_with_rates(self, service, clear_exchange_rates):
        """Test statistics with rates"""
        # Create rates with different ages
        old_time = timezone.now() - timedelta(hours=48)
        
        old_rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.85')
        )
        ExchangeRate.objects.filter(pk=old_rate.pk).update(last_updated=old_time)
        
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.73')
        )
        ExchangeRate.objects.create(
            base_currency='EUR',
            target_currency='GBP',
            rate=Decimal('0.86')
        )
        
        stats = service.get_statistics()
        
        assert stats['total_rates'] == 3
        assert 'USD' in stats['base_currencies']
        assert 'EUR' in stats['base_currencies']
        assert set(stats['supported_currencies']) == {'USD', 'EUR', 'GBP'}
        assert stats['oldest_rate']['pair'] == 'USD/EUR'
        assert stats['newest_rate'] is not None
        assert stats['stale_rates_count'] == 1  # The old rate


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_service_cleanup_on_deletion(self, service):
        """Test service closes session on cleanup"""
        session = service.session
        del service
        
        # Session should be closed (this is hard to verify directly,
        # but we can at least ensure __del__ was called without errors)
    
    def test_update_rate_with_invalid_value(self, service, clear_exchange_rates):
        """Test updating rate with invalid value raises ValidationError"""
        with pytest.raises((ValidationError, ValueError)):
            service.update_rate('USD', 'EUR', Decimal('-0.85'))  # Negative rate
    
    def test_convert_amount_nonexistent_rate(self, service, clear_exchange_rates):
        """Test converting with nonexistent rate returns None"""
        result = service.convert_amount(
            Decimal('100'),
            'USD',
            'XYZ'
        )
        assert result is None
    
    def test_get_current_rates_empty(self, service, clear_exchange_rates):
        """Test getting rates for base with no rates returns empty dict"""
        rates = service.get_current_rates('USD')
        assert rates == {}
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_fetch_rates_with_partial_invalid_data(self, mock_get, service):
        """Test fetch handles partial invalid data gracefully"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'base': 'USD',
            'rates': {
                'EUR': 0.85,      # Valid
                'GBP': None,      # Invalid
                'NGN': 'text',    # Invalid
                'JPY': 110.25     # Valid
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        rates = service.fetch_rates_from_exchangerate_api('USD')
        
        # Should keep only valid rates
        assert len(rates) == 2
        assert 'EUR' in rates
        assert 'JPY' in rates
        assert 'GBP' not in rates
        assert 'NGN' not in rates


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestIntegration:
    """Test integration with ExchangeRate model"""
    
    @patch('subscriptions.services.exchange_rate_service.requests.Session.get')
    def test_full_workflow(self, mock_get, sample_api_response, clear_exchange_rates):
        """Test complete workflow: fetch, update, query, convert"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 1. Initialize service
        service = ExchangeRateService(base_currency='USD')
        
        # 2. Fetch and update rates
        success = service.fetch_and_update_rates()
        assert success is True
        
        # 3. Verify rates in database
        rates = service.get_current_rates('USD')
        assert len(rates) == 5
        assert rates['EUR'] == Decimal('0.85')
        
        # 4. Convert amount
        converted = service.convert_amount(
            Decimal('100'),
            'USD',
            'EUR',
            round_result=True
        )
        assert converted == Decimal('85.00')
        
        # 5. Check supported currencies
        currencies = service.get_supported_currencies()
        assert 'USD' in currencies
        assert 'EUR' in currencies
        
        # 6. Check staleness
        assert service.needs_update(hours=24) is False
