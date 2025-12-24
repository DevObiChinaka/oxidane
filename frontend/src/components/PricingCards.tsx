'use client';

import { useState, useEffect } from 'react';
import { formatCurrency, type Currency } from '@/lib/utils/currency';
import { useCurrencyConverter } from '@/hooks/useCurrencyConverter';
import { checkSubscriptionConflict, type CheckConflictResponse } from '@/lib/api/payment';
import { API_ENDPOINTS } from '@/config/api';

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
  isAuthenticated?: boolean;
}

export default function PricingCards({ 
  onPlanSelect, 
  selectedPlanId,
  currency = 'USD',
  isAuthenticated = false
}: PricingCardsProps) {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conflictData, setConflictData] = useState<Map<string, CheckConflictResponse>>(new Map());
  const [conflictLoading, setConflictLoading] = useState(false);
  const [conflictError, setConflictError] = useState<string | null>(null);
  
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
        const response = await fetch(API_ENDPOINTS.user.subscriptionPlans);
        
        if (!response.ok) {
          throw new Error('Failed to fetch pricing plans');
        }
        
        const data = await response.json();
        setPlans(data.results || data || []);
      } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load pricing plans');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []); // Remove currency dependency - we handle conversion client-side

  // Check for subscription conflicts when plans are loaded
  useEffect(() => {
    const checkConflicts = async () => {
      if (!isAuthenticated || plans.length === 0) {
        return;
      }

      try {
        setConflictLoading(true);
        setConflictError(null);

        // Check all plans in parallel
        const conflictChecks = plans.map(async (plan) => {
          try {
            const result = await checkSubscriptionConflict(plan.id);
            return { planId: plan.id, result };
          } catch (err) {
                        return { planId: plan.id, result: null };
          }
        });

        const results = await Promise.all(conflictChecks);
        
        // Build conflict map
        const newConflictData = new Map<string, CheckConflictResponse>();
        results.forEach(({ planId, result }) => {
          if (result) {
            newConflictData.set(planId, result);
          }
        });
        
        setConflictData(newConflictData);
      } catch (err) {
                setConflictError('Unable to check subscription status');
      } finally {
        setConflictLoading(false);
      }
    };

    checkConflicts();
  }, [plans, isAuthenticated]);

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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 lg:gap-6 max-w-6xl mx-auto">
      {/* Conflict Error Banner */}
      {conflictError && (
        <div className="col-span-full mb-3 sm:mb-4 p-2.5 sm:p-3 bg-yellow-50/10 border border-yellow-400/30 rounded-lg">
          <p className="text-xs sm:text-sm text-yellow-200 text-center">
            ⚠️ {conflictError}. You can still browse plans.
          </p>
        </div>
      )}
      
      {/* Rate Error Banner */}
      {rateError && currency !== 'USD' && (
        <div className="col-span-full mb-3 sm:mb-4 p-2.5 sm:p-3 bg-yellow-50/10 border border-yellow-400/30 rounded-lg">
          <p className="text-xs sm:text-sm text-yellow-200 text-center">
            ⚠️ Currency conversion temporarily unavailable. Showing USD prices.
          </p>
        </div>
      )}
      
      {/* Rate Info Banner */}
      {rate && currency !== 'USD' && !rateLoading && !rateError && (
        <div className="col-span-full mb-3 sm:mb-4 p-2.5 sm:p-3 bg-white/5 border border-white/10 rounded-lg">
          <p className="text-xs sm:text-sm text-gray-300 text-center break-words">
            Exchange rate: 1 USD = {rate.toFixed(2)} {currency}
            {cached && <span className="text-gray-400 ml-2">(updates hourly)</span>}
          </p>
        </div>
      )}
      
      {plans.map((plan) => {
        // Calculate converted price using live rates
        const basePrice = plan.base_price || plan.price;
        const displayPrice = currency === 'USD' ? basePrice : convert(basePrice);
        
        // Get conflict information for this plan
        const conflict = conflictData.get(plan.id);
        const isCurrentPlan = conflict?.existing_subscription?.plan_id === plan.id;
        
        // Only block recurring plans if user has active recurring subscription
        const isRecurringPlan = ['weekly', 'monthly', 'quarterly', 'yearly'].includes(plan.billing_period);
        const hasRecurringConflict = isRecurringPlan && conflict?.conflict === true;
        const canPurchase = conflict?.can_purchase !== false; // Default to true if no data
        
        return (
        <div
          key={plan.id}
          className={`relative bg-white/10 backdrop-blur-md rounded-xl border-2 transition-all duration-300 ${
            isCurrentPlan
              ? 'border-[#00B38F] shadow-lg'
              : hasRecurringConflict
              ? 'border-yellow-400/30 opacity-75'
              : plan.is_featured 
              ? 'border-[#00B38F]/50 shadow-md hover:shadow-lg hover:bg-white/15' 
              : 'border-white/20 hover:border-[#00B38F]/30 hover:shadow-lg hover:bg-white/15'
          } ${selectedPlanId === plan.id ? 'ring-2 ring-[#00B38F] ring-offset-2 ring-offset-transparent' : ''}`}
        >
          {/* Current Plan Badge */}
          {isCurrentPlan && (
            <div className="absolute -top-2.5 sm:-top-3 left-1/2 -translate-x-1/2 px-3 sm:px-4 py-0.5 sm:py-1 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white text-xs font-semibold rounded-full shadow-md z-10">
              ✓ Current Plan
            </div>
          )}
          
          {/* Conflict Warning Banner - Only for recurring plans */}
          {hasRecurringConflict && !isCurrentPlan && conflict?.existing_subscription && (
            <div className="absolute top-0 left-0 right-0 bg-yellow-50/95 backdrop-blur-sm border-b border-yellow-200 rounded-t-xl p-2.5 sm:p-3 z-10">
              <p className="text-xs leading-tight text-yellow-900">
                ⚠️ You have an active {conflict.existing_subscription.billing_period_display.toLowerCase()} subscription ({conflict.existing_subscription.plan_name}).
                Please wait until it expires before purchasing another recurring plan.
                {conflict.existing_subscription.end_date && (
                  <span className="font-medium block sm:inline sm:ml-1 mt-1 sm:mt-0">Expires: {new Date(conflict.existing_subscription.end_date).toLocaleDateString()}</span>
                )}
              </p>
            </div>
          )}
          
          <div className={`p-4 sm:p-5 lg:p-6 ${hasRecurringConflict && !isCurrentPlan ? 'pt-14 sm:pt-16' : ''}`}>
            {/* Plan Name */}
            <h3 className="text-base sm:text-lg font-bold text-white mb-1">{plan.name}</h3>
            <p className="text-xs sm:text-sm text-gray-300 mb-4 sm:mb-6 min-h-[32px] sm:min-h-[40px] line-clamp-2">{plan.description}</p>

            {/* Price */}
            <div className="mb-4 sm:mb-6">
              {rateLoading && currency !== 'USD' ? (
                <div className="h-10 sm:h-12 bg-white/10 animate-pulse rounded"></div>
              ) : (
                <>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl sm:text-3xl font-bold text-white">
                      {formatCurrency(displayPrice, currency).split('.')[0]}
                    </span>
                    {plan.billing_period !== 'lifetime' && (
                      <span className="text-xs sm:text-sm text-gray-400">
                      /{plan.billing_period.replace('ly', '')}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>

          {/* CTA Button */}
          {isCurrentPlan ? (
            <div className="space-y-2">
              <button
                disabled
                className="w-full py-2 sm:py-2.5 px-3 sm:px-4 rounded-lg font-semibold text-xs sm:text-sm bg-gray-100 text-gray-700 cursor-not-allowed"
              >
                Active Plan
              </button>
              <a
                href="/subscriptions"
                className="block w-full py-1.5 sm:py-2 text-center text-[#00B38F] hover:text-[#00A87D] text-xs sm:text-sm font-medium transition-colors"
              >
                Manage Subscription →
              </a>
            </div>
          ) : hasRecurringConflict ? (
            <div className="relative group">
              <button
                disabled
                className="w-full py-2 sm:py-2.5 px-3 sm:px-4 rounded-lg font-semibold text-xs sm:text-sm bg-gray-200 text-gray-500 cursor-not-allowed opacity-60"
              >
                Not Available
              </button>
              {/* Tooltip */}
              <div className="absolute bottom-full left-0 right-0 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 shadow-lg">
                <p className="text-center">
                  You have an active subscription. Please wait until it expires to purchase this plan.
                </p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
              </div>
            </div>
          ) : (
            <>
              <button
                onClick={() => onPlanSelect?.(plan)}
                className="w-full py-2 sm:py-2.5 px-3 sm:px-4 rounded-lg font-semibold text-xs sm:text-sm transition-all duration-200 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white hover:from-[#00A87D] hover:to-[#00A58D] shadow-sm"
              >
                {plan.billing_period === 'lifetime' ? 'Get Lifetime Access' : 'Get Started'}
              </button>
              
              {/* Lifetime Plan Info when user has recurring subscription */}
              {plan.billing_period === 'lifetime' && conflict?.existing_subscription && !hasRecurringConflict && (
                <div className="mt-2.5 sm:mt-3 bg-blue-50/10 border border-blue-400/30 rounded-lg p-2">
                  <p className="text-xs leading-tight text-blue-200">
                    💡 Lifetime access works alongside your {conflict.existing_subscription.billing_period_display.toLowerCase()} subscription
                  </p>
                </div>
              )}
            </>
          )}
          
            {/* Features */}
            <div className="mt-4 sm:mt-5 lg:mt-6 pt-4 sm:pt-5 lg:pt-6 border-t border-white/10">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3 sm:mb-4">
                What's included
              </p>
              <div className="space-y-2.5 sm:space-y-3">
                {plan.features && plan.features.length > 0 ? (
                  plan.features
                    .sort((a, b) => a.sort_order - b.sort_order)
                    .slice(0, 6)
                    .map((feature) => (
                      <div key={feature.id} className="flex items-start gap-2">
                        <svg 
                          className="w-4 h-4 sm:w-5 sm:h-5 text-[#00B38F] flex-shrink-0 mt-0.5" 
                          fill="currentColor" 
                          viewBox="0 0 20 20"
                        >
                          <path 
                            fillRule="evenodd" 
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                        <span className="text-xs sm:text-sm text-gray-200 leading-tight">
                          {feature.name}
                        </span>
                      </div>
                    ))
                ) : (
                  <div className="text-center text-gray-400 text-xs sm:text-sm py-2">
                    Contact for details
                  </div>
                )}
                {plan.features && plan.features.length > 6 && (
                  <p className="text-xs text-gray-400 pl-6">
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