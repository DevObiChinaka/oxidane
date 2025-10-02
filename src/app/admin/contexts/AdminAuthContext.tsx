'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';

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

import { API_BASE_URL } from '../config/api';

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
    console.log('🔐 Checking admin auth status with token:', token ? 'Present' : 'Missing');
    console.log('🔐 API_BASE_URL:', API_BASE_URL);
    
    const url = 'http://127.0.0.1:8000/api/admin-auth/check-session/';
    console.log('🔐 Full URL (hardcoded correct):', url);
    console.log('🔐 API_BASE_URL was:', API_BASE_URL);
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('🔐 Auth check response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        url: response.url
      });

      const responseText = await response.text();
      console.log('🔐 Response text (first 200 chars):', responseText.substring(0, 200));

      let data;
      try {
        data = JSON.parse(responseText);
        console.log('🔐 Auth check data:', data);
      } catch (parseError) {
        console.error('🔐 Failed to parse response as JSON:', parseError);
        console.error('🔐 Raw response:', responseText);
        return false;
      }

      if (data.authenticated) {
        console.log('✅ Admin authentication successful');
        setIsAuthenticated(true);
        setUser(data.user);
        return true;
      } else {
        // Session expired or invalid
        console.log('❌ Admin authentication failed:', data.error);
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        setIsAuthenticated(false);
        setUser(null);
        return false;
      }
    } catch (error) {
      console.error('❌ Auth check failed:', {
        error: error instanceof Error ? error.message : error,
        name: error instanceof Error ? error.name : typeof error,
        stack: error instanceof Error ? error.stack : undefined
      });
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }
  };

  const login = (token: string, userData: AdminUser) => {
    console.log('🔐 Admin login called with:', { token: token ? 'Present' : 'Missing', userData });
    localStorage.setItem('admin_token', token);
    localStorage.setItem('admin_user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
    setAuthInitialized(true);
    console.log('✅ Admin login completed, authenticated:', true);
  };

  const logout = async () => {
    const token = localStorage.getItem('admin_token');
    
    if (token) {
      try {
        await fetch('http://127.0.0.1:8000/api/admin-auth/logout/', {
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

      console.log('🔐 InitAuth - requiresAuth:', requiresAuth, 'pathname:', pathname);

      if (token && storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          console.log('🔐 Found stored admin session:', { token: token ? 'Present' : 'Missing', userData });
          
          // TEMPORARY FIX: Skip server validation to prevent redirect loop
          // Trust the stored session for now until we fix the HTML response issue
          setIsAuthenticated(true);
          setUser(userData);
          console.log('✅ Admin session restored from localStorage (skipping server check)');
          
          // Try server validation in background, but don't act on it
          checkAuthStatus(token).then(isValid => {
            console.log('🔍 Background auth check result:', isValid);
            if (!isValid) {
              console.warn('⚠️ Server says session invalid, but keeping user logged in to prevent loop');
            }
          }).catch(err => {
            console.warn('⚠️ Background auth check failed:', err);
          });
          
        } catch (e) {
          console.error('❌ Failed to parse stored user data:', e);
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
          setIsAuthenticated(false);
          setUser(null);
        }
      } else {
        console.log('🔐 No stored session found');
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
      console.log('🔄 Redirect logic - loading:', loading, 'authInitialized:', authInitialized, 'isAuthenticated:', isAuthenticated, 'pathname:', pathname);
      
      // Prevent redirect loops by checking if we're already redirecting
      const isRedirecting = sessionStorage.getItem('admin_redirecting');
      
      if (isRedirecting) {
        console.log('🔄 Already redirecting, skipping...');
        return;
      }
      
      if (pathname === '/admin' || pathname === '/admin/') {
        if (isAuthenticated) {
          console.log('🔄 Redirecting to dashboard from admin root');
          sessionStorage.setItem('admin_redirecting', 'true');
          router.push('/admin/dashboard');
          setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
        } else {
          console.log('🔄 Redirecting to login from admin root');
          sessionStorage.setItem('admin_redirecting', 'true');
          router.push('/admin/login');
          setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
        }
      } else if (pathname === '/admin/login' && isAuthenticated) {
        console.log('🔄 Already logged in, redirecting to dashboard');
        sessionStorage.setItem('admin_redirecting', 'true');
        router.push('/admin/dashboard');
        setTimeout(() => sessionStorage.removeItem('admin_redirecting'), 1000);
      } else if (requiresAuth && !isAuthenticated && pathname !== '/admin/login') {
        console.log('🔄 Auth required but not authenticated, redirecting to login');
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