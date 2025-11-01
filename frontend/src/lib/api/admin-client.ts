// Enhanced Admin API Client for Subscription Management
import { 
  Subscription, 
  SubscriptionFilters, 
  SubscriptionListResponse,
  SubscriptionDetailResponse,
  AnalyticsResponse,
  PerformanceMetricsResponse,
  SubscriptionUpdateForm,
  PaymentVerificationRequest,
  TelegramActionRequest 
} from '../../types/subscription';

interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class AdminAPIClient {
  private baseURL: string;
  private authToken: string | null = null;

  constructor() {
    // Use environment variable or default to localhost
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  }

  // Authentication methods
  setAuthToken(token: string) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = null;
  }

  // Private method for making authenticated requests
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      };

      // Add authorization header if token exists
      if (this.authToken) {
        headers['Authorization'] = `Bearer ${this.authToken}`;
      }

      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          error: errorData.error || errorData.message || `HTTP ${response.status}`,
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API Request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Subscription Management Methods
  async getSubscriptions(params: {
    page?: number;
    limit?: number;
  } & SubscriptionFilters): Promise<APIResponse<SubscriptionListResponse>> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    return this.makeRequest<SubscriptionListResponse>(
      `/admin/subscriptions/?${queryParams.toString()}`
    );
  }

  async getSubscriptionDetail(subscriptionId: string): Promise<APIResponse<SubscriptionDetailResponse>> {
    return this.makeRequest<SubscriptionDetailResponse>(
      `/admin/subscriptions/${subscriptionId}/`
    );
  }

  async updateSubscription(
    subscriptionId: string, 
    updates: SubscriptionUpdateForm,
    reason?: string
  ): Promise<APIResponse<Subscription>> {
    return this.makeRequest<Subscription>(
      `/admin/subscriptions/${subscriptionId}/`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          ...updates,
          admin_reason: reason
        }),
      }
    );
  }

  async verifyPayment(
    subscriptionId: string,
    data?: PaymentVerificationRequest
  ): Promise<APIResponse<Subscription>> {
    return this.makeRequest<Subscription>(
      `/admin/subscriptions/${subscriptionId}/verify/`,
      {
        method: 'POST',
        body: JSON.stringify(data || {}),
      }
    );
  }

  async processRefund(
    subscriptionId: string,
    reason: string,
    amount?: number
  ): Promise<APIResponse<Subscription>> {
    return this.makeRequest<Subscription>(
      `/admin/subscriptions/${subscriptionId}/refund/`,
      {
        method: 'POST',
        body: JSON.stringify({
          reason,
          amount,
        }),
      }
    );
  }

  // Telegram Management Methods
  async performTelegramAction(
    subscriptionId: string,
    action: TelegramActionRequest
  ): Promise<APIResponse<{ status: string; message: string }>> {
    return this.makeRequest(
      `/admin/subscriptions/${subscriptionId}/telegram/`,
      {
        method: 'POST',
        body: JSON.stringify(action),
      }
    );
  }

  async getTelegramQueue(): Promise<APIResponse<{
    pending_additions: Subscription[];
    pending_removals: Subscription[];
    failed_operations: Subscription[];
  }>> {
    return this.makeRequest(
      '/admin/telegram/queue/'
    );
  }

  // Analytics Methods
  async getSubscriptionAnalytics(params: {
    period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
    days_back?: number;
  } = {}): Promise<APIResponse<AnalyticsResponse>> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    return this.makeRequest<AnalyticsResponse>(
      `/admin/analytics/dashboard/?${queryParams.toString()}`
    );
  }

  async getPerformanceMetrics(params: {
    hours?: number;
    category?: string;
  } = {}): Promise<APIResponse<PerformanceMetricsResponse>> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    return this.makeRequest<PerformanceMetricsResponse>(
      `/admin/performance/metrics/?${queryParams.toString()}`
    );
  }

  // Dashboard Methods
  async getDashboardMetrics(): Promise<APIResponse<{
    total_users: number;
    active_subscriptions: number;
    pending_payments: number;
    monthly_revenue: number;
    telegram_success_rate: number;
    recent_subscriptions: Subscription[];
    revenue_trend: number[];
  }>> {
    return this.makeRequest('/admin/dashboard/');
  }

  // Export Methods
  async exportSubscriptions(
    filters: SubscriptionFilters,
    format: 'csv' | 'xlsx' = 'csv'
  ): Promise<APIResponse<{ download_url: string }>> {
    return this.makeRequest(
      '/admin/export/',
      {
        method: 'POST',
        body: JSON.stringify({
          filters,
          format,
        }),
      }
    );
  }

  // Bulk Operations
  async bulkUpdateSubscriptions(
    subscriptionIds: string[],
    updates: Partial<SubscriptionUpdateForm>,
    reason: string
  ): Promise<APIResponse<{ updated_count: number; errors: string[] }>> {
    return this.makeRequest(
      '/admin/bulk-update/',
      {
        method: 'POST',
        body: JSON.stringify({
          subscription_ids: subscriptionIds,
          updates,
          reason,
        }),
      }
    );
  }

  async bulkTelegramAction(
    subscriptionIds: string[],
    action: 'add_to_group' | 'remove_from_group',
    groupName?: string
  ): Promise<APIResponse<{ 
    success_count: number; 
    error_count: number; 
    errors: string[] 
  }>> {
    return this.makeRequest(
      '/admin/bulk-telegram/',
      {
        method: 'POST',
        body: JSON.stringify({
          subscription_ids: subscriptionIds,
          action,
          group_name: groupName,
        }),
      }
    );
  }

  // Audit and Logging Methods
  async getAuditLogs(params: {
    page?: number;
    limit?: number;
    action_type?: string;
    admin_user?: string;
    sensitivity?: string;
    date_from?: string;
    date_to?: string;
  } = {}): Promise<APIResponse<{
    logs: any[];
    pagination: any;
  }>> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    return this.makeRequest(
      `/admin/audit-logs/?${queryParams.toString()}`
    );
  }

  // System Health Check
  async getSystemHealth(): Promise<APIResponse<{
    database_status: 'healthy' | 'degraded' | 'down';
    api_response_time: number;
    cache_status: 'healthy' | 'degraded' | 'down';
    telegram_status: 'healthy' | 'degraded' | 'down';
    last_checked: string;
  }>> {
    return this.makeRequest('/admin/health/');
  }
}

// Create and export a singleton instance
const adminAPIClient = new AdminAPIClient();
export { adminAPIClient as AdminAPIClient };

// Also export the class for testing
export { AdminAPIClient as AdminAPIClientClass };

// Export helper functions for authentication
export const setAdminAuthToken = (token: string) => {
  adminAPIClient.setAuthToken(token);
  
  // Optionally store in localStorage for persistence
  if (typeof window !== 'undefined') {
    localStorage.setItem('admin_auth_token', token);
  }
};

export const clearAdminAuthToken = () => {
  adminAPIClient.clearAuthToken();
  
  // Clear from localStorage
  if (typeof window !== 'undefined') {
    localStorage.removeItem('admin_auth_token');
  }
};

export const initializeAdminAuth = () => {
  // Initialize auth token from localStorage on app start
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('admin_auth_token');
    if (token) {
      adminAPIClient.setAuthToken(token);
    }
  }
};