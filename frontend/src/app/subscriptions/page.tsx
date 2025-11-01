'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';

interface Subscription {
  id: string;
  plan_name: string;
  plan_type: 'signal' | 'mentorship' | 'bundle';
  status: 'active' | 'expired' | 'cancelled';
  amount: number;
  currency: string;
  billing_cycle: 'one_time' | 'weekly' | 'monthly';
  start_date: string;
  end_date: string | null; // null for lifetime (mentorship)
  auto_renew: boolean;
  features: string[];
  telegram_username?: string;
  days_remaining?: number | null; // null for lifetime
  is_lifetime?: boolean; // For mentorship
}

interface SubscriptionStats {
  active_count: number;
  total_monthly_cost: number;
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

  useEffect(() => {
    checkAuthAndFetchSubscriptions();
  }, []);

  const checkAuthAndFetchSubscriptions = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
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
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/subscriptions/my-subscriptions/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

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

  const handleCancelSubscription = async (subscriptionId: string) => {
    if (!confirm('Are you sure you want to cancel this subscription? It will remain active until the end of your billing period.')) {
      return;
    }

    setCancellingId(subscriptionId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/subscriptions/${subscriptionId}/cancel/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        await fetchSubscriptions();
        alert('Subscription cancelled successfully. You will retain access until the end of your billing period.');
      } else {
        alert('Failed to cancel subscription. Please try again or contact support.');
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setCancellingId(null);
    }
  };

  const toggleAutoRenewal = async (subscriptionId: string, currentValue: boolean) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/subscriptions/${subscriptionId}/auto-renewal/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ auto_renew: !currentValue }),
      });

      if (response.ok) {
        await fetchSubscriptions();
      }
    } catch (error) {
      console.error('Error toggling auto-renewal:', error);
    }
  };

  const getStatusBadge = (status: string, daysRemaining?: number | null, isLifetime?: boolean) => {
    if (isLifetime) {
      return (
        <span className="px-3 py-1.5 bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 rounded-full text-xs font-bold flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
          LIFETIME
        </span>
      );
    }
    
    if (status === 'active') {
      if (daysRemaining && daysRemaining <= 7) {
        return (
          <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
            Expiring Soon
          </span>
        );
      }
      return (
        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
          Active
        </span>
      );
    }
    if (status === 'expired') {
      return (
        <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
          Expired
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
        Cancelled
      </span>
    );
  };

  const getPlanIcon = (planType: string) => {
    if (planType === 'signal') {
      return (
        <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
    }
    if (planType === 'mentorship') {
      return (
        <svg className="w-6 h-6 text-[#000856]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      );
    }
    return (
      <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');
  const inactiveSubscriptions = subscriptions.filter(sub => sub.status !== 'active');

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardSidebar />
        <div className="ml-72 flex-1 flex items-center justify-center min-h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-gray-600">Loading subscriptions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardSidebar />

      {/* Main Content */}
      <main className="ml-72 min-h-screen">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-8 py-8">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">My Subscriptions</h2>
            <p className="text-gray-500 text-sm mt-1">Manage your active plans and billing</p>
          </div>
        </header>

        <div className="p-8 max-w-7xl">
          {/* Stats Cards */}
          {stats && stats.active_count > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
              {/* Active Count */}
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Active Subscriptions</p>
                    <p className="text-3xl font-bold text-gray-900">{stats.active_count}</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Monthly Cost */}
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Total Monthly Cost</p>
                    <p className="text-3xl font-bold text-gray-900">${stats.total_monthly_cost}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Next Renewal */}
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Next Renewal</p>
                    {stats.days_until_renewal !== null ? (
                      <>
                        <p className="text-3xl font-bold text-gray-900">{stats.days_until_renewal}</p>
                        <p className="text-xs text-gray-500 mt-1">days</p>
                      </>
                    ) : (
                      <p className="text-lg text-gray-400">N/A</p>
                    )}
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Active Subscriptions */}
          {activeSubscriptions.length > 0 ? (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Plans</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {activeSubscriptions.map((subscription) => (
                  <div
                    key={subscription.id}
                    className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gray-50 rounded-lg flex items-center justify-center">
                          {getPlanIcon(subscription.plan_type)}
                        </div>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">{subscription.plan_name}</h4>
                          <p className="text-sm text-gray-500 capitalize">
                            {subscription.is_lifetime ? 'Lifetime Access' : subscription.billing_cycle}
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(subscription.status, subscription.days_remaining, subscription.is_lifetime)}
                    </div>

                    {/* Price */}
                    <div className="mb-4">
                      <p className="text-2xl font-bold text-gray-900">
                        ${subscription.amount}
                        {!subscription.is_lifetime && (
                          <span className="text-sm font-normal text-gray-500">
                            /{subscription.billing_cycle === 'weekly' ? 'week' : subscription.billing_cycle === 'monthly' ? 'month' : 'year'}
                          </span>
                        )}
                        {subscription.is_lifetime && (
                          <span className="text-sm font-normal text-gray-500"> (one-time)</span>
                        )}
                      </p>
                    </div>

                    {/* Dates */}
                    <div className="space-y-2 mb-4 pb-4 border-b border-gray-100">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Started</span>
                        <span className="text-gray-900 font-medium">{formatDate(subscription.start_date)}</span>
                      </div>
                      {!subscription.is_lifetime && subscription.end_date && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">
                            {subscription.auto_renew ? 'Renews' : 'Expires'}
                          </span>
                          <span className="text-gray-900 font-medium">
                            {formatDate(subscription.end_date)}
                            {subscription.days_remaining !== undefined && subscription.days_remaining !== null && (
                              <span className="text-gray-500 ml-1">
                                ({subscription.days_remaining} days)
                              </span>
                            )}
                          </span>
                        </div>
                      )}
                      {subscription.is_lifetime && (
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-gray-500">Access</span>
                          <span className="text-purple-700 font-bold flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                            </svg>
                            Never Expires
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Features */}
                    <div className="mb-4">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Included</p>
                      <div className="space-y-1.5">
                        {subscription.features.map((feature, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm text-gray-700">
                            <svg className="w-4 h-4 text-[#00B38F] flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {feature}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Auto-renewal Toggle - Only for recurring subscriptions */}
                    {!subscription.is_lifetime && (
                      <div className="flex items-center justify-between py-3 px-3 bg-gray-50 rounded-lg mb-4">
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span className="text-sm font-medium text-gray-700">Auto-renewal</span>
                        </div>
                        <button
                          onClick={() => toggleAutoRenewal(subscription.id, subscription.auto_renew)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            subscription.auto_renew ? 'bg-[#00B38F]' : 'bg-gray-300'
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

                    {/* Lifetime Info Banner */}
                    {subscription.is_lifetime && (
                      <div className="py-3 px-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg mb-4">
                        <div className="flex items-center gap-2 text-sm text-purple-800">
                          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="font-medium">You have lifetime access to this plan - no renewals needed!</span>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3">
                      {!subscription.is_lifetime && (
                        <>
                          <button
                            onClick={() => router.push('/pricing')}
                            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                          >
                            Upgrade Plan
                          </button>
                          <button
                            onClick={() => handleCancelSubscription(subscription.id)}
                            disabled={cancellingId === subscription.id}
                            className="flex-1 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                          >
                            {cancellingId === subscription.id ? 'Cancelling...' : 'Cancel'}
                          </button>
                        </>
                      )}
                      {subscription.is_lifetime && (
                        <button
                          onClick={() => router.push('/courses')}
                          className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-bold hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg"
                        >
                          Access Your Courses
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            // Empty State - No Active Subscriptions
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center mb-8">
              <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-5">
                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Active Subscriptions</h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Unlock premium features, trading signals, and personalized mentorship to accelerate your forex journey.
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => router.push('/pricing')}
                  className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg font-medium transition-colors"
                >
                  View Pricing Plans
                </button>
                <button
                  onClick={() => router.push('/courses')}
                  className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
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
                className="flex items-center gap-2 text-gray-700 hover:text-gray-900 mb-4"
              >
                <svg
                  className={`w-5 h-5 transition-transform ${showExpired ? 'rotate-90' : ''}`}
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {inactiveSubscriptions.map((subscription) => (
                    <div
                      key={subscription.id}
                      className="bg-gray-50 rounded-lg border border-gray-200 p-6 opacity-75"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                            {getPlanIcon(subscription.plan_type)}
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">{subscription.plan_name}</h4>
                            <p className="text-sm text-gray-500">
                              {subscription.end_date ? `Ended ${formatDate(subscription.end_date)}` : 'Lifetime Access'}
                            </p>
                          </div>
                        </div>
                        {getStatusBadge(subscription.status)}
                      </div>
                      <button
                        onClick={() => router.push('/pricing')}
                        className="w-full mt-4 px-4 py-2 bg-white hover:bg-gray-100 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-200"
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
    </div>
  );
}
