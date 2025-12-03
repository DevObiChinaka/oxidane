'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import AdminSidebar from './AdminSidebar';
import { API_ENDPOINTS } from '@/config/api';

interface AdminLayoutWrapperProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutWrapperProps) {
  const { user, isAdmin } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [setupChecked, setSetupChecked] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Don't protect login and password reset pages
  const publicPages = ['/admin/login', '/admin/forgot-password'];
  const isPublicPage = publicPages.includes(pathname);
  
  // Don't redirect if already on setup page
  const isSetupPage = pathname.startsWith('/admin/setup');
  
  // Allow access to configuration pages even during setup
  // These pages are needed to complete the setup process
  const isConfigPage = pathname.startsWith('/admin/settings') || 
                       pathname.startsWith('/admin/plans') || 
                       pathname.startsWith('/admin/features');

  // Check platform setup status on every page load (except setup page itself)
  useEffect(() => {
    const checkSetupStatus = async () => {
      // Skip check for public pages, setup page, or configuration pages
      if (isPublicPage || isSetupPage || isConfigPage) {
        setSetupChecked(true);
        setSetupComplete(true);
        setCheckingSetup(false);
        return;
      }

      // Skip if user is not authenticated
      const token = localStorage.getItem('access_token');
      if (!token) {
        setSetupChecked(true);
        setCheckingSetup(false);
        return;
      }

      try {
        const response = await fetch(API_ENDPOINTS.admin.setupStatus, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          
          if (!data.setup_complete) {
            // Setup is incomplete - redirect to setup page
            router.push('/admin/setup');
            setSetupComplete(false);
          } else {
            setSetupComplete(true);
          }
        } else {
          // If check fails, allow access (fail open to prevent lockout)
          console.warn('Setup status check failed, allowing access');
          setSetupComplete(true);
        }
      } catch (error) {
        console.error('Setup status check error:', error);
        // Allow access on error to prevent lockout
        setSetupComplete(true);
      } finally {
        setSetupChecked(true);
        setCheckingSetup(false);
      }
    };

    checkSetupStatus();
  }, [pathname, router, isPublicPage, isSetupPage, isConfigPage]);
  
  
  // Render public pages without protection or layout
  if (isPublicPage) {
    return <>{children}</>;
  }

  // Show loading state while checking setup
  if (checkingSetup && !isSetupPage) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-[#00B38F] border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Checking platform setup...</p>
        </div>
      </div>
    );
  }
  
  // Protect all other admin routes
  return (
    <ProtectedRoute requireAdmin>
      <div className="flex h-screen bg-gray-50">
        {/* Don't show sidebar on setup page */}
        {!isSetupPage && (
          <AdminSidebar 
            isMobileMenuOpen={isMobileMenuOpen}
            setIsMobileMenuOpen={setIsMobileMenuOpen}
          />
        )}
        <main className="flex-1 overflow-y-auto">
          {/* Mobile Menu Button - Only visible on mobile */}
          {!isSetupPage && (
            <div className="md:hidden sticky top-0 z-40 bg-white border-b border-gray-200 px-4 py-3">
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                <span className="text-sm font-medium">Menu</span>
              </button>
            </div>
          )}
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}