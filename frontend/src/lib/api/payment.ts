/**
 * Payment API Service
 * Handles all payment-related API calls
 * 
 * Created: November 10, 2025
 */

import { API_BASE_URL } from '@/config/api';

// ============================================================================
// Types
// ============================================================================

export interface InitializePaymentRequest {
  plan_id: string;
  currency?: 'NGN' | 'USD';
  coupon_code?: string;
  gateway?: 'paystack' | 'stripe';
  callback_url?: string;
}

export interface InitializePaymentResponse {
  success: boolean;
  payment_url: string;
  reference: string;
  amount: number;
  processing_fee: number;
  total_amount: number;
  currency: string;
  gateway: string;
  exchange_rate?: number;
  paystack_public_key?: string;
  is_trial?: boolean;
  trial_days?: number;
  plan_price?: number;
}

export interface VerifyPaymentRequest {
  reference: string;
}

export interface CheckPendingPaymentRequest {
  plan_id: string;
}

export interface CheckPendingPaymentResponse {
  has_pending: boolean;
  reference?: string;
  payment_url?: string;
  amount?: number;
  currency?: string;
  created_at?: string;
  payment_id?: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  message: string;
  payment: {
    id: string;
    reference: string;
    amount: number;
    currency: string;
    status: string;
    gateway: string;
    paid_at?: string;
  };
  subscription?: {
    id: string;
    plan_name: string;
    status: string;
    start_date: string;
    end_date: string;
  };
  telegram?: {
    groups_added: string[];
    groups_failed: any[];
  };
}

export interface ValidateCouponRequest {
  code: string;
  plan_id?: string;
  amount?: number;
  user_id?: string;
}

export interface ValidateCouponResponse {
  valid: boolean;
  code?: string;
  discount_type?: 'percentage' | 'fixed';
  discount_value?: number;
  discount_display?: string;
  description?: string;
  message?: string;
  original_price?: number;
  discount_amount?: number;
  final_price?: number;
  savings_percentage?: number;
  error?: string;
  error_code?: string;
}

export interface PaymentHistoryParams {
  page?: number;
  page_size?: number;
  status?: string;
  gateway?: string;
  start_date?: string;
  end_date?: string;
}

export interface PaymentHistoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Array<{
    id: string;
    reference: string;
    amount: number;
    processing_fee: number;
    total_amount: number;
    currency: string;
    status: string;
    gateway: string;
    plan_name?: string;
    created_at: string;
    paid_at?: string;
  }>;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get authentication token from localStorage
 */
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // Primary: user_auth_token (set by UserAuthContext and NewAuthForm after fix)
  // Fallback: access_token (for users who logged in before the fix)
  const token = localStorage.getItem('user_auth_token') || localStorage.getItem('access_token');
  
  // If we found token in access_token but not user_auth_token, copy it over
  if (!localStorage.getItem('user_auth_token') && localStorage.getItem('access_token')) {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      localStorage.setItem('user_auth_token', accessToken);
    }
  }
  
  return token;
};

/**
 * Create headers for authenticated requests
 */
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Handle API errors
 */
const handleApiError = async (response: Response): Promise<never> => {
  let errorMessage = 'An error occurred';
  
  try {
    const errorData = await response.json();
    errorMessage = errorData.error || errorData.detail || errorData.message || errorMessage;
  } catch {
    errorMessage = response.statusText || errorMessage;
  }
  
  throw new Error(errorMessage);
};

// ============================================================================
// API Functions
// ============================================================================

/**
 * Initialize a payment transaction
 * 
 * @param request - Payment initialization data
 * @returns Payment URL and transaction details
 */
export async function initializePayment(
  request: InitializePaymentRequest
): Promise<InitializePaymentResponse> {
  const response = await fetch(`${API_BASE_URL}/payments/initialize/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Check for pending payment
 * Prevents duplicate charges and allows resuming interrupted payments
 * 
 * @param request - Plan ID to check
 * @returns Pending payment details if exists
 */
export async function checkPendingPayment(
  request: CheckPendingPaymentRequest
): Promise<CheckPendingPaymentResponse> {
  const response = await fetch(`${API_BASE_URL}/payments/check-pending/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Verify a payment transaction
 * 
 * @param request - Payment reference to verify
 * @returns Verification result and subscription details
 */
export async function verifyPayment(
  request: VerifyPaymentRequest
): Promise<VerifyPaymentResponse> {
  const response = await fetch(`${API_BASE_URL}/payments/verify/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Validate a coupon code
 * 
 * @param request - Coupon code and optional plan ID
 * @returns Coupon validity and discount details
 */
export async function validateCoupon(
  request: ValidateCouponRequest
): Promise<ValidateCouponResponse> {
  const response = await fetch(
    `${API_BASE_URL}/v1/subscriptions/validate-coupon/validate/`,
    {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: request.code,
        plan_id: request.plan_id,
        amount: request.amount,
        user_id: request.user_id,
      }),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Get payment history for the authenticated user
 * 
 * @param params - Pagination and filter parameters
 * @returns List of payment transactions
 */
export async function getPaymentHistory(
  params?: PaymentHistoryParams
): Promise<PaymentHistoryResponse> {
  const queryParams = new URLSearchParams();
  
  if (params) {
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.gateway) queryParams.append('gateway', params.gateway);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
  }

  const response = await fetch(
    `${API_BASE_URL}/payments/history/?${queryParams.toString()}`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Download invoice for a payment
 * 
 * @param paymentId - Payment ID
 * @returns Invoice PDF blob
 */
export async function downloadInvoice(paymentId: string): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/payments/${paymentId}/invoice/`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const blob = await response.blob();
  return blob;
}

/**
 * Helper: Download invoice and trigger browser download
 * 
 * @param paymentId - Payment ID
 * @param filename - Optional custom filename
 */
export async function downloadInvoiceFile(
  paymentId: string,
  filename?: string
): Promise<void> {
  const blob = await downloadInvoice(paymentId);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || `invoice-${paymentId}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Get current user's billing profile
 * 
 * @returns Billing profile with telegram status
 */
export async function getBillingProfile(): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/status/`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Generate Telegram verification code
 * 
 * @returns Verification code and deep link, OR already verified status
 */
export async function generateTelegramCode(): Promise<{
  verification_code?: string;
  deep_link?: string;
  bot_username?: string;
  expires_at?: string;
  already_verified?: boolean;
  telegram_verified?: boolean;
  telegram_username?: string;
  telegram_user_id?: string;
  message?: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/generate-code/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    
    // Parse error and throw with proper message
    let errorMessage = 'Failed to generate verification code';
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.error || errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data;
}

/**
 * Verify Telegram username and send confirmation code
 * 
 * @param verificationCode - The verification code from generate step
 * @param telegramUsername - User's Telegram username (with or without @)
 * @returns Success status and message
 */
export async function verifyTelegramUsername(
  verificationCode: string,
  telegramUsername: string
): Promise<{
  success: boolean;
  message: string;
  telegram_username: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/verify-username/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        verification_code: verificationCode,
        telegram_username: telegramUsername,
      }),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}

/**
 * Confirm Telegram verification with code sent via Telegram
 * 
 * @param verificationCode - The verification code from generate step
 * @param confirmationCode - The 6-digit code sent to user's Telegram
 * @returns Success status and verified username
 */
export async function confirmTelegramVerification(
  verificationCode: string,
  confirmationCode: string
): Promise<{
  success: boolean;
  message: string;
  telegram_username: string;
  verified_at: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/confirm/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        verification_code: verificationCode,
        confirmation_code: confirmationCode,
      }),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}

/**
 * Check Telegram verification status
 * 
 * @returns Current telegram verification status
 */
export async function checkTelegramStatus(): Promise<{
  telegram_verified: boolean;
  telegram_username?: string;
  telegram_user_id?: string;
  verification_error?: string | null;
}> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/status/`,
    {
      method: 'GET',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Unlink Telegram account
 */
export async function unlinkTelegram(): Promise<{ success: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/unlink/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  const data = await response.json();
  return data;
}

/**
 * Check if purchasing a plan would conflict with existing subscriptions
 */
export interface CheckConflictResponse {
  can_purchase: boolean;
  conflict: boolean;
  existing_subscription?: {
    id: string;
    plan_id: string;
    plan_name: string;
    billing_period: string;
    billing_period_display: string;
    end_date: string;
    auto_renew: boolean;
  };
  message?: string;
}

export async function checkSubscriptionConflict(planId: string): Promise<CheckConflictResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/payments/check-conflict/?plan_id=${planId}`,
      {
        method: 'GET',
        headers: getAuthHeaders(),
      }
    );

    if (!response.ok) {
      // If endpoint doesn't exist or returns error, return no conflict
      return { has_conflict: false, conflict_type: null, message: null };
    }

    return response.json();
  } catch (error) {
    // If any error occurs, assume no conflict to allow purchase
    return { has_conflict: false, conflict_type: null, message: null };
  }
}
