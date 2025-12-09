'use client';

import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';

interface DashboardSidebarProps {
  isMobileMenuOpen?: boolean;
  setIsMobileMenuOpen?: (open: boolean) => void;
}

export default function DashboardSidebar({ isMobileMenuOpen = false, setIsMobileMenuOpen }: DashboardSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/auth');
  };

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return pathname === '/dashboard';
    }
    return pathname?.startsWith(path);
  };

  const menuItems = [
    {
      path: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
      label: 'Dashboard',
      description: 'Overview & Stats'
    },
    {
      path: '/my-courses',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      label: 'My Courses',
      description: 'Continue Learning'
    },
    {
      path: '/courses',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
      label: 'Browse Courses',
      description: 'Explore Library'
    },
    {
      path: '/subscriptions',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      label: 'Subscriptions',
      description: 'Manage Plans'
    },
    {
      path: '/billing',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
      label: 'Billing',
      description: 'Payments & Telegram'
    },
    {
      path: '/profile',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      label: 'Profile',
      description: 'Your Account'
    },
    {
      path: '/settings',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      label: 'Settings',
      description: 'Preferences'
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-gray-900/50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen?.(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-72 bg-white border-r border-gray-200 
        flex flex-col overflow-y-auto
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Mobile Close Button */}
        <div className="lg:hidden absolute top-4 right-4 z-10">
          <button
            onClick={() => setIsMobileMenuOpen?.(false)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Logo Section */}
      <div className="p-3 sm:p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
            <Image 
              src="/logo_main.png" 
              alt="OxiWorld Logo" 
              width={64} 
              height={64}
              className="object-contain"
            />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-semibold text-[#000856]">
              OxiWorld
            </h1>
            <p className="text-xs text-gray-500">Forex Academy</p>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-1">
        {menuItems.map((item) => (
          <button
            key={item.path}
            onClick={() => {
              router.push(item.path);
              setIsMobileMenuOpen?.(false); // Close menu on navigation
            }}
            className={`w-full group relative rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-gray-100 text-gray-900'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center space-x-2 sm:space-x-3 px-3 sm:px-4 py-2.5 sm:py-3">
              <div className={`flex-shrink-0 ${isActive(item.path) ? 'text-gray-900' : 'text-gray-400'}`}>
                {item.icon}
              </div>
              <div className="flex-1 text-left min-w-0">
                <div className={`text-xs sm:text-sm font-medium truncate ${isActive(item.path) ? 'text-gray-900' : 'text-gray-900'}`}>
                  {item.label}
                </div>
                <div className={`text-xs ${isActive(item.path) ? 'text-gray-600' : 'text-gray-500'} truncate`}>
                  {item.description}
                </div>
              </div>
              {isActive(item.path) && (
                <div className="w-1 h-6 sm:h-8 bg-[#00B38F] rounded-full flex-shrink-0" />
              )}
            </div>
          </button>
        ))}
      </nav>

      {/* User Info & Logout */}
      <div className="p-3 sm:p-4 border-t border-gray-200 space-y-2 sm:space-y-3">
        {/* Quick Stats */}
        <div className="bg-gray-50 rounded-lg p-3 sm:p-4 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-700">Learning Streak</span>
            <span className="text-base font-semibold text-gray-900">7 days</span>
          </div>
          <div className="flex items-center text-xs text-gray-600">
            <svg className="w-3.5 h-3.5 mr-1 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Keep it going!
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center space-x-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-gray-700 hover:bg-gray-100 border border-gray-200 hover:border-gray-300 transition-colors font-medium text-xs sm:text-sm"
        >
          <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span>Logout</span>
        </button>
      </div>
    </aside>
    </>
  );
}
