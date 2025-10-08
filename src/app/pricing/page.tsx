'use client';

import { useState, useEffect } from 'react';
import PricingCards from '@/components/PricingCards';
import { PricingPlan } from '@/types/pricing';

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [showCouponInput, setShowCouponInput] = useState(false);
  const [couponCode, setCouponCode] = useState('');

  const handlePlanSelect = (plan: PricingPlan) => {
    setSelectedPlan(plan);
    // Here you would typically redirect to checkout or open a modal
    console.log('Selected plan:', plan);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 mb-6">
              Choose Your
              <span className="block bg-gradient-to-r from-[#00B38F] to-[#000ABE] bg-clip-text text-transparent">
                Trading Plan
              </span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Join thousands of successful traders with our comprehensive forex education 
              and premium signals. Choose the plan that fits your trading journey.
            </p>
            <div className="flex justify-center items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                <span>Cancel Anytime</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                <span>Instant Access</span>
              </div>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                <span>Premium Support</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Category Tabs */}
        <div className="flex justify-center mb-12">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button className="px-6 py-3 text-sm font-medium text-white bg-[#000ABE] rounded-md">
              All Plans
            </button>
            <button className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-900">
              Signals Only
            </button>
            <button className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-900">
              Mentorship
            </button>
            <button className="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-900">
              VIP Access
            </button>
          </div>
        </div>

        <PricingCards 
          onPlanSelect={handlePlanSelect}
          selectedPlanId={selectedPlan?.id}
        />

        {/* Coupon Section */}
        <div className="mt-16 text-center">
          <button
            onClick={() => setShowCouponInput(!showCouponInput)}
            className="text-[#000ABE] hover:text-[#000ABE]/80 text-sm font-medium"
          >
            Have a coupon code? Click here to apply
          </button>
          
          {showCouponInput && (
            <div className="mt-4 max-w-md mx-auto">
              <div className="flex">
                <input
                  type="text"
                  placeholder="Enter coupon code"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-[#000ABE] focus:border-transparent"
                />
                <button className="px-6 py-2 bg-[#000ABE] text-white rounded-r-lg hover:bg-[#000ABE]/90 transition-colors">
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose OxiWorld?
            </h2>
            <p className="text-lg text-gray-600">
              Professional trading education and signals trusted by thousands
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Live Trading Signals</h3>
              <p className="text-gray-600">
                Real-time forex signals with entry and exit points, delivered directly to your Telegram
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Expert Education</h3>
              <p className="text-gray-600">
                Comprehensive forex education from market psychology to advanced strategies
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">24/7 Community</h3>
              <p className="text-gray-600">
                Join our exclusive Telegram groups with direct access to professional traders
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                How quickly do I get access after payment?
              </h3>
              <p className="text-gray-600">
                Access is instant! Once your payment is confirmed, you'll receive Telegram invite 
                links within minutes and can start receiving signals immediately.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I cancel my subscription anytime?
              </h3>
              <p className="text-gray-600">
                Yes, you can cancel your subscription at any time. You'll continue to have access 
                until the end of your current billing period.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Do you offer refunds?
              </h3>
              <p className="text-gray-600">
                We offer a 7-day money-back guarantee for monthly and yearly plans. One-time 
                purchases are final unless there are technical issues.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What's the difference between Signal and VIP plans?
              </h3>
              <p className="text-gray-600">
                Signal plans include trading signals and basic support. VIP plans include everything 
                plus exclusive community access, 1-on-1 sessions, and advanced strategies.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}