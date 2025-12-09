'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Import getSession dynamically to avoid SSR issues
        const { getSession } = await import('next-auth/react');
        const session = await getSession();

        if (session && (session as any).backendAccessToken) {
          // Store JWT tokens in localStorage
          localStorage.setItem('user_auth_token', (session as any).backendAccessToken);
          localStorage.setItem('refresh_token', (session as any).backendRefreshToken || '');
          
          // Small delay to ensure tokens are stored
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // Redirect to dashboard
          router.push('/dashboard');
        } else {
          // No backend tokens, try again or redirect to login
          setError('Authentication failed. Please try again.');
          setTimeout(() => router.push('/auth'), 2000);
        }
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('An error occurred. Redirecting to login...');
        setTimeout(() => router.push('/auth'), 2000);
      }
    };

    handleOAuthCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#002A5C] to-[#000D2E]">
      <div className="text-center">
        {error ? (
          <>
            <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-16 h-16 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-white text-lg">{error}</p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 border-4 border-white/20 border-t-[#00B38F] rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg">Completing sign in...</p>
          </>
        )}
      </div>
    </div>
  );
}
