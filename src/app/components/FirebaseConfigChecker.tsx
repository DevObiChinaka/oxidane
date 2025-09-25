'use client';

import { useState } from 'react';

export default function FirebaseConfigChecker() {
  const [showDetails, setShowDetails] = useState(false);

  const checkAuthDomain = async () => {
    try {
      // Don't test the hosting domain - test the auth service directly
      console.log('🔍 Testing Firebase Auth service connectivity...');
      
      // Try to get the current user (this will test if auth service is reachable)
      const { onAuthStateChanged } = await import('firebase/auth');
      const { auth } = await import('../firebase');
      
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        console.log('✅ Firebase Auth service is reachable');
        console.log('Current user:', user ? user.email : 'No user signed in');
        unsubscribe();
      });
      
    } catch (error) {
      console.error('❌ Firebase Auth service test failed:', error);
    }
  };

  return (
    <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-blue-900">Firebase Configuration Checker</h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-blue-600 hover:text-blue-800"
        >
          {showDetails ? 'Hide' : 'Show'} Details
        </button>
      </div>
      
      {showDetails && (
        <div className="mt-4 space-y-4">
          <div className="text-sm text-blue-800">
            <h4 className="font-medium mb-2">Firebase Console Checklist:</h4>
            <ul className="space-y-1 list-disc list-inside">
              <li>✅ Google provider enabled in Authentication → Sign-in method</li>
              <li>✅ Authorized domains include: localhost, oxidane-dd474.firebaseapp.com</li>
              <li>✅ OAuth consent screen configured (if using custom domain)</li>
              <li>✅ Web app configuration matches .env.local values</li>
            </ul>
          </div>
          
          <div className="text-sm text-blue-800">
            <h4 className="font-medium mb-2">Current Configuration:</h4>
            <div className="bg-blue-100 p-2 rounded font-mono text-xs">
              <div>Auth Domain: {process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN}</div>
              <div>Project ID: {process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID}</div>
              <div>App ID: {process.env.NEXT_PUBLIC_FIREBASE_APP_ID}</div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={checkAuthDomain}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              Test Auth Service
            </button>
            <button
              onClick={() => {
                console.log('Environment variables:');
                console.log('API Key:', process.env.NEXT_PUBLIC_FIREBASE_API_KEY ? 'Present' : 'Missing');
                console.log('Auth Domain:', process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN);
                console.log('Project ID:', process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID);
                console.log('App ID:', process.env.NEXT_PUBLIC_FIREBASE_APP_ID);
              }}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              Log Config
            </button>
          </div>
        </div>
      )}
    </div>
  );
}