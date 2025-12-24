'use client';

import { useState, useEffect } from 'react';
import { useDashboardMetrics } from '../hooks/useAdminAPI';
import { adminAPI } from '../utils/api';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/config/api';

interface SetupStatus {
  setup_complete: boolean;
  completion_percentage: number;
  components: {
    telegram: { configured: boolean };
    payment: { configured: boolean };
    email: { configured: boolean };
    database: { has_active_plans: boolean };
  };
  summary: {
    total_checks: number;
    completed_checks: number;
  };
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

export default function AdminDashboard() {
  const router = useRouter();
  const { data: dashboardMetrics, loading: metricsLoading, error: metricsError } = useDashboardMetrics();
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [subscriptionStats, setSubscriptionStats] = useState<SubscriptionStats | null>(null);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdditionalData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };

        // Fetch setup status
        const setupResponse = await fetch(API_ENDPOINTS.admin.setupStatus, { headers });
        if (setupResponse.ok) {
          const setupData = await setupResponse.json();
                    setSetupStatus(setupData);
        } else {
                  }

        // Fetch subscription stats
        const subsResponse = await fetch(`${API_ENDPOINTS.admin.subscriptions}?page=1&page_size=1`, { headers });
        if (subsResponse.ok) {
          const subsData = await subsResponse.json();
                    setSubscriptionStats(subsData.analytics);
        } else {
                    const errorText = await subsResponse.text();
                  }

        // Fetch email stats
        const emailResponse = await fetch(API_ENDPOINTS.admin.emailAnalytics, { headers });
        if (emailResponse.ok) {
          const emailData = await emailResponse.json();
                    setEmailStats(emailData.analytics);
        } else {
                  }
      } catch (error) {
              } finally {
        setLoading(false);
      }
    };

    if (!metricsLoading) {
      fetchAdditionalData();
    }
  }, [metricsLoading]);

  if (metricsLoading || loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="flex items-center gap-3 text-gray-600">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-[#00B38F]"></div>
          <span className="font-medium">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (metricsError) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-900 font-medium">Failed to load dashboard</p>
          <p className="text-gray-500 text-sm mt-1">{metricsError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-3 sm:p-6">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="px-2 sm:px-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">Monitor platform performance and metrics</p>
        </div>

        {/* Platform Health Status */}
        {setupStatus && (
          <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
                  setupStatus.setup_complete 
                    ? 'bg-teal-50' 
                    : 'bg-gray-100'
                }`}>
                  {setupStatus.setup_complete ? (
                    <svg className="w-5 h-5 sm:w-6 sm:h-6 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 sm:w-6 sm:h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900">
                    Platform Setup {setupStatus.setup_complete ? 'Complete' : 'In Progress'}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600">
                    {setupStatus.summary.completed_checks} of {setupStatus.summary.total_checks} components configured
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 sm:gap-6">
                <div className="text-right">
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {setupStatus.completion_percentage}%
                  </div>
                  <div className="text-xs text-gray-600">
                    Complete
                  </div>
                </div>
                {!setupStatus.setup_complete && (
                  <button
                    onClick={() => router.push('/admin/setup')}
                    className="px-3 sm:px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm rounded-lg font-medium transition-colors whitespace-nowrap"
                  >
                    Complete Setup
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {/* Total Users */}
          <MetricCard
            title="Total Users"
            value={dashboardMetrics?.users?.total || 0}
            subtitle={`${dashboardMetrics?.users?.verified || 0} verified`}
            icon={
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            }
            trend={dashboardMetrics?.users?.recent_signups ? `+${dashboardMetrics.users.recent_signups} this week` : undefined}
          />

          {/* Active Subscriptions */}
          <MetricCard
            title="Active Subscriptions"
            value={subscriptionStats?.active_count || 0}
            subtitle={`${subscriptionStats?.total_count || 0} total`}
            icon={
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            trend={subscriptionStats?.recent_revenue_30d ? `$${subscriptionStats.recent_revenue_30d.toFixed(2)} this month` : undefined}
          />

          {/* Total Courses */}
          <MetricCard
            title="Total Courses"
            value={dashboardMetrics?.courses?.total || 0}
            subtitle={`${dashboardMetrics?.courses?.published || 0} published`}
            icon={
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            }
            trend={`${dashboardMetrics?.content?.total_lessons || 0} lessons`}
          />

          {/* Email Templates */}
          <MetricCard
            title="Email Templates"
            value={emailStats?.total_templates || 0}
            subtitle={`${emailStats?.active_templates || 0} active`}
            icon={
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
            trend={emailStats ? `${emailStats.recent_sent} sent this month` : undefined}
          />
        </div>

        {/* Revenue & Engagement Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-6">
          {/* Revenue Overview */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900">Revenue Overview</h3>
              <button
                onClick={() => router.push('/admin/subscriptions-management')}
                className="text-xs sm:text-sm text-[#00B38F] hover:text-[#00A87D] font-medium whitespace-nowrap"
              >
                View All →
              </button>
            </div>
            <div className="space-y-3 sm:space-y-4">
              <div className="flex items-center justify-between py-2 sm:py-3 border-b border-gray-100">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs sm:text-sm text-gray-600">Total Revenue</div>
                    <div className="text-base sm:text-xl font-semibold text-gray-900 truncate">
                      ${(subscriptionStats?.total_revenue_usd || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between py-2 sm:py-3 border-b border-gray-100">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs sm:text-sm text-gray-600">This Month</div>
                    <div className="text-base sm:text-xl font-semibold text-gray-900 truncate">
                      ${(subscriptionStats?.recent_revenue_30d || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between py-2 sm:py-3">
                <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs sm:text-sm text-gray-600">Active Subscribers</div>
                    <div className="text-base sm:text-xl font-semibold text-gray-900 truncate">
                      {subscriptionStats?.active_count || 0}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Learning Engagement */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900">Learning Engagement</h3>
              <button
                onClick={() => router.push('/admin/courses')}
                className="text-xs sm:text-sm text-[#00B38F] hover:text-[#00A87D] font-medium whitespace-nowrap"
              >
                View Courses →
              </button>
            </div>
            <div className="space-y-3 sm:space-y-4">
              <div className="flex items-center justify-between py-2 sm:py-3 border-b border-gray-100">
                <span className="text-xs sm:text-sm text-gray-600 min-w-0 truncate pr-2">Total Enrollments</span>
                <span className="text-sm sm:text-base font-semibold text-gray-900 flex-shrink-0">
                  {dashboardMetrics?.engagement?.total_enrollments || 0}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 sm:py-3 border-b border-gray-100">
                <span className="text-xs sm:text-sm text-gray-600 min-w-0 truncate pr-2">Active Learners</span>
                <span className="text-sm sm:text-base font-semibold text-gray-900 flex-shrink-0">
                  {dashboardMetrics?.engagement?.active_learners || 0}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 sm:py-3 border-b border-gray-100">
                <span className="text-xs sm:text-sm text-gray-600 min-w-0 truncate pr-2">Completed Courses</span>
                <span className="text-sm sm:text-base font-semibold text-gray-900 flex-shrink-0">
                  {dashboardMetrics?.engagement?.completed_courses || 0}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 sm:py-3">
                <span className="text-xs sm:text-sm text-gray-600 min-w-0 truncate pr-2">Avg. Completion Rate</span>
                <span className="text-sm sm:text-base font-semibold text-gray-900 flex-shrink-0">
                  {dashboardMetrics?.engagement?.avg_completion_rate || 0}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            <QuickActionButton
              label="Manage Users"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              }
              onClick={() => router.push('/admin/users')}
            />
            <QuickActionButton
              label="Email Templates"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              }
              onClick={() => router.push('/admin/emails')}
            />
            <QuickActionButton
              label="Pricing Plans"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              onClick={() => router.push('/admin/plans')}
            />
            <QuickActionButton
              label="Settings"
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              }
              onClick={() => router.push('/admin/settings/system')}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Metric Card Component
function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend
}: {
  title: string;
  value: number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm font-medium text-gray-600 truncate">{title}</p>
          <p className="text-xl sm:text-2xl font-bold text-gray-900 mt-1 sm:mt-2">{value.toLocaleString()}</p>
          {subtitle && (
            <p className="text-xs sm:text-sm text-gray-500 mt-1 truncate">{subtitle}</p>
          )}
          {trend && (
            <p className="text-xs text-[#00B38F] mt-1 sm:mt-2 truncate">{trend}</p>
          )}
        </div>
        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
      </div>
    </div>
  );
}

// Quick Action Button Component
function QuickActionButton({
  label,
  icon,
  onClick
}: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center p-3 sm:p-4 rounded-lg border border-gray-200 hover:border-[#00B38F] hover:bg-gray-50 transition-all group"
    >
      <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-100 rounded-lg flex items-center justify-center mb-2 group-hover:bg-[#00B38F] transition-colors">
        <div className="text-gray-600 group-hover:text-white transition-colors">
          {icon}
        </div>
      </div>
      <span className="text-xs sm:text-sm font-medium text-gray-700 group-hover:text-gray-900 text-center">
        {label}
      </span>
    </button>
  );
}
