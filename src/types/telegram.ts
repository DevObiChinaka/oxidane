// Telegram Management Types
export interface TelegramQueueItem {
  id: string;
  user: {
    id: string;
    username: string;
    email: string;
    telegram_username?: string;
    telegram_id?: string;
  };
  subscription_id: string;
  action_type: 'add_to_group' | 'remove_from_group' | 'send_message';
  group_name: string;
  group_id: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying' | 'cancelled';
  attempts: number;
  max_attempts: number;
  error_message?: string;
  retry_after?: string;
  scheduled_for?: string;
  processing_started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  metadata?: {
    invite_link?: string;
    message_content?: string;
    bot_response?: string;
  };
}

export interface TelegramGroup {
  id: string;
  name: string;
  chat_id: string;
  invite_link: string;
  description?: string;
  member_count: number;
  max_members?: number;
  is_active: boolean;
  is_private: boolean;
  created_at: string;
  updated_at: string;
  permissions: {
    can_send_messages: boolean;
    can_add_users: boolean;
    can_remove_users: boolean;
    can_pin_messages: boolean;
    can_delete_messages: boolean;
    is_admin: boolean;
  };
  settings: {
    auto_add_enabled: boolean;
    welcome_message?: string;
    removal_message?: string;
    notification_enabled: boolean;
  };
  associated_plans?: string[]; // Plan types that give access to this group
}

export interface TelegramStats {
  pending_additions: number;
  pending_removals: number;
  failed_operations: number;
  successful_operations_today: number;
  successful_operations_week: number;
  successful_operations_month: number;
  queue_processing_rate: number;
  average_processing_time: number; // in seconds
  bot_status: 'connected' | 'disconnected' | 'error' | 'rate_limited';
  last_activity?: string;
  total_groups: number;
  active_groups: number;
  total_members: number;
}

export interface TelegramBotStatus {
  is_connected: boolean;
  username: string;
  first_name: string;
  can_join_groups: boolean;
  can_read_all_group_messages: boolean;
  supports_inline_queries: boolean;
  last_seen?: string;
  rate_limit_remaining?: number;
  rate_limit_reset_time?: string;
}

export interface TelegramQueueFilters {
  status?: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying' | 'cancelled' | 'all';
  action_type?: 'add_to_group' | 'remove_from_group' | 'send_message' | 'all';
  priority?: 'low' | 'normal' | 'high' | 'urgent' | 'all';
  group_name?: string;
  user_search?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}

export interface TelegramBulkAction {
  action: 'retry' | 'cancel' | 'priority_high' | 'priority_normal' | 'priority_low' | 'delete';
  item_ids: string[];
  reason?: string;
  metadata?: Record<string, any>;
}

export interface TelegramActionRequest {
  action: 'add_to_group' | 'remove_from_group' | 'send_message' | 'update_permissions' | 'get_member_count';
  group_id?: string;
  user_id?: string;
  message?: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  scheduled_for?: string;
  metadata?: Record<string, any>;
}

export interface TelegramActionResponse {
  success: boolean;
  message: string;
  queue_item_id?: string;
  telegram_response?: any;
  error?: {
    code: string;
    description: string;
    retry_after?: number;
  };
}

export interface TelegramGroupCreateRequest {
  name: string;
  chat_id: string;
  description?: string;
  is_active?: boolean;
  associated_plans?: string[];
  settings?: {
    auto_add_enabled?: boolean;
    welcome_message?: string;
    removal_message?: string;
    notification_enabled?: boolean;
  };
}

export interface TelegramGroupUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  associated_plans?: string[];
  settings?: {
    auto_add_enabled?: boolean;
    welcome_message?: string;
    removal_message?: string;
    notification_enabled?: boolean;
  };
}

export interface TelegramAnalytics {
  queue_metrics: {
    total_processed: number;
    success_rate: number;
    average_processing_time: number;
    peak_processing_time: string;
    failed_operations: {
      count: number;
      common_errors: Array<{
        error_type: string;
        count: number;
        percentage: number;
      }>;
    };
  };
  group_metrics: {
    total_groups: number;
    active_groups: number;
    total_members: number;
    member_growth: Array<{
      date: string;
      count: number;
    }>;
    group_activity: Array<{
      group_name: string;
      additions_today: number;
      removals_today: number;
      current_members: number;
    }>;
  };
  bot_metrics: {
    uptime_percentage: number;
    api_calls_today: number;
    rate_limit_hits: number;
    errors_count: number;
    response_times: {
      average: number;
      p95: number;
      p99: number;
    };
  };
  trends: {
    daily_operations: Array<{
      date: string;
      additions: number;
      removals: number;
      failures: number;
    }>;
    hourly_load: Array<{
      hour: number;
      operations: number;
    }>;
  };
}

// API Response Types
export interface TelegramQueueResponse {
  items: TelegramQueueItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  stats: TelegramStats;
}

export interface TelegramGroupsResponse {
  groups: TelegramGroup[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  bot_status: TelegramBotStatus;
}

export interface TelegramBulkActionResponse {
  success_count: number;
  error_count: number;
  errors: Array<{
    item_id: string;
    error: string;
  }>;
  updated_items: TelegramQueueItem[];
}

// Hook Return Types
export interface UseTelegramQueue {
  data: TelegramQueueResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  performBulkAction: (action: TelegramBulkAction) => Promise<TelegramBulkActionResponse>;
  retryItem: (itemId: string) => Promise<void>;
  cancelItem: (itemId: string) => Promise<void>;
}

export interface UseTelegramGroups {
  data: TelegramGroupsResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  createGroup: (group: TelegramGroupCreateRequest) => Promise<TelegramGroup>;
  updateGroup: (groupId: string, updates: TelegramGroupUpdateRequest) => Promise<TelegramGroup>;
  deleteGroup: (groupId: string) => Promise<void>;
  toggleGroupStatus: (groupId: string, isActive: boolean) => Promise<TelegramGroup>;
}

export interface UseTelegramAnalytics {
  data: TelegramAnalytics | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}