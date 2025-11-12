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
  video_file_url?: string; // Full URL to uploaded video
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

// ==================== Settings Types ====================

export type SettingCategory = 
  | 'platform' 
  | 'email' 
  | 'telegram' 
  | 'courses' 
  | 'security' 
  | 'notifications' 
  | 'system' 
  | 'payment' 
  | 'legal';

export type SettingDataType = 
  | 'string' 
  | 'integer' 
  | 'boolean' 
  | 'json' 
  | 'text' 
  | 'email' 
  | 'url' 
  | 'color';

export interface PlatformSetting {
  id: number;
  category: SettingCategory;
  category_display: string;
  key: string;
  label: string;
  value: any;
  data_type: SettingDataType;
  is_encrypted: boolean;
  is_sensitive: boolean;
  description: string;
  default_value?: any;
  validation_rules?: Record<string, any>;
  is_active: boolean;
  requires_restart: boolean;
  created_at: string;
  updated_at: string;
  last_modified_by?: number;
  last_modified_by_username?: string;
}

export interface SettingChangeLog {
  id: number;
  setting: number;
  setting_key: string;
  setting_category: string;
  old_value: any;
  new_value: any;
  change_reason: string;
  changed_by: number;
  changed_by_username: string;
  changed_at: string;
  ip_address: string;
  user_agent: string;
}

export type TelegramAccessLevel = 'all' | 'weekly' | 'monthly' | 'vip' | 'mentorship';

export interface TelegramGroup {
  id: number;
  name: string;
  chat_id: string;
  group_key: string;
  access_level: TelegramAccessLevel;
  access_level_display: string;
  description: string;
  is_active: boolean;
  auto_add_users: boolean;
  auto_remove_expired: boolean;
  welcome_message_enabled: boolean;
  welcome_message_template: string;
  is_public: boolean;
  invite_link: string;
  sort_order: number;
  member_count: number;
  last_sync_at?: string;
  created_at: string;
  updated_at: string;
}

export interface SettingsBackup {
  id: number;
  name: string;
  description: string;
  settings_data: Record<string, any>;
  telegram_groups_data?: any[];
  created_by: number;
  created_by_username: string;
  created_at: string;
  restored_at?: string;
  restored_by?: number;
  restored_by_username?: string;
}

export interface SettingsByCategoryResponse {
  success: boolean;
  categories: Array<{
    category: SettingCategory;
    category_label: string;
    settings: PlatformSetting[];
    count: number;
  }>;
}

export interface SettingsStatsResponse {
  success: boolean;
  stats: {
    total_settings: number;
    encrypted_settings: number;
    public_settings: number;
    settings_by_category: Array<{
      category: SettingCategory;
      count: number;
    }>;
    recent_changes_7days: number;
    active_telegram_groups: number;
    total_backups: number;
  };
}
