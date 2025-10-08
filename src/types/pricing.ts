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
  plan_category: 'signals' | 'mentorship' | 'vip';
  billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
  telegram_groups: string[];
  is_active: boolean;
  is_featured: boolean;
  features_list?: string[];
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
  applicable_plans: string[]; // Plan IDs or empty array for all plans
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
    vip: PricingPlan[];
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
    vip: number;
  };
}

// Update existing subscription types to include pricing plan
export interface EnhancedSubscription extends Subscription {
  pricing_plan: PricingPlan;
  coupon_used?: CouponCode;
  original_amount?: number; // Before coupon discount
}

// New plan type options based on dynamic data
export const DYNAMIC_PLAN_TYPE_OPTIONS = [
  { value: 'signals_weekly', label: 'Weekly Signals', duration: '7 days' },
  { value: 'signals_monthly', label: 'Monthly Signals', duration: '30 days' },
  { value: 'signals_yearly', label: 'Yearly Signals', duration: '365 days' },
  { value: 'mentorship_one_time', label: 'Basic Mentorship', duration: 'Lifetime' },
  { value: 'vip_weekly', label: 'Weekly VIP', duration: '7 days' },
  { value: 'vip_monthly', label: 'Monthly VIP', duration: '30 days' },
  { value: 'vip_yearly', label: 'Yearly VIP', duration: '365 days' },
] as const;