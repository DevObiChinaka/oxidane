// Admin dashboard type definitions

export interface EmailTemplate {
  id?: string;
  name: string;
  template_type: string;
  template_type_display?: string;
  status: 'active' | 'inactive' | 'draft';
  subject_template: string;
  html_content: string;
  text_content: string;
  description: string;
  is_default: boolean;
  sent_count?: number;
  last_used?: string | null;
  created_at?: string;
  updated_at?: string;
  available_variables?: Record<string, string>;
  from_email?: string;
  from_name?: string;
}

export interface EmailTemplateType {
  value: string;
  label: string;
  description: string;
}

export interface EmailAnalytics {
  total_templates: number;
  active_templates: number;
  total_sent: number;
  recent_sent: number;
  success_rate: number;
  failed_emails?: number;
  top_templates?: Array<{
    name: string;
    template_type: string;
    sent_count: number;
    last_used: string | null;
  }>;
}

export interface PreviewData {
  success: boolean;
  subject: string;
  html_content: string;
  variables_used: Record<string, string>;
  template_name: string;
}

export interface TestResult {
  success: boolean;
  message: string;
}

// Subscription related types
export interface Subscription {
  id: string;
  user: string;
  plan_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
}

// Analytics types
export interface AnalyticsData {
  total_users: number;
  active_subscriptions: number;
  total_revenue: number;
  monthly_growth: number;
}