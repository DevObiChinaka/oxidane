'use client';

import { useState } from 'react';
import { usePayments, usePaymentAnalytics, usePaymentActions } from '../hooks/useAdminAPI';
import { PaymentTransaction, PaymentAnalytics, PaymentFilters } from '../../../types/payment';
import PaymentTable from '../../../components/admin/PaymentTable';
import PaymentFiltersComponent from '../../../components/admin/PaymentFilters';
import PaymentModal from '../../../components/admin/PaymentModal';
import PaymentAnalyticsDashboard from '../../../components/admin/PaymentAnalyticsDashboard';
import { 
  CreditCardIcon, 
  BanknotesIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

export default function PaymentsManagement() {
  // Pagination and filtering state
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<PaymentFilters>({});
  
  // Modal state
  const [selectedPayment, setSelectedPayment] = useState<PaymentTransaction | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'view' | 'verify' | 'refund'>('view');
  
  // View mode
  const [viewMode, setViewMode] = useState<'table' | 'analytics'>('table');
  
  // Use hooks for data fetching
  const { 
    data: paymentsData, 
    loading: paymentsLoading, 
    error: paymentsError, 
    refetch: refetchPayments 
  } = usePayments({
    page: currentPage,
    limit: 20,
    ...filters
  });
  
  const { 
    data: analytics, 
    loading: analyticsLoading, 
    error: analyticsError 
  } = usePaymentAnalytics({
    period: 'monthly',
    days_back: 30
  });
  
  const { 
    verifyPayment, 
    processRefund, 
    updatePaymentStatus,
    loading: actionLoading, 
    error: actionError 
  } = usePaymentActions();

  // Handle filter changes
  const handleFilterChange = (newFilters: PaymentFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle payment selection
  const handlePaymentSelect = (payment: PaymentTransaction, mode: 'view' | 'verify' | 'refund' = 'view') => {
    setSelectedPayment(payment);
    setModalMode(mode);
    setModalOpen(true);
  };

  // Handle payment verification
  const handlePaymentVerification = async (paymentId: string, verificationData: any) => {
    try {
      await verifyPayment(paymentId, verificationData);
      refetchPayments();
      setModalOpen(false);
      console.log('Payment verified successfully');
    } catch (err) {
      console.error('Payment verification error:', err);
    }
  };

  // Handle refund processing
  const handleRefundProcessing = async (paymentId: string, refundData: any) => {
    try {
      await processRefund(paymentId, refundData);
      refetchPayments();
      setModalOpen(false);
      console.log('Refund processed successfully');
    } catch (err) {
      console.error('Refund processing error:', err);
    }
  };

  // Quick stats from analytics
  const quickStats = analytics ? [
    {
      name: 'Total Revenue',
      value: `$${analytics.total_revenue.toLocaleString()}`,
      change: `+${analytics.revenue_growth_percentage}%`,
      changeType: 'positive',
      icon: BanknotesIcon,
    },
    {
      name: 'Verified Payments',
      value: analytics.verified_payments.toLocaleString(),
      change: `${analytics.pending_payments} pending`,
      changeType: 'neutral',
      icon: CheckCircleIcon,
    },
    {
      name: 'Failed Payments',
      value: analytics.failed_payments.toLocaleString(),
      change: `${((analytics.failed_payments / (analytics.verified_payments + analytics.failed_payments)) * 100).toFixed(1)}% failure rate`,
      changeType: 'negative',
      icon: XCircleIcon,
    },
    {
      name: 'Processing Time',
      value: `${analytics.avg_processing_time || 'N/A'}`,
      change: 'Average time',
      changeType: 'neutral',
      icon: ClockIcon,
    },
  ] : [];

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
      {!analyticsLoading && analytics && (
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
                        <div className={`ml-2 text-sm ${
                          item.changeType === 'positive' ? 'text-green-600' :
                          item.changeType === 'negative' ? 'text-red-600' : 'text-gray-500'
                        }`}>
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
      )}

      {/* Error Display */}
      {(paymentsError || analyticsError || actionError) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error Loading Data
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {paymentsError || analyticsError || actionError}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {viewMode === 'table' ? (
        <>
          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border">
            <PaymentFiltersComponent
              filters={filters}
              onFiltersChange={handleFilterChange}
            />
          </div>

          {/* Payments Table */}
          <div className="bg-white rounded-lg shadow-sm border">
            <PaymentTable
              payments={paymentsData?.results || []}
              loading={paymentsLoading}
              onPaymentSelect={handlePaymentSelect}
              onVerifyPayment={(id: string) => handlePaymentSelect(
                paymentsData?.results.find((p: PaymentTransaction) => p.id === id)!, 
                'verify'
              )}
              onProcessRefund={(id: string) => handlePaymentSelect(
                paymentsData?.results.find((p: PaymentTransaction) => p.id === id)!, 
                'refund'
              )}
            />
            
            {/* Pagination */}
            {paymentsData?.pagination && (
              <div className="px-6 py-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Showing {((currentPage - 1) * 20) + 1} to{' '}
                    {Math.min(currentPage * 20, paymentsData.pagination.total_payments)} of{' '}
                    {paymentsData.pagination.total_payments} payments
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={!paymentsData.pagination.has_previous}
                      className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-2 text-sm font-medium text-gray-900">
                      Page {currentPage} of {paymentsData.pagination.total_pages}
                    </span>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={!paymentsData.pagination.has_next}
                      className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        <PaymentAnalyticsDashboard
          analytics={analytics}
          loading={analyticsLoading}
        />
      )}

      {/* Payment Modal */}
      {selectedPayment && (
        <PaymentModal
          payment={selectedPayment}
          mode={modalMode}
          open={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setSelectedPayment(null);
          }}
          onVerify={handlePaymentVerification}
          onRefund={handleRefundProcessing}
          loading={actionLoading}
        />
      )}
    </div>
  );
}