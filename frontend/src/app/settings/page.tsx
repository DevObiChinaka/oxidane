'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardSidebar from '../components/DashboardSidebar';

interface UserData {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  is_email_verified: boolean;
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'password' | 'notifications' | 'security'>('password');

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Notification preferences state
  const [notifications, setNotifications] = useState({
    emailLogin: true,
    courseUpdates: true,
    subscriptionRenewal: true,
    promotionalEmails: false,
    signalAlerts: true,
  });
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsSuccess, setNotificationsSuccess] = useState('');

  useEffect(() => {
    fetchUserProfile();
    fetchNotificationPreferences();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        router.push('/auth');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      const data = await response.json();
      setUser(data);
    } catch (error) {
      console.error('Profile fetch failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/auth');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotificationPreferences = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) return;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/get-notifications/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.preferences);
      }
    } catch (error) {
      console.error('Failed to fetch notification preferences:', error);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('All password fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/[0-9]/.test(newPassword)) {
      setPasswordError('Password must contain uppercase, lowercase, and numbers');
      return;
    }

    setPasswordLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/change-password/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to change password');
      }

      setPasswordSuccess('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      
      setTimeout(() => setPasswordSuccess(''), 3000);
    } catch (error: any) {
      setPasswordError(error.message || 'Failed to change password');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleNotificationsUpdate = async () => {
    setNotificationsLoading(true);
    setNotificationsSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/update-notifications/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(notifications),
      });

      if (!response.ok) {
        throw new Error('Failed to update notification preferences');
      }

      setNotificationsSuccess('Notification preferences updated!');
      setTimeout(() => setNotificationsSuccess(''), 3000);
    } catch (error) {
      console.error('Notification update failed:', error);
    } finally {
      setNotificationsLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
          <p className="text-slate-300">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <DashboardSidebar />

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        <header className="bg-slate-800/30 backdrop-blur-sm border-b border-slate-700/50 px-8 py-6">
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <p className="text-slate-400 mt-1">Manage your account preferences and security</p>
        </header>

        <div className="p-8 max-w-4xl">
          {/* Tab Navigation */}
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setActiveTab('password')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'password'
                  ? 'bg-[#00B38F] text-white'
                  : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
              }`}
            >
              Password
            </button>
            <button
              onClick={() => setActiveTab('notifications')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'notifications'
                  ? 'bg-[#00B38F] text-white'
                  : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
              }`}
            >
              Notifications
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'security'
                  ? 'bg-[#00B38F] text-white'
                  : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800'
              }`}
            >
              Security
            </button>
          </div>

          {/* Password Tab */}
          {activeTab === 'password' && (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8">
              <h3 className="text-lg font-bold text-white mb-6">Change Password</h3>

              {passwordError && (
                <div className="mb-6 bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                  <p className="text-red-200">{passwordError}</p>
                </div>
              )}

              {passwordSuccess && (
                <div className="mb-6 bg-green-500/20 border border-green-500/50 rounded-lg p-4">
                  <p className="text-green-200">{passwordSuccess}</p>
                </div>
              )}

              <form onSubmit={handlePasswordChange} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F]"
                    placeholder="Enter current password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F]"
                    placeholder="Enter new password"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Must be at least 8 characters with uppercase, lowercase, and numbers
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00B38F]"
                    placeholder="Confirm new password"
                  />
                </div>

                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {passwordLoading ? 'Changing...' : 'Change Password'}
                </button>
              </form>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8">
              <h3 className="text-lg font-bold text-white mb-6">Email Notifications</h3>

              {notificationsSuccess && (
                <div className="mb-6 bg-green-500/20 border border-green-500/50 rounded-lg p-4">
                  <p className="text-green-200">{notificationsSuccess}</p>
                </div>
              )}

              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Login Notifications</h4>
                    <p className="text-sm text-slate-400">Get notified when someone logs into your account</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.emailLogin}
                      onChange={(e) => setNotifications({ ...notifications, emailLogin: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#00B38F] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00B38F]"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Course Updates</h4>
                    <p className="text-sm text-slate-400">Receive updates about new lessons and course materials</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.courseUpdates}
                      onChange={(e) => setNotifications({ ...notifications, courseUpdates: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#00B38F] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00B38F]"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Subscription Renewal</h4>
                    <p className="text-sm text-slate-400">Get reminders before your subscription renews</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.subscriptionRenewal}
                      onChange={(e) => setNotifications({ ...notifications, subscriptionRenewal: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#00B38F] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00B38F]"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Signal Alerts</h4>
                    <p className="text-sm text-slate-400">Receive trading signal notifications</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.signalAlerts}
                      onChange={(e) => setNotifications({ ...notifications, signalAlerts: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#00B38F] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00B38F]"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">Promotional Emails</h4>
                    <p className="text-sm text-slate-400">Receive promotional offers and marketing emails</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.promotionalEmails}
                      onChange={(e) => setNotifications({ ...notifications, promotionalEmails: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#00B38F] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#00B38F]"></div>
                  </label>
                </div>

                <button
                  onClick={handleNotificationsUpdate}
                  disabled={notificationsLoading}
                  className="px-6 py-3 bg-[#00B38F] hover:bg-[#00A87D] text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {notificationsLoading ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8">
                <h3 className="text-lg font-bold text-white mb-4">Account Security</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-white font-medium">Email Verification</h4>
                      <p className="text-sm text-slate-400">Your email is {user?.is_email_verified ? 'verified' : 'not verified'}</p>
                    </div>
                    <span className={`px-4 py-2 rounded-full text-sm ${
                      user?.is_email_verified
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}>
                      {user?.is_email_verified ? 'Verified' : 'Pending'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-8">
                <h3 className="text-lg font-bold text-white mb-4">Active Sessions</h3>
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="w-10 h-10 rounded-full bg-[#00B38F]/20 flex items-center justify-center mt-1">
                        <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-white font-medium">Current Device</h4>
                        <p className="text-sm text-slate-400">Windows • Chrome</p>
                        <p className="text-xs text-slate-500 mt-1">Active now</p>
                      </div>
                    </div>
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded-full">Active</span>
                  </div>
                </div>
              </div>

              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-8">
                <h3 className="text-lg font-bold text-red-400 mb-2">Danger Zone</h3>
                <p className="text-slate-400 text-sm mb-4">Permanently delete your account and all associated data</p>
                <button className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-all border border-red-500/50">
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
