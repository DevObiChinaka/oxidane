'use client';

import { useAuth } from '../contexts/AuthContext';

export default function UserProfile() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-lg">
      <h3 className="text-lg font-semibold text-green-800 mb-4">
        🎉 Authentication Successful!
      </h3>
      
      <div className="space-y-2 text-sm text-green-700">
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Display Name:</strong> {user.name || 'Not set'}</p>
        <p><strong>Image:</strong> {user.image || 'Not set'}</p>
      </div>

      <button
        onClick={logout}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
      >
        Sign Out
      </button>
    </div>
  );
}