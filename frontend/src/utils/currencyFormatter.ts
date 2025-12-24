/**
 * Currency Formatter Utility
 * Provides consistent currency formatting across the application
 */

/**
 * Format amount with currency symbol and proper decimal places
 * @param amount - Numeric amount to format
 * @param currencyCode - ISO 4217 currency code (e.g., USD, EUR, GBP, NGN)
 * @returns Formatted currency string (e.g., "$50.00", "€50.00")
 */
export function formatCurrency(amount: number, currencyCode: string = 'USD'): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode.toUpperCase(),
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Fallback for invalid currency codes
        return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  }
}

/**
 * Format amount with compact notation for large numbers
 * @param amount - Numeric amount to format
 * @param currencyCode - ISO 4217 currency code
 * @returns Compact formatted currency string (e.g., "$1.5K", "$2.3M")
 */
export function formatCurrencyCompact(amount: number, currencyCode: string = 'USD'): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode.toUpperCase(),
      notation: 'compact',
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount);
  } catch {
        return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(amount);
  }
}
