'use client';

import { usePathname } from 'next/navigation';
import { useAdminAuth } from '../contexts/AdminAuthContext';
import AdminSidebar from './AdminSidebar';

interface AdminLayoutWrapperProps {
  children: React.ReactNode;
}

export default function AdminLayoutWrapper({ children }: AdminLayoutWrapperProps) {
  const { user } = useAdminAuth();
  const pathname = usePathname();
  
  // Don't show sidebar on login page or if user is not authenticated
  const shouldShowSidebar = user && pathname !== '/admin/login';
  
  if (!shouldShowSidebar) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}