'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';

interface SetupStatus {
  setup_complete: boolean;
  completion_percentage: number;
}

export default function AdminSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);

  useEffect(() => {
    fetchSetupStatus();
  }, []);

  const fetchSetupStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://127.0.0.1:8000/api/admin/setup/status/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSetupStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch setup status:', error);
    }
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
    setShowUserMenu(false);
  };

  const navigationItems = [
    {
      section: 'Overview',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Dashboard', href: '/admin', icon: '📊' },
        { name: 'Analytics', href: '/admin/analytics', icon: '📈' },
      ]
    },
    {
      section: 'Content Management',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Courses', href: '/admin/courses', icon: '📚' },
        { name: 'Lessons', href: '/admin/lessons', icon: '🎥' },
      ]
    },
    {
      section: 'User Management',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Users', href: '/admin/users', icon: '👥' },
        { name: 'Signal Subscriptions', href: '/admin/subscriptions', icon: '📡' },
        { name: 'Mentorship Program', href: '/admin/mentorship', icon: '🎓' },
        { name: 'Telegram Queue', href: '/admin/telegram', icon: '💬' },
      ]
    },
    {
      section: 'Financial',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Subscription Plans', href: '/admin/plans', icon: '💰' },
        { name: 'Features', href: '/admin/features', icon: '✨' },
        { name: 'Coupons', href: '/admin/coupons', icon: '🎟️' },
        { name: 'Referral Codes', href: '/admin/referrals', icon: '🔗' },
        { name: 'Payments', href: '/admin/payments', icon: '💳' },
        { name: 'Revenue Reports', href: '/admin/revenue', icon: '📊' },
      ]
    },
    {
      section: 'Settings',
      requiresSetup: false, // Always accessible
      items: [
        { name: 'Platform Setup', href: '/admin/setup', icon: '⚙️' },
        { name: 'Payment Gateway', href: '/admin/settings/payment', icon: '💳' },
        { name: 'Email Configuration', href: '/admin/settings/email', icon: '📧' },
        { name: 'Telegram Integration', href: '/admin/settings/telegram', icon: '💬' },
        { name: 'System Health', href: '/admin/settings/system', icon: '🔧' },
        { name: 'Email Templates', href: '/admin/emails', icon: '✉️' },
      ]
    }
  ];

  const isActive = (href: string) => {
    if (href === '/admin') {
      return pathname === '/admin';
    }
    return pathname.startsWith(href);
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto flex-shrink-0 flex flex-col">
      {/* Branding Header */}
      <div className="px-4 py-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
            <Image 
              src="/logo_main.png" 
              alt="OxiWorld Logo" 
              width={48} 
              height={48}
              className="object-contain"
            />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-[#000856]">OxiWorld Admin</h1>
            <p className="text-xs text-gray-500">Forex Academy Management</p>
          </div>
        </div>
      </div>
      <div className="p-4 flex-1">
        {/* Setup Status Banner */}
        {setupStatus && !setupStatus.setup_complete && (
          <div className="mb-6 bg-blue-50 border border-blue-200 p-4 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-blue-900 mb-1">Platform Setup</p>
                <p className="text-xs text-blue-700 mb-2">
                  {setupStatus.completion_percentage}% complete · Configure all settings to unlock features
                </p>
                <div className="w-full bg-blue-100 rounded-full h-1.5">
                  <div 
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${setupStatus.completion_percentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {navigationItems.map((section, sectionIndex) => {
          const isBlocked = section.requiresSetup && setupStatus && !setupStatus.setup_complete;
          
          return (
            <div key={sectionIndex} className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-xs font-semibold uppercase tracking-wider ${
                  isBlocked ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {section.section}
                </h3>
                {isBlocked && (
                  <div className="flex items-center gap-1">
                    <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
              <nav className="space-y-1">
                {section.items.map((item) => {
                  const itemActive = isActive(item.href);
                  const itemDisabled = isBlocked;

                  return itemDisabled ? (
                    <div
                      key={item.href}
                      className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-gray-400 cursor-not-allowed bg-gray-50/50 border border-gray-100"
                      title="Complete platform setup to access this feature"
                    >
                      <span className="mr-3 text-base opacity-40">{item.icon}</span>
                      <span className="flex-1">{item.name}</span>
                      <svg className="w-3.5 h-3.5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  ) : (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`
                        flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                        ${
                          itemActive
                            ? 'bg-[#00B38F]/10 text-[#00B38F] border-r-2 border-[#00B38F]'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }
                      `}
                    >
                      <span className="mr-3 text-base">{item.icon}</span>
                      {item.name}
                      {itemActive && (
                        <div className="ml-auto w-1.5 h-1.5 bg-[#00B38F] rounded-full"></div>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>
          );
        })}
      </div>
      
      {/* User Profile & System Status */}
      <div className="mt-auto border-t border-gray-200">
        {/* User Profile */}
        <div className="p-4">
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="w-full flex items-center space-x-3 hover:bg-gray-50 p-2 rounded-lg transition-colors"
            >
              <div className="w-8 h-8 bg-[#00B38F] rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {(user?.first_name || user?.username || 'A').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name || user?.username || 'Admin'}
                </p>
                <p className="text-xs text-gray-500">Super Admin</p>
              </div>
            </button>
            
            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  👤 Profile Settings
                </button>
                
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  🔒 Change Password
                </button>
                
                <hr className="my-1" />
                
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  🚪 Logout
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* System Status */}
        <div className="p-4 bg-gray-50">
          <div className="text-xs text-gray-500">
            <div className="flex justify-between items-center mb-1">
              <span>System Status</span>
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
            </div>
            <div className="text-gray-400">All systems operational</div>
          </div>
        </div>
      </div>
      
      {/* Click outside to close dropdown */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </div>
  );
}