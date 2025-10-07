'use client';

import { PaymentTransaction, formatPaymentAmount, getPaymentStatusColor, getPaymentStatusLabel, getPaymentRiskLevel, canVerifyPayment, canRefundPayment } from '../../types/payment';
import { 
  EyeIcon, 
  CheckCircleIcon, 
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CreditCardIcon,
  BanknotesIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface PaymentTableProps {
  payments: PaymentTransaction[];
  loading: boolean;
  onPaymentSelect: (payment: PaymentTransaction, mode: 'view' | 'verify' | 'refund') => void;
  onVerifyPayment: (paymentId: string) => void;
  onProcessRefund: (paymentId: string) => void;
}

export default function PaymentTable({ 
  payments, 
  loading, 
  onPaymentSelect, 
  onVerifyPayment, 
  onProcessRefund 
}: PaymentTableProps) {
  
  const getStatusBadgeClasses = (status: PaymentTransaction['status']) => {
    const color = getPaymentStatusColor(status);
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (color) {
      case 'green':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'yellow':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'red':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'blue':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'purple':
        return `${baseClasses} bg-purple-100 text-purple-800`;
      case 'orange':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const getRiskBadgeClasses = (risk: 'low' | 'medium' | 'high') => {
    switch (risk) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'card':
        return <CreditCardIcon className="h-4 w-4" />;
      case 'bank_transfer':
        return <BanknotesIcon className="h-4 w-4" />;
      default:
        return <BanknotesIcon className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-sm text-gray-500">Loading payments...</p>
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="p-8 text-center">
        <CreditCardIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No payments found</h3>
        <p className="mt-1 text-sm text-gray-500">No payments match your current filters.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User & Transaction
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount & Method
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status & Risk
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type & Plan
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Dates
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {payments.map((payment) => {
              const riskLevel = getPaymentRiskLevel(payment);
              const canVerify = canVerifyPayment(payment);
              const canRefund = canRefundPayment(payment);

              return (
                <tr key={payment.id} className="hover:bg-gray-50">
                  {/* User & Transaction */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {payment.user_name || payment.user_email}
                        </div>
                        <div className="text-sm text-gray-500">
                          {payment.user_email}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          Ref: {payment.reference}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Amount & Method */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {formatPaymentAmount(payment.amount, payment.currency)}
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      {getPaymentMethodIcon(payment.payment_method)}
                      <span className="ml-1 capitalize">
                        {payment.payment_method.replace('_', ' ')}
                      </span>
                    </div>
                  </td>

                  {/* Status & Risk */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col space-y-1">
                      <span className={getStatusBadgeClasses(payment.status)}>
                        {getPaymentStatusLabel(payment.status)}
                      </span>
                      {riskLevel !== 'low' && (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getRiskBadgeClasses(riskLevel)}`}>
                          {riskLevel === 'high' && <ExclamationTriangleIcon className="h-3 w-3 mr-1" />}
                          {riskLevel.toUpperCase()} RISK
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Type & Plan */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 capitalize">
                      {payment.transaction_type.replace('_', ' ')}
                    </div>
                    {payment.subscription_plan && (
                      <div className="text-sm text-gray-500">
                        {payment.subscription_plan.plan_type}
                        {payment.subscription_plan.telegram_username && (
                          <div className="text-xs">@{payment.subscription_plan.telegram_username}</div>
                        )}
                      </div>
                    )}
                    {payment.course_enrollment && (
                      <div className="text-sm text-gray-500">
                        {payment.course_enrollment.course_title}
                      </div>
                    )}
                  </td>

                  {/* Dates */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      <div>
                        <div>Created: {new Date(payment.created_at).toLocaleDateString()}</div>
                        {payment.processed_at && (
                          <div>Processed: {new Date(payment.processed_at).toLocaleDateString()}</div>
                        )}
                        {payment.verification_attempts && payment.verification_attempts > 0 && (
                          <div className="text-xs text-orange-600">
                            {payment.verification_attempts} verification attempts
                          </div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      {/* View Details */}
                      <button
                        onClick={() => onPaymentSelect(payment, 'view')}
                        className="text-blue-600 hover:text-blue-900"
                        title="View Details"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>

                      {/* Verify Payment */}
                      {canVerify && (
                        <button
                          onClick={() => onVerifyPayment(payment.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Verify Payment"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                      )}

                      {/* Process Refund */}
                      {canRefund && (
                        <button
                          onClick={() => onProcessRefund(payment.id)}
                          className="text-purple-600 hover:text-purple-900"
                          title="Process Refund"
                        >
                          <ArrowPathIcon className="h-4 w-4" />
                        </button>
                      )}

                      {/* Quick Actions Dropdown */}
                      <div className="relative inline-block text-left">
                        <button className="text-gray-400 hover:text-gray-600">
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}