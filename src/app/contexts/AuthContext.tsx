'use client';

import { createContext, useContext } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { Session } from 'next-auth';

interface AuthContextType {
  session: Session | null;
  user: Session['user'] | null;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  
  const logout = async () => {
    await signOut({ callbackUrl: '/' });
  };

  const value = {
    session,
    user: session?.user || null,
    loading: status === 'loading',
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}