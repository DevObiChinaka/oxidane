import { Metadata } from 'next';
import { AdminAuthProvider } from './contexts/AdminAuthContext';
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
    <AdminAuthProvider>
      <AdminLayoutWrapper>
        {children}
      </AdminLayoutWrapper>
    </AdminAuthProvider>
  );
}