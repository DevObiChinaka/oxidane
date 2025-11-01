'use client';

import { useState, useEffect } from 'react';
import { SubscriptionFilters as SubscriptionFiltersType } from '@/types/subscription';
import { PAYMENT_STATUS_OPTIONS, PLAN_TYPE_OPTIONS, TELEGRAM_STATUS_OPTIONS } from '@/types/subscription';

interface SubscriptionFiltersProps {
  filters: SubscriptionFiltersType;
  onFiltersChange: (filters: SubscriptionFiltersType) => void;
  loading: boolean;
}

export default function SubscriptionFilters({
  filters,
  onFiltersChange,
  loading
}: SubscriptionFiltersProps) {
  const [localFilters, setLocalFilters] = useState<SubscriptionFiltersType>(filters);
  const [isExpanded, setIsExpanded] = useState(false);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Apply filters with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange(localFilters);
    }, 300);

    return () => clearTimeout(timer);
  }, [localFilters, onFiltersChange]);

  const handleFilterChange = (key: keyof SubscriptionFiltersType, value: string) => {
    setLocalFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    const clearedFilters: SubscriptionFiltersType = {};
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const hasActiveFilters = Object.values(localFilters).some(value => 
    value !== undefined && value !== null && value !== ''
  );

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200">
      {/* Filter Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-lg font-medium text-gray-900">Filters</h3>
            {hasActiveFilters && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {Object.values(localFilters).filter(v => v).length} active
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear all
              </button>
            )}
            
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              {isExpanded ? 'Show Less' : 'Advanced Filters'}
            </button>
          </div>
        </div>
      </div>

      {/* Basic Filters (Always Visible) */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Search */}
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <input
                type="text"
                id="search"
                placeholder="Email, name, reference..."
                value={localFilters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                disabled={loading}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed pl-10"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Payment Status */}
          <div>
            <label htmlFor="payment_status" className="block text-sm font-medium text-gray-700 mb-1">
              Payment Status
            </label>
            <select
              id="payment_status"
              value={localFilters.payment_status || ''}
              onChange={(e) => handleFilterChange('payment_status', e.target.value)}
              disabled={loading}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">All Statuses</option>
              {PAYMENT_STATUS_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Plan Type */}
          <div>
            <label htmlFor="plan_type" className="block text-sm font-medium text-gray-700 mb-1">
              Plan Type
            </label>
            <select
              id="plan_type"
              value={localFilters.plan_type || ''}
              onChange={(e) => handleFilterChange('plan_type', e.target.value)}
              disabled={loading}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">All Plans</option>
              {PLAN_TYPE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Telegram Status */}
          <div>
            <label htmlFor="telegram_status" className="block text-sm font-medium text-gray-700 mb-1">
              Telegram Status
            </label>
            <select
              id="telegram_status"
              value={localFilters.telegram_status || ''}
              onChange={(e) => handleFilterChange('telegram_status', e.target.value)}
              disabled={loading}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">All Telegram Statuses</option>
              {TELEGRAM_STATUS_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Advanced Filters (Expandable) */}
      {isExpanded && (
        <div className="px-6 pb-4 border-t border-gray-100">
          <div className="pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Date Range</h4>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {/* Date From */}
              <div>
                <label htmlFor="date_from" className="block text-sm font-medium text-gray-700 mb-1">
                  From Date
                </label>
                <input
                  type="date"
                  id="date_from"
                  value={localFilters.date_from || ''}
                  onChange={(e) => handleFilterChange('date_from', e.target.value)}
                  disabled={loading}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {/* Date To */}
              <div>
                <label htmlFor="date_to" className="block text-sm font-medium text-gray-700 mb-1">
                  To Date
                </label>
                <input
                  type="date"
                  id="date_to"
                  value={localFilters.date_to || ''}
                  onChange={(e) => handleFilterChange('date_to', e.target.value)}
                  disabled={loading}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm text-gray-900 bg-white focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {/* Quick Date Filters */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quick Filters
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => {
                      const today = new Date().toISOString().split('T')[0];
                      handleFilterChange('date_from', today);
                      handleFilterChange('date_to', today);
                    }}
                    className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Today
                  </button>
                  <button
                    onClick={() => {
                      const today = new Date();
                      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                      handleFilterChange('date_from', weekAgo.toISOString().split('T')[0]);
                      handleFilterChange('date_to', today.toISOString().split('T')[0]);
                    }}
                    className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Last 7 days
                  </button>
                  <button
                    onClick={() => {
                      const today = new Date();
                      const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                      handleFilterChange('date_from', monthAgo.toISOString().split('T')[0]);
                      handleFilterChange('date_to', today.toISOString().split('T')[0]);
                    }}
                    className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Last 30 days
                  </button>
                </div>
              </div>
            </div>

            {/* Additional Filters */}
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Additional Filters</h4>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* User Email */}
                <div>
                  <label htmlFor="user_email" className="block text-sm font-medium text-gray-700 mb-1">
                    User Email
                  </label>
                  <input
                    type="email"
                    id="user_email"
                    placeholder="user@example.com"
                    value={localFilters.user_email || ''}
                    onChange={(e) => handleFilterChange('user_email', e.target.value)}
                    disabled={loading}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>

                {/* Filter Presets */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Filter Presets
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => {
                        setLocalFilters({
                          payment_status: 'pending'
                        });
                      }}
                      className="px-3 py-2 text-xs bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 transition-colors"
                    >
                      Pending Payments
                    </button>
                    <button
                      onClick={() => {
                        setLocalFilters({
                          telegram_status: 'pending_add'
                        });
                      }}
                      className="px-3 py-2 text-xs bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      Telegram Pending
                    </button>
                    <button
                      onClick={() => {
                        setLocalFilters({
                          payment_status: 'verified',
                          telegram_status: 'added'
                        });
                      }}
                      className="px-3 py-2 text-xs bg-green-100 text-green-800 rounded-md hover:bg-green-200 transition-colors"
                    >
                      Active Subs
                    </button>
                    <button
                      onClick={() => {
                        setLocalFilters({
                          payment_status: 'failed'
                        });
                      }}
                      className="px-3 py-2 text-xs bg-red-100 text-red-800 rounded-md hover:bg-red-200 transition-colors"
                    >
                      Failed Payments
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter Summary */}
      {hasActiveFilters && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4 text-gray-600">
              <span>Active filters:</span>
              <div className="flex flex-wrap gap-2">
                {Object.entries(localFilters).map(([key, value]) => {
                  if (!value) return null;
                  
                  let displayValue = value;
                  if (key === 'payment_status') {
                    const option = PAYMENT_STATUS_OPTIONS.find(opt => opt.value === value);
                    displayValue = option?.label || value;
                  } else if (key === 'plan_type') {
                    const option = PLAN_TYPE_OPTIONS.find(opt => opt.value === value);
                    displayValue = option?.label || value;
                  } else if (key === 'telegram_status') {
                    const option = TELEGRAM_STATUS_OPTIONS.find(opt => opt.value === value);
                    displayValue = option?.label || value;
                  }
                  
                  return (
                    <span
                      key={key}
                      className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {key.replace('_', ' ')}: {displayValue}
                      <button
                        onClick={() => handleFilterChange(key as keyof SubscriptionFiltersType, '')}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>
            
            {loading && (
              <div className="flex items-center text-gray-500">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Applying filters...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}