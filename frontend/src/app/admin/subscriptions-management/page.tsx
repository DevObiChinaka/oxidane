'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { formatCurrency } from '@/utils/currencyFormatter';
import { API_BASE_URL } from '@/config/api';

// Types
interface Subscription {
  id: string;
  user: {
    id: string;
    email: string;
    username: string;
    full_name: string;
  };
  plan: {
    id: string | null;
    name: string;
    slug: string;
    base_price_usd: number;
    billing_period: string;
  };
  status: string;
  start_date: string | null;
  end_date: string | null;
  auto_renew: boolean;
  next_billing_date: string | null;
  amount_paid: number;
  currency: string;
  payment_method: string | null;
  cancelled_at: string | null;
  days_remaining: number;
  created_at: string;
}

interface Analytics {
  total_count: number;
  active_count: number;
  total_revenue_usd: number;
  average_value_usd: number;
  plan_breakdown: Record<string, number>;
}

interface Plan {
  id: string;
  name: string;
  slug: string;
  base_price: number;
  billing_period: string;
}

export default function SubscriptionsManagementPage() {
  const { user, isAdmin } = useAuth();
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [planFilter, setPlanFilter] = useState('');
  const [autoRenewFilter, setAutoRenewFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Selected for bulk actions
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  
  // Action modal state
  const [actionModal, setActionModal] = useState<{
    type: 'cancel' | 'extend' | null;
    subscription: Subscription | null;
  }>({ type: null, subscription: null });
  const [actionReason, setActionReason] = useState('');
  const [extendDays, setExtendDays] = useState(30);

  useEffect(() => {
    if (!user || !isAdmin) {
      router.push('/admin/login');
      return;
    }
    fetchPlans();
  }, [user, isAdmin, router]);

  useEffect(() => {
    if (user && isAdmin) {
      fetchSubscriptions();
    }
  }, [statusFilter, planFilter, autoRenewFilter, searchQuery, currentPage, user, isAdmin]);

  const fetchPlans = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/admin/subscriptions-management/plans/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans || []);
      }
    } catch (err) {
          }
  };

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        status: statusFilter,
        plan: planFilter,
        auto_renew: autoRenewFilter,
        search: searchQuery,
        page: currentPage.toString(),
        page_size: '20'
      });

      const response = await fetch(`${API_BASE_URL}/admin/subscriptions-management/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
        setAnalytics(data.analytics || null);
        setTotalPages(data.pagination?.total_pages || 1);
      } else {
        setError('Failed to fetch subscriptions');
      }
    } catch (err) {
      setError('Network error');
          } finally {
      setLoading(false);
    }
  };

  const handleAction = async () => {
    if (!actionModal.subscription || !actionModal.type) return;

    try {
      const token = localStorage.getItem('access_token');
      const body: any = { action: actionModal.type };

      if (actionModal.type === 'cancel') {
        body.reason = actionReason || 'Admin cancellation';
      } else if (actionModal.type === 'extend') {
        body.days = extendDays;
      }

      const response = await fetch(
        `${API_BASE_URL}/admin/subscriptions-management/${actionModal.subscription.id}/update/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body)
        }
      );

      if (response.ok) {
        setActionModal({ type: null, subscription: null });
        setActionReason('');
        setExtendDays(30);
        fetchSubscriptions();
      } else {
        const data = await response.json();
        setError(data.error || 'Action failed');
      }
    } catch (err) {
      alert('Network error');
          }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'text-emerald-600',
      cancelled: 'text-red-600',
      expired: 'text-gray-600',
      suspended: 'text-orange-600',
      pending: 'text-amber-600',
    };
    return (
      <span className={`text-sm font-medium ${styles[status] || 'text-gray-600'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (!user || !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Checking authentication...</div>
      </div>
    );
  }

  if (loading && subscriptions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading subscriptions...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Subscriptions Management</h1>
        <p className="text-gray-600 mt-1">Manage all user subscriptions across plans</p>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Total Subscriptions</div>
            <div className="text-3xl font-bold text-gray-900">{analytics.total_count}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Active Subscriptions</div>
            <div className="text-3xl font-bold text-emerald-600">{analytics.active_count}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Total Revenue</div>
            <div className="text-3xl font-bold text-purple-600">
              {formatCurrency(analytics.total_revenue_usd, 'USD')}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Average Value</div>
            <div className="text-3xl font-bold text-blue-600">
              {formatCurrency(analytics.average_value_usd, 'USD')}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-teal"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="cancelled">Cancelled</option>
              <option value="expired">Expired</option>
              <option value="suspended">Suspended</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Plan</label>
            <select
              value={planFilter}
              onChange={(e) => {
                setPlanFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-teal"
            >
              <option value="">All Plans</option>
              {plans.map(plan => (
                <option key={plan.id} value={plan.slug}>{plan.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Auto-Renew</label>
            <select
              value={autoRenewFilter}
              onChange={(e) => {
                setAutoRenewFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-teal"
            >
              <option value="all">All</option>
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search by email, name, username..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal"
            />
          </div>
        </div>
      </div>

      {/* Subscriptions Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount Paid</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Auto-Renew</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {subscriptions.map(sub => (
                <tr key={sub.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{sub.user.full_name}</div>
                    <div className="text-sm text-gray-500">{sub.user.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-brand-teal">{sub.plan.name}</div>
                    <div className="text-xs text-gray-500">{sub.plan.billing_period}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatCurrency(sub.plan.base_price_usd, 'USD')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatCurrency(sub.amount_paid, sub.currency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(sub.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    <div>{formatDate(sub.start_date)}</div>
                    <div className="text-xs text-gray-500">to {formatDate(sub.end_date)}</div>
                    {sub.status === 'active' && sub.days_remaining > 0 && (
                      <div className="text-xs text-brand-teal mt-1">{sub.days_remaining} days left</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {sub.auto_renew ? (
                      <span className="text-emerald-600">✓ Yes</span>
                    ) : (
                      <span className="text-gray-400">✗ No</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setActionModal({ type: 'extend', subscription: sub })}
                        className="p-2 rounded-lg bg-emerald-50 text-emerald-600 hover:bg-emerald-100 hover:text-emerald-700 transition-colors"
                        title="Extend Subscription"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      {sub.status === 'active' && (
                        <button
                          onClick={() => setActionModal({ type: 'cancel', subscription: sub })}
                          className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 hover:text-red-700 transition-colors"
                          title="Cancel Subscription"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Action Modal */}
      {actionModal.type && actionModal.subscription && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                {actionModal.type === 'cancel' && (
                  <span className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Cancel Subscription
                  </span>
                )}
                {actionModal.type === 'extend' && (
                  <span className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Extend Subscription
                  </span>
                )}
              </h3>
              <button
                onClick={() => {
                  setActionModal({ type: null, subscription: null });
                  setActionReason('');
                  setExtendDays(30);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium text-gray-900">{actionModal.subscription.user.full_name}</div>
              <div className="text-sm text-gray-600">{actionModal.subscription.plan.name}</div>
            </div>

            {actionModal.type === 'cancel' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Cancellation Reason</label>
                <textarea
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  rows={3}
                  placeholder="Optional reason..."
                />
              </div>
            )}

            {actionModal.type === 'extend' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Extend By (Days)</label>
                <input
                  type="number"
                  value={extendDays}
                  onChange={(e) => setExtendDays(parseInt(e.target.value) || 0)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal"
                  min="1"
                  placeholder="Enter number of days"
                />
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setActionModal({ type: null, subscription: null });
                  setActionReason('');
                  setExtendDays(30);
                }}
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium text-gray-700"
              >
                Close
              </button>
              <button
                onClick={handleAction}
                className={`flex-1 px-4 py-2.5 text-white rounded-lg hover:opacity-90 font-medium ${
                  actionModal.type === 'cancel' ? 'bg-red-600' : 'bg-brand-teal'
                }`}
              >
                {actionModal.type === 'cancel' ? 'Cancel Subscription' : 'Extend Subscription'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
