'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import AdminSidebar from './AdminSidebar';

interface AdminLayoutWrapperProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutWrapperProps) {
  const { user, isAdmin } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [setupChecked, setSetupChecked] = useState(false);
  
  // Don't protect login and password reset pages
  const publicPages = ['/admin/login', '/admin/forgot-password'];
  const isPublicPage = publicPages.includes(pathname);
  
  // Don't redirect if already on setup page
  const isSetupPage = pathname.startsWith('/admin/setup');

  useEffect(() => {
    // Don't check setup status - users can navigate to setup page anytime
    // Setup redirect only happens on first login (handled in AuthContext)
    setSetupChecked(true);
  }, []);
  
  // Render public pages without protection or layout
  if (isPublicPage) {
    return <>{children}</>;
  }
  
  // Protect all other admin routes
  return (
    <ProtectedRoute requireAdmin>
      <div className="flex h-screen bg-gray-50">
        {/* Don't show sidebar on setup page */}
        {!isSetupPage && <AdminSidebar />}
        <main className={`flex-1 overflow-y-auto ${isSetupPage ? '' : ''}`}>
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}