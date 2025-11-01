'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { EnvelopeIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export default function ForgotPasswordPage() {
  const router = useRouter();
  
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/password-reset/request/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
      } else {
        setError(data.error || 'Failed to send reset email. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 px-4">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-lg">
              <EnvelopeIcon className="h-8 w-8 text-white" />
            </div>
            <h2 className="mt-6 text-3xl font-bold text-gray-900">
              Check Your Email
            </h2>
            <p className="mt-4 text-gray-600 leading-relaxed">
              If an account exists with <span className="font-semibold text-gray-900">{email}</span>, 
              you will receive password reset instructions shortly.
            </p>
            <p className="mt-4 text-sm text-gray-500">
              The reset link will expire in 1 hour for security reasons.
            </p>
          </div>

          <div className="space-y-4">
            <Link
              href="/auth"
              className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 rounded-xl text-sm font-semibold text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#00B38F] transition-all duration-200"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              Back to Login
            </Link>

            <button
              onClick={() => {
                setSuccess(false);
                setEmail('');
              }}
              className="w-full text-sm text-[#00B38F] hover:text-[#00A87D] font-medium transition-colors"
            >
              Send to a different email
            </button>
          </div>

          <p className="text-center text-xs text-gray-500 mt-6">
            Didn't receive the email? Check your spam folder or try again in a few minutes.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 px-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-[#00B38F] to-[#00A87D] rounded-full flex items-center justify-center shadow-lg">
            <EnvelopeIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Forgot Password?
          </h2>
          <p className="mt-2 text-gray-600">
            No worries! Enter your email and we'll send you reset instructions.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

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
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#00B38F] focus:border-transparent transition-all duration-200 text-gray-900 bg-white"
                placeholder="Enter your email"
                disabled={loading}
                required
                autoComplete="email"
                autoFocus
              />
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
                Sending...
              </div>
            ) : (
              'Send Reset Link'
            )}
          </button>

          <div className="text-center space-y-3">
            <Link
              href="/auth"
              className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-[#00B38F] transition-colors"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              Back to Login
            </Link>
            
            <div className="text-sm text-gray-500">
              Don't have an account?{' '}
              <Link href="/auth" className="font-medium text-[#00B38F] hover:text-[#00A87D]">
                Sign up
              </Link>
            </div>
          </div>
        </form>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            For security reasons, we'll only send reset instructions if your email is registered.
          </p>
        </div>
      </div>
    </div>
  );
}
