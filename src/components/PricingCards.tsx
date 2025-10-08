'use client';

import { useState, useEffect } from 'react';
import { usePublicPricing } from '@/app/admin/hooks/useAdminAPI';

interface PricingPlan {
  id: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  current_price?: number;
  currency: string;
  plan_category: 'signals' | 'mentorship' | 'vip';
  billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
  telegram_groups: string[];
  is_active: boolean;
  is_featured: boolean;
  features_list?: string[];
  created_at: string;
  updated_at: string;
}

interface PricingCardsProps {
  onPlanSelect?: (plan: PricingPlan) => void;
  selectedPlanId?: string;
  showAllPlans?: boolean;
  category?: 'signals' | 'mentorship' | 'vip';
}

export default function PricingCards({ 
  onPlanSelect, 
  selectedPlanId, 
  showAllPlans = true,
  category 
}: PricingCardsProps) {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock data - replace with actual API call
  useEffect(() => {
    // Simulate API call
    const mockPlans: PricingPlan[] = [
      {
        id: '1',
        plan_type: 'mentorship',
        name: 'Basic Mentorship',
        description: 'Comprehensive one-time mentorship program with personal guidance',
        price: 135,
        currency: 'USD',
        plan_category: 'mentorship',
        billing_cycle: 'one_time',
        telegram_groups: ['mentorship_group'],
        is_active: true,
        is_featured: false,
        features_list: [
          '1-on-1 mentorship session',
          'Personal trading strategy',
          'Risk management guide',
          'Lifetime access to resources',
          'Email support'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '2',
        plan_type: 'signals',
        name: 'Weekly Signals',
        description: 'Premium trading signals delivered weekly',
        price: 20,
        currency: 'USD',
        plan_category: 'signals',
        billing_cycle: 'weekly',
        telegram_groups: ['signals_main'],
        is_active: true,
        is_featured: false,
        features_list: [
          '5-7 premium signals per week',
          'Entry and exit points',
          'Risk management levels',
          'Telegram group access',
          'Basic support'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '3',
        plan_type: 'signals',
        name: 'Monthly Signals',
        description: 'Best value - Monthly signals with premium support',
        price: 50,
        currency: 'USD',
        plan_category: 'signals',
        billing_cycle: 'monthly',
        telegram_groups: ['signals_monthly'],
        is_active: true,
        is_featured: true,
        features_list: [
          '20-30 premium signals per month',
          'Detailed market analysis',
          'Entry and exit strategies',
          'Priority Telegram support',
          'Weekly market updates'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '4',
        plan_type: 'signals',
        name: 'Yearly Signals',
        description: 'Maximum savings - Annual signals subscription',
        price: 500,
        currency: 'USD',
        plan_category: 'signals',
        billing_cycle: 'yearly',
        telegram_groups: ['signals_main'],
        is_active: true,
        is_featured: false,
        features_list: [
          'All monthly features',
          '2 months free (12 for 10)',
          'Quarterly strategy review',
          'Direct access to analysts',
          'Premium market insights'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '5',
        plan_type: 'vip',
        name: 'Weekly VIP',
        description: 'VIP trading signals with exclusive content',
        price: 35,
        currency: 'USD',
        plan_category: 'vip',
        billing_cycle: 'weekly',
        telegram_groups: ['vip_main'],
        is_active: true,
        is_featured: false,
        features_list: [
          'Exclusive VIP signals',
          'Live trading sessions',
          'Advanced market analysis',
          'VIP Telegram group',
          '24/7 priority support'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '6',
        plan_type: 'vip',
        name: 'Monthly VIP',
        description: 'Premium VIP access with comprehensive support',
        price: 100,
        currency: 'USD',
        plan_category: 'vip',
        billing_cycle: 'monthly',
        telegram_groups: ['vip_main'],
        is_active: true,
        is_featured: false,
        features_list: [
          'All VIP weekly features',
          'Monthly strategy call',
          'Custom risk assessment',
          'Advanced trading tools',
          'Dedicated account manager'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      },
      {
        id: '7',
        plan_type: 'vip',
        name: 'Yearly VIP',
        description: 'Ultimate VIP experience with maximum value',
        price: 900,
        currency: 'USD',
        plan_category: 'vip',
        billing_cycle: 'yearly',
        telegram_groups: ['vip_main'],
        is_active: true,
        is_featured: false,
        features_list: [
          'All VIP monthly features',
          'Quarterly 1-on-1 calls',
          'Custom trading strategy',
          'Portfolio review sessions',
          'Exclusive market insights'
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }
    ];

    setTimeout(() => {
      let filteredPlans = mockPlans;
      if (category) {
        filteredPlans = mockPlans.filter(plan => plan.plan_category === category);
      }
      setPlans(filteredPlans);
      setLoading(false);
    }, 1000);
  }, [category]);

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      signals: 'from-blue-500 to-blue-600',
      mentorship: 'from-purple-500 to-purple-600',
      vip: 'from-yellow-500 to-yellow-600'
    };
    return colors[category as keyof typeof colors] || 'from-gray-500 to-gray-600';
  };

  const getBillingText = (cycle: string) => {
    const texts = {
      one_time: 'One-time payment',
      weekly: 'per week',
      monthly: 'per month',
      yearly: 'per year'
    };
    return texts[cycle as keyof typeof texts] || cycle;
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
                Featured
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
                  {formatCurrency(plan.price, plan.currency)}
                </span>
              </div>
              <p className="text-gray-500 text-sm mt-1">
                {getBillingText(plan.billing_cycle)}
              </p>
            </div>

            {/* Features */}
            <div className="space-y-4 mb-8">
              {plan.features_list?.map((feature: string, index: number) => (
                <div key={index} className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center w-5 h-5 bg-green-100 rounded-full">
                      <svg className="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-3">
                    <p className="text-gray-700 text-sm">{feature}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* CTA Button */}
            <button
              onClick={() => onPlanSelect?.(plan)}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all duration-300 ${
                plan.is_featured
                  ? `bg-gradient-to-r ${getCategoryColor(plan.plan_category)} hover:shadow-lg hover:scale-105`
                  : `bg-gradient-to-r ${getCategoryColor(plan.plan_category)} hover:shadow-lg hover:scale-105`
              }`}
            >
              {plan.billing_cycle === 'one_time' ? 'Get Started' : 'Subscribe Now'}
            </button>

            {/* Category Badge */}
            <div className="mt-4 text-center">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                plan.plan_category === 'signals' ? 'bg-blue-100 text-blue-800' :
                plan.plan_category === 'mentorship' ? 'bg-purple-100 text-purple-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {plan.plan_category.charAt(0).toUpperCase() + plan.plan_category.slice(1)}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}