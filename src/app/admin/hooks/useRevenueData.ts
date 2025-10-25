import { useState, useEffect } from 'react';
import { AdminAPIClient } from '../utils/api';

interface DateRange {
  startDate: string;
  endDate: string;
}

interface ApiResponse {
  total_revenue: number;
  monthly_growth: number;
  active_subscriptions: number;
  average_revenue_per_user: number;
  monthly_recurring_revenue: number;
  coupon_discount_impact: number;
  new_student_revenue: number;
  retention_revenue: number;
  revenue_breakdown: {
    [key: string]: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

interface RevenueData {
  totalRevenue: number;
  monthlyGrowth: number;
  activeSubscriptions: number;
  averageRevenuePerUser: number;
  monthlyRecurringRevenue: number;
  couponDiscountImpact: number;
  newStudentRevenue: number;
  retentionRevenue: number;
  revenueBreakdown: {
    [key: string]: number;
  };
  period: DateRange;
}

export const useRevenueData = (dateRange: DateRange) => {
  const [data, setData] = useState<RevenueData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const apiClient = new AdminAPIClient();

  useEffect(() => {
    const fetchRevenueData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await apiClient.get<ApiResponse>(
          `/admin/revenue/analytics/?start_date=${dateRange.startDate}&end_date=${dateRange.endDate}`
        );

        // Transform API response to match our frontend data structure
        const transformedData: RevenueData = {
          totalRevenue: response.total_revenue,
          monthlyGrowth: response.monthly_growth,
          activeSubscriptions: response.active_subscriptions,
          averageRevenuePerUser: response.average_revenue_per_user,
          monthlyRecurringRevenue: response.monthly_recurring_revenue,
          couponDiscountImpact: response.coupon_discount_impact,
          newStudentRevenue: response.new_student_revenue,
          retentionRevenue: response.retention_revenue,
          revenueBreakdown: response.revenue_breakdown,
          period: {
            startDate: response.period.start_date,
            endDate: response.period.end_date
          }
        };

        setData(transformedData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch revenue data');
        console.error('Revenue data fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRevenueData();
  }, [dateRange.startDate, dateRange.endDate]);

  return { data, isLoading, error };
};