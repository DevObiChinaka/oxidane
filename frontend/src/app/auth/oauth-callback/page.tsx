'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string>('');

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        setDebugInfo('Fetching session...');
        
        // Import getSession dynamically to avoid SSR issues
        const { getSession } = await import('next-auth/react');
        const session = await getSession();

        setDebugInfo('Session retrieved');
        console.log('[OAuth Callback] Session:', session);

        if (session) {
          // Check if backend tokens are already in session
          const backendAccessToken = (session as any).backendAccessToken;
          
          if (backendAccessToken) {
            console.log('[OAuth Callback] Backend tokens found in session');
            setDebugInfo('Storing tokens from session...');
            
            localStorage.setItem('user_auth_token', backendAccessToken);
            localStorage.setItem('refresh_token', (session as any).backendRefreshToken || '');
            
            await new Promise(resolve => setTimeout(resolve, 200));
            setDebugInfo('Redirecting to dashboard...');
            router.push('/dashboard');
          } else {
            // Manually sync with backend since NextAuth callback might have failed
            console.log('[OAuth Callback] No backend tokens in session, manually syncing...');
            setDebugInfo('Syncing with backend...');
            
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.oxiworldforexacademy.com';
            console.log('[OAuth Callback] API URL:', apiUrl);
            
            const userInfo = {
              email: session.user?.email,
              name: session.user?.name,
              picture: session.user?.image,
              given_name: session.user?.name?.split(' ')[0] || '',
              family_name: session.user?.name?.split(' ').slice(1).join(' ') || '',
              sub: (session.user as any)?.id || session.user?.email,
            };
            
            console.log('[OAuth Callback] Calling backend OAuth endpoint...');
            
            const response = await fetch(`${apiUrl}/api/auth/oauth/`, {
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
            
            console.log('[OAuth Callback] Backend response status:', response.status);
            
            if (response.ok) {
              const backendUser = await response.json();
              console.log('[OAuth Callback] Backend sync successful');
              console.log('[OAuth Callback] Has access token:', !!backendUser.access_token);
              
              if (backendUser.access_token) {
                setDebugInfo('Storing tokens...');
                localStorage.setItem('user_auth_token', backendUser.access_token);
                localStorage.setItem('refresh_token', backendUser.refresh_token || '');
                
                await new Promise(resolve => setTimeout(resolve, 200));
                setDebugInfo('Redirecting to dashboard...');
                router.push('/dashboard');
              } else {
                console.error('[OAuth Callback] No access token in backend response');
                setError('Backend sync incomplete. No access token received.');
                setTimeout(() => router.push('/auth'), 3000);
              }
            } else {
              const errorText = await response.text();
              console.error('[OAuth Callback] Backend sync failed:', errorText);
              setError(`Backend sync failed: ${response.status}`);
              setTimeout(() => router.push('/auth'), 3000);
            }
          }
        } else {
          console.error('[OAuth Callback] No session found');
          setError('No session found. Please try signing in again.');
          setTimeout(() => router.push('/auth'), 2000);
        }
      } catch (err) {
        console.error('[OAuth Callback] Error:', err);
        setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
            <p className="text-white/60 text-sm">Redirecting to login...</p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 border-4 border-white/20 border-t-[#00B38F] rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg mb-2">Completing sign in...</p>
            {debugInfo && <p className="text-white/60 text-sm">{debugInfo}</p>}
          </>
        )}
      </div>
    </div>
  );
}
