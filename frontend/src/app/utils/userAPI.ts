/**
 * User API Client
 * Handles all user-facing API requests with authentication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Helper Functions ====================

const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('user_auth_token');
};

// ==================== API Client Class ====================

class UserAPIClient {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Make authenticated API request
   */
  private async request(endpoint: string, options: RequestInit = {}) {
    const token = getAuthToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle different response statuses
    if (response.status === 401) {
      // Token expired or invalid - clear token and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('user_auth_token');
        window.location.href = '/auth';
      }
      throw new Error('Authentication required');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Make request with FormData (for file uploads)
   */
  private async uploadRequest(endpoint: string, formData: FormData) {
    const token = getAuthToken();

    const headers: HeadersInit = {};

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || error.message || 'Upload failed');
    }

    return response.json();
  }

  // ==================== Authentication APIs ====================

  /**
   * Login with email and password (Step 1 - sends OTP)
   */
  async login(email: string, password: string) {
    return this.request('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  /**
   * Verify OTP and complete login (Step 2)
   */
  async verifyLoginOTP(sessionToken: string, otp: string) {
    return this.request('/api/auth/verify-login-otp/', {
      method: 'POST',
      body: JSON.stringify({ session_token: sessionToken, otp }),
    });
  }

  /**
   * Resend login OTP
   */
  async resendLoginOTP(sessionToken: string) {
    return this.request('/api/auth/resend-login-otp/', {
      method: 'POST',
      body: JSON.stringify({ session_token: sessionToken }),
    });
  }

  /**
   * Register new user (Step 1 - sends OTP)
   */
  async register(name: string, email: string, password: string) {
    return this.request('/api/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
  }

  /**
   * Verify registration OTP
   */
  async verifyRegistrationOTP(email: string, otp: string) {
    return this.request('/api/auth/verify-email-otp/', {
      method: 'POST',
      body: JSON.stringify({ email, otp }),
    });
  }

  // ==================== User Profile APIs ====================

  /**
   * Get current user profile
   */
  async getProfile() {
    return this.request('/auth/profile/');
  }

  /**
   * Update user profile
   */
  async updateProfile(data: {
    first_name?: string;
    last_name?: string;
    phone?: string;
    bio?: string;
    location?: string;
  }) {
    return this.request('/auth/profile/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File) {
    const formData = new FormData();
    formData.append('avatar', file);
    return this.uploadRequest('/auth/profile/avatar/', formData);
  }

  /**
   * Delete user avatar
   */
  async deleteAvatar() {
    return this.request('/auth/profile/avatar/', {
      method: 'DELETE',
    });
  }

  // ==================== Dashboard APIs ====================

  /**
   * Get dashboard data (overview, stats, recent activity)
   */
  async getDashboard() {
    return this.request('/api/user/dashboard/');
  }

  /**
   * Get user activity feed
   */
  async getActivity(limit: number = 10) {
    return this.request(`/api/user/activity/?limit=${limit}`);
  }

  // ==================== Subscription APIs ====================

  /**
   * Get user subscriptions
   */
  async getSubscriptions() {
    return this.request('/api/user/subscriptions/');
  }

  /**
   * Get subscription details
   */
  async getSubscriptionDetail(subscriptionId: string) {
    return this.request(`/api/user/subscriptions/${subscriptionId}/`);
  }

  // ==================== Course APIs ====================

  /**
   * Get user's enrolled courses
   */
  async getEnrolledCourses() {
    return this.request('/api/user/courses/');
  }

  /**
   * Get course details
   */
  async getCourseDetail(courseId: string) {
    return this.request(`/api/courses/${courseId}/`);
  }

  /**
   * Enroll in a course
   */
  async enrollCourse(courseId: string) {
    return this.request(`/api/courses/${courseId}/enroll/`, {
      method: 'POST',
    });
  }

  /**
   * Get course progress
   */
  async getCourseProgress(courseId: string) {
    return this.request(`/api/courses/${courseId}/progress/`);
  }

  /**
   * Mark lesson as complete
   */
  async markLessonComplete(lessonId: string, watchTime?: number) {
    return this.request(`/api/courses/lessons/${lessonId}/complete/`, {
      method: 'POST',
      body: JSON.stringify({ watch_time: watchTime }),
    });
  }

  // ==================== Settings APIs ====================

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string) {
    return this.request('/api/user/change-password/', {
      method: 'PUT',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  /**
   * Get user preferences
   */
  async getPreferences() {
    return this.request('/api/user/preferences/');
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: {
    email_notifications?: boolean;
    course_updates?: boolean;
    subscription_reminders?: boolean;
    payment_confirmations?: boolean;
    marketing_emails?: boolean;
    telegram_notifications?: boolean;
  }) {
    return this.request('/api/user/preferences/', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // ==================== Public APIs (No Auth Required) ====================

  /**
   * Get public course catalog
   */
  async getPublicCourses(params?: {
    search?: string;
    category?: string;
    difficulty?: string;
    page?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.difficulty) queryParams.append('difficulty', params.difficulty);
    if (params?.page) queryParams.append('page', params.page.toString());

    const queryString = queryParams.toString();
    return this.request(`/api/courses/${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get public pricing plans
   */
  async getPublicPricing() {
    return this.request('/api/pricing/public/');
  }

  /**
   * Validate coupon code
   */
  async validateCoupon(code: string, planId: string) {
    return this.request('/api/pricing/coupons/validate/', {
      method: 'POST',
      body: JSON.stringify({ code, plan_id: planId }),
    });
  }
}

// ==================== Export Singleton Instance ====================

export const userAPI = new UserAPIClient();

// Export class for testing or custom instances
export default UserAPIClient;
