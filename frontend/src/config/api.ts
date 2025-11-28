/**
 * Centralized API Configuration
 * Single source of truth for all API endpoints
 */

// Base API URL - defaults to localhost for development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Remove trailing /api if present to avoid duplication
const BASE = API_BASE_URL.replace(/\/api\/?$/, '');

/**
 * API Endpoints Configuration
 * All endpoints are organized by feature/module
 */
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: `${BASE}/api/auth/login/`,
    loginWithOtp: `${BASE}/api/auth/login-with-otp/`,
    register: `${BASE}/api/auth/register/`,
    token: `${BASE}/api/auth/token/`,
    tokenRefresh: `${BASE}/api/auth/token/refresh/`,
    logout: `${BASE}/api/auth/logout/`,
    checkEmail: `${BASE}/api/auth/check-email/`,
    verifyEmail: `${BASE}/api/auth/verify-email/`,
    verifyEmailOtp: `${BASE}/api/auth/verify-email-otp/`,
    verifyLoginOtp: `${BASE}/api/auth/verify-login-otp/`,
    resendVerificationOtp: `${BASE}/api/auth/resend-verification-otp/`,
    resendLoginOtp: `${BASE}/api/auth/resend-login-otp/`,
    forgotPassword: `${BASE}/api/auth/forgot-password/`,
    resetPassword: `${BASE}/api/auth/reset-password/`,
    profile: `${BASE}/api/auth/profile/`,
  },

  // Admin
  admin: {
    // Dashboard
    setupStatus: `${BASE}/api/admin/setup/status/`,
    dashboard: `${BASE}/api/admin/dashboard/`,
    
    // User Management
    users: `${BASE}/api/admin/users/`,
    userDetail: (userId: string) => `${BASE}/api/admin/users/${userId}/`,
    
    // Profile
    profile: `${BASE}/api/admin/profile/`,
    changePassword: `${BASE}/api/admin/change-password/`,
    requestEmailChange: `${BASE}/api/admin/request-email-change/`,
    verifyEmailChange: `${BASE}/api/admin/verify-email-change/`,
    requestEmailVerification: `${BASE}/api/admin/request-email-verification/`,
    verifyEmail: `${BASE}/api/admin/verify-email/`,
    
    // Subscriptions Management
    subscriptions: `${BASE}/api/admin/subscriptions-management/`,
    subscriptionDetail: (id: string) => `${BASE}/api/admin/subscriptions-management/${id}/`,
    
    // Analytics
    emailAnalytics: `${BASE}/api/admin/email-analytics/`,
    revenueAnalytics: `${BASE}/api/admin/revenue/analytics/`,
    revenueExport: `${BASE}/api/admin/revenue/export/`,
    
    // Courses
    courses: `${BASE}/api/admin/courses/`,
    courseDetail: (id: string) => `${BASE}/api/admin/courses/${id}/`,
    
    // Plans
    plans: `${BASE}/api/admin/plans/`,
    planDetail: (id: string) => `${BASE}/api/admin/plans/${id}/`,
    
    // Features
    features: `${BASE}/api/admin/features/`,
    featureDetail: (id: string) => `${BASE}/api/admin/features/${id}/`,
    
    // Coupons
    coupons: `${BASE}/api/admin/coupons/`,
    couponDetail: (id: string) => `${BASE}/api/admin/coupons/${id}/`,
    
    // Telegram Settings
    telegram: {
      config: `${BASE}/api/admin/telegram/config/`,
      testConnection: `${BASE}/api/admin/telegram/test-connection/`,
      groups: `${BASE}/api/admin/telegram/groups/`,
      groupDetail: (id: string) => `${BASE}/api/admin/telegram/groups/${id}/`,
      discoverChats: `${BASE}/api/admin/telegram/discover-chats/`,
    },
    
    // Email Settings
    email: {
      config: `${BASE}/api/admin/email/config/`,
      configDetail: (id: string) => `${BASE}/api/admin/email/config/${id}/`,
    },
    
    // Payment Settings
    payment: {
      config: `${BASE}/api/admin/payment/config/`,
    },
    
    // Payments/Transactions
    payments: {
      transactions: `${BASE}/api/admin/payments/transactions/`,
      transactionDetail: (id: string) => `${BASE}/api/admin/payments/transactions/${id}/`,
    },
  },

  // User/Public
  user: {
    // Subscriptions
    subscriptionPlans: `${BASE}/api/v1/subscriptions/plans/`,
    subscriptionPlanDetail: (id: string) => `${BASE}/api/v1/subscriptions/plans/${id}/`,
    mySubscriptions: `${BASE}/api/subscriptions/my-subscriptions/`,
    
    // Courses
    courses: `${BASE}/api/courses/`,
    courseDetail: (id: string) => `${BASE}/api/courses/${id}/`,
    lessonDetail: (lessonId: string) => `${BASE}/api/lessons/${lessonId}/`,
    videoEmbed: (lessonId: string) => `${BASE}/api/lessons/${lessonId}/video-embed/`,
    
    // Payment
    paymentMethods: `${BASE}/api/payment-methods/`,
    chargeSavedCard: `${BASE}/api/payments/charge-saved-card/`,
    
    // Currency
    currencyConvert: `${BASE}/api/v1/currency/convert/`,
  },

  // Checkout
  checkout: {
    initiate: `${BASE}/api/checkout/initiate/`,
    verify: `${BASE}/api/checkout/verify/`,
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
