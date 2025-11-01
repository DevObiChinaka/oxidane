'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUserAuth } from '../contexts/UserAuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireSubscription?: boolean;
  redirectTo?: string;
}

/**
 * Protected Route Component
 * Ensures user is authenticated before accessing certain routes
 * Optionally checks for active subscription
 */
export default function ProtectedRoute({ 
  children, 
  requireSubscription = false,
  redirectTo = '/auth'
}: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useUserAuth();
  const router = useRouter();

  useEffect(() => {
    // Wait for auth state to initialize
    if (loading) return;

    // Redirect if not authenticated
    if (!isAuthenticated) {
      router.push(redirectTo);
      return;
    }

    // Check subscription requirement
    if (requireSubscription && user && !user.has_active_subscription) {
      router.push('/pricing');
      return;
    }
  }, [isAuthenticated, loading, requireSubscription, user, router, redirectTo]);

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-brand-teal"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render children until authenticated
  if (!isAuthenticated) {
    return null;
  }

  // Check subscription requirement
  if (requireSubscription && user && !user.has_active_subscription) {
    return null;
  }

  // Render children if authenticated (and subscribed if required)
  return <>{children}</>;
}
