import { useState, useEffect, useCallback } from 'react';
import { AdminAPIClient } from '../utils/api';
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

const apiClient = new AdminAPIClient();

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
  return useAPI<DashboardMetrics>(() => apiClient.getDashboardMetrics());
}

// Course management hooks
export function useCourses(page: number = 1, filters?: { search?: string; status?: string; type?: string }) {
  const { search, status, type } = filters || {};
  return useAPI<CourseListResponse>(
    () => apiClient.getCourses({ page, search, status, type }),
    [page, search, status, type]
  );
}

export function useCourse(courseId: string) {
  return useAPI<Course>(
    () => apiClient.getCourseDetail(courseId),
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
      const response = await apiClient.getCourseLessons(courseId);
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
    () => apiClient.getCourseAnalytics(courseId),
    [courseId]
  );
}

// Course progress hooks - TODO: Add API endpoints for these
// export function useCourseProgress(page: number = 1, courseId?: string) {
//   return useAPI<{ results: CourseProgress[]; pagination: any }>(
//     () => apiClient.getCourseProgress(page, courseId),
//     [page, courseId]
//   );
// }

// export function useLessonProgress(page: number = 1, lessonId?: string) {
//   return useAPI<{ results: LessonProgress[]; pagination: any }>(
//     () => apiClient.getLessonProgress(page, lessonId),
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
      console.log('🔍 useCourseActions: Creating course with data:', courseData);
      console.log('🔍 useCourseActions: Data keys:', Object.keys(courseData));
      console.log('🔍 useCourseActions: Required fields check:');
      console.log('  - title:', courseData.title);
      console.log('  - description:', courseData.description);
      console.log('  - short_description:', courseData.short_description);
      console.log('  - slug:', courseData.slug);
      
      const course = await apiClient.createCourse(courseData);
      console.log('✅ useCourseActions: Course created successfully:', course);
      return course;
    } catch (err) {
      console.error('❌ useCourseActions: Course creation failed:', err);
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
      console.log('🔄 useCourseActions: Starting course update...', { courseId, courseData });
      const course = await apiClient.updateCourse(courseId, courseData);
      console.log('✅ useCourseActions: Course update successful', course);
      return course;
    } catch (err) {
      console.error('❌ useCourseActions: Course update failed:', err);
      console.error('❌ Error details:', {
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: err instanceof Error ? err.stack : undefined,
        courseId,
        courseData
      });
      const errorMessage = err instanceof Error ? err.message : 'Failed to update course';
      setError(errorMessage);
      throw err; // Re-throw the original error instead of creating a new one
    } finally {
      setLoading(false);
    }
  };

  const deleteCourse = async (courseId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.deleteCourse(courseId);
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
      const lesson = await apiClient.createLesson(courseId, lessonData);
      return lesson;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateLesson = async (lessonId: string, lessonData: Partial<Lesson>) => {
    try {
      setLoading(true);
      setError(null);
      const lesson = await apiClient.updateLesson(lessonId, lessonData);
      return lesson;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteLesson = async (lessonId: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.deleteLesson(lessonId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete lesson';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    createLesson, // Note: requires courseId as first parameter
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
      const searchResults = await apiClient.getCourses({ search: query, type, status });
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
//         const status = await apiClient.checkAuthStatus();
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
    () => apiClient.getUsers(params || {}),
    [params?.page, params?.per_page, params?.search, params?.status, params?.subscription, params?.date_from, params?.date_to]
  );
}

export function useUsersAnalytics() {
  return useAPI(() => apiClient.getUsersAnalytics());
}

export function useUserActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAction = useCallback(async (userId: string, action: string) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.userAction(userId, action);
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
}) {
  return useAPI<{results: Subscription[], count: number, next?: string, previous?: string}>(
    () => apiClient.getSubscriptions(params || {}),
    [params?.page, params?.limit, params?.payment_status, params?.plan_type, params?.telegram_status, params?.search, params?.date_from, params?.date_to]
  );
}

export function useSubscriptionAnalytics(params?: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  days_back?: number;
}) {
  return useAPI<SubscriptionAnalytics>(
    () => apiClient.getSubscriptionAnalytics(params || {}),
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
      const result = await apiClient.updateSubscription(subscriptionId, updates, reason);
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
      const result = await apiClient.verifyPayment(subscriptionId, data);
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
      const response = await apiClient.getUserDetail(userId);
      console.log('🔍 useUserDetail - Full response:', response);
      console.log('🔍 useUserDetail - User data:', response.user);
      
      // Extract user data from the nested response structure
      const userData = {
        ...response.user,
        subscription_history: response.subscription_history || [],
        oauth_providers: response.oauth_providers || [],
        metrics: response.metrics || {}
      };
      
      console.log('🔍 useUserDetail - Processed user data:', userData);
      setUserDetailData(userData);
    } catch (err) {
      console.error('❌ useUserDetail - Error:', err);
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