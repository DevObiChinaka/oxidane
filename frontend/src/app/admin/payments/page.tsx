'use client';

import { useState } from 'react';
import { 
  CreditCardIcon, 
  BanknotesIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

// Simple mock data for testing
const mockPayments = [
  {
    id: '1',
    user_email: 'john@example.com',
    user_name: 'John Doe',
    amount: 29.99,
    currency: 'USD',
    status: 'verified',
    payment_method: 'card',
    transaction_type: 'subscription',
    created_at: new Date().toISOString(),
    reference: 'PAY_12345'
  },
  {
    id: '2',
    user_email: 'jane@example.com',
    user_name: 'Jane Smith',
    amount: 49.99,
    currency: 'USD',
    status: 'pending',
    payment_method: 'bank_transfer',
    transaction_type: 'subscription',
    created_at: new Date().toISOString(),
    reference: 'PAY_67890'
  }
];

const mockAnalytics = {
  total_revenue: 15420.50,
  verified_payments: 145,
  pending_payments: 12,
  failed_payments: 8,
  revenue_growth_percentage: 12.5,
  success_rate: 94.2,
  payment_methods: [
    { method: 'card', count: 120, total_amount: 12000, success_rate: 96.5 },
    { method: 'bank_transfer', count: 45, total_amount: 3420, success_rate: 89.2 }
  ]
};

export default function PaymentsManagement() {
  // View mode state
  const [viewMode, setViewMode] = useState<'table' | 'analytics'>('table');
  
  // Mock loading states
  const [loading] = useState(false);
  const [error] = useState<string | null>(null);

  // Quick stats
  const quickStats = [
    {
      name: 'Total Revenue',
      value: `$${mockAnalytics.total_revenue.toLocaleString()}`,
      change: `+${mockAnalytics.revenue_growth_percentage}%`,
      icon: BanknotesIcon,
      color: 'green'
    },
    {
      name: 'Verified Payments',
      value: mockAnalytics.verified_payments.toLocaleString(),
      change: `${mockAnalytics.pending_payments} pending`,
      icon: CheckCircleIcon,
      color: 'blue'
    },
    {
      name: 'Failed Payments',
      value: mockAnalytics.failed_payments.toLocaleString(),
      change: `${mockAnalytics.success_rate}% success rate`,
      icon: XCircleIcon,
      color: 'red'
    },
    {
      name: 'Processing Time',
      value: '2.3 min',
      change: 'Average time',
      icon: ClockIcon,
      color: 'purple'
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Payment Management
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Monitor transactions, verify payments, and process refunds
            </p>
          </div>
            
          {/* View Toggle */}
          <div className="flex items-center space-x-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'table'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <CreditCardIcon className="w-4 h-4 inline mr-2" />
                Transactions
              </button>
              <button
                onClick={() => setViewMode('analytics')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'analytics'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Analytics
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((item) => (
          <div key={item.name} className="bg-white overflow-hidden shadow-sm border rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {item.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {item.value}
                      </div>
                      <div className="ml-2 text-sm text-gray-500">
                        {item.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error Loading Data
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Transactions</h3>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-sm text-gray-500">Loading payments...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Method
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {mockPayments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {payment.user_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {payment.user_email}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          ${payment.amount}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                            {payment.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                          {payment.payment_method.replace('_', ' ')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(payment.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Analytics</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Payment Methods */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Payment Methods</h4>
              <div className="space-y-3">
                {mockAnalytics.payment_methods.map((method) => (
                  <div key={method.method} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {method.method.replace('_', ' ')}
                      </span>
                      <div className="text-xs text-gray-500">
                        {method.count} transactions
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-900">
                        ${method.total_amount.toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-500">
                        {method.success_rate}% success
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Revenue Overview */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Revenue Overview</h4>
              <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-600">Total Revenue</p>
                    <p className="text-2xl font-bold text-green-900">
                      ${mockAnalytics.total_revenue.toLocaleString()}
                    </p>
                    <p className="text-sm text-green-700 mt-1">
                      +{mockAnalytics.revenue_growth_percentage}% from last month
                    </p>
                  </div>
                  <BanknotesIcon className="h-8 w-8 text-green-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}