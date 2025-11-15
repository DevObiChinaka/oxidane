'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { formatCurrency } from '@/utils/currencyFormatter';
import {
  BanknotesIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  CreditCardIcon,
  BuildingLibraryIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
}

interface Plan {
  id: string;
  name: string;
  base_price_usd: number;
}

interface PaymentDetails {
  card_last4?: string;
  card_brand?: string;
  bank_name?: string;
}

interface Transaction {
  id: string;
  user: User;
  plan: Plan;
  amount_paid: number;
  currency: string;
  status: string;
  payment_method: string;
  payment_details: PaymentDetails | null;
  created_at: string;
  start_date: string | null;
  end_date: string | null;
}

interface PaymentMethod {
  type: string;
  count: number;
  total_amount: number;
}

interface RevenueCurrency {
  currency: string;
  total: number;
}

interface Analytics {
  total_revenue_usd: number;
  total_transactions: number;
  verified_transactions: number;
  pending_transactions: number;
  recent_revenue_30d: number;
  average_transaction_value: number;
  payment_methods: PaymentMethod[];
  revenue_by_currency: RevenueCurrency[];
}

interface Pagination {
  page: number;
  page_size: number;
  total_pages: number;
  total_count: number;
}

interface PaymentsResponse {
  transactions: Transaction[];
  analytics: Analytics;
  pagination: Pagination;
}

export default function PaymentsPage() {
  const router = useRouter();
  const { user, isAdmin } = useAuth();

  // State
  const [data, setData] = useState<PaymentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [paymentMethodFilter, setPaymentMethodFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Auth protection
  useEffect(() => {
    if (!user || !isAdmin) {
      router.push('/admin/login');
      return;
    }
  }, [user, isAdmin, router]);

  // Fetch transactions
  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
      });

      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (paymentMethodFilter && paymentMethodFilter !== 'all') {
        params.append('payment_method', paymentMethodFilter);
      }
      if (dateFrom) {
        params.append('date_from', dateFrom);
      }
      if (dateTo) {
        params.append('date_to', dateTo);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://127.0.0.1:8000/api/admin/payments/transactions/?${params.toString()}`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch transactions');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
    } finally {
      setLoading(false);
    }
  };

  // Load data on mount and filter changes
  useEffect(() => {
    if (user && isAdmin) {
      fetchTransactions();
    }
  }, [
    user,
    isAdmin,
    currentPage,
    statusFilter,
    searchTerm,
    paymentMethodFilter,
    dateFrom,
    dateTo,
  ]);

  // Calculate success rate
  const getSuccessRate = () => {
    if (!data) return 0;
    const total = data.analytics.total_transactions;
    if (total === 0) return 0;
    return ((data.analytics.verified_transactions / total) * 100).toFixed(1);
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600';
      case 'pending':
        return 'text-yellow-600';
      case 'cancelled':
        return 'text-red-600';
      case 'expired':
        return 'text-gray-600';
      default:
        return 'text-blue-600';
    }
  };

  // Get payment method icon
  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'card':
        return <CreditCardIcon className="w-4 h-4" />;
      case 'bank_transfer':
        return <BuildingLibraryIcon className="w-4 h-4" />;
      default:
        return <BanknotesIcon className="w-4 h-4" />;
    }
  };

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Show loading if authentication is still being checked or user not loaded
  if (!user) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-teal"></div>
      </div>
    );
  }

  // Redirect if not admin (handled by useEffect, but this prevents flash of content)
  if (!isAdmin) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">You don't have permission to access this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Payment Transactions</h1>
          <p className="mt-2 text-sm text-gray-600">
            View and manage all payment transactions
          </p>
        </div>

        {/* Analytics Cards */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(data.analytics.total_revenue_usd, 'USD')}
                  </p>
                </div>
                <BanknotesIcon className="w-8 h-8 text-green-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                30-day: {formatCurrency(data.analytics.recent_revenue_30d, 'USD')}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Total Transactions</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {data.analytics.total_transactions}
                  </p>
                </div>
                <CheckCircleIcon className="w-8 h-8 text-blue-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Verified: {data.analytics.verified_transactions}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{getSuccessRate()}%</p>
                </div>
                <CheckCircleIcon className="w-8 h-8 text-green-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Pending: {data.analytics.pending_transactions}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Avg Transaction</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(data.analytics.average_transaction_value, 'USD')}
                  </p>
                </div>
                <BanknotesIcon className="w-8 h-8 text-purple-500" />
              </div>
              <p className="text-xs text-gray-500 mt-2">Per transaction</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Search
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder="Search by user..."
                  className="pl-10 pr-3 py-2 w-full text-sm border border-gray-300 rounded-md text-gray-900 bg-white"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-900 bg-white"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>

            {/* Payment Method Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Payment Method
              </label>
              <select
                value={paymentMethodFilter}
                onChange={(e) => {
                  setPaymentMethodFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-900 bg-white"
              >
                <option value="all">All Methods</option>
                <option value="card">Card</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="ussd">USSD</option>
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                From Date
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-900 bg-white"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                To Date
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-900 bg-white"
              />
            </div>
          </div>

          {/* Clear Filters */}
          <div className="mt-4">
            <button
              onClick={() => {
                setStatusFilter('all');
                setSearchTerm('');
                setPaymentMethodFilter('all');
                setDateFrom('');
                setDateTo('');
                setCurrentPage(1);
              }}
              className="text-xs text-brand-teal hover:text-brand-teal/80"
            >
              Clear All Filters
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <ArrowPathIcon className="w-8 h-8 text-brand-teal animate-spin" />
          </div>
        )}

        {/* Transactions Table */}
        {!loading && data && (
          <>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        User
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Plan
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Plan Price (USD)
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Amount Paid
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Method
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.transactions.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                          No transactions found
                        </td>
                      </tr>
                    ) : (
                      data.transactions.map((transaction) => (
                        <tr key={transaction.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="text-sm">
                              <div className="font-medium text-gray-900">
                                {transaction.user.full_name}
                              </div>
                              <div className="text-gray-500">{transaction.user.email}</div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm text-gray-900">
                              {transaction.plan.name}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-medium text-gray-900">
                              {formatCurrency(transaction.plan.base_price_usd, 'USD')}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-medium text-gray-900">
                              {formatCurrency(transaction.amount_paid, transaction.currency)}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {getPaymentMethodIcon(transaction.payment_method)}
                              <span className="text-sm text-gray-900 capitalize">
                                {transaction.payment_method.replace('_', ' ')}
                              </span>
                            </div>
                            {transaction.payment_details && (
                              <div className="text-xs text-gray-500 mt-1">
                                {transaction.payment_details.card_brand &&
                                  `${transaction.payment_details.card_brand} ****${transaction.payment_details.card_last4}`}
                                {transaction.payment_details.bank_name &&
                                  transaction.payment_details.bank_name}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`text-xs font-semibold capitalize ${getStatusColor(
                                transaction.status
                              )}`}
                            >
                              {transaction.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm text-gray-900">
                              {formatDate(transaction.created_at)}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {data.pagination.total_pages > 1 && (
              <div className="bg-white rounded-lg shadow px-4 py-3 mt-4 flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() =>
                      setCurrentPage((p) => Math.min(data.pagination.total_pages, p + 1))
                    }
                    disabled={currentPage === data.pagination.total_pages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">
                        {(currentPage - 1) * pageSize + 1}
                      </span>{' '}
                      to{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * pageSize, data.pagination.total_count)}
                      </span>{' '}
                      of <span className="font-medium">{data.pagination.total_count}</span>{' '}
                      results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <ChevronLeftIcon className="h-5 w-5" />
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        Page {currentPage} of {data.pagination.total_pages}
                      </span>
                      <button
                        onClick={() =>
                          setCurrentPage((p) => Math.min(data.pagination.total_pages, p + 1))
                        }
                        disabled={currentPage === data.pagination.total_pages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <ChevronRightIcon className="h-5 w-5" />
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
