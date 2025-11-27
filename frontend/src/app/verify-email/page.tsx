'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import Logo from '../components/Logo';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link');
      return;
    }

    // Verify the token with the backend
    const verifyEmail = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/verify-email/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! You can now sign in.');
          setTimeout(() => {
            router.push('/auth');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(data.error || 'Email verification failed');
        }
      } catch (error) {
        setStatus('error');
        setMessage('An error occurred during verification');
      }
    };

    verifyEmail();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#000856] via-[#001B73] to-[#004A42] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-x-hidden">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-80 h-80 bg-[#00B38F]/30 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-[#000ABE]/30 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-pulse animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#00B39F]/30 rounded-full mix-blend-multiply filter blur-xl opacity-50 animate-pulse animation-delay-4000"></div>
      </div>

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <Logo size="lg" />
          </div>
          <h2 className="text-3xl font-bold text-white">
            Email Verification
          </h2>
        </div>

        <div className="bg-white/10 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-white/20">
          <div className="text-center">
            {status === 'loading' && (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
                <p className="text-white">Verifying your email...</p>
              </div>
            )}

            {status === 'success' && (
              <div className="flex flex-col items-center">
                <div className="bg-green-500/20 border border-green-500/50 rounded-full p-4 mb-4">
                  <svg className="w-8 h-8 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Verification Successful!</h3>
                <p className="text-slate-300 mb-4">{message}</p>
                <p className="text-sm text-slate-400">Redirecting to sign in page...</p>
              </div>
            )}

            {status === 'error' && (
              <div className="flex flex-col items-center">
                <div className="bg-red-500/20 border border-red-500/50 rounded-full p-4 mb-4">
                  <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">Verification Failed</h3>
                <p className="text-slate-300 mb-6">{message}</p>
                <button
                  onClick={() => router.push('/auth')}
                  className="py-3 px-6 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white font-medium rounded-xl hover:from-[#00A87D] hover:to-[#00A58D] focus:outline-none focus:ring-2 focus:ring-[#00B38F] transition-all duration-200"
                >
                  Go to Sign In
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 text-center">
          <div className="text-xs text-slate-400">
            Professional forex education platform for serious traders
          </div>
          <div className="text-xs text-slate-500 mt-2">
            © 2025 Oxidane Forex Academy
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
