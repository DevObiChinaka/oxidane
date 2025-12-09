'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';
import MobileMenuButton from '../components/MobileMenuButton';
import { useSmartNavbar } from '../hooks/useSmartNavbar';
import { apiGet } from '@/lib/api';

interface UserData {
  id: string;
  email: string;
  name: string;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
}

interface SubscriptionData {
  active_count: number;
  total_monthly_cost: number;
  next_renewal_date: string | null;
  days_until_renewal: number | null;
  has_active_subscription: boolean;
  plan_names: string[];
}

export default function UserDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [coursesCount, setCoursesCount] = useState(0);
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'resources'>('overview');
  const showNavbar = useSmartNavbar();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Fetch user profile data
      const response = await apiGet('/auth/profile/');

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();
      setUser(data);
      
      // Fetch enrolled courses count
      await fetchEnrolledCoursesCount();
      
      // Fetch subscription data
      await fetchSubscriptionData();
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionData = async () => {
    try {
      const response = await apiGet('/subscriptions/my-subscriptions/');

      if (response.ok) {
        const data = await response.json();
        const activeSubscriptions = data.subscriptions?.filter((sub: any) => sub.status === 'active') || [];
        const planNames = activeSubscriptions.map((sub: any) => sub.plan_name);
        
        setSubscriptionData({
          active_count: data.stats?.active_count || 0,
          total_monthly_cost: data.stats?.total_monthly_cost || 0,
          next_renewal_date: data.stats?.next_renewal_date || null,
          days_until_renewal: data.stats?.days_until_renewal || null,
          has_active_subscription: activeSubscriptions.length > 0,
          plan_names: planNames,
        });
      }
    } catch (error) {
      console.error('Failed to fetch subscription data:', error);
      // Set default empty subscription data
      setSubscriptionData({
        active_count: 0,
        total_monthly_cost: 0,
        next_renewal_date: null,
        days_until_renewal: null,
        has_active_subscription: false,
        plan_names: [],
      });
    }
  };

  const fetchEnrolledCoursesCount = async () => {
    try {
      const response = await apiGet('/courses/enrolled/');

      if (response.ok) {
        const data = await response.json();

        // The API returns an object with courses array, not the array directly
        const coursesArray = data.courses || data;

        setCoursesCount(coursesArray.length || 0);
      } else {
        console.error('Failed to fetch enrolled courses, status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Failed to fetch courses count:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/auth');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-3 border-gray-200 border-t-[#00B38F] rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 text-sm">Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />

      {/* Main Content */}
      <main className="flex-1 min-h-screen lg:ml-0">
        <MobileMenuButton showNavbar={showNavbar} onMenuOpen={() => setIsMobileMenuOpen(true)} />

        {/* Header - Mobile Responsive */}
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6">
            <div className="md:flex md:items-center md:justify-between">
              <div className="flex-1 min-w-0">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  Welcome back, {user?.first_name || user?.name?.split(' ')[0] || 'User'}
                </h1>
                <p className="mt-1 text-xs sm:text-sm text-gray-600">
                  {subscriptionData?.has_active_subscription 
                    ? `Manage your ${subscriptionData.active_count} active subscription${subscriptionData.active_count > 1 ? 's' : ''} and learning progress` 
                    : 'Track your learning journey and manage your account'}
                </p>
              </div>
              <div className="mt-3 md:mt-0 flex items-center space-x-3">
                <div className="text-right hidden lg:block">
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Account</p>
                  <p className="text-sm text-gray-700 font-medium truncate max-w-[200px]">{user?.email}</p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00B38F] to-[#00A87D] flex items-center justify-center text-white font-bold text-sm shadow-sm">
                  {(user?.first_name?.[0] || user?.name?.[0] || 'U').toUpperCase()}
                </div>
              </div>
            </div>

            {/* Analytics Cards - Mobile Responsive */}
            <div className="mt-4 sm:mt-6 grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-[#00B38F]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Subscriptions</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{subscriptionData?.active_count || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-cyan-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">My Courses</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{coursesCount}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      {user?.is_email_verified ? (
                        <svg className="h-5 w-5 sm:h-6 sm:w-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 sm:h-6 sm:w-6 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                      )}
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Email Status</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">
                          {user?.is_email_verified ? 'Verified' : 'Pending'}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Account</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">Active</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 mt-4 sm:mt-6">
          {/* Tabs - Mobile Responsive */}
          <div className="border-b border-gray-200 overflow-x-auto">
            <nav className="-mb-px flex space-x-4 sm:space-x-8 min-w-max">
              <button
                onClick={() => setActiveTab('overview')}
                className={`${
                  activeTab === 'overview'
                    ? 'border-[#00B38F] text-[#00B38F]'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
                } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
              >
                <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                </svg>
                <span>Overview</span>
              </button>

              <button
                onClick={() => setActiveTab('activity')}
                className={`${
                  activeTab === 'activity'
                    ? 'border-[#00B38F] text-[#00B38F]'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
                } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
              >
                <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                </svg>
                <span className="hidden sm:inline">Learning Activity</span>
                <span className="sm:hidden">Activity</span>
              </button>

              <button
                onClick={() => setActiveTab('resources')}
                className={`${
                  activeTab === 'resources'
                    ? 'border-[#00B38F] text-[#00B38F]'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
                } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
              >
                <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
                </svg>
                <span>Resources</span>
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="mt-6 pb-12">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-4 sm:space-y-6">
                {/* Subscription Status Section */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-base sm:text-lg font-medium text-gray-900">Subscription Status</h3>
                        <p className="mt-1 text-xs sm:text-sm text-gray-600">
                          {subscriptionData?.has_active_subscription 
                            ? 'Manage your active plans and benefits' 
                            : 'Get access to premium features'}
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2.5 sm:px-3 py-1 rounded-full text-xs font-medium ${
                        subscriptionData?.has_active_subscription 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {subscriptionData?.has_active_subscription ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    {subscriptionData?.has_active_subscription ? (
                      <div className="mt-4 space-y-3">
                        {subscriptionData.plan_names.map((plan, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 sm:p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-[#00B38F] flex items-center justify-center flex-shrink-0">
                                <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </div>
                              <div>
                                <p className="text-sm sm:text-base font-medium text-gray-900">{plan}</p>
                                <p className="text-xs text-gray-500">Premium Access</p>
                              </div>
                            </div>
                            <button
                              onClick={() => router.push('/subscriptions')}
                              className="text-xs sm:text-sm text-[#00B38F] hover:text-[#00A87D] font-medium"
                            >
                              Manage
                            </button>
                          </div>
                        ))}
                        {subscriptionData.days_until_renewal !== null && (
                          <div className="mt-4 p-3 sm:p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-xs sm:text-sm text-blue-800">
                              <span className="font-medium">Next renewal:</span> in {subscriptionData.days_until_renewal} day{subscriptionData.days_until_renewal !== 1 ? 's' : ''}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="mt-4 p-6 sm:p-8 bg-gradient-to-br from-[#00B38F]/5 to-cyan-50 rounded-lg border border-[#00B38F]/20">
                        <div className="text-center">
                          <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 rounded-full bg-[#00B38F]/10 flex items-center justify-center">
                            <svg className="w-6 h-6 sm:w-8 sm:h-8 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                          </div>
                          <h4 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Unlock Premium Features</h4>
                          <p className="text-xs sm:text-sm text-gray-600 mb-4 max-w-md mx-auto">
                            Get access to exclusive Forex signals, expert mentorship, and premium trading strategies
                          </p>
                          <a
                            href="/pricing"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-4 sm:px-6 py-2 sm:py-3 bg-[#00B38F] text-white font-medium text-xs sm:text-sm rounded-lg hover:bg-[#00A87D] transition-colors"
                          >
                            <span>View Plans</span>
                            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                            </svg>
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Quick Actions Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  <button
                    onClick={() => router.push('/courses')}
                    className="bg-white border border-gray-200 rounded-lg p-4 sm:p-5 hover:border-[#00B38F] hover:shadow-md transition-all text-left group"
                  >
                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gray-50 group-hover:bg-[#00B38F]/10 flex items-center justify-center mb-3 transition-colors">
                      <svg className="w-5 h-5 sm:w-6 sm:h-6 text-[#000ABE] group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <span className="text-xs sm:text-sm font-medium text-gray-900">Browse Courses</span>
                    <p className="text-xs text-gray-500 mt-1">Explore library</p>
                  </button>

                  <button
                    onClick={() => router.push('/my-courses')}
                    className="bg-white border border-gray-200 rounded-lg p-4 sm:p-5 hover:border-[#00B38F] hover:shadow-md transition-all text-left group"
                  >
                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gray-50 group-hover:bg-[#00B38F]/10 flex items-center justify-center mb-3 transition-colors">
                      <svg className="w-5 h-5 sm:w-6 sm:h-6 text-cyan-600 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </div>
                    <span className="text-xs sm:text-sm font-medium text-gray-900">My Courses</span>
                    <p className="text-xs text-gray-500 mt-1">{coursesCount} enrolled</p>
                  </button>

                  <button
                    onClick={() => router.push('/profile')}
                    className="bg-white border border-gray-200 rounded-lg p-4 sm:p-5 hover:border-[#00B38F] hover:shadow-md transition-all text-left group"
                  >
                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gray-50 group-hover:bg-[#00B38F]/10 flex items-center justify-center mb-3 transition-colors">
                      <svg className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <span className="text-xs sm:text-sm font-medium text-gray-900">Edit Profile</span>
                    <p className="text-xs text-gray-500 mt-1">Update info</p>
                  </button>

                  <button
                    onClick={() => router.push('/settings')}
                    className="bg-white border border-gray-200 rounded-lg p-4 sm:p-5 hover:border-[#00B38F] hover:shadow-md transition-all text-left group"
                  >
                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gray-50 group-hover:bg-[#00B38F]/10 flex items-center justify-center mb-3 transition-colors">
                      <svg className="w-5 h-5 sm:w-6 sm:h-6 text-gray-600 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <span className="text-xs sm:text-sm font-medium text-gray-900">Settings</span>
                    <p className="text-xs text-gray-500 mt-1">Preferences</p>
                  </button>
                </div>
              </div>
            )}

            {/* Activity Tab */}
            {activeTab === 'activity' && (
              <div className="space-y-4 sm:space-y-6">
                {/* Learning Progress */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-4">Learning Progress</h3>
                    
                    {coursesCount > 0 ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-cyan-100 flex items-center justify-center">
                              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                              </svg>
                            </div>
                            <div>
                              <p className="text-sm sm:text-base font-medium text-gray-900">Enrolled Courses</p>
                              <p className="text-xs sm:text-sm text-gray-500">{coursesCount} course{coursesCount !== 1 ? 's' : ''} in progress</p>
                            </div>
                          </div>
                          <button
                            onClick={() => router.push('/my-courses')}
                            className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white border border-gray-300 rounded-lg text-xs sm:text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            View All
                          </button>
                        </div>

                        <div className="p-4 sm:p-6 bg-blue-50 border border-blue-200 rounded-lg">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0">
                              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </div>
                            <div>
                              <h4 className="text-sm sm:text-base font-medium text-blue-900 mb-1">Keep Learning!</h4>
                              <p className="text-xs sm:text-sm text-blue-800">
                                Continue your courses to unlock new trading strategies and improve your skills.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 sm:py-12">
                        <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                          <svg className="w-8 h-8 sm:w-10 sm:h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                        </div>
                        <h4 className="text-base sm:text-lg font-medium text-gray-900 mb-2">No courses yet</h4>
                        <p className="text-xs sm:text-sm text-gray-600 mb-4">Start learning by enrolling in your first course</p>
                        <button
                          onClick={() => router.push('/courses')}
                          className="inline-flex items-center px-4 sm:px-6 py-2 sm:py-3 bg-[#00B38F] text-white font-medium text-xs sm:text-sm rounded-lg hover:bg-[#00A87D] transition-colors"
                        >
                          Browse Courses
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Account Activity */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-4">Account Activity</h3>
                    <div className="space-y-3">
                      <div className="flex items-start gap-3 p-3 sm:p-4 bg-gray-50 rounded-lg">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          user?.is_email_verified ? 'bg-green-100' : 'bg-amber-100'
                        }`}>
                          {user?.is_email_verified ? (
                            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900">Email Verification</p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {user?.is_email_verified ? 'Your email is verified' : 'Please verify your email address'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 p-3 sm:p-4 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900">Account Created</p>
                          <p className="text-xs text-gray-500 mt-0.5">Welcome to the platform!</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Resources Tab */}
            {activeTab === 'resources' && (
              <div className="space-y-4 sm:space-y-6">
                {/* Premium Resources */}
                {!subscriptionData?.has_active_subscription && (
                  <div className="bg-gradient-to-br from-[#00B38F]/10 via-cyan-50 to-blue-50 border-2 border-[#00B38F]/30 rounded-lg p-6 sm:p-8">
                    <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                      <div className="flex-1">
                        <div className="inline-flex items-center px-3 py-1 bg-white/80 backdrop-blur-sm rounded-full mb-3 sm:mb-4">
                          <svg className="w-4 h-4 text-[#00B38F] mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          <span className="text-[#00B38F] font-semibold text-xs sm:text-sm">Premium Resources</span>
                        </div>
                        <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">Unlock Exclusive Trading Resources</h3>
                        <p className="text-xs sm:text-sm text-gray-700 mb-4 sm:mb-6">
                          Get instant access to premium Forex signals, expert analysis, trading strategies, and mentorship from professional traders.
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 sm:mb-6">
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-xs sm:text-sm text-gray-700">Real-time Forex signals</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-xs sm:text-sm text-gray-700">Expert market analysis</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-xs sm:text-sm text-gray-700">Trading strategies</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-xs sm:text-sm text-gray-700">24/7 Community support</span>
                          </div>
                        </div>
                        <a
                          href="/pricing"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-5 sm:px-6 py-2.5 sm:py-3 bg-[#00B38F] text-white font-semibold text-xs sm:text-sm rounded-lg hover:bg-[#00A87D] shadow-lg hover:shadow-xl transition-all"
                        >
                          <span>View Subscription Plans</span>
                          <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </a>
                      </div>
                      <div className="hidden lg:block flex-shrink-0">
                        <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-white/60 to-white/30 backdrop-blur-sm flex items-center justify-center shadow-lg">
                          <svg className="w-20 h-20 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quick Links */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-4">Quick Links</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                      <a
                        href="/pricing"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-3 sm:p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 hover:border-[#00B38F] transition-all group"
                      >
                        <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                          <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900 group-hover:text-[#00B38F] transition-colors">Pricing Plans</p>
                          <p className="text-xs text-gray-500">View all plans</p>
                        </div>
                        <svg className="w-4 h-4 text-gray-400 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </a>

                      <button
                        onClick={() => router.push('/billing')}
                        className="flex items-center gap-3 p-3 sm:p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 hover:border-[#00B38F] transition-all group text-left"
                      >
                        <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900 group-hover:text-[#00B38F] transition-colors">Billing & Payment</p>
                          <p className="text-xs text-gray-500">Manage payments</p>
                        </div>
                        <svg className="w-4 h-4 text-gray-400 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>

                      <button
                        onClick={() => router.push('/subscriptions')}
                        className="flex items-center gap-3 p-3 sm:p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 hover:border-[#00B38F] transition-all group text-left"
                      >
                        <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900 group-hover:text-[#00B38F] transition-colors">My Subscriptions</p>
                          <p className="text-xs text-gray-500">{subscriptionData?.active_count || 0} active</p>
                        </div>
                        <svg className="w-4 h-4 text-gray-400 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>

                      <button
                        onClick={() => router.push('/settings')}
                        className="flex items-center gap-3 p-3 sm:p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 hover:border-[#00B38F] transition-all group text-left"
                      >
                        <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900 group-hover:text-[#00B38F] transition-colors">Account Settings</p>
                          <p className="text-xs text-gray-500">Manage preferences</p>
                        </div>
                        <svg className="w-4 h-4 text-gray-400 group-hover:text-[#00B38F] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm font-medium text-gray-900">Account Created</p>
                          <p className="text-xs text-gray-500 mt-0.5">Welcome to the platform!</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
              {/* Stats Cards - Clean and Minimal */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {/* Subscription Status Card */}
                <div className="bg-white border border-gray-200 rounded-lg p-4 sm:p-6 hover:border-gray-300 transition-colors">
                  <div className="flex items-start justify-between mb-3 sm:mb-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Subscription</p>
                      <p className="text-xl sm:text-2xl font-semibold text-gray-900">
                        {subscriptionData?.has_active_subscription ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded bg-gray-50 flex items-center justify-center">
                      <svg className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${
                        subscriptionData?.has_active_subscription ? 'text-[#00B38F]' : 'text-gray-400'
                      }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 space-y-1">
                    {subscriptionData?.plan_names && subscriptionData.plan_names.length > 0 ? (
                      <>
                        {subscriptionData.plan_names.slice(0, 2).map((name, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-green-500 rounded-full flex-shrink-0" />
                            <span className="truncate">{name}</span>
                          </div>
                        ))}
                        {subscriptionData.plan_names.length > 2 && (
                          <button
                            onClick={() => router.push('/subscriptions')}
                            className="text-xs text-blue-600 hover:text-blue-700 hover:underline ml-3.5 transition-colors"
                          >
                            +{subscriptionData.plan_names.length - 2} more plan{subscriptionData.plan_names.length - 2 > 1 ? 's' : ''}
                          </button>
                        )}
                      </>
                    ) : (
                      <span>No active plans</span>
                    )}
                  </div>
                </div>

                {/* Enrolled Courses Card */}
                <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">My Courses</p>
                      <p className="text-2xl font-semibold text-gray-900">{coursesCount}</p>
                    </div>
                    <div className="w-8 h-8 rounded bg-gray-50 flex items-center justify-center">
                      <svg className="w-4 h-4 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    {coursesCount === 1 ? 'Enrolled course' : 'Enrolled courses'}
                  </p>
                </div>

                {/* Email Verification Card */}
                <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Email Status</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {user?.is_email_verified ? 'Verified' : 'Pending'}
                      </p>
                    </div>
                    <div className="w-8 h-8 rounded bg-gray-50 flex items-center justify-center">
                      {user?.is_email_verified ? (
                        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">
                    {user?.is_email_verified ? 'Email confirmed' : 'Verification pending'}
                  </p>
                </div>
              </div>

                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
