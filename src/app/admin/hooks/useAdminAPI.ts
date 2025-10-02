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
      const course = await apiClient.createCourse(courseData);
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
//   }, []);

//   const login = async (username: string, password: string) => {
//     const result = await apiClient.login(username, password);
//     if (result.success) {
//       setIsAuthenticated(true);
//     }
//     return result;
//   };

//   const logout = async () => {
//     try {
//       await apiClient.logout();
//       setIsAuthenticated(false);
//     } catch (err) {
//       // Handle logout error if needed
//       console.error('Logout error:', err);
//     }
//   };

//   return {
//     isAuthenticated,
//     login,
//     logout,
//     loading
//   };
// }