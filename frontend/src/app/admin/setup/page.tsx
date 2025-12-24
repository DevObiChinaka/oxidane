'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_ENDPOINTS } from '@/config/api';
import TelegramIcon from './TelegramIcon';
import {
  CreditCardIcon,
  EnvelopeIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

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
  icon: React.ComponentType<{ className?: string }>;
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
      icon: TelegramIcon,
      href: '/admin/settings/telegram',
      key: 'telegram'
    },
    {
      id: 'payment',
      title: 'Payment Gateway',
      description: 'Set up Paystack or Stripe for accepting payments',
      icon: CreditCardIcon,
      href: '/admin/settings/payment',
      key: 'payment'
    },
    {
      id: 'email',
      title: 'Email Configuration',
      description: 'Configure SMTP settings for sending notifications',
      icon: EnvelopeIcon,
      href: '/admin/settings/email',
      key: 'email'
    },
    {
      id: 'plans',
      title: 'Subscription Plans',
      description: 'Create pricing plans with features and billing options',
      icon: CurrencyDollarIcon,
      href: '/admin/plans',
      key: 'database'
    },
    {
      id: 'features',
      title: 'Platform Features',
      description: 'Define features that can be assigned to subscription plans',
      icon: SparklesIcon,
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

      const response = await fetch(API_ENDPOINTS.admin.setupStatus, {
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
          <ArrowPathIcon className="w-12 h-12 text-brand-teal animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading setup status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Setup Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={fetchSetupStatus}
            className="bg-brand-teal text-white px-6 py-2 rounded-lg hover:bg-brand-teal/90 transition-colors"
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
            <div>
              <h1 className="text-2xl font-bold text-black">Platform Setup</h1>
              <p className="text-sm text-gray-500 mt-1">Configure your platform components to get started</p>
            </div>
            {status.setup_complete && (
              <Link
                href="/admin/dashboard"
                className="bg-brand-teal text-white px-6 py-2.5 rounded-lg hover:bg-brand-teal/90 transition-colors flex items-center gap-2 text-sm font-medium"
              >
                <span>Go to Dashboard</span>
                <ChevronRightIcon className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {status.setup_complete ? (
          <div className="flex items-center gap-3 mb-8">
            <CheckCircleIcon className="w-6 h-6 text-brand-teal" />
            <span className="text-base font-semibold text-gray-800">Setup Complete</span>
            <span className="text-sm text-gray-500">Your platform is fully configured and ready to use.</span>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Setup Progress</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {status.summary.completed_checks} of {status.summary.total_checks} components configured
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-brand-teal">
                  {status.completion_percentage}%
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">Complete</div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div 
                className="bg-brand-teal h-full rounded-full transition-all duration-500"
                style={{ width: `${status.completion_percentage}%` }}
              />
            </div>

            {/* Recommendations */}
            {status.recommendations.length > 0 && (
              <div className="mt-6 space-y-2">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Pending Tasks
                </h3>
                {status.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-100 rounded-lg">
                    <ExclamationTriangleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-blue-900">{rec.message}</p>
                      <p className="text-xs text-blue-700 mt-1">{rec.action}</p>
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
            const IconComponent = step.icon;

            return (
              <Link
                key={step.id}
                href={step.href}
                className={`
                  group relative bg-white rounded-lg border p-6 transition-all duration-200 hover:shadow-md
                  ${isComplete 
                    ? 'border-teal-200 hover:border-teal-300' 
                    : 'border-gray-200 hover:border-brand-teal/50'
                  }
                `}
              >
                {/* Step Number */}
                <div className="absolute -top-2.5 -left-2.5 w-6 h-6 bg-white border border-gray-300 rounded-full flex items-center justify-center text-xs font-semibold text-gray-500 shadow-sm">
                  {index + 1}
                </div>

                {/* Status Badge */}
                {isComplete && (
                  <div className="absolute -top-2.5 -right-2.5">
                    <div className="w-6 h-6 bg-brand-teal rounded-full flex items-center justify-center shadow-sm">
                      <CheckCircleIcon className="w-4 h-4 text-white" strokeWidth={2.5} />
                    </div>
                  </div>
                )}

                {/* Icon */}
                <div className={`
                  w-11 h-11 rounded-lg flex items-center justify-center mb-4 transition-colors
                  ${isComplete ? 'bg-teal-50 text-brand-teal' : 'bg-gray-50 text-gray-500 group-hover:bg-teal-50/50 group-hover:text-brand-teal'}
                `}>
                  <IconComponent className="w-5 h-5" />
                </div>

                {/* Content */}
                <h3 className="text-base font-semibold text-gray-900 mb-2 group-hover:text-brand-teal transition-colors">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                  {step.description}
                </p>

                {/* Status Details */}
                <div className={`
                  text-xs font-medium px-2.5 py-1.5 rounded-md inline-flex items-center gap-1.5
                  ${isComplete 
                    ? 'bg-teal-50 text-brand-teal' 
                    : 'bg-gray-50 text-gray-600'
                  }
                `}>
                  {isComplete && <CheckCircleIcon className="w-3.5 h-3.5" strokeWidth={2.5} />}
                  <span>{stepDetails || 'Not configured'}</span>
                </div>

                {/* Hover Arrow */}
                <ChevronRightIcon className="absolute bottom-6 right-6 w-4 h-4 text-brand-teal opacity-0 group-hover:opacity-100 transform translate-x-1 group-hover:translate-x-0 transition-all" strokeWidth={2.5} />
              </Link>
            );
          })}
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-blue-50 rounded-lg p-6 text-blue-900 shadow-sm border border-blue-100">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <LightBulbIcon className="w-5 h-5 text-blue-400" strokeWidth={2} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">Setup Guidelines</h3>
              <p className="text-blue-700 mb-4 text-sm leading-relaxed">
                Follow these steps to configure your platform. Each page includes detailed instructions 
                and test functionality to ensure everything works correctly.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-1 h-1 rounded-full bg-brand-teal flex-shrink-0"></div>
                  <span className="text-blue-700">Test each configuration</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-1 h-1 rounded-full bg-brand-teal flex-shrink-0"></div>
                  <span className="text-blue-700">Save changes after testing</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-1 h-1 rounded-full bg-brand-teal flex-shrink-0"></div>
                  <span className="text-blue-700">Check progress anytime</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-1 h-1 rounded-full bg-brand-teal flex-shrink-0"></div>
                  <span className="text-blue-700">Complete in any order</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <button
            onClick={fetchSetupStatus}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors inline-flex items-center gap-2"
          >
            <ArrowPathIcon className="w-4 h-4" />
            <span>Refresh Status</span>
          </button>
        </div>
      </div>
    </div>
  );
}
