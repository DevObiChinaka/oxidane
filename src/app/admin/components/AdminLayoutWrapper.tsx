'use client';

import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import AdminSidebar from './AdminSidebar';

interface AdminLayoutWrapperProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutWrapperProps) {
  const { user, isAdmin } = useAuth();
  const pathname = usePathname();
  
  // Don't protect login and password reset pages
  const publicPages = ['/admin/login', '/admin/forgot-password'];
  if (publicPages.includes(pathname)) {
    return <>{children}</>;
  }
  
  // Protect all other admin routes
  return (
    <ProtectedRoute requireAdmin>
      <div className="flex h-screen bg-gray-50">
        <AdminSidebar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}