'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useUserAuth } from '../contexts/UserAuthContext';
import Navigation from '../components/Navigation';
import Footer from '../components/Footer';
import TelegramVerification from '@/components/TelegramVerification';
import { useCurrencyConverter } from '@/hooks/useCurrencyConverter';
import { API_ENDPOINTS } from '@/config/api';
import {
  initializePayment, 
  validateCoupon, 
  checkTelegramStatus,
  checkSubscriptionConflict,
  checkPendingPayment,
  type InitializePaymentRequest,
  type CheckConflictResponse
} from '@/lib/api/payment';
import Script from 'next/script';

interface Feature {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

interface PricingPlan {
  id: string;
  name: string;
  description: string;
  billing_period: string;
  billing_period_display: string;
  price: number;
  base_price: number;
  currency: string;
  features?: Feature[];
}

// Declare Paystack globally
declare global {
  interface Window {
    PaystackPop?: any;
  }
}

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useUserAuth();
  const planId = searchParams.get('plan');

  const [plan, setPlan] = useState<PricingPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [telegramVerified, setTelegramVerified] = useState(false);
  const [showTelegramVerification, setShowTelegramVerification] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [conflict, setConflict] = useState<CheckConflictResponse | null>(null);
  const [conflictChecking, setConflictChecking] = useState(false);
  const [savedPaymentMethod, setSavedPaymentMethod] = useState<{
    id: string;
    card_brand: string;
    card_last4: string;
  } | null>(null);
  const [showNoCardModal, setShowNoCardModal] = useState(false);
  const [pendingPayment, setPendingPayment] = useState<{
    reference: string;
    payment_url: string;
    amount: number;
  } | null>(null);

  // Form state
  const [currency, setCurrency] = useState<'NGN' | 'USD'>('NGN');
  const [gateway, setGateway] = useState<'paystack' | 'stripe'>('paystack');
  const [couponCode, setCouponCode] = useState('');
  const [couponApplied, setCouponApplied] = useState(false);
  const [couponValidating, setCouponValidating] = useState(false);
  const [discount, setDiscount] = useState<{
    amount: number;
    final_amount: number;
    type: string;
    value: number;
  } | null>(null);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  
  // Live currency conversion
  const { convert, rate, loading: rateLoading, error: rateError } = useCurrencyConverter({
    fromCurrency: 'USD',
    toCurrency: currency,
    autoFetch: true
  });

  // Redirect if not authenticated
  useEffect(() => {
    // Give the auth context time to load
    const checkAuth = () => {
      if (typeof window === 'undefined') return;
      
      const token = localStorage.getItem('user_auth_token');
      if (!token && !isAuthenticated) {
        router.push(`/auth/login?redirect=/checkout&plan=${planId}`);
      }
    };
    
    // Small delay to let auth context initialize
    const timer = setTimeout(checkAuth, 100);
    return () => clearTimeout(timer);
  }, [isAuthenticated, router, planId]);

  // Fetch plan details
  useEffect(() => {
    const fetchPlan = async () => {
      if (!planId) {
        router.push('/pricing');
        return;
      }

      try {
        setLoading(true);
        const response = await fetch(
          `${API_ENDPOINTS.user.subscriptionPlans}${planId}/`
        );

        if (!response.ok) throw new Error('Plan not found');

        const data = await response.json();
        setPlan(data);
        setCurrency(data.currency || 'NGN');
        
        // Check for pending payment after plan is loaded
        if (isAuthenticated) {
          try {
            const pendingResponse = await checkPendingPayment({ plan_id: planId });
            if (pendingResponse.has_pending && pendingResponse.payment_url) {
              setPendingPayment({
                reference: pendingResponse.reference!,
                payment_url: pendingResponse.payment_url,
                amount: pendingResponse.amount!
              });
            }
          } catch (err) {
            console.log('No pending payment found');
          }
        }
      } catch (err) {
        router.push('/pricing');
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [planId, router, isAuthenticated]);

  // Fetch saved payment method
  useEffect(() => {
    const fetchSavedPaymentMethod = async () => {
      if (!isAuthenticated) return;
      
      try {
        const response = await fetch(
          API_ENDPOINTS.user.paymentMethods,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('user_auth_token')}`
            }
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.payment_methods && data.payment_methods.length > 0) {
            setSavedPaymentMethod(data.payment_methods[0]);
          }
        }
      } catch (err) {
        // Silent fail - user can still proceed with new payment
      }
    };
    
    fetchSavedPaymentMethod();
  }, [isAuthenticated]);

  // Check for subscription conflicts
  useEffect(() => {
    const checkConflict = async () => {
      if (!planId || !isAuthenticated) {
        return;
      }

      try {
        setConflictChecking(true);
        const conflictData = await checkSubscriptionConflict(planId);
        
        if (conflictData.conflict) {
          setConflict(conflictData);
          setError('Subscription conflict detected. Please manage your existing subscription first.');
          
          // Auto-redirect after 5 seconds
          setTimeout(() => {
            router.push('/subscriptions');
          }, 5000);
        } else {
          setConflict(null);
        }
      } catch (err) {
        // If check fails, allow purchase to proceed
        // Don't block checkout if conflict check fails - backend will handle it
      } finally {
        setConflictChecking(false);
      }
    };

    checkConflict();
  }, [planId, isAuthenticated, router]);

  // Check Telegram verification status
  useEffect(() => {
    const checkTelegram = async () => {
      try {
        const data = await checkTelegramStatus();
        setTelegramVerified(data.telegram_verified);
        setShowTelegramVerification(!data.telegram_verified);
      } catch (err) {
        // If check fails, assume not verified
        // Don't show error to user - Telegram is optional
      }
    };

    // Only check if authenticated AND token exists in localStorage
    if (isAuthenticated && typeof window !== 'undefined') {
      const token = localStorage.getItem('user_auth_token');
      if (token) {
        checkTelegram();
      }
    }
  }, [isAuthenticated]);

  // Auto-select gateway based on currency
  useEffect(() => {
    if (currency === 'NGN') {
      setGateway('paystack');
    } else if (currency === 'USD') {
      setGateway('stripe');
    }
  }, [currency]);

  // Validate coupon
  const handleValidateCoupon = async () => {
    if (!couponCode.trim()) return;

    try {
      setCouponValidating(true);
      setError('');
      
      // Get base price in USD for coupon validation
      const basePriceUSD = plan?.base_price || plan?.price || 0;
      
      const data = await validateCoupon({
        code: couponCode,
        amount: basePriceUSD,
        plan_id: plan?.id,
        user_id: user?.id
      });

      if (data.valid) {
        setCouponApplied(true);
        setDiscount({
          amount: data.discount_amount || 0,
          final_amount: data.final_price || 0,
          type: data.discount_type || 'percentage',
          value: data.discount_value || 0
        });
        setError('');
      } else {
        setError(data.error || 'Invalid coupon code');
        setCouponApplied(false);
        setDiscount(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate coupon');
      setCouponApplied(false);
      setDiscount(null);
    } finally {
      setCouponValidating(false);
    }
  };

  // Remove coupon
  const handleRemoveCoupon = () => {
    setCouponCode('');
    setCouponApplied(false);
    setDiscount(null);
    setError('');
  };

  // Handle payment
  const handleProceedToPayment = async () => {
    if (!telegramVerified) {
      setShowTelegramVerification(true);
      setError('Please verify your Telegram account first');
      return;
    }

    if (!agreedToTerms) {
      setError('Please agree to the terms and conditions');
      return;
    }

    // Check if user has a saved payment method
    if (!savedPaymentMethod) {
      setShowNoCardModal(true);
      return;
    }

    try {
      setProcessing(true);
      setError('');

      // Charge using saved card
      const response = await fetch(
        API_ENDPOINTS.user.chargeSavedCard,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('user_auth_token')}`
          },
          body: JSON.stringify({
            plan_id: planId,
            coupon_code: couponApplied ? couponCode : undefined,
            currency: currency,
            amount: basePriceConverted  // Send the already-converted base price
          })
        }
      );

      const data = await response.json();

      if (data.success) {
        // Payment successful - redirect to success page
        router.push(`/payment/callback?reference=${data.reference}&status=success`);
      } else {
        // Payment failed
        if (data.redirect_to_billing) {
          setShowNoCardModal(true);
        } else {
          setError(data.error || 'Payment failed. Please try again.');
        }
        setProcessing(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process payment');
      setProcessing(false);
    }
  };

  // Calculate amounts with live conversion
  const basePriceUSD = plan?.base_price || plan?.price || 0;
  const basePriceConverted = currency === 'USD' ? basePriceUSD : convert(basePriceUSD);
  
  // Convert discount amount to selected currency
  const discountAmountUSD = discount?.amount || 0;
  const discountAmount = currency === 'USD' ? discountAmountUSD : convert(discountAmountUSD);
  
  // Convert final amount to selected currency
  const finalAmountUSD = discount?.final_amount || basePriceUSD;
  const finalAmount = currency === 'USD' ? finalAmountUSD : convert(finalAmountUSD);
  
  const processingFee = finalAmount * 0.015; // 1.5% processing fee
  const totalAmount = finalAmount + processingFee;

  const formatCurrency = (amount: number, curr: string = currency) => {
    // Round to 2 decimal places to avoid floating point precision issues
    const roundedAmount = Math.round(amount * 100) / 100;
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(roundedAmount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F] mb-4"></div>
          <p className="text-white text-lg">Loading checkout...</p>
        </div>
      </div>
    );
  }

  if (!plan) return null;

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42]">
        <Navigation />
        
        {/* Background Elements */}
        <div className="absolute inset-0 opacity-8">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}></div>
        </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        {/* Conflict Warning Banner */}
        {conflict && conflict.conflict && conflict.existing_subscription && (
          <div className="mb-8 bg-red-50/95 backdrop-blur-sm border-2 border-red-300 rounded-2xl p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-900 mb-2">
                  Subscription Conflict Detected
                </h3>
                <p className="text-sm text-red-800 mb-4 leading-relaxed">
                  You already have an active <strong>{conflict.existing_subscription.plan_name}</strong> ({conflict.existing_subscription.billing_period_display}) 
                  subscription ending on <strong>{new Date(conflict.existing_subscription.end_date).toLocaleDateString()}</strong>. 
                  You can only have one recurring subscription at a time.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button 
                    onClick={() => router.push('/subscriptions')}
                    className="px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium text-sm shadow-sm"
                  >
                    Manage Subscriptions
                  </button>
                  <button 
                    onClick={() => router.push('/pricing')}
                    className="px-5 py-2.5 bg-white text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors font-medium text-sm"
                  >
                    View Other Plans
                  </button>
                </div>
                <p className="text-xs text-red-700 mt-4">
                  Redirecting to subscriptions page in 5 seconds...
                </p>
              </div>
            </div>
          </div>
        )}
        
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Plan Summary */}
          <div className="space-y-6">
            {/* Back Button */}
            <button
              onClick={() => router.push('/pricing')}
              className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Pricing
            </button>

            {/* Plan Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">{plan.name}</h2>
                  <p className="text-gray-300 text-sm">{plan.description}</p>
                </div>
              </div>

              <div className="space-y-4 py-6 border-white/10">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">
                    Base Price
                  </span>
                  <span className="text-white font-semibold">
                    {rateLoading ? (
                      <span className="inline-block w-20 h-4 bg-white/10 animate-pulse rounded"></span>
                    ) : (
                      formatCurrency(basePriceConverted)
                    )}
                  </span>
                </div>

                {rate && currency !== 'USD' && !rateError && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Exchange Rate</span>
                    <span className="text-gray-400">1 USD = {rate.toFixed(2)} {currency}</span>
                  </div>
                )}

                {discount && (
                  <div className="flex justify-between text-sm">
                    <span className="text-green-400">Discount ({discount.type === 'percentage' ? `${discount.value}%` : formatCurrency(discount.value)})</span>
                    <span className="text-green-400 font-semibold">-{formatCurrency(discountAmount)}</span>
                  </div>
                )}

                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Processing Fee (1.5%)</span>
                  <span className="text-white font-semibold">{formatCurrency(processingFee)}</span>
                </div>
              </div>

              <div className="flex justify-between items-baseline mt-6">
                <span className="text-gray-300">
                  Total Amount
                </span>
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">
                    {formatCurrency(totalAmount)}
                  </div>
                  <div className="text-sm text-gray-400">{plan.billing_period_display}</div>
                </div>
              </div>
            </div>

            {/* What's Included */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">What's Included</h3>
              <ul className="space-y-3">
                {plan?.features && plan.features.length > 0 ? (
                  plan.features.map((feature) => (
                    <li key={feature.id} className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-[#00B38F] flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <span className="text-gray-200 text-sm font-medium">{feature.name}</span>
                        {feature.description && (
                          <p className="text-gray-400 text-xs mt-0.5">{feature.description}</p>
                        )}
                      </div>
                    </li>
                  ))
                ) : (
                  <li className="text-gray-400 text-sm">No features listed for this plan</li>
                )}
              </ul>
            </div>
          </div>

          {/* Right Column - Payment Form */}
          <div className="space-y-6">
            {/* Saved Payment Method Display */}
            {savedPaymentMethod && (
              <div className="bg-white/10 backdrop-blur-md rounded-2xl border-2 border-[#00B38F]/50 p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-white font-semibold">Payment Method</h3>
                  <button
                    onClick={() => router.push('/billing')}
                    className="text-[#00B38F] text-sm hover:underline"
                  >
                    Change
                  </button>
                </div>
                <div className="flex items-center gap-3 bg-black/20 rounded-lg p-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-white font-medium capitalize">{savedPaymentMethod.card_brand}</p>
                    <p className="text-gray-400 text-sm">•••• •••• •••• {savedPaymentMethod.card_last4}</p>
                  </div>
                </div>
                <p className="text-gray-400 text-xs mt-2">
                  This card will be charged for your subscription
                </p>
              </div>
            )}

            {/* Telegram Verification Status */}
            <div className={`bg-white/10 backdrop-blur-md rounded-2xl border-2 p-6 ${
              telegramVerified ? 'border-green-500/50' : 'border-yellow-500/50'
            }`}>
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                  telegramVerified ? 'bg-green-500/20' : 'bg-yellow-500/20'
                }`}>
                  {telegramVerified ? (
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-white font-semibold mb-1">
                    {telegramVerified ? 'Telegram Verified ✓' : 'Telegram Verification Required'}
                  </h3>
                  <p className="text-gray-300 text-sm">
                    {telegramVerified 
                      ? 'Your Telegram is connected and ready for group access'
                      : 'You need to verify your Telegram to access premium signals'
                    }
                  </p>
                  {!telegramVerified && (
                    <button
                      onClick={() => setShowTelegramVerification(!showTelegramVerification)}
                      className="mt-3 text-sm text-[#00B38F] hover:text-[#00A87D] font-medium"
                    >
                      {showTelegramVerification ? 'Hide Verification' : 'Verify Now →'}
                    </button>
                  )}
                </div>
              </div>

              {showTelegramVerification && !telegramVerified && (
                <div className="mt-6 pt-6 border-t border-white/10">
                  <TelegramVerification
                    onVerified={() => {
                      setTelegramVerified(true);
                      setShowTelegramVerification(false);
                    }}
                    onError={(err) => setError(err)}
                    showInline={false}
                    autoStart={true}
                    theme="dark"
                  />
                </div>
              )}
            </div>

            {/* Payment Options */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Payment Details</h3>

              {/* Currency Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Currency
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { code: 'NGN', name: 'Nigerian Naira', symbol: '₦' },
                    { code: 'USD', name: 'US Dollar', symbol: '$' }
                  ].map((curr) => (
                    <button
                      key={curr.code}
                      onClick={() => setCurrency(curr.code as 'NGN' | 'USD')}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        currency === curr.code
                          ? 'border-[#00B38F] bg-[#00B38F]/10'
                          : 'border-white/20 bg-white/5 hover:border-white/40'
                      }`}
                    >
                      <div className="text-left">
                        <div className="font-semibold text-white">{curr.symbol} {curr.code}</div>
                        <div className="text-xs text-gray-400">{curr.name}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Gateway Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Payment Gateway
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: 'paystack', name: 'Paystack', recommended: currency === 'NGN', available: true },
                    { id: 'stripe', name: 'Stripe', recommended: currency === 'USD', available: false }
                  ].map((gw) => (
                    <button
                      key={gw.id}
                      onClick={() => setGateway(gw.id as 'paystack' | 'stripe')}
                      className={`p-3 rounded-lg border-2 transition-all relative ${
                        gateway === gw.id
                          ? 'border-[#00B38F] bg-[#00B38F]/10'
                          : 'border-white/20 bg-white/5 hover:border-white/40'
                      }`}
                    >
                      <div className="text-left">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{gw.name}</span>
                          {!gw.available && (
                            <span className="text-xs px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded-full border border-amber-500/30">
                              Coming Soon
                            </span>
                          )}
                        </div>
                        {gw.recommended && gw.available && (
                          <div className="text-xs text-[#00B38F]">Recommended</div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* International Payment Notice */}
              {gateway === 'stripe' && (
                <div className="bg-blue-500/10 border-2 border-blue-500/50 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center mt-0.5">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-blue-300 font-semibold mb-1">International Payments</h4>
                      <p className="text-sm text-blue-200/90 mb-3">
                        For international payments, please contact our support team. We'll assist you with manual payment processing and provide immediate access to your subscription.
                      </p>
                      <div className="flex flex-col sm:flex-row gap-2">
                        <a
                          href="mailto:support@oxidane.com"
                          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          Contact Support
                        </a>
                        <button
                          onClick={() => setGateway('paystack')}
                          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          <span>Switch to Paystack</span>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Coupon Code */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Coupon Code (Optional)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    disabled={couponApplied}
                    placeholder="Enter coupon code"
                    className="flex-1 px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-[#00B38F] focus:border-transparent disabled:opacity-50"
                  />
                  {couponApplied ? (
                    <button
                      onClick={handleRemoveCoupon}
                      className="px-4 py-3 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                    >
                      Remove
                    </button>
                  ) : (
                    <button
                      onClick={handleValidateCoupon}
                      disabled={couponValidating || !couponCode.trim()}
                      className="px-6 py-3 bg-[#00B38F] text-white rounded-lg hover:bg-[#00A87D] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {couponValidating ? 'Validating...' : 'Apply'}
                    </button>
                  )}
                </div>
                {couponApplied && discount && (
                  <p className="text-sm text-green-400 mt-2">
                    ✓ Coupon applied! You save {formatCurrency(discountAmount)}
                  </p>
                )}
              </div>
            </div>

            {/* Terms & Conditions */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="mt-1 w-4 h-4 text-[#00B38F] border-gray-300 rounded focus:ring-[#00B38F]"
                />
                <span className="text-sm text-gray-300">
                  I agree to the{' '}
                  <a href="/terms" target="_blank" className="text-[#00B38F] hover:underline">
                    Terms & Conditions
                  </a>{' '}
                  and{' '}
                  <a href="/privacy" target="_blank" className="text-[#00B38F] hover:underline">
                    Privacy Policy
                  </a>
                </span>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Payment Button */}
            {pendingPayment ? (
              <div className="space-y-3">
                {/* Pending Payment Notice */}
                <div className="bg-amber-500/10 border-2 border-amber-500/50 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center mt-0.5">
                      <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-amber-300 font-semibold mb-1">Pending Payment Found</h4>
                      <p className="text-sm text-amber-200/90">
                        You have an incomplete payment for this plan. You can resume your previous payment or start a new one.
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        Reference: {pendingPayment.reference}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Resume Payment Button */}
                <button
                  onClick={() => {
                    window.location.href = pendingPayment.payment_url;
                  }}
                  className="w-full py-4 px-6 bg-gradient-to-r from-amber-500 to-amber-600 text-white rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity shadow-lg"
                >
                  Resume Payment - {formatCurrency(pendingPayment.amount)}
                </button>

                {/* Start New Payment Button */}
                <button
                  onClick={() => {
                    setPendingPayment(null);
                  }}
                  className="w-full py-3 px-6 bg-white/10 border-2 border-white/20 text-white rounded-xl font-medium text-base hover:bg-white/20 transition-colors"
                >
                  Start New Payment Instead
                </button>
              </div>
            ) : (
              <button
                onClick={handleProceedToPayment}
                disabled={processing || !agreedToTerms || !telegramVerified || (conflict?.conflict === true) || gateway === 'stripe'}
                className="w-full py-4 px-6 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {processing ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    Processing...
                  </span>
                ) : gateway === 'stripe' ? (
                  'Contact Support for International Payments'
                ) : (
                  `Proceed to Payment - ${formatCurrency(totalAmount)}`
                )}
              </button>
            )}

            {/* Security Badge */}
            <div className="flex items-center justify-center gap-2 text-gray-400 text-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>Secure payment powered by {gateway === 'paystack' ? 'Paystack' : 'Stripe'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* No Payment Method Modal */}
      {showNoCardModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-[#001845] to-[#003366] rounded-2xl max-w-md w-full p-8 border border-[#00B38F]/30">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">No Payment Method</h3>
              <p className="text-gray-300 mb-6">
                You need to add a payment method before you can subscribe to a plan. Your card will be charged ₦50 for verification (refunded immediately).
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowNoCardModal(false)}
                className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => router.push('/billing')}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                Add Payment Method
              </button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
    </>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F] mb-4"></div>
          <p className="text-white text-lg">Loading...</p>
        </div>
      </div>
    }>
      <CheckoutContent />
    </Suspense>
  );
}
