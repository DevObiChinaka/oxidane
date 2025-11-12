/**
 * Currency Conversion and Formatting Utilities
 * 
 * Provides:
 * - Currency formatting with proper symbols
 * - Client-side exchange rate estimation (fallback)
 * - Price display helpers
 */

export type Currency = 'USD' | 'NGN';

export const CURRENCY_CONFIG = {
  USD: {
    symbol: '$',
    name: 'US Dollar',
    code: 'USD',
    locale: 'en-US',
  },
  NGN: {
    symbol: '₦',
    name: 'Nigerian Naira',
    code: 'NGN',
    locale: 'en-NG',
  },
} as const;

/**
 * Format amount with proper currency symbol and formatting
 */
export function formatCurrency(
  amount: number,
  currency: Currency = 'USD',
  options: Intl.NumberFormatOptions = {}
): string {
  const config = CURRENCY_CONFIG[currency];
  
  return new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...options,
  }).format(amount);
}

/**
 * Format currency with rounding for approximations
 * NGN rounds to nearest 100, USD stays precise
 */
export function formatCurrencyApprox(
  amount: number,
  currency: Currency = 'USD'
): string {
  const config = CURRENCY_CONFIG[currency];
  
  // Round NGN to nearest 100 for cleaner approximations
  let displayAmount = amount;
  if (currency === 'NGN') {
    displayAmount = Math.round(amount / 100) * 100;
  }
  
  return new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.code,
    minimumFractionDigits: currency === 'NGN' ? 0 : 2,
    maximumFractionDigits: currency === 'NGN' ? 0 : 2,
  }).format(displayAmount);
}

/**
 * Get currency symbol
 */
export function getCurrencySymbol(currency: Currency): string {
  return CURRENCY_CONFIG[currency].symbol;
}

/**
 * Get currency name
 */
export function getCurrencyName(currency: Currency): string {
  return CURRENCY_CONFIG[currency].name;
}

/**
 * Parse currency string back to number
 * Example: "$99.99" -> 99.99
 */
export function parseCurrency(value: string): number | null {
  // Remove currency symbols and whitespace
  const cleaned = value.replace(/[₦$,\s]/g, '');
  const parsed = parseFloat(cleaned);
  
  return isNaN(parsed) ? null : parsed;
}

/**
 * Format compact currency (for large amounts)
 * Example: $1,500,000 -> $1.5M
 */
export function formatCompactCurrency(
  amount: number,
  currency: Currency = 'USD'
): string {
  const config = CURRENCY_CONFIG[currency];
  
  return new Intl.NumberFormat(config.locale, {
    style: 'currency',
    currency: config.code,
    notation: 'compact',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(amount);
}

/**
 * Detect user's preferred currency based on location/browser
 * Defaults to USD if detection fails
 */
export function detectUserCurrency(): Currency {
  // Try to detect from browser timezone/locale
  const locale = navigator.language || 'en-US';
  
  if (locale.toLowerCase().includes('ng') || locale.toLowerCase().includes('nigeria')) {
    return 'NGN';
  }
  
  // Default to USD
  return 'USD';
}

/**
 * Get currency from localStorage or detect
 */
export function getSavedCurrency(): Currency {
  if (typeof window === 'undefined') return 'USD';
  
  const saved = localStorage.getItem('preferred_currency') as Currency;
  if (saved && (saved === 'USD' || saved === 'NGN')) {
    return saved;
  }
  
  return detectUserCurrency();
}

/**
 * Save currency preference to localStorage
 */
export function saveCurrencyPreference(currency: Currency): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('preferred_currency', currency);
}

/**
 * Currency selector options for UI
 */
export const CURRENCY_OPTIONS = [
  {
    value: 'USD' as Currency,
    label: 'US Dollar ($)',
    symbol: '$',
    flag: '🇺🇸',
  },
  {
    value: 'NGN' as Currency,
    label: 'Nigerian Naira (₦)',
    symbol: '₦',
    flag: '🇳🇬',
  },
];
