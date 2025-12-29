// API endpoints for pricing and coupons
export const pricingAPI = {
  // Pricing Plans
  async getPricingPlans(params: {
    active_only?: boolean;
    plan_category?: string;
    billing_cycle?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/api/pricing/plans/${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  async createPricingPlan(planData: {
    name: string;
    description: string;
    price: number;
    currency: string;
    plan_category: 'signals' | 'mentorship' | 'vip';
    billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
    telegram_groups: string[];
    is_active?: boolean;
    is_promotion?: boolean;
    promotion_text?: string;
  }) {
    const response = await fetch('/api/pricing/plans/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify(planData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  async updatePricingPlan(planId: string, updates: Partial<{
    name: string;
    description: string;
    price: number;
    currency: string;
    plan_category: 'signals' | 'mentorship' | 'vip';
    billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
    telegram_groups: string[];
    is_active: boolean;
    is_promotion: boolean;
    promotion_text: string;
  }>) {
    const response = await fetch(`/api/pricing/plans/${planId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  async deletePricingPlan(planId: string) {
    const response = await fetch(`/api/pricing/plans/${planId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return true;
  },

  // Coupon Codes
  async getCouponCodes(params: {
    active_only?: boolean;
    search?: string;
    valid_only?: boolean;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/api/pricing/coupons/${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  async createCouponCode(couponData: {
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
  }) {
    const response = await fetch('/api/pricing/coupons/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
      },
      body: JSON.stringify(couponData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  async validateCoupon(code: string, planId: string, amount: number) {
    const response = await fetch('/api/pricing/coupons/validate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ code, plan_id: planId, amount })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  // Public pricing (no auth required)
  async getPublicPricing(params: {
    active_only?: boolean;
    plan_category?: string;
  } = { active_only: true }) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, String(value));
      }
    });

    const endpoint = `/api/pricing/public/${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
};

// Hooks for pricing data
export const usePricingPlans = (params?: {
  active_only?: boolean;
  plan_category?: string;
  billing_cycle?: string;
}) => {
  // Implementation using your existing useAPI pattern
  // This would use your existing useAPI hook with the pricingAPI.getPricingPlans
  return {
    data: null,
    loading: true,
    error: null,
    refetch: () => {}
  };
};

export const usePublicPricing = (params?: {
  active_only?: boolean;
  plan_category?: string;
}) => {
  // Implementation for public pricing (no auth)
  return {
    data: null,
    loading: true,
    error: null,
    refetch: () => {}
  };
};

export const useCouponCodes = (params?: {
  active_only?: boolean;
  search?: string;
  valid_only?: boolean;
}) => {
  return {
    data: null,
    loading: true,
    error: null,
    refetch: () => {}
  };
};