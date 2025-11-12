'use client';

import { useState, useEffect } from 'react';
import { formatCurrency, type Currency } from '@/lib/utils/currency';
import { useCurrencyConverter } from '@/hooks/useCurrencyConverter';

interface Feature {
  id: string;
  key: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  sort_order: number;
}

interface PricingPlan {
  id: string;
  name: string;
  slug: string;
  description: string;
  billing_period: 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'lifetime';
  billing_period_display: string;
  is_featured: boolean;
  is_active: boolean;
  sort_order: number;
  price: number;
  base_price: number;
  currency: string;
  base_price_usd?: number;
  features: Feature[];
  limits: any;
}

interface PricingCardsProps {
  onPlanSelect?: (plan: PricingPlan) => void;
  selectedPlanId?: string;
  currency?: Currency;
}

export default function PricingCards({ 
  onPlanSelect, 
  selectedPlanId,
  currency = 'USD'
}: PricingCardsProps) {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Live currency conversion hook
  const { 
    convert, 
    loading: rateLoading, 
    error: rateError, 
    rate,
    cached 
  } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: currency,
    autoFetch: true
  });

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch plans in USD (base currency)
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/v1/subscriptions/plans/`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch pricing plans');
        }
        
        const data = await response.json();
        setPlans(data.results || data || []);
      } catch (err) {
        console.error('Error fetching plans:', err);
        setError(err instanceof Error ? err.message : 'Failed to load pricing plans');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []); // Remove currency dependency - we handle conversion client-side

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 animate-pulse">
            <div className="h-6 bg-white/20 rounded w-24 mb-3"></div>
            <div className="h-4 bg-white/20 rounded w-full mb-2"></div>
            <div className="h-4 bg-white/20 rounded w-3/4 mb-6"></div>
            <div className="h-10 bg-white/20 rounded w-32 mb-6"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((j) => (
                <div key={j} className="h-4 bg-white/20 rounded w-full"></div>
              ))}
            </div>
            <div className="h-11 bg-white/20 rounded-lg mt-6"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 px-4">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-50 rounded-full mb-4">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to Load Plans</h3>
        <p className="text-gray-600 mb-4 text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2.5 bg-[#00B38F] text-white rounded-lg hover:bg-[#00A87D] transition-colors text-sm font-medium"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="text-center py-12 px-4">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-50 rounded-full mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Plans Available</h3>
        <p className="text-gray-600 text-sm">Check back soon for pricing options</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
      {/* Rate Error Banner */}
      {rateError && currency !== 'USD' && (
        <div className="col-span-full mb-4 p-3 bg-yellow-50/10 border border-yellow-400/30 rounded-lg">
          <p className="text-sm text-yellow-200 text-center">
            ⚠️ Currency conversion temporarily unavailable. Showing USD prices.
          </p>
        </div>
      )}
      
      {/* Rate Info Banner */}
      {rate && currency !== 'USD' && !rateLoading && !rateError && (
        <div className="col-span-full mb-4 p-3 bg-white/5 border border-white/10 rounded-lg">
          <p className="text-sm text-gray-300 text-center">
            Exchange rate: 1 USD = {rate.toFixed(2)} {currency}
            {cached && <span className="text-gray-400 ml-2">(updates hourly)</span>}
          </p>
        </div>
      )}
      
      {plans.map((plan) => {
        // Calculate converted price using live rates
        const basePrice = plan.base_price || plan.price;
        const displayPrice = currency === 'USD' ? basePrice : convert(basePrice);
        
        return (
        <div
          key={plan.id}
          className={`relative bg-white/10 backdrop-blur-md rounded-xl border-2 transition-all duration-300 hover:shadow-lg hover:bg-white/15 ${
            plan.is_featured 
              ? 'border-[#00B38F]/50 shadow-md' 
              : 'border-white/20 hover:border-[#00B38F]/30'
          } ${selectedPlanId === plan.id ? 'ring-2 ring-[#00B38F] ring-offset-2 ring-offset-transparent' : ''}`}
        >
          <div className="p-6">
            {/* Plan Name */}
            <h3 className="text-lg font-bold text-white mb-1">{plan.name}</h3>
            <p className="text-sm text-gray-300 mb-6 min-h-[40px]">{plan.description}</p>

            {/* Price */}
            <div className="mb-6">
              {rateLoading && currency !== 'USD' ? (
                <div className="h-12 bg-white/10 animate-pulse rounded"></div>
              ) : (
                <>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-white">
                      {formatCurrency(displayPrice, currency).split('.')[0]}
                    </span>
                    {plan.billing_period !== 'lifetime' && (
                      <span className="text-sm text-gray-400">
                      /{plan.billing_period.replace('ly', '')}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>

          {/* CTA Button */}
          <button
            onClick={() => onPlanSelect?.(plan)}
            className="w-full py-2.5 px-4 rounded-lg font-semibold text-sm transition-all duration-200 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white hover:from-[#00A87D] hover:to-[#00A58D] shadow-sm"
          >
            {plan.billing_period === 'lifetime' ? 'Get Lifetime Access' : 'Get Started'}
          </button>            {/* Features */}
            <div className="mt-6 pt-6 border-t border-white/10">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
                What's included
              </p>
              <div className="space-y-3">
                {plan.features && plan.features.length > 0 ? (
                  plan.features
                    .sort((a, b) => a.sort_order - b.sort_order)
                    .slice(0, 6)
                    .map((feature) => (
                      <div key={feature.id} className="flex items-start gap-2.5">
                        <svg 
                          className="w-5 h-5 text-[#00B38F] flex-shrink-0 mt-0.5" 
                          fill="currentColor" 
                          viewBox="0 0 20 20"
                        >
                          <path 
                            fillRule="evenodd" 
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                        <span className="text-sm text-gray-200 leading-tight">
                          {feature.name}
                        </span>
                      </div>
                    ))
                ) : (
                  <div className="text-center text-gray-400 text-sm py-2">
                    Contact for details
                  </div>
                )}
                {plan.features && plan.features.length > 6 && (
                  <p className="text-xs text-gray-400 pl-7">
                    + {plan.features.length - 6} more features
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
        );
      })}
    </div>
  );
}