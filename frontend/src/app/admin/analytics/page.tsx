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

// Consistent Metric Card Component (matches dashboard style)
function MetricCard({ 
  title, 
  value, 
  icon, 
  change, 
  changeType 
}: {
  title: string;
  value: string | number;
  icon: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
}) {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }[changeType];

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-700">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          <p className={`text-xs ${changeColor}`}>{change}</p>
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
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
    color: item.difficulty_level === 'beginner' ? '#3B82F6' : 
           item.difficulty_level === 'intermediate' ? '#10B981' : '#F59E0B'
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
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load and auto-refresh setup
  useEffect(() => {
    fetchAnalytics();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 30000);

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
            <div className="text-red-600 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics Unavailable</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => fetchAnalytics()}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
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
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">
                Live business metrics and performance insights
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {lastUpdate && (
                <span className="text-sm text-gray-500">
                  Last updated: {lastUpdate}
                </span>
              )}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${refreshing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {refreshing ? 'Updating...' : 'Live (Auto-refresh: 30s)'}
                </span>
              </div>
              <button
                onClick={() => fetchAnalytics(true)}
                disabled={refreshing}
                className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm font-medium"
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
                    Refresh Now
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4 mb-6">
          <MetricCard
            title="Total Courses"
            value={course_metrics.total_courses}
            icon="📚"
            change={`${course_metrics.published_courses} published (${course_metrics.publish_rate.toFixed(1)}%)`}
            changeType={course_metrics.publish_rate > 75 ? 'positive' : course_metrics.publish_rate > 50 ? 'neutral' : 'negative'}
          />
          <MetricCard
            title="Total Lessons"
            value={content_metrics.total_lessons}
            icon="🎥"
            change={`${content_metrics.total_duration_hours.toFixed(1)} hours content`}
            changeType="positive"
          />
          <MetricCard
            title="Total Users"
            value={user_metrics.total_users}
            icon="👥"
            change={`${user_metrics.verified_users} verified (${user_metrics.verification_rate.toFixed(1)}%)`}
            changeType={user_metrics.verification_rate > 75 ? 'positive' : 'neutral'}
          />
          <MetricCard
            title="Course Growth"
            value={`${growth_metrics?.course_trend_summary?.percentage > 0 ? '+' : ''}${(growth_metrics?.course_trend_summary?.percentage || 0).toFixed(1)}%`}
            icon="📈"
            change="Last 3 months trend"
            changeType={
              growth_metrics?.course_trend_summary?.trend === 'up' ? 'positive' : 
              growth_metrics?.course_trend_summary?.trend === 'down' ? 'negative' : 'neutral'
            }
          />
          <MetricCard
            title="User Growth"
            value={`${growth_metrics?.user_trend_summary?.percentage > 0 ? '+' : ''}${(growth_metrics?.user_trend_summary?.percentage || 0).toFixed(1)}%`}
            icon="👤"
            change="User registration trend"
            changeType={
              growth_metrics?.user_trend_summary?.trend === 'up' ? 'positive' : 
              growth_metrics?.user_trend_summary?.trend === 'down' ? 'negative' : 'neutral'
            }
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Growth Trends Chart */}
          <div className="bg-white rounded-lg shadow-sm p-4 overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Growth Trends</h2>
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

          {/* Difficulty Distribution */}
          <div className="bg-white rounded-lg shadow-sm p-4 overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Course Difficulty Distribution</h2>
            </div>
            <div className="w-full overflow-hidden">
              <DonutChart
                data={transformDifficultyData(course_metrics.difficulty_distribution)}
                height={240}
                showLegend={true}
              />
            </div>
          </div>
        </div>

        {/* Second Row of Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Popular Courses */}
          <div className="bg-white rounded-lg shadow-sm p-4 overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Popular Courses by Lessons</h2>
            </div>
            <div className="w-full overflow-hidden">
              <BarChart
                data={transformPopularCoursesData(popular_courses)}
                title=""
                height={240}
                horizontal={false}
                showValues={false}
                maxBars={6}
              />
            </div>
          </div>

          {/* Course Types */}
          <div className="bg-white rounded-lg shadow-sm p-4 overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Course Types</h2>
            </div>
            <div className="w-full overflow-hidden">
              <DonutChart
                data={[
                  { label: 'Free Courses', value: course_metrics.free_courses, color: '#10B981' },
                  { label: 'Premium Courses', value: course_metrics.premium_courses, color: '#8B5CF6' }
                ]}
                height={240}
                showLegend={true}
              />
            </div>
          </div>
        </div>

        {/* Recent Activity Summary */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              title="Recent Registrations (7d)"
              value={user_metrics.recent_registrations_7d}
              icon="🆕"
              change="Last 7 days"
              changeType="positive"
            />
            <MetricCard
              title="Recent Registrations (30d)"
              value={user_metrics.recent_registrations_30d}
              icon="📊"
              change="Last 30 days"
              changeType="positive"
            />
            <MetricCard
              title="Preview Lessons"
              value={content_metrics.preview_lessons}
              icon="👁️"
              change={`${content_metrics.preview_percentage.toFixed(1)}% of total`}
              changeType="neutral"
            />
          </div>
        </div>
      </div>
    </div>
  );
}