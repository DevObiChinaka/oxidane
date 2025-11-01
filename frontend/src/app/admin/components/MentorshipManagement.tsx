'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { 
  useMentorshipSubscriptions, 
  useMentorshipAnalytics 
} from '../hooks/useAdminAPI';

interface MentorshipSubscription {
  id: string;
  user_email: string;
  user_name: string;
  plan_name: string;
  plan_type: string;
  amount_paid: number;
  currency: string;
  payment_status: string;
  subscription_status: string;
  subscription_start: string | null;
  subscription_end: string | null;
  days_remaining: number;
  telegram_username: string;
  telegram_status: string;
  is_active: boolean;
  created_at: string;
}

export default function MentorshipManagement() {
  const router = useRouter();
  const { isAuthenticated, user, loading: authLoading, logout } = useAuth();
  
  // Use the new hooks
  const subscriptionHook = useMentorshipSubscriptions();
  const analyticsHook = useMentorshipAnalytics();
  
  const [subscriptions, setSubscriptions] = useState<MentorshipSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'subscriptions' | 'analytics'>('subscriptions');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [telegramFilter, setTelegramFilter] = useState('all');
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    // Only fetch data if user is authenticated and is admin
    if (isAuthenticated && !authLoading && user?.is_staff) {
      fetchData();
    }
  }, [isAuthenticated, authLoading, user, activeTab]);

  // Handle authentication redirects
  useEffect(() => {
    if (!authLoading && (!isAuthenticated || !user?.is_staff)) {
      router.push('/admin/login');
    }
  }, [authLoading, isAuthenticated, user, router]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (activeTab === 'subscriptions') {
        const response = await subscriptionHook.fetchSubscriptions({
          search: searchTerm || undefined,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          telegram_status: telegramFilter !== 'all' ? telegramFilter : undefined,
        }) as any;
        
        if (response.success) {
          setSubscriptions(response.subscriptions || []);
        }
      } else if (activeTab === 'analytics') {
        const response = await analyticsHook.fetchAnalytics() as any;
        
        if (response.success) {
          setAnalytics(response.analytics);
        }
      }
      } catch (error) {
      console.error('Failed to fetch data:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string, type: 'payment' | 'subscription' | 'telegram' | 'session' = 'subscription') => {
    const statusStyles: {[key: string]: string} = {
      // Payment statuses
      'verified': 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium',
      'pending': 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium',
      'failed': 'bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium',
      
      // Subscription statuses  
      'active': 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium',
      'expired': 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium',
      'subscription_cancelled': 'bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium',
      'suspended': 'bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium',
      
      // Telegram statuses
      'added': 'bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium',
      'pending_add': 'bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium',
      'not_added': 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium',
      'failed_add': 'bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium',
      'removed': 'bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium',
      
      // Session statuses
      'scheduled': 'bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium',
      'completed': 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium',
      'session_cancelled': 'bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium',
      'no_show': 'bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium',
    };
    
    // Map status based on type for proper styling
    let statusKey = status;
    if (type === 'subscription' && status === 'cancelled') {
      statusKey = 'subscription_cancelled';
    } else if (type === 'session' && status === 'cancelled') {
      statusKey = 'session_cancelled';
    }
    
    return (
      <span className={statusStyles[statusKey] || statusStyles.pending}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const handleExtendSubscription = async (subscriptionId: string) => {
    const days = prompt('Enter number of days to extend:');
    const reason = prompt('Reason for extension:');
    
    if (days && reason && !isNaN(parseInt(days))) {
      try {
        const response = await subscriptionHook.extendSubscription(subscriptionId, {
          extend_days: parseInt(days),
          reason: reason
        }) as any;
        
        if (response.success) {
          alert('Subscription extended successfully!');
          fetchData();
        } else {
          alert('Failed to extend subscription: ' + (response.error || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error extending subscription:', error);
        alert('Error extending subscription. Please try again.');
      }
    } else if (days && isNaN(parseInt(days))) {
      alert('Please enter a valid number of days.');
    }
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    const matchesSearch = sub.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         sub.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         sub.telegram_username.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || sub.subscription_status === statusFilter;
    const matchesTelegram = telegramFilter === 'all' || sub.telegram_status === telegramFilter;
    
    return matchesSearch && matchesStatus && matchesTelegram;
  });

  // Let AdminAuthContext handle authentication and redirects
  // Just show loading while auth is being checked
  if (authLoading || !isAuthenticated) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading mentorship data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading data</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={() => fetchData()}
                className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Mentorship Program Management</h1>
            <p className="mt-1 text-sm text-gray-600">Manage lifetime mentorship subscriptions and analytics</p>
          </div>
        </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'subscriptions', label: '👥 Subscriptions', count: subscriptions.length },
            { key: 'analytics', label: '📊 Analytics' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => {setActiveTab(tab.key as any); fetchData();}}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          ))}
        </nav>
      </div>

      {/* Subscriptions Tab */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-4">
          {/* Controls */}
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-900 mb-2">Search Users</label>
                <input
                  type="text"
                  placeholder="Search by email, name, or username..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
                >
                  <option value="all" className="text-gray-900">All Statuses</option>
                  <option value="active" className="text-gray-900">Active</option>
                  <option value="expired" className="text-gray-900">Expired</option>
                  <option value="cancelled" className="text-gray-900">Cancelled</option>
                  <option value="suspended" className="text-gray-900">Suspended</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Telegram Status</label>
                <select
                  value={telegramFilter}
                  onChange={(e) => setTelegramFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
                >
                  <option value="all" className="text-gray-900">All Telegram</option>
                  <option value="added" className="text-gray-900">Added</option>
                  <option value="pending_add" className="text-gray-900">Pending</option>
                  <option value="not_added" className="text-gray-900">Not Added</option>
                  <option value="failed_add" className="text-gray-900">Failed</option>
                </select>
              </div>
            </div>
          </div>

          {/* Subscriptions Table */}
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">User</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Plan</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Payment</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Telegram</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Access</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredSubscriptions.map((subscription) => (
                    <tr key={subscription.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{subscription.user_name || 'N/A'}</div>
                          <div className="text-sm text-gray-500">{subscription.user_email}</div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{subscription.plan_name}</div>
                          <div className="text-sm text-gray-500">{subscription.currency} {subscription.amount_paid}</div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {getStatusBadge(subscription.payment_status, 'payment')}
                      </td>
                      <td className="px-4 py-4">
                        <div className="space-y-1">
                          {getStatusBadge(subscription.subscription_status, 'subscription')}
                          {subscription.is_active && (
                            <div className="text-xs text-green-600">
                              {subscription.days_remaining} days left
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm text-gray-900">{subscription.telegram_username}</div>
                          {getStatusBadge(subscription.telegram_status, 'telegram')}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-green-600">
                          Lifetime Access
                        </div>
                        <div className="text-xs text-gray-500">
                          All Premium Courses
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => handleExtendSubscription(subscription.id)}
                          className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                        >
                          Manage
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}


      {/* Analytics Tab */}
      {activeTab === 'analytics' && analytics && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-green-600">{analytics.total_purchases}</div>
              <div className="text-sm text-gray-600">Total Purchases</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-blue-600">${analytics.monthly_revenue?.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Monthly Revenue</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-purple-600">${analytics.total_revenue?.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Total Revenue</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-orange-600">{analytics.recent_purchases_30d}</div>
              <div className="text-sm text-gray-600">Recent Purchases (30d)</div>
            </div>
          </div>

          {/* Telegram Status Distribution */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Telegram Status</h3>
            <div className="grid grid-cols-3 gap-4">
              {analytics.telegram_stats?.map((stat: any, index: number) => (
                <div key={index}>
                  <div className="text-lg font-medium text-gray-900">{stat.count}</div>
                  <div className="text-sm text-gray-600 capitalize">{stat.telegram_status || 'Not Connected'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}