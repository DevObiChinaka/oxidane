'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserAuth } from '../contexts/UserAuthContext';
import Navigation from '../components/Navigation';
import Footer from '../components/Footer';
import PricingCards from '@/components/PricingCards';
import { type Currency } from '@/lib/utils/currency';

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

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated } = useUserAuth();
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [currency, setCurrency] = useState<Currency>('USD');

  const handlePlanSelect = (plan: PricingPlan) => {
    setSelectedPlan(plan);
    
    console.log('🎯 Plan selected:', plan.name);
    console.log('🔐 Is authenticated:', isAuthenticated);
    
    // Check if user is authenticated
    if (!isAuthenticated) {
      // Redirect to login with plan and redirect params preserved
      console.log('➡️ Redirecting to login:', `/auth/login?redirect=/checkout&plan=${plan.id}&source=pricing`);
      router.push(`/auth/login?redirect=/checkout&plan=${plan.id}&source=pricing`);
    } else {
      // User is authenticated - go to checkout
      console.log('➡️ Redirecting to checkout:', `/checkout?plan=${plan.id}`);
      router.push(`/checkout?plan=${plan.id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42]">
      <Navigation />
      {/* Background Elements */}
      <div className="absolute inset-0 opacity-8">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>

      {/* Glow Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#00B38F]/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#000ABE]/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full text-sm font-medium text-white/90 mb-6">
            <div className="w-2 h-2 bg-[#00B38F] rounded-full mr-2 animate-pulse"></div>
            Simple, Transparent Pricing
          </div>
          
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
            Choose Your
            <span className="block bg-gradient-to-r from-[#00B38F] to-[#00B39F] bg-clip-text text-transparent mt-2">
              Trading Plan
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto mb-8">
            Professional forex education and signals. All plans include full access to our platform. Cancel anytime.
          </p>

          {/* Currency Selector */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-1">
              <button
                onClick={() => setCurrency('USD')}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                  currency === 'USD'
                    ? 'bg-[#00B38F] text-white shadow-md'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                🇺🇸 USD
              </button>
              <button
                onClick={() => setCurrency('NGN')}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                  currency === 'NGN'
                    ? 'bg-[#00B38F] text-white shadow-md'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                🇳🇬 NGN
              </button>
            </div>
          </div>

          {/* Trust Badges */}
          <div className="flex flex-wrap justify-center items-center gap-6 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Instant Access</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Cancel Anytime</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>24/7 Support</span>
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="mb-20">
          <PricingCards 
            onPlanSelect={handlePlanSelect}
            selectedPlanId={selectedPlan?.id}
            currency={currency}
          />
        </div>

        {/* Features Grid */}
        <div className="mt-24 pt-16 border-t border-white/10">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-lg text-gray-300">
              All plans include access to our complete platform
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                ),
                title: 'Live Trading Signals',
                description: 'Real-time forex signals with entry/exit points'
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                ),
                title: 'Premium Courses',
                description: 'Comprehensive forex education library'
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                ),
                title: 'Exclusive Community',
                description: 'Private Telegram groups with experts'
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                ),
                title: 'Market Analysis',
                description: 'Daily market insights and forecasts'
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ),
                title: 'Risk Management',
                description: 'Professional risk management tools'
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ),
                title: '24/7 Support',
                description: 'Round-the-clock customer support'
              }
            ].map((feature, index) => (
              <div 
                key={index} 
                className="flex items-start gap-4 p-6 bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 hover:bg-white/10 transition-all duration-300"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-[#00B38F] to-[#00B39F] flex items-center justify-center text-white">
                  {feature.icon}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-24 pt-16 border-t border-white/10">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Common Questions
            </h2>
          </div>

          <div className="max-w-3xl mx-auto space-y-4">
            {[
              {
                q: 'How quickly do I get access?',
                a: 'Access is instant! Once payment is confirmed, you receive Telegram invite links within minutes.'
              },
              {
                q: 'Can I cancel anytime?',
                a: 'Yes, cancel your subscription anytime. You\'ll retain access until the end of your billing period.'
              },
              {
                q: 'Do you offer refunds?',
                a: 'We offer a 7-day money-back guarantee for all subscription plans.'
              },
              {
                q: 'What payment methods do you accept?',
                a: 'We accept all major credit cards, PayPal, and bank transfers for enterprise plans.'
              }
            ].map((faq, index) => (
              <div 
                key={index}
                className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all duration-300"
              >
                <h3 className="text-lg font-semibold text-white mb-2">{faq.q}</h3>
                <p className="text-gray-300">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}