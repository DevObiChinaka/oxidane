'use client';

import { useSession, signOut } from 'next-auth/react';

export default function NewUserProfile() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="p-4 bg-gray-100 rounded-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-300 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
        <p className="text-blue-800">Please sign in to access your account.</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {session.user?.image && (
            <img
              src={session.user.image}
              alt="Profile"
              className="w-10 h-10 rounded-full"
            />
          )}
          <div>
            <p className="font-medium text-green-900">
              Welcome, {session.user?.name || session.user?.email}!
            </p>
            <p className="text-sm text-green-700">
              {session.user?.email}
            </p>
            {session.provider && (
              <p className="text-xs text-green-600">
                Signed in via {session.provider}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => signOut()}
          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
        >
          Sign Out
        </button>
      </div>
      
      {/* Debug info for development */}
      {process.env.NODE_ENV === 'development' && (
        <details className="mt-3">
          <summary className="text-xs text-green-600 cursor-pointer">
            Session Details (Dev Only)
          </summary>
          <pre className="mt-2 text-xs bg-green-100 p-2 rounded overflow-auto">
            {JSON.stringify(session, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}