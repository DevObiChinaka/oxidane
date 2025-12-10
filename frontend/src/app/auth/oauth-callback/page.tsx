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

        if (session) {
          // Check if backend tokens are already in session
          const backendAccessToken = (session as any).backendAccessToken;
          
          if (backendAccessToken) {
            localStorage.setItem('user_auth_token', backendAccessToken);
            localStorage.setItem('refresh_token', (session as any).backendRefreshToken || '');
            
            await new Promise(resolve => setTimeout(resolve, 200));
            router.push('/dashboard');
          } else {
            // Manually sync with backend
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.oxiworldforexacademy.com';
            
            const userInfo = {
              email: session.user?.email,
              name: session.user?.name,
              picture: session.user?.image,
              given_name: session.user?.name?.split(' ')[0] || '',
              family_name: session.user?.name?.split(' ').slice(1).join(' ') || '',
              sub: (session.user as any)?.id || session.user?.email,
            };
            
            const response = await fetch(`${apiUrl}/auth/oauth/`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                provider: (session as any).provider || 'google',
                access_token: (session as any).accessToken,
                user_info: userInfo,
              }),
            });
            
            if (response.ok) {
              const backendUser = await response.json();
              
              if (backendUser.access_token) {
                localStorage.setItem('user_auth_token', backendUser.access_token);
                localStorage.setItem('refresh_token', backendUser.refresh_token || '');
                
                await new Promise(resolve => setTimeout(resolve, 200));
                router.push('/dashboard');
              } else {
                setError('Authentication incomplete. Please try again.');
                setTimeout(() => router.push('/auth'), 3000);
              }
            } else {
              setError('Authentication failed. Please try again.');
              setTimeout(() => router.push('/auth'), 3000);
            }
          }
        } else {
          setError('Please try signing in again.');
          setTimeout(() => router.push('/auth'), 2000);
        }
      } catch (err) {
        setError('An error occurred. Please try again.');
        setTimeout(() => router.push('/auth'), 3000);
      }
    };

    handleOAuthCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#002A5C] to-[#000D2E]">
      <div className="text-center max-w-md px-6">
        {error ? (
          <>
            <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <svg className="w-16 h-16 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-white text-lg mb-2">{error}</p>
            <p className="text-white/60 text-sm">Redirecting...</p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 border-4 border-white/20 border-t-[#00B38F] rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg mb-2">Completing sign in...</p>
            <p className="text-white/60 text-sm">Please wait</p>
          </>
        )}
      </div>
    </div>
  );
}
