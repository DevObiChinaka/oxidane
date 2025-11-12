'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  generateTelegramCode, 
  checkTelegramStatus, 
  verifyTelegramUsername, 
  confirmTelegramVerification 
} from '@/lib/api/payment';

interface TelegramVerificationProps {
  onVerified?: () => void;
  onError?: (error: string) => void;
  showInline?: boolean;
  autoStart?: boolean;
}

type VerificationStep = 'initial' | 'bot' | 'username' | 'confirm';

export default function TelegramVerification({
  onVerified,
  onError,
  showInline = false,
  autoStart = true
}: TelegramVerificationProps) {
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [botUrl, setBotUrl] = useState<string>('');
  const [botUsername, setBotUsername] = useState<string>('');
  const [expiresAt, setExpiresAt] = useState<string>('');
  const [isVerified, setIsVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string>('');
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [copied, setCopied] = useState(false);
  
  // New states for username entry flow
  const [currentStep, setCurrentStep] = useState<VerificationStep>('initial');
  const [telegramUsername, setTelegramUsername] = useState<string>('');
  const [confirmationCode, setConfirmationCode] = useState<string>('');
  const [codeSent, setCodeSent] = useState(false);

  // Generate verification code and open deep link
  const generateCode = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Check if auth token exists before making API call
      if (typeof window !== 'undefined') {
        let token = localStorage.getItem('user_auth_token');
        
        // Fallback to access_token if user_auth_token not found
        if (!token) {
          token = localStorage.getItem('access_token');
          if (token) {
            // Auto-migrate
            localStorage.setItem('user_auth_token', token);
            console.log('🔧 Auto-migrated access_token to user_auth_token');
          }
        }
        
        console.log('Token check:', token ? 'Token exists' : 'No token');
        if (!token) {
          throw new Error('Please log in to verify your Telegram account');
        }
      }
      
      console.log('Calling generateTelegramCode...');
      const data = await generateTelegramCode();
      console.log('Telegram code generated:', data);
      
      // Check if already verified (success response)
      if (data.already_verified || data.telegram_verified) {
        console.log('✅ Telegram already verified');
        setIsVerified(true);
        onVerified?.();
        setLoading(false);
        return;
      }
      
      setVerificationCode(data.verification_code || '');
      setBotUrl(data.deep_link || '');
      setBotUsername(data.bot_username || '');
      setExpiresAt(data.expires_at || '');
      
      // Calculate time left (5 minutes)
      if (data.expires_at) {
        const expires = new Date(data.expires_at).getTime();
        const now = Date.now();
        setTimeLeft(Math.max(0, Math.floor((expires - now) / 1000)));
      }
      
      // Show verification code and bot instructions (Option C flow)
      setCurrentStep('bot');
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate verification code';
      
      // Check if already verified (case-insensitive) - treat as SUCCESS, not error
      if (errorMessage.toLowerCase().includes('already verified') || 
          errorMessage.toLowerCase().includes('telegram already verified')) {
        console.log('✅ Telegram already verified, showing success state');
        // User is already verified, just check status and show success
        try {
          const status = await checkTelegramStatus();
          if (status.telegram_verified) {
            setIsVerified(true);
            onVerified?.();
            setLoading(false);
            return; // Success - no error to show
          }
        } catch (statusErr) {
          // Even if status check fails, we know they're verified from the error message
          setIsVerified(true);
          onVerified?.();
          setLoading(false);
          return; // Success - no error to show
        }
      }
      
      // Only log as error if it's NOT the "already verified" case
      console.error('Telegram verification error:', err);
      
      // Check if token expired
      if (errorMessage.includes('token') && errorMessage.includes('expired')) {
        setError('Your session has expired. Please log in again.');
        onError?.('Your session has expired. Please log in again.');
        // Clear expired token
        if (typeof window !== 'undefined') {
          localStorage.removeItem('user_auth_token');
          localStorage.removeItem('access_token');
        }
      } else {
        setError(errorMessage);
        onError?.(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [onError]);

  // Open Telegram deep link
  const openTelegramBot = () => {
    if (botUsername && verificationCode) {
      // Create deep link with START parameter
      const username = botUsername.replace('@', '');
      const deepLink = `https://t.me/${username}?start=VERIFY_${verificationCode}`;
      window.open(deepLink, '_blank');
    }
  };

  // Submit username for verification
  const handleUsernameSubmit = async () => {
    if (!telegramUsername.trim()) {
      setError('Please enter your Telegram username');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const data = await verifyTelegramUsername(verificationCode, telegramUsername);
      
      if (data.success) {
        setCodeSent(true);
        setCurrentStep('confirm');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to verify username';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Confirm verification code
  const handleConfirmCode = async () => {
    if (!confirmationCode.trim()) {
      setError('Please enter the confirmation code');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const data = await confirmTelegramVerification(verificationCode, confirmationCode);
      
      if (data.success) {
        setIsVerified(true);
        onVerified?.();
      } else {
        setError(data.message || 'Invalid confirmation code');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to confirm code';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
      const timer = setTimeout(async () => {
        // First check if already verified
        try {
          const status = await checkTelegramStatus();
          if (status.telegram_verified) {
            setIsVerified(true);
            onVerified?.();
            return; // Don't generate code if already verified
          }
          
          // Not verified yet, generate code
          generateCode();
        } catch (err) {
          console.log('Status check failed:', err);
          // If status check fails, still try to generate code
          // The generate endpoint will return the proper error if already verified
          generateCode();
        }
      }, 200);
      
      return () => clearTimeout(timer);
    }
  }, [autoStart, generateCode, onVerified]);

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
      setCopied(true);
      setTimeout(() => setCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (isVerified) {
    return (
      <div className="text-center py-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-50 dark:bg-green-900/20 rounded-full mb-4">
          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          🎉 Telegram Verified!
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Your Telegram account is now connected and ready
        </p>
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-xs text-green-800 dark:text-green-200 mb-2 font-medium">
            ✅ What happens next?
          </p>
          <ul className="text-xs text-green-700 dark:text-green-300 space-y-1 text-left">
            <li>• You'll be automatically added to exclusive Telegram groups</li>
            <li>• Access to course materials and community discussions</li>
            <li>• Real-time updates and notifications</li>
            <li>• Direct support from mentors and instructors</li>
          </ul>
        </div>
      </div>
    );
  }

  if (loading && !verificationCode) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#00B38F] mb-4"></div>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Preparing verification...
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Setting up your secure verification code
        </p>
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
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          Connect Your Telegram Account
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
          Quick and easy - just 2 simple steps!
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-500">
          Get instant access to exclusive course groups and community
        </p>
      </div>

      {/* Progress Indicator - Simplified for Option C */}
      {currentStep === 'bot' && verificationCode && (
        <div className="flex items-center justify-center mb-6">
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-blue-50 dark:bg-blue-900/20 rounded-full border border-blue-200 dark:border-blue-700">
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold animate-pulse">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <span className="text-sm font-semibold">Waiting for verification in Telegram...</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Step 1: Open Bot */}
      {currentStep === 'bot' && (
        <div className="space-y-4">
          {/* Show Verification Code Prominently */}
          <div className="bg-gradient-to-r from-emerald-50 to-blue-50 dark:from-emerald-900/20 dark:to-blue-900/20 border-2 border-emerald-200 dark:border-emerald-800 rounded-lg p-6 text-center">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Your Verification Code
            </p>
            <div className="bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-3 relative group">
              <p className="text-3xl font-bold font-mono tracking-widest text-emerald-600 dark:text-emerald-400 select-all">
                {verificationCode}
              </p>
              <button
                onClick={copyToClipboard}
                className={`absolute top-2 right-2 p-2 rounded-lg transition-all ${
                  copied 
                    ? 'bg-emerald-100 dark:bg-emerald-900 opacity-100' 
                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 opacity-0 group-hover:opacity-100'
                }`}
                title={copied ? "Copied!" : "Copy code"}
              >
                {copied ? (
                  <svg className="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
            <div className="flex items-center justify-center gap-2 text-xs text-gray-600 dark:text-gray-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Expires in {formatTimeLeft(timeLeft)}</span>
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="mb-4">
              <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center gap-2">
                <span className="flex items-center justify-center w-6 h-6 bg-blue-600 text-white rounded-full text-xs font-bold">1</span>
                Open Telegram Bot
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200 mb-3">
                Click the button below to open {botUsername || 'our bot'} in Telegram
              </p>
            </div>
            
            <button
              onClick={openTelegramBot}
              disabled={!botUsername || !verificationCode}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-[#0088cc] hover:bg-[#0077b3] text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
              Open {botUsername || 'Telegram Bot'}
            </button>
          </div>

          <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
            <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-100 mb-2 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 bg-emerald-600 text-white rounded-full text-xs font-bold">2</span>
              Type Your Code in Telegram
            </p>
            <p className="text-sm text-emerald-800 dark:text-emerald-200 mb-3">
              After opening the bot and clicking START, type or paste your code:
            </p>
            <div className="bg-white dark:bg-gray-800 rounded p-3 mb-3 border border-emerald-200 dark:border-emerald-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 font-mono">Type in Telegram chat:</p>
              <p className="text-lg font-bold font-mono text-gray-900 dark:text-white select-all">
                {verificationCode}
              </p>
            </div>
            <ul className="text-xs text-emerald-700 dark:text-emerald-300 space-y-1.5 ml-4 list-disc">
              <li>Click START button when you open the bot</li>
              <li>Simply type or paste the code above</li>
              <li>The bot will verify instantly!</li>
            </ul>
          </div>
          
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              💡 This page will automatically detect when you're verified
            </p>
          </div>
        </div>
      )}

      {/* Timer - Show below code display */}
      {verificationCode && timeLeft > 0 && currentStep === 'bot' && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
              Code expires in <span className="text-emerald-600 dark:text-emerald-400 font-mono">{formatTimeLeft(timeLeft)}</span>
            </p>
          </div>
        </div>
      )}
      {timeLeft === 0 && verificationCode && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-600 dark:text-red-400">
              Code expired.{' '}
              <button onClick={generateCode} className="underline font-semibold hover:text-red-700 dark:hover:text-red-300">
                Generate new code
              </button>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
