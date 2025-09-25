'use client';

import { useState, useEffect } from 'react';
import { signup, login, signInWithGoogle, handleRedirectResult } from '../auth';

export default function AuthForm() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [debugInfo, setDebugInfo] = useState('');

  // Handle redirect result on component mount
  useEffect(() => {
    const checkRedirectResult = async () => {
      const wasAttemptingSignIn = localStorage.getItem('googleSignInAttempt');
      
      if (wasAttemptingSignIn) {
        setLoading(true);
        setDebugInfo('Checking for Google sign-in result...');
        
        try {
          const user = await handleRedirectResult();
          if (user) {
            setDebugInfo(`✅ Success! Signed in as: ${user.email}`);
            setError('');
            console.log('Google sign-in successful via redirect!', user);
            localStorage.removeItem('googleSignInAttempt');
            
            // Show success message for a longer time
            setTimeout(() => setDebugInfo(''), 10000);
          } else {
            setDebugInfo('No sign-in result found');
            setTimeout(() => setDebugInfo(''), 3000);
          }
        } catch (error) {
          console.error('Redirect result error:', error);
          setError('Authentication failed. Please try again.');
          setDebugInfo(`❌ Redirect error: ${error}`);
          setTimeout(() => setDebugInfo(''), 5000);
        } finally {
          setLoading(false);
          localStorage.removeItem('googleSignInAttempt');
        }
      }
    };

    checkRedirectResult();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await signup(email, password);
      }
      console.log('Authentication successful!');
    } catch (err: any) {
      console.error('Auth error:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError('');
    setDebugInfo('Redirecting to Google for authentication...');

    try {
      console.log('Starting Google Sign-in with redirect...');
      
      // Store that we're attempting sign-in so we can show appropriate message
      localStorage.setItem('googleSignInAttempt', 'true');
      
      await signInWithGoogle(); // This will trigger redirect
      
      // This won't be reached due to redirect, but just in case
      setDebugInfo('Redirecting to Google...');
      
    } catch (err: any) {
      console.error('Google sign-in error:', err);
      setDebugInfo(`Error: ${err.message || err.code || 'Unknown error'}`);
      setError(getErrorMessage(err));
      setLoading(false);
      localStorage.removeItem('googleSignInAttempt');
    }
  };

  const getErrorMessage = (error: any) => {
    switch (error.code) {
      case 'auth/user-not-found':
        return 'No account found with this email.';
      case 'auth/wrong-password':
        return 'Incorrect password.';
      case 'auth/email-already-in-use':
        return 'An account with this email already exists.';
      case 'auth/weak-password':
        return 'Password should be at least 6 characters.';
      case 'auth/invalid-email':
        return 'Invalid email address.';
      case 'auth/popup-blocked':
        return 'Popup was blocked. Please allow popups and try again.';
      case 'auth/popup-closed-by-user':
        return 'Sign-in was cancelled.';
      case 'auth/network-request-failed':
        return 'Network error. Please check your connection.';
      default:
        return error.message || 'An error occurred during authentication.';
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center text-gray-900">
        {isLogin ? 'Sign In' : 'Sign Up'}
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {debugInfo && (
        <div className="mb-4 p-3 bg-blue-100 border border-blue-400 text-blue-700 rounded text-sm">
          <strong>Debug:</strong> {debugInfo}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Sign Up')}
        </button>
      </form>

      <div className="mt-4">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or</span>
          </div>
        </div>

        <button
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="mt-4 w-full flex justify-center items-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {loading ? 'Signing in...' : 'Sign in with Google'}
        </button>
      </div>

      <div className="mt-4 text-center">
        <button
          onClick={() => setIsLogin(!isLogin)}
          disabled={loading}
          className="text-blue-600 hover:text-blue-500 text-sm disabled:opacity-50"
        >
          {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  );
}