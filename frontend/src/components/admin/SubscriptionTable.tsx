'use client';

import { useState } from 'react';
import { Subscription } from '@/types/subscription';
import { PAYMENT_STATUS_OPTIONS, PLAN_TYPE_OPTIONS, TELEGRAM_STATUS_OPTIONS } from '@/types/subscription';

interface SubscriptionTableProps {
  subscriptions: Subscription[];
  loading: boolean;
  onSubscriptionSelect: (subscription: Subscription, mode?: 'view' | 'edit') => void;
  onPaymentVerify: (subscriptionId: string) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function SubscriptionTable({
  subscriptions,
  loading,
  onSubscriptionSelect,
  onPaymentVerify,
  currentPage,
  totalPages,
  onPageChange,
}: SubscriptionTableProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [sortField, setSortField] = useState<keyof Subscription>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Handle select all checkbox
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(subscriptions.map(sub => sub.id));
    } else {
      setSelectedIds([]);
    }
  };

  // Handle individual row selection
  const handleRowSelect = (subscriptionId: string, checked: boolean) => {
    if (checked) {
      setSelectedIds(prev => [...prev, subscriptionId]);
    } else {
      setSelectedIds(prev => prev.filter(id => id !== subscriptionId));
    }
  };

  // Get status badge styling
  const getStatusBadge = (status: string, type: 'payment' | 'telegram') => {
    let options;
    if (type === 'payment') {
      options = PAYMENT_STATUS_OPTIONS;
    } else {
      options = TELEGRAM_STATUS_OPTIONS;
    }
    
    const option = options.find(opt => opt.value === status);
    if (!option) return null;
    
    const colorClasses = {
      green: 'bg-green-100 text-green-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      red: 'bg-red-100 text-red-800',
      gray: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        colorClasses[option.color as keyof typeof colorClasses]
      }`}>
        {option.label}
      </span>
    );
  };

  // Get plan type badge
  const getPlanBadge = (planType: string) => {
    const plan = PLAN_TYPE_OPTIONS.find(p => p.value === planType);
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
        {plan?.label || planType}
      </span>
    );
  };

  // Format currency
  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Handle sorting
  const handleSort = (field: keyof Subscription) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {Array.from({ length: 8 }).map((_, i) => (
                  <th key={i} className="px-6 py-3">
                    <div className="h-4 bg-gray-200 rounded"></div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Array.from({ length: 10 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="h-4 bg-gray-200 rounded"></div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Bulk Actions Bar (shown when items are selected) */}
      {selectedIds.length > 0 && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-sm font-medium text-blue-900">
                {selectedIds.length} item{selectedIds.length !== 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <button className="text-sm text-blue-700 hover:text-blue-900 font-medium">
                Bulk Verify Payments
              </button>
              <button className="text-sm text-blue-700 hover:text-blue-900 font-medium">
                Add to Telegram
              </button>
              <button className="text-sm text-blue-700 hover:text-blue-900 font-medium">
                Export Selected
              </button>
              <button
                onClick={() => setSelectedIds([])}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={selectedIds.length === subscriptions.length && subscriptions.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('user')}
              >
                <div className="flex items-center">
                  User
                  <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                  </svg>
                </div>
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('plan_type')}
              >
                Plan
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('amount_paid')}
              >
                Amount
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('payment_status')}
              >
                Payment Status
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('telegram_status')}
              >
                Telegram Status
              </th>
              
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('created_at')}
              >
                Created
              </th>
              
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          
          <tbody className="bg-white divide-y divide-gray-200">
            {subscriptions.map((subscription) => (
              <tr 
                key={subscription.id}
                className={`hover:bg-gray-50 ${selectedIds.includes(subscription.id) ? 'bg-blue-50' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    checked={selectedIds.includes(subscription.id)}
                    onChange={(e) => handleRowSelect(subscription.id, e.target.checked)}
                  />
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {subscription.user.first_name?.charAt(0) || subscription.user.email.charAt(0)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {subscription.user.first_name} {subscription.user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {subscription.user.email}
                      </div>
                      {subscription.telegram_username && (
                        <div className="text-xs text-gray-400">
                          @{subscription.telegram_username}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  {getPlanBadge(subscription.plan_type)}
                  {subscription.is_active && (
                    <div className="text-xs text-green-600 mt-1">
                      {subscription.days_remaining} days left
                    </div>
                  )}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(subscription.amount_paid, subscription.currency)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {subscription.paystack_reference.slice(0, 12)}...
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(subscription.payment_status, 'payment')}
                  {subscription.payment_verified_at && (
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDate(subscription.payment_verified_at)}
                    </div>
                  )}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(subscription.telegram_status, 'telegram')}
                  {subscription.telegram_group_name && (
                    <div className="text-xs text-gray-500 mt-1">
                      {subscription.telegram_group_name}
                    </div>
                  )}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(subscription.created_at)}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    <button
                      onClick={() => onSubscriptionSelect(subscription, 'view')}
                      className="text-blue-600 hover:text-blue-900 text-sm"
                    >
                      View
                    </button>
                    
                    <button
                      onClick={() => onSubscriptionSelect(subscription, 'edit')}
                      className="text-indigo-600 hover:text-indigo-900 text-sm"
                    >
                      Edit
                    </button>
                    
                    {subscription.payment_status === 'pending' && (
                      <button
                        onClick={() => onPaymentVerify(subscription.id)}
                        className="text-green-600 hover:text-green-900 text-sm"
                      >
                        Verify
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {!loading && subscriptions.length === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No subscriptions found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white px-6 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Page <span className="font-medium">{currentPage}</span> of{' '}
                <span className="font-medium">{totalPages}</span>
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Previous</span>
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
                
                {/* Page numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNumber = Math.max(1, Math.min(currentPage - 2 + i, totalPages - 4 + i));
                  if (pageNumber <= totalPages) {
                    return (
                      <button
                        key={pageNumber}
                        onClick={() => onPageChange(pageNumber)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === pageNumber
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNumber}
                      </button>
                    );
                  }
                  return null;
                })}
                
                <button
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Next</span>
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}