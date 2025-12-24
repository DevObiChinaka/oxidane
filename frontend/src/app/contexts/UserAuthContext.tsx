'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

// ==================== Types ====================

export interface UserSubscription {
  id: string;
  plan_type: string;
  plan_name: string;
  status: 'active' | 'expired' | 'cancelled';
  subscription_start: string;
  subscription_end: string | null;
  telegram_status: string;
  access_level: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar: string | null;
  is_email_verified: boolean;
  auth_method: 'oauth' | 'credentials';
  oauth_provider?: 'google' | null;
  created_at: string;
  last_login: string | null;
  subscriptions: UserSubscription[];
  has_active_subscription: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface OTPVerification {
  session_token: string;
  otp: string;
}

export interface ProfileUpdateData {
  first_name?: string;
  last_name?: string;
  phone?: string;
  bio?: string;
  location?: string;
}

interface UserAuthContextType {
  // User state
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  
  // Auth methods
  loginWithCredentials: (credentials: LoginCredentials) => Promise<{ requiresOTP: boolean; sessionToken?: string; message?: string }>;
  verifyOTP: (data: OTPVerification) => Promise<void>;
  resendOTP: (sessionToken: string) => Promise<void>;
  logout: () => Promise<void>;
  
  // Profile management
  updateProfile: (data: ProfileUpdateData) => Promise<void>;
  uploadAvatar: (file: File) => Promise<string>;
  refreshUser: () => Promise<void>;
  
  // Error handling
  error: string | null;
  clearError: () => void;
}

// ==================== Context ====================

const UserAuthContext = createContext<UserAuthContextType | undefined>(undefined);

// ==================== API Configuration ====================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Helper Functions ====================

const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('user_auth_token');
};

const setAuthToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user_auth_token', token);
  }
};

const removeAuthToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('user_auth_token');
  }
};

const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || error.message || 'Request failed');
  }
  
  return response.json();
};

// ==================== Provider Component ====================

interface UserAuthProviderProps {
  children: ReactNode;
}

export function UserAuthProvider({ children }: UserAuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // ==================== Fetch User Profile ====================

  const fetchUserProfile = useCallback(async () => {
    const token = getAuthToken();
    
    if (token) {
      try {
        const data = await apiRequest('/auth/profile/');
        setUser(data);
        setLoading(false);
        return;
      } catch (err) {
                removeAuthToken();
      }
    }
    
    // No token - user is not authenticated
    setUser(null);
    setLoading(false);
  }, []);

  // ==================== Initialize Auth State ====================

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  // ==================== Login with Credentials (Step 1: Check credentials, send OTP) ====================

  const loginWithCredentials = async (credentials: LoginCredentials) => {
    setError(null);
    setLoading(true);

    try {

      const response = await fetch(`${API_URL}/api/auth/login-with-otp/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {

        // Handle specific error codes
        if (data.code === 'ACCOUNT_NOT_FOUND') {
          const errorMsg = 'No account found with this email address. Please sign up first.';

          throw new Error(errorMsg);
        } else if (data.code === 'INVALID_PASSWORD') {
          const errorMsg = 'Incorrect password. Please try again.';

          throw new Error(errorMsg);
        } else if (data.code === 'EMAIL_NOT_VERIFIED') {
          const errorMsg = 'Please verify your email before signing in. Check your inbox for the verification code.';

          throw new Error(errorMsg);
        } else if (data.code === 'ACCOUNT_INACTIVE') {
          const errorMsg = 'Your account is inactive. Please contact support.';

          throw new Error(errorMsg);
        }
        throw new Error(data.error || 'Login failed');
      }

      // OTP should be required
      if (data.requires_otp && data.session_token) {

        setLoading(false);
        return {
          requiresOTP: true,
          sessionToken: data.session_token,
          message: data.message || 'OTP sent to your email',
        };
      }

      throw new Error('Invalid response from server');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
            setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  // ==================== Verify OTP (Step 2: Complete login) ====================

  const verifyOTP = async (data: OTPVerification) => {
    setError(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/verify-login-otp/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'OTP verification failed');
      }

      // Store the JWT token
      if (result.token) {
        setAuthToken(result.token);
        await fetchUserProfile();
        setLoading(false);
        router.push('/dashboard');
      } else {
        throw new Error('No token received');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'OTP verification failed';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  // ==================== Resend OTP ====================

  const resendOTP = async (sessionToken: string) => {
    setError(null);

    try {
      await fetch(`${API_URL}/api/auth/resend-login-otp/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_token: sessionToken }),
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resend OTP';
      setError(errorMessage);
      throw err;
    }
  };

  // ==================== Logout ====================

  const logout = async () => {
    setLoading(true);
    
    try {
      // Remove token
      removeAuthToken();
      
      // Clear user state
      setUser(null);
      
      // Redirect to home
      router.push('/');
    } catch (err) {
          } finally {
      setLoading(false);
    }
  };

  // ==================== Update Profile ====================

  const updateProfile = async (data: ProfileUpdateData) => {
    setError(null);

    try {
      const updatedUser = await apiRequest('/auth/profile/', {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      setUser(updatedUser);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
      setError(errorMessage);
      throw err;
    }
  };

  // ==================== Upload Avatar ====================

  const uploadAvatar = async (file: File): Promise<string> => {
    setError(null);

    try {
      const formData = new FormData();
      formData.append('avatar', file);

      const token = getAuthToken();
      const response = await fetch(`${API_URL}/auth/profile/avatar/`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload avatar');
      }

      const data = await response.json();
      
      // Update user with new avatar
      if (user) {
        setUser({ ...user, avatar: data.avatar });
      }

      return data.avatar;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload avatar';
      setError(errorMessage);
      throw err;
    }
  };

  // ==================== Refresh User Data ====================

  const refreshUser = async () => {
    await fetchUserProfile();
  };

  // ==================== Clear Error ====================

  const clearError = () => {
    setError(null);
  };

  // ==================== Context Value ====================

  const value: UserAuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    loginWithCredentials,
    verifyOTP,
    resendOTP,
    logout,
    updateProfile,
    uploadAvatar,
    refreshUser,
    error,
    clearError,
  };

  return (
    <UserAuthContext.Provider value={value}>
      {children}
    </UserAuthContext.Provider>
  );
}

// ==================== Hook ====================

export function useUserAuth() {
  const context = useContext(UserAuthContext);
  if (context === undefined) {
    throw new Error('useUserAuth must be used within a UserAuthProvider');
  }
  return context;
}
