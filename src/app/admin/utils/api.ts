import { API_BASE_URL } from '../config/api';

// API client with error handling
export class AdminAPIClient {
  // Test connectivity to the backend with comprehensive debugging
  async testConnection(): Promise<boolean> {
    try {
      console.log('🔍 === NETWORK DEBUGGING START ===');
      console.log('🔍 API_BASE_URL:', API_BASE_URL);
      console.log('🔍 Window location:', window.location.href);
      console.log('🔍 User agent:', navigator.userAgent);
      
      // Test multiple endpoints to isolate the issue
      const testEndpoints = [
        '/health/',
        '/admin-auth/check-session/',
        '/admin/dashboard/metrics/'
      ];
      
      for (const endpoint of testEndpoints) {
        const fullUrl = `${API_BASE_URL}${endpoint}`;
        console.log(`🔍 Testing: ${fullUrl}`);
        
        try {
          const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            }
          });
          
          const contentType = response.headers.get('content-type') || 'unknown';
          const responseText = await response.text();
          
          console.log(`🔍 ${endpoint} - Status:`, response.status);
          console.log(`🔍 ${endpoint} - Content-Type:`, contentType);
          console.log(`🔍 ${endpoint} - Response preview:`, responseText.substring(0, 150));
          console.log(`🔍 ${endpoint} - Is HTML:`, responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html'));
          
          // Check if this looks like a Django error page
          if (responseText.includes('Django') && responseText.includes('<!DOCTYPE')) {
            console.log('🔍 ❌ Getting Django HTML error page instead of API response!');
          }
          
        } catch (error) {
          console.error(`🔍 ${endpoint} failed:`, error);
        }
      }
      
      console.log('🔍 === NETWORK DEBUGGING END ===');
      return true; // Always return true for now, just for debugging
    } catch (error) {
      console.error('🔍 Connection test failed:', error);
      return false;
    }
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    // Use correct base URL
    const correctBaseURL = 'http://127.0.0.1:8000/api';
    const url = `${correctBaseURL}${endpoint}`;
    console.log('🌐 API request - using URL:', url);
    
    // Debug logging
    console.log('🌐 API Request:', {
      url,
      method: options.method || 'GET',
      endpoint,
      timestamp: new Date().toISOString()
    });
    
    const defaultHeaders: Record<string, string> = {};

    // Only set Content-Type if not FormData (FormData sets its own boundary)
    if (!(options.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    // Add auth token if available
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('admin_token');
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
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid - redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            window.location.href = '/admin/login';
          }
        }
        
        // Get detailed error message from response
        let errorMessage = `API Error: ${response.status} ${response.statusText}`;
        try {
          // Clone response so we can read it multiple times if needed
          const responseClone = response.clone();
          const responseText = await responseClone.text();
          console.log('🔍 Error response text (first 200 chars):', responseText.substring(0, 200));
          
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
          console.log('Could not parse error response as JSON:', e);
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
      console.error('API Request failed:', {
        url,
        method: options.method || 'GET',
        error: error instanceof Error ? error.message : error,
        errorName: error instanceof Error ? error.name : typeof error,
        errorStack: error instanceof Error ? error.stack : undefined,
        endpoint
      });
      
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
    console.log('🌐 API: Updating course', {
      courseId,
      courseIdType: typeof courseId,
      courseIdLength: courseId ? courseId.length : 'null',
      endpoint: `/admin/courses/${courseId}/`
    });
    
    console.log('🌐 API: Course data being sent:', {
      courseData,
      courseDataKeys: Object.keys(courseData),
      courseDataTypes: Object.fromEntries(
        Object.entries(courseData).map(([key, value]) => [key, typeof value])
      )
    });
    
    // Validate courseId
    if (!courseId || courseId === 'undefined' || courseId === 'null') {
      throw new Error(`Invalid course ID: ${courseId}`);
    }
    
    const result = await this.request(`/admin/courses/${courseId}/`, {
      method: 'PUT',
      body: JSON.stringify(courseData),
    });
    console.log('🌐 API: Update course response:', result);
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
}

export const adminAPI = new AdminAPIClient();