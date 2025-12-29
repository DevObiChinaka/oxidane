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

// Known user-facing error codes that should be shown as-is
const KNOWN_ERROR_CODES = [
  'ACCOUNT_NOT_FOUND',
  'INVALID_PASSWORD',
  'EMAIL_NOT_VERIFIED',
  'ACCOUNT_INACTIVE',
  'EMAIL_ALREADY_EXISTS',
  'INVALID_OTP',
  'OTP_EXPIRED',
  'SESSION_EXPIRED',
  'INVALID_EMAIL',
  'WEAK_PASSWORD',
];

// Helper to determine if error message should be shown to user
const sanitizeError = (errorData: any, defaultMessage: string): string => {
  // If there's a known error code, use the error message
  if (errorData.code && KNOWN_ERROR_CODES.includes(errorData.code)) {
    return errorData.error || errorData.message || defaultMessage;
  }
  
  // For validation errors, show them
  if (errorData.error && typeof errorData.error === 'string') {
    const lowerError = errorData.error.toLowerCase();
    if (lowerError.includes('email') || 
        lowerError.includes('password') || 
        lowerError.includes('otp') ||
        lowerError.includes('required') ||
        lowerError.includes('invalid') ||
        lowerError.includes('verification')) {
      return errorData.error;
    }
  }
  
  // For all other errors (technical/server errors), show generic message
  return defaultMessage;
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

        // Sanitize error message - show user-friendly errors or generic message
        const errorMsg = sanitizeError(data, 'Something went wrong. Please try again later.');

        throw new Error(errorMsg);
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

      throw new Error('Something went wrong. Please try again later.');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again later.';
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
        const errorMsg = sanitizeError(result, 'Something went wrong. Please try again later.');
        throw new Error(errorMsg);
      }

      // Store the JWT token
      if (result.token) {
        setAuthToken(result.token);
        await fetchUserProfile();
        setLoading(false);
        router.push('/dashboard');
      } else {
        throw new Error('Something went wrong. Please try again later.');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again later.';
      setError(errorMessage);
      setLoading(false);
      throw err;
    }
  };

  // ==================== Resend OTP ====================

  const resendOTP = async (sessionToken: string) => {
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/resend-login-otp/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_token: sessionToken }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        const errorMsg = sanitizeError(data, 'Something went wrong. Please try again later.');
        throw new Error(errorMsg);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again later.';
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
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again later.';
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
        const data = await response.json().catch(() => ({}));
        const errorMsg = sanitizeError(data, 'Something went wrong. Please try again later.');
        throw new Error(errorMsg);
      }

      const data = await response.json();
      
      // Update user with new avatar
      if (user) {
        setUser({ ...user, avatar: data.avatar });
      }

      return data.avatar;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again later.';
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
