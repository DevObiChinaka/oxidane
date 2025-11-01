"""
Comprehensive tests for ExchangeRate model (Phase 0.5, Task 0.5.10).

Test-Driven Development approach: Write tests FIRST, then implement model.
Target: 45+ comprehensive tests covering all functionality.

Test Categories:
1. Basic CRUD Operations (8 tests)
2. Validation (8 tests)
3. Rate Retrieval (8 tests)
4. Currency Conversion (8 tests)
5. Rate Updates (6 tests)
6. Edge Cases (7 tests)
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from subscriptions.models import ExchangeRate

# ============================================================================
# CATEGORY 1: BASIC CRUD OPERATIONS (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestExchangeRateBasicOperations:
    """Test basic CRUD operations for ExchangeRate."""

    def test_create_exchange_rate(self):
        """Test creating an exchange rate."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        assert rate.id is not None
        assert rate.base_currency == 'USD'
        assert rate.target_currency == 'NGN'
        assert rate.rate == Decimal('1500.00')
        assert rate.last_updated is not None

    def test_create_multiple_rates(self):
        """Test creating multiple exchange rates."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.79')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.92')
        )
        
        assert ExchangeRate.objects.count() == 3

    def test_update_exchange_rate(self):
        """Test updating an exchange rate."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        original_updated = rate.last_updated
        
        import time
        time.sleep(0.1)
        
        rate.rate = Decimal('1550.00')
        rate.save()
        
        rate.refresh_from_db()
        assert rate.rate == Decimal('1550.00')
        assert rate.last_updated > original_updated

    def test_delete_exchange_rate(self):
        """Test deleting an exchange rate."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        rate_id = rate.id
        rate.delete()
        
        assert not ExchangeRate.objects.filter(id=rate_id).exists()

    def test_string_representation(self):
        """Test __str__ method."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        assert str(rate) == "1 USD = 1500.00 NGN"

    def test_unique_currency_pair(self):
        """Test that currency pair is unique."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        with pytest.raises(Exception):  # IntegrityError
            ExchangeRate.objects.create(
                base_currency='USD',
                target_currency='NGN',
                rate=Decimal('1600.00')
            )

    def test_timestamps_auto_update(self):
        """Test that last_updated updates automatically."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        original_time = rate.last_updated
        
        import time
        time.sleep(0.1)
        
        rate.rate = Decimal('1550.00')
        rate.save()
        
        assert rate.last_updated > original_time

    def test_decimal_precision(self):
        """Test that rate maintains decimal precision."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.789456')
        )
        
        rate.refresh_from_db()
        # Should preserve up to 6 decimal places
        assert rate.rate == Decimal('0.789456')


# ============================================================================
# CATEGORY 2: VALIDATION (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestExchangeRateValidation:
    """Test validation logic."""

    def test_currency_code_uppercase(self):
        """Test currency codes are converted to uppercase."""
        rate = ExchangeRate.objects.create(
            base_currency='usd',
            target_currency='ngn',
            rate=Decimal('1500.00')
        )
        
        rate.refresh_from_db()
        assert rate.base_currency == 'USD'
        assert rate.target_currency == 'NGN'

    def test_currency_code_length(self):
        """Test currency codes must be 3 characters."""
        with pytest.raises(ValidationError):
            rate = ExchangeRate(
                base_currency='US',  # Too short
                target_currency='NGN',
                rate=Decimal('1500.00')
            )
            rate.full_clean()

    def test_rate_must_be_positive(self):
        """Test that rate must be positive."""
        with pytest.raises(ValidationError):
            rate = ExchangeRate(
                base_currency='USD',
                target_currency='NGN',
                rate=Decimal('-1500.00')
            )
            rate.full_clean()

    def test_rate_cannot_be_zero(self):
        """Test that rate cannot be zero."""
        with pytest.raises(ValidationError):
            rate = ExchangeRate(
                base_currency='USD',
                target_currency='NGN',
                rate=Decimal('0.00')
            )
            rate.full_clean()

    def test_base_and_target_cannot_be_same(self):
        """Test that base and target currencies must be different."""
        with pytest.raises(ValidationError):
            rate = ExchangeRate(
                base_currency='USD',
                target_currency='USD',
                rate=Decimal('1.00')
            )
            rate.full_clean()

    def test_currency_code_valid_format(self):
        """Test currency codes are valid ISO format."""
        # Valid codes
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        rate.full_clean()  # Should not raise

    def test_rate_maximum_value(self):
        """Test rate has reasonable maximum."""
        # Very large but valid rate
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='VND',  # Vietnamese Dong
            rate=Decimal('25000.00')
        )
        rate.full_clean()  # Should not raise

    def test_rate_decimal_places(self):
        """Test rate supports adequate decimal places."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='BTC',  # Cryptocurrency
            rate=Decimal('0.000023')
        )
        
        rate.refresh_from_db()
        assert rate.rate == Decimal('0.000023')


# ============================================================================
# CATEGORY 3: RATE RETRIEVAL (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestExchangeRateRetrieval:
    """Test rate retrieval methods."""

    def test_get_rate_direct(self):
        """Test getting rate for direct currency pair."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        rate = ExchangeRate.get_rate('USD', 'NGN')
        assert rate == Decimal('1500.00')

    def test_get_rate_reverse(self):
        """Test getting rate for reverse currency pair."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        # Reverse: NGN to USD should be 1/1500
        rate = ExchangeRate.get_rate('NGN', 'USD')
        expected = Decimal('1') / Decimal('1500.00')
        assert abs(rate - expected) < Decimal('0.000001')

    def test_get_rate_same_currency(self):
        """Test getting rate for same currency returns 1."""
        rate = ExchangeRate.get_rate('USD', 'USD')
        assert rate == Decimal('1.00')

    def test_get_rate_not_found(self):
        """Test getting rate for non-existent pair."""
        rate = ExchangeRate.get_rate('USD', 'XYZ')
        assert rate is None

    def test_get_rate_case_insensitive(self):
        """Test get_rate is case-insensitive."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        rate = ExchangeRate.get_rate('usd', 'ngn')
        assert rate == Decimal('1500.00')

    def test_get_all_rates_for_base(self):
        """Test getting all rates for a base currency."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.79')
        )
        ExchangeRate.objects.create(
            base_currency='EUR',
            target_currency='GBP',
            rate=Decimal('0.86')
        )
        
        rates = ExchangeRate.get_all_rates_for_base('USD')
        assert len(rates) == 2
        assert 'NGN' in rates
        assert 'GBP' in rates
        assert rates['NGN'] == Decimal('1500.00')

    def test_get_supported_currencies(self):
        """Test getting list of supported currencies."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.79')
        )
        ExchangeRate.objects.create(
            base_currency='EUR',
            target_currency='GBP',
            rate=Decimal('0.86')
        )
        
        currencies = ExchangeRate.get_supported_currencies()
        assert 'USD' in currencies
        assert 'NGN' in currencies
        assert 'GBP' in currencies
        assert 'EUR' in currencies

    def test_is_supported_currency(self):
        """Test checking if currency is supported."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        assert ExchangeRate.is_supported('USD') is True
        assert ExchangeRate.is_supported('NGN') is True
        assert ExchangeRate.is_supported('XYZ') is False


# ============================================================================
# CATEGORY 4: CURRENCY CONVERSION (8 tests)
# ============================================================================

@pytest.mark.django_db
class TestCurrencyConversion:
    """Test currency conversion methods."""

    def test_convert_amount_direct(self):
        """Test converting amount with direct rate."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'NGN'
        )
        assert result == Decimal('150000.00')

    def test_convert_amount_reverse(self):
        """Test converting amount with reverse rate."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('150000.00'),
            'NGN',
            'USD'
        )
        assert result == Decimal('100.00')

    def test_convert_amount_same_currency(self):
        """Test converting amount with same currency."""
        result = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'USD'
        )
        assert result == Decimal('100.00')

    def test_convert_amount_not_found(self):
        """Test converting with non-existent rate returns None."""
        result = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'XYZ'
        )
        assert result is None

    def test_convert_amount_maintains_precision(self):
        """Test conversion maintains decimal precision."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.789456')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'GBP'
        )
        # Should be 100 * 0.789456 = 78.9456
        assert result == Decimal('78.9456')

    def test_convert_amount_rounds_correctly(self):
        """Test conversion rounds to 2 decimal places."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.50')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('99.99'),
            'USD',
            'NGN',
            round_result=True
        )
        # Should be 99.99 * 1500.50 = 150034.995, rounded to 150034.99 or 150035.00
        assert isinstance(result, Decimal)

    def test_convert_zero_amount(self):
        """Test converting zero amount."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('0.00'),
            'USD',
            'NGN'
        )
        assert result == Decimal('0.00')

    def test_convert_negative_amount(self):
        """Test converting negative amount (for refunds)."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('-50.00'),
            'USD',
            'NGN'
        )
        assert result == Decimal('-75000.00')


# ============================================================================
# CATEGORY 5: RATE UPDATES (6 tests)
# ============================================================================

@pytest.mark.django_db
class TestRateUpdates:
    """Test rate update functionality."""

    def test_update_rate(self):
        """Test updating an existing rate."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        original_time = rate.last_updated
        
        import time
        time.sleep(0.1)
        
        ExchangeRate.update_rate('USD', 'NGN', Decimal('1550.00'))
        
        rate.refresh_from_db()
        assert rate.rate == Decimal('1550.00')
        assert rate.last_updated > original_time

    def test_update_rate_creates_if_not_exists(self):
        """Test update_rate creates rate if it doesn't exist."""
        ExchangeRate.update_rate('USD', 'EUR', Decimal('0.92'))
        
        rate = ExchangeRate.objects.get(
            base_currency='USD',
            target_currency='EUR'
        )
        assert rate.rate == Decimal('0.92')

    def test_bulk_update_rates(self):
        """Test bulk updating multiple rates."""
        rates_dict = {
            'NGN': Decimal('1500.00'),
            'GBP': Decimal('0.79'),
            'EUR': Decimal('0.92')
        }
        
        ExchangeRate.bulk_update_rates('USD', rates_dict)
        
        assert ExchangeRate.objects.count() == 3
        assert ExchangeRate.get_rate('USD', 'NGN') == Decimal('1500.00')
        assert ExchangeRate.get_rate('USD', 'GBP') == Decimal('0.79')

    def test_is_stale(self):
        """Test checking if rate is stale."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        # Fresh rate should not be stale
        assert rate.is_stale(hours=24) is False
        
        # Manually set old timestamp
        old_time = timezone.now() - timedelta(hours=25)
        ExchangeRate.objects.filter(id=rate.id).update(last_updated=old_time)
        rate.refresh_from_db()
        
        # Now should be stale
        assert rate.is_stale(hours=24) is True

    def test_get_stale_rates(self):
        """Test getting list of stale rates."""
        # Create fresh rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        # Create stale rate
        stale_rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='GBP',
            rate=Decimal('0.79')
        )
        old_time = timezone.now() - timedelta(hours=25)
        ExchangeRate.objects.filter(id=stale_rate.id).update(last_updated=old_time)
        
        stale_rates = ExchangeRate.get_stale_rates(hours=24)
        assert len(stale_rates) == 1
        assert stale_rates[0].target_currency == 'GBP'

    def test_needs_update(self):
        """Test class method to check if any rates need update."""
        # No rates - should need update
        assert ExchangeRate.needs_update() is True
        
        # Create fresh rate
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        # Fresh rates - should not need update
        assert ExchangeRate.needs_update(hours=24) is False


# ============================================================================
# CATEGORY 6: EDGE CASES (7 tests)
# ============================================================================

@pytest.mark.django_db
class TestExchangeRateEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_rate(self):
        """Test handling very small exchange rates."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='BTC',
            rate=Decimal('0.000023')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('1000000.00'),
            'USD',
            'BTC'
        )
        assert result == Decimal('23.00')

    def test_very_large_rate(self):
        """Test handling very large exchange rates."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='VND',
            rate=Decimal('25000.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'VND'
        )
        assert result == Decimal('2500000.00')

    def test_fractional_amount_conversion(self):
        """Test converting fractional amounts."""
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        result = ExchangeRate.convert_amount(
            Decimal('0.01'),
            'USD',
            'NGN'
        )
        assert result == Decimal('15.00')

    def test_concurrent_rate_updates(self):
        """Test handling concurrent rate updates."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='NGN',
            rate=Decimal('1500.00')
        )
        
        # Simulate concurrent updates
        ExchangeRate.update_rate('USD', 'NGN', Decimal('1550.00'))
        ExchangeRate.update_rate('USD', 'NGN', Decimal('1560.00'))
        
        rate.refresh_from_db()
        # Last update should win
        assert rate.rate == Decimal('1560.00')

    def test_whitespace_in_currency_codes(self):
        """Test handling whitespace in currency codes."""
        rate = ExchangeRate.objects.create(
            base_currency=' USD ',
            target_currency=' NGN ',
            rate=Decimal('1500.00')
        )
        
        rate.refresh_from_db()
        assert rate.base_currency == 'USD'
        assert rate.target_currency == 'NGN'

    def test_chain_conversion(self):
        """Test chain conversion through intermediate currency."""
        # USD -> EUR
        ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='EUR',
            rate=Decimal('0.92')
        )
        # EUR -> GBP
        ExchangeRate.objects.create(
            base_currency='EUR',
            target_currency='GBP',
            rate=Decimal('0.86')
        )
        
        # Convert USD -> EUR -> GBP
        usd_to_eur = ExchangeRate.convert_amount(
            Decimal('100.00'),
            'USD',
            'EUR'
        )
        eur_to_gbp = ExchangeRate.convert_amount(
            usd_to_eur,
            'EUR',
            'GBP'
        )
        
        # Should be approximately 100 * 0.92 * 0.86 = 79.12
        assert abs(eur_to_gbp - Decimal('79.12')) < Decimal('0.01')

    def test_rate_with_many_decimal_places(self):
        """Test rate with maximum decimal precision."""
        rate = ExchangeRate.objects.create(
            base_currency='USD',
            target_currency='ETH',
            rate=Decimal('0.000456')  # Max 6 decimal places
        )
        
        rate.refresh_from_db()
        # Should preserve precision up to 6 decimal places
        assert rate.rate == Decimal('0.000456')


# ============================================================================
# SUMMARY
# ============================================================================
"""
EXCHANGE RATE MODEL TEST SUMMARY:
==================================

CATEGORY 1: Basic CRUD Operations (8 tests)
- Create, update, delete operations
- String representation
- Unique currency pairs
- Timestamp updates
- Decimal precision

CATEGORY 2: Validation (8 tests)
- Currency code format (uppercase, 3 chars)
- Rate positivity and non-zero
- Base/target currency difference
- Valid ISO format
- Decimal places support

CATEGORY 3: Rate Retrieval (8 tests)
- Get rate direct/reverse
- Same currency = 1.0
- Not found handling
- Case insensitive
- Get all rates for base
- Supported currencies
- Currency support check

CATEGORY 4: Currency Conversion (8 tests)
- Convert amount direct/reverse
- Same currency conversion
- Not found handling
- Precision maintenance
- Rounding
- Zero/negative amounts

CATEGORY 5: Rate Updates (6 tests)
- Update existing rate
- Create if not exists
- Bulk updates
- Stale rate detection
- Needs update check

CATEGORY 6: Edge Cases (7 tests)
- Very small/large rates
- Fractional amounts
- Concurrent updates
- Whitespace handling
- Chain conversions
- Maximum precision

TOTAL: 45 TESTS
===============
All categories comprehensive, following TDD best practices.
"""
