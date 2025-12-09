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

        {/* Welcome Section */}
        <div className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">
                Welcome back, {user?.first_name || user?.name?.split(' ')[0] || 'User'}
              </h1>
              <p className="text-xs sm:text-sm text-gray-500 mt-1">
                {subscriptionData?.has_active_subscription 
                  ? `You have ${subscriptionData.active_count} active subscription${subscriptionData.active_count > 1 ? 's' : ''}` 
                  : 'Manage your account and subscriptions'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right hidden md:block">
                <p className="text-xs text-gray-400 uppercase tracking-wide">Account</p>
                <p className="text-sm text-gray-700 font-medium">{user?.email}</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-[#00B38F] flex items-center justify-center text-white font-semibold text-sm">
                {(user?.first_name?.[0] || user?.name?.[0] || 'U').toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="p-3 sm:p-4 md:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
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

              {/* Quick Actions */}
              <div className="bg-white border-2 border-gray-200 rounded-2xl p-8 shadow-sm">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
                  <p className="text-sm text-gray-500 mt-1">Access key features</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <button
                    onClick={() => router.push('/courses')}
                    className="flex flex-col items-start p-5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded flex items-center justify-center bg-gray-50 mb-3">
                      <svg className="w-4 h-4 text-[#000ABE]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <span className="text-sm font-medium text-gray-900">Browse Courses</span>
                    <span className="text-xs text-gray-500 mt-1">Explore library</span>
                  </button>

                  <a
                    href="/pricing"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex flex-col items-start p-5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded flex items-center justify-center bg-gray-50 mb-3">
                      <svg className="w-4 h-4 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <span className="text-sm font-medium text-gray-900">View Plans</span>
                    <span className="text-xs text-gray-500 mt-1">Upgrade membership</span>
                  </a>

                  <button
                    onClick={() => router.push('/profile')}
                    className="flex flex-col items-start p-5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded flex items-center justify-center bg-gray-50 mb-3">
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <span className="text-sm font-medium text-gray-900">Edit Profile</span>
                    <span className="text-xs text-gray-500 mt-1">Your account</span>
                  </button>

                  <button
                    onClick={() => router.push('/settings')}
                    className="flex flex-col items-start p-5 rounded-lg bg-white border border-gray-200 hover:border-gray-300 transition-colors text-left"
                  >
                    <div className="w-8 h-8 rounded flex items-center justify-center bg-gray-50 mb-3">
                      <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <span className="text-sm font-medium text-gray-900">Settings</span>
                    <span className="text-xs text-gray-500 mt-1">Preferences</span>
                  </button>
                </div>
              </div>

              {/* Getting Started */}
              {!subscriptionData?.has_active_subscription && (
                <div className="bg-white border border-gray-200 rounded-lg p-8">
                  <div className="flex items-start justify-between gap-8">
                    <div className="flex-1">
                      <div className="inline-flex items-center px-3 py-1 bg-gray-100 rounded-full mb-4">
                        <svg className="w-4 h-4 text-gray-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        <span className="text-gray-700 font-medium text-xs">Premium Feature</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        Unlock Your Trading Potential
                      </h3>
                      <p className="text-gray-600 text-sm mb-6 max-w-2xl">
                        Get instant access to premium Forex signals, expert mentorship, exclusive trading strategies, and a thriving community of successful traders.
                      </p>
                      <div className="flex flex-wrap gap-4 mb-6">
                        <div className="flex items-center text-gray-700">
                          <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm">Real-time signals</span>
                        </div>
                        <div className="flex items-center text-gray-700">
                          <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm">Expert mentorship</span>
                        </div>
                        <div className="flex items-center text-gray-700">
                          <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm">24/7 Support</span>
                        </div>
                      </div>
                      <a
                        href="/pricing"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-6 py-3 bg-[#00B38F] text-white font-medium text-sm rounded-lg hover:bg-[#00A87D] transition-colors"
                      >
                        <span>View Subscription Plans</span>
                        <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </a>
                    </div>
                    
                    {/* Graduation Cap Icon */}
                    <div className="hidden lg:block flex-shrink-0">
                      <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#00B38F]/10 to-cyan-50 flex items-center justify-center">
                        <svg className="w-14 h-14 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
        </div>
      </main>
    </div>
  );
}
