/**
 * Example: Currency Conversion Hook Usage
 * 
 * This file demonstrates how to integrate the useCurrencyConverter hook
 * into your pricing components.
 */

import { useCurrencyConverter, useExchangeRates } from '@/hooks/useCurrencyConverter';
import { useState } from 'react';

// ============================================================================
// Example 1: Simple Pricing Card with Live Conversion
// ============================================================================

interface Plan {
  id: number;
  name: string;
  base_price: number;
  features: string[];
}

export function SimplePricingCard({ plan }: { plan: Plan }) {
  const [currency, setCurrency] = useState<'USD' | 'NGN'>('USD');
  
  // Fetch live conversion rate
  const { convert, loading, error, rate, cached } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: currency,
    autoFetch: true
  });

  // Convert price
  const displayPrice = currency === 'USD' ? plan.base_price : convert(plan.base_price);
  const currencySymbol = currency === 'USD' ? '$' : '₦';

  return (
    <div className="border rounded-lg p-6">
      {/* Currency Switcher */}
      <div className="mb-4">
        <select 
          value={currency}
          onChange={(e) => setCurrency(e.target.value as 'USD' | 'NGN')}
          className="border rounded px-3 py-1"
        >
          <option value="USD">USD ($)</option>
          <option value="NGN">NGN (₦)</option>
        </select>
      </div>

      {/* Plan Details */}
      <h3 className="text-xl font-bold">{plan.name}</h3>
      
      {/* Price Display */}
      <div className="my-4">
        {loading ? (
          <span className="text-gray-500">Updating prices...</span>
        ) : (
          <>
            <p className="text-3xl font-bold">
              {currencySymbol}{displayPrice.toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </p>
            {rate && currency !== 'USD' && (
              <small className="text-gray-600">
                Rate: 1 USD = ₦{rate.toFixed(2)} {cached && '(cached)'}
              </small>
            )}
          </>
        )}
      </div>

      {/* Error Handling */}
      {error && currency !== 'USD' && (
        <div className="text-sm text-yellow-600 mb-2">
          ⚠️ Showing USD prices (conversion unavailable)
        </div>
      )}

      {/* Features */}
      <ul className="space-y-2">
        {plan.features.map((feature, idx) => (
          <li key={idx} className="flex items-center">
            <span className="text-green-500 mr-2">✓</span>
            {feature}
          </li>
        ))}
      </ul>

      {/* Subscribe Button */}
      <button className="w-full mt-4 bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
        Subscribe Now
      </button>
    </div>
  );
}

// ============================================================================
// Example 2: Multi-Plan Pricing Page with Shared State
// ============================================================================

export function PricingPage() {
  const [currency, setCurrency] = useState<'USD' | 'NGN'>('USD');
  
  // Single hook for all plans (more efficient)
  const { convert, loading, error, rate, refresh, cached } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: currency,
    autoFetch: true
  });

  const plans: Plan[] = [
    {
      id: 1,
      name: 'Basic',
      base_price: 30,
      features: ['Feature 1', 'Feature 2', 'Feature 3']
    },
    {
      id: 2,
      name: 'Premium',
      base_price: 60,
      features: ['All Basic features', 'Feature 4', 'Feature 5']
    },
    {
      id: 3,
      name: 'VIP',
      base_price: 90,
      features: ['All Premium features', 'Feature 6', 'Priority support']
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header with Currency Selector */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
        
        {/* Currency Selector */}
        <div className="flex items-center justify-center gap-4">
          <label className="text-gray-700">Currency:</label>
          <select 
            value={currency}
            onChange={(e) => setCurrency(e.target.value as 'USD' | 'NGN')}
            className="border rounded-lg px-4 py-2 text-lg"
          >
            <option value="USD">🇺🇸 USD ($)</option>
            <option value="NGN">🇳🇬 NGN (₦)</option>
          </select>
          
          {/* Manual Refresh Button */}
          <button
            onClick={refresh}
            className="px-3 py-2 border rounded-lg hover:bg-gray-100"
            disabled={loading}
          >
            🔄 Refresh Rates
          </button>
        </div>

        {/* Rate Info */}
        {rate && currency !== 'USD' && !loading && (
          <p className="mt-2 text-sm text-gray-600">
            Exchange rate: 1 USD = {rate.toFixed(2)} {currency}
            {cached && ' (cached, updates hourly)'}
          </p>
        )}

        {/* Error Banner */}
        {error && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800">
              ⚠️ Currency conversion temporarily unavailable. Showing USD prices.
            </p>
          </div>
        )}
      </div>

      {/* Pricing Cards Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {plans.map(plan => {
          const displayPrice = currency === 'USD' ? plan.base_price : convert(plan.base_price);
          const currencySymbol = currency === 'USD' ? '$' : '₦';

          return (
            <div key={plan.id} className="border-2 rounded-lg p-6 hover:shadow-lg transition">
              <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
              
              {/* Price */}
              <div className="mb-6">
                {loading ? (
                  <div className="h-12 bg-gray-200 animate-pulse rounded"></div>
                ) : (
                  <p className="text-4xl font-bold">
                    {currencySymbol}{displayPrice.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </p>
                )}
                <p className="text-gray-600 text-sm mt-1">per month</p>
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <button className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition">
                Get Started
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// Example 3: All Exchange Rates Selector
// ============================================================================

export function CurrencyRatesTable() {
  const { rates, count, loading, error, lastUpdated } = useExchangeRates({
    baseCurrency: 'USD',
    autoFetch: true
  });

  if (loading) {
    return <div>Loading exchange rates...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <div className="border rounded-lg p-6">
      <h3 className="text-xl font-bold mb-4">
        Exchange Rates for USD ({count} currencies)
      </h3>
      
      {lastUpdated && (
        <p className="text-sm text-gray-600 mb-4">
          Last updated: {new Date(lastUpdated).toLocaleString()}
        </p>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {rates && Object.entries(rates).slice(0, 20).map(([currency, rate]) => (
          <div key={currency} className="border rounded p-3">
            <p className="font-bold">{currency}</p>
            <p className="text-gray-600">{rate.toFixed(4)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Example 4: Checkout Page with Live Conversion
// ============================================================================

export function CheckoutPage() {
  const [selectedPlan] = useState<Plan>({
    id: 1,
    name: 'Premium',
    base_price: 60,
    features: []
  });
  
  const [currency, setCurrency] = useState<'USD' | 'NGN'>('USD');
  
  const { convert, rate, loading } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: currency,
    autoFetch: true
  });

  const totalAmount = currency === 'USD' ? selectedPlan.base_price : convert(selectedPlan.base_price);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Checkout</h1>

      {/* Currency Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Payment Currency</label>
        <select 
          value={currency}
          onChange={(e) => setCurrency(e.target.value as 'USD' | 'NGN')}
          className="border rounded-lg px-4 py-2 w-full max-w-xs"
        >
          <option value="USD">USD (United States Dollar)</option>
          <option value="NGN">NGN (Nigerian Naira)</option>
        </select>
      </div>

      {/* Order Summary */}
      <div className="border rounded-lg p-6 max-w-md">
        <h2 className="text-xl font-bold mb-4">Order Summary</h2>
        
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Plan:</span>
            <span className="font-medium">{selectedPlan.name}</span>
          </div>
          
          <div className="flex justify-between">
            <span>Base Price:</span>
            <span>${selectedPlan.base_price}</span>
          </div>

          {currency !== 'USD' && rate && (
            <div className="flex justify-between text-sm text-gray-600">
              <span>Exchange Rate:</span>
              <span>1 USD = ₦{rate.toFixed(2)}</span>
            </div>
          )}

          <hr className="my-2" />

          <div className="flex justify-between text-lg font-bold">
            <span>Total:</span>
            {loading ? (
              <span className="text-gray-400">Calculating...</span>
            ) : (
              <span>
                {currency === 'USD' ? '$' : '₦'}
                {totalAmount.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </span>
            )}
          </div>
        </div>

        <button 
          className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Complete Payment'}
        </button>
      </div>
    </div>
  );
}
