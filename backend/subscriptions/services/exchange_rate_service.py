"""
Exchange Rate Service

Fetches currency exchange rates from external APIs and updates the ExchangeRate model.
This service is designed to be called by Celery tasks for automated updates.

Supported APIs:
- exchangerate-api.io (Free tier: 1,500 requests/month, no API key required)
- fixer.io (Requires API key, fallback option)

Usage:
    from subscriptions.services import ExchangeRateService
    
    service = ExchangeRateService()
    
    # Fetch and update all rates for USD
    success = service.fetch_and_update_rates()
    
    # Fetch rates for specific base currency
    success = service.fetch_and_update_rates(base_currency='EUR')
    
    # Get current rates from database
    rates = service.get_current_rates('USD')
"""

import logging
import time
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, List
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from subscriptions.models import ExchangeRate

logger = logging.getLogger(__name__)


class ExchangeRateServiceError(Exception):
    """Base exception for ExchangeRate service errors"""
    pass


class APIConnectionError(ExchangeRateServiceError):
    """Raised when API connection fails"""
    pass


class APIResponseError(ExchangeRateServiceError):
    """Raised when API returns invalid or error response"""
    pass


class ExchangeRateService:
    """
    Service for fetching and managing currency exchange rates.
    
    This service integrates with external exchange rate APIs to fetch
    current rates and stores them in the ExchangeRate model for use
    throughout the application.
    
    Attributes:
        DEFAULT_BASE_CURRENCY: Default base currency for rate fetching (USD)
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts for failed requests
        RETRY_DELAY: Delay between retries in seconds
    """
    
    # Configuration
    DEFAULT_BASE_CURRENCY = 'USD'
    DEFAULT_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # API Endpoints
    EXCHANGERATE_API_URL = "https://api.exchangerate-api.io/v4/latest/{currency}"
    FIXER_API_URL = "http://data.fixer.io/api/latest"
    
    def __init__(self, base_currency: str = None):
        """
        Initialize the exchange rate service.
        
        Args:
            base_currency: Base currency for fetching rates (defaults to USD)
        """
        self.base_currency = (base_currency or self.DEFAULT_BASE_CURRENCY).upper()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Oxidane-SaaS/1.0'
        })
    
    # ========================================================================
    # FETCH METHODS
    # ========================================================================
    
    def fetch_rates_from_exchangerate_api(
        self,
        base_currency: str = None
    ) -> Dict[str, Decimal]:
        """
        Fetch exchange rates from exchangerate-api.io (free tier).
        
        Args:
            base_currency: Base currency code (defaults to service default)
            
        Returns:
            Dictionary of {currency_code: rate}
            
        Raises:
            APIConnectionError: If connection to API fails
            APIResponseError: If API returns invalid response
        """
        base = (base_currency or self.base_currency).upper()
        url = self.EXCHANGERATE_API_URL.format(currency=base)
        
        try:
            logger.info(f"Fetching exchange rates for {base} from exchangerate-api.io")
            
            response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response structure
            if 'rates' not in data:
                raise APIResponseError(
                    f"Invalid API response: missing 'rates' key. Response: {data}"
                )
            
            # Convert rates to Decimal
            rates = {}
            for currency, rate in data['rates'].items():
                try:
                    # Handle None or invalid values
                    if rate is None:
                        logger.warning(f"Skipping null rate for {currency}")
                        continue
                    rates[currency.upper()] = Decimal(str(rate))
                except (ValueError, TypeError, InvalidOperation) as e:
                    logger.warning(
                        f"Skipping invalid rate for {currency}: {rate}. Error: {e}"
                    )
                    continue
            
            logger.info(f"Successfully fetched {len(rates)} exchange rates for {base}")
            return rates
            
        except requests.exceptions.Timeout:
            raise APIConnectionError(f"Timeout while fetching rates from {url}")
        
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Connection error: {e}")
        
        except requests.exceptions.HTTPError as e:
            raise APIResponseError(f"HTTP error {e.response.status_code}: {e}")
        
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Request failed: {e}")
        
        except ValueError as e:
            raise APIResponseError(f"Invalid JSON response: {e}")
    
    def fetch_rates_from_fixer(
        self,
        base_currency: str = None,
        api_key: str = None
    ) -> Dict[str, Decimal]:
        """
        Fetch exchange rates from fixer.io (requires API key).
        
        Note: Free tier of fixer.io only supports EUR as base currency.
        
        Args:
            base_currency: Base currency code (defaults to EUR for free tier)
            api_key: Fixer.io API key (can be set in settings.FIXER_API_KEY)
            
        Returns:
            Dictionary of {currency_code: rate}
            
        Raises:
            APIConnectionError: If connection to API fails
            APIResponseError: If API returns invalid response
            ValueError: If API key is not provided
        """
        api_key = api_key or getattr(settings, 'FIXER_API_KEY', None)
        if not api_key:
            raise ValueError("Fixer.io API key is required. Set FIXER_API_KEY in settings.")
        
        base = (base_currency or 'EUR').upper()  # Free tier only supports EUR
        
        params = {
            'access_key': api_key,
            'base': base
        }
        
        try:
            logger.info(f"Fetching exchange rates for {base} from fixer.io")
            
            response = self.session.get(
                self.FIXER_API_URL,
                params=params,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if not data.get('success', False):
                error_info = data.get('error', {})
                raise APIResponseError(
                    f"Fixer.io API error: {error_info.get('info', 'Unknown error')}"
                )
            
            # Validate response structure
            if 'rates' not in data:
                raise APIResponseError(
                    f"Invalid API response: missing 'rates' key. Response: {data}"
                )
            
            # Convert rates to Decimal
            rates = {}
            for currency, rate in data['rates'].items():
                try:
                    # Handle None or invalid values
                    if rate is None:
                        logger.warning(f"Skipping null rate for {currency}")
                        continue
                    rates[currency.upper()] = Decimal(str(rate))
                except (ValueError, TypeError, InvalidOperation) as e:
                    logger.warning(
                        f"Skipping invalid rate for {currency}: {rate}. Error: {e}"
                    )
                    continue
            
            logger.info(f"Successfully fetched {len(rates)} exchange rates for {base}")
            return rates
            
        except requests.exceptions.Timeout:
            raise APIConnectionError(f"Timeout while fetching rates from fixer.io")
        
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Connection error: {e}")
        
        except requests.exceptions.HTTPError as e:
            raise APIResponseError(f"HTTP error {e.response.status_code}: {e}")
        
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Request failed: {e}")
        
        except ValueError as e:
            raise APIResponseError(f"Invalid JSON response: {e}")
    
    def fetch_rates_with_retry(
        self,
        base_currency: str = None,
        use_fixer: bool = False,
        api_key: str = None
    ) -> Dict[str, Decimal]:
        """
        Fetch exchange rates with automatic retry on failure.
        
        Args:
            base_currency: Base currency code
            use_fixer: Use fixer.io instead of exchangerate-api.io
            api_key: API key for fixer.io (if using fixer)
            
        Returns:
            Dictionary of {currency_code: rate}
            
        Raises:
            ExchangeRateServiceError: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                if use_fixer:
                    return self.fetch_rates_from_fixer(base_currency, api_key)
                else:
                    return self.fetch_rates_from_exchangerate_api(base_currency)
            
            except ExchangeRateServiceError as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt}/{self.MAX_RETRIES} failed: {e}"
                )
                
                if attempt < self.MAX_RETRIES:
                    logger.info(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
        
        # All retries failed
        raise ExchangeRateServiceError(
            f"Failed to fetch rates after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )
    
    # ========================================================================
    # UPDATE METHODS
    # ========================================================================
    
    def update_rate(
        self,
        base_currency: str,
        target_currency: str,
        rate: Decimal
    ) -> ExchangeRate:
        """
        Update a single exchange rate in the database.
        
        Args:
            base_currency: Base currency code
            target_currency: Target currency code
            rate: Exchange rate value
            
        Returns:
            ExchangeRate object
            
        Raises:
            ValidationError: If rate is invalid
        """
        try:
            obj = ExchangeRate.update_rate(
                base_currency=base_currency.upper(),
                target_currency=target_currency.upper(),
                rate=rate
            )
            logger.debug(
                f"Updated rate: {base_currency}/{target_currency} = {rate}"
            )
            return obj
        
        except ValidationError as e:
            logger.error(
                f"Validation error updating rate {base_currency}/{target_currency}: {e}"
            )
            raise
    
    def bulk_update_rates(
        self,
        base_currency: str,
        rates_dict: Dict[str, Decimal]
    ) -> List[ExchangeRate]:
        """
        Bulk update exchange rates in the database.
        
        Args:
            base_currency: Base currency code
            rates_dict: Dictionary of {target_currency: rate}
            
        Returns:
            List of ExchangeRate objects
        """
        try:
            results = ExchangeRate.bulk_update_rates(
                base_currency=base_currency.upper(),
                rates_dict=rates_dict
            )
            logger.info(
                f"Bulk updated {len(results)} rates for {base_currency}"
            )
            return results
        
        except Exception as e:
            logger.error(f"Error bulk updating rates: {e}")
            raise
    
    def fetch_and_update_rates(
        self,
        base_currency: str = None,
        use_fixer: bool = False,
        api_key: str = None,
        force_update: bool = False
    ) -> bool:
        """
        Fetch rates from API and update database in one operation.
        
        This is the main method to be called by Celery tasks or management commands.
        
        Args:
            base_currency: Base currency code (defaults to USD)
            use_fixer: Use fixer.io instead of exchangerate-api.io
            api_key: API key for fixer.io (if using fixer)
            force_update: Update even if rates are not stale
            
        Returns:
            True if update successful, False otherwise
        """
        base = (base_currency or self.base_currency).upper()
        
        try:
            # Check if update is needed
            if not force_update and not ExchangeRate.needs_update(hours=24):
                logger.info("Exchange rates are up to date, skipping fetch")
                return True
            
            # Fetch rates from API
            logger.info(f"Fetching exchange rates for {base}...")
            rates = self.fetch_rates_with_retry(
                base_currency=base,
                use_fixer=use_fixer,
                api_key=api_key
            )
            
            if not rates:
                logger.warning("No rates fetched from API")
                return False
            
            # Update database
            logger.info(f"Updating {len(rates)} exchange rates in database...")
            self.bulk_update_rates(base, rates)
            
            logger.info(
                f"Successfully updated exchange rates for {base}. "
                f"Total rates: {len(rates)}"
            )
            return True
        
        except ExchangeRateServiceError as e:
            logger.error(f"Failed to fetch and update rates: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error updating rates: {e}", exc_info=True)
            return False
    
    # ========================================================================
    # QUERY METHODS
    # ========================================================================
    
    def get_current_rates(
        self,
        base_currency: str = None
    ) -> Dict[str, Decimal]:
        """
        Get current exchange rates from database for a base currency.
        
        Args:
            base_currency: Base currency code (defaults to service default)
            
        Returns:
            Dictionary of {target_currency: rate}
        """
        base = (base_currency or self.base_currency).upper()
        return ExchangeRate.get_all_rates_for_base(base)
    
    def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate as Decimal, or None if not found
        """
        return ExchangeRate.get_rate(from_currency, to_currency)
    
    def convert_amount(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        round_result: bool = False
    ) -> Optional[Decimal]:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            round_result: Whether to round to 2 decimal places
            
        Returns:
            Converted amount, or None if rate not found
        """
        return ExchangeRate.convert_amount(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            round_result=round_result
        )
    
    def get_supported_currencies(self) -> set:
        """
        Get list of all supported currencies.
        
        Returns:
            Set of currency codes
        """
        return ExchangeRate.get_supported_currencies()
    
    def is_currency_supported(self, currency_code: str) -> bool:
        """
        Check if a currency is supported.
        
        Args:
            currency_code: Currency code to check
            
        Returns:
            True if currency is supported
        """
        return ExchangeRate.is_supported(currency_code)
    
    def get_stale_rates(self, hours: int = 24) -> List[ExchangeRate]:
        """
        Get all rates that are older than specified hours.
        
        Args:
            hours: Number of hours before rate is considered stale
            
        Returns:
            List of stale ExchangeRate objects
        """
        return list(ExchangeRate.get_stale_rates(hours=hours))
    
    def needs_update(self, hours: int = 24) -> bool:
        """
        Check if exchange rates need updating.
        
        Args:
            hours: Number of hours before rate is considered stale
            
        Returns:
            True if no rates exist or any rates are stale
        """
        return ExchangeRate.needs_update(hours=hours)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_rate_age(self, base_currency: str, target_currency: str) -> Optional[timedelta]:
        """
        Get the age of a specific exchange rate.
        
        Args:
            base_currency: Base currency code
            target_currency: Target currency code
            
        Returns:
            Timedelta representing age, or None if rate doesn't exist
        """
        try:
            rate = ExchangeRate.objects.get(
                base_currency=base_currency.upper(),
                target_currency=target_currency.upper()
            )
            return timezone.now() - rate.last_updated
        
        except ExchangeRate.DoesNotExist:
            return None
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about stored exchange rates.
        
        Returns:
            Dictionary with statistics
        """
        rates = ExchangeRate.objects.all()
        
        if not rates.exists():
            return {
                'total_rates': 0,
                'base_currencies': [],
                'target_currencies': [],
                'supported_currencies': [],
                'oldest_rate': None,
                'newest_rate': None,
                'stale_rates_count': 0
            }
        
        base_currencies = set(rates.values_list('base_currency', flat=True))
        target_currencies = set(rates.values_list('target_currency', flat=True))
        all_currencies = base_currencies | target_currencies
        
        oldest = rates.order_by('last_updated').first()
        newest = rates.order_by('-last_updated').first()
        
        return {
            'total_rates': rates.count(),
            'base_currencies': sorted(list(base_currencies)),
            'target_currencies': sorted(list(target_currencies)),
            'supported_currencies': sorted(list(all_currencies)),
            'oldest_rate': {
                'pair': f"{oldest.base_currency}/{oldest.target_currency}",
                'age': timezone.now() - oldest.last_updated
            } if oldest else None,
            'newest_rate': {
                'pair': f"{newest.base_currency}/{newest.target_currency}",
                'age': timezone.now() - newest.last_updated
            } if newest else None,
            'stale_rates_count': ExchangeRate.get_stale_rates().count()
        }
    
    def __del__(self):
        """Close the requests session on cleanup"""
        if hasattr(self, 'session'):
            self.session.close()
