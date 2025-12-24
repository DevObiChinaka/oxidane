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
  theme?: 'light' | 'dark';
}

type VerificationStep = 'initial' | 'bot' | 'username' | 'confirm';

export default function TelegramVerification({
  onVerified,
  onError,
  showInline = false,
  autoStart = true,
  theme = 'light'
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
          }
        }
        
        if (!token) {
          throw new Error('Please log in to verify your Telegram account');
        }
      }
      
      const data = await generateTelegramCode();
      
      // Check if already verified (success response)
      if (data.already_verified || data.telegram_verified) {
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
      
      // Only show error if it's NOT the "already verified" case
      
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
      
      // Check for verification errors first
      if (data.verification_error) {
        setError(data.verification_error);
        onError?.(data.verification_error);
        setChecking(false);
        return;
      }
      
      if (data.telegram_verified) {
        setIsVerified(true);
        onVerified?.();
      }
    } catch (err) {
      // Silent fail
    } finally {
      setChecking(false);
    }
  }, [onVerified, onError]);

  // Auto-generate code on mount with delay to ensure auth is ready
  useEffect(() => {
    if (autoStart) {
      // Add 200ms delay to ensure localStorage auth token is set
      const timer = setTimeout(async () => {
        // First check if already verified
        try {
          const status = await checkTelegramStatus();
          
          // Check for verification errors
          if (status.verification_error) {
            setError(status.verification_error);
            onError?.(status.verification_error);
            return;
          }
          
          if (status.telegram_verified) {
            setIsVerified(true);
            onVerified?.();
            return; // Don't generate code if already verified
          }
          
          // Not verified yet, generate code
          generateCode();
        } catch (err) {
          // Continue checking
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
          }
  };

  if (isVerified) {
    return (
      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-green-50 rounded-full mb-4">
          <svg className="w-7 h-7 text-[#00B38F]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Telegram Verified
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Your account is connected and ready
        </p>
      </div>
    );
  }

  if (loading && !verificationCode) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-[#00B38F] mb-4"></div>
        <p className="text-sm text-gray-600">
          Generating verification link...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-6">
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
        <button
          onClick={generateCode}
          className="px-5 py-2 bg-[#000856] text-white rounded-lg hover:bg-[#000856]/90 transition-colors text-sm font-medium"
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


      {/* Waiting indicator */}
      {currentStep === 'bot' && verificationCode && (
        <div className="flex items-center justify-center mb-6">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${
            theme === 'dark' 
              ? 'bg-blue-500/10 border-blue-500/30' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
              theme === 'dark' ? 'border-blue-400' : 'border-blue-600'
            }`}></div>
            <span className={`text-sm ${theme === 'dark' ? 'text-blue-100' : 'text-gray-700'}`}>
              Waiting for verification...
            </span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Verification Steps */}
      {currentStep === 'bot' && (
        <div className="space-y-4">
          {/* Step 1: Open Bot */}
          <div className={`border rounded-lg p-5 ${
            theme === 'dark'
              ? 'border-white/20 bg-white/5'
              : 'border-gray-200 bg-white'
          }`}>
            <div className="flex items-start gap-3 mb-3">
              <div className="flex-shrink-0 w-6 h-6 bg-[#00B38F] text-white rounded-full flex items-center justify-center text-xs font-bold">
                1
              </div>
              <div className="flex-1">
                <h4 className={`font-medium mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Open Telegram Bot
                </h4>
                <p className={`text-sm mb-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  Click below to open {botUsername || 'our bot'}
                </p>
                <button
                  onClick={openTelegramBot}
                  disabled={!botUsername || !verificationCode}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#0088cc] hover:bg-[#0077b3] text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
                  </svg>
                  Open Telegram Bot
                </button>
                
                {/* Web User Instructions */}
                <div className={`mt-3 pt-3 border-t ${
                  theme === 'dark' ? 'border-white/10' : 'border-gray-200'
                }`}>
                  <p className={`text-xs mb-2 ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    <span className={`font-medium ${
                      theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>Using Telegram Web?</span> Click START when the bot opens, then continue to Step 2.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Enter Code */}
          <div className={`border rounded-lg p-5 ${
            theme === 'dark'
              ? 'border-white/20 bg-white/5'
              : 'border-gray-200 bg-white'
          }`}>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-[#00B38F] text-white rounded-full flex items-center justify-center text-xs font-bold">
                2
              </div>
              <div className="flex-1">
                <h4 className={`font-medium mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Send Your Code
                </h4>
                <p className={`text-sm mb-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  After clicking START, type this code in the chat:
                </p>
                <div className={`border rounded-lg p-4 mb-2 ${
                  theme === 'dark'
                    ? 'bg-[#000856]/30 border-[#00B38F]/30'
                    : 'bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <code className={`text-xl font-mono font-bold ${
                      theme === 'dark' ? 'text-white' : 'text-[#000856]'
                    }`}>
                      {verificationCode}
                    </code>
                    <button
                      onClick={copyToClipboard}
                      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                        theme === 'dark'
                          ? 'bg-[#00B38F] hover:bg-[#00A87D] text-white'
                          : 'bg-white border border-gray-200 hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </div>
                {timeLeft > 0 && (
                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                    Code expires in {formatTimeLeft(timeLeft)}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Expired code */}
      {timeLeft === 0 && verificationCode && (
        <div className="mt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-sm text-red-600 mb-2">
              Code expired
            </p>
            <button onClick={generateCode} className="text-sm text-red-700 font-medium hover:underline">
              Generate new code
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
