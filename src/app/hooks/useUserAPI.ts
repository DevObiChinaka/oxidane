/**
 * Custom Hooks for User API
 * Provides reusable hooks for data fetching with loading and error states
 */

import { useState, useEffect, useCallback } from 'react';
import { userAPI } from '../utils/userAPI';

// ==================== Generic API Hook ====================

interface UseAPIResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useAPI<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): UseAPIResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ==================== Dashboard Hooks ====================

/**
 * Fetch user dashboard data
 */
export function useDashboard() {
  return useAPI(() => userAPI.getDashboard());
}

/**
 * Fetch user activity feed
 */
export function useUserActivity(limit: number = 10) {
  return useAPI(() => userAPI.getActivity(limit), [limit]);
}

// ==================== Profile Hooks ====================

/**
 * Fetch user profile
 */
export function useUserProfile() {
  return useAPI(() => userAPI.getProfile());
}

/**
 * Hook for profile updates
 */
export function useProfileUpdate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateProfile = async (data: {
    first_name?: string;
    last_name?: string;
    phone?: string;
    bio?: string;
    location?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const result = await userAPI.updateProfile(data);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Update failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { updateProfile, loading, error };
}

/**
 * Hook for avatar upload
 */
export function useAvatarUpload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const uploadAvatar = async (file: File) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 100);

      const result = await userAPI.uploadAvatar(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      setLoading(false);
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  const deleteAvatar = async () => {
    setLoading(true);
    setError(null);

    try {
      await userAPI.deleteAvatar();
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Delete failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { uploadAvatar, deleteAvatar, loading, error, progress };
}

// ==================== Subscription Hooks ====================

/**
 * Fetch user subscriptions
 */
export function useUserSubscriptions() {
  return useAPI(() => userAPI.getSubscriptions());
}

/**
 * Fetch subscription details
 */
export function useSubscriptionDetail(subscriptionId: string | null) {
  return useAPI(
    () => {
      if (!subscriptionId) throw new Error('No subscription ID');
      return userAPI.getSubscriptionDetail(subscriptionId);
    },
    [subscriptionId]
  );
}

// ==================== Course Hooks ====================

/**
 * Fetch user's enrolled courses
 */
export function useEnrolledCourses() {
  return useAPI(() => userAPI.getEnrolledCourses());
}

/**
 * Fetch course details
 */
export function useCourseDetail(courseId: string | null) {
  return useAPI(
    () => {
      if (!courseId) throw new Error('No course ID');
      return userAPI.getCourseDetail(courseId);
    },
    [courseId]
  );
}

/**
 * Fetch course progress
 */
export function useCourseProgress(courseId: string | null) {
  return useAPI(
    () => {
      if (!courseId) throw new Error('No course ID');
      return userAPI.getCourseProgress(courseId);
    },
    [courseId]
  );
}

/**
 * Hook for course enrollment
 */
export function useCourseEnrollment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const enrollCourse = async (courseId: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await userAPI.enrollCourse(courseId);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Enrollment failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { enrollCourse, loading, error };
}

/**
 * Hook for marking lessons complete
 */
export function useLessonCompletion() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const markComplete = async (lessonId: string, watchTime?: number) => {
    setLoading(true);
    setError(null);

    try {
      const result = await userAPI.markLessonComplete(lessonId, watchTime);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to mark complete';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { markComplete, loading, error };
}

// ==================== Settings Hooks ====================

/**
 * Hook for password change
 */
export function usePasswordChange() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const changePassword = async (currentPassword: string, newPassword: string) => {
    setLoading(true);
    setError(null);

    try {
      await userAPI.changePassword(currentPassword, newPassword);
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password change failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { changePassword, loading, error };
}

/**
 * Fetch user preferences
 */
export function useUserPreferences() {
  return useAPI(() => userAPI.getPreferences());
}

/**
 * Hook for updating preferences
 */
export function usePreferencesUpdate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updatePreferences = async (preferences: {
    email_notifications?: boolean;
    course_updates?: boolean;
    subscription_reminders?: boolean;
    payment_confirmations?: boolean;
    marketing_emails?: boolean;
    telegram_notifications?: boolean;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const result = await userAPI.updatePreferences(preferences);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Update failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { updatePreferences, loading, error };
}

// ==================== Public API Hooks ====================

/**
 * Fetch public course catalog
 */
export function usePublicCourses(params?: {
  search?: string;
  category?: string;
  difficulty?: string;
  page?: number;
}) {
  return useAPI(
    () => userAPI.getPublicCourses(params),
    [params?.search, params?.category, params?.difficulty, params?.page]
  );
}

/**
 * Fetch public pricing plans
 */
export function usePublicPricing() {
  return useAPI(() => userAPI.getPublicPricing());
}

/**
 * Hook for coupon validation
 */
export function useCouponValidation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateCoupon = async (code: string, planId: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await userAPI.validateCoupon(code, planId);
      setLoading(false);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Validation failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  return { validateCoupon, loading, error };
}
