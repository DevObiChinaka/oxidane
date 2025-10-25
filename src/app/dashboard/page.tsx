'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';

interface UserData {
  id: string;
  email: string;
  name: string;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
  subscription_status?: string;
  subscription_plan?: string;
  courses_enrolled?: number;
}

export default function UserDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [coursesCount, setCoursesCount] = useState(0);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Check if user is logged in by verifying token
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth');
        return;
      }

      // Fetch user profile data
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();
      setUser(data);
      
      // Fetch enrolled courses count
      await fetchEnrolledCoursesCount(token);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    } finally {
      setLoading(false);
    }
  };

  const fetchEnrolledCoursesCount = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/courses/enrolled/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Enrolled courses response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Enrolled courses data:', data);
        // The API returns an object with courses array, not the array directly
        const coursesArray = data.courses || data;
        console.log('Courses count:', coursesArray.length);
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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
          <p className="text-slate-300">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <DashboardSidebar />

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        {/* Top Header */}
        <header className="bg-slate-800/30 backdrop-blur-sm border-b border-slate-700/50 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">
                Welcome back, {user?.first_name || user?.name?.split(' ')[0] || 'User'}! 👋
              </h2>
              <p className="text-slate-400 mt-1">
                {user?.subscription_status === 'active' 
                  ? '✨ Your subscription is active'
                  : '📚 Start your learning journey today'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-slate-400">Signed in as</p>
                <p className="text-white font-medium">{user?.email}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[#00B38F] to-[#000856] flex items-center justify-center text-white font-bold text-lg">
                {(user?.first_name?.[0] || user?.name?.[0] || 'U').toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="p-8">
          <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Subscription Status Card */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-slate-600/50 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-slate-300 font-medium">Subscription</h3>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      user?.subscription_status === 'active' 
                        ? 'bg-[#00B38F]/20' 
                        : 'bg-slate-600/30'
                    }`}>
                      <svg className={`w-5 h-5 ${
                        user?.subscription_status === 'active' 
                          ? 'text-[#00B38F]' 
                          : 'text-slate-400'
                      }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-white mb-2">
                    {user?.subscription_status === 'active' ? 'Active' : 'Inactive'}
                  </p>
                  <p className="text-slate-400 text-sm">
                    {user?.subscription_plan || 'No active plan'}
                  </p>
                </div>

                {/* Enrolled Courses Card */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-slate-600/50 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-slate-300 font-medium">My Courses</h3>
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-white mb-2">
                    {coursesCount}
                  </p>
                  <p className="text-slate-400 text-sm">Enrolled courses</p>
                </div>

                {/* Email Verification Card */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-slate-600/50 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-slate-300 font-medium">Email Status</h3>
                    {user?.is_email_verified ? (
                      <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                        <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-slate-600/30 flex items-center justify-center">
                        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <p className={`text-3xl font-bold mb-2 ${user?.is_email_verified ? 'text-white' : 'text-slate-300'}`}>
                    {user?.is_email_verified ? 'Verified' : 'Pending'}
                  </p>
                  <p className="text-slate-400 text-sm">
                    {user?.is_email_verified ? 'Email confirmed' : 'Verification pending'}
                  </p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                <h3 className="text-xl font-bold text-white mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <button
                    onClick={() => router.push('/my-courses')}
                    className="flex items-center space-x-3 p-4 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-all border border-slate-600/30"
                  >
                    <svg className="w-6 h-6 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span className="text-white font-medium">Browse Courses</span>
                  </button>

                  <button
                    onClick={() => router.push('/pricing')}
                    className="flex items-center space-x-3 p-4 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-all border border-slate-600/30"
                  >
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span className="text-white font-medium">View Plans</span>
                  </button>

                  <button
                    onClick={() => router.push('/profile')}
                    className="flex items-center space-x-3 p-4 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-all border border-slate-600/30"
                  >
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span className="text-white font-medium">Edit Profile</span>
                  </button>

                  <button
                    onClick={() => router.push('/settings')}
                    className="flex items-center space-x-3 p-4 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-all border border-slate-600/30"
                  >
                    <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="text-white font-medium">Settings</span>
                  </button>
                </div>
              </div>

              {/* Getting Started */}
              {(!user?.subscription_status || user?.subscription_status !== 'active') && (
                <div className="bg-gradient-to-r from-[#00B38F]/20 to-[#000856]/20 backdrop-blur-sm border border-[#00B38F]/30 rounded-xl p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-2">🚀 Get Started with OxiWorld</h3>
                      <p className="text-slate-300 mb-4">
                        Subscribe to access premium Forex signals and trading courses.
                      </p>
                      <button
                        onClick={() => router.push('/pricing')}
                        className="px-6 py-3 bg-gradient-to-r from-[#00B38F] to-[#000856] text-white font-medium rounded-xl hover:opacity-90 transition-all"
                      >
                        View Subscription Plans
                      </button>
                    </div>
                    <svg className="w-24 h-24 text-[#00B38F]/30" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                    </svg>
                  </div>
                </div>
              )}
            </div>
        </div>
      </main>
    </div>
  );
}
