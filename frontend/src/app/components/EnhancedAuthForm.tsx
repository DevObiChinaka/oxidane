'use client';

import React, { useState } from 'react';
import { useUserAuth } from '../contexts/UserAuthContext';
import { signIn } from 'next-auth/react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

interface EnhancedAuthFormProps {
  initialIsLogin?: boolean;
}

export default function EnhancedAuthForm({ initialIsLogin = true }: EnhancedAuthFormProps) {
  // Auth state
  const { loginWithCredentials, verifyOTP, resendOTP, error: authError, clearError } = useUserAuth();

  // Form state
  const [isLogin, setIsLogin] = useState(initialIsLogin);
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  
  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Password validation requirements
  const getPasswordRequirements = (password: string) => {
    return [
      { label: 'At least 8 characters', met: password.length >= 8 },
      { label: 'One uppercase letter', met: /[A-Z]/.test(password) },
      { label: 'One lowercase letter', met: /[a-z]/.test(password) },
      { label: 'One number', met: /\d/.test(password) },
      { label: 'One special character', met: /[!@#$%^&*(),.?":{}|<>]/.test(password) }
    ];
  };

  const isPasswordValid = (password: string) => {
    return getPasswordRequirements(password).every(req => req.met);
  };

  // ==================== Handlers ====================

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    clearError();

    if (!isLogin) {
      // Registration validation
      if (!name.trim()) {
        setError('Name is required');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
      if (!isPasswordValid(password)) {
        setError('Please meet all password requirements');
        return;
      }
    }

    setLoading(true);

    try {
      if (isLogin) {

        // Login flow - sends OTP
        const result = await loginWithCredentials({ email, password });

        if (result.requiresOTP && result.sessionToken) {
          setSessionToken(result.sessionToken);
          setStep('otp');
          setSuccess(result.message || 'Verification code sent to your email');
        }
      } else {
        // Registration flow
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
          // Better error messages for registration
          if (data.error?.toLowerCase().includes('already exists')) {
            setError('An account with this email already exists. Please sign in instead.');
          } else {
            setError(data.error || 'Registration failed');
          }
          return;
        }

        if (data.otp_sent || data.requires_verification) {
          setStep('otp');
          setSuccess('Verification code sent! Check your email.');
        }
      }
    } catch (err) {
      // Enhanced error handling
      console.error('💥 [EnhancedAuthForm] Error caught:', err);
      if (err instanceof Error) {
        console.error('💥 [EnhancedAuthForm] Error message:', err.message);
        setError(err.message);
      } else {
        console.error('💥 [EnhancedAuthForm] Unknown error type');
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    clearError();

    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        // Login OTP verification
        await verifyOTP({ session_token: sessionToken, otp });
        // Redirect handled by context
      } else {
        // Registration OTP verification
        const response = await fetch('/api/auth/verify-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, otp }),
        });

        const data = await response.json();

        if (!response.ok) {
          // Better error messages for OTP verification
          if (data.code === 'SESSION_EXPIRED' || data.error?.toLowerCase().includes('expired')) {
            setError('Verification code expired. Requesting a new code...');
            setTimeout(() => handleResendOTP(), 2000);
          } else if (data.code === 'INVALID_OTP' || data.error?.toLowerCase().includes('invalid')) {
            setError('Invalid verification code. Please check and try again.');
          } else {
            setError(data.error || 'Verification failed');
          }
          return;
        }

        setSuccess('🎉 Account created successfully! Redirecting to login...');
        setTimeout(() => {
          setStep('credentials');
          setIsLogin(true);
          setOtp('');
          setPassword('');
          setConfirmPassword('');
          setName('');
          setError('');
        }, 2000);
      }
    } catch (err) {
      // Enhanced error handling for OTP verification
      if (err instanceof Error) {
        if (err.message.includes('expired')) {
          setError('Verification session expired. Please sign in again.');
          setTimeout(() => {
            setStep('credentials');
            setOtp('');
          }, 3000);
        } else if (err.message.includes('Invalid')) {
          setError('Invalid verification code. Please check and try again.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (isLogin && sessionToken) {
        await resendOTP(sessionToken);
        setSuccess('New code sent to your email');
      } else {
        const response = await fetch('/api/auth/resend-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
        });

        if (!response.ok) {
          throw new Error('Failed to resend code');
        }

        setSuccess('New code sent to your email');
      }
    } catch (err) {
      setError('Failed to resend code');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      await signIn('google', { callbackUrl: '/dashboard' });
    } catch (err) {
      setError('Google sign-in failed');
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setStep('credentials');
    setError('');
    setSuccess('');
    setOtp('');
    setPassword('');
    setConfirmPassword('');
    setName('');
  };

  // ==================== OTP Screen ====================

  if (step === 'otp') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">
              Verify your email
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              We sent a 6-digit code to <strong>{email}</strong>
            </p>
          </div>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow-sm border border-gray-200 sm:rounded-lg sm:px-10">
            {/* Success/Error Messages */}
            {success && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start">
                <svg className="w-5 h-5 text-green-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-green-800">{success}</p>
              </div>
            )}

            {(error || authError) && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
                <svg className="w-5 h-5 text-red-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-800">{error || authError}</p>
              </div>
            )}

            <form onSubmit={handleOTPSubmit} className="space-y-6">
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-900 mb-2">
                  Verification Code
                </label>
                <input
                  id="otp"
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  maxLength={6}
                  placeholder="000000"
                  className="w-full px-4 py-3 text-center text-2xl font-semibold tracking-widest border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                  autoComplete="off"
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full bg-brand-teal text-white py-3 rounded-lg font-medium hover:bg-brand-teal/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify Code'}
              </button>
            </form>

            <div className="mt-6 text-center space-y-4">
              <button
                onClick={handleResendOTP}
                disabled={loading}
                className="text-sm text-brand-teal hover:text-brand-teal/80 font-medium"
              >
                Resend Code
              </button>

              <div>
                <button
                  onClick={() => setStep('credentials')}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  ← Back to {isLogin ? 'login' : 'registration'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ==================== Credentials Screen ====================

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">
            {isLogin ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {isLogin ? 'Sign in to access your dashboard' : 'Start your trading journey today'}
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm border border-gray-200 sm:rounded-lg sm:px-10">
          {/* Success/Error Messages */}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start">
              <svg className="w-5 h-5 text-green-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          {(error || authError) && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm text-red-800">{error || authError}</p>
                  {isLogin && (error || authError)?.includes('No account found') && (
                    <button
                      onClick={switchMode}
                      className="mt-2 text-sm text-brand-teal font-medium hover:text-brand-teal/80"
                    >
                      Create an account →
                    </button>
                  )}
                  {!isLogin && (error || authError)?.includes('already exists') && (
                    <button
                      onClick={switchMode}
                      className="mt-2 text-sm text-brand-teal font-medium hover:text-brand-teal/80"
                    >
                      Sign in instead →
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* OAuth Button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors mb-6"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span className="text-sm font-medium text-gray-900">Continue with Google</span>
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with email</span>
            </div>
          </div>

          {/* Credentials Form */}
          <form onSubmit={handleCredentialsSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-900 mb-1">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={!isLogin}
                  autoComplete="name"
                  placeholder="John Doe"
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                  disabled={loading}
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-900 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="your@email.com"
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                disabled={loading}
              />
              {isLogin && email && !email.includes('@') && (
                <p className="mt-1 text-xs text-gray-500">Enter your registered email address</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-900 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  placeholder={isLogin ? 'Enter your password' : 'Create a strong password'}
                  className="w-full px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {!isLogin && (
              <>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-900 mb-1">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <input
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="w-full px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showConfirmPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Password Requirements */}
                {password && (
                  <div className="text-xs space-y-1 p-3 bg-gray-50 rounded-lg">
                    {getPasswordRequirements(password).map((req, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${req.met ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <span className={req.met ? 'text-green-700' : 'text-gray-600'}>{req.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-teal text-white py-3 rounded-lg font-medium hover:bg-brand-teal/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button
                onClick={switchMode}
                className="text-brand-teal font-medium hover:text-brand-teal/80"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
