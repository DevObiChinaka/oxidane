import { Metadata } from 'next';
import { AuthProvider } from '@/contexts/AuthContext';
import AdminLayoutWrapper from './components/AdminLayoutWrapper';

export const metadata: Metadata = {
  title: 'Admin Dashboard - OxiWorld Forex Academy',
  description: 'Manage courses, subscriptions, and users',
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <AdminLayoutWrapper>
        {children}
      </AdminLayoutWrapper>
    </AuthProvider>
  );
}