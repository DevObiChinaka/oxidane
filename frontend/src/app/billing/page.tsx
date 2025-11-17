'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  CreditCardIcon,
  UserGroupIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { apiGet, apiPost, apiDelete } from '@/lib/api';
import DashboardSidebar from '../components/DashboardSidebar';
import { useUserAuth } from '../contexts/UserAuthContext';
import TelegramVerification from '@/components/TelegramVerification';

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

// Declare PaystackPop global type
declare global {
  interface Window {
    PaystackPop: any;
  }
}

export default function BillingPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'payment-methods' | 'telegram'>('payment-methods');
  const [billingProfile, setBillingProfile] = useState<BillingProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
      id: 'payment-methods' as const,
      name: 'Payment Methods',
      icon: CreditCardIcon,
      description: 'Manage saved cards',
    },
    {
      id: 'telegram' as const,
      name: 'Telegram Access',
      icon: UserGroupIcon,
      description: 'Connect your account',
    },
  ];

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />
        <div className="flex-1 flex items-center justify-center min-h-screen">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#00B38F]"></div>
            <p className="text-gray-600">Loading billing information...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />

      <main className="flex-1 min-h-screen lg:ml-0">
        {/* Mobile Menu Button */}
        <div className="lg:hidden fixed top-4 left-4 z-30">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
          <div className="ml-12 lg:ml-0">
            <h2 className="text-2xl sm:text-3xl font-semibold text-gray-900">Billing</h2>
            <p className="text-gray-500 text-sm mt-1">Manage your payment methods and Telegram access</p>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl">
          {/* Error Alert */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
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

          {/* Telegram Status Alert */}
          {billingProfile && !billingProfile.verified && (
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start">
              <ExclamationCircleIcon className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-amber-900 mb-1">Telegram Not Connected</h4>
                <p className="text-sm text-amber-700 mb-3">
                  Link your Telegram account to access premium groups and receive notifications.
                </p>
                <button
                  onClick={() => setActiveTab('telegram')}
                  className="text-sm font-medium text-amber-900 hover:text-amber-800 underline"
                >
                  Connect Now →
                </button>
              </div>
            </div>
          )}

          {billingProfile && billingProfile.verified && (
            <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
              <CheckCircleIcon className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-green-900 mb-1">Telegram Connected</h4>
                <p className="text-sm text-green-700">
                  Linked to <span className="font-semibold">@{billingProfile.telegram_username}</span>
                </p>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {/* Tab Headers */}
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm
                        transition-all duration-200
                        ${isActive
                          ? 'border-[#000856] text-gray-900'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="flex flex-col sm:flex-row items-center justify-center gap-2">
                        <Icon className={`w-5 h-5 ${isActive ? 'text-[#000856]' : 'text-gray-400'}`} />
                        <div className="text-center sm:text-left">
                          <div className="font-semibold">{tab.name}</div>
                          <div className="text-xs text-gray-500 hidden sm:block">{tab.description}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'payment-methods' && <PaymentMethodsSection />}
              {activeTab === 'telegram' && (
                <TelegramVerificationSection 
                  billingProfile={billingProfile} 
                  onUpdate={fetchBillingProfile}
                />
              )}
            </div>
          </div>

          {/* Quick Links */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => router.push('/subscriptions')}
              className="bg-white rounded-lg border border-gray-200 p-5 hover:border-gray-300 transition-colors text-left group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-gray-900">My Subscriptions</h4>
              </div>
              <p className="text-sm text-gray-500">View and manage your active subscriptions</p>
            </button>

            <button
              onClick={() => router.push('/pricing')}
              className="bg-white rounded-lg border border-gray-200 p-5 hover:border-gray-300 transition-colors text-left group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center group-hover:bg-green-100 transition-colors">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-gray-900">Pricing Plans</h4>
              </div>
              <p className="text-sm text-gray-500">Browse and subscribe to new plans</p>
            </button>
          </div>
        </div>
      </main>
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
  const [showUnlinkConfirm, setShowUnlinkConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  // If verified, show verification info with unlink option
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

  // If not verified, use the modern TelegramVerification component
  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Link Your Telegram Account</h3>
        <p className="text-gray-600">
          Connect your Telegram account to access premium groups and receive real-time notifications.
        </p>
      </div>

      {/* Modern Telegram Verification Component */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <TelegramVerification
          onVerified={() => {
            onUpdate();
          }}
          onError={(err) => setError(err)}
          showInline={true}
          autoStart={true}
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Helpful Instructions */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 text-sm mb-1">Quick & Easy Process</h4>
            <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
              <li>Click "Generate Verification Link" below</li>
              <li>Click "Open Telegram Bot" to launch Telegram</li>
              <li>Tap "START" in the bot chat - that's it!</li>
            </ol>
            <p className="text-xs text-gray-500 mt-2">
              Your verification happens automatically - no need to type any codes!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Payment Methods Section
function PaymentMethodsSection() {
  const { user } = useUserAuth();
  const [paymentMethods, setPaymentMethods] = useState<Array<{
    id: string;
    card_last4: string;
    card_brand: string;
    card_exp_month: string;
    card_exp_year: string;
    is_default: boolean;
    last_used_at: string | null;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [showAddMethod, setShowAddMethod] = useState(false);
  const [deletingMethodId, setDeletingMethodId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [paystackReady, setPaystackReady] = useState(false);
  const [paystackPublicKey, setPaystackPublicKey] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchPaymentMethods();
    fetchPaystackConfig();
    
    // Check if Paystack is already loaded
    if (typeof window !== 'undefined' && window.PaystackPop) {
      setPaystackReady(true);
    } else {
      // Wait for script to load
      const checkPaystack = setInterval(() => {
        if (typeof window !== 'undefined' && window.PaystackPop) {
          setPaystackReady(true);
          clearInterval(checkPaystack);
        }
      }, 100);

      // Cleanup
      return () => clearInterval(checkPaystack);
    }
  }, []);

  const fetchPaystackConfig = async () => {
    try {
      const response = await apiGet('/payment-methods/config/');
      if (response.ok) {
        const data = await response.json();
        setPaystackPublicKey(data.paystack_public_key || '');
      }
    } catch (err) {
      console.error('Failed to fetch Paystack config:', err);
    }
  };

  const fetchPaymentMethods = async () => {
    try {
      setLoading(true);
      const response = await apiGet('/payment-methods/');
      if (response.ok) {
        const data = await response.json();
        setPaymentMethods(data.payment_methods || []);
      }
    } catch (error) {
      console.error('Error fetching payment methods:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefaultPaymentMethod = async (methodId: string) => {
    setSettingDefaultId(methodId);
    try {
      const response = await apiPost(`/payment-methods/${methodId}/set-default/`, {});
      if (response.ok) {
        await fetchPaymentMethods();
      } else {
        alert('Failed to set default payment method. Please try again.');
      }
    } catch (error) {
      console.error('Error setting default payment method:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setSettingDefaultId(null);
    }
  };

  const handleDeletePaymentMethod = async (methodId: string) => {
    setDeletingMethodId(methodId);
    try {
      const response = await apiDelete(`/payment-methods/${methodId}/`);

      if (response.ok) {
        const data = await response.json();
        if (data.affected_subscriptions > 0) {
          setSuccessMessage(`Payment method deleted. Auto-renewal has been disabled on ${data.affected_subscriptions} subscription(s) for your safety.`);
        } else {
          setSuccessMessage('Payment method deleted successfully.');
        }
        await fetchPaymentMethods();
      } else {
        setErrorMessage('Failed to delete payment method. Please try again.');
      }
    } catch (error) {
      console.error('Error deleting payment method:', error);
      setErrorMessage('An error occurred. Please try again.');
    } finally {
      setDeletingMethodId(null);
      setShowDeleteConfirm(null);
    }
  };

  const handleAddCard = () => {
    // Check if Paystack is ready
    if (!paystackReady || !window.PaystackPop) {
      setErrorMessage('Payment system is still loading. Please wait a moment and try again.');
      return;
    }

    // Check if we have the Paystack public key
    if (!paystackPublicKey) {
      setErrorMessage('Payment system is not configured. Please contact support.');
      return;
    }

    // Check if user is logged in
    if (!user || !user.email) {
      setErrorMessage('Please log in to add a payment method.');
      return;
    }

    try {
      const handler = window.PaystackPop.setup({
        key: paystackPublicKey,
        email: user.email,
        amount: 5000, // ₦50 verification charge (will be refunded)
        currency: 'NGN',
        ref: `CARD_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        metadata: {
          purpose: 'card_verification',
          custom_fields: [
            {
              display_name: 'Purpose',
              variable_name: 'purpose',
              value: 'Add Payment Method'
            }
          ]
        },
        onClose: function() {
          setShowAddMethod(false);
        },
        callback: function(response: any) {
          // Payment successful - save the card
          apiPost('/payment-methods/save/', {
            reference: response.reference
          }).then(async (saveResponse) => {
            if (saveResponse.ok) {
              setSuccessMessage('Card added successfully! The ₦50 verification charge will be refunded shortly.');
              await fetchPaymentMethods();
              setShowAddMethod(false);
            } else {
              const errorData = await saveResponse.json();
              setErrorMessage(`Failed to save card: ${errorData.error || 'Unknown error'}`);
            }
          }).catch((error) => {
            console.error('Error saving card:', error);
            setErrorMessage('An error occurred while saving your card. Please try again.');
          });
        }
      });

      handler.openIframe();
    } catch (error) {
      console.error('Error initializing Paystack:', error);
      setErrorMessage('Failed to open payment modal. Please refresh the page and try again.');
    }
  };

  const getCardBrandIcon = (brand: string) => {
    const brandLower = brand.toLowerCase();
    
    if (brandLower.includes('visa')) {
      return (
        <div className="text-[#1434CB] font-bold text-lg">VISA</div>
      );
    }
    
    if (brandLower.includes('master')) {
      return (
        <div className="flex items-center gap-1">
          <div className="w-6 h-6 rounded-full bg-[#EB001B]"></div>
          <div className="w-6 h-6 rounded-full bg-[#F79E1B] -ml-3"></div>
        </div>
      );
    }
    
    if (brandLower.includes('amex') || brandLower.includes('american')) {
      return (
        <div className="text-[#006FCF] font-bold text-lg">AMEX</div>
      );
    }
    
    if (brandLower.includes('verve')) {
      return (
        <div className="text-[#EE312A] font-bold text-sm">VERVE</div>
      );
    }
    
    return (
      <CreditCardIcon className="w-6 h-6 text-gray-600" />
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Payment Method</h3>
          <p className="text-gray-600">
            {paymentMethods.length > 0 ? 'Your card for all subscriptions and renewals' : 'Add a card for subscriptions and auto-renewals'}
          </p>
        </div>
        <button
          onClick={() => setShowAddMethod(true)}
          className="px-4 py-2.5 bg-[#000856] text-white rounded-lg text-sm font-medium hover:bg-[#000856]/90 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {paymentMethods.length > 0 ? 'Update Card' : 'Add Card'}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#00B38F]"></div>
        </div>
      ) : paymentMethods.length === 0 ? (
        <div className="bg-white rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CreditCardIcon className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Payment Method</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Add a payment method to enable quick checkout and auto-renewal for all your subscriptions.
          </p>
          <button
            onClick={() => setShowAddMethod(true)}
            className="px-6 py-3 bg-[#000856] text-white rounded-lg font-medium hover:bg-[#000856]/90 transition-colors inline-flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Your Card
          </button>
        </div>
      ) : (
        <div className="max-w-md">
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              className="bg-white rounded-xl border-2 border-gray-200 p-6 shadow-sm"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl flex items-center justify-center border border-gray-200">
                    {getCardBrandIcon(method.card_brand)}
                  </div>
                  <div>
                    <h4 className="text-base font-semibold text-gray-900 capitalize">
                      {method.card_brand}
                    </h4>
                    <p className="text-sm text-gray-600 font-mono">
                      •••• •••• •••• {method.card_last4}
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-green-700 bg-green-50 rounded-full border border-green-200">
                  Primary
                </span>
              </div>

              <div className="space-y-2 mb-4 pb-4 border-b border-gray-100">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Expires</span>
                  <span className="text-gray-900 font-medium">
                    {method.card_exp_month}/{method.card_exp_year}
                  </span>
                </div>
                {method.last_used_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Last used</span>
                    <span className="text-gray-900 font-medium">
                      {formatDate(method.last_used_at)}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Use for</span>
                  <span className="text-gray-900 font-medium">
                    All subscriptions
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowAddMethod(true)}
                  className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  Update Card
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(method.id)}
                  disabled={deletingMethodId === method.id}
                  className="px-3 py-2 text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                  title="Delete payment method"
                >
                  {deletingMethodId === method.id ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-red-600 border-t-transparent"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Security Notice */}
      <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-start">
          <ShieldCheckIcon className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-green-900 mb-1">Secure Payment Processing</h4>
            <p className="text-sm text-green-700">
              All payment information is encrypted and securely stored by Paystack. We never store your full card details on our servers.
            </p>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <ExclamationCircleIcon className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Remove Payment Method?</h3>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              This will remove your payment method and automatically disable auto-renewal on all active subscriptions. 
              You won't be able to make new purchases until you add a new card.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeletePaymentMethod(showDeleteConfirm)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
              >
                Yes, Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add/Update Payment Method Modal */}
      {showAddMethod && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {paymentMethods.length > 0 ? 'Update Payment Method' : 'Add Payment Method'}
              </h3>
              <button
                onClick={() => setShowAddMethod(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-6">
              {paymentMethods.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                  <div className="flex gap-3">
                    <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="text-sm text-amber-900">
                      <p className="font-medium mb-1">This will replace your current card</p>
                      <p className="text-amber-700">
                        Your existing payment method will be replaced. All subscriptions will use the new card.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex gap-3">
                  <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-blue-900">
                    <p className="font-medium mb-1">Secure Card Verification</p>
                    <p className="text-blue-700">
                      We'll charge ₦50 to verify your card. This amount will be refunded immediately after verification.
                    </p>
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                Your card details are processed securely through Paystack. We never store your full card number on our servers.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowAddMethod(false)}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCard}
                className="flex-1 px-4 py-2 bg-[#00B38F] text-white rounded-lg text-sm font-medium hover:bg-[#00A07D] transition-colors"
              >
                Continue to Paystack
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {successMessage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircleIcon className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Success!</h3>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              {successMessage}
            </p>
            <button
              onClick={() => setSuccessMessage(null)}
              className="w-full px-4 py-2 bg-[#000856] text-white rounded-lg text-sm font-medium hover:bg-[#000856]/90 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Error Modal */}
      {errorMessage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <ExclamationCircleIcon className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Error</h3>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              {errorMessage}
            </p>
            <button
              onClick={() => setErrorMessage(null)}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
