import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/utils/apiClient';
import { 
  DashboardMetrics, 
  Course, 
  CourseListResponse, 
  Lesson, 
  CourseProgress, 
  LessonProgress, 
  CourseAnalytics, 
  APIError 
} from '../types/admin';
import { 
  Subscription, 
  SubscriptionAnalytics 
} from '../../../types/subscription';
import {
  PaymentTransaction,
  PaymentAnalytics,
  PaymentFilters
} from '../../../types/payment';

// Generic hook for API calls with loading and error states
export function useAPI<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Dashboard metrics hook
export function useDashboardMetrics() {
  return useAPI<DashboardMetrics>(() => apiClient.get<DashboardMetrics>('/admin/dashboard/metrics/'));
}

// Course management hooks
export function useCourses(page: number = 1, filters?: { search?: string; status?: string; type?: string }) {
  const { search, status, type } = filters || {};
  return useAPI<CourseListResponse>(
    () => {
      const params = new URLSearchParams({ page: page.toString() });
      if (search) params.append('search', search);
      if (status) params.append('status', status);
      if (type) params.append('type', type);
      return apiClient.get<CourseListResponse>(`/admin/courses/?${params.toString()}`);
    },
    [page, search, status, type]
  );
}

export function useCourse(courseId: string) {
  return useAPI<Course>(
    () => apiClient.get<Course>(`/admin/courses/${courseId}/`),
    [courseId]
  );
}

export function useCourseLessons(courseId: string) {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLessons = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ lessons: Lesson[] }>(`/admin/courses/${courseId}/lessons/`);
      setLessons(response.lessons);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch lessons');
      setLessons([]);
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    if (courseId) {
      fetchLessons();
    }
  }, [fetchLessons]);

  return { lessons, loading, error, refetch: fetchLessons };
}

// Course analytics hook
export function useCourseAnalytics(courseId: string) {
  return useAPI<CourseAnalytics>(
    () => apiClient.get<CourseAnalytics>(`/admin/courses/${courseId}/analytics/`),
    [courseId]
  );
}

// Course progress hooks - TODO: Add API endpoints for these
// export function useCourseProgress(page: number = 1, courseId?: string) {
//   return useAPI<{ results: CourseProgress[]; pagination: any }>(
//     () => apiClient.get(`/admin/courses/progress/?page=${page}${courseId ? `&course_id=${courseId}` : ''}`),
//     [page, courseId]
//   );
// }

// export function useLessonProgress(page: number = 1, lessonId?: string) {
//   return useAPI<{ results: LessonProgress[]; pagination: any }>(
//     () => apiClient.get(`/admin/lessons/progress/?page=${page}${lessonId ? `&lesson_id=${lessonId}` : ''}`),
//     [page, lessonId]
//   );
// }

// Mutation hooks for create/update/delete operations
export function useCourseActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createCourse = async (courseData: Partial<Course>) => {
    try {
      setLoading(true);
      setError(null);
      const course = await apiClient.post<Course>('/admin/courses/', courseData);
      return course;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create course';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateCourse = async (courseId: string, courseData: Partial<Course>) => {
    try {
      setLoading(true);
      setError(null);
      const course = await apiClient.put<Course>(`/admin/courses/${courseId}/`, courseData);
      return course;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update course';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteCourse = async (courseId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.delete(`/admin/courses/${courseId}/`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete course';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    createCourse,
    updateCourse,
    deleteCourse,
    loading,
    error
  };
}

export function useLessonActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createLesson = async (courseId: string, lessonData: Partial<Lesson>) => {
    try {
      setLoading(true);
      setError(null);
      const lesson = await apiClient.post<Lesson>(`/admin/courses/${courseId}/lessons/`, lessonData);
      return lesson;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateLesson = async (courseId: string, lessonId: string, lessonData: Partial<Lesson>) => {
    try {
      setLoading(true);
      setError(null);
      const lesson = await apiClient.put<Lesson>(`/admin/lessons/${lessonId}/`, lessonData);
      return lesson;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteLesson = async (courseId: string, lessonId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.delete(`/admin/lessons/${lessonId}/`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    createLesson,
    updateLesson,
    deleteLesson,
    loading,
    error
  };
}

// Search hook - using the getCourses method with search parameter
export function useSearch() {
  const [results, setResults] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchCourses = async (query: string, type?: string, status?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({ search: query });
      if (type) params.append('type', type);
      if (status) params.append('status', status);
      const searchResults = await apiClient.get<CourseListResponse>(`/admin/courses/?${params.toString()}`);
      setResults(searchResults.courses || []);
      return searchResults.courses || [];
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed';
      setError(errorMessage);
      setResults([]);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    results,
    searchCourses,
    loading,
    error
  };
}

// Authentication hook - TODO: Add authentication endpoints
// export function useAuth() {
//   const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     const checkAuth = async () => {
//       try {
//         const status = await apiClient.get('/auth/check');
//         setIsAuthenticated(status);
//       } catch (err) {
//         setIsAuthenticated(false);
//       } finally {
//         setLoading(false);
//       }
//     };

//     checkAuth();
// User management hooks
export function useUsers(params?: {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  subscription?: string;
  date_from?: string;
  date_to?: string;
}) {
  return useAPI(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
      if (params?.search) queryParams.append('search', params.search);
      if (params?.status) queryParams.append('status', params.status);
      if (params?.subscription) queryParams.append('subscription', params.subscription);
      if (params?.date_from) queryParams.append('date_from', params.date_from);
      if (params?.date_to) queryParams.append('date_to', params.date_to);
      return apiClient.get(`/admin/users/?${queryParams.toString()}`);
    },
    [params?.page, params?.per_page, params?.search, params?.status, params?.subscription, params?.date_from, params?.date_to]
  );
}

export function useUsersAnalytics() {
  return useAPI(() => apiClient.get('/admin/users-analytics/'));
}

export function useUserActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAction = useCallback(async (userId: string, action: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post(`/admin/users/${userId}/action/`, { action });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Action failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { performAction, loading, error };
}

export function useBulkUserActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performBulkAction = useCallback(async (userIds: string[], action: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post('/admin/users/bulk-action/', { user_ids: userIds, action });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bulk action failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { performBulkAction, loading, error };
}

export function useDeleteUser() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteUser = useCallback(async (userId: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.delete(`/admin/users/${userId}/delete/`);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Delete failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { deleteUser, loading, error };
}

export function useUserAuditLog(userId: string | null) {
  return useAPI(
    () => userId ? apiClient.get(`/admin/users/${userId}/audit-log/`) : Promise.resolve(null),
    [userId]
  );
}

// Pricing Management Hooks
export function usePricingPlans(params?: {
  plan_category?: string;
  billing_cycle?: string;
  active_only?: boolean;
}) {
  return useAPI(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.plan_category) queryParams.append('plan_category', params.plan_category);
      if (params?.billing_cycle) queryParams.append('billing_cycle', params.billing_cycle);
      if (params?.active_only) queryParams.append('is_active', 'true');
      return apiClient.get(`/admin/plans/?${queryParams.toString()}`);
    },
    [params?.plan_category, params?.billing_cycle, params?.active_only]
  );
}

export function usePricingPlanCategories() {
  return useAPI(() => apiClient.get('/admin/pricing/plans/categories/'));
}

export function usePricingPlanActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createPlan = async (planData: {
    plan_type: string;
    name: string;
    description: string;
    price: number;
    currency: string;
    plan_category: 'signals' | 'mentorship' | 'vip';
    billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
    telegram_groups: string[];
    features_list?: string[];
    is_active?: boolean;
    is_featured?: boolean;
  }) => {
    try {
      setLoading(true);
      setError(null);
      const plan = await apiClient.post('/admin/pricing/plans/', planData);
      return plan;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create pricing plan';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updatePlan = async (planId: string, updates: any) => {
    try {
      setLoading(true);
      setError(null);
      const plan = await apiClient.put(`/admin/pricing/plans/${planId}/`, updates);
      return plan;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update pricing plan';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deletePlan = async (planId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.delete(`/admin/pricing/plans/${planId}/`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete pricing plan';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (planId: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post(`/admin/pricing/plans/${planId}/toggle_active/`, {});
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle plan status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const toggleFeatured = async (planId: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post(`/admin/pricing/plans/${planId}/toggle_featured/`, {});
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle featured status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    createPlan,
    updatePlan,
    deletePlan,
    toggleActive,
    toggleFeatured,
    loading,
    error
  };
}

// Coupon Management Hooks
export function useCouponCodes(params?: {
  active_only?: boolean;
  valid_only?: boolean;
  search?: string;
}) {
  return useAPI(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.active_only) queryParams.append('active_only', params.active_only.toString());
      if (params?.valid_only) queryParams.append('valid_only', params.valid_only.toString());
      if (params?.search) queryParams.append('search', params.search);
      return apiClient.get(`/admin/pricing/coupons/?${queryParams.toString()}`);
    },
    [params?.active_only, params?.valid_only, params?.search]
  );
}

export function useCouponActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createCoupon = async (couponData: {
    code: string;
    description: string;
    discount_type: 'percentage' | 'fixed_amount';
    discount_value: number;
    minimum_amount?: number;
    currency: string;
    max_uses?: number;
    plans: string[];
    valid_from: string;
    valid_until: string;
    is_active?: boolean;
  }) => {
    try {
      setLoading(true);
      setError(null);
      const coupon = await apiClient.post('/admin/pricing/coupons/', couponData);
      return coupon;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create coupon';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateCoupon = async (couponId: string, updates: any) => {
    try {
      setLoading(true);
      setError(null);
      const coupon = await apiClient.put(`/admin/pricing/coupons/${couponId}/`, updates);
      return coupon;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update coupon';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteCoupon = async (couponId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.delete(`/admin/pricing/coupons/${couponId}/`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete coupon';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (couponId: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post(`/admin/pricing/coupons/${couponId}/toggle_active/`, {});
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle coupon status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const validateCoupon = async (code: string, planId: string, amount: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post('/admin/pricing/coupons/validate/', { code, plan_id: planId, amount });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to validate coupon';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    createCoupon,
    updateCoupon,
    deleteCoupon,
    toggleActive,
    validateCoupon,
    loading,
    error
  };
}

// Public Pricing Hook (for frontend use, no auth required)
export function usePublicPricing(params?: {
  active_only?: boolean;
  plan_category?: string;
}) {
  return useAPI(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.active_only !== undefined) queryParams.append('active_only', params.active_only.toString());
      if (params?.plan_category) queryParams.append('plan_category', params.plan_category);
      return apiClient.get(`/public/pricing/?${queryParams.toString()}`);
    },
    [params?.active_only, params?.plan_category]
  );
}

// Subscription management hooks
export function useSubscriptions(params?: {
  page?: number;
  limit?: number;
  payment_status?: string;
  plan_type?: string;
  telegram_status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  user_email?: string;
}) {
  return useAPI<{results: Subscription[], count: number, next?: string, previous?: string}>(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.payment_status) queryParams.append('payment_status', params.payment_status);
      if (params?.plan_type) queryParams.append('plan_type', params.plan_type);
      if (params?.telegram_status) queryParams.append('telegram_status', params.telegram_status);
      if (params?.search) queryParams.append('search', params.search);
      if (params?.date_from) queryParams.append('date_from', params.date_from);
      if (params?.date_to) queryParams.append('date_to', params.date_to);
      if (params?.user_email) queryParams.append('user_email', params.user_email);
      return apiClient.get(`/admin/subscriptions/?${queryParams.toString()}`);
    },
    [params?.page, params?.limit, params?.payment_status, params?.plan_type, params?.telegram_status, params?.search, params?.date_from, params?.date_to, params?.user_email]
  );
}

export function useSubscriptionAnalytics(params?: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  days_back?: number;
}) {
  return useAPI<SubscriptionAnalytics>(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.period) queryParams.append('period', params.period);
      if (params?.days_back) queryParams.append('days_back', params.days_back.toString());
      return apiClient.get(`/admin/analytics/?${queryParams.toString()}`);
    },
    [params?.period, params?.days_back]
  );
}

export function useSubscriptionActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateSubscription = useCallback(async (subscriptionId: string, updates: any, reason?: string) => {
    try {
      setLoading(true);
      setError(null);
      const body = { ...updates };
      if (reason) body.reason = reason;
      const result = await apiClient.put(`/admin/subscriptions/${subscriptionId}/`, body);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Update failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyPayment = useCallback(async (subscriptionId: string, data?: any) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.post(`/admin/subscriptions/${subscriptionId}/verify-payment/`, data || {});
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Verification failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { updateSubscription, verifyPayment, loading, error };
}

export function useUserDetail(userId: string | null) {
  const [userDetailData, setUserDetailData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUserDetail = useCallback(async () => {
    if (!userId) {
      setUserDetailData(null);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const response: any = await apiClient.get(`/admin/users/${userId}/`);

      // Extract user data from the nested response structure
      const userData = {
        ...response.user,
        subscription_history: response.subscription_history || [],
        oauth_providers: response.oauth_providers || [],
        metrics: response.metrics || {}
      };

      setUserDetailData(userData);
    } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch user details');
      setUserDetailData(null);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUserDetail();
  }, [fetchUserDetail]);

  return { 
    data: userDetailData, 
    loading, 
    error,
    refetch: fetchUserDetail 
  };
}

// Payment Management Hooks
export function usePayments(params: {
  page?: number;
  limit?: number;
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
  sort_by?: string;
  sort_order?: string;
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPayments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build query string
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value.toString());
        }
      });

      const response = await fetch(`/api/admin/payments?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payments');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch payments');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]);

  useEffect(() => {
    fetchPayments();
  }, [fetchPayments]);

  return { data, loading, error, refetch: fetchPayments };
}

export function usePaymentAnalytics(params: {
  period?: string;
  days_back?: number;
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });

      const response = await fetch(`/api/admin/payment-analytics?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payment analytics');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { data, loading, error, refetch: fetchAnalytics };
}

export function usePaymentActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const verifyPayment = useCallback(async (paymentId: string, verificationData: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/admin/payments/${paymentId}/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(verificationData),
      });

      if (!response.ok) {
        throw new Error('Failed to verify payment');
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to verify payment';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const processRefund = useCallback(async (paymentId: string, refundData: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/admin/payments/${paymentId}/refund`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(refundData),
      });

      if (!response.ok) {
        throw new Error('Failed to process refund');
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process refund';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePaymentStatus = useCallback(async (paymentId: string, statusData: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/admin/payments/${paymentId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(statusData),
      });

      if (!response.ok) {
        throw new Error('Failed to update payment status');
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update status';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { 
    verifyPayment, 
    processRefund, 
    updatePaymentStatus,
    loading, 
    error 
  };
}

// Telegram Management Hooks
export function useTelegramQueue(filters?: {
  status?: string;
  action_type?: string;
  priority?: string;
  group_name?: string;
  user_search?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performBulkAction = useCallback(async (action: string, itemIds: string[]) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        success_count: itemIds.length,
        error_count: 0,
        errors: []
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bulk action failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const retryItem = useCallback(async (itemId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 500));
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Retry failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelItem = useCallback(async (itemId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 500));
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Cancel failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    performBulkAction,
    retryItem,
    cancelItem,
    loading,
    error
  };
}

export function useTelegramGroups() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createGroup = useCallback(async (groupData: any) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        id: Date.now().toString(),
        ...groupData,
        member_count: 0,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        permissions: {
          can_send_messages: true,
          can_add_users: true,
          can_remove_users: true,
          can_pin_messages: false,
          can_delete_messages: false,
          is_admin: true
        }
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create group';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateGroup = useCallback(async (groupId: string, updates: any) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        id: groupId,
        ...updates,
        updated_at: new Date().toISOString()
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update group';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteGroup = useCallback(async (groupId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 1000));
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete group';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleGroupStatus = useCallback(async (groupId: string, isActive: boolean) => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock implementation - replace with actual API call

      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        id: groupId,
        is_active: isActive,
        updated_at: new Date().toISOString()
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle group status';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    createGroup,
    updateGroup,
    deleteGroup,
    toggleGroupStatus,
    loading,
    error
  };
}

export function useTelegramAnalytics(params?: {
  period?: 'daily' | 'weekly' | 'monthly';
  days_back?: number;
}) {
  return useAPI(
    () => {
      // Mock implementation - replace with actual API call
      return Promise.resolve({
        queue_metrics: {
          total_processed: 1247,
          success_rate: 95.2,
          average_processing_time: 3.4,
          peak_processing_time: '14:30',
          failed_operations: {
            count: 58,
            common_errors: [
              { error_type: 'User not found', count: 23, percentage: 39.7 },
              { error_type: 'Group full', count: 18, percentage: 31.0 },
              { error_type: 'Rate limited', count: 17, percentage: 29.3 }
            ]
          }
        },
        group_metrics: {
          total_groups: 3,
          active_groups: 2,
          total_members: 4680,
          member_growth: [],
          group_activity: []
        },
        bot_metrics: {
          uptime_percentage: 99.2,
          api_calls_today: 423,
          rate_limit_hits: 12,
          errors_count: 8,
          response_times: {
            average: 1.2,
            p95: 2.8,
            p99: 4.1
          }
        },
        trends: {
          daily_operations: [],
          hourly_load: []
        }
      });
    },
    [params?.period, params?.days_back]
  );
}

// Revenue Analytics Hook
export function useRevenueData(params?: {
  start_date?: string;
  end_date?: string;
  period?: 'daily' | 'weekly' | 'monthly';
}) {
  return useAPI(
    () => {
      const queryParams = new URLSearchParams();
      if (params?.start_date) queryParams.append('start_date', params.start_date);
      if (params?.end_date) queryParams.append('end_date', params.end_date);
      if (params?.period) queryParams.append('period', params.period);
      return apiClient.get(`/admin/revenue-analytics/?${queryParams.toString()}`);
    },
    [params?.start_date, params?.end_date, params?.period]
  );
}

export function useRevenueActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportRevenuePDF = async (params: {
    start_date: string;
    end_date: string;
    format: 'pdf' | 'excel';
  }) => {
    try {
      setLoading(true);
      setError(null);
      
      // Use downloadFile method or direct fetch for blob response
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        start_date: params.start_date,
        end_date: params.end_date,
        format: params.format
      });
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/revenue/export/?${queryParams.toString()}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      return await response.blob();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const exportRevenueExcel = async (params: {
    start_date: string;
    end_date: string;
    format: 'pdf' | 'excel';
  }) => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      const queryParams = new URLSearchParams({
        start_date: params.start_date,
        end_date: params.end_date,
        format: params.format
      });
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/admin/revenue/export/?${queryParams.toString()}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      return await response.blob();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    exportRevenuePDF,
    exportRevenueExcel,
    loading,
    error
  };
}

// Mentorship Hooks
export function useMentorshipSubscriptions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscriptions = async (params?: {
    search?: string;
    status?: string;
    plan?: string;
    telegram_status?: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const queryParams = new URLSearchParams();
      if (params?.search) queryParams.append('search', params.search);
      if (params?.status) queryParams.append('status', params.status);
      if (params?.plan) queryParams.append('plan', params.plan);
      if (params?.telegram_status) queryParams.append('telegram_status', params.telegram_status);

      const response = await apiClient.get(
        `/admin/mentorship/subscriptions/?${queryParams.toString()}`
      );
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch subscriptions');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const extendSubscription = async (subscriptionId: string, data: {
    extend_days: number;
    reason: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.post(
        `/admin/mentorship/extend/${subscriptionId}/`,
        data
      );
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extend subscription');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    fetchSubscriptions,
    extendSubscription,
    loading,
    error
  };
}

export function useMentorshipSessions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async (params?: {
    search?: string;
    status?: string;
    type?: string;
    date_from?: string;
    date_to?: string;
  }) => {
    try {
      setLoading(true);
      setError(null);

      const queryParams = new URLSearchParams();
      if (params?.search) queryParams.append('search', params.search);
      if (params?.status) queryParams.append('status', params.status);
      if (params?.type) queryParams.append('type', params.type);
      if (params?.date_from) queryParams.append('date_from', params.date_from);
      if (params?.date_to) queryParams.append('date_to', params.date_to);

      const response = await apiClient.get(
        `/admin/mentorship/sessions/?${queryParams.toString()}`
      );
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const manageSession = async (action: string, sessionId: string, data?: any) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.post('/admin/mentorship/sessions/', {
        action,
        session_id: sessionId,
        ...data
      });
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to manage session');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    fetchSessions,
    manageSession,
    loading,
    error
  };
}

export function useMentorshipAnalytics() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.get('/admin/mentorship/analytics/');
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    fetchAnalytics,
    loading,
    error
  };
}
