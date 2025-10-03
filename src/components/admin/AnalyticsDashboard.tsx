'use client';

import { useState } from 'react';
import { SubscriptionAnalytics } from '@/types/subscription';
import RevenueChart from './charts/RevenueChart';
import PlanDistributionChart from './charts/PlanDistributionChart';
import PaymentStatusChart from './charts/PaymentStatusChart';

interface AnalyticsDashboardProps {
  analytics: SubscriptionAnalytics | null;
  loading: boolean;
  onRefresh: () => void;
}

export default function AnalyticsDashboard({
  analytics,
  loading,
  onRefresh
}: AnalyticsDashboardProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly'>('monthly');

  const formatCurrency = (amount: number | undefined | null) => {
    if (amount == null || isNaN(amount)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number | undefined | null) => {
    if (value == null || isNaN(value)) {
      return '0.0%';
    }
    return `${value.toFixed(1)}%`;
  };

  const formatNumber = (value: number | undefined | null) => {
    if (value == null || isNaN(value)) {
      return '0';
    }
    return value.toLocaleString();
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="h-8 bg-gray-200 rounded w-64"></div>
          <div className="h-8 bg-gray-200 rounded w-32"></div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 bg-gray-200 rounded"></div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                    <div className="h-6 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts area */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No analytics data</h3>
        <p className="mt-1 text-sm text-gray-500">Analytics data is not available at this time.</p>
        <div className="mt-6">
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Refresh Analytics
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">Subscription and revenue insights</p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Period Selector */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as 'daily' | 'weekly' | 'monthly')}
            className="block w-40 pl-3 pr-10 py-2 text-base text-gray-900 bg-white border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="daily">Daily View</option>
            <option value="weekly">Weekly View</option>
            <option value="monthly">Monthly View</option>
          </select>
          
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Revenue */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatCurrency(analytics.total_revenue)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <div className="text-sm">
              <span className={`font-medium ${(analytics.growth_rate || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {(analytics.growth_rate || 0) >= 0 ? '+' : ''}{formatPercentage(analytics.growth_rate)}
              </span>
              <span className="text-gray-500"> from last period</span>
            </div>
          </div>
        </div>

        {/* Total Subscriptions */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Subscriptions</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatNumber(analytics.total_subscriptions)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <div className="text-sm">
              <span className="font-medium text-blue-600">
                {formatNumber(analytics.new_subscriptions)} new
              </span>
              <span className="text-gray-500"> this period</span>
            </div>
          </div>
        </div>

        {/* Payment Success Rate */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Payment Success</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatPercentage(
                      analytics.total_subscriptions > 0 
                        ? (analytics.verified_payments / analytics.total_subscriptions) * 100 
                        : 0
                    )}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <div className="text-sm">
              <span className="font-medium text-green-600">
                {formatNumber(analytics.verified_payments)} verified
              </span>
              <span className="text-gray-500"> / {formatNumber(analytics.pending_payments)} pending</span>
            </div>
          </div>
        </div>

        {/* Telegram Success Rate */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Telegram Success</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatPercentage(analytics.telegram_success_rate)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-5 py-3">
            <div className="text-sm">
              <span className="font-medium text-purple-600">
                {formatNumber(analytics.telegram_additions)} added
              </span>
              <span className="text-gray-500"> / {formatNumber(analytics.telegram_failures)} failed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Plan Breakdown and Payment Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Plan Type Breakdown */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Plan Type Breakdown</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(analytics.plan_type_breakdown || {}).map(([planType, data]) => {
                const percentage = (analytics.total_subscriptions || 0) > 0 
                  ? ((data?.count || 0) / (analytics.total_subscriptions || 1)) * 100 
                  : 0;
                
                return (
                  <div key={planType} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-blue-500 mr-3"></div>
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {planType.replace('_', ' ')} Plan
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatNumber(data?.count)} ({formatPercentage(percentage)})
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatCurrency(data?.revenue || 0)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Payment Status Breakdown */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Payment Status</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-3"></div>
                  <span className="text-sm font-medium text-gray-900">Verified</span>
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {formatNumber(analytics.verified_payments)} ({formatPercentage(
                    (analytics.total_subscriptions || 0) > 0 
                      ? ((analytics.verified_payments || 0) / (analytics.total_subscriptions || 1)) * 100 
                      : 0
                  )})
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-yellow-500 mr-3"></div>
                  <span className="text-sm font-medium text-gray-900">Pending</span>
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {analytics.pending_payments} ({formatPercentage(
                    analytics.total_subscriptions > 0 
                      ? (analytics.pending_payments / analytics.total_subscriptions) * 100 
                      : 0
                  )})
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-red-500 mr-3"></div>
                  <span className="text-sm font-medium text-gray-900">Failed</span>
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {analytics.failed_payments} ({formatPercentage(
                    analytics.total_subscriptions > 0 
                      ? (analytics.failed_payments / analytics.total_subscriptions) * 100 
                      : 0
                  )})
                </div>
              </div>

              {analytics.refunded_amount > 0 && (
                <div className="pt-3 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">Total Refunded</span>
                    <span className="text-sm font-medium text-red-600">
                      {formatCurrency(analytics.refunded_amount)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Revenue and Subscription Trends */}
        <div className="bg-white shadow rounded-lg p-6">
          <RevenueChart 
            analytics={analytics}
            period={selectedPeriod}
          />
        </div>

        {/* Plan Distribution */}
        <div className="bg-white shadow rounded-lg p-6">
          <PlanDistributionChart 
            analytics={analytics}
          />
        </div>
      </div>

      {/* Payment Status Chart */}
      <div className="bg-white shadow rounded-lg p-6">
        <PaymentStatusChart 
          analytics={analytics}
        />
      </div>

      {/* Additional Metrics */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Additional Insights</h3>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Average Subscription Value</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {formatCurrency(analytics.average_subscription_value)}
              </dd>
            </div>
            
            <div>
              <dt className="text-sm font-medium text-gray-500">Renewal Rate</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {formatPercentage(
                  analytics.total_subscriptions > 0 
                    ? (analytics.renewed_subscriptions / analytics.total_subscriptions) * 100 
                    : 0
                )}
              </dd>
            </div>
            
            <div>
              <dt className="text-sm font-medium text-gray-500">Cancellation Rate</dt>
              <dd className="mt-1 text-2xl font-semibold text-gray-900">
                {formatPercentage(
                  analytics.total_subscriptions > 0 
                    ? (analytics.cancelled_subscriptions / analytics.total_subscriptions) * 100 
                    : 0
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}