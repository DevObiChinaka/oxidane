'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_ENDPOINTS } from '@/config/api';
import { LockClosedIcon, EnvelopeIcon, EyeIcon, EyeSlashIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

export default function AdminLoginPage() {
  const router = useRouter();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  const [message, setMessage] = useState('');

  // Check if already authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    if (token && user) {
      try {
        const userData = JSON.parse(user);
        if (userData.is_staff) {
          router.push('/admin/dashboard');
        }
      } catch (e) {
        console.error('Failed to parse user data:', e);
      }
    }
  }, [router]);

  const handleCredentialsSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      // Step 1: Request OTP
      const response = await fetch(API_ENDPOINTS.adminAuth.loginRequest, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'Login request failed');
      }

      const data = await response.json();
      
      // Store session token for OTP verification
      setSessionToken(data.session_token);
      setMessage(data.message || 'OTP sent to your email. Please check your inbox.');
      
      // Move to OTP step
      setStep('otp');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to send OTP. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      // Step 2: Verify OTP and get JWT tokens
      const response = await fetch(API_ENDPOINTS.adminAuth.verifyOtp, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_token: sessionToken,
          otp: otp 
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || error.error || 'OTP verification failed');
      }

      const data = await response.json();

      // Verify user is admin/staff (should already be validated on backend)
      if (!data.user.is_staff) {
        throw new Error('Access denied. Admin privileges required.');
      }

      // Store tokens and user data
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Check setup status
      try {
        const setupResponse = await fetch(API_ENDPOINTS.admin.setupStatus, {
          headers: {
            'Authorization': `Bearer ${data.access}`,
            'Content-Type': 'application/json'
          }
        });

        if (setupResponse.ok) {
          const setupData = await setupResponse.json();
          
          // If setup is not complete, redirect to setup page
          if (!setupData.setup_complete) {
            router.push('/admin/setup');
            return;
          }
        }
      } catch (error) {
        console.error('Setup status check failed:', error);
        // Continue to dashboard if check fails
      }
      
      // Redirect to admin dashboard
      router.push('/admin/dashboard');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('OTP verification failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackToCredentials = () => {
    setStep('credentials');
    setOtp('');
    setSessionToken('');
    setError('');
    setMessage('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-[#00B38F] to-[#00A87D] rounded-full flex items-center justify-center shadow-lg">
            {step === 'credentials' ? (
              <LockClosedIcon className="h-8 w-8 text-white" />
            ) : (
              <ShieldCheckIcon className="h-8 w-8 text-white" />
            )}
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            {step === 'credentials' ? 'Admin Login' : 'Verify OTP'}
          </h2>
          <p className="mt-2 text-gray-600 font-medium">
            OxiWorld Forex Academy Dashboard
          </p>
          <p className="mt-1 text-sm text-gray-500">
            {step === 'credentials' 
              ? 'Enter your credentials to access the admin panel'
              : 'Enter the 6-digit code sent to your email'}
          </p>
        </div>

        {step === 'credentials' ? (
          <form onSubmit={handleCredentialsSubmit} className="mt-8 space-y-6">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value.trim())}
                    className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 bg-white"
                    placeholder="admin@example.com"
                    disabled={loading}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
                    Password
                  </label>
                  <Link 
                    href="/admin/forgot-password"
                    className="text-sm font-medium text-[#00B38F] hover:text-[#00A87D] transition-colors"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 bg-white"
                    placeholder="Enter your password"
                    disabled={loading}
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    disabled={loading}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00A87D] hover:to-[#009970] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending OTP...
                </div>
              ) : (
                'Send OTP'
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleOtpSubmit} className="mt-8 space-y-6">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
            {message && (
              <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                <p className="text-sm text-green-800">{message}</p>
              </div>
            )}

            <div className="space-y-5">
              <div>
                <label htmlFor="otp" className="block text-sm font-semibold text-gray-700 mb-2">
                  One-Time Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="otp"
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 bg-white text-center text-2xl tracking-widest font-mono"
                    placeholder="000000"
                    disabled={loading}
                    required
                    maxLength={6}
                    pattern="\d{6}"
                    autoComplete="one-time-code"
                    autoFocus
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500 text-center">
                  Code expires in 10 minutes
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-gradient-to-r from-[#00B38F] to-[#00A87D] hover:from-[#00A87D] hover:to-[#009970] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {loading ? (
                  <div className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Verifying...
                  </div>
                ) : (
                  'Verify & Sign In'
                )}
              </button>

              <button
                type="button"
                onClick={handleBackToCredentials}
                disabled={loading}
                className="w-full py-2 px-4 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                ← Back to Login
              </button>
            </div>
          </form>
        )}

        <div className="text-center">
          <p className="text-xs text-gray-500">
            {step === 'credentials' 
              ? 'This is a protected admin area. Only authorized personnel can access this dashboard.'
              : 'Check your email for the verification code. Make sure to check your spam folder.'}
          </p>
        </div>
      </div>
    </div>
  );
}
