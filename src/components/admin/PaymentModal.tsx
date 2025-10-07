'use client';

import { useState } from 'react';
import { PaymentTransaction, formatPaymentAmount, getPaymentStatusLabel, calculateRefundableAmount } from '../../types/payment';
import { 
  XMarkIcon, 
  CreditCardIcon, 
  CheckCircleIcon, 
  ArrowPathIcon,
  ClockIcon,
  UserIcon
} from '@heroicons/react/24/outline';

interface PaymentModalProps {
  payment: PaymentTransaction;
  mode: 'view' | 'verify' | 'refund';
  open: boolean;
  onClose: () => void;
  onVerify: (paymentId: string, verificationData: any) => void;
  onRefund: (paymentId: string, refundData: any) => void;
  loading: boolean;
}

export default function PaymentModal({ 
  payment, 
  mode, 
  open, 
  onClose, 
  onVerify, 
  onRefund, 
  loading 
}: PaymentModalProps) {
  
  const [verificationData, setVerificationData] = useState({
    verification_method: 'manual',
    admin_notes: '',
    force_verify: false,
    notify_user: true,
  });

  const [refundData, setRefundData] = useState({
    refund_amount: calculateRefundableAmount(payment),
    reason: '',
    refund_method: 'original_source',
    admin_notes: '',
    notify_user: true,
    revoke_access: true,
  });

  const handleVerify = () => {
    onVerify(payment.id, verificationData);
  };

  const handleRefund = () => {
    onRefund(payment.id, refundData);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-25" onClick={onClose} />
        <div className="relative w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
          
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div className="flex items-center">
              {mode === 'verify' ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600 mr-3" />
              ) : mode === 'refund' ? (
                <ArrowPathIcon className="h-6 w-6 text-purple-600 mr-3" />
              ) : (
                <CreditCardIcon className="h-6 w-6 text-blue-600 mr-3" />
              )}
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {mode === 'verify' && 'Verify Payment'}
                  {mode === 'refund' && 'Process Refund'}
                  {mode === 'view' && 'Payment Details'}
                </h3>
                <p className="text-sm text-gray-500">
                  Reference: {payment.reference}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Payment Information */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-4 flex items-center">
                <CreditCardIcon className="h-4 w-4 mr-2" />
                Payment Information
              </h3>
              
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Amount:</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {formatPaymentAmount(payment.amount, payment.currency)}
                  </dd>
                </div>
                
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Status:</dt>
                  <dd className="text-sm font-medium">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-800">
                      {getPaymentStatusLabel(payment.status)}
                    </span>
                  </dd>
                </div>
                
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Method:</dt>
                  <dd className="text-sm font-medium text-gray-900 capitalize">
                    {payment.payment_method.replace('_', ' ')}
                  </dd>
                </div>
                
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Type:</dt>
                  <dd className="text-sm font-medium text-gray-900 capitalize">
                    {payment.transaction_type.replace('_', ' ')}
                  </dd>
                </div>

                {payment.paystack_reference && (
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Paystack Ref:</dt>
                    <dd className="text-sm font-mono text-gray-900">
                      {payment.paystack_reference}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* User Information */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-4 flex items-center">
                <UserIcon className="h-4 w-4 mr-2" />
                User Information
              </h3>
              
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Name:</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {payment.user_name || 'N/A'}
                  </dd>
                </div>
                
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Email:</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {payment.user_email}
                  </dd>
                </div>

                {payment.subscription_plan?.telegram_username && (
                  <div className="flex justify-between">
                    <dt className="text-sm text-gray-500">Telegram:</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      @{payment.subscription_plan.telegram_username}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Action Forms */}
          {mode === 'verify' && (
            <div className="mt-6 bg-green-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-green-900 mb-4">
                Payment Verification
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Verification Method
                  </label>
                  <select
                    value={verificationData.verification_method}
                    onChange={(e) => setVerificationData(prev => ({ ...prev, verification_method: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option value="manual">Manual Verification</option>
                    <option value="paystack_recheck">Paystack Re-check</option>
                    <option value="bank_confirmation">Bank Confirmation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Admin Notes
                  </label>
                  <textarea
                    value={verificationData.admin_notes}
                    onChange={(e) => setVerificationData(prev => ({ ...prev, admin_notes: e.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="Add verification notes..."
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={verificationData.force_verify}
                      onChange={(e) => setVerificationData(prev => ({ ...prev, force_verify: e.target.checked }))}
                      className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">Force verify (override checks)</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={verificationData.notify_user}
                      onChange={(e) => setVerificationData(prev => ({ ...prev, notify_user: e.target.checked }))}
                      className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">Notify user</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {mode === 'refund' && (
            <div className="mt-6 bg-purple-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-purple-900 mb-4">
                Process Refund
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Refund Amount
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="number"
                      value={refundData.refund_amount}
                      onChange={(e) => setRefundData(prev => ({ ...prev, refund_amount: parseFloat(e.target.value) }))}
                      max={payment.amount}
                      step="0.01"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    />
                    <span className="text-sm text-gray-500">
                      Max: {formatPaymentAmount(payment.amount, payment.currency)}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Refund Reason
                  </label>
                  <textarea
                    value={refundData.reason}
                    onChange={(e) => setRefundData(prev => ({ ...prev, reason: e.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Reason for refund..."
                    required
                  />
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
            
            {mode === 'verify' && (
              <button
                onClick={handleVerify}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify Payment'}
              </button>
            )}
            
            {mode === 'refund' && (
              <button
                onClick={handleRefund}
                disabled={loading || !refundData.reason}
                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Process Refund'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}