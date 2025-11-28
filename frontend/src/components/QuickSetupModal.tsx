'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import TelegramVerification from '@/components/TelegramVerification';
import { API_ENDPOINTS } from '@/config/api';

interface QuickSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  redirectUrl?: string;
  onComplete?: () => void;
}

export default function QuickSetupModal({
  isOpen,
  onClose,
  redirectUrl,
  onComplete
}: QuickSetupModalProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setError('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleNameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.first_name.trim()) {
      setError('Please enter your first name');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');

      // Update user profile
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.auth.profile, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: formData.first_name,
          last_name: formData.last_name,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      // Update local storage
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      user.first_name = formData.first_name;
      user.last_name = formData.last_name;
      localStorage.setItem('user', JSON.stringify(user));

      // Move to next step
      setCurrentStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTelegramVerified = () => {
    // Telegram verification complete - proceed to checkout
    const planId = searchParams.get('plan');
    const finalRedirect = redirectUrl || (planId ? `/checkout?plan=${planId}` : '/dashboard');
    
    onComplete?.();
    router.push(finalRedirect);
  };

  const handleSkip = () => {
    // Skip setup and go to redirect URL
    const planId = searchParams.get('plan');
    const finalRedirect = redirectUrl || (planId ? `/checkout?plan=${planId}` : '/dashboard');
    
    onClose();
    router.push(finalRedirect);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-900 shadow-2xl transition-all">
          {/* Progress Bar */}
          <div className="h-1 bg-gray-200 dark:bg-gray-700">
            <div 
              className="h-full bg-gradient-to-r from-[#00B38F] to-[#00B39F] transition-all duration-300"
              style={{ width: `${(currentStep / 2) * 100}%` }}
            />
          </div>

          {/* Header */}
          <div className="px-6 pt-6 pb-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {currentStep === 1 ? 'Complete Your Profile' : 'Connect Telegram'}
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Step {currentStep} of 2
            </p>
          </div>

          {/* Content */}
          <div className="px-6 pb-6">
            {currentStep === 1 ? (
              /* Step 1: Name Input */
              <form onSubmit={handleNameSubmit} className="space-y-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900 dark:text-white"
                    placeholder="Enter your first name"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900 dark:text-white"
                    placeholder="Enter your last name"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleSkip}
                    className="flex-1 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-medium"
                  >
                    Skip for Now
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-lg hover:opacity-90 transition-opacity font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                        Saving...
                      </span>
                    ) : (
                      'Continue'
                    )}
                  </button>
                </div>
              </form>
            ) : (
              /* Step 2: Telegram Verification */
              <div>
                <TelegramVerification
                  onVerified={handleTelegramVerified}
                  onError={(error) => setError(error)}
                  showInline={false}
                  autoStart={true}
                />

                <div className="mt-4">
                  <button
                    onClick={handleSkip}
                    className="w-full px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-medium text-sm"
                  >
                    I'll do this later
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer Info */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
              {currentStep === 1 
                ? 'We need your name to personalize your experience'
                : 'Telegram verification is required to access premium signals and groups'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
