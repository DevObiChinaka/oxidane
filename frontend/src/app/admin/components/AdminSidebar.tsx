'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';

export default function AdminSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
    setShowUserMenu(false);
  };

  const navigationItems = [
    {
      section: 'Overview',
      items: [
        { name: 'Dashboard', href: '/admin', icon: '📊' },
        { name: 'Analytics', href: '/admin/analytics', icon: '📈' },
      ]
    },
    {
      section: 'Content Management',
      items: [
        { name: 'Courses', href: '/admin/courses', icon: '📚' },
        { name: 'Lessons', href: '/admin/lessons', icon: '🎥' },
      ]
    },
    {
      section: 'User Management',
      items: [
        { name: 'Users', href: '/admin/users', icon: '👥' },
        { name: 'Signal Subscriptions', href: '/admin/subscriptions', icon: '📡' },
        { name: 'Mentorship Program', href: '/admin/mentorship', icon: '🎓' },
        { name: 'Telegram Queue', href: '/admin/telegram', icon: '💬' },
      ]
    },
    {
      section: 'Financial',
      items: [
        { name: 'Pricing Plans', href: '/admin/pricing', icon: '💰' },
        { name: 'Payments', href: '/admin/payments', icon: '💳' },
        { name: 'Revenue Reports', href: '/admin/revenue', icon: '📊' },
      ]
    },
    {
      section: 'Settings',
      items: [
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
        {navigationItems.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-6">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              {section.section}
            </h3>
            <nav className="space-y-1">
              {section.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                    ${
                      isActive(item.href)
                        ? 'bg-[#00B38F]/10 text-[#00B38F] border-r-2 border-[#00B38F]'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }
                  `}
                >
                  <span className="mr-3 text-base">{item.icon}</span>
                  {item.name}
                  {isActive(item.href) && (
                    <div className="ml-auto w-1.5 h-1.5 bg-[#00B38F] rounded-full"></div>
                  )}
                </Link>
              ))}
            </nav>
          </div>
        ))}
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