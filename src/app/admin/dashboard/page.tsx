'use client';

import { useDashboardMetrics, useCourses } from '../hooks/useAdminAPI';
import { adminAPI } from '../utils/api';
import { useEffect } from 'react';

interface PricingMetrics {
  revenue: {
    daily: number;
    monthly: number;
  };
  subscriptions: {
    active_total: number;
    breakdown: {
      weekly: { count: number; revenue: number };
      monthly: { count: number; revenue: number };
      vip: { count: number; revenue: number };
    };
  };
  pending_actions: {
    telegram_adds: number;
    payment_verifications: number;
  };
}

export default function AdminDashboard() {
  // Test backend connectivity on load
  useEffect(() => {
    const testBackend = async () => {
      console.log('🔍 Testing backend connectivity...');
      const isConnected = await adminAPI.testConnection();
      console.log('🔍 Backend connectivity result:', isConnected ? '✅ Connected' : '❌ Failed');
      
      // Also check if admin token exists
      const token = localStorage.getItem('admin_token');
      console.log('🔍 Admin token status:', token ? '✅ Present' : '❌ Missing');
    };
    testBackend();
  }, []);

  // Real API data hooks
  const { data: dashboardMetrics, loading: metricsLoading, error: metricsError } = useDashboardMetrics();
  const { data: coursesData, loading: coursesLoading, error: coursesError } = useCourses(1);

  // Mock data for pricing (will be replaced with real API in Phase 2)
  const pricingMetrics: PricingMetrics = {
    revenue: { daily: 450.00, monthly: 8970.00 },
    subscriptions: {
      active_total: 89,
      breakdown: {
        weekly: { count: 23, revenue: 2070.00 },
        monthly: { count: 52, revenue: 5148.00 },
        vip: { count: 14, revenue: 4186.00 }
      }
    },
    pending_actions: { telegram_adds: 3, payment_verifications: 1 }
  };

  const loading = metricsLoading || coursesLoading;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2 text-gray-700">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          Loading dashboard...
        </div>
      </div>
    );
  }

  if (metricsError || coursesError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2 text-red-600">
          <span className="text-red-500">⚠️</span>
          Error loading dashboard: {metricsError || coursesError}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-700">Manage your OxiWorld Forex Academy platform</p>
        </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Users"
          value={dashboardMetrics?.users?.total || 0}
          icon="👥"
          change={dashboardMetrics?.users?.recent_signups ? `+${dashboardMetrics.users.recent_signups} this week` : "+0 this week"}
          changeType="positive"
        />
        <MetricCard
          title="Verified Users"
          value={dashboardMetrics?.users?.verified || 0}
          icon="✅"
          change={`${dashboardMetrics?.users?.active || 0} active`}
          changeType="positive"
        />
        <MetricCard
          title="Total Courses"
          value={dashboardMetrics?.courses?.total || 0}
          icon="�"
          change={`${dashboardMetrics?.courses?.published || 0} published`}
          changeType="positive"
        />
        <MetricCard
          title="Course Completions"
          value={dashboardMetrics?.engagement?.completed_courses || 0}
          icon="📚"
          change={`${dashboardMetrics?.engagement.recent_completions || 0} this week`}
          changeType="neutral"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Course Overview */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Course Overview</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Published Courses</span>
              <span className="font-semibold text-gray-900">{dashboardMetrics?.courses.published}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Draft Courses</span>
              <span className="font-semibold text-gray-900">{dashboardMetrics?.courses.draft}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Total Lessons</span>
              <span className="font-semibold text-gray-900">{dashboardMetrics?.content.total_lessons}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Avg. Completion Rate</span>
              <span className="font-semibold text-gray-900">{dashboardMetrics?.engagement.avg_completion_rate}%</span>
            </div>
          </div>
        </div>

        {/* Subscription Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Signal Subscriptions</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-gray-700">Weekly Plans</span>
              </div>
              <span className="font-semibold text-gray-900">{pricingMetrics?.subscriptions.breakdown.weekly.count}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-gray-700">Monthly Plans</span>
              </div>
              <span className="font-semibold text-gray-900">{pricingMetrics?.subscriptions.breakdown.monthly.count}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                <span className="text-gray-700">VIP Plans</span>
              </div>
              <span className="font-semibold text-gray-900">{pricingMetrics?.subscriptions.breakdown.vip.count}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Actions */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Pending Actions</h3>
          <div className="space-y-3">
            <ActionItem
              icon="💬"
              title="Telegram Group Additions"
              count={pricingMetrics?.pending_actions.telegram_adds || 0}
              action="Add users to premium groups"
              href="/admin/telegram"
            />
            <ActionItem
              icon="💳"
              title="Payment Verifications"
              count={pricingMetrics?.pending_actions.payment_verifications || 0}
              action="Verify pending payments"
              href="/admin/payments"
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Activity</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">New Registrations</span>
              <span className="font-semibold text-green-600">+8</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Course Completions</span>
              <span className="font-semibold text-blue-600">+{dashboardMetrics?.engagement.recent_completions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Daily Revenue</span>
              <span className="font-semibold text-green-600">${pricingMetrics?.revenue.daily}</span>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}

// Reusable Components
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

function ActionItem({
  icon,
  title,
  count,
  action,
  href
}: {
  icon: string;
  title: string;
  count: number;
  action: string;
  href: string;
}) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <span className="text-xl">{icon}</span>
        <div>
          <p className="font-medium text-gray-900">{title}</p>
          <p className="text-sm text-gray-700">{action}</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
          {count}
        </span>
        <button 
          onClick={() => window.location.href = href}
          className="text-sm text-[#00B38F] hover:text-[#00A87D] font-medium"
        >
          View →
        </button>
      </div>
    </div>
  );
}