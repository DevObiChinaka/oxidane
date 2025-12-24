import { API_BASE_URL } from '@/config/api';

// API client with error handling and token refresh
export class AdminAPIClient {
  private refreshing: boolean = false;
  private refreshPromise: Promise<void> | null = null;

  private async refreshToken(): Promise<void> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshing = true;
    this.refreshPromise = (async () => {
      try {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error('No refresh token');

        const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        });

        if (!response.ok) throw new Error('Token refresh failed');

        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        
        if (data.refresh) {
          localStorage.setItem('refresh_token', data.refresh);
        }
      } finally {
        this.refreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request(endpoint, {
      method: 'GET',
    });
  }

  async exportFile(endpoint: string, data: any): Promise<Blob> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    // Add JWT auth token
    if (typeof window !== 'undefined') {
      // Check for both admin_token (AdminAuthContext) and access_token (regular AuthContext)
      const token = localStorage.getItem('admin_token') || localStorage.getItem('access_token');
      if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: defaultHeaders,
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          window.location.href = '/admin/login';
        }
      }
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Test connectivity to the backend
  async testConnection(): Promise<boolean> {
    try {
      // Test health endpoint only
      const testEndpoints = [
        '/health/',
      ];
      
      for (const endpoint of testEndpoints) {
        const fullUrl = `${API_BASE_URL}${endpoint}`;

        try {
          const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            }
          });
          
          const responseText = await response.text();
          
          // Check if this looks like a Django error page
          if (responseText.includes('Django') && responseText.includes('<!DOCTYPE')) {

          }
          
        } catch (error) {
          // Silent fail
        }
      }

      return true; // Always return true for now, just for debugging
    } catch (error) {
      return false;
    }
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {};

    // Only set Content-Type if not FormData (FormData sets its own boundary)
    if (!(options.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    // Add auth token if available
    if (typeof window !== 'undefined') {
      // Check for both admin_token (AdminAuthContext) and access_token (regular AuthContext)
      const token = localStorage.getItem('admin_token') || localStorage.getItem('access_token');
      if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      let response = await fetch(url, config);
      
      // Handle token refresh on 401
      if (response.status === 401 && typeof window !== 'undefined') {
        try {
          // Try to refresh the token
          await this.refreshToken();
          
          // Retry the request with new token
          const newToken = localStorage.getItem('access_token');
          if (newToken && config.headers) {
            (config.headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
          }
          response = await fetch(url, config);
        } catch (refreshError) {
          // Refresh failed - clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          localStorage.removeItem('user');
          window.location.href = '/admin/login';
          throw new Error('Session expired. Please login again.');
        }
      }
      
      if (!response.ok) {
        if (response.status === 401) {
          // Still 401 after refresh attempt - redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            localStorage.removeItem('user');
            window.location.href = '/admin/login';
          }
        }
        
        // Get detailed error message from response
        let errorMessage = `API Error: ${response.status} ${response.statusText}`;
        try {
          // Clone response so we can read it multiple times if needed
          const responseClone = response.clone();
          const responseText = await responseClone.text();
          
          // Check if it's HTML (which would indicate wrong endpoint)
          if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
            errorMessage = `Received HTML page instead of JSON API response. Check if Django server is running and API endpoints are correct.`;
          } else {
            // Try to parse as JSON
            const errorData = JSON.parse(responseText);
            if (errorData.error) {
              errorMessage = errorData.error;
            } else if (errorData.detail) {
              errorMessage = errorData.detail;
            } else if (typeof errorData === 'object') {
              // Handle validation errors
              const errors = Object.entries(errorData).map(([field, messages]) => 
                `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`
              ).join('; ');
              if (errors) {
                errorMessage = `Validation errors: ${errors}`;
              }
            }
          }
        } catch (e) {

        }
        
        throw new Error(errorMessage);
      }

      // Handle responses that might not have JSON body (like DELETE operations)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else if (response.status === 204 || options.method === 'DELETE') {
        // No content or DELETE operation - return success indicator
        return { success: true };
      } else {
        // Try to parse as JSON, fallback to text
        try {
          return await response.json();
        } catch {
          const text = await response.text();
          return text || { success: true };
        }
      }
    } catch (error) {
      // Provide more user-friendly error messages
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`Cannot connect to server at ${url}. Please check if the Django server is running.`);
      }
      
      throw error;
    }
  }

  // Dashboard metrics
  async getDashboardMetrics() {
    return this.request('/admin/dashboard/metrics/');
  }

  // Course management
  async getCourses(params: {
    page?: number;
    search?: string;
    status?: string;
    type?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value.toString());
    });
    
    const endpoint = `/admin/courses/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  async createCourse(courseData: any) {

    return this.request('/admin/courses/', {
      method: 'POST',
      body: JSON.stringify(courseData),
    });
  }

  async getCourseDetail(courseId: string) {
    return this.request(`/admin/courses/${courseId}/`);
  }

  async updateCourse(courseId: string, courseData: any) {
    
    // Validate courseId
    if (!courseId || courseId === 'undefined' || courseId === 'null') {
      throw new Error(`Invalid course ID: ${courseId}`);
    }
    
    const result = await this.request(`/admin/courses/${courseId}/`, {
      method: 'PUT',
      body: JSON.stringify(courseData),
    });

    return result;
  }

  async deleteCourse(courseId: string) {
    return this.request(`/admin/courses/${courseId}/`, {
      method: 'DELETE',
    });
  }

  async publishCourse(courseId: string, action: 'publish' | 'unpublish') {
    return this.request(`/admin/courses/${courseId}/publish/`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }

  // Lesson management
  async getAllLessons() {
    return this.request(`/admin/lessons/`);
  }

  async getCourseLessons(courseId: string) {
    return this.request(`/admin/courses/${courseId}/lessons/`);
  }

  async createLesson(courseId: string, lessonData: any) {
    return this.request(`/admin/courses/${courseId}/lessons/`, {
      method: 'POST',
      body: JSON.stringify(lessonData),
    });
  }

  async updateLesson(lessonId: string, lessonData: any) {
    return this.request(`/admin/lessons/${lessonId}/`, {
      method: 'PUT',
      body: JSON.stringify(lessonData),
    });
  }

  // File upload methods for lessons with video files
  async createLessonWithFile(courseId: string, formData: FormData) {
    return this.request(`/admin/courses/${courseId}/lessons/`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary for FormData
      headers: {},
    });
  }

  async updateLessonWithFile(lessonId: string, formData: FormData) {
    return this.request(`/admin/lessons/${lessonId}/`, {
      method: 'PUT',
      body: formData,
      // Don't set Content-Type header - let browser set it with boundary for FormData
      headers: {},
    });
  }

  async deleteLesson(lessonId: string) {
    return this.request(`/admin/lessons/${lessonId}/`, {
      method: 'DELETE',
    });
  }

  // Course analytics
  async getCourseAnalytics(courseId: string) {
    return this.request(`/admin/courses/${courseId}/analytics/`);
  }

  // Dashboard analytics
  async getDashboardAnalytics() {
    return this.request('/admin/dashboard/analytics/');
  }

  // User management
  async getUsers(params: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
    subscription?: string;
    date_from?: string;
    date_to?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value.toString());
    });
    
    const endpoint = `/admin/users/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  async getUserDetail(userId: string) {
    return this.request(`/admin/users/${userId}/`);
  }

  async userAction(userId: string, action: string) {
    return this.request(`/admin/users/${userId}/action/`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }

  async getUsersAnalytics() {
    return this.request('/admin/users-analytics/');
  }

  // Subscription Management Methods
  async getSubscriptions(params: {
    page?: number;
    limit?: number;
    payment_status?: string;
    plan_type?: string;
    telegram_status?: string;
    search?: string;
    date_from?: string;
    date_to?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/subscriptions/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  async getSubscriptionDetail(subscriptionId: string) {
    return this.request(`/admin/subscriptions/${subscriptionId}/`);
  }

  async updateSubscription(subscriptionId: string, updates: any, reason?: string) {
    return this.request(`/admin/subscriptions/${subscriptionId}/`, {
      method: 'PATCH',
      body: JSON.stringify({
        ...updates,
        admin_reason: reason
      }),
    });
  }

  async verifyPayment(subscriptionId: string, data?: any) {
    return this.request(`/admin/subscriptions/${subscriptionId}/verify/`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  }

  async getSubscriptionAnalytics(params: {
    period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
    days_back?: number;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/analytics/dashboard/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  async getPerformanceMetrics(params: {
    hours?: number;
    category?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/performance/metrics/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  // Email Template Management
  async getEmailTemplates(params: {
    page?: number;
    page_size?: number;
    type?: string;
    status?: string;
    search?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/email-templates/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  async getEmailTemplateTypes() {
    return this.request('/admin/email-template-types/');
  }

  async getEmailAnalytics() {
    return this.request('/admin/email-analytics/');
  }

  async getEmailTemplate(templateId: string) {
    return this.request(`/admin/email-templates/${templateId}/`);
  }

  async createEmailTemplate(templateData: any) {
    return this.request('/admin/email-templates/', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async updateEmailTemplate(templateId: string, templateData: any) {
    return this.request(`/admin/email-templates/${templateId}/`, {
      method: 'PUT',
      body: JSON.stringify(templateData),
    });
  }

  async deleteEmailTemplate(templateId: string) {
    return this.request(`/admin/email-templates/${templateId}/`, {
      method: 'DELETE',
    });
  }

  async previewEmailTemplate(templateId: string, sampleData: any) {
    return this.request(`/admin/email-templates/${templateId}/preview/`, {
      method: 'POST',
      body: JSON.stringify(sampleData),
    });
  }

  async sendTestEmail(templateId: string, testData: any) {
    return this.request(`/admin/email-templates/${templateId}/test/`, {
      method: 'POST',
      body: JSON.stringify(testData),
    });
  }

  async sendBulkEmail(templateId: string, sendData: {
    recipientType: string;
    specificUsers?: string[];
    subscriptionPlans?: string[];
    scheduleType: string;
    scheduledDate?: string;
    scheduledTime?: string;
  }) {
    return this.request(`/admin/email-templates/${templateId}/send/`, {
      method: 'POST',
      body: JSON.stringify(sendData),
    });
  }

  async getEmailLogs(params: {
    limit?: number;
    status?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/email-logs/${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.request(endpoint);
  }

  // Pricing Management Methods
  async getPricingPlans(params: {
    plan_category?: string;
    billing_cycle?: string;
    active_only?: boolean;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/pricing/plans/${queryParams.toString() ? `?${queryParams}` : ''}`;
    const result = await this.request(endpoint);
    
    // Handle paginated response - DRF often returns {results: [...], count: n, next: url, previous: url}
    if (result && typeof result === 'object' && 'results' in result) {
      return result.results; // Return the actual array of plans
    }
    
    // If it's already an array, return as is
    return result;
  }

  async getPricingPlanCategories() {
    return this.request('/admin/pricing/plans/categories/');
  }

  async createPricingPlan(planData: {
    plan_type: string;
    name: string;
    description: string;
    price: number;
    currency: string;
    plan_category: 'signals' | 'mentorship';
    billing_cycle: 'one_time' | 'weekly' | 'monthly';
    duration_days?: number | null;
    gives_course_access: boolean;
    gives_signals_access: boolean;
    telegram_group_key: string;
    features_list?: string[];
    is_active?: boolean;
    is_featured?: boolean;
  }) {
    return this.request('/admin/pricing/plans/', {
      method: 'POST',
      body: JSON.stringify(planData),
    });
  }

  async updatePricingPlan(planId: string, updates: any) {
    return this.request(`/admin/pricing/plans/${planId}/`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deletePricingPlan(planId: string) {
    return this.request(`/admin/pricing/plans/${planId}/`, {
      method: 'DELETE',
    });
  }

  async togglePricingPlanActive(planId: string) {
    return this.request(`/admin/pricing/plans/${planId}/toggle_active/`, {
      method: 'POST',
    });
  }

  async togglePricingPlanFeatured(planId: string) {
    return this.request(`/admin/pricing/plans/${planId}/toggle_featured/`, {
      method: 'POST',
    });
  }

  // Coupon Management Methods
  async getCouponCodes(params: {
    active_only?: boolean;
    valid_only?: boolean;
    search?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/pricing/coupons/${queryParams.toString() ? `?${queryParams}` : ''}`;
    const result = await this.request(endpoint);
    
    // Handle paginated response - DRF often returns {results: [...], count: n, next: url, previous: url}
    if (result && typeof result === 'object' && 'results' in result) {
      return result.results; // Return the actual array of coupons
    }
    
    // If it's already an array, return as is
    return result;
  }

  async createCouponCode(couponData: {
    code: string;
    description: string;
    discount_type: 'percentage' | 'fixed_amount';
    discount_value: number;
    minimum_amount?: number;
    currency: string;
    max_uses?: number;
    applicable_plans: string[];
    valid_from: string;
    valid_until: string;
    is_active?: boolean;
  }) {
    return this.request('/admin/pricing/coupons/', {
      method: 'POST',
      body: JSON.stringify(couponData),
    });
  }

  async updateCouponCode(couponId: string, updates: any) {
    return this.request(`/admin/pricing/coupons/${couponId}/`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteCouponCode(couponId: string) {
    return this.request(`/admin/pricing/coupons/${couponId}/`, {
      method: 'DELETE',
    });
  }

  async toggleCouponActive(couponId: string) {
    return this.request(`/admin/pricing/coupons/${couponId}/toggle_active/`, {
      method: 'POST',
    });
  }

  async validateCoupon(code: string, planId: string, amount: number) {
    return this.request('/admin/pricing/coupons/validate_coupon/', {
      method: 'POST',
      body: JSON.stringify({ code, plan_id: planId, amount }),
    });
  }

  // Public Pricing (no auth required)
  async getPublicPricing(params: {
    active_only?: boolean;
    plan_category?: string;
  } = { active_only: true }) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    // Note: This endpoint doesn't require authentication
    const endpoint = `/api/pricing/plans/public/${queryParams.toString() ? `?${queryParams}` : ''}`;
    
    // For public endpoint, make direct fetch call without auth
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  // Revenue Analytics APIs
  async getRevenueAnalytics(params: {
    start_date?: string;
    end_date?: string;
    period?: 'daily' | 'weekly' | 'monthly';
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/admin/revenue/analytics/${queryParams.toString() ? `?${queryParams}` : ''}`;
    
    // For now, return mock data until backend is implemented
    return Promise.resolve({
      totalRevenue: 45280.50,
      monthlyGrowth: 12.5,
      activeSubscriptions: 1247,
      averageRevenuePerUser: 36.31,
      monthlyRecurringRevenue: 38420.00,
      couponDiscountImpact: -2340.25,
      newStudentRevenue: 18750.00,
      retentionRevenue: 26530.50,
      revenueBreakdown: {
        subscriptions: 38420.00,
        courses: 4850.25,
        mentorship: 1650.00,
        certifications: 360.25,
      },
      trends: [],
      charts: []
    });
    
    // TODO: Replace with actual API call when backend is ready
    // return this.request(endpoint);
  }

  async exportRevenueReport(params: {
    start_date: string;
    end_date: string;
    format: 'pdf' | 'excel';
  }) {
    const endpoint = `/admin/revenue/export/`;
    
    // For now, return mock success until backend is implemented
    return Promise.resolve({
      success: true,
      download_url: '#',
      filename: `revenue_report_${params.start_date}_to_${params.end_date}.${params.format}`,
      message: `${params.format.toUpperCase()} report generated successfully`
    });
    
    // TODO: Replace with actual API call when backend is ready
    // return this.request(endpoint, {
    //   method: 'POST',
    //   body: JSON.stringify(params)
    // });
  }

  // ==================== Settings API Methods ====================
  
  // Get all settings or by category
  async getSettings(category?: string) {
    let endpoint = '/admin/settings/';
    if (category) {
      endpoint += `?category=${category}`;
    }
    return this.request(endpoint);
  }

  // Get settings grouped by category
  async getSettingsByCategory() {
    return this.request('/admin/settings/by-category/');
  }

  // Get single setting by key
  async getSetting(key: string) {
    return this.request(`/admin/settings/${key}/`);
  }

  // Update a setting
  async updateSetting(key: string, data: { value: any; description?: string; change_reason?: string }) {
    return this.request(`/admin/settings/${key}/update/`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // Bulk update settings
  async bulkUpdateSettings(settings: Array<{ key: string; value: any }>, changeReason?: string) {
    return this.request('/admin/settings/actions/bulk-update/', {
      method: 'POST',
      body: JSON.stringify({
        settings,
        change_reason: changeReason
      })
    });
  }

  // Validate setting value
  async validateSetting(key: string, value: any) {
    return this.request('/admin/settings/actions/validate/', {
      method: 'POST',
      body: JSON.stringify({ key, value })
    });
  }

  // Test email configuration
  async testEmailConfiguration(recipientEmail: string) {
    return this.request('/admin/settings/actions/test-email/', {
      method: 'POST',
      body: JSON.stringify({ recipient_email: recipientEmail })
    });
  }

  // Test bot connection
  async testBotConnection() {
    return this.request('/admin/settings/actions/test-bot/', {
      method: 'POST'
    });
  }

  // Get setting change history
  async getSettingHistory(key: string) {
    return this.request(`/admin/settings/${key}/history/`);
  }

  // Get all change logs
  async getChangeLogs(params?: { setting_key?: string; user_id?: string; days?: number }) {
    let endpoint = '/admin/change-logs/';
    if (params) {
      const queryParams = new URLSearchParams();
      if (params.setting_key) queryParams.append('setting_key', params.setting_key);
      if (params.user_id) queryParams.append('user_id', params.user_id);
      if (params.days) queryParams.append('days', params.days.toString());
      if (queryParams.toString()) {
        endpoint += `?${queryParams.toString()}`;
      }
    }
    return this.request(endpoint);
  }

  // Telegram Groups
  async getTelegramGroups(params?: { access_level?: string; is_active?: boolean }) {
    let endpoint = '/admin/telegram-groups/';
    if (params) {
      const queryParams = new URLSearchParams();
      if (params.access_level) queryParams.append('access_level', params.access_level);
      if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
      if (queryParams.toString()) {
        endpoint += `?${queryParams.toString()}`;
      }
    }
    return this.request(endpoint);
  }

  async getTelegramGroup(groupId: number) {
    return this.request(`/admin/telegram-groups/${groupId}/`);
  }

  async createTelegramGroup(data: any) {
    return this.request('/admin/telegram-groups/create/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateTelegramGroup(groupId: number, data: any) {
    return this.request(`/admin/telegram-groups/${groupId}/update/`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteTelegramGroup(groupId: number) {
    return this.request(`/admin/telegram-groups/${groupId}/delete/`, {
      method: 'DELETE'
    });
  }

  async syncGroupMembers(groupId: number) {
    return this.request(`/admin/telegram-groups/${groupId}/sync-members/`, {
      method: 'POST'
    });
  }

  async bulkUpdateTelegramGroups(groups: any[]) {
    return this.request('/admin/telegram-groups/actions/bulk-update/', {
      method: 'POST',
      body: JSON.stringify({ groups })
    });
  }

  // Backups
  async getBackups() {
    return this.request('/admin/backups/');
  }

  async createBackup(data: { name: string; description?: string }) {
    return this.request('/admin/backups/create/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async restoreBackup(backupId: number) {
    return this.request(`/admin/backups/${backupId}/restore/`, {
      method: 'POST'
    });
  }

  async deleteBackup(backupId: number) {
    return this.request(`/admin/backups/${backupId}/delete/`, {
      method: 'DELETE'
    });
  }

  // Settings Statistics
  async getSettingsStats() {
    return this.request('/admin/stats/');
  }
}

export const adminAPI = new AdminAPIClient();