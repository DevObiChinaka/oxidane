// Payment Management Types
export interface PaymentTransaction {
  id: string;
  user_email: string;
  user_name?: string;
  transaction_type: 'subscription' | 'course' | 'mentorship' | 'refund';
  reference: string;
  paystack_reference?: string;
  amount: number;
  currency: string;
  payment_method: 'card' | 'bank_transfer' | 'ussd' | 'qr' | 'mobile_money';
  subscription_plan?: {
    plan_type: string;
    telegram_username?: string;
    subscription_end?: string;
  };
  status: 'pending' | 'processing' | 'verified' | 'failed' | 'refunded' | 'disputed';
  processed_at?: string;
  created_at: string;
  updated_at: string;
  
  // Additional details
  gateway_response?: string;
  failure_reason?: string;
  admin_notes?: string;
  verification_attempts?: number;
  last_verification_attempt?: string;
  
  // Related subscription/course info
  signal_subscription?: {
    id: string;
    plan_type: string;
    telegram_status: string;
    subscription_end?: string;
  };
  course_enrollment?: {
    id: string;
    course_title: string;
    enrollment_date: string;
  };
}

export interface PaymentAnalytics {
  // Revenue metrics
  total_revenue: number;
  revenue_growth_percentage: number;
  monthly_revenue: number;
  weekly_revenue: number;
  daily_revenue: number;
  
  // Transaction counts
  total_transactions: number;
  verified_payments: number;
  pending_payments: number;
  failed_payments: number;
  refunded_payments: number;
  disputed_payments: number;
  
  // Success metrics
  success_rate: number;
  failure_rate: number;
  refund_rate: number;
  
  // Processing metrics
  avg_processing_time?: string;
  fastest_processing_time?: string;
  slowest_processing_time?: string;
  
  // Payment methods breakdown
  payment_methods: Array<{
    method: string;
    count: number;
    total_amount: number;
    success_rate: number;
  }>;
  
  // Currency breakdown
  currency_breakdown: Array<{
    currency: string;
    count: number;
    total_amount: number;
  }>;
  
  // Time-based data for charts
  daily_stats: Array<{
    date: string;
    revenue: number;
    transactions: number;
    success_rate: number;
  }>;
  
  // Plan type performance
  plan_performance: Array<{
    plan_type: string;
    count: number;
    revenue: number;
    success_rate: number;
  }>;
  
  // Recent trends
  trends: {
    revenue_trend: 'increasing' | 'decreasing' | 'stable';
    transaction_trend: 'increasing' | 'decreasing' | 'stable';
    success_rate_trend: 'improving' | 'declining' | 'stable';
  };
}

export interface PaymentFilters {
  status?: string;
  transaction_type?: string;
  payment_method?: string;
  currency?: string;
  amount_min?: number;
  amount_max?: number;
  date_from?: string;
  date_to?: string;
  user_email?: string;
  reference?: string;
  plan_type?: string;
  verification_status?: 'verified' | 'unverified' | 'pending_verification';
  sort_by?: 'created_at' | 'amount' | 'processed_at' | 'status';
  sort_order?: 'asc' | 'desc';
}

export interface PaymentListResponse {
  results: PaymentTransaction[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_payments: number;
    has_next: boolean;
    has_previous: boolean;
  };
  filters_applied: PaymentFilters;
  summary: {
    total_amount: number;
    average_amount: number;
    status_counts: Record<string, number>;
  };
}

export interface PaymentVerificationRequest {
  payment_id: string;
  verification_method: 'manual' | 'paystack_recheck' | 'bank_confirmation';
  admin_notes?: string;
  force_verify?: boolean;
  notify_user?: boolean;
}

export interface PaymentVerificationResponse {
  success: boolean;
  message: string;
  payment: PaymentTransaction;
  gateway_response?: unknown;
  actions_taken: string[];
}

export interface RefundRequest {
  payment_id: string;
  refund_amount?: number; // If not provided, full refund
  reason: string;
  refund_method: 'original_source' | 'bank_transfer' | 'manual';
  admin_notes?: string;
  notify_user?: boolean;
  revoke_access?: boolean; // For subscriptions
}

export interface RefundResponse {
  success: boolean;
  message: string;
  refund_reference: string;
  refund_amount: number;
  estimated_completion: string;
  actions_taken: string[];
}

export interface PaymentStatusUpdate {
  payment_id: string;
  new_status: PaymentTransaction['status'];
  reason: string;
  admin_notes?: string;
  notify_user?: boolean;
}

// Constants for dropdowns and filters
export const PAYMENT_STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending', color: 'yellow', description: 'Payment initiated but not processed' },
  { value: 'processing', label: 'Processing', color: 'blue', description: 'Payment being processed by gateway' },
  { value: 'verified', label: 'Verified', color: 'green', description: 'Payment confirmed and successful' },
  { value: 'failed', label: 'Failed', color: 'red', description: 'Payment failed or rejected' },
  { value: 'refunded', label: 'Refunded', color: 'purple', description: 'Payment refunded to user' },
  { value: 'disputed', label: 'Disputed', color: 'orange', description: 'Payment under dispute' },
];

export const TRANSACTION_TYPE_OPTIONS = [
  { value: 'subscription', label: 'Signal Subscription' },
  { value: 'course', label: 'Course Purchase' },
  { value: 'mentorship', label: 'Mentorship Program' },
  { value: 'refund', label: 'Refund Transaction' },
];

export const PAYMENT_METHOD_OPTIONS = [
  { value: 'card', label: 'Debit/Credit Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'ussd', label: 'USSD Code' },
  { value: 'qr', label: 'QR Code' },
  { value: 'mobile_money', label: 'Mobile Money' },
];

export const CURRENCY_OPTIONS = [
  { value: 'USD', label: 'US Dollar ($)', symbol: '$' },
  { value: 'NGN', label: 'Nigerian Naira (₦)', symbol: '₦' },
  { value: 'EUR', label: 'Euro (€)', symbol: '€' },
  { value: 'GBP', label: 'British Pound (£)', symbol: '£' },
];

export const VERIFICATION_STATUS_OPTIONS = [
  { value: 'verified', label: 'Verified Payments' },
  { value: 'unverified', label: 'Unverified Payments' },
  { value: 'pending_verification', label: 'Pending Verification' },
];

// Helper functions
export function getPaymentStatusColor(status: PaymentTransaction['status']): string {
  const option = PAYMENT_STATUS_OPTIONS.find(opt => opt.value === status);
  return option?.color || 'gray';
}

export function getPaymentStatusLabel(status: PaymentTransaction['status']): string {
  const option = PAYMENT_STATUS_OPTIONS.find(opt => opt.value === status);
  return option?.label || status;
}

export function getCurrencySymbol(currency: string): string {
  const option = CURRENCY_OPTIONS.find(opt => opt.value === currency);
  return option?.symbol || currency;
}

export function formatPaymentAmount(amount: number, currency: string): string {
  const symbol = getCurrencySymbol(currency);
  return `${symbol}${amount.toLocaleString()}`;
}

export function calculateRefundableAmount(payment: PaymentTransaction): number {
  // Business logic for calculating refundable amount
  // This could consider fees, time since payment, etc.
  if (payment.status !== 'verified') return 0;
  
  // For now, return full amount minus processing fees
  const processingFee = payment.amount * 0.015; // 1.5% processing fee
  return Math.max(0, payment.amount - processingFee);
}

export function canRefundPayment(payment: PaymentTransaction): boolean {
  return payment.status === 'verified' && 
         payment.transaction_type !== 'refund' &&
         calculateRefundableAmount(payment) > 0;
}

export function canVerifyPayment(payment: PaymentTransaction): boolean {
  return ['pending', 'processing', 'failed'].includes(payment.status);
}

export function getPaymentRiskLevel(payment: PaymentTransaction): 'low' | 'medium' | 'high' {
  // Risk assessment logic
  if (payment.amount > 10000) return 'high'; // Large amounts
  if (payment.verification_attempts && payment.verification_attempts > 3) return 'high';
  if (payment.status === 'disputed') return 'high';
  if (payment.status === 'failed' && payment.verification_attempts) return 'medium';
  return 'low';
}