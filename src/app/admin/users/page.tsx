'use client';

import React, { useState, useEffect } from 'react';
import { useUsers, useUsersAnalytics, useUserActions, useUserDetail } from '../hooks/useAdminAPI';
import { useAdminAuth } from '../contexts/AdminAuthContext';

// Types
interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  display_name: string;
  has_oauth: boolean;
  oauth_provider: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  signal_subscriptions_count: number;
  active_signal_subscriptions_count: number;
  latest_signal_subscription: {
    plan_type: string;
    subscription_end: string | null;
    telegram_status: string;
  } | null;
  days_since_registration: number;
  days_since_last_login: number | null;
}

interface UserDetail extends User {
  avatar: string | null;
  display_name: string;
  subscription_history: Array<{
    id: string;
    plan_type: string;
    amount_paid: number;
    currency: string;
    payment_status: string;
    telegram_username: string;
    telegram_status: string;
    subscription_start: string | null;
    subscription_end: string | null;
    created_at: string;
    paystack_reference: string;
  }>;
  oauth_providers: Array<{
    provider: string;
    provider_user_id: string;
    created_at: string;
  }>;
  metrics: {
    days_since_registration: number;
    days_since_last_login: number | null;
    total_subscriptions: number;
    active_subscriptions: number;
    total_paid: number;
    has_oauth: boolean;
  };
}

interface UsersResponse {
  users: User[];
  pagination: {
    current_page: number;
    per_page: number;
    total_pages: number;
    total_users: number;
    has_previous: boolean;
    has_next: boolean;
  };
  filters: {
    search: string;
    status: string;
    subscription: string;
    date_from: string | null;
    date_to: string | null;
  };
}

interface UsersAnalytics {
  summary: {
    total_users: number;
    active_users: number;
    verified_users: number;
    staff_users: number;
    verification_rate: number;
    active_rate: number;
  };
  growth: {
    new_users_30d: number;
    new_users_7d: number;
    recent_logins_7d: number;
  };
  subscriptions: {
    active_signal_subscriptions: number;
    subscription_rate: number;
  };
}

// Utility functions
function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Invalid Date';
  }
}

function formatDateShort(dateString: string | null): string {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    return 'Invalid';
  }
}

// Components
interface UserActionsProps {
  user: User;
  onAction: (userId: string, action: string) => void;
  isLoading: boolean;
}

function UserActions({ user, onAction, isLoading }: UserActionsProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  const actions = [
    {
      id: 'activate',
      label: user.is_active ? 'Deactivate User' : 'Activate User',
      icon: user.is_active ? '🚫' : '✅',
      action: user.is_active ? 'deactivate' : 'activate',
      danger: user.is_active
    },
    {
      id: 'verify_email',
      label: 'Verify Email',
      icon: '📧',
      action: 'verify_email',
      disabled: user.is_email_verified
    },
    {
      id: 'staff',
      label: user.is_staff ? 'Remove Staff' : 'Make Staff',
      icon: user.is_staff ? '👤' : '👨‍💼',
      action: user.is_staff ? 'remove_staff' : 'make_staff',
      disabled: user.is_superuser
    }
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        disabled={isLoading}
        className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
      >
        <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01" />
        </svg>
      </button>

      {showDropdown && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
            <div className="py-1">
              {actions.map((action) => (
                <button
                  key={action.id}
                  onClick={() => {
                    onAction(user.id, action.action);
                    setShowDropdown(false);
                  }}
                  disabled={action.disabled || isLoading}
                  className={`w-full text-left px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    action.danger 
                      ? 'text-red-700 hover:bg-red-50 hover:text-red-800' 
                      : 'text-gray-900 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <span className="mr-2">{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

interface UserDetailModalProps {
  userId: string | null;
  onClose: () => void;
}

function UserDetailModal({ userId, onClose }: UserDetailModalProps) {
  const { data: user, loading, error } = useUserDetail(userId);

  // Debug logging
  React.useEffect(() => {
    if (user) {
      console.log('🔍 User Detail Modal Data:', {
        user,
        fullName: user.full_name,
        displayName: user.display_name,
        firstName: user.first_name,
        lastName: user.last_name,
        email: user.email,
        username: user.username,
        createdAt: user.created_at
      });
    }
  }, [user]);

  if (!userId) return null;

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-gray-100 max-w-5xl w-full max-h-[90vh] overflow-hidden">
        <div className="sticky top-0 bg-white border-b-2 border-brand-navy px-8 py-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">User Profile</h2>
            <p className="text-gray-600 text-sm mt-1">Comprehensive user information and activity</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-gray-800"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-96px)]">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="relative">
                <div className="animate-spin rounded-full h-12 w-12 border-3 border-gray-200"></div>
                <div className="animate-spin rounded-full h-12 w-12 border-3 border-brand-teal border-t-transparent absolute top-0 left-0"></div>
              </div>
              <p className="text-gray-600 mt-4 font-medium">Loading user details...</p>
            </div>
          )}

          {error && (
            <div className="m-8">
              <div className="bg-red-50 border-l-4 border-red-400 rounded-r-lg p-6">
                <div className="flex">
                  <svg className="w-6 h-6 text-red-400 mr-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="text-red-800 font-semibold text-lg">Unable to Load User Details</h3>
                    <p className="text-red-600 text-sm mt-2 leading-relaxed">{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {user && (
            <div className="px-8 py-6 space-y-8">
              {/* User Header Card */}
              <div className="relative bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
                <div className="absolute top-6 right-6">
                  {user.has_oauth ? (
                    <div className="flex items-center gap-2 bg-blue-50 px-3 py-1.5 rounded-md border border-blue-200">
                      <div className="w-5 h-5 rounded-full bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                        <svg className="w-3 h-3" viewBox="0 0 24 24">
                          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                      </div>
                      <span className="text-xs font-semibold text-blue-700 capitalize">{user.oauth_provider}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-md border border-gray-200">
                      <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span className="text-xs font-semibold text-gray-700">Standard</span>
                    </div>
                  )}
                </div>

                <div className="flex items-start gap-6">
                  <div className="w-20 h-20 bg-brand-navy rounded-xl flex items-center justify-center shadow-sm">
                    <span className="text-2xl font-bold text-white">
                      {(user.display_name || user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="flex-1">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                      {user.display_name || user.full_name || user.username || 'Unknown User'}
                    </h1>
                    <p className="text-gray-600 text-lg mb-4">{user.email}</p>
                    
                    <div className="flex flex-wrap gap-3">
                      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium ${
                        user.is_active 
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        <div className={`w-2 h-2 rounded-sm ${user.is_active ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                        {user.is_active ? 'Active Account' : 'Inactive Account'}
                      </div>
                      
                      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium ${
                        user.is_email_verified 
                          ? 'bg-brand-teal bg-opacity-10 text-brand-teal border border-brand-teal border-opacity-30' 
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        <div className={`w-2 h-2 rounded-sm ${user.is_email_verified ? 'bg-brand-teal' : 'bg-amber-500'}`}></div>
                        {user.is_email_verified ? 'Email Verified' : 'Email Unverified'}
                      </div>
                      
                      {user.is_staff && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium bg-brand-navy bg-opacity-10 text-brand-navy border border-brand-navy border-opacity-30">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-.257-.257A6 6 0 0118 8zM2 8a6 6 0 1010.743 5.743L12 14l-.257-.257A6 6 0 012 8zm8-2a2 2 0 100 4 2 2 0 000-4z" clipRule="evenodd" />
                          </svg>
                          Staff Member
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-blue-600">{user.signal_subscriptions_count || 0}</div>
                  <p className="text-blue-700 font-medium mt-1">Total Subscriptions</p>
                </div>
                
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-emerald-600">{user.active_signal_subscriptions_count || 0}</div>
                  <p className="text-emerald-700 font-medium mt-1">Active Subscriptions</p>
                </div>
                
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    ${user.latest_signal_subscription?.amount_paid || '0.00'}
                  </div>
                  <p className="text-purple-700 font-medium mt-1">Total Paid</p>
                </div>
                
                <div className="bg-teal-50 border border-teal-200 rounded-xl p-6 text-center">
                  <div className="text-3xl font-bold text-teal-600">
                    {user.created_at ? Math.floor((new Date().getTime() - new Date(user.created_at).getTime()) / (1000 * 60 * 60 * 24)) : 0}
                  </div>
                  <p className="text-teal-700 font-medium mt-1">Days Since Registration</p>
                </div>
              </div>

              {/* Detailed Information Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Account Details
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Username</span>
                      <span className="text-gray-800">{user.username || 'Not set'}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Registration</span>
                      <span className="text-gray-800">{formatDate(user.created_at)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-gray-600 font-medium">Last Login</span>
                      <span className="text-gray-800">{user.last_login ? formatDate(user.last_login) : <span className="text-gray-500 italic">Never logged in</span>}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Activity Summary
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Active Subscriptions</span>
                      <span className="text-gray-800 font-semibold">{user.active_signal_subscriptions_count || 0}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Total Subscriptions</span>
                      <span className="text-gray-800">{user.signal_subscriptions_count || 0}</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-gray-600 font-medium">Latest Plan</span>
                      <span className="text-gray-800 capitalize">{user.latest_signal_subscription?.plan_type?.replace('_', ' ') || 'None'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Subscription History */}
              {user.subscription_history.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                      </svg>
                      Subscription History
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Period</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Telegram</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {user.subscription_history.map((sub: any) => (
                            <tr key={sub.id}>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <div className="w-2 h-2 rounded-full bg-brand-teal"></div>
                                  <span className="text-sm font-medium text-brand-teal capitalize">
                                    {sub.plan_type.replace('_', ' ')}
                                  </span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                                {sub.amount_paid} {sub.currency}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                {formatDateShort(sub.subscription_start)} - {formatDateShort(sub.subscription_end)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                <div>
                                  <div className="font-medium text-gray-800">@{sub.telegram_username}</div>
                                  <div className="flex items-center gap-1.5 mt-1">
                                    <div className={`w-1.5 h-1.5 rounded-full ${
                                      sub.telegram_status === 'added' ? 'bg-emerald-400' : 
                                      sub.telegram_status === 'pending_add' ? 'bg-amber-400' : 'bg-red-400'
                                    }`}></div>
                                    <span className={`text-xs font-medium ${
                                      sub.telegram_status === 'added' ? 'text-emerald-600' : 
                                      sub.telegram_status === 'pending_add' ? 'text-amber-600' : 'text-red-600'
                                    }`}>
                                      {sub.telegram_status === 'added' ? 'Added to Group' :
                                       sub.telegram_status === 'pending_add' ? 'Pending Addition' :
                                       sub.telegram_status === 'removed' ? 'Removed' : 'Failed to Add'}
                                    </span>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <div className={`w-2 h-2 rounded-full ${
                                    sub.payment_status === 'verified' ? 'bg-emerald-400' :
                                    sub.payment_status === 'pending' ? 'bg-amber-400' :
                                    'bg-red-400'
                                  }`}></div>
                                  <span className={`text-sm font-medium ${
                                    sub.payment_status === 'verified' ? 'text-emerald-700' :
                                    sub.payment_status === 'pending' ? 'text-amber-600' :
                                    'text-red-600'
                                  }`}>
                                    {sub.payment_status === 'verified' ? 'Verified' :
                                     sub.payment_status === 'pending' ? 'Pending' : 'Failed'}
                                  </span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* OAuth Providers */}
              {user.oauth_providers.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      Connected Accounts
                    </h3>
                  </div>
                  <div className="p-6 space-y-4">
                    {user.oauth_providers.map((provider: any, index: number) => (
                      <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:bg-gray-100 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-xl bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                            {provider.provider === 'google' ? (
                              <svg className="w-6 h-6" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                              </svg>
                            ) : (
                              <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M13.5 2L8.5 7H11V16H13V7H15.5L13.5 2Z M19 19H5V21H19V19Z"/>
                              </svg>
                            )}
                          </div>
                          <div>
                            <div className="font-semibold text-gray-900 text-lg capitalize">{provider.provider}</div>
                            <div className="text-sm text-gray-600">Connected on {formatDateShort(provider.created_at)}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1.5 rounded-md border border-emerald-200">
                          <div className="w-2 h-2 bg-emerald-500 rounded-sm"></div>
                          <span className="text-sm font-medium text-emerald-700">Connected</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Footer Info */}
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
                <p className="text-sm text-gray-600">
                  User ID: <span className="font-mono font-medium text-gray-800">{user.id}</span>
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Profile last updated: {formatDate(user.updated_at || user.created_at)}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Main component
export default function UsersPage() {
  const { isAuthenticated, loading: authLoading } = useAdminAuth();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  
  // Filter states
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [subscriptionFilter, setSubscriptionFilter] = useState('');

  // Build params for the API call
  const usersParams = {
    page: currentPage,
    per_page: perPage,
    ...(search && { search }),
    ...(statusFilter && { status: statusFilter }),
    ...(subscriptionFilter && { subscription: subscriptionFilter })
  };

  // Use hooks for data fetching
  const { data: usersData, loading: usersLoading, error: usersError, refetch: refetchUsers } = useUsers(usersParams);
  const { data: analytics, loading: analyticsLoading, refetch: refetchAnalytics } = useUsersAnalytics();
  const { performAction, loading: actionLoading } = useUserActions();

  // Handle user actions
  const handleUserAction = async (userId: string, action: string) => {
    try {
      await performAction(userId, action);
      
      // Refresh data
      refetchUsers();
      refetchAnalytics();
      
      console.log('Action completed successfully');
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  // Show loading if authentication is still being checked
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand-teal border-t-transparent"></div>
      </div>
    );
  }

  // Redirect if not authenticated (this should be handled by AdminLayoutWrapper, but just in case)
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600">Please log in to access the admin panel.</p>
        </div>
      </div>
    );
  }

  // Extract data from the hooks
  const users = usersData?.users || [];
  const pagination = usersData?.pagination || null;
  const loading = usersLoading;
  const error = usersError;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">User Management</h1>
          <p className="text-gray-600">Manage user accounts, subscriptions, and access</p>
        </div>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-xl">👥</span>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Total Users</h3>
                <p className="text-2xl font-semibold text-gray-900">{analytics.summary.total_users.toLocaleString()}</p>
                <p className="text-sm text-green-600">{analytics.growth.new_users_7d} new this week</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-xl">✅</span>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Verified Users</h3>
                <p className="text-2xl font-semibold text-gray-900">{analytics.summary.verified_users.toLocaleString()}</p>
                <p className="text-sm text-gray-600">{analytics.summary.verification_rate.toFixed(1)}% verification rate</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-xl">📡</span>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Active Subscriptions</h3>
                <p className="text-2xl font-semibold text-gray-900">{analytics.subscriptions.active_signal_subscriptions}</p>
                <p className="text-sm text-gray-600">{analytics.subscriptions.subscription_rate.toFixed(1)}% conversion</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-teal-100 rounded-lg">
                <span className="text-xl">🔄</span>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Recent Activity</h3>
                <p className="text-2xl font-semibold text-gray-900">{analytics.growth.recent_logins_7d}</p>
                <p className="text-sm text-gray-600">logins this week</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search by email or name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white placeholder-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
            >
              <option value="" className="text-gray-900">All Users</option>
              <option value="active" className="text-gray-900">Active</option>
              <option value="inactive" className="text-gray-900">Inactive</option>
              <option value="verified" className="text-gray-900">Verified</option>
              <option value="unverified" className="text-gray-900">Unverified</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Subscriptions</label>
            <select
              value={subscriptionFilter}
              onChange={(e) => {
                setSubscriptionFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
            >
              <option value="" className="text-gray-900">All Subscriptions</option>
              <option value="has_signals" className="text-gray-900">Has Signal Subscription</option>
              <option value="has_courses" className="text-gray-900">Has Course Access</option>
              <option value="none" className="text-gray-900">No Subscriptions</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Per Page</label>
            <select
              value={perPage}
              onChange={(e) => {
                setPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent text-gray-900 bg-white"
            >
              <option value={10} className="text-gray-900">10</option>
              <option value={25} className="text-gray-900">25</option>
              <option value={50} className="text-gray-900">50</option>
              <option value={100} className="text-gray-900">100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 className="text-red-800 font-medium">Error</h3>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden relative">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand-teal border-t-transparent"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Auth Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registration</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subscriptions</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user: User) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="font-semibold text-gray-800">{user.display_name || user.full_name || user.username}</div>
                          <div className="text-sm text-gray-600">{user.email}</div>
                          <div className="flex items-center gap-2 mt-1">
                            <div className={`w-1.5 h-1.5 rounded-full ${
                              user.is_active ? 'bg-emerald-400' : 'bg-red-400'
                            }`}></div>
                            <span className={`text-xs ${
                              user.is_active ? 'text-emerald-600' : 'text-red-600'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                            {user.is_staff && (
                              <>
                                <span className="text-xs text-gray-400">•</span>
                                <span className="text-xs text-brand-navy font-medium">Staff</span>
                              </>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.has_oauth ? (
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                              {user.oauth_provider === 'google' ? (
                                <svg className="w-3 h-3" viewBox="0 0 24 24">
                                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                </svg>
                              ) : (
                                <svg className="w-3 h-3 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-.257-.257A6 6 0 0118 8z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-700 capitalize">{user.oauth_provider}</div>
                              <div className="text-xs text-gray-500">OAuth Login</div>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">
                              <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-700">Standard</div>
                              <div className="text-xs text-gray-500">Email/Password</div>
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {formatDateShort(user.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {user.last_login ? formatDateShort(user.last_login) : (
                          <span className="text-gray-500">Never</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700">
                          <div>Signals: <span className="font-medium">{user.active_signal_subscriptions_count}</span>/{user.signal_subscriptions_count}</div>
                          {user.latest_signal_subscription && (
                            <div className="text-xs text-gray-500 mt-0.5">
                              {user.latest_signal_subscription.plan_type} - {user.latest_signal_subscription.telegram_status}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedUserId(user.id)}
                            className="text-brand-teal hover:text-brand-cyan transition-colors"
                          >
                            View Details
                          </button>
                          <UserActions
                            user={user}
                            onAction={handleUserAction}
                            isLoading={actionLoading}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && pagination.total_pages > 1 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={!pagination.has_previous}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(pagination.total_pages, currentPage + 1))}
                    disabled={!pagination.has_next}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing <span className="font-medium">{((currentPage - 1) * perPage) + 1}</span> to{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * perPage, pagination.total_users)}
                      </span>{' '}
                      of <span className="font-medium">{pagination.total_users}</span> users
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={!pagination.has_previous}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">Previous</span>
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </button>

                      {/* Page numbers */}
                      {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                        let pageNum;
                        if (pagination.total_pages <= 5) {
                          pageNum = i + 1;
                        } else {
                          const start = Math.max(1, currentPage - 2);
                          const end = Math.min(pagination.total_pages, start + 4);
                          pageNum = start + i;
                          if (pageNum > end) return null;
                        }

                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              currentPage === pageNum
                                ? 'z-10 bg-brand-teal border-brand-teal text-white'
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}

                      <button
                        onClick={() => setCurrentPage(Math.min(pagination.total_pages, currentPage + 1))}
                        disabled={!pagination.has_next}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">Next</span>
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* User Detail Modal */}
      <UserDetailModal
        userId={selectedUserId}
        onClose={() => setSelectedUserId(null)}
      />
    </div>
  );
}