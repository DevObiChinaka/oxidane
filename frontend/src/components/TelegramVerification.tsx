'use client';

import { useState, useEffect, useCallback } from 'react';
import { generateTelegramCode, checkTelegramStatus } from '@/lib/api/payment';

interface TelegramVerificationProps {
  onVerified?: () => void;
  onError?: (error: string) => void;
  showInline?: boolean;
  autoStart?: boolean;
}

export default function TelegramVerification({
  onVerified,
  onError,
  showInline = false,
  autoStart = true
}: TelegramVerificationProps) {
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [botUrl, setBotUrl] = useState<string>('');
  const [expiresAt, setExpiresAt] = useState<string>('');
  const [isVerified, setIsVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string>('');
  const [timeLeft, setTimeLeft] = useState<number>(0);

  // Generate verification code
  const generateCode = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Check if auth token exists before making API call
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('user_auth_token');
        if (!token) {
          throw new Error('Please log in to verify your Telegram account');
        }
      }
      
      const data = await generateTelegramCode();
      
      setVerificationCode(data.verification_code);
      setBotUrl(data.bot_url);
      setExpiresAt(data.expires_at);
      
      // Calculate time left
      const expires = new Date(data.expires_at).getTime();
      const now = Date.now();
      setTimeLeft(Math.max(0, Math.floor((expires - now) / 1000)));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate verification code';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [onError]);

  // Check verification status
  const checkStatus = useCallback(async () => {
    try {
      setChecking(true);
      const data = await checkTelegramStatus();
      
      if (data.telegram_verified) {
        setIsVerified(true);
        onVerified?.();
      }
    } catch (err) {
      console.error('Error checking Telegram status:', err);
    } finally {
      setChecking(false);
    }
  }, [onVerified]);

  // Auto-generate code on mount with delay to ensure auth is ready
  useEffect(() => {
    if (autoStart) {
      // Add 200ms delay to ensure localStorage auth token is set
      const timer = setTimeout(() => {
        generateCode();
      }, 200);
      
      return () => clearTimeout(timer);
    }
  }, [autoStart, generateCode]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  // Poll for verification status
  useEffect(() => {
    if (!verificationCode || isVerified) return;

    const pollInterval = setInterval(() => {
      checkStatus();
    }, 3000); // Check every 3 seconds

    return () => clearInterval(pollInterval);
  }, [verificationCode, isVerified, checkStatus]);

  // Format time left
  const formatTimeLeft = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Copy to clipboard
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(verificationCode);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (isVerified) {
    return (
      <div className="text-center py-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-50 rounded-full mb-4">
          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Telegram Verified! 
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Your Telegram account is connected and ready
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#00B38F] mb-4"></div>
        <p className="text-sm text-gray-600 dark:text-gray-400">Generating verification code...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-50 rounded-full mb-4">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Verification Failed
        </h3>
        <p className="text-sm text-red-600 mb-4">{error}</p>
        <button
          onClick={generateCode}
          className="px-6 py-2.5 bg-[#00B38F] text-white rounded-lg hover:bg-[#00A87D] transition-colors text-sm font-medium"
        >
          Try Again
        </button>
      </div>
    );
  }

  const containerClass = showInline 
    ? "border border-gray-200 dark:border-gray-700 rounded-lg p-6"
    : "";

  return (
    <div className={containerClass}>
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-full mb-4">
          <svg className="w-8 h-8 text-[#0088cc]" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Verify Your Telegram
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Connect your Telegram account to access exclusive groups
        </p>
      </div>

      {/* Instructions */}
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mb-6">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Follow these steps:
        </h4>
        <ol className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li className="flex items-start">
            <span className="inline-flex items-center justify-center w-5 h-5 bg-[#00B38F] text-white rounded-full text-xs font-bold mr-2 mt-0.5 flex-shrink-0">
              1
            </span>
            <span>Click the button below to open our Telegram bot</span>
          </li>
          <li className="flex items-start">
            <span className="inline-flex items-center justify-center w-5 h-5 bg-[#00B38F] text-white rounded-full text-xs font-bold mr-2 mt-0.5 flex-shrink-0">
              2
            </span>
            <span>Send your verification code to the bot</span>
          </li>
          <li className="flex items-start">
            <span className="inline-flex items-center justify-center w-5 h-5 bg-[#00B38F] text-white rounded-full text-xs font-bold mr-2 mt-0.5 flex-shrink-0">
              3
            </span>
            <span>Wait for automatic verification (takes a few seconds)</span>
          </li>
        </ol>
      </div>

      {/* Verification Code */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Your Verification Code
        </label>
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={verificationCode}
              readOnly
              className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-center text-2xl font-mono font-bold tracking-wider text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={copyToClipboard}
            className="px-4 py-3 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
            title="Copy to clipboard"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
        
        {/* Timer */}
        {timeLeft > 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            Expires in {formatTimeLeft(timeLeft)}
          </p>
        )}
        {timeLeft === 0 && verificationCode && (
          <p className="text-xs text-red-500 mt-2 text-center">
            Code expired. 
            <button onClick={generateCode} className="underline ml-1">
              Generate new code
            </button>
          </p>
        )}
      </div>

      {/* Bot Button */}
      <a
        href={botUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="block w-full py-3 px-6 bg-[#0088cc] hover:bg-[#0077b5] text-white rounded-lg font-medium text-center transition-colors mb-4"
      >
        <div className="flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
          </svg>
          <span>Open Telegram Bot</span>
        </div>
      </a>

      {/* Status Indicator */}
      {checking && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#00B38F]"></div>
            <span>Checking verification status...</span>
          </div>
        </div>
      )}
    </div>
  );
}
