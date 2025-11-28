'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { API_ENDPOINTS } from '@/config/api';

interface AdminUser {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

interface AdminAuthContextType {
  isAuthenticated: boolean;
  user: AdminUser | null;
  login: (token: string, user: AdminUser) => void;
  logout: () => void;
  loading: boolean;
  authInitialized: boolean;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export { AdminAuthContext };

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}

interface AdminAuthProviderProps {
  children: ReactNode;
}

export function AdminAuthProvider({ children }: AdminAuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authInitialized, setAuthInitialized] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Check if current path requires authentication
  const requiresAuth = pathname?.startsWith('/admin') && pathname !== '/admin/login';

  const checkAuthStatus = async (token: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.admin.setupStatus, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const responseText = await response.text();

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Failed to parse auth response as JSON');
        return false;
      }

      if (data.authenticated) {
        setIsAuthenticated(true);
        setUser(data.user);
        return true;
      } else {
        // Session expired or invalid
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        setIsAuthenticated(false);
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error('Auth check failed:', error instanceof Error ? error.message : error);
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }
  };

  const login = (token: string, userData: AdminUser) => {
    localStorage.setItem('admin_token', token);
    localStorage.setItem('admin_user', JSON.stringify(userData));
    
    setIsAuthenticated(true);
    setUser(userData);
    setAuthInitialized(true);
  };

  const logout = async () => {
    const token = localStorage.getItem('admin_token');
    
    if (token) {
      try {
        await fetch(API_ENDPOINTS.auth.logout, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout request failed:', error);
      }
    }

    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    setIsAuthenticated(false);
    setUser(null);
    setAuthInitialized(true); // Keep initialized state to prevent redirect loops
    router.push('/admin/login');
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('admin_token');
      const storedUser = localStorage.getItem('admin_user');

      if (token && storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          
          // Trust the stored session - skip server validation to prevent redirect loop
          setIsAuthenticated(true);
          setUser(userData);
          
        } catch (e) {
          console.error('Failed to parse stored user data:', e);
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          setIsAuthenticated(false);
          setUser(null);
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }

      setLoading(false);
      setAuthInitialized(true);
    };

    // Prevent rapid re-initialization
    const timeoutId = setTimeout(initAuth, 100);
    return () => clearTimeout(timeoutId);
  }, [pathname, router, requiresAuth]);

  // Redirect logic with loop prevention - only after auth is initialized
  useEffect(() => {
    if (!loading && authInitialized && pathname) {
      // Prevent redirect loops by checking if we're already redirecting
      const isRedirecting = sessionStorage.getItem('admin_redirecting');
      
      if (isRedirecting) {
        return;
      }
      
      if (pathname === '/admin' || pathname === '/admin/') {
        if (isAuthenticated) {
          sessionStorage.setItem('admin_redirecting', 'true');
          router.push('/admin/dashboard');
          setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
        } else {
          sessionStorage.setItem('admin_redirecting', 'true');
          router.push('/admin/login');
          setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
        }
      } else if (pathname === '/admin/login' && isAuthenticated) {
        sessionStorage.setItem('admin_redirecting', 'true');
        router.push('/admin/dashboard');
        setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
      } else if (requiresAuth && !isAuthenticated && pathname !== '/admin/login') {
        sessionStorage.setItem('admin_redirecting', 'true');
        router.push('/admin/login');
        setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
      }
    }
  }, [isAuthenticated, loading, authInitialized, pathname, router, requiresAuth]);

  const value: AdminAuthContextType = {
    isAuthenticated,
    user,
    login,
    logout,
    loading,
    authInitialized
  };

  return (
    <AdminAuthContext.Provider value={value}>
      {children}
    </AdminAuthContext.Provider>
  );
}

// Higher-order component to protect admin routes
export function withAdminAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function AdminProtectedComponent(props: P) {
    const { isAuthenticated, loading } = useAdminAuth();
    const router = useRouter();

    useEffect(() => {
      if (!loading && !isAuthenticated) {
        router.push('/admin/login');
      }
    }, [isAuthenticated, loading, router]);

    if (loading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#00B38F]"></div>
            <span>Checking authentication...</span>
          </div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-600 text-xl mb-2">🔒</div>
            <p>Redirecting to login...</p>
          </div>
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };
}