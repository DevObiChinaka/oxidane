'use client';

import { PaymentAnalytics } from '../../types/payment';
import { 
  BanknotesIcon, 
  CreditCardIcon, 
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface PaymentAnalyticsDashboardProps {
  analytics: PaymentAnalytics | null;
  loading: boolean;
}

export default function PaymentAnalyticsDashboard({ analytics, loading }: PaymentAnalyticsDashboardProps) {
  
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-sm text-gray-500">Loading analytics...</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
        <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No analytics data</h3>
        <p className="mt-1 text-sm text-gray-500">Analytics data is not available at the moment.</p>
      </div>
    );
  }

  // Safe access with default values to prevent runtime errors
  const safeAnalytics = {
    total_revenue: analytics.total_revenue || 0,
    monthly_revenue: analytics.monthly_revenue || 0,
    success_rate: analytics.success_rate || 0,
    revenue_growth_percentage: analytics.revenue_growth_percentage || 0,
    trends: {
      revenue_trend: analytics.trends?.revenue_trend || 'stable' as const,
      success_rate_trend: analytics.trends?.success_rate_trend || 'stable' as const,
    },
    verified_payments: analytics.verified_payments || 0,
    pending_payments: analytics.pending_payments || 0,
    failed_payments: analytics.failed_payments || 0,
    refunded_payments: analytics.refunded_payments || 0,
    total_transactions: analytics.total_transactions || 1, // Prevent division by zero
    payment_methods: analytics.payment_methods || [],
    plan_performance: analytics.plan_performance || [],
    daily_stats: analytics.daily_stats || [],
    avg_processing_time: analytics.avg_processing_time,
    fastest_processing_time: analytics.fastest_processing_time,
    slowest_processing_time: analytics.slowest_processing_time,
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
      case 'improving':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'decreasing':
      case 'declining':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <ArrowPathIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing':
      case 'improving':
        return 'text-green-600';
      case 'decreasing':
      case 'declining':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Revenue Overview */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Revenue Overview</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Total Revenue</p>
                <p className="text-2xl font-bold text-green-900">${safeAnalytics.total_revenue.toLocaleString()}</p>
                <div className="flex items-center mt-2">
                  {getTrendIcon(safeAnalytics.trends.revenue_trend)}
                  <span className={`ml-1 text-sm ${getTrendColor(safeAnalytics.trends.revenue_trend)}`}>
                    {safeAnalytics.revenue_growth_percentage > 0 ? '+' : ''}{safeAnalytics.revenue_growth_percentage}%
                  </span>
                </div>
              </div>
              <BanknotesIcon className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Monthly Revenue</p>
                <p className="text-2xl font-bold text-blue-900">${safeAnalytics.monthly_revenue.toLocaleString()}</p>
                <p className="text-sm text-blue-700 mt-2">This month</p>
              </div>
              <CreditCardIcon className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Success Rate</p>
                <p className="text-2xl font-bold text-purple-900">{safeAnalytics.success_rate.toFixed(1)}%</p>
                <div className="flex items-center mt-2">
                  {getTrendIcon(safeAnalytics.trends.success_rate_trend)}
                  <span className={`ml-1 text-sm ${getTrendColor(safeAnalytics.trends.success_rate_trend)}`}>
                    {safeAnalytics.trends.success_rate_trend}
                  </span>
                </div>
              </div>
              <ChartBarIcon className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Transaction Status Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Transaction Status</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium text-gray-700">Verified</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-gray-900">{safeAnalytics.verified_payments}</span>
                <span className="text-xs text-gray-500 ml-1">
                  ({((safeAnalytics.verified_payments / safeAnalytics.total_transactions) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium text-gray-700">Pending</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-gray-900">{safeAnalytics.pending_payments}</span>
                <span className="text-xs text-gray-500 ml-1">
                  ({((safeAnalytics.pending_payments / safeAnalytics.total_transactions) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                <span className="text-sm font-medium text-gray-700">Failed</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-gray-900">{safeAnalytics.failed_payments}</span>
                <span className="text-xs text-gray-500 ml-1">
                  ({((safeAnalytics.failed_payments / safeAnalytics.total_transactions) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>

            {safeAnalytics.refunded_payments > 0 && (
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-purple-500 rounded-full mr-3"></div>
                  <span className="text-sm font-medium text-gray-700">Refunded</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-gray-900">{safeAnalytics.refunded_payments}</span>
                  <span className="text-xs text-gray-500 ml-1">
                    ({((safeAnalytics.refunded_payments / safeAnalytics.total_transactions) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Payment Methods */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Methods</h3>
          
          <div className="space-y-3">
            {safeAnalytics.payment_methods.length > 0 ? safeAnalytics.payment_methods.map((method, index) => (
              <div key={method.method} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <CreditCardIcon className="h-4 w-4 text-gray-400 mr-3" />
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {method.method.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-gray-900">{method.count}</div>
                  <div className="text-xs text-gray-500">
                    ${method.total_amount.toLocaleString()} • {method.success_rate.toFixed(1)}% success
                  </div>
                </div>
              </div>
            )) : (
              <div className="text-center text-gray-500 py-4">
                <p>No payment method data available</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Plan Performance */}
      {safeAnalytics.plan_performance && safeAnalytics.plan_performance.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Plan Performance</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {safeAnalytics.plan_performance.map((plan) => (
              <div key={plan.plan_type} className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-sm font-medium text-gray-900 capitalize">
                    {plan.plan_type.replace('_', ' ')}
                  </h4>
                  <span className="text-xs text-gray-500">
                    {plan.success_rate.toFixed(1)}% success
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Transactions:</span>
                    <span className="text-sm font-medium">{plan.count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Revenue:</span>
                    <span className="text-sm font-medium">${plan.revenue.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Daily Revenue Chart */}
      {safeAnalytics.daily_stats && safeAnalytics.daily_stats.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Revenue Trend</h3>
          
          <div className="space-y-2">
            {safeAnalytics.daily_stats.slice(-7).map((stat) => (
              <div key={stat.date} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <span className="text-sm text-gray-600">
                  {new Date(stat.date).toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </span>
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium">${stat.revenue.toLocaleString()}</span>
                  <span className="text-xs text-gray-500">{stat.transactions} txns</span>
                  <div className="w-16 h-2 bg-gray-200 rounded-full">
                    <div 
                      className="h-2 bg-blue-500 rounded-full" 
                      style={{ 
                        width: `${Math.min(stat.success_rate, 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Metrics */}
      {safeAnalytics.avg_processing_time && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Metrics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">Average Processing Time</p>
              <p className="text-xl font-bold text-blue-900">{safeAnalytics.avg_processing_time}</p>
            </div>
            
            {safeAnalytics.fastest_processing_time && (
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Fastest Processing</p>
                <p className="text-xl font-bold text-green-900">{safeAnalytics.fastest_processing_time}</p>
              </div>
            )}
            
            {safeAnalytics.slowest_processing_time && (
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600">Slowest Processing</p>
                <p className="text-xl font-bold text-red-900">{safeAnalytics.slowest_processing_time}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}