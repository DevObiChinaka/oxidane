'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export default function OAuthCallbackPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'loading') return;

    if (session && (session as any).backendAccessToken) {
      // Store JWT tokens in localStorage
      localStorage.setItem('user_auth_token', (session as any).backendAccessToken);
      localStorage.setItem('refresh_token', (session as any).backendRefreshToken || '');
      
      // Redirect to dashboard
      router.push('/dashboard');
    } else if (status === 'unauthenticated') {
      // No session, redirect to login
      router.push('/auth');
    }
  }, [session, status, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#002A5C] to-[#000D2E]">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-white/20 border-t-[#00B38F] rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white text-lg">Completing sign in...</p>
      </div>
    </div>
  );
}
