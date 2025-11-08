'use client';

import { useState, useEffect } from 'react';

// Types matching backend API response
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
  trial_days: number;
  is_featured: boolean;
  is_active: boolean;
  sort_order: number;
  price: number;
  base_price: number;
  features: Feature[];
  limits: any;
}

interface PricingCardsProps {
  onPlanSelect?: (plan: PricingPlan) => void;
  selectedPlanId?: string;
  currency?: string;
}

export default function PricingCards({ 
  onPlanSelect, 
  selectedPlanId,
  currency = 'USD'
}: PricingCardsProps) {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const queryParams = new URLSearchParams();
        if (currency) queryParams.append('currency', currency);
        
        const response = await fetch(
          `http://127.0.0.1:8000/api/v1/subscriptions/plans/?${queryParams.toString()}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch pricing plans');
        }
        
        const data = await response.json();
        setPlans(data || []);
      } catch (err) {
        console.error('Error fetching plans:', err);
        setError(err instanceof Error ? err.message : 'Failed to load pricing plans');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, [currency]);

  const formatCurrency = (amount: number, currencyCode: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
    }).format(amount);
  };

  const getBillingCycleColor = (cycle: string) => {
    const colors = {
      weekly: 'from-blue-500 to-blue-600',
      monthly: 'from-purple-500 to-purple-600',
      quarterly: 'from-green-500 to-green-600',
      yearly: 'from-yellow-500 to-yellow-600',
      lifetime: 'from-red-500 to-red-600'
    };
    return colors[cycle as keyof typeof colors] || 'from-gray-500 to-gray-600';
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-2xl shadow-lg animate-pulse">
            <div className="p-8">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3 mb-6"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
              <div className="space-y-3">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j} className="h-4 bg-gray-200 rounded w-full"></div>
                ))}
              </div>
              <div className="h-12 bg-gray-200 rounded mt-8"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Plans</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-[#000ABE] text-white rounded-lg hover:bg-[#000ABE]/90 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Plans Available</h3>
        <p className="text-gray-600">Check back soon for new pricing options!</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {plans.map((plan) => (
        <div
          key={plan.id}
          className={`relative bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 ${
            selectedPlanId === plan.id ? 'ring-4 ring-[#000ABE] ring-opacity-50' : ''
          } ${plan.is_featured ? 'border-2 border-yellow-400' : 'border border-gray-200'}`}
        >
          {/* Featured Badge */}
          {plan.is_featured && (
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <span className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">
                ⭐ Most Popular
              </span>
            </div>
          )}

          {/* Trial Badge */}
          {plan.trial_days > 0 && (
            <div className="absolute -top-4 right-4">
              <span className="bg-gradient-to-r from-green-400 to-green-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                {plan.trial_days}-Day Free Trial
              </span>
            </div>
          )}

          <div className="p-8">
            {/* Plan Header */}
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{plan.description}</p>
            </div>

            {/* Pricing */}
            <div className="text-center mb-8">
              <div className="flex items-center justify-center">
                <span className="text-4xl font-bold text-gray-900">
                  {formatCurrency(plan.price, currency)}
                </span>
              </div>
              <p className="text-gray-500 text-sm mt-1">
                {plan.billing_period_display}
              </p>
            </div>

            {/* Features */}
            <div className="space-y-4 mb-8">
              {plan.features && plan.features.length > 0 ? (
                plan.features
                  .sort((a, b) => a.sort_order - b.sort_order)
                  .map((feature) => (
                    <div key={feature.id} className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="flex items-center justify-center w-5 h-5 bg-green-100 rounded-full">
                          {feature.icon ? (
                            <span className="text-sm">{feature.icon}</span>
                          ) : (
                            <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-gray-900 text-sm font-medium">{feature.name}</p>
                        {feature.description && (
                          <p className="text-gray-600 text-xs mt-1">{feature.description}</p>
                        )}
                      </div>
                    </div>
                  ))
              ) : (
                <div className="text-center text-gray-500 text-sm py-4">
                  Contact us for plan details
                </div>
              )}
            </div>

            {/* CTA Button */}
            <button
              onClick={() => onPlanSelect?.(plan)}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all duration-300 ${
                plan.is_featured
                  ? `bg-gradient-to-r ${getBillingCycleColor(plan.billing_period)} hover:shadow-lg hover:scale-105`
                  : `bg-gradient-to-r ${getBillingCycleColor(plan.billing_period)} hover:shadow-lg hover:scale-105`
              }`}
            >
              {plan.billing_period === 'lifetime' ? 'Get Lifetime Access' : 'Subscribe Now'}
            </button>

            {/* Billing Period Badge */}
            <div className="mt-4 text-center">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                plan.billing_period === 'weekly' ? 'bg-blue-100 text-blue-800' :
                plan.billing_period === 'monthly' ? 'bg-purple-100 text-purple-800' :
                plan.billing_period === 'quarterly' ? 'bg-green-100 text-green-800' :
                plan.billing_period === 'yearly' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {plan.billing_period_display}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}