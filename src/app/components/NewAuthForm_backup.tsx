'use client';

import React, { useState } from 'react';
import Image from 'next/image';

interface NewAuthFormProps {
  initialIsLogin?: boolean;
}

export default function NewAuthForm({ initialIsLogin = true }: NewAuthFormProps) {
  const [isLogin, setIsLogin] = useState(initialIsLogin);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const [showOtpVerification, setShowOtpVerification] = useState(false);
  const [otp, setOtp] = useState('');
  const [emailForVerification, setEmailForVerification] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (!isLogin && password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin
        ? { email, password }
        : { email, password, name };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.error === 'Email not verified' && !isLogin) {
          setEmailForVerification(email);
          setShowOtpVerification(true);
          setSuccess('Please verify your email to complete registration');
        } else {
          setError(data.error || 'Authentication failed');
        }
        setLoading(false);
        return;
      }

      if (isLogin) {
        setSuccess('Login successful! Redirecting...');
        // Handle successful login (redirect, store token, etc.)
        window.location.href = '/dashboard';
      } else {
        setEmailVerificationSent(true);
        setSuccess('Registration successful! Please check your email to verify your account.');
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  const handleGoogleSignIn = async () => {
    try {
      window.location.href = '/api/auth/google';
    } catch (error) {
      setError('Google sign-in failed. Please try again.');
    }
  };

  const handleResendOtp = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailForVerification }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'Failed to resend verification code');
      } else {
        setSuccess('Verification code resent to your email');
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'Failed to send reset email');
        setLoading(false);
        return;
      }

      setSuccess('Password reset link sent to your email');
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  const handleOtpVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailForVerification, otp }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'OTP verification failed');
        setLoading(false);
        return;
      }

      setSuccess('Email verified successfully! Your account is now active.');
      setTimeout(() => {
        setShowOtpVerification(false);
        setIsLogin(true);
        setEmail(emailForVerification);
        setPassword(''); // Clear password for security
      }, 2000);
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  // OTP Verification Screen
  if (showOtpVerification) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-x-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-32 w-80 h-80 bg-purple-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
          <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-blue-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse animation-delay-2000"></div>
          <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-indigo-600 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse animation-delay-4000"></div>
        </div>

        <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center gradient-brand-glow animate-pulse-glow">
                <Image
                  src="/logo_bright.png"
                  alt="OxiWorld Forex Academy"
                  width={64}
                  height={64}
                  className="rounded-xl"
                  priority
                />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Verify Your Email</h2>
            <p className="text-slate-300">We sent a verification code to</p>
            <p className="text-purple-300 font-medium">{emailForVerification}</p>
          </div>

          <div className="bg-white/10 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-white/20">
            <form className="space-y-6" onSubmit={handleOtpVerification}>
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-white mb-2">
                  Verification Code
                </label>
                <input
                  id="otp"
                  name="otp"
                  type="text"
                  maxLength={6}
                  pattern="\d{6}"
                  required
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm text-center text-lg tracking-widest"
                  placeholder="000000"
                />
                <p className="text-xs text-slate-300 mt-2">Enter the 6-digit code from your email</p>
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-red-200">{error}</span>
                  </div>
                </div>
              )}

              {success && (
                <div className="bg-green-500/20 border border-green-500/50 rounded-xl p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-green-200">{success}</span>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-xl hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 transition-all duration-200"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Verifying...
                  </div>
                ) : (
                  'Verify Email'
                )}
              </button>

              <div className="text-center">
                <span className="text-slate-300 text-sm">Didn't receive the code?</span>
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={loading}
                  className="ml-2 text-purple-300 hover:text-purple-200 text-sm font-medium transition-colors disabled:opacity-50"
                >
                  Resend Code
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setShowOtpVerification(false);
                    setOtp('');
                    setError('');
                    setSuccess('');
                  }}
                  className="text-slate-400 hover:text-slate-300 text-sm transition-colors"
                >
                  Back to Registration
                </button>
              </div>
            </form>
          </div>

          <div className="mt-8 text-center">
            <div className="text-xs text-slate-400">
              © 2025 OxiWorld Forex Academy • Transforming Traders Worldwide
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Forgot Password Screen
  if (showForgotPassword) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-x-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-32 w-80 h-80 bg-purple-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
          <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-blue-600 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse animation-delay-2000"></div>
          <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-indigo-600 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse animation-delay-4000"></div>
        </div>

        <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center gradient-brand-glow animate-pulse-glow">
                <Image
                  src="/logo_bright.png"
                  alt="OxiWorld Forex Academy"
                  width={64}
                  height={64}
                  className="rounded-xl"
                  priority
                />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Reset Password</h2>
            <p className="text-slate-300">Enter your email to receive a reset link</p>
          </div>

          <div className="bg-white/10 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-white/20">
            <form className="space-y-6" onSubmit={handleForgotPassword}>
              <div>
                <label htmlFor="reset-email" className="block text-sm font-medium text-white mb-2">
                  Email address
                </label>
                <input
                  id="reset-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent backdrop-blur-sm"
                  placeholder="Enter your email address"
                />
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-red-200">{error}</span>
                  </div>
                </div>
              )}

              {success && (
                <div className="bg-green-500/20 border border-green-500/50 rounded-xl p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-green-200">{success}</span>
                  </div>
                </div>
              )}

              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(false)}
                  className="flex-1 py-3 px-4 border border-white/30 rounded-xl text-white font-medium hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-200"
                >
                  Back to Sign In
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-xl hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 transition-all duration-200"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Sending...
                    </div>
                  ) : (
                    'Send Reset Link'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Main Auth Form
  return (
    <div className="min-h-screen bg-brand-auth flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Creative animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-96 h-96 gradient-brand-electric rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-float"></div>
        <div className="absolute -bottom-40 -left-32 w-80 h-80 gradient-brand-ocean rounded-full mix-blend-multiply filter blur-2xl opacity-40 animate-pulse"></div>
        <div className="absolute top-1/3 left-1/4 w-64 h-64 gradient-brand-glow rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-1/3 right-1/4 w-72 h-72 gradient-brand-secondary rounded-full mix-blend-multiply filter blur-xl opacity-25 animate-pulse" style={{ animationDelay: '4s' }}></div>
        
        {/* Floating geometric shapes */}
        <div className="absolute top-20 left-10 w-4 h-4 bg-[var(--brand-electric)] rounded-full animate-pulse opacity-60"></div>
        <div className="absolute top-40 right-20 w-6 h-6 bg-[var(--brand-aqua)] rotate-45 animate-float opacity-50"></div>
        <div className="absolute bottom-32 left-32 w-3 h-3 bg-[var(--brand-mint)] rounded-full animate-pulse opacity-70" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-20 right-10 w-5 h-5 bg-[var(--brand-electric)] rotate-45 animate-float opacity-60" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-2xl flex items-center justify-center gradient-brand-glow animate-pulse-glow">
              <Image
                src="/logo_bright.png"
                alt="OxiWorld Forex Academy"
                width={64}
                height={64}
                className="rounded-xl"
                priority
              />
            </div>
          </div>
          <h2 className="text-4xl font-bold gradient-brand-text mb-2">
            {isLogin ? 'Welcome Back' : 'Join OxiWorld'}
          </h2>
          <p className="text-xl text-white/80 mb-4">
            {isLogin ? 'Access Your Trading Universe' : 'Start Your Trading Journey'}
          </p>
          <p className="text-sm text-white/60">
            {isLogin ? 'Sign in to your professional trading dashboard' : 'Create your account to unlock advanced trading tools'}
          </p>
        </div>

        <div className="card-brand-glow py-10 px-8 shadow-brand-lg animate-float">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <div>
                <label htmlFor="name" className="block text-sm font-medium gradient-brand-text mb-3">
                  Full Name
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-brand w-full"
                  placeholder="Enter your full name"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium gradient-brand-text mb-3">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-brand w-full"
                placeholder="Enter your email address"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium gradient-brand-text mb-3">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={isLogin ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-brand w-full"
                placeholder="Enter your secure password"
              />
              {isLogin && (
                <div className="text-right mt-3">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-sm text-[var(--brand-electric)] hover:text-[var(--brand-aqua)] transition-colors font-medium"
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </div>

            {!isLogin && (
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium gradient-brand-text mb-3">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input-brand w-full"
                  placeholder="Confirm your secure password"
                />
                <div className="text-xs text-white/60 mt-3 p-3 card-brand">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-[var(--brand-electric)] rounded-full mt-1.5"></div>
                    <span>Password must be at least 8 characters with uppercase, lowercase, and numbers.</span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="alert-error rounded-xl p-4 animate-pulse-glow">
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 bg-red-400 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-medium">{error}</span>
                </div>
              </div>
            )}

            {success && (
              <div className="alert-success rounded-xl p-4 animate-pulse-glow">
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 bg-[var(--brand-teal-green)] rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-medium">{success}</span>
                </div>
              </div>
            )}

            {emailVerificationSent && (
              <div className="bg-blue-500/20 border border-blue-500/50 rounded-xl p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-200">Email verification required</h3>
                    <div className="mt-2 text-sm text-blue-300">
                      <p>
                        We've sent a verification link to your email address. Please click the link to activate your account before signing in.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 px-6 gradient-brand-glow text-white font-semibold rounded-xl hover-brand-lift disabled:opacity-50 transition-all duration-300 transform hover:scale-105 shadow-brand-lg"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-white border-t-transparent"></div>
                  <span className="text-lg font-medium">
                    {isLogin ? 'Accessing Your Dashboard...' : 'Creating Your Account...'}
                  </span>
                </div>
              ) : (
                <span className="text-lg font-bold">
                  {isLogin ? '🚀 Launch Trading Dashboard' : '✨ Start Your Trading Journey'}
                </span>
              )}
            </button>

            {/* Creative Divider */}
            <div className="mt-8 mb-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gradient-to-r from-transparent via-[var(--brand-electric)]/30 to-transparent" />
                </div>
                <div className="relative flex justify-center">
                  <span className="px-6 py-2 card-brand text-white/80 text-sm font-medium rounded-full">
                    Or continue with
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={loading}
                className="w-full py-4 px-6 card-brand border-2 border-white/20 rounded-xl text-white font-semibold hover:border-[var(--brand-electric)]/50 focus:outline-none focus:border-[var(--brand-electric)] disabled:opacity-50 transition-all duration-300 flex items-center justify-center group hover-brand-lift"
              >
                <div className="w-6 h-6 mr-4 p-1 bg-white rounded-md group-hover:scale-110 transition-transform">
                  <svg viewBox="0 0 24 24" className="w-full h-full">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </div>
                <span className="text-lg">Continue with Google</span>
              </button>
            </div>

            {/* Creative Toggle Section */}
            <div className="text-center mt-8">
              <div className="card-brand p-4 rounded-full inline-flex items-center space-x-3">
                <span className="text-white/80">
                  {isLogin ? "New to OxiWorld?" : "Already have an account?"}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError('');
                    setSuccess('');
                    setEmailVerificationSent(false);
                    setName('');
                    setPassword('');
                    setConfirmPassword('');
                  }}
                  className="font-bold gradient-brand-text hover:text-[var(--brand-electric)] transition-colors"
                >
                  {isLogin ? 'Create Account' : 'Sign In'}
                </button>
              </div>
            </div>
          </form>

          <div className="mt-10 text-center space-y-4">
            <div className="card-brand p-4 rounded-xl">
              <div className="text-sm gradient-brand-text font-medium">
                🌟 Professional Forex Education Platform
              </div>
              <div className="text-xs text-white/60 mt-2">
                For Serious Traders & Future Market Leaders
              </div>
            </div>
            <div className="text-xs text-white/40">
              © 2025 OxiWorld Forex Academy • Transforming Traders Worldwide
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}