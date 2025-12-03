/**
 * Centralized API Configuration
 * Single source of truth for all API endpoints
 */

// Base API URL - defaults to localhost for development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * API Endpoints Configuration
 * All endpoints are organized by feature/module
 * Note: API_BASE_URL already includes /api, so endpoints should start with the path after /api
 */
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: `${API_BASE_URL}/auth/login/`,
    loginWithOtp: `${API_BASE_URL}/auth/login-with-otp/`,
    register: `${API_BASE_URL}/auth/register/`,
    token: `${API_BASE_URL}/auth/token/`,
    tokenRefresh: `${API_BASE_URL}/auth/token/refresh/`,
    logout: `${API_BASE_URL}/auth/logout/`,
    checkEmail: `${API_BASE_URL}/auth/check-email/`,
    verifyEmail: `${API_BASE_URL}/auth/verify-email/`,
    verifyEmailOtp: `${API_BASE_URL}/auth/verify-email-otp/`,
    verifyLoginOtp: `${API_BASE_URL}/auth/verify-login-otp/`,
    resendVerificationOtp: `${API_BASE_URL}/auth/resend-verification-otp/`,
    resendLoginOtp: `${API_BASE_URL}/auth/resend-login-otp/`,
    forgotPassword: `${API_BASE_URL}/auth/password-reset-otp/request/`,
    resetPassword: `${API_BASE_URL}/auth/password-reset-otp/verify/`,
    profile: `${API_BASE_URL}/auth/profile/`,
  },

  // Admin Authentication (2FA with OTP)
  adminAuth: {
    loginRequest: `${API_BASE_URL}/admin-auth/login/`,
    verifyOtp: `${API_BASE_URL}/admin-auth/verify-otp/`,
  },

  // Admin
  admin: {
    // Dashboard
    setupStatus: `${API_BASE_URL}/admin/setup/status/`,
    dashboard: `${API_BASE_URL}/admin/dashboard/`,
    
    // User Management
    users: `${API_BASE_URL}/admin/users/`,
    userDetail: (userId: string) => `${API_BASE_URL}/admin/users/${userId}/`,
    
    // Profile
    profile: `${API_BASE_URL}/admin/profile/`,
    changePassword: `${API_BASE_URL}/admin/change-password/`,
    requestEmailChange: `${API_BASE_URL}/admin/request-email-change/`,
    verifyEmailChange: `${API_BASE_URL}/admin/verify-email-change/`,
    requestEmailVerification: `${API_BASE_URL}/admin/request-email-verification/`,
    verifyEmail: `${API_BASE_URL}/admin/verify-email/`,
    
    // Subscriptions Management
    subscriptions: `${API_BASE_URL}/admin/subscriptions-management/`,
    subscriptionDetail: (id: string) => `${API_BASE_URL}/admin/subscriptions-management/${id}/`,
    
    // Analytics
    emailAnalytics: `${API_BASE_URL}/admin/email-analytics/`,
    revenueAnalytics: `${API_BASE_URL}/admin/revenue/analytics/`,
    revenueExport: `${API_BASE_URL}/admin/revenue/export/`,
    
    // Courses
    courses: `${API_BASE_URL}/admin/courses/`,
    courseDetail: (id: string) => `${API_BASE_URL}/admin/courses/${id}/`,
    
    // Plans
    plans: `${API_BASE_URL}/admin/plans/`,
    planDetail: (id: string) => `${API_BASE_URL}/admin/plans/${id}/`,
    
    // Features
    features: `${API_BASE_URL}/admin/features/`,
    featureDetail: (id: string) => `${API_BASE_URL}/admin/features/${id}/`,
    
    // Coupons
    coupons: `${API_BASE_URL}/admin/coupons/`,
    couponDetail: (id: string) => `${API_BASE_URL}/admin/coupons/${id}/`,
    
    // Telegram Settings
    telegram: {
      config: `${API_BASE_URL}/admin/telegram/config/`,
      testConnection: `${API_BASE_URL}/admin/telegram/test-connection/`,
      groups: `${API_BASE_URL}/admin/telegram/groups/`,
      groupDetail: (id: string) => `${API_BASE_URL}/admin/telegram/groups/${id}/`,
      discoverChats: `${API_BASE_URL}/admin/telegram/discover-chats/`,
    },
    
    // Email Settings
    email: {
      config: `${API_BASE_URL}/admin/email/config/`,
      configDetail: (id: string) => `${API_BASE_URL}/admin/email/config/${id}/`,
    },
    
    // Payment Settings
    payment: {
      config: `${API_BASE_URL}/admin/payment/config/`,
    },
    
    // Payments/Transactions
    payments: {
      transactions: `${API_BASE_URL}/admin/payments/transactions/`,
      transactionDetail: (id: string) => `${API_BASE_URL}/admin/payments/transactions/${id}/`,
    },
  },

  // User/Public
  user: {
    // Subscriptions
    subscriptionPlans: `${API_BASE_URL}/v1/subscriptions/plans/`,
    subscriptionPlanDetail: (id: string) => `${API_BASE_URL}/v1/subscriptions/plans/${id}/`,
    mySubscriptions: `${API_BASE_URL}/subscriptions/my-subscriptions/`,
    
    // Courses
    courses: `${API_BASE_URL}/courses/`,
    courseDetail: (id: string) => `${API_BASE_URL}/courses/${id}/`,
    lessonDetail: (lessonId: string) => `${API_BASE_URL}/lessons/${lessonId}/`,
    videoEmbed: (lessonId: string) => `${API_BASE_URL}/lessons/${lessonId}/video-embed/`,
    
    // Payment
    paymentMethods: `${API_BASE_URL}/payment-methods/`,
    chargeSavedCard: `${API_BASE_URL}/payments/charge-saved-card/`,
    
    // Currency
    currencyConvert: `${API_BASE_URL}/v1/currency/convert/`,
  },

  // Checkout
  checkout: {
    initiate: `${API_BASE_URL}/checkout/initiate/`,
    verify: `${API_BASE_URL}/checkout/verify/`,
  },
} as const;

/**
 * Helper function to build API URL with query parameters
 */
export function buildApiUrl(endpoint: string, params?: Record<string, string | number | boolean>): string {
  if (!params) return endpoint;
  
  const url = new URL(endpoint);
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.append(key, String(value));
  });
  
  return url.toString();
}

/**
 * Helper function to get authorization headers
 */
export function getAuthHeaders(token?: string): HeadersInit {
  const accessToken = token || (typeof window !== 'undefined' ? localStorage.getItem('access_token') : null);
  
  return {
    'Content-Type': 'application/json',
    ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
  };
}

export default API_ENDPOINTS;
