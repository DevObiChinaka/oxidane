'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/config/api';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  BoltIcon,
  CreditCardIcon,
  EnvelopeIcon,
  CircleStackIcon,
  ExclamationTriangleIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import TelegramIcon from '../telegram/TelegramIcon';

interface HealthMetrics {
  status: 'ok' | 'error';
  message: string;
}

interface Recommendation {
  component: string;
  message: string;
  action: string;
}

interface SetupStatus {
  setup_complete: boolean;
  completion_percentage: number;
  components: {
    telegram: {
      configured: boolean;
      healthy: boolean;
      has_token: boolean;
      has_username: boolean;
      last_check: string | null;
      connection_status: 'connected' | 'disconnected' | 'error';
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
      connection_status: 'connected' | 'not_tested';
      last_test: string | null;
    };
    database: {
      has_active_plans: boolean;
      plans_count: number;
      features_count: number;
      active_groups_count: number;
      ready: boolean;
    };
  };
  recommendations: Recommendation[];
}

export default function SystemHealthPage() {
  const router = useRouter();
  const [healthStatus, setHealthStatus] = useState<HealthMetrics | null>(null);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchHealthData = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const token = localStorage.getItem('access_token');
      
      const healthRes = await fetch(API_ENDPOINTS.admin.health, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealthStatus(healthData);
      } else {
                const errorText = await healthRes.text();
                setHealthStatus({
          status: 'error',
          message: `API returned ${healthRes.status}: ${healthRes.statusText}`,
        });
      }

      const setupRes = await fetch(API_ENDPOINTS.admin.setupStatus, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (setupRes.ok) {
        const setupData = await setupRes.json();
        setSetupStatus(setupData);
      } else {
                const errorText = await setupRes.text();
              }

      setLastUpdate(new Date());
    } catch (error) {
            setHealthStatus({
        status: 'error',
        message: 'Failed to connect to API',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(() => {
      fetchHealthData(true);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    fetchHealthData(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading system health...</p>
        </div>
      </div>
    );
  }

  const isHealthy = healthStatus?.status === 'healthy' || healthStatus?.status === 'degraded';
  const setupComplete = setupStatus?.setup_complete || false;
  const completionPercentage = setupStatus?.completion_percentage || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-black">System Health & Monitoring</h1>
          <p className="text-gray-600">Real-time platform status and configuration overview</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="px-4 py-2 text-sm font-medium text-white bg-brand-teal rounded-lg hover:bg-brand-teal/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
          >
            {refreshing ? (
              <>
                <ArrowPathIcon className="h-4 w-4 animate-spin" strokeWidth={2} />
                <span>Refreshing...</span>
              </>
            ) : (
              <>
                <ArrowPathIcon className="h-4 w-4" strokeWidth={2} />
                <span>Refresh</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Overall System Status */}
      <div className="flex items-center gap-2 mb-4">
        {isHealthy ? (
          <CheckCircleIcon className="w-5 h-5 text-brand-teal" strokeWidth={2} />
        ) : (
          <ExclamationCircleIcon className="w-5 h-5 text-red-600" strokeWidth={2} />
        )}
        <span className={`font-medium ${
          isHealthy ? 'text-brand-teal' : 'text-red-600'
        }`}>
          {isHealthy ? 'System Operational' : 'System Error'}
        </span>
        <span className="text-sm text-gray-500">
          · {healthStatus?.message || 'Status unknown'}
        </span>
      </div>

      {/* Platform Setup Progress */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Platform Setup Progress</h3>
            <p className="text-sm text-gray-600">Configuration completion status</p>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${
              completionPercentage === 100 ? 'text-green-600' : 
              completionPercentage >= 75 ? 'text-blue-600' :
              completionPercentage >= 50 ? 'text-orange-600' :
              'text-red-600'
            }`}>
              {completionPercentage}%
            </div>
            <p className="text-xs text-gray-500">Complete</p>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
          <div 
            className={`h-4 rounded-full transition-all duration-500 ${
              completionPercentage === 100 ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 
              completionPercentage >= 75 ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
              completionPercentage >= 50 ? 'bg-gradient-to-r from-orange-500 to-orange-600' :
              'bg-gradient-to-r from-red-500 to-red-600'
            }`}
            style={{ width: `${completionPercentage}%` }}
          ></div>
        </div>

        {setupComplete && (
          <div className="mt-4 p-3 flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" strokeWidth={2} />
            <span className="text-sm font-medium text-green-800">
              Platform setup is complete! All components are configured.
            </span>
          </div>
        )}
      </div>

      {/* Component Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Telegram Status */}
        <div className={`rounded-lg border-2 p-5 transition-all ${
          setupStatus?.components.telegram.configured
            ? 'bg-blue-50 border-blue-300 hover:border-blue-400'
            : 'bg-gray-50 border-gray-300 hover:border-gray-400'
        }`}>
          <div className="flex items-start justify-between mb-3">
            <TelegramIcon className="h-8 w-8" color={setupStatus?.components.telegram.configured ? '#229ED9' : '#9CA3AF'} />
            <div className={`w-2 h-2 rounded-full ${
              setupStatus?.components.telegram.connection_status === 'connected' ? 'bg-green-500' :
              setupStatus?.components.telegram.connection_status === 'error' ? 'bg-red-500' :
              'bg-gray-400'
            }`}></div>
          </div>
          
          <h4 className="font-semibold text-gray-900 mb-1">Telegram Bot</h4>
          <div className="space-y-1">
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.telegram.has_token ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-gray-600">Token: {setupStatus?.components.telegram.has_token ? 'Set' : 'Not set'}</span>
            </div>
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.telegram.connection_status === 'connected' ? 'bg-green-500' :
                setupStatus?.components.telegram.connection_status === 'error' ? 'bg-red-500' :
                'bg-gray-400'
              }`}></span>
              <span className="text-gray-600 capitalize">{setupStatus?.components.telegram.connection_status || 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Payment Status */}
        <div className={`rounded-lg border-2 p-5 transition-all ${
          setupStatus?.components.payment.configured
            ? 'bg-green-50 border-green-300 hover:border-green-400'
            : 'bg-gray-50 border-gray-300 hover:border-gray-400'
        }`}>
          <div className="flex items-start justify-between mb-3">
            <CreditCardIcon className={`h-8 w-8 ${
              setupStatus?.components.payment.configured ? 'text-green-600' : 'text-gray-400'
            }`} strokeWidth={1.5} />
            <span className={`text-xs font-medium ${
              setupStatus?.components.payment.test_mode 
                ? 'text-orange-600' 
                : 'text-green-600'
            }`}>
              {setupStatus?.components.payment.test_mode ? 'Test' : 'Live'}
            </span>
          </div>
          
          <h4 className="font-semibold text-gray-900 mb-1">Payment Gateways</h4>
          <div className="space-y-1">
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.payment.paystack_configured ? 'bg-green-500' : 'bg-gray-400'
              }`}></span>
              <span className="text-gray-600">Paystack: {setupStatus?.components.payment.paystack_configured ? 'Configured' : 'Not set'}</span>
            </div>
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.payment.stripe_configured ? 'bg-green-500' : 'bg-gray-400'
              }`}></span>
              <span className="text-gray-600">Stripe: {setupStatus?.components.payment.stripe_configured ? 'Configured' : 'Not set'}</span>
            </div>
          </div>
        </div>

        {/* Email Status */}
        <div className={`rounded-lg border-2 p-5 transition-all ${
          setupStatus?.components.email.configured
            ? 'bg-purple-50 border-purple-300 hover:border-purple-400'
            : 'bg-gray-50 border-gray-300 hover:border-gray-400'
        }`}>
          <div className="flex items-start justify-between mb-3">
            <EnvelopeIcon className={`h-8 w-8 ${
              setupStatus?.components.email.configured ? 'text-purple-600' : 'text-gray-400'
            }`} strokeWidth={1.5} />
            <div className={`w-2 h-2 rounded-full ${
              setupStatus?.components.email.connection_status === 'connected' ? 'bg-green-500' :
              'bg-gray-400'
            }`}></div>
          </div>
          
          <h4 className="font-semibold text-gray-900 mb-1">Email Service</h4>
          <div className="space-y-1">
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.email.has_credentials ? 'bg-green-500' : 'bg-red-500'
              }`}></span>
              <span className="text-gray-600">SMTP: {setupStatus?.components.email.has_credentials ? 'Configured' : 'Not set'}</span>
            </div>
            <div className="flex items-center text-xs">
              <span className={`w-2 h-2 rounded-full mr-2 ${
                setupStatus?.components.email.connection_status === 'connected' ? 'bg-green-500' :
                'bg-gray-400'
              }`}></span>
              <span className="text-gray-600 capitalize">{setupStatus?.components.email.connection_status === 'not_tested' ? 'Not tested' : setupStatus?.components.email.connection_status}</span>
            </div>
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg border-2 border-indigo-300 hover:border-indigo-400 p-5 transition-all">
          <div className="flex items-start justify-between mb-3">
            <CircleStackIcon className="h-8 w-8 text-indigo-600" strokeWidth={1.5} />
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
          </div>
          
          <h4 className="font-semibold text-gray-900 mb-1">Database</h4>
          <div className="space-y-1">
            <div className="flex items-center text-xs">
              <span className="w-2 h-2 rounded-full mr-2 bg-indigo-500"></span>
              <span className="text-gray-600">{setupStatus?.components.database.plans_count || 0} Plans</span>
            </div>
            <div className="flex items-center text-xs">
              <span className="w-2 h-2 rounded-full mr-2 bg-indigo-500"></span>
              <span className="text-gray-600">{setupStatus?.components.database.features_count || 0} Features</span>
            </div>
            <div className="flex items-center text-xs">
              <span className="w-2 h-2 rounded-full mr-2 bg-indigo-500"></span>
              <span className="text-gray-600">{setupStatus?.components.database.active_groups_count || 0} Groups</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Panel */}
      {setupStatus && setupStatus.recommendations.length > 0 && (
        <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6">
          <div className="flex items-start mb-4">
            <ExclamationTriangleIcon className="h-6 w-6 text-orange-600 mr-3 flex-shrink-0" strokeWidth={2} />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-orange-900 mb-2">Setup Recommendations</h3>
              <ul className="space-y-3">
                {setupStatus.recommendations.map((recommendation, index) => (
                  <li key={index} className="bg-white rounded-lg p-3 border border-orange-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-xs font-semibold text-orange-700 bg-orange-100 px-2 py-1 rounded">
                            {recommendation.component}
                          </span>
                        </div>
                        <p className="text-sm text-gray-800 mb-2">{recommendation.message}</p>
                        <p className="text-xs text-orange-600 font-medium">? {recommendation.action}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BoltIcon className="h-5 w-5 mr-2 text-brand-teal" strokeWidth={2} />
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => router.push('/admin/settings/telegram')}
            className="flex items-center p-4 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors text-left"
          >
            <TelegramIcon className="h-6 w-6 mr-3" color="#229ED9" />
            <div>
              <div className="font-medium text-gray-900">Configure Telegram</div>
              <div className="text-xs text-gray-600">Setup bot token and connection</div>
            </div>
          </button>

          <button
            onClick={() => router.push('/admin/settings/payment')}
            className="flex items-center p-4 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg transition-colors text-left"
          >
            <CreditCardIcon className="h-6 w-6 text-green-600 mr-3" strokeWidth={2} />
            <div>
              <div className="font-medium text-gray-900">Configure Payment</div>
              <div className="text-xs text-gray-600">Setup Paystack and Stripe</div>
            </div>
          </button>

          <button
            onClick={() => router.push('/admin/settings/email')}
            className="flex items-center p-4 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors text-left"
          >
            <EnvelopeIcon className="h-6 w-6 text-purple-600 mr-3" strokeWidth={2} />
            <div>
              <div className="font-medium text-gray-900">Configure Email</div>
              <div className="text-xs text-gray-600">Setup SMTP server</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
