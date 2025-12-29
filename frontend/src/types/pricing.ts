// Enhanced types for dynamic pricing system
import { Subscription } from './subscription';

export interface PricingPlan {
  id: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  current_price?: number;
  currency: string;
  plan_category: 'signals' | 'mentorship';
  billing_cycle: 'one_time' | 'weekly' | 'monthly';
  
  // New fields for simplified structure
  duration_days: number | null; // null for lifetime (mentorship)
  gives_course_access: boolean;
  gives_signals_access: boolean;
  telegram_group_key: string; // 'mentorship', 'signals', or 'vip'
  
  is_active: boolean;
  is_featured: boolean;
  features_list?: string[];
  call_to_action?: string;
  sort_order?: number;
  
  // Analytics
  subscription_count?: number;
  revenue_total?: number;
  
  created_at: string;
  updated_at: string;
}

export interface CouponCode {
  id: string;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed_amount';
  discount_value: number;
  minimum_amount?: number;
  currency: string;
  max_uses?: number;
  used_count: number;
  plans: string[]; // Plan IDs or empty array for all plans
  valid_from: string;
  valid_until: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CouponValidation {
  valid: boolean;
  discount_amount: number;
  final_amount: number;
  message: string;
  coupon?: CouponCode;
  error?: string;
}

export interface PublicPricingResponse {
  plans: PricingPlan[];
  categories: {
    signals: PricingPlan[];
    mentorship: PricingPlan[];
  };
}

export interface PricingAnalytics {
  total_revenue: number;
  active_plans: number;
  total_plans: number;
  active_coupons: number;
  coupon_usage: number;
  plan_popularity: Array<{
    plan_id: string;
    plan_name: string;
    subscription_count: number;
    revenue: number;
  }>;
  revenue_by_category: {
    signals: number;
    mentorship: number;
  };
}

// Update existing subscription types to include pricing plan
export interface EnhancedSubscription extends Subscription {
  pricing_plan: PricingPlan;
  coupon_used?: CouponCode;
  original_amount?: number; // Before coupon discount
}

// Simplified plan type options (4 types total)
export const DYNAMIC_PLAN_TYPE_OPTIONS = [
  { 
    value: 'mentorship', 
    label: 'Mentorship Program', 
    duration: 'Lifetime',
    category: 'mentorship',
    billing: 'one_time',
    description: 'One-time payment for lifetime course access'
  },
  { 
    value: 'signals_weekly', 
    label: 'Weekly Signals', 
    duration: '7 days',
    category: 'signals',
    billing: 'weekly',
    description: 'Weekly trading signals subscription'
  },
  { 
    value: 'signals_monthly', 
    label: 'Monthly Signals', 
    duration: '30 days',
    category: 'signals',
    billing: 'monthly',
    description: 'Monthly trading signals subscription'
  },
  { 
    value: 'vip_monthly', 
    label: 'VIP Signals', 
    duration: '30 days',
    category: 'signals',
    billing: 'monthly',
    description: 'Premium VIP signals with trade bias and analysis'
  },
] as const;