/**
 * Payment API Service
 * Handles all payment-related API calls
 * 
 * Created: November 10, 2025
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

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
}

export interface VerifyPaymentRequest {
  reference: string;
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
  
  // Try multiple token keys (different auth contexts use different keys)
  return localStorage.getItem('user_auth_token') 
    || localStorage.getItem('access_token')
    || null;
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
 * @returns Verification code and bot URL
 */
export async function generateTelegramCode(): Promise<{
  verification_code: string;
  bot_url: string;
  expires_at: string;
}> {
  console.log('🔐 Generating Telegram code...');
  console.log('API URL:', `${API_BASE_URL}/billing/telegram/generate-code/`);
  
  const token = getAuthToken();
  console.log('Auth token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
  
  const response = await fetch(
    `${API_BASE_URL}/billing/telegram/generate-code/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
    }
  );

  console.log('Response status:', response.status);
  console.log('Response ok:', response.ok);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Error response:', errorText);
    await handleApiError(response);
  }

  const data = await response.json();
  console.log('Success data:', data);
  return data;
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
