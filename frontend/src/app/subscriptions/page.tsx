'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';
import { formatCurrency, formatCurrencyApprox, type Currency } from '@/lib/utils/currency';
import { apiGet, apiPost } from '@/lib/api';
import { API_ENDPOINTS } from '@/config/api';

interface Subscription {
  id: string;
  plan_name: string;
  status: 'active' | 'expired' | 'cancelled';
  amount: number;  // What user actually paid (could be in any currency, with discounts)
  currency: string;  // Currency they paid in (NGN, USD, etc.)
  plan_base_price: number;  // Plan's base price in USD (required)
  plan_currency: string;  // Always 'USD'
  billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'lifetime';
  start_date: string;
  end_date: string | null;
  auto_renew: boolean;
  features: string[];
  telegram_username?: string;
  days_remaining?: number | null;
  is_lifetime?: boolean;
}

interface SubscriptionStats {
  next_renewal_date: string | null;
  days_until_renewal: number | null;
}

export default function SubscriptionsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [stats, setStats] = useState<SubscriptionStats | null>(null);
  const [showExpired, setShowExpired] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [subscriptionToCancel, setSubscriptionToCancel] = useState<Subscription | null>(null);
  const [displayCurrency, setDisplayCurrency] = useState<Currency>('USD');
  const [conversionRate, setConversionRate] = useState<number>(1650); // Default NGN rate
  const [convertedAmounts, setConvertedAmounts] = useState<{ [key: string]: number }>({});
  const [convertedPaidAmounts, setConvertedPaidAmounts] = useState<{ [key: string]: number }>({});
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    checkAuthAndFetchSubscriptions();
  }, []);

  // Fetch conversion rate when currency changes
  useEffect(() => {
    // Always fetch USD to NGN rate for showing conversions
    fetchConversionRate();
  }, [displayCurrency]);

  // Convert amounts when subscriptions or currency changes
  useEffect(() => {
    convertSubscriptionAmounts();
  }, [subscriptions, displayCurrency, conversionRate]);

  const fetchConversionRate = async () => {
    try {
      // Always fetch USD to NGN for showing conversions in parentheses
      const response = await fetch(
        `${API_ENDPOINTS.user.currencyConvert}?from=USD&to=NGN&amount=1`
      );
      
      console.log('Currency conversion response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Currency conversion data:', data);
        // API returns 'to_amount', not 'converted_amount'
        const rate = data.to_amount || data.converted_amount || 1;
        console.log('Setting conversion rate to:', rate);
        setConversionRate(rate);
      } else {
        console.error('Failed to fetch conversion rate:', response.statusText);
        // Use fallback rate if API fails
        const fallbackRate = 1650;
        console.log('Using fallback rate:', fallbackRate);
        setConversionRate(fallbackRate);
      }
    } catch (error) {
      console.error('Error fetching conversion rate:', error);
      // Use fallback rate: approximate NGN/USD rate
      const fallbackRate = displayCurrency === 'NGN' ? 1650 : 1;
      console.log('Using fallback rate (error):', fallbackRate);
      setConversionRate(fallbackRate);
    }
  };

  const convertSubscriptionAmounts = () => {
    const converted: { [key: string]: number } = {};
    const convertedPaid: { [key: string]: number } = {};
    
    subscriptions.forEach(sub => {
      // Use plan base price (what renewals will cost) in USD
      const basePriceUSD = (sub.plan_base_price && !isNaN(sub.plan_base_price)) ? sub.plan_base_price : 0;
      
      // Convert from USD to display currency
      converted[sub.id] = displayCurrency === 'NGN' 
        ? basePriceUSD * conversionRate 
        : basePriceUSD;
      
      // Convert amount paid based on original currency
      const amountPaid = sub.amount || 0;
      const paidCurrency = sub.currency || 'USD';
      
      if (displayCurrency === paidCurrency) {
        // Same currency, no conversion needed
        convertedPaid[sub.id] = amountPaid;
      } else if (displayCurrency === 'NGN' && paidCurrency === 'USD') {
        // USD to NGN
        convertedPaid[sub.id] = amountPaid * conversionRate;
      } else if (displayCurrency === 'USD' && paidCurrency === 'NGN') {
        // NGN to USD
        convertedPaid[sub.id] = amountPaid / conversionRate;
      } else {
        // Default: use original amount
        convertedPaid[sub.id] = amountPaid;
      }
    });
    
    setConvertedAmounts(converted);
    setConvertedPaidAmounts(convertedPaid);
  };

  const checkAuthAndFetchSubscriptions = async () => {
    try {
      const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth');
        return;
      }

      await fetchSubscriptions();
    } catch (error) {
      console.error('Auth check failed:', error);
      router.push('/auth');
    }
  };

  const fetchSubscriptions = async () => {
    try {
      const response = await apiGet('/subscriptions/my-subscriptions/');

      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
        setStats(data.stats || null);
      }
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async (subscription: Subscription) => {
    setSubscriptionToCancel(subscription);
    setShowCancelModal(true);
  };

  const confirmCancelSubscription = async () => {
    if (!subscriptionToCancel) return;

    setCancellingId(subscriptionToCancel.id);
    setShowCancelModal(false);

    try {
      const response = await apiPost(`/subscriptions/${subscriptionToCancel.id}/cancel/`);

      if (response.ok) {
        await fetchSubscriptions();
      } else {
        alert('Failed to cancel subscription. Please try again or contact support.');
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setCancellingId(null);
      setSubscriptionToCancel(null);
    }
  };

  const toggleAutoRenewal = async (subscriptionId: string, currentValue: boolean) => {
    try {
      const response = await apiPost(`/subscriptions/${subscriptionId}/auto-renewal/`, {
        auto_renew: !currentValue,
      });

      if (response.ok) {
        // Update the subscription in state WITHOUT refetching
        // This prevents currency/price changes and unnecessary API calls
        setSubscriptions(prevSubs => 
          prevSubs.map(sub => 
            sub.id === subscriptionId 
              ? { ...sub, auto_renew: !currentValue }
              : sub
          )
        );
      }
    } catch (error) {
      console.error('Error toggling auto-renewal:', error);
    }
  };

  const getStatusBadge = (status: string, daysRemaining?: number | null, isLifetime?: boolean, autoRenew?: boolean, billingCycle?: string) => {
    if (isLifetime) {
      return (
        <span className="text-xs font-medium uppercase tracking-wide text-[#00B38F]">
          Lifetime
        </span>
      );
    }
    
    if (status === 'active') {
      // Only show auto-renewing for recurring plans (not one-time/lifetime)
      if (autoRenew && billingCycle !== 'one_time' && billingCycle !== 'lifetime') {
        return (
          <span className="text-xs font-medium uppercase tracking-wide text-[#00B38F]">
            Auto-Renewing
          </span>
        );
      }
      if (daysRemaining && daysRemaining <= 7) {
        return (
          <span className="text-xs font-medium uppercase tracking-wide text-orange-600">
            Expiring Soon
          </span>
        );
      }
      return (
        <span className="text-xs font-medium uppercase tracking-wide text-green-600">
          Active
        </span>
      );
    }
    if (status === 'expired') {
      return (
        <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
          Expired
        </span>
      );
    }
    return (
      <span className="text-xs font-medium uppercase tracking-wide text-red-600">
        Cancelled
      </span>
    );
  };

  const getPlanIcon = () => {
    // Generic plan icon - admin creates any type of plan
    return (
      <svg className="w-5 h-5 text-[#000856]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');
  const inactiveSubscriptions = subscriptions.filter(sub => sub.status !== 'active');
  
  // Check if user has active recurring subscription (not lifetime, not one-time)
  const hasActiveRecurring = activeSubscriptions.some(sub => 
    sub.billing_cycle !== 'one_time' && 
    sub.billing_cycle !== 'lifetime' && 
    !sub.is_lifetime
  );

  // Get next renewal info from earliest renewing subscription
  const nextRenewal = activeSubscriptions
    .filter(sub => !sub.is_lifetime && sub.end_date)
    .sort((a, b) => new Date(a.end_date!).getTime() - new Date(b.end_date!).getTime())[0];

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />
        <div className="flex-1 flex items-center justify-center min-h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-gray-600">Loading subscriptions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />

      {/* Main Content */}
      <main className="flex-1 min-h-screen lg:ml-0">
        {/* Mobile Menu Button */}
        <div className="lg:hidden fixed top-4 left-4 z-30">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ml-12 lg:ml-0">
            <div>
              <h2 className="text-2xl sm:text-3xl font-semibold text-gray-900">My Subscriptions</h2>
              <p className="text-gray-500 text-sm mt-1">Manage your active plans and billing</p>
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-3">
              {/* Manage Billing Button */}
              <button
                onClick={() => router.push('/billing')}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                Manage Billing
              </button>

              {/* Currency Selector */}
              <div className="flex items-center gap-1 text-sm">
                <button
                  onClick={() => setDisplayCurrency('USD')}
                  className={`px-3 py-1.5 font-medium transition-colors ${
                    displayCurrency === 'USD'
                      ? 'text-gray-900 underline underline-offset-4'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  USD
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => setDisplayCurrency('NGN')}
                  className={`px-3 py-1.5 font-medium transition-colors ${
                    displayCurrency === 'NGN'
                      ? 'text-gray-900 underline underline-offset-4'
                      : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  NGN
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl">
          {/* Recurring Subscription Notice */}
          {hasActiveRecurring && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 text-sm mb-1">
                    Recurring Subscription Active
                  </h3>
                  <p className="text-sm text-gray-600">
                    You have an active recurring subscription. To purchase another recurring plan, cancel your current one first. You can have multiple lifetime plans.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Active Subscriptions */}
          {activeSubscriptions.length > 0 ? (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-5">Active Plans</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {activeSubscriptions.map((subscription) => {
                  const isRecurring = !subscription.is_lifetime && 
                    subscription.billing_cycle !== 'one_time' && 
                    subscription.billing_cycle !== 'lifetime';
                  const amount = convertedAmounts[subscription.id] ?? 0;
                  const paidAmount = convertedPaidAmounts[subscription.id] ?? subscription.amount ?? 0;
                  
                  return (
                    <div
                      key={subscription.id}
                      className="bg-white rounded-lg border border-gray-200 p-6 hover:border-gray-300 transition-all"
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between mb-4 pb-4 border-b border-gray-100">
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900 mb-1">
                            {subscription.plan_name}
                          </h4>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-600">
                              {isRecurring ? 'RECURRING' : subscription.is_lifetime ? 'LIFETIME' : 'ONE-TIME'}
                            </span>
                          </div>
                        </div>
                        {getStatusBadge(subscription.status, subscription.days_remaining, subscription.is_lifetime, subscription.auto_renew, subscription.billing_cycle)}
                      </div>

                      {/* Pricing */}
                      <div className="mb-4 pb-4 border-b border-gray-100">
                        <div className="flex items-baseline gap-1 mb-1">
                          <span className="text-2xl font-semibold text-gray-900">
                            {formatCurrency(amount, displayCurrency)}
                          </span>
                          {!subscription.is_lifetime && subscription.billing_cycle !== 'lifetime' && subscription.billing_cycle !== 'one_time' && (
                            <span className="text-sm text-gray-500">
                              /{subscription.billing_cycle === 'weekly' ? 'week' : 
                                subscription.billing_cycle === 'monthly' ? 'month' : 
                                subscription.billing_cycle === 'quarterly' ? 'quarter' : 'year'}
                            </span>
                          )}
                          {(subscription.is_lifetime || subscription.billing_cycle === 'lifetime') && (
                            <span className="text-sm text-gray-500">one-time</span>
                          )}
                        </div>
                        {subscription.amount && (
                          <p className="text-sm text-gray-500">
                            You paid: {formatCurrency(paidAmount, displayCurrency)}
                          </p>
                        )}
                      </div>

                      {/* Timeline */}
                      <div className="space-y-3 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Started</span>
                          <span className="font-medium text-gray-900">{formatDate(subscription.start_date)}</span>
                        </div>
                        
                        {!subscription.is_lifetime && subscription.end_date && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">
                              {subscription.auto_renew ? 'Renews' : 'Expires'}
                            </span>
                            <div className="text-right">
                              <div className="font-medium text-gray-900">
                                {formatDate(subscription.end_date)}
                              </div>
                              {subscription.days_remaining !== undefined && subscription.days_remaining !== null && (
                                <div className="text-xs text-gray-500">
                                  {subscription.days_remaining} {subscription.days_remaining === 1 ? 'day' : 'days'} remaining
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {subscription.is_lifetime && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Access</span>
                            <span className="font-medium text-[#00B38F]">Lifetime</span>
                          </div>
                        )}
                      </div>

                      {/* Auto-renewal Toggle - Only for recurring */}
                      {isRecurring && (
                        <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg mb-4">
                          <span className="text-sm text-gray-700">Auto-renewal</span>
                          <button
                            onClick={() => toggleAutoRenewal(subscription.id, subscription.auto_renew)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              subscription.auto_renew ? 'bg-green-600' : 'bg-gray-300'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                subscription.auto_renew ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </div>
                      )}

                      {/* Lifetime Notice */}
                      {subscription.is_lifetime && (
                        <div className="py-3 px-4 bg-emerald-50 border border-emerald-200 rounded-lg mb-4">
                          <p className="text-sm text-emerald-800">
                            You have lifetime access to this plan - no renewals needed!
                          </p>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-3">
                        {!subscription.is_lifetime && (
                          <button
                            onClick={() => handleCancelSubscription(subscription)}
                            disabled={cancellingId === subscription.id}
                            className="w-full px-4 py-2.5 text-red-600 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {cancellingId === subscription.id ? 'Cancelling...' : 'Cancel Subscription'}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            // Empty State - No Active Subscriptions
            <div className="bg-white rounded-xl border border-gray-200 p-8 sm:p-12 text-center mb-6 lg:mb-8">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-5">
                <svg className="w-8 h-8 sm:w-10 sm:h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">No Active Subscriptions</h3>
              <p className="text-sm sm:text-base text-gray-500 mb-6 max-w-md mx-auto">
                Unlock premium features, trading signals, and personalized mentorship to accelerate your forex journey.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => router.push('/pricing')}
                  className="px-6 py-2.5 sm:py-3 bg-[#000856] hover:bg-[#000856]/90 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  View Pricing Plans
                </button>
                <button
                  onClick={() => router.push('/courses')}
                  className="px-6 py-2.5 sm:py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Browse Free Courses
                </button>
              </div>
            </div>
          )}

          {/* Expired/Inactive Subscriptions */}
          {inactiveSubscriptions.length > 0 && (
            <div>
              <button
                onClick={() => setShowExpired(!showExpired)}
                className="flex items-center gap-2 text-gray-700 hover:text-gray-900 mb-4 text-sm sm:text-base"
              >
                <svg
                  className={`w-4 h-4 sm:w-5 sm:h-5 transition-transform ${
                    showExpired ? 'rotate-90' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-medium">
                  Inactive Subscriptions ({inactiveSubscriptions.length})
                </span>
              </button>

              {showExpired && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
                  {inactiveSubscriptions.map((subscription) => (
                    <div
                      key={subscription.id}
                      className="bg-gray-50 rounded-lg border border-gray-200 p-4 sm:p-6"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                            {getPlanIcon()}
                          </div>
                          <div>
                            <h4 className="text-sm sm:text-base font-semibold text-gray-900">{subscription.plan_name}</h4>
                            <p className="text-xs sm:text-sm text-gray-500">
                              {subscription.end_date ? `Ended ${formatDate(subscription.end_date)}` : 'Lifetime Access'}
                            </p>
                          </div>
                        </div>
                        {getStatusBadge(subscription.status)}
                      </div>
                      <button
                        onClick={() => router.push('/pricing')}
                        className="w-full mt-4 px-4 py-2 bg-white hover:bg-gray-100 text-gray-700 rounded-lg text-xs sm:text-sm font-medium transition-colors border border-gray-200"
                      >
                        Reactivate Plan
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Cancel Confirmation Modal */}
      {showCancelModal && subscriptionToCancel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">Cancel Subscription?</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Are you sure you want to cancel your <strong>{subscriptionToCancel.plan_name}</strong> subscription?
                </p>
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-4">
                  <p className="text-sm text-gray-700 mb-2">
                    <strong>What happens next:</strong>
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span>You'll keep full access until <strong>{subscriptionToCancel.end_date ? formatDate(subscriptionToCancel.end_date) : 'end of billing period'}</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span>Auto-renewal will be disabled</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span>No charges after {subscriptionToCancel.end_date ? formatDate(subscriptionToCancel.end_date) : 'billing period ends'}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCancelModal(false);
                  setSubscriptionToCancel(null);
                }}
                className="flex-1 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
              >
                Keep Subscription
              </button>
              <button
                onClick={confirmCancelSubscription}
                className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Yes, Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
