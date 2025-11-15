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

// Icon Component
const Icon: React.FC<{ name: string; className?: string }> = ({ name, className = "w-5 h-5" }) => {
  const icons: Record<string, string> = {
    // Overview
    'dashboard': 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
    'analytics': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    
    // Content
    'courses': 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    'lessons': 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z',
    
    // Users
    'users': 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
    'subscriptions': 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    'mentorship': 'M12 14l9-5-9-5-9 5 9 5z M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222',
    'telegram': 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    
    // Financial
    'plans': 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
    'features': 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z',
    'coupons': 'M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z',
    'payments': 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z',
    'revenue': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    
    // Settings
    'setup': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    'email': 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
    'system': 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z',
    
    // User menu
    'profile': 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    'lock': 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
    'logout': 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
  };

  const pathData = icons[name] || icons['dashboard'];
  
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={pathData} />
    </svg>
  );
};

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
        { name: 'Dashboard', href: '/admin', icon: 'dashboard' },
        { name: 'Analytics', href: '/admin/analytics', icon: 'analytics' },
      ]
    },
    {
      section: 'Content Management',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Courses', href: '/admin/courses', icon: 'courses' },
        { name: 'Lessons', href: '/admin/lessons', icon: 'lessons' },
      ]
    },
    {
      section: 'User Management',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Users', href: '/admin/users', icon: 'users' },
        { name: 'Subscriptions', href: '/admin/subscriptions-management', icon: 'subscriptions' },
      ]
    },
    {
      section: 'Financial',
      requiresSetup: false, // TEMP: Disabled for development
      items: [
        { name: 'Subscription Plans', href: '/admin/plans', icon: 'plans' },
        { name: 'Features', href: '/admin/features', icon: 'features' },
        { name: 'Coupons', href: '/admin/coupons', icon: 'coupons' },
        { name: 'Payments', href: '/admin/payments', icon: 'payments' },
      ]
    },
    {
      section: 'Settings',
      requiresSetup: false, // Always accessible
      items: [
        { name: 'Platform Setup', href: '/admin/setup', icon: 'setup' },
        { name: 'Payment Gateway', href: '/admin/settings/payment', icon: 'payments' },
        { name: 'Email Configuration', href: '/admin/settings/email', icon: 'email' },
        { name: 'Telegram Integration', href: '/admin/settings/telegram', icon: 'telegram' },
        { name: 'System Health', href: '/admin/settings/system', icon: 'system' },
        { name: 'Email Templates', href: '/admin/emails', icon: 'email' },
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
                      <Icon name={item.icon} className="mr-3 w-5 h-5 opacity-40" />
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
                      <Icon name={item.icon} className="mr-3 w-5 h-5" />
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
                
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2">
                  <Icon name="profile" className="w-4 h-4" />
                  Profile Settings
                </button>
                
                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2">
                  <Icon name="lock" className="w-4 h-4" />
                  Change Password
                </button>
                
                <hr className="my-1" />
                
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <Icon name="logout" className="w-4 h-4" />
                  Logout
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