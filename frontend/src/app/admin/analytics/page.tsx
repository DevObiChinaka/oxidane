'use client';

import { useState, useEffect } from 'react';
import { adminAPI } from '../utils/api';
import { GrowthChart, DonutChart, BarChart } from '../components/charts';

// Type definitions for analytics data
interface CourseMetrics {
  total_courses: number;
  published_courses: number;
  draft_courses: number;
  archived_courses: number;
  free_courses: number;
  premium_courses: number;
  difficulty_distribution: Array<{ difficulty_level: string; count: number }>;
  publish_rate: number;
}

interface ContentMetrics {
  total_lessons: number;
  total_duration_minutes: number;
  total_duration_hours: number;
  avg_lessons_per_course: number;
  preview_lessons: number;
  preview_percentage: number;
}

interface UserMetrics {
  total_users: number;
  verified_users: number;
  active_users: number;
  recent_registrations_30d: number;
  recent_registrations_7d: number;
  verification_rate: number;
}

interface SubscriptionStats {
  total_count: number;
  active_count: number;
  total_revenue_usd: number;
  recent_revenue_30d: number;
}

interface EmailStats {
  total_templates: number;
  active_templates: number;
  total_sent: number;
  recent_sent: number;
}

interface RevenueMonthlyData {
  month: string;
  month_name: string;
  revenue: number;
  count: number;
  year: number;
  month_number: number;
  growth_rate?: number;
}

interface PopularCourse {
  id: string;
  title: string;
  slug: string;
  course_type: string;
  difficulty_level: string;
  lesson_count: number;
  total_duration: number;
  created_at: string;
  published_at: string | null;
}

interface GrowthMetrics {
  monthly_courses: Array<{ 
    month: string; 
    month_name: string;
    courses: number; 
    year: number;
    month_number: number;
    growth_rate: number;
    growth_direction: 'up' | 'down' | 'neutral';
  }>;
  monthly_users: Array<{ 
    month: string; 
    month_name: string;
    users: number; 
    year: number;
    month_number: number;
    growth_rate: number;
    growth_direction: 'up' | 'down' | 'neutral';
  }>;
  course_trend_summary: {
    trend: 'up' | 'down' | 'neutral';
    percentage: number;
  };
  user_trend_summary: {
    trend: 'up' | 'down' | 'neutral';
    percentage: number;
  };
  total_months: number;
}

interface AnalyticsData {
  course_metrics: CourseMetrics;
  content_metrics: ContentMetrics;
  user_metrics: UserMetrics;
  popular_courses: PopularCourse[];
  growth_metrics: GrowthMetrics;
  generated_at: string;
}

// Updated Metric Card Component with Icons (matches dashboard)
function MetricCard({ 
  title, 
  value, 
  icon, 
  subtitle
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <div className="text-gray-600">
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      {subtitle && (
        <p className="text-sm text-gray-500">{subtitle}</p>
      )}
    </div>
  );
}

// Chart data transformation utilities
const transformGrowthData = (coursesData: any[], usersData: any[]) => {
  // Create a map for easy lookup
  const usersMap = new Map();
  usersData.forEach(item => {
    usersMap.set(item.month, item);
  });

  return coursesData.map(courseItem => {
    const userItem = usersMap.get(courseItem.month) || {};
    return {
      month: courseItem.month,
      courses_created: courseItem.courses || 0,
      users_registered: userItem.users || 0,
      growth_rate: courseItem.growth_rate || 0,
    };
  });
};

const transformDifficultyData = (difficultyData: any[]) => {
  return difficultyData.map(item => ({
    label: item.difficulty_level,
    value: item.count,
    color: item.difficulty_level === 'beginner' ? '#9CA3AF' : 
           item.difficulty_level === 'intermediate' ? '#6B7280' : '#00B38F'
  }));
};

const transformRevenueData = (revenueData: RevenueMonthlyData[]) => {
  return revenueData.map(item => ({
    label: item.month_name,
    value: item.revenue,
    color: '#00B38F'
  }));
};

const transformPopularCoursesData = (popularCourses: PopularCourse[]) => {
  return popularCourses.slice(0, 8).map(course => ({
    label: course.title.length > 20 ? course.title.substring(0, 17) + '...' : course.title,
    value: course.lesson_count,
    color: course.course_type === 'premium' ? '#8B5CF6' : '#06B6D4'
  }));
};

// Main Analytics Page Component with Chart.js
export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [subscriptionStats, setSubscriptionStats] = useState<SubscriptionStats | null>(null);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueMonthlyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Fetch analytics data
  const fetchAnalytics = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      
      setError(null);
      const data = await adminAPI.getDashboardAnalytics();
      setAnalyticsData(data);
      
      // Fetch subscription and email stats
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const subsResponse = await fetch('http://localhost:8000/api/admin/subscriptions-management/?page=1&page_size=1', { headers });
      if (subsResponse.ok) {
        const subsData = await subsResponse.json();
        setSubscriptionStats(subsData.analytics);
      }

      const emailResponse = await fetch('http://localhost:8000/api/admin/email-analytics/', { headers });
      if (emailResponse.ok) {
        const emailData = await emailResponse.json();
        setEmailStats(emailData.analytics);
      }

      // Fetch revenue analytics
      const revenueResponse = await fetch('http://localhost:8000/api/admin/revenue/analytics/', { headers });
      if (revenueResponse.ok) {
        const revenueDataRes = await revenueResponse.json();
        setRevenueData(revenueDataRes.monthly_revenue || []);
      }

      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load and auto-refresh setup (increased to 60s)
  useEffect(() => {
    fetchAnalytics();
    
    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  if (loading && !analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="h-80 bg-gray-200 rounded-lg"></div>
              <div className="h-80 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics Unavailable</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => fetchAnalytics()}
              className="bg-teal-600 text-white px-6 py-3 rounded-lg hover:bg-teal-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!analyticsData) return null;

  const { course_metrics, content_metrics, user_metrics, popular_courses, growth_metrics } = analyticsData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
              <p className="mt-1 text-sm text-gray-600">
                Platform performance and business metrics
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {lastUpdate && (
                <span className="text-sm text-gray-500">
                  Updated {lastUpdate}
                </span>
              )}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${refreshing ? 'bg-amber-500 animate-pulse' : 'bg-teal-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {refreshing ? 'Updating...' : 'Auto-refresh: 60s'}
                </span>
              </div>
              <button
                onClick={() => fetchAnalytics(true)}
                disabled={refreshing}
                className="inline-flex items-center bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors text-sm font-medium"
              >
                {refreshing ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Refreshing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics Grid - MVP Focus */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <MetricCard
            title="Total Users"
            value={user_metrics.total_users}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            }
            subtitle={`${user_metrics.verified_users} verified (${user_metrics.verification_rate.toFixed(1)}%)`}
          />
          <MetricCard
            title="Total Revenue"
            value={`$${subscriptionStats?.total_revenue_usd.toFixed(2) || '0.00'}`}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            subtitle={`$${subscriptionStats?.recent_revenue_30d?.toFixed(2) || '0.00'} this month`}
          />
          <MetricCard
            title="Active Subscriptions"
            value={subscriptionStats?.active_count || 0}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            subtitle={`${subscriptionStats?.total_count || 0} total subscriptions`}
          />
          <MetricCard
            title="Total Courses"
            value={course_metrics.total_courses}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            }
            subtitle={`${course_metrics.published_courses} published`}
          />
          <MetricCard
            title="Email Templates"
            value={emailStats?.total_templates || 0}
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
            subtitle={`${emailStats?.recent_sent || 0} sent this month`}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Growth Trends Chart */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Platform Growth Trends</h2>
              <div className="text-xs text-gray-500">
                Last 12 months
              </div>
            </div>
            <div className="w-full overflow-hidden">
              <GrowthChart 
                data={transformGrowthData(growth_metrics.monthly_courses, growth_metrics.monthly_users)}
                height={240}
              />
            </div>
          </div>

          {/* Revenue Growth Chart */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Monthly Revenue</h2>
              <div className="text-xs text-gray-500">
                Last 12 months
              </div>
            </div>
            <div className="w-full overflow-hidden">
              <BarChart 
                data={transformRevenueData(revenueData)}
                title=""
                height={240}
                horizontal={false}
                showValues={true}
                maxBars={12}
              />
            </div>
          </div>
        </div>

        {/* Subscription Status Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Subscription Status</h2>
          </div>
          <div className="w-full overflow-hidden">
            <DonutChart
              data={[
                { 
                  label: 'Active', 
                  value: subscriptionStats?.active_count || 0, 
                  color: '#00B38F' 
                },
                { 
                  label: 'Inactive', 
                  value: (subscriptionStats?.total_count || 0) - (subscriptionStats?.active_count || 0), 
                  color: '#E5E7EB' 
                }
              ]}
              height={300}
              showLegend={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}