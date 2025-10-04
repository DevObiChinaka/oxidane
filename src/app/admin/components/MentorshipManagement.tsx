'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '../contexts/AdminAuthContext';

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
  sessions_used: number;
  sessions_remaining: number;
  is_active: boolean;
  created_at: string;
}

interface OneOnOneSession {
  id: string;
  user_email: string;
  user_name: string;
  session_type: string;
  scheduled_datetime: string;
  duration_minutes: number;
  status: string;
  meeting_link?: string;
  physical_location?: string;
  phone_number?: string;
  admin_notified: boolean;
  session_notes?: string;
  created_at: string;
  completed_at?: string;
}

export default function MentorshipManagement() {
  const router = useRouter();
  const { isAuthenticated, user, loading: authLoading, logout } = useAdminAuth();
  const [subscriptions, setSubscriptions] = useState<MentorshipSubscription[]>([]);
  const [sessions, setSessions] = useState<OneOnOneSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'subscriptions' | 'sessions' | 'analytics'>('subscriptions');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sessionTypeFilter, setSessionTypeFilter] = useState('all');
  const [telegramFilter, setTelegramFilter] = useState('all');
  const [analytics, setAnalytics] = useState<any>(null);

  // Helper function to handle authentication errors
  const handleAuthError = (response: Response) => {
    if (response.status === 401) {
      console.log('🔒 Authentication failed, logging out...');
      logout(); // Use the logout method from AdminAuthContext
      return true; // Indicates auth error was handled
    }
    return false; // Not an auth error
  };

  useEffect(() => {
    // Only fetch data if user is authenticated
    if (isAuthenticated && !authLoading) {
      fetchData();
    }
  }, [isAuthenticated, authLoading]);

  // Handle authentication redirects
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      console.log('🔒 Not authenticated, redirecting to login...');
      router.push('/admin/login');
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use Django backend URL (port 8000) instead of Next.js frontend (port 3000)
      const baseUrl = 'http://localhost:8000';
      
      if (activeTab === 'subscriptions') {
        const response = await fetch(`${baseUrl}/api/admin/mentorship/subscriptions/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          console.error('Response status:', response.status);
          console.error('Response URL:', response.url);
          
          // Handle authentication errors
          if (response.status === 401) {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            window.location.href = '/admin/login';
            return;
          }
          
          throw new Error(`HTTP error! status: ${response.status} - URL: ${response.url}`);
        }
        
        const data = await response.json();
        console.log('Subscriptions API response:', data);
        if (data.success) {
          setSubscriptions(data.subscriptions || []);
        } else {
          throw new Error(data.error || 'Failed to fetch subscriptions');
        }
      } else if (activeTab === 'sessions') {
        const response = await fetch(`${baseUrl}/api/admin/mentorship/sessions/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          if (handleAuthError(response)) return;
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
          setSessions(data.sessions || []);
        } else {
          throw new Error(data.error || 'Failed to fetch sessions');
        }
      } else if (activeTab === 'analytics') {
        const response = await fetch(`${baseUrl}/api/admin/mentorship/analytics/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          if (handleAuthError(response)) return;
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
          setAnalytics(data.analytics);
        } else {
          throw new Error(data.error || 'Failed to fetch analytics');
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
      
      // For development: Add mock data when API is not available
      if (activeTab === 'subscriptions') {
        console.log('Loading mock subscription data for development...');
        setSubscriptions([
          {
            id: '1',
            user_email: 'john@example.com',
            user_name: 'John Doe',
            plan_name: 'Premium Mentorship + 1-on-1',
            plan_type: 'mentorship_premium',
            amount_paid: 799.00,
            currency: 'USD',
            payment_status: 'verified',
            subscription_status: 'active',
            subscription_start: new Date().toISOString(),
            subscription_end: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(), // 90 days from now
            days_remaining: 85,
            telegram_username: '@johndoe',
            telegram_status: 'added',
            sessions_used: 1,
            sessions_remaining: 2,
            is_active: true,
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            user_email: 'jane@example.com',
            user_name: 'Jane Smith',
            plan_name: 'Basic Mentorship',
            plan_type: 'mentorship_basic',
            amount_paid: 299.00,
            currency: 'USD',
            payment_status: 'verified',
            subscription_status: 'active',
            subscription_start: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(), // 45 days ago
            subscription_end: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(), // 45 days from now
            days_remaining: 45,
            telegram_username: '@janesmith',
            telegram_status: 'pending_add',
            sessions_used: 0,
            sessions_remaining: 0,
            is_active: true,
            created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
          }
        ]);
      } else if (activeTab === 'sessions') {
        console.log('Loading mock session data for development...');
        setSessions([
          {
            id: '1',
            user_email: 'john@example.com',
            user_name: 'John Doe',
            session_type: 'virtual',
            scheduled_datetime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
            duration_minutes: 60,
            status: 'scheduled',
            meeting_link: 'https://zoom.us/j/123456789',
            physical_location: '',
            phone_number: '',
            admin_notified: false,
            session_notes: '',
            created_at: new Date().toISOString(),
            completed_at: undefined,
          },
          {
            id: '2',
            user_email: 'alice@example.com',
            user_name: 'Alice Johnson',
            session_type: 'physical',
            scheduled_datetime: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // In 3 days
            duration_minutes: 90,
            status: 'scheduled',
            meeting_link: '',
            physical_location: 'Office Building, 123 Main St, Room 301',
            phone_number: '',
            admin_notified: false,
            session_notes: '',
            created_at: new Date().toISOString(),
            completed_at: undefined,
          }
        ]);
      } else if (activeTab === 'analytics') {
        console.log('Loading mock analytics data for development...');
        setAnalytics({
          active_subscriptions: 15,
          monthly_revenue: 8500.00,
          total_sessions: 45,
          completed_sessions: 38,
          upcoming_sessions: 7,
          physical_sessions_pending_notification: 2,
          plan_distribution: [
            { name: 'Premium Mentorship + 1-on-1', count: 8 },
            { name: 'Basic Mentorship', count: 7 }
          ],
          telegram_stats: [
            { telegram_status: 'added', count: 12 },
            { telegram_status: 'pending_add', count: 3 }
          ]
        });
      }
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
        const baseUrl = 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/admin/mentorship/extend/${subscriptionId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          },
          body: JSON.stringify({
            extend_days: parseInt(days),
            reason: reason
          })
        });
        
        if (!response.ok) {
          if (handleAuthError(response)) return;
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.success) {
          alert('Subscription extended successfully!');
          fetchData();
        } else {
          alert('Failed to extend subscription: ' + data.error);
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

  const filteredSessions = sessions.filter(session => {
    const matchesSearch = session.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.user_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;
    const matchesType = sessionTypeFilter === 'all' || session.session_type === sessionTypeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
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
            <h1 className="text-2xl font-bold text-gray-800">Mentorship Management</h1>
            <p className="mt-1 text-sm text-gray-600">Manage mentorship subscriptions, sessions, and analytics</p>
          </div>
        </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'subscriptions', label: '👥 Subscriptions', count: subscriptions.length },
            { key: 'sessions', label: '📅 1-on-1 Sessions', count: sessions.length },
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
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Sessions</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Expires</th>
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
                        <div className="text-sm text-gray-900">
                          {subscription.sessions_used} / {subscription.sessions_used + subscription.sessions_remaining} used
                        </div>
                        <div className="text-xs text-gray-500">
                          {subscription.sessions_remaining} remaining
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {subscription.subscription_end ? new Date(subscription.subscription_end).toLocaleDateString() : 'N/A'}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => handleExtendSubscription(subscription.id)}
                          className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                        >
                          Extend
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

      {/* Sessions Tab */}
      {activeTab === 'sessions' && (
        <div className="space-y-4">
          {/* Session Controls */}
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-1">
                <label className="block text-sm font-medium text-gray-900 mb-2">Search Sessions</label>
                <input
                  type="text"
                  placeholder="Search by user email or name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Session Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
                >
                  <option value="all" className="text-gray-900">All Sessions</option>
                  <option value="scheduled" className="text-gray-900">Scheduled</option>
                  <option value="completed" className="text-gray-900">Completed</option>
                  <option value="cancelled" className="text-gray-900">Cancelled</option>
                  <option value="no_show" className="text-gray-900">No Show</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Session Type</label>
                <select
                  value={sessionTypeFilter}
                  onChange={(e) => setSessionTypeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
                >
                  <option value="all" className="text-gray-900">All Types</option>
                  <option value="virtual" className="text-gray-900">Virtual</option>
                  <option value="physical" className="text-gray-900">Physical</option>
                  <option value="phone" className="text-gray-900">Phone</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">User</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Type</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Scheduled</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Details</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Admin Alert</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredSessions.map((session) => (
                    <tr key={session.id} className={`hover:bg-gray-50 ${session.session_type === 'physical' && !session.admin_notified ? 'bg-yellow-50' : ''}`}>
                      <td className="px-4 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{session.user_name}</div>
                          <div className="text-sm text-gray-500">{session.user_email}</div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          session.session_type === 'physical' ? 'bg-purple-100 text-purple-800' :
                          session.session_type === 'virtual' ? 'bg-blue-100 text-blue-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {session.session_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {new Date(session.scheduled_datetime).toLocaleDateString()}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(session.scheduled_datetime).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {getStatusBadge(session.status, 'session')}
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {session.duration_minutes} minutes
                        </div>
                        {session.meeting_link && (
                          <div className="text-xs text-blue-600 truncate max-w-32">
                            {session.meeting_link}
                          </div>
                        )}
                        {session.physical_location && (
                          <div className="text-xs text-gray-600 truncate max-w-32">
                            📍 {session.physical_location}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        {session.session_type === 'physical' && (
                          <div className={`text-xs ${session.admin_notified ? 'text-green-600' : 'text-red-600 font-medium'}`}>
                            {session.admin_notified ? '✅ Notified' : '🚨 NEEDS ATTENTION'}
                          </div>
                        )}
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
              <div className="text-2xl font-bold text-green-600">{analytics.active_subscriptions}</div>
              <div className="text-sm text-gray-600">Active Subscriptions</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-blue-600">${analytics.monthly_revenue?.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Monthly Revenue</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-purple-600">{analytics.upcoming_sessions}</div>
              <div className="text-sm text-gray-600">Upcoming Sessions</div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="text-2xl font-bold text-orange-600">{analytics.physical_sessions_pending_notification}</div>
              <div className="text-sm text-gray-600">Physical Sessions Pending</div>
            </div>
          </div>

          {/* More detailed analytics can be added here */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Statistics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-lg font-medium text-gray-900">{analytics.total_sessions}</div>
                <div className="text-sm text-gray-600">Total Sessions</div>
              </div>
              <div>
                <div className="text-lg font-medium text-green-600">{analytics.completed_sessions}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </div>
              <div>
                <div className="text-lg font-medium text-yellow-600">
                  {((analytics.completed_sessions / analytics.total_sessions) * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Completion Rate</div>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}