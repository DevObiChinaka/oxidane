'use client';

import { useState, useEffect } from 'react';
import { Subscription, SubscriptionChangeLog, AuditLog } from '@/types/subscription';
import { PAYMENT_STATUS_OPTIONS, PLAN_TYPE_OPTIONS, TELEGRAM_STATUS_OPTIONS } from '@/types/subscription';

interface SubscriptionModalProps {
  subscription: Subscription;
  mode: 'view' | 'edit';
  onClose: () => void;
  onSave: (updatedSubscription: Subscription) => void;
}

export default function SubscriptionModal({
  subscription,
  mode,
  onClose,
  onSave
}: SubscriptionModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'history' | 'audit'>('details');
  const [editData, setEditData] = useState(subscription);
  const [changeReason, setChangeReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [changeHistory, setChangeHistory] = useState<SubscriptionChangeLog[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  // Reset form when subscription changes
  useEffect(() => {
    setEditData(subscription);
    setChangeReason('');
  }, [subscription]);

  const handleInputChange = (field: keyof Subscription, value: any) => {
    setEditData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    if (mode === 'view') return;
    
    if (!changeReason.trim()) {
      alert('Please provide a reason for the changes');
      return;
    }

    setLoading(true);
    try {
      await onSave(editData);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string, type: 'payment' | 'telegram') => {
    let options;
    if (type === 'payment') {
      options = PAYMENT_STATUS_OPTIONS;
    } else {
      options = TELEGRAM_STATUS_OPTIONS;
    }
    
    const option = options.find(opt => opt.value === status);
    if (!option) return status;
    
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

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        {/* Modal positioning */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        {/* Modal content */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {mode === 'edit' ? 'Edit Subscription' : 'Subscription Details'}
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  {subscription.user.first_name} {subscription.user.last_name} ({subscription.user.email})
                </p>
              </div>
              
              <div className="flex items-center space-x-3">
                {mode === 'view' && (
                  <button
                    onClick={() => window.location.href = `/admin/subscriptions/${subscription.id}/edit`}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Edit
                  </button>
                )}
                
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-4">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('details')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'details'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Details
                </button>
                <button
                  onClick={() => setActiveTab('history')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'history'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Change History
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'audit'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Audit Trail
                </button>
              </nav>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-96 overflow-y-auto">
            {/* Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                {/* User Information */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">User Information</h3>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Name</label>
                      <p className="mt-1 text-sm text-gray-900">
                        {subscription.user.first_name} {subscription.user.last_name}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Email</label>
                      <p className="mt-1 text-sm text-gray-900">{subscription.user.email}</p>
                    </div>
                  </div>
                </div>

                {/* Subscription Details */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Subscription Details</h3>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Plan Type</label>
                      {mode === 'edit' ? (
                        <select
                          value={editData.plan_type}
                          onChange={(e) => handleInputChange('plan_type', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        >
                          {PLAN_TYPE_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <p className="mt-1 text-sm text-gray-900">
                          {PLAN_TYPE_OPTIONS.find(p => p.value === subscription.plan_type)?.label}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Amount Paid</label>
                      {mode === 'edit' ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editData.amount_paid}
                          onChange={(e) => handleInputChange('amount_paid', parseFloat(e.target.value))}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900">
                          {formatCurrency(subscription.amount_paid, subscription.currency)}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Payment Status</label>
                      {mode === 'edit' ? (
                        <select
                          value={editData.payment_status}
                          onChange={(e) => handleInputChange('payment_status', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        >
                          {PAYMENT_STATUS_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <div className="mt-1">
                          {getStatusBadge(subscription.payment_status, 'payment')}
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Paystack Reference</label>
                      <p className="mt-1 text-sm text-gray-900 font-mono">
                        {subscription.paystack_reference}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Subscription Period */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Subscription Period</h3>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Start Date</label>
                      {mode === 'edit' ? (
                        <input
                          type="datetime-local"
                          value={editData.subscription_start?.slice(0, 16) || ''}
                          onChange={(e) => handleInputChange('subscription_start', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900">
                          {subscription.subscription_start ? formatDate(subscription.subscription_start) : 'Not set'}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">End Date</label>
                      {mode === 'edit' ? (
                        <input
                          type="datetime-local"
                          value={editData.subscription_end?.slice(0, 16) || ''}
                          onChange={(e) => handleInputChange('subscription_end', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900">
                          {subscription.subscription_end ? formatDate(subscription.subscription_end) : 'Not set'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Telegram Information */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Telegram Information</h3>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Telegram Username</label>
                      {mode === 'edit' ? (
                        <input
                          type="text"
                          value={editData.telegram_username}
                          onChange={(e) => handleInputChange('telegram_username', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          placeholder="@username"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900">@{subscription.telegram_username}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Telegram Status</label>
                      {mode === 'edit' ? (
                        <select
                          value={editData.telegram_status}
                          onChange={(e) => handleInputChange('telegram_status', e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        >
                          {TELEGRAM_STATUS_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <div className="mt-1">
                          {getStatusBadge(subscription.telegram_status, 'telegram')}
                        </div>
                      )}
                    </div>

                    {subscription.telegram_group_name && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Telegram Group</label>
                        <p className="mt-1 text-sm text-gray-900">{subscription.telegram_group_name}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Admin Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Admin Notes</label>
                  {mode === 'edit' ? (
                    <textarea
                      rows={3}
                      value={editData.admin_notes || ''}
                      onChange={(e) => handleInputChange('admin_notes', e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Add internal notes about this subscription..."
                    />
                  ) : (
                    <p className="mt-1 text-sm text-gray-900">
                      {subscription.admin_notes || 'No notes'}
                    </p>
                  )}
                </div>

                {/* Change Reason (Edit Mode) */}
                {mode === 'edit' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Reason for Changes <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      rows={2}
                      value={changeReason}
                      onChange={(e) => setChangeReason(e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Explain why these changes are being made..."
                      required
                    />
                  </div>
                )}
              </div>
            )}

            {/* Change History Tab */}
            {activeTab === 'history' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Change History</h3>
                {changeHistory.length > 0 ? (
                  <div className="space-y-4">
                    {changeHistory.map((change) => (
                      <div key={change.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="text-sm font-medium text-gray-900">
                            {change.change_type.replace('_', ' ')}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(change.timestamp)}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 mb-2">
                          <strong>{change.field_name}:</strong> {JSON.stringify(change.previous_value)} → {JSON.stringify(change.new_value)}
                        </div>
                        {change.reason && (
                          <div className="text-xs text-gray-500">
                            <strong>Reason:</strong> {change.reason}
                          </div>
                        )}
                        <div className="text-xs text-gray-400 mt-1">
                          By: {change.admin_user.first_name} {change.admin_user.last_name} ({change.admin_user.email})
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No change history available</p>
                )}
              </div>
            )}

            {/* Audit Trail Tab */}
            {activeTab === 'audit' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Audit Trail</h3>
                {auditLogs.length > 0 ? (
                  <div className="space-y-3">
                    {auditLogs.map((log) => (
                      <div key={log.id} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-1">
                          <div className="text-sm font-medium text-gray-900">
                            {log.action_type.replace(/_/g, ' ')}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(log.timestamp)}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 mb-1">
                          {log.action_description}
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-gray-500">
                            By: {log.admin_user.first_name} {log.admin_user.last_name}
                          </span>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              log.status === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                              log.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {log.status}
                            </span>
                            {log.duration_ms && (
                              <span className="text-gray-400">{log.duration_ms}ms</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No audit logs available</p>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {mode === 'edit' ? 'Cancel' : 'Close'}
            </button>
            
            {mode === 'edit' && (
              <button
                onClick={handleSave}
                disabled={loading || !changeReason.trim()}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}