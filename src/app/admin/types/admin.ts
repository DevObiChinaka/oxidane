export interface DashboardMetrics {
  users: {
    total: number;
    verified: number;
    active: number;
    admins: number;
    recent_signups: number;
  };
  courses: {
    total: number;
    published: number;
    draft: number;
  };
  content: {
    total_lessons: number;
    avg_lessons_per_course: number;
  };
  engagement: {
    total_enrollments: number;
    active_learners: number;
    completed_courses: number;
    avg_completion_rate: number;
    recent_completions: number;
  };
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  description: string;
  short_description?: string;
  course_type: 'free' | 'premium';
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  status: 'draft' | 'published' | 'archived';
  meta_title?: string;
  meta_description?: string;
  keywords?: string;
  thumbnail?: string;
  trailer_video_url?: string;
  estimated_duration: number;
  order: number;
  created_at: string;
  updated_at: string;
  published_at?: string;
  lesson_count?: number;
  total_duration?: number;
  enrollment_count?: number;
  completion_rate?: number;
}

export interface Lesson {
  id: string;
  course: string;
  title: string;
  slug: string;
  description: string;
  video_source: 'upload' | 'youtube' | 'vimeo';
  video_file?: string;
  video_url?: string;
  youtube_video_id?: string;
  duration: number;
  order: number;
  is_preview: boolean;
  lesson_notes?: string;
  downloadable_resources?: string;
  youtube_thumbnail?: string;
  created_at: string;
  updated_at: string;
}

export interface CourseProgress {
  id: string;
  user_email: string;
  course_title: string;
  course_type: string;
  completion_percentage: number;
  lessons_completed: number;
  total_time_spent: number;
  started_at: string;
  completed_at?: string;
  certificate_generated: boolean;
}

export interface LessonProgress {
  id: string;
  user_email: string;
  lesson_title: string;
  course_title: string;
  completed: boolean;
  completion_percentage: number;
  time_spent: number;
  last_watched_at: string;
  completed_at?: string;
}

export interface CourseAnalytics {
  course: {
    id: string;
    title: string;
    type: string;
  };
  stats: {
    total_enrollments: number;
    completed_enrollments: number;
    completion_rate: number;
    avg_progress: number;
  };
  lesson_analytics: Array<{
    lesson_id: string;
    title: string;
    order: number;
    completions: number;
    completion_rate: number;
  }>;
}

export interface PaginatedResponse<T> {
  results: T[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_courses: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface CourseListResponse {
  courses: Course[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_courses: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface CourseLessonsResponse {
  course: {
    id: string;
    title: string;
  };
  lessons: Lesson[];
}

// API Response types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Subscription types
export interface Subscription {
  id: string;
  user: {
    id: string;
    username: string;
    email: string;
    telegram_id?: string;
    is_verified: boolean;
  };
  plan_type: 'monthly' | 'yearly' | 'lifetime';
  payment_status: 'pending' | 'completed' | 'failed' | 'cancelled' | 'refunded';
  telegram_status: 'none' | 'pending' | 'verified' | 'expired';
  start_date: string;
  end_date?: string;
  amount: string;
  currency: string;
  payment_method: string;
  payment_reference?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface SubscriptionListResponse {
  results: Subscription[];
  count: number;
  next?: string;
  previous?: string;
}

export interface SubscriptionAnalytics {
  total_subscriptions: number;
  active_subscriptions: number;
  revenue_this_month: string;
  revenue_growth: number;
  top_plans: Array<{
    plan_type: string;
    count: number;
    revenue: string;
  }>;
  payment_status_distribution: Array<{
    status: string;
    count: number;
    percentage: number;
  }>;
  monthly_trends: Array<{
    month: string;
    subscriptions: number;
    revenue: string;
  }>;
}

// Error types
export interface APIError {
  message: string;
  status?: number;
  code?: string;
}