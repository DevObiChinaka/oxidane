'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  CreditCardIcon,
  UserGroupIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  SparklesIcon,
  ShieldCheckIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { apiGet, apiPost } from '@/lib/api';

interface BillingProfile {
  verified: boolean;
  telegram_username: string;
  telegram_user_id: string;
  verified_at: string | null;
  active_subscriptions: Array<{
    plan_name: string;
    plan_category: string;
    end_date: string;
    days_remaining: number;
    telegram_groups: string[];
  }>;
  has_pending_code: boolean;
}

export default function BillingPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'telegram' | 'subscriptions' | 'payment-methods'>('telegram');
  const [billingProfile, setBillingProfile] = useState<BillingProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBillingProfile();
  }, []);

  const fetchBillingProfile = async () => {
    try {
      setLoading(true);
      
      const response = await apiGet('/billing/telegram/status/');

      if (!response.ok) {
        throw new Error('Failed to fetch billing profile');
      }

      const data = await response.json();
      setBillingProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    {
      id: 'telegram' as const,
      name: 'Telegram',
      icon: UserGroupIcon,
      description: 'Connect your account',
      badge: billingProfile?.verified ? 'Verified' : 'Not Connected',
      badgeColor: billingProfile?.verified ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700',
    },
    {
      id: 'subscriptions' as const,
      name: 'Subscriptions',
      icon: DocumentTextIcon,
      description: 'Manage your plans',
      badge: billingProfile?.active_subscriptions.length || 0,
      badgeColor: 'bg-teal-100 text-teal-700',
    },
    {
      id: 'payment-methods' as const,
      name: 'Payment Methods',
      icon: CreditCardIcon,
      description: 'Saved cards & banks',
      badge: 'Coming Soon',
      badgeColor: 'bg-blue-100 text-blue-700',
    },
  ];

  if (loading) {
    return (
      <div className="ml-72 min-h-screen bg-gradient-to-br from-gray-50 to-teal-50/30">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-teal-200 border-t-[#00B38F] rounded-full animate-spin mx-auto"></div>
              <SparklesIcon className="w-6 h-6 text-[#00B38F] absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="mt-4 text-gray-700 font-medium">Loading your billing dashboard...</p>
            <p className="text-sm text-gray-500 mt-1">Please wait a moment</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ml-72 min-h-screen bg-gradient-to-br from-gray-50 to-teal-50/30">
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-[#00B38F] to-[#00A87D] rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/30">
              <CreditCardIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Billing & Account</h1>
              <p className="text-gray-600">Manage subscriptions, payments, and Telegram access</p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-2xl p-5 flex items-start shadow-sm">
            <ExclamationCircleIcon className="w-6 h-6 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-900 mb-1">Something went wrong</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-400 hover:text-red-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Verification Status Banner */}
        {billingProfile && !billingProfile.verified && (
          <div className="mb-6 bg-gradient-to-r from-orange-50 to-yellow-50 border-2 border-orange-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                  <ExclamationCircleIcon className="w-6 h-6 text-orange-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <h3 className="text-lg font-semibold text-orange-900 mb-1">Action Required: Connect Telegram</h3>
                <p className="text-orange-800 mb-3">
                  Your Telegram account isn't linked yet. Connect now to unlock premium group access and receive real-time trading signals.
                </p>
                <button
                  onClick={() => setActiveTab('telegram')}
                  className="inline-flex items-center px-5 py-2.5 bg-gradient-to-r from-orange-600 to-yellow-600 text-white font-medium rounded-xl hover:from-orange-700 hover:to-yellow-700 transition-all shadow-lg shadow-orange-500/30"
                >
                  <UserGroupIcon className="w-5 h-5 mr-2" />
                  Connect Telegram Now
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {billingProfile && billingProfile.verified && (
          <div className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                  <CheckCircleIcon className="w-7 h-7 text-green-600" />
                </div>
              </div>
              <div className="ml-4 flex-1">
                <h3 className="text-lg font-semibold text-green-900 mb-1">✅ Telegram Connected Successfully</h3>
                <p className="text-green-800">
                  Your account <span className="font-semibold">@{billingProfile.telegram_username}</span> is verified. 
                  You now have access to all premium groups based on your active subscriptions.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50/50">
            <nav className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex-1 py-5 px-6 text-center border-b-4 font-medium text-sm
                      transition-all duration-200 relative group
                      ${isActive
                        ? 'border-[#00B38F] bg-white'
                        : 'border-transparent hover:border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      <Icon className={`w-6 h-6 ${isActive ? 'text-[#00B38F]' : 'text-gray-400 group-hover:text-gray-600'}`} />
                      <div>
                        <div className={`font-semibold ${isActive ? 'text-gray-900' : 'text-gray-600'}`}>
                          {tab.name}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">{tab.description}</div>
                      </div>
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${tab.badgeColor}`}>
                        {tab.badge}
                      </span>
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === 'telegram' && (
              <TelegramVerificationSection 
                billingProfile={billingProfile} 
                onUpdate={fetchBillingProfile}
              />
            )}
            
            {activeTab === 'subscriptions' && (
              <SubscriptionsSection subscriptions={billingProfile?.active_subscriptions || []} />
            )}
            
            {activeTab === 'payment-methods' && (
              <PaymentMethodsSection />
            )}
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-6 bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-teal-100 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-[#00B38F]" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-semibold text-teal-900 mb-1">Need Help?</h3>
              <p className="text-sm text-teal-800 mb-3">
                If you encounter any issues with billing, subscriptions, or Telegram verification, our support team is here to assist you.
              </p>
              <button className="inline-flex items-center text-sm font-medium text-[#00B38F] hover:text-[#00A87D]">
                Contact Support
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Telegram Verification Section
function TelegramVerificationSection({ 
  billingProfile, 
  onUpdate 
}: { 
  billingProfile: BillingProfile | null;
  onUpdate: () => void;
}) {
  const [verificationCode, setVerificationCode] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [showUnlinkConfirm, setShowUnlinkConfirm] = useState(false);

  // Clear polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const generateCode = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiPost('/billing/telegram/generate-code/');

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to generate verification code');
      }

      const data = await response.json();
      setVerificationCode(data.verification_code);
      setExpiresAt(data.expires_at);
      
      // Start polling for verification status
      startPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate code');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
    const interval = setInterval(async () => {
      const response = await apiGet('/billing/telegram/status/');
      
      if (response.ok) {
        const data = await response.json();
        if (data.verified) {
          // Stop polling and update parent
          if (pollingInterval) clearInterval(pollingInterval);
          onUpdate();
        }
      }
    }, 3000); // Poll every 3 seconds
    
    setPollingInterval(interval);
  };

  const unlinkTelegram = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiPost('/billing/telegram/unlink/');

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to unlink Telegram');
      }

      setShowUnlinkConfirm(false);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unlink Telegram');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // If verified, show verification info
  if (billingProfile?.verified) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <CheckCircleIcon className="w-6 h-6 text-green-600 mr-2" />
              Telegram Account Verified
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Your account is linked and you have access to premium groups
            </p>
          </div>
          <button
            onClick={() => setShowUnlinkConfirm(true)}
            className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            Unlink Account
          </button>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Telegram Username</p>
              <p className="text-lg font-semibold text-gray-900">@{billingProfile.telegram_username}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">User ID</p>
              <p className="text-lg font-mono text-gray-900">{billingProfile.telegram_user_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Verified At</p>
              <p className="text-lg text-gray-900">
                {billingProfile.verified_at 
                  ? new Date(billingProfile.verified_at).toLocaleString()
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Active Groups</p>
              <p className="text-lg font-semibold text-green-600">
                {billingProfile.active_subscriptions.length} subscription(s)
              </p>
            </div>
          </div>
        </div>

        {/* Unlink Confirmation Modal */}
        {showUnlinkConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Unlink Telegram Account?</h3>
              <p className="text-gray-600 mb-6">
                You will lose access to all premium Telegram groups until you verify again.
                Are you sure you want to continue?
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowUnlinkConfirm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={unlinkTelegram}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? 'Unlinking...' : 'Yes, Unlink'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // If not verified, show verification flow
  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Link Your Telegram Account</h3>
        <p className="text-gray-600">
          Connect your Telegram account to access premium groups and receive real-time notifications.
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!verificationCode ? (
        <div className="text-center py-8">
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-8 max-w-md mx-auto">
            <UserGroupIcon className="w-16 h-16 text-blue-600 mx-auto mb-4" />
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Get Started</h4>
            <p className="text-gray-600 mb-6">
              Generate a verification code to link your Telegram account and unlock premium features.
            </p>
            <button
              onClick={generateCode}
              disabled={loading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Generating...' : 'Generate Verification Code'}
            </button>
          </div>
        </div>
      ) : (
        <div className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-200 rounded-lg p-6">
            <div className="flex items-start mb-4">
              <div className="bg-blue-600 rounded-full p-2 mr-3">
                <span className="text-white font-bold text-lg">1</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Your Verification Code</h4>
                <p className="text-sm text-gray-600">Copy this code - you'll need it for step 2</p>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <code className="text-2xl font-mono font-bold text-blue-600">{verificationCode}</code>
                <button
                  onClick={() => copyToClipboard(verificationCode)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Copy Code
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Expires: {expiresAt ? new Date(expiresAt).toLocaleString() : 'N/A'}
              </p>
            </div>

            <div className="flex items-start mb-4">
              <div className="bg-blue-600 rounded-full p-2 mr-3">
                <span className="text-white font-bold text-lg">2</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Open Telegram</h4>
                <p className="text-sm text-gray-600 mb-2">Search for and start a chat with:</p>
                <a 
                  href="https://t.me/OxiWorldBot" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors border border-blue-200"
                >
                  @OxiWorldBot
                  <svg className="w-4 h-4 ml-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                    <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                  </svg>
                </a>
              </div>
            </div>

            <div className="flex items-start">
              <div className="bg-blue-600 rounded-full p-2 mr-3">
                <span className="text-white font-bold text-lg">3</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Send Verification Command</h4>
                <p className="text-sm text-gray-600 mb-2">Type this command in the bot chat:</p>
                <div className="bg-white rounded-lg p-3 border border-blue-200">
                  <code className="text-sm font-mono text-gray-900">/verify {verificationCode}</code>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <div className="inline-flex items-center px-4 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
              <ArrowPathIcon className="w-5 h-5 text-yellow-600 animate-spin mr-2" />
              <span className="text-sm text-yellow-800 font-medium">
                Waiting for verification... (checking every 3 seconds)
              </span>
            </div>
          </div>

          <div className="mt-4 text-center">
            <button
              onClick={() => {
                setVerificationCode(null);
                setExpiresAt(null);
                if (pollingInterval) clearInterval(pollingInterval);
              }}
              className="text-sm text-gray-600 hover:text-gray-900 underline"
            >
              Cancel and generate new code
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Subscriptions Section
function SubscriptionsSection({ 
  subscriptions 
}: { 
  subscriptions: Array<{
    plan_name: string;
    plan_category: string;
    end_date: string;
    days_remaining: number;
    telegram_groups: string[];
  }>;
}) {
  const router = useRouter();

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'mentorship': 'blue',
      'signals': 'teal',
      'vip': 'yellow',
    };
    return colors[category] || 'gray';
  };

  const getCategoryBadge = (category: string) => {
    const color = getCategoryColor(category);
    const bgColors: Record<string, string> = {
      'blue': 'bg-blue-100 text-blue-800',
      'teal': 'bg-teal-100 text-teal-800',
      'yellow': 'bg-yellow-100 text-yellow-800',
      'gray': 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${bgColors[color]}`}>
        {category.toUpperCase()}
      </span>
    );
  };

  if (subscriptions.length === 0) {
    return (
      <div className="text-center py-12">
        <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Subscriptions</h3>
        <p className="text-gray-600 mb-6">
          You don't have any active subscriptions yet. Browse our pricing plans to get started.
        </p>
        <button
          onClick={() => router.push('/pricing')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          View Pricing Plans
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Active Subscriptions</h3>
        <p className="text-gray-600">
          Manage your active subscription plans and access
        </p>
      </div>

      <div className="space-y-4">
        {subscriptions.map((subscription, index) => (
          <div
            key={index}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {subscription.plan_name}
                  </h4>
                  {getCategoryBadge(subscription.plan_category)}
                </div>
                <p className="text-sm text-gray-600">
                  Access to {subscription.telegram_groups.length} premium group(s)
                </p>
              </div>
              
              <div className="text-right">
                <div className={`text-2xl font-bold ${
                  subscription.days_remaining > 7 
                    ? 'text-green-600' 
                    : subscription.days_remaining > 3 
                    ? 'text-yellow-600' 
                    : 'text-red-600'
                }`}>
                  {subscription.days_remaining}
                </div>
                <p className="text-xs text-gray-600">days left</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">Expires On</p>
                <p className="text-sm font-medium text-gray-900">
                  {new Date(subscription.end_date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
              
              <div>
                <p className="text-xs text-gray-500 mb-1">Access Groups</p>
                <div className="flex flex-wrap gap-1">
                  {subscription.telegram_groups.map((group, idx) => (
                    <span 
                      key={idx}
                      className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {group}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <p className="text-xs text-gray-500 mb-1">Status</p>
                <div className="flex items-center">
                  <CheckCircleIcon className="w-4 h-4 text-green-600 mr-1" />
                  <span className="text-sm font-medium text-green-600">Active</span>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => router.push('/pricing')}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Renew Subscription
              </button>
              <button
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Manage
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">Auto-Renewal Information</h4>
            <p className="text-sm text-blue-700">
              Your subscriptions will automatically renew unless cancelled. You'll receive an email reminder 3 days before renewal.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Payment Methods Section
function PaymentMethodsSection() {
  const [paymentMethods, setPaymentMethods] = useState<Array<{
    id: string;
    payment_type: string;
    card_last4: string;
    card_brand: string;
    card_exp_month: string;
    card_exp_year: string;
    bank_name: string;
    is_default: boolean;
    is_active: boolean;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [showAddMethod, setShowAddMethod] = useState(false);

  // Placeholder data for demo (remove when API is integrated)
  useEffect(() => {
    // TODO: Fetch payment methods from API
    // For now, showing empty state
    setPaymentMethods([]);
  }, []);

  const getCardIcon = (brand: string) => {
    const icons: Record<string, string> = {
      'visa': '💳',
      'mastercard': '💳',
      'verve': '💳',
    };
    return icons[brand.toLowerCase()] || '💳';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Payment Methods</h3>
          <p className="text-gray-600">
            Manage your saved payment methods for quick checkout
          </p>
        </div>
        <button
          onClick={() => setShowAddMethod(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Payment Method
        </button>
      </div>

      {paymentMethods.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <CreditCardIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Payment Methods</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Add a payment method to enable quick checkout and auto-renewal for your subscriptions.
          </p>
          <button
            onClick={() => setShowAddMethod(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors inline-flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Your First Payment Method
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              className={`bg-white border-2 rounded-lg p-6 transition-all ${
                method.is_default 
                  ? 'border-blue-500 shadow-md' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className="text-4xl">{getCardIcon(method.card_brand)}</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-lg font-semibold text-gray-900">
                        {method.payment_type === 'card' 
                          ? `${method.card_brand} •••• ${method.card_last4}`
                          : method.bank_name}
                      </h4>
                      {method.is_default && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                          Default
                        </span>
                      )}
                    </div>
                    {method.payment_type === 'card' && (
                      <p className="text-sm text-gray-600">
                        Expires {method.card_exp_month}/{method.card_exp_year}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {!method.is_default && (
                    <button
                      className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      Set as Default
                    </button>
                  )}
                  <button
                    className="px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Security Notice */}
      <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-green-900 mb-1">Secure Payment Processing</h4>
            <p className="text-sm text-green-700">
              All payment information is encrypted and securely stored by Paystack. We never store your full card details on our servers.
            </p>
          </div>
        </div>
      </div>

      {/* Add Payment Method Modal */}
      {showAddMethod && (
        <AddPaymentMethodModal onClose={() => setShowAddMethod(false)} />
      )}
    </div>
  );
}

// Add Payment Method Modal Component
function AddPaymentMethodModal({ onClose }: { onClose: () => void }) {
  const [paymentType, setPaymentType] = useState<'card' | 'bank'>('card');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">Add Payment Method</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Payment Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Payment Method Type
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setPaymentType('card')}
                className={`p-4 border-2 rounded-lg text-left transition-all ${
                  paymentType === 'card'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <CreditCardIcon className={`w-8 h-8 mb-2 ${
                  paymentType === 'card' ? 'text-blue-600' : 'text-gray-400'
                }`} />
                <div className="font-medium text-gray-900">Card</div>
                <div className="text-xs text-gray-600">Debit or Credit Card</div>
              </button>
              
              <button
                onClick={() => setPaymentType('bank')}
                className={`p-4 border-2 rounded-lg text-left transition-all ${
                  paymentType === 'bank'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <svg className={`w-8 h-8 mb-2 ${
                  paymentType === 'bank' ? 'text-blue-600' : 'text-gray-400'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                </svg>
                <div className="font-medium text-gray-900">Bank Account</div>
                <div className="text-xs text-gray-600">Direct bank transfer</div>
              </button>
            </div>
          </div>

          {/* Paystack Integration Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-blue-900 mb-1">Paystack Integration Required</h4>
                <p className="text-sm text-blue-700">
                  Payment method management will be available once Paystack is integrated. 
                  You'll be able to securely add and manage cards and bank accounts.
                </p>
              </div>
            </div>
          </div>

          {/* Coming Soon Preview */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">Coming Soon</h4>
            <p className="text-gray-600 mb-4">
              Payment method integration with Paystack is in progress. 
              You'll soon be able to:
            </p>
            <ul className="text-left max-w-md mx-auto space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Securely save your payment methods</span>
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Enable auto-renewal for subscriptions</span>
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Quick checkout with saved methods</span>
              </li>
              <li className="flex items-start">
                <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                <span>Multiple payment options (cards, bank transfers, mobile money)</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
