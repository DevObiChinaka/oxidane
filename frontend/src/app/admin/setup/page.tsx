'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';

interface SetupStatus {
  setup_complete: boolean;
  completion_percentage: number;
  components: {
    telegram: {
      configured: boolean;
      healthy: boolean;
      has_token: boolean;
      has_username: boolean;
      connection_status: string;
    };
    payment: {
      configured: boolean;
      paystack_configured: boolean;
      stripe_configured: boolean;
      test_mode: boolean;
    };
    email: {
      configured: boolean;
      enabled: boolean;
      has_host: boolean;
      has_credentials: boolean;
      connection_status: string;
    };
    database: {
      has_active_plans: boolean;
      plans_count: number;
      features_count: number;
      active_groups_count: number;
      ready: boolean;
    };
  };
  recommendations: Array<{
    component: string;
    message: string;
    action: string;
  }>;
  summary: {
    total_checks: number;
    completed_checks: number;
    pending_checks: number;
  };
}

interface SetupStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  href: string;
  key: 'telegram' | 'payment' | 'email' | 'database';
}

export default function SetupDashboardPage() {
  const router = useRouter();
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const setupSteps: SetupStep[] = [
    {
      id: 'telegram',
      title: 'Telegram Integration',
      description: 'Configure Telegram bot for automated group management',
      icon: '💬',
      href: '/admin/settings/telegram',
      key: 'telegram'
    },
    {
      id: 'payment',
      title: 'Payment Gateway',
      description: 'Set up Paystack or Stripe for accepting payments',
      icon: '💳',
      href: '/admin/settings/payment',
      key: 'payment'
    },
    {
      id: 'email',
      title: 'Email Configuration',
      description: 'Configure SMTP settings for sending notifications',
      icon: '📧',
      href: '/admin/settings/email',
      key: 'email'
    },
    {
      id: 'plans',
      title: 'Subscription Plans',
      description: 'Create pricing plans with features and billing options',
      icon: '💰',
      href: '/admin/plans',
      key: 'database'
    },
    {
      id: 'features',
      title: 'Platform Features',
      description: 'Define features that can be assigned to subscription plans',
      icon: '⚡',
      href: '/admin/features',
      key: 'database'
    }
  ];

  useEffect(() => {
    fetchSetupStatus();
  }, []);

  const fetchSetupStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/api/admin/setup/status/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          router.push('/admin/login');
          return;
        }
        throw new Error('Failed to fetch setup status');
      }

      const data = await response.json();
      setStatus(data);

      // Allow users to stay on setup page - they can access settings anytime
      // Mark setup as completed in localStorage when they visit this page
      if (data.setup_complete) {
        localStorage.setItem('admin_setup_completed', 'true');
      }
    } catch (err: any) {
      console.error('Setup status error:', err);
      setError(err.message || 'Failed to load setup status');
    } finally {
      setLoading(false);
    }
  };

  const getStepStatus = (step: SetupStep): 'complete' | 'incomplete' | 'partial' => {
    if (!status) return 'incomplete';

    const components = status.components;
    
    if (step.key === 'database') {
      const dbComponent = components.database;
      // For database, check both plans and features
      if (step.id === 'plans') {
        return dbComponent.has_active_plans ? 'complete' : 'incomplete';
      } else if (step.id === 'features') {
        return dbComponent.features_count > 0 ? 'complete' : 'incomplete';
      }
      return dbComponent.ready ? 'complete' : 'incomplete';
    }
    
    // For other components, check configured status
    const component = components[step.key];
    if ('configured' in component) {
      return component.configured ? 'complete' : 'incomplete';
    }
    
    return 'incomplete';
  };

  const getStepDetails = (step: SetupStep): string => {
    if (!status) return '';

    const components = status.components;
    
    switch (step.id) {
      case 'telegram': {
        const telegramComponent = components.telegram;
        return telegramComponent.has_token 
          ? `✓ Connected (${telegramComponent.connection_status})`
          : 'Not configured';
      }
      case 'payment': {
        const paymentComponent = components.payment;
        if (paymentComponent.paystack_configured && paymentComponent.stripe_configured) {
          return '✓ Both gateways configured';
        } else if (paymentComponent.paystack_configured) {
          return '✓ Paystack configured';
        } else if (paymentComponent.stripe_configured) {
          return '✓ Stripe configured';
        }
        return 'No payment gateway';
      }
      case 'email': {
        const emailComponent = components.email;
        return emailComponent.configured 
          ? `✓ SMTP configured (${emailComponent.connection_status})`
          : 'Not configured';
      }
      case 'plans': {
        const dbComponent = components.database;
        return dbComponent.plans_count > 0
          ? `✓ ${dbComponent.plans_count} active plan${dbComponent.plans_count !== 1 ? 's' : ''}`
          : 'No plans created';
      }
      case 'features': {
        const dbComponent = components.database;
        return dbComponent.features_count > 0
          ? `✓ ${dbComponent.features_count} feature${dbComponent.features_count !== 1 ? 's' : ''} defined`
          : 'No features defined';
      }
      default:
        return '';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00B38F] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading setup status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Setup Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={fetchSetupStatus}
            className="bg-[#00B38F] text-white px-6 py-2 rounded-lg hover:bg-[#009174] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!status) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden">
                <Image 
                  src="/logo_main.png" 
                  alt="OxiWorld Logo" 
                  width={48} 
                  height={48}
                  className="object-contain"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[#000856]">Platform Setup</h1>
                <p className="text-sm text-gray-500">Complete these steps to activate your platform</p>
              </div>
            </div>
            {status.setup_complete && (
              <Link
                href="/admin"
                className="bg-[#00B38F] text-white px-6 py-2 rounded-lg hover:bg-[#009174] transition-colors flex items-center space-x-2"
              >
                <span>Go to Dashboard</span>
                <span>→</span>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {status.setup_complete ? (
          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl p-8 text-white mb-8">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <span className="text-4xl">🎉</span>
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold mb-2">Setup Complete!</h2>
                <p className="text-green-100">
                  Your platform is fully configured and ready to use. You can access settings anytime from the sidebar.
                </p>
              </div>
              <Link
                href="/admin/dashboard"
                className="bg-white text-green-600 px-6 py-3 rounded-lg hover:bg-green-50 transition-colors font-semibold flex items-center space-x-2"
              >
                <span>Go to Dashboard</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Setup Progress</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {status.summary.completed_checks} of {status.summary.total_checks} steps completed
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-[#00B38F]">
                  {status.completion_percentage}%
                </div>
                <div className="text-xs text-gray-500">Complete</div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-[#00B38F] to-[#00D9A5] h-full rounded-full transition-all duration-500"
                style={{ width: `${status.completion_percentage}%` }}
              />
            </div>

            {/* Recommendations */}
            {status.recommendations.length > 0 && (
              <div className="mt-6 space-y-2">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                  Pending Tasks
                </h3>
                {status.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <span className="text-amber-600 mt-0.5">⚠️</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-amber-900">{rec.message}</p>
                      <p className="text-xs text-amber-700 mt-1">{rec.action}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Setup Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {setupSteps.map((step, index) => {
            const stepStatus = getStepStatus(step);
            const stepDetails = getStepDetails(step);
            const isComplete = stepStatus === 'complete';

            return (
              <Link
                key={step.id}
                href={step.href}
                className={`
                  group relative bg-white rounded-xl border-2 p-6 transition-all duration-200
                  ${isComplete 
                    ? 'border-green-300 hover:border-green-400 hover:shadow-lg' 
                    : 'border-gray-200 hover:border-[#00B38F] hover:shadow-xl'
                  }
                `}
              >
                {/* Step Number Badge */}
                <div className="absolute -top-3 -left-3 w-8 h-8 bg-white border-2 border-gray-200 rounded-full flex items-center justify-center text-sm font-semibold text-gray-600 group-hover:border-[#00B38F] group-hover:text-[#00B38F] transition-colors">
                  {index + 1}
                </div>

                {/* Status Badge */}
                <div className="absolute -top-3 -right-3">
                  {isComplete ? (
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center shadow-lg">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded-full"></div>
                    </div>
                  )}
                </div>

                {/* Icon */}
                <div className={`
                  w-16 h-16 rounded-xl flex items-center justify-center text-3xl mb-4
                  ${isComplete ? 'bg-green-100' : 'bg-gray-100 group-hover:bg-[#00B38F]/10'}
                  transition-colors
                `}>
                  {step.icon}
                </div>

                {/* Content */}
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-[#00B38F] transition-colors">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                  {step.description}
                </p>

                {/* Status Details */}
                <div className={`
                  text-xs font-medium px-3 py-2 rounded-lg inline-block
                  ${isComplete 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-600'
                  }
                `}>
                  {stepDetails || 'Not started'}
                </div>

                {/* Hover Arrow */}
                <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all">
                  <svg className="w-5 h-5 text-[#00B38F]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-[#000856] rounded-xl p-8 text-white">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">💡</span>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">Need Help?</h3>
              <p className="text-gray-300 mb-4">
                Follow these steps in order for the best experience. Each configuration page includes 
                detailed instructions and test functionality to ensure everything works correctly.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex items-center space-x-2 text-sm">
                  <span className="text-[#00B38F]">✓</span>
                  <span>Test each configuration before proceeding</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <span className="text-[#00B38F]">✓</span>
                  <span>Save changes after testing</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <span className="text-[#00B38F]">✓</span>
                  <span>Return here anytime to check progress</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <span className="text-[#00B38F]">✓</span>
                  <span>Setup can be completed in any order</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <button
            onClick={fetchSetupStatus}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors inline-flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh Status</span>
          </button>
        </div>
      </div>
    </div>
  );
}
