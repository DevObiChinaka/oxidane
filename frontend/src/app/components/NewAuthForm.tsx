'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';

interface NewAuthFormProps {
  initialIsLogin?: boolean;
}

export default function NewAuthForm({ initialIsLogin = true }: NewAuthFormProps) {
  const [isLogin, setIsLogin] = useState(initialIsLogin);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [emailVerificationSent, setEmailVerificationSent] = useState(false);
  const [showOtpVerification, setShowOtpVerification] = useState(false);
  const [otp, setOtp] = useState('');
  const [emailForVerification, setEmailForVerification] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // OTP countdown timers
  const [otpExpiresIn, setOtpExpiresIn] = useState(600); // 10 minutes in seconds
  const [resendCooldown, setResendCooldown] = useState(0); // Cooldown for resend button
  
  // Email validation states
  const [emailValidation, setEmailValidation] = useState<{
    isValid: boolean;
    isChecking: boolean;
    accountExists: boolean;
    message: string;
  }>({
    isValid: false,
    isChecking: false,
    accountExists: false,
    message: '',
  });

  // Email validation function
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Check if email account exists (debounced)
  const checkEmailAvailability = async (emailToCheck: string) => {
    if (!validateEmail(emailToCheck)) {
      setEmailValidation({
        isValid: false,
        isChecking: false,
        accountExists: false,
        message: '',
      });
      return;
    }

    setEmailValidation(prev => ({ ...prev, isChecking: true }));

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/check-email/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailToCheck }),
      });

      const data = await response.json();

      if (response.ok) {
        setEmailValidation({
          isValid: true,
          isChecking: false,
          accountExists: data.exists || false,
          message: data.exists ? 'Account already exists' : 'Email available',
        });
      } else {
        setEmailValidation({
          isValid: true,
          isChecking: false,
          accountExists: false,
          message: '',
        });
      }
    } catch (error) {
      // If endpoint doesn't exist, just validate format
      setEmailValidation({
        isValid: true,
        isChecking: false,
        accountExists: false,
        message: 'Valid email format',
      });
    }
  };

  // Debounce email check
  useEffect(() => {
    if (!isLogin && email) {
      const timer = setTimeout(() => {
        checkEmailAvailability(email);
      }, 500); // Check after 500ms of no typing

      return () => clearTimeout(timer);
    } else if (isLogin && email) {
      // For login, just validate format
      setEmailValidation({
        isValid: validateEmail(email),
        isChecking: false,
        accountExists: false,
        message: validateEmail(email) ? 'Valid email format' : '',
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, isLogin]);

  // OTP countdown timers
  useEffect(() => {
    if (!showOtpVerification) return;

    // OTP expiration countdown
    const otpTimer = setInterval(() => {
      setOtpExpiresIn((prev) => {
        if (prev <= 0) {
          clearInterval(otpTimer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Resend cooldown countdown
    let resendTimer: NodeJS.Timeout;
    if (resendCooldown > 0) {
      resendTimer = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 0) {
            clearInterval(resendTimer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      clearInterval(otpTimer);
      if (resendTimer) clearInterval(resendTimer);
    };
  }, [showOtpVerification, resendCooldown]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Password validation requirements
  const getPasswordRequirements = (password: string) => {
    return [
      {
        label: 'At least 8 characters',
        met: password.length >= 8
      },
      {
        label: 'At least one uppercase letter',
        met: /[A-Z]/.test(password)
      },
      {
        label: 'At least one lowercase letter',
        met: /[a-z]/.test(password)
      },
      {
        label: 'At least one number',
        met: /\d/.test(password)
      },
      {
        label: 'At least one special character',
        met: /[!@#$%^&*(),.?":{}|<>]/.test(password)
      }
    ];
  };

  const isPasswordValid = (password: string) => {
    return getPasswordRequirements(password).every(req => req.met);
  };

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

    if (!isLogin && !isPasswordValid(password)) {
      setError('Please meet all password requirements');
      setLoading(false);
      return;
    }

    // Prevent registration if account already exists
    if (!isLogin && emailValidation.accountExists) {
      setError('An account with this email already exists. Please sign in instead.');
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin
        ? { email, password }
        : { email, password, first_name: firstName, last_name: lastName };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        // Enhanced error messages based on error codes
        if (data.code === 'ACCOUNT_NOT_FOUND') {
          setError('No account found with this email address. Please sign up first.');
        } else if (data.code === 'INVALID_PASSWORD') {
          setError('Incorrect password. Please try again.');
        } else if (data.code === 'EMAIL_NOT_VERIFIED') {
          setError('Please verify your email before signing in. Check your inbox for the verification code.');
          // Auto-switch to OTP verification if available
          if (data.email) {
            setEmailForVerification(data.email);
            setShowOtpVerification(true);
          }
        } else if (data.code === 'ACCOUNT_INACTIVE') {
          setError('Your account is inactive. Please contact support.');
        } else {
          setError(data.error || 'Authentication failed');
        }
        setLoading(false);
        return;
      }

      if (isLogin) {
        // New OTP flow for login
        if (data.requires_otp && data.session_token) {
          setEmailForVerification(email);
          setShowOtpVerification(true);
          setSuccess(data.message || 'Verification code sent to your email. Please enter it to complete sign-in.');
          // Store session token for OTP verification (you may need to add state for this)
          sessionStorage.setItem('login_session_token', data.session_token);
          // Reset countdown timers
          setOtpExpiresIn(600); // 10 minutes
          setResendCooldown(0);
        } else {
          // Old flow fallback (shouldn't happen with new backend)
          setSuccess('Login successful! Redirecting...');
          window.location.href = '/dashboard';
        }
      } else {
        // Registration: Show OTP verification screen
        if (data.otp_sent || data.requires_verification) {
          setEmailForVerification(email);
          setShowOtpVerification(true);
          setSuccess('Verification code sent! Please check your email and enter the code to complete your registration.');
          // Reset countdown timers
          setOtpExpiresIn(600); // 10 minutes
          setResendCooldown(0);
        } else {
          setEmailVerificationSent(true);
          setSuccess('Registration successful! Please check your email to verify your account.');
        }
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Use NextAuth.js Google provider
      const { signIn } = await import('next-auth/react');
      await signIn('google', { callbackUrl: '/' });
    } catch (error) {
      console.error('Google Sign-In Error:', error);
      setError('Google sign-in failed. Please try again.');
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const sessionToken = sessionStorage.getItem('login_session_token');
      
      if (sessionToken) {
        // Resend login OTP
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/resend-login-otp/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_token: sessionToken }),
        });

        const data = await response.json();

        if (!response.ok) {
          setError(data.error || 'Failed to resend verification code');
        } else {
          setSuccess('Verification code resent to your email');
          // Reset timers after successful resend
          setOtpExpiresIn(600); // Reset to 10 minutes
          setResendCooldown(60); // 60 second cooldown
        }
      } else {
        // Resend registration OTP
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
          // Reset timers after successful resend
          setOtpExpiresIn(600); // Reset to 10 minutes
          setResendCooldown(60); // 60 second cooldown
        }
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
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';
      const response = await fetch(`${API_BASE_URL}/auth/password-reset/request/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'Failed to send reset email');
        setLoading(false);
        return;
      }

      setSuccess('If an account exists with this email, you will receive password reset instructions shortly.');
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
      // Check if this is login OTP or registration OTP
      const sessionToken = sessionStorage.getItem('login_session_token');
      
      if (sessionToken) {
        // Login OTP verification
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/verify-login-otp/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            session_token: sessionToken,
            otp 
          }),
        });

        const data = await response.json();

        if (!response.ok) {
          if (data.code === 'OTP_EXPIRED') {
            setError('Verification code expired. Please request a new one.');
          } else if (data.code === 'INVALID_OTP') {
            setError('Invalid verification code. Please check and try again.');
          } else if (data.code === 'SESSION_EXPIRED') {
            setError('Session expired. Please sign in again.');
            setTimeout(() => {
              setShowOtpVerification(false);
              sessionStorage.removeItem('login_session_token');
            }, 2000);
          } else {
            setError(data.error || 'OTP verification failed');
          }
          setLoading(false);
          return;
        }

        // Login successful - store token and redirect
        if (data.token) {
          localStorage.setItem('access_token', data.token);
          if (data.refresh) {
            localStorage.setItem('refresh_token', data.refresh);
          }
          sessionStorage.removeItem('login_session_token');
          setSuccess('🎉 Login successful! Redirecting to dashboard...');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 1500);
        }
      } else {
        // Registration OTP verification
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

        setSuccess('🎉 Account created successfully! Your registration is complete. You can now sign in with your credentials.');
        setTimeout(() => {
          setShowOtpVerification(false);
          setIsLogin(true); // Switch to login form
          setEmail(emailForVerification);
          setPassword(''); // Clear password for security
          setFirstName(''); // Clear first name
          setLastName(''); // Clear last name
          setConfirmPassword(''); // Clear confirm password
          setOtp(''); // Clear OTP
          setError(''); // Clear any errors
        }, 3000); // Give user time to read success message
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }

    setLoading(false);
  };

  // OTP Verification Screen
  if (showOtpVerification) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
        {/* Hero-Inspired Background Design - same as main form */}
        <div className="absolute inset-0 overflow-hidden">
          {/* Financial Pattern Background */}
          <div className="absolute inset-0 opacity-8">
            <div className="absolute inset-0" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }}></div>
          </div>

          {/* Animated Chart Lines */}
          <div className="absolute inset-0 opacity-15">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path
                d="M0,50 Q25,30 50,40 T100,35"
                stroke="#00B38F"
                strokeWidth="0.5"
                fill="none"
                className="animate-pulse"
              />
              <path
                d="M0,60 Q25,45 50,50 T100,45"
                stroke="#00B38F"
                strokeWidth="0.3"
                fill="none"
                opacity="0.6"
                className="animate-pulse"
                style={{ animationDelay: '1s' }}
              />
            </svg>
          </div>

          {/* Floating Elements */}
          <div className="absolute top-20 right-20 w-32 h-32 bg-[#00B38F]/10 rounded-full blur-xl animate-float"></div>
          <div className="absolute bottom-32 left-20 w-48 h-48 bg-[#004A42]/20 rounded-full blur-2xl animate-float-delayed"></div>
          <div className="absolute top-1/3 left-1/4 w-24 h-24 bg-[#002A5C]/15 rounded-full blur-lg animate-pulse"></div>
        </div>

        <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[#00B38F] to-[#000ABE] shadow-2xl animate-pulse">
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
            <p className="text-[#00B38F] font-medium">{emailForVerification}</p>
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
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-300 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent backdrop-blur-sm text-center text-lg tracking-widest"
                  placeholder="000000"
                />
                <p className="text-xs text-slate-300 mt-2">Enter the 6-digit code from your email</p>
              </div>

              <div className="bg-[#00B38F]/20 border border-[#00B38F]/30 rounded-xl p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-[#00B38F] mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <div className="text-[#00B38F]/90 text-sm">
                    <p className="font-medium mb-1">After verification:</p>
                    <p>Your account will be created and you'll be redirected to the sign-in form to access your new OxiWorld account.</p>
                  </div>
                </div>
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

              {/* OTP Expiration Countdown */}
              <div className={`text-center p-3 rounded-xl border ${
                otpExpiresIn <= 60 
                  ? 'bg-red-500/10 border-red-500/30 text-red-300' 
                  : otpExpiresIn <= 300 
                    ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300'
                    : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
              }`}>
                <div className="flex items-center justify-center text-sm">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {otpExpiresIn > 0 ? (
                    <>Code expires in <span className="font-mono font-semibold ml-1">{formatTime(otpExpiresIn)}</span></>
                  ) : (
                    <span className="font-semibold">Code expired - Please request a new code</span>
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6 || otpExpiresIn === 0}
                className="w-full py-3 px-4 bg-gradient-to-r from-[#00B38F] to-[#000ABE] text-white font-medium rounded-xl hover:from-[#00A87D] hover:to-[#000C9E] focus:outline-none focus:ring-2 focus:ring-[#00B38F] disabled:opacity-50 transition-all duration-200 shadow-lg"
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
                  disabled={loading || resendCooldown > 0}
                  className="ml-2 text-[#00B38F] hover:text-[#00A87D] text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {resendCooldown > 0 
                    ? `Resend Code (${resendCooldown}s)` 
                    : 'Resend Code'}
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
      <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#001A7A] to-[#000856] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-x-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-32 w-80 h-80 bg-[#00B38F] rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
          <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-[#00B39F] rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse animation-delay-2000"></div>
          <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-[#000ABE] rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse animation-delay-4000"></div>
        </div>

        <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[#00B38F] to-[#000ABE] shadow-2xl animate-pulse">
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
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-300 focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent backdrop-blur-sm"
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
                  className="flex-1 py-3 px-4 border border-white/30 rounded-xl text-white font-medium hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-[#00B38F] transition-all duration-200"
                >
                  Back to Sign In
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 px-4 bg-gradient-to-r from-[#00B38F] to-[#000ABE] text-white font-medium rounded-xl hover:from-[#00A87D] hover:to-[#000C9E] focus:outline-none focus:ring-2 focus:ring-[#00B38F] disabled:opacity-50 transition-all duration-200 shadow-lg"
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
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Hero-Inspired Background Design */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Financial Pattern Background - same as hero */}
        <div className="absolute inset-0 opacity-8">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}></div>
        </div>

        {/* Animated Chart Lines - like hero */}
        <div className="absolute inset-0 opacity-15">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path
              d="M0,50 Q25,30 50,40 T100,35"
              stroke="#00B38F"
              strokeWidth="0.5"
              fill="none"
              className="animate-pulse"
            />
            <path
              d="M0,60 Q25,80 50,60 T100,65"
              stroke="#00B39F"
              strokeWidth="0.5"
              fill="none"
              className="animate-pulse"
              style={{animationDelay: '1s'}}
            />
            <path
              d="M0,40 Q40,20 80,45 T160,40"
              stroke="#000ABE"
              strokeWidth="0.3"
              fill="none"
              className="animate-pulse"
              style={{animationDelay: '2s'}}
            />
          </svg>
        </div>

        {/* Gradient Orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#00B38F]/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#000ABE]/5 rounded-full blur-3xl"></div>
        <div className="absolute top-3/4 left-3/4 w-64 h-64 bg-[#00B39F]/8 rounded-full blur-2xl"></div>
      </div>
      
      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <div className="relative group">
              <div className="w-24 h-24 rounded-3xl flex items-center justify-center bg-gradient-to-br from-[#00B38F] via-[#00B39F] to-[#000ABE] shadow-2xl transform group-hover:scale-110 transition-all duration-500 group-hover:rotate-3 relative overflow-hidden">
                {/* Logo Inner Glow */}
                <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-transparent rounded-3xl"></div>
                <div className="absolute inset-0 bg-gradient-to-tl from-transparent via-white/10 to-white/20 rounded-3xl"></div>
                
                <Image
                  src="/logo_bright.png"
                  alt="OxiWorld Forex Academy"
                  width={64}
                  height={64}
                  className="rounded-2xl relative z-10"
                  priority
                />
              </div>
              {/* Logo Outer Glow */}
              <div className="absolute -inset-3 bg-gradient-to-br from-[#00B38F]/30 to-[#000ABE]/30 rounded-3xl blur-xl -z-10 opacity-60 group-hover:opacity-80 transition-opacity duration-500"></div>
              <div className="absolute -inset-1 bg-gradient-to-br from-[#00B38F]/20 to-[#000ABE]/20 rounded-3xl blur-md -z-10 animate-pulse"></div>
            </div>
          </div>
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-white via-white/90 to-white bg-clip-text text-transparent mb-2 drop-shadow-lg">
              {isLogin ? 'Welcome Back' : 'Join OxiWorld'}
            </h2>
            <div className="w-20 h-1.5 bg-gradient-to-r from-[#00B38F] via-[#00B39F] to-[#000ABE] mx-auto rounded-full shadow-lg"></div>
            <p className="text-white/80 font-medium text-lg">
              {isLogin ? 'Sign in to your account to continue' : 'Create your account and start your trading journey'}
            </p>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-2xl py-10 px-6 shadow-2xl border border-white/20 sm:rounded-3xl sm:px-12 relative overflow-hidden">
          {/* Glassmorphism Inner Glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#00B38F]/10 via-transparent to-[#000ABE]/10 rounded-3xl"></div>
          <div className="absolute inset-0 bg-gradient-to-tl from-white/5 via-transparent to-white/10 rounded-3xl"></div>
          
          {/* Top Gradient Border */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#00B38F] via-[#00B39F] to-[#000ABE] rounded-t-3xl"></div>
          
          {/* Subtle Inner Border */}
          <div className="absolute inset-[1px] rounded-3xl border border-white/10"></div>
          
          <div className="relative z-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  {/* First Name Field */}
                  <div>
                    <label htmlFor="firstName" className="block text-sm font-medium text-white/90 mb-3">
                      First Name
                    </label>
                    <div className="mt-1">
                      <div className="relative group">
                        <input
                          id="firstName"
                          name="firstName"
                          type="text"
                          autoComplete="given-name"
                          required
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          className="appearance-none block w-full px-5 py-4 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F] backdrop-blur-sm transition-all duration-300 group-hover:bg-white/15"
                          placeholder="First name"
                        />
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00B38F]/5 to-[#000ABE]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                      </div>
                    </div>
                  </div>

                  {/* Last Name Field */}
                  <div>
                    <label htmlFor="lastName" className="block text-sm font-medium text-white/90 mb-3">
                      Last Name
                    </label>
                    <div className="mt-1">
                      <div className="relative group">
                        <input
                          id="lastName"
                          name="lastName"
                          type="text"
                          autoComplete="family-name"
                          required
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          className="appearance-none block w-full px-5 py-4 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F] backdrop-blur-sm transition-all duration-300 group-hover:bg-white/15"
                          placeholder="Last name"
                        />
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00B38F]/5 to-[#000ABE]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white/90 mb-3">
                Email Address
              </label>
              <div className="mt-1">
                <div className="relative group">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`appearance-none block w-full px-5 py-4 pr-12 bg-white/10 border ${
                      !isLogin && email && emailValidation.accountExists 
                        ? 'border-yellow-400/50' 
                        : !isLogin && email && emailValidation.isValid 
                        ? 'border-green-400/50' 
                        : 'border-white/20'
                    } rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F] backdrop-blur-sm transition-all duration-300 group-hover:bg-white/15`}
                    placeholder="Enter your email address"
                  />
                  
                  {/* Validation Icons */}
                  <div className="absolute inset-y-0 right-0 flex items-center pr-4">
                    {!isLogin && emailValidation.isChecking && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    )}
                    {!isLogin && email && !emailValidation.isChecking && emailValidation.isValid && !emailValidation.accountExists && (
                      <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                    {!isLogin && email && !emailValidation.isChecking && emailValidation.accountExists && (
                      <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    {isLogin && email && validateEmail(email) && (
                      <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00B38F]/5 to-[#000ABE]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                </div>
                
                {/* Email validation message */}
                {!isLogin && email && !emailValidation.isChecking && emailValidation.accountExists && (
                  <div className="mt-2 flex items-center text-yellow-300 text-sm">
                    <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Account already exists. 
                    <button
                      type="button"
                      onClick={() => {
                        setIsLogin(true);
                        setError('');
                        setSuccess('');
                      }}
                      className="ml-1 font-medium hover:text-yellow-200 underline"
                    >
                      Sign in instead?
                    </button>
                  </div>
                )}
                {!isLogin && email && !emailValidation.isChecking && emailValidation.isValid && !emailValidation.accountExists && (
                  <p className="mt-2 text-green-300 text-sm flex items-center">
                    <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Email available
                  </p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white/90 mb-3">
                Password
              </label>
              <div className="mt-1">
                <div className="relative group">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="appearance-none block w-full px-5 py-4 pr-12 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F] backdrop-blur-sm transition-all duration-300 group-hover:bg-white/15"
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-white/60 hover:text-white/90 transition-colors duration-200 z-10"
                  >
                    {showPassword ? (
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.464 8.464m1.414 1.414L8.464 8.464m5.656 5.656l1.415 1.415m-1.415-1.415l1.415 1.415M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.543 7-1.275 4.057-5.065 7-9.543 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00B38F]/5 to-[#000ABE]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                </div>
              </div>
              {isLogin && (
                <div className="text-right mt-2">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-sm text-[#00B38F] hover:text-[#00A87D] transition-colors font-medium"
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </div>

            {!isLogin && (
              <>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-white/80 mb-3 tracking-wider">
                    Confirm Password
                  </label>
                  <div className="relative group">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      autoComplete="new-password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="appearance-none block w-full px-5 py-4 pr-12 bg-white/10 border border-white/20 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F] backdrop-blur-sm transition-all duration-300 group-hover:bg-white/15"
                      placeholder="Confirm your password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 pr-4 flex items-center text-white/60 hover:text-white/90 transition-colors duration-200 z-10"
                    >
                      {showConfirmPassword ? (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.464 8.464m1.414 1.414L8.464 8.464m5.656 5.656l1.415 1.415m-1.415-1.415l1.415 1.415M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.543 7-1.275 4.057-5.065 7-9.543 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      )}
                    </button>
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00B38F]/5 to-[#000ABE]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                  </div>
                  {confirmPassword && password !== confirmPassword && (
                    <p className="mt-2 text-sm text-red-300/80 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      Passwords do not match
                    </p>
                  )}
                </div>

                {/* Password Requirements */}
                {password && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-white/80 tracking-wider">Password Requirements</h4>
                    <div className="grid grid-cols-1 gap-2">
                      {getPasswordRequirements(password).map((requirement, index) => (
                        <div key={index} className={`flex items-center gap-3 px-4 py-2 rounded-xl backdrop-blur-sm transition-all duration-300 ${
                          requirement.met 
                            ? 'bg-[#00B38F]/20 border border-[#00B38F]/30 text-[#00B38F]' 
                            : 'bg-white/5 border border-white/10 text-white/60'
                        }`}>
                          <div className={`flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300 ${
                            requirement.met 
                              ? 'bg-[#00B38F] text-white' 
                              : 'bg-white/20 text-white/40'
                          }`}>
                            {requirement.met ? (
                              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <div className="w-1.5 h-1.5 bg-current rounded-full"></div>
                            )}
                          </div>
                          <span className="text-sm font-medium">{requirement.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {error && (
              <div className="rounded-xl bg-red-500/20 border border-red-500/30 p-4 backdrop-blur-sm">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-red-200">{error}</p>
                    {isLogin && error.includes('No account found') && (
                      <button
                        type="button"
                        onClick={() => {
                          setIsLogin(false);
                          setError('');
                          setSuccess('');
                        }}
                        className="mt-2 text-sm text-[#00B38F] font-medium hover:text-[#00B39F] transition-colors"
                      >
                        Create an account →
                      </button>
                    )}
                    {!isLogin && error.includes('already exists') && (
                      <button
                        type="button"
                        onClick={() => {
                          setIsLogin(true);
                          setError('');
                          setSuccess('');
                        }}
                        className="mt-2 text-sm text-[#00B38F] font-medium hover:text-[#00B39F] transition-colors"
                      >
                        Sign in instead →
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {success && (
              <div className="rounded-xl bg-[#00B38F]/20 border border-[#00B38F]/30 p-4 backdrop-blur-sm">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-white">{success}</p>
                  </div>
                </div>
              </div>
            )}

            {emailVerificationSent && (
              <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Email verification required</h3>
                    <div className="mt-2 text-sm text-blue-700">
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
              className="group w-full flex justify-center py-4 px-6 border border-white/20 rounded-2xl text-base font-medium text-white bg-white/10 hover:bg-white/15 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 focus:border-[#00B38F]/50 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.01] transition-all duration-300 relative overflow-hidden"
            >
              {/* Subtle gradient overlay on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-[#00B38F]/20 via-[#00B39F]/20 to-[#000ABE]/20 opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-300"></div>
              
              {/* Subtle shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
              
              {loading ? (
                <div className="flex items-center relative z-10">
                  <div className="w-5 h-5 border-2 border-white/70 border-t-transparent rounded-full animate-spin mr-2"></div>
                  <span className="text-white/90">Processing...</span>
                </div>
              ) : (
                <span className="relative z-10 font-medium tracking-wide text-white">
                  {isLogin ? 'Sign In' : 'Create Account'}
                </span>
              )}
            </button>

            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-gradient-to-r from-transparent via-[#002A5C] to-transparent text-white/70 font-medium">Or continue with</span>
                </div>
              </div>

              <div className="mt-6">
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={loading}
                  className="group w-full inline-flex justify-center items-center py-4 px-4 border border-white/20 rounded-2xl shadow-lg bg-white/10 hover:bg-white/15 backdrop-blur-sm text-sm font-semibold text-white focus:outline-none focus:ring-2 focus:ring-[#00B38F]/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:shadow-xl"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  <span className="ml-2">Continue with Google</span>
                </button>
              </div>
            </div>

            {/* Creative Toggle Section */}
            <div className="text-center mt-8">
              <div className="text-sm text-white/70">
                {isLogin ? "New to OxiWorld?" : "Already have an account?"}{' '}
                <button
                  type="button"
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError('');
                    setSuccess('');
                    setEmailVerificationSent(false);
                    setFirstName('');
                    setLastName('');
                    setPassword('');
                    setConfirmPassword('');
                  }}
                  className="font-medium text-[#00B38F] hover:text-white focus:outline-none focus:underline transition-colors duration-200"
                >
                  {isLogin ? 'Create Account' : 'Sign In'}
                </button>
              </div>
            </div>
          </form>

          <div className="mt-8 text-center text-sm text-white/50">
            © 2025 OxiWorld Forex Academy
          </div>
          </div>
        </div>
      </div>
    </div>
  );
}