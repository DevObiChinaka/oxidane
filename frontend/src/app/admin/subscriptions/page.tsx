'use client';

import { useState } from 'react';
import { useSubscriptions, useSubscriptionAnalytics, useSubscriptionActions } from '../hooks/useAdminAPI';
import { Subscription, SubscriptionAnalytics, SubscriptionFilters } from '../../../types/subscription';
import SubscriptionTable from '../../../components/admin/SubscriptionTable';
import SubscriptionFiltersComponent from '../../../components/admin/SubscriptionFilters';
import SubscriptionModal from '../../../components/admin/SubscriptionModal';
import AnalyticsDashboard from '../../../components/admin/AnalyticsDashboard';

export default function SubscriptionsManagement() {
  // Pagination and filtering state
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<SubscriptionFilters>({});
  
  // Modal state
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'view' | 'edit'>('view');
  
  // View mode
  const [viewMode, setViewMode] = useState<'table' | 'analytics'>('table');
  
  // Use hooks for data fetching - Filter for signals subscriptions only (exclude mentorship)
  const { data: subscriptionsData, loading: subscriptionsLoading, error: subscriptionsError, refetch: refetchSubscriptions } = useSubscriptions({
    page: currentPage,
    limit: 20,
    plan_type: 'signals', // Only show signals subscriptions (weekly, monthly, VIP)
    ...filters
  });
  
  const { data: analytics, loading: analyticsLoading, error: analyticsError, refetch: refetchAnalytics } = useSubscriptionAnalytics({
    period: 'monthly',
    days_back: 30
  });
  
  const { updateSubscription, verifyPayment, loading: actionLoading, error: actionError } = useSubscriptionActions();

  // Handle filter changes
  const handleFilterChange = (newFilters: SubscriptionFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle subscription selection
  const handleSubscriptionSelect = (subscription: Subscription, mode: 'view' | 'edit' = 'view') => {
    setSelectedSubscription(subscription);
    setModalMode(mode);
    setModalOpen(true);
  };

  // Handle subscription update
  const handleSubscriptionUpdate = async (updatedSubscription: Subscription) => {
    try {
      await updateSubscription(updatedSubscription.id, updatedSubscription);
      refetchSubscriptions();
      setModalOpen(false);

    } catch (err) {
      console.error('Update subscription error:', err);
    }
  };

  // Handle payment verification
  const handlePaymentVerification = async (subscriptionId: string) => {
    try {
      await verifyPayment(subscriptionId);
      refetchSubscriptions();

    } catch (err) {
      console.error('Payment verification error:', err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Signals Subscription Management
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage signals subscriptions (Weekly, Monthly, VIP), payments, and Telegram access
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
                Subscriptions
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

      {/* Main Content */}
      <div>
        {(subscriptionsError || analyticsError || actionError) && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  {subscriptionsError || analyticsError || actionError}
                </div>
              </div>
            </div>
          </div>
        )}

        {viewMode === 'table' ? (
          <>
            {/* Filters */}
            <div className="mb-6">
              <SubscriptionFiltersComponent
                filters={filters}
                onFiltersChange={handleFilterChange}
                loading={subscriptionsLoading}
              />
            </div>

            {/* Subscription Table */}
            <div className="bg-white shadow-sm rounded-lg border border-gray-200">
              <SubscriptionTable
                subscriptions={subscriptionsData?.results || []}
                loading={subscriptionsLoading}
                onSubscriptionSelect={handleSubscriptionSelect}
                onPaymentVerify={handlePaymentVerification}
                currentPage={currentPage}
                totalPages={Math.ceil((subscriptionsData?.count || 0) / 20)}
                onPageChange={handlePageChange}
              />
            </div>
          </>
        ) : (
          /* Analytics Dashboard */
          <AnalyticsDashboard
            analytics={analytics}
            loading={analyticsLoading}
            onRefresh={refetchAnalytics}
          />
        )}
      </div>

      {/* Subscription Detail/Edit Modal */}
      {modalOpen && selectedSubscription && (
        <SubscriptionModal
          subscription={selectedSubscription}
          mode={modalMode}
          onClose={() => {
            setModalOpen(false);
            setSelectedSubscription(null);
          }}
          onSave={handleSubscriptionUpdate}
        />
      )}
    </div>
  );
}