// Subscription management type definitions
export interface Subscription {
  id: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    username?: string;
  };
  plan_type: 'weekly' | 'monthly' | 'vip';
  pricing_plan?: {
    id: string;
    name: string;
    price: number;
    currency: string;
  };
  paystack_reference: string;
  amount_paid: number;
  currency: string;
  payment_status: 'pending' | 'verified' | 'failed' | 'refunded';
  payment_verified_at?: string;
  subscription_start?: string;
  subscription_end?: string;
  auto_renewal: boolean;
  telegram_username: string;
  telegram_group_name?: string;
  telegram_status: 'not_added' | 'pending_add' | 'added' | 'removed' | 'failed_add';
  telegram_added_at?: string;
  admin_notes?: string;
  created_at: string;
  updated_at: string;
  is_active?: boolean;
  days_remaining?: number;
}

export interface SubscriptionFilters {
  payment_status?: string;
  plan_type?: string;
  telegram_status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  user_email?: string;
}

export interface SubscriptionAnalytics {
  total_subscriptions: number;
  new_subscriptions: number;
  renewed_subscriptions: number;
  cancelled_subscriptions: number;
  total_revenue: number;
  average_subscription_value: number;
  refunded_amount: number;
  plan_type_breakdown: Record<string, {
    count: number;
    revenue: number;
  }>;
  verified_payments: number;
  pending_payments: number;
  failed_payments: number;
  telegram_success_rate: number;
  telegram_additions: number;
  telegram_failures: number;
  growth_rate: number;
}

export interface SubscriptionChangeLog {
  id: string;
  change_type: string;
  field_name: string;
  previous_value: unknown;
  new_value: unknown;
  reason: string;
  business_justification?: string;
  financial_impact?: number;
  timestamp: string;
  admin_user: {
    email: string;
    first_name: string;
    last_name: string;
  };
}

export interface AuditLog {
  id: string;
  admin_user: {
    email: string;
    first_name: string;
    last_name: string;
  };
  action_type: string;
  sensitivity: 'LOW' | 'NORMAL' | 'FINANCIAL' | 'HIGH' | 'CRITICAL';
  status: 'SUCCESS' | 'FAILED' | 'PARTIAL' | 'PENDING';
  timestamp: string;
  ip_address?: string;
  duration_ms?: number;
  action_description: string;
  error_message?: string;
}

export interface PerformanceMetric {
  id: string;
  category: 'database' | 'api' | 'telegram' | 'payment' | 'admin' | 'system';
  metric_name: string;
  response_time_ms?: number;
  throughput_per_second?: number;
  error_rate_percent?: number;
  endpoint_path?: string;
  timestamp: string;
}

// API Response types
export interface PaginationInfo {
  current_page: number;
  total_pages: number;
  total_items: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  pagination: PaginationInfo;
  filters_applied: SubscriptionFilters;
}

export interface SubscriptionDetailResponse {
  subscription: Subscription;
  change_history: SubscriptionChangeLog[];
  audit_logs: AuditLog[];
  performance_metrics?: PerformanceMetric[];
}

export interface AnalyticsResponse {
  period: string;
  days_analyzed: number;
  date_range: {
    start: string;
    end: string;
  };
  summary: SubscriptionAnalytics;
  daily_data: Array<{
    date: string;
    total_subscriptions: number;
    new_subscriptions: number;
    total_revenue: number;
    verified_payments: number;
    pending_payments: number;
    failed_payments: number;
    refunded_amount: number;
    telegram_success_rate: number;
    plan_breakdown: Record<string, { count: number; revenue: number }>;
    admin_actions_count: number;
  }>;
  performance_metrics: {
    avg_response_time?: number;
    avg_throughput?: number;
    avg_error_rate?: number;
  };
  cache_info: {
    cached: boolean;
    generated_at: string;
  };
}

export interface PerformanceMetricsResponse {
  time_period: string;
  summary: Record<string, {
    avg_response_time: number;
    avg_error_rate: number;
    avg_throughput: number;
    total_requests: number;
  }>;
  alerts: Array<{
    type: string;
    endpoint: string;
    response_time: number;
    timestamp: string;
  }>;
  total_requests: number;
  generated_at: string;
}

// Form data types
export interface SubscriptionUpdateForm {
  payment_status?: 'pending' | 'verified' | 'failed' | 'refunded';
  amount_paid?: number;
  subscription_start?: string;
  subscription_end?: string;
  telegram_status?: 'not_added' | 'pending_add' | 'added' | 'removed' | 'failed_add';
  telegram_group_name?: string;
  admin_notes?: string;
  auto_renewal?: boolean;
}

export interface PaymentVerificationRequest {
  paystack_reference: string;
  force_verify?: boolean;
  admin_notes?: string;
}

export interface TelegramActionRequest {
  action: 'add_to_group' | 'remove_from_group' | 'send_message';
  group_name?: string;
  message?: string;
  admin_notes?: string;
}

// Status and plan type options for forms
export const PAYMENT_STATUS_OPTIONS = [
  { value: 'pending', label: 'Payment Pending', color: 'yellow' },
  { value: 'verified', label: 'Payment Verified', color: 'green' },
  { value: 'failed', label: 'Payment Failed', color: 'red' },
  { value: 'refunded', label: 'Refunded', color: 'gray' },
] as const;

export const PLAN_TYPE_OPTIONS = [
  { value: 'weekly', label: 'Weekly Signals', duration: '7 days' },
  { value: 'monthly', label: 'Monthly Signals', duration: '30 days' },
  { value: 'vip', label: 'VIP Signals', duration: '30 days' },
] as const;

export const TELEGRAM_STATUS_OPTIONS = [
  { value: 'not_added', label: 'Not Added to Group', color: 'gray' },
  { value: 'pending_add', label: 'Pending Addition', color: 'yellow' },
  { value: 'added', label: 'Added to Group', color: 'green' },
  { value: 'removed', label: 'Removed from Group', color: 'red' },
  { value: 'failed_add', label: 'Failed to Add', color: 'red' },
] as const;

export const SENSITIVITY_LEVELS = [
  { value: 'LOW', label: 'Low', description: 'General operations' },
  { value: 'NORMAL', label: 'Normal', description: 'Standard admin actions' },
  { value: 'FINANCIAL', label: 'Financial', description: 'Payment/subscription related' },
  { value: 'HIGH', label: 'High', description: 'Critical security operations' },
  { value: 'CRITICAL', label: 'Critical', description: 'System-wide changes' },
] as const;