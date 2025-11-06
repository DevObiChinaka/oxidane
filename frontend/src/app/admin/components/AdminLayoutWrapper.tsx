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
  if (publicPages.includes(pathname)) {
    return <>{children}</>;
  }

  // Don't redirect if already on setup page
  const isSetupPage = pathname.startsWith('/admin/setup');

  useEffect(() => {
    // Only check setup status once, and not on setup pages
    if (isSetupPage || setupChecked) return;

    const checkSetupStatus = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('http://127.0.0.1:8000/api/admin/setup/status/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          
          // Redirect to setup if not complete (strict mode)
          if (!data.setup_complete) {
            router.push('/admin/setup');
          }
        }
      } catch (error) {
        console.error('Setup status check failed:', error);
        // Don't block access if check fails
      } finally {
        setSetupChecked(true);
      }
    };

    checkSetupStatus();
  }, [isSetupPage, setupChecked, router]);
  
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