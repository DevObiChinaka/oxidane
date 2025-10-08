'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { EyeIcon, EyeSlashIcon, UserIcon, LockClosedIcon, EnvelopeIcon } from '../components/Icons';
import { useAdminAuth } from '../contexts/AdminAuthContext';

interface LoginStep1Props {
  onLoginSuccess: (sessionToken: string, message: string) => void;
  onError: (error: string) => void;
}

interface LoginStep2Props {
  sessionToken: string;
  onOTPSuccess: (adminToken: string, userData: any) => void;
  onError: (error: string) => void;
  onBack: () => void;
}

import { API_BASE_URL } from '../config/api';

console.log('🔍 [IMPORT DEBUG] API_BASE_URL imported as:', API_BASE_URL);
console.log('🔍 [IMPORT DEBUG] process.env.NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);

function AdminLoginStep1({ onLoginSuccess, onError }: LoginStep1Props) {
  const [credential, setCredential] = useState(''); // email or username
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{credential?: string; password?: string}>({});

  const validateForm = () => {
    const errors: {credential?: string; password?: string} = {};
    
    if (!credential.trim()) {
      errors.credential = 'Email or username is required';
    } else if (credential.includes('@') && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(credential)) {
      errors.credential = 'Please enter a valid email address';
    }
    
    if (!password.trim()) {
      errors.password = 'Password is required';
    } else if (password.length < 3) {
      errors.password = 'Password is too short';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setFieldErrors({});
    
    try {
      // TEMPORARY FIX: Hardcode correct URL until we fix the import issue
      const correctURL = 'http://127.0.0.1:8000/api/admin-auth/login/';
      const importedURL = `${API_BASE_URL}/admin-auth/login/`;
      
      console.log('🚀 === LOGIN DEBUG START ===');
      console.log('🚀 API_BASE_URL imported as:', API_BASE_URL);
      console.log('🚀 Imported URL would be:', importedURL);
      console.log('🚀 Correct URL should be:', correctURL);
      console.log('🚀 Using correct URL for request');
      console.log('🚀 === LOGIN DEBUG END ===');
      
      const loginUrl = correctURL;
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: credential.trim(),
          password: password,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        onLoginSuccess(data.session_token, data.message);
      } else {
        // Handle specific error cases
        if (response.status === 401) {
          onError('Invalid email/username or password. Please check your credentials.');
        } else if (response.status === 403) {
          onError('Access denied. Admin privileges required.');
        } else if (response.status === 400) {
          onError(data.error || 'Please check your input and try again.');
        } else {
          onError(data.error || 'Login failed. Please try again.');
        }
      }
    } catch (error) {
      onError('Unable to connect to server. Please check your internet connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-[#00B38F] to-[#00A87D] rounded-full flex items-center justify-center shadow-lg">
            <LockClosedIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Admin Login
          </h2>
          <p className="mt-2 text-gray-600 font-medium">
            OxiWorld Forex Academy Dashboard
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Enter your credentials to access the admin panel
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-5">
            <div>
              <label htmlFor="credential" className="block text-sm font-semibold text-gray-700 mb-2">
                Email or Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  {credential.includes('@') ? (
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <UserIcon className="h-5 w-5 text-gray-400" />
                  )}
                </div>
                <input
                  id="credential"
                  type="text"
                  value={credential}
                  onChange={(e) => {
                    setCredential(e.target.value);
                    if (fieldErrors.credential) setFieldErrors(prev => ({...prev, credential: undefined}));
                  }}
                  className={`block w-full pl-10 pr-4 py-3 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 ${
                    fieldErrors.credential 
                      ? 'border-red-300 focus:ring-red-500 bg-red-50' 
                      : 'border-gray-300 hover:border-gray-400 bg-white focus:bg-white'
                  } ${loading ? 'bg-gray-50' : 'bg-white focus:bg-white'}`}
                  placeholder="Enter your email or username"
                  disabled={loading}
                  autoComplete="username"
                />
              </div>
              {fieldErrors.credential && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <span className="inline-block w-1 h-1 bg-red-600 rounded-full mr-2"></span>
                  {fieldErrors.credential}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (fieldErrors.password) setFieldErrors(prev => ({...prev, password: undefined}));
                  }}
                  className={`block w-full pl-10 pr-12 py-3 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 ${
                    fieldErrors.password 
                      ? 'border-red-300 focus:ring-red-500 bg-red-50' 
                      : 'border-gray-300 hover:border-gray-400 bg-white focus:bg-white'
                  } ${loading ? 'bg-gray-50' : 'bg-white focus:bg-white'}`}
                  placeholder="Enter your password"
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                  disabled={loading}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <span className="inline-block w-1 h-1 bg-red-600 rounded-full mr-2"></span>
                  {fieldErrors.password}
                </p>
              )}
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || !credential.trim() || !password.trim()}
              className="w-full flex justify-center items-center py-4 px-6 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00A87D] hover:to-[#009270] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                  Verifying credentials...
                </div>
              ) : (
                <div className="flex items-center">
                  <LockClosedIcon className="h-5 w-5 mr-2" />
                  Send Login Code
                </div>
              )}
            </button>
          </div>
        </form>

        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Secure access with email verification required</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminLoginStep2({ sessionToken, onOTPSuccess, onError, onBack }: LoginStep2Props) {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!otp.trim() || otp.length !== 6) {
      onError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/admin-auth/verify-otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_token: sessionToken,
          otp: otp.trim(),
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Pass both token and user data to the parent component
        // Don't store in localStorage here - let the auth context handle it
        onOTPSuccess(data.admin_token, data.user);
      } else {
        onError(data.error || 'OTP verification failed');
      }
    } catch (error) {
      onError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setOtp(value);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
            <EnvelopeIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Check Your Email
          </h2>
          <p className="mt-2 text-gray-600 leading-relaxed">
            We've sent a 6-digit verification code to your registered email address
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Please check your inbox and enter the code below
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="otp" className="block text-sm font-semibold text-gray-700 text-center mb-3">
                Enter Verification Code
              </label>
              <div className="relative">
                <input
                  id="otp"
                  type="text"
                  value={otp}
                  onChange={handleOtpChange}
                  className="block w-full px-6 py-4 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-3xl font-mono tracking-widest bg-white focus:bg-white transition-all duration-200 text-gray-900"
                  placeholder="• • • • • •"
                  maxLength={6}
                  disabled={loading}
                  autoComplete="one-time-code"
                />
              </div>
              <div className="flex items-center justify-center mt-3 text-xs text-gray-500">
                <div className="flex items-center space-x-2">
                  <div className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></div>
                  <span>Code expires in 10 minutes</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full flex justify-center items-center py-4 px-6 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                  Verifying...
                </div>
              ) : (
                <div className="flex items-center">
                  <LockClosedIcon className="h-5 w-5 mr-2" />
                  Verify & Access Dashboard
                </div>
              )}
            </button>

            <button
              type="button"
              onClick={onBack}
              disabled={loading}
              className="w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-xl shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 transition-all duration-200"
            >
              <UserIcon className="h-4 w-4 mr-2" />
              Back to Login
            </button>
          </div>
        </form>

        <div className="text-center">
          <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
            <EnvelopeIcon className="h-3 w-3" />
            <span>Didn't receive the code? Check your spam folder</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminLogin() {
  const [step, setStep] = useState<1 | 2>(1);
  const [sessionToken, setSessionToken] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const router = useRouter();
  const { login } = useAdminAuth();

  const handleLoginSuccess = (token: string, message: string) => {
    setSessionToken(token);
    setSuccessMessage(message);
    setError('');
    setStep(2);
  };

  const handleOTPSuccess = (adminToken: string, userData: any) => {
    // Properly login through the auth context
    login(adminToken, userData);
    // Redirect to admin dashboard
    router.push('/admin/dashboard');
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setSuccessMessage('');
  };

  const handleBack = () => {
    setStep(1);
    setSessionToken('');
    setError('');
    setSuccessMessage('');
  };

  // Auto-hide alerts after 5 seconds
  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  React.useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  return (
    <div>
      {error && (
        <div className="fixed top-4 right-4 max-w-md bg-red-50 border-l-4 border-red-400 text-red-800 px-4 py-3 rounded-lg shadow-lg z-50">
          <div className="flex items-start">
            <span className="mr-2 mt-0.5">❌</span>
            <div className="flex-1">
              <p className="font-medium">Login Error</p>
              <p className="text-sm">{error}</p>
            </div>
            <button 
              onClick={() => setError('')}
              className="ml-2 text-red-600 hover:text-red-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="fixed top-4 right-4 max-w-md bg-green-50 border-l-4 border-green-400 text-green-800 px-4 py-3 rounded-lg shadow-lg z-50">
          <div className="flex items-start">
            <span className="mr-2 mt-0.5">✅</span>
            <div className="flex-1">
              <p className="font-medium">Success</p>
              <p className="text-sm">{successMessage}</p>
            </div>
            <button 
              onClick={() => setSuccessMessage('')}
              className="ml-2 text-green-600 hover:text-green-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {step === 1 ? (
        <AdminLoginStep1
          onLoginSuccess={handleLoginSuccess}
          onError={handleError}
        />
      ) : (
        <AdminLoginStep2
          sessionToken={sessionToken}
          onOTPSuccess={handleOTPSuccess}
          onError={handleError}
          onBack={handleBack}
        />
      )}
    </div>
  );
}