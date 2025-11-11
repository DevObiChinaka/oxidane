import { useState, useEffect, useCallback } from 'react';

// API_URL already includes /api (e.g., 'http://localhost:8000/api')
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface CurrencyConversionResponse {
  success: boolean;
  from_currency: string;
  to_currency: string;
  from_amount: number;
  to_amount: number;
  exchange_rate: number;
  last_updated: string;
  cached: boolean;
  error?: string;
  error_code?: string;
}

export interface ExchangeRatesResponse {
  success: boolean;
  base_currency: string;
  rates: Record<string, number>;
  count: number;
  last_updated: string;
  error?: string;
  error_code?: string;
}

export interface UseCurrencyConverterOptions {
  fromCurrency?: string;
  toCurrency?: string;
  autoFetch?: boolean;
}

export interface UseCurrencyConverterResult {
  rate: number | null;
  loading: boolean;
  error: string | null;
  convert: (amount: number) => number;
  refresh: () => Promise<void>;
  lastUpdated: string | null;
  cached: boolean;
}

/**
 * React hook for live currency conversion with smart caching
 * 
 * Features:
 * - Auto-fetches rates on mount (configurable)
 * - 1-hour backend cache for performance
 * - Fallback to USD on errors
 * - Manual refresh capability
 * 
 * @example
 * ```tsx
 * const { rate, convert, loading, error } = useCurrencyConverter({
 *   fromCurrency: 'USD',
 *   toCurrency: 'NGN'
 * });
 * 
 * const price = convert(30); // Converts $30 USD to NGN
 * ```
 */
export function useCurrencyConverter({
  fromCurrency = 'USD',
  toCurrency = 'NGN',
  autoFetch = true,
}: UseCurrencyConverterOptions = {}): UseCurrencyConverterResult {
  const [rate, setRate] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [cached, setCached] = useState(false);

  /**
   * Fetch exchange rate from backend API
   */
  const fetchRate = useCallback(async () => {
    // Same currency conversion
    if (fromCurrency === toCurrency) {
      setRate(1.0);
      setError(null);
      setLoading(false);
      setLastUpdated(new Date().toISOString());
      setCached(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/v1/currency/convert/?from=${fromCurrency}&to=${toCurrency}&amount=1`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: CurrencyConversionResponse = await response.json();

      if (data.success) {
        setRate(data.exchange_rate);
        setLastUpdated(data.last_updated);
        setCached(data.cached);
        setError(null);
      } else {
        // API returned error (e.g., rate not available)
        throw new Error(data.error || 'Conversion failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch exchange rate';
      setError(errorMessage);
      setRate(null);
      
      // Fallback: If converting from USD, set rate to null (will return original amount)
      // If converting to USD, we can't provide a fallback
      console.warn(`Currency conversion failed (${fromCurrency}→${toCurrency}):`, errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fromCurrency, toCurrency]);

  /**
   * Manual refresh function
   */
  const refresh = useCallback(async () => {
    await fetchRate();
  }, [fetchRate]);

  /**
   * Convert amount using current rate
   * Returns original amount if rate is unavailable
   */
  const convert = useCallback(
    (amount: number): number => {
      if (rate === null) {
        console.warn(`No exchange rate available for ${fromCurrency}→${toCurrency}, returning original amount`);
        return amount;
      }
      return amount * rate;
    },
    [rate, fromCurrency, toCurrency]
  );

  // Auto-fetch on mount or when currencies change
  useEffect(() => {
    if (autoFetch) {
      fetchRate();
    }
  }, [autoFetch, fetchRate]);

  return {
    rate,
    loading,
    error,
    convert,
    refresh,
    lastUpdated,
    cached,
  };
}

/**
 * Hook to fetch all exchange rates for a base currency
 * Useful for currency selector dropdowns or rate tables
 * 
 * @example
 * ```tsx
 * const { rates, loading, error } = useExchangeRates({ baseCurrency: 'USD' });
 * ```
 */
export function useExchangeRates({
  baseCurrency = 'USD',
  autoFetch = true,
}: {
  baseCurrency?: string;
  autoFetch?: boolean;
} = {}) {
  const [rates, setRates] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [count, setCount] = useState(0);

  const fetchRates = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/v1/currency/rates/?base=${baseCurrency}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ExchangeRatesResponse = await response.json();

      if (data.success) {
        setRates(data.rates);
        setCount(data.count);
        setLastUpdated(data.last_updated);
        setError(null);
      } else {
        throw new Error(data.error || 'Failed to fetch rates');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch exchange rates';
      setError(errorMessage);
      setRates(null);
      console.error(`Failed to fetch rates for ${baseCurrency}:`, errorMessage);
    } finally {
      setLoading(false);
    }
  }, [baseCurrency]);

  const refresh = useCallback(async () => {
    await fetchRates();
  }, [fetchRates]);

  useEffect(() => {
    if (autoFetch) {
      fetchRates();
    }
  }, [autoFetch, fetchRates]);

  return {
    rates,
    count,
    loading,
    error,
    refresh,
    lastUpdated,
  };
}
