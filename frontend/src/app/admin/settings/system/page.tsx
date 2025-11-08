'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

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
      
      const healthRes = await fetch('http://127.0.0.1:8000/api/health/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealthStatus(healthData);
      }

      const setupRes = await fetch('http://127.0.0.1:8000/api/admin/setup/status/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (setupRes.ok) {
        const setupData = await setupRes.json();
        setSetupStatus(setupData);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch health data:', error);
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

  const isHealthy = healthStatus?.status === 'ok';
  const setupComplete = setupStatus?.setup_complete || false;
  const completionPercentage = setupStatus?.completion_percentage || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Health & Monitoring</h1>
          <p className="text-gray-600">Real-time platform status and configuration overview</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
          >
            {refreshing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Refreshing...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Overall System Status */}
      <div className={`rounded-lg border-2 p-6 transition-all ${ 
        isHealthy 
          ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300' 
          : 'bg-gradient-to-br from-red-50 to-orange-50 border-red-300'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              {isHealthy ? (
                <>
                  <div className="w-4 h-4 bg-green-500 rounded-full mr-3 animate-pulse"></div>
                  <h2 className="text-2xl font-bold text-green-700">System Operational</h2>
                </>
              ) : (
                <>
                  <div className="w-4 h-4 bg-red-500 rounded-full mr-3 animate-pulse"></div>
                  <h2 className="text-2xl font-bold text-red-700">System Error</h2>
                </>
              )}
            </div>
            <p className={`text-sm ${isHealthy ? 'text-green-600' : 'text-red-600'}`}>
              {healthStatus?.message || 'Status unknown'}
            </p>
          </div>
          <div className={`p-4 rounded-lg ${isHealthy ? 'bg-green-100' : 'bg-red-100'}`}>
            <svg className={`h-10 w-10 ${isHealthy ? 'text-green-600' : 'text-red-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isHealthy ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              )}
            </svg>
          </div>
        </div>
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
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 flex items-center">
            <svg className="h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
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
            <div className={`p-2 rounded-lg ${
              setupStatus?.components.telegram.configured ? 'bg-blue-100' : 'bg-gray-200'
            }`}>
              <svg className={`h-6 w-6 ${
                setupStatus?.components.telegram.configured ? 'text-blue-600' : 'text-gray-500'
              }`} fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
            </div>
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
            <div className={`p-2 rounded-lg ${
              setupStatus?.components.payment.configured ? 'bg-green-100' : 'bg-gray-200'
            }`}>
              <svg className={`h-6 w-6 ${
                setupStatus?.components.payment.configured ? 'text-green-600' : 'text-gray-500'
              }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${
              setupStatus?.components.payment.test_mode 
                ? 'bg-orange-100 text-orange-700' 
                : 'bg-green-100 text-green-700'
            }`}>
              {setupStatus?.components.payment.test_mode ? 'Test' : 'Live'}
            </div>
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
            <div className={`p-2 rounded-lg ${
              setupStatus?.components.email.configured ? 'bg-purple-100' : 'bg-gray-200'
            }`}>
              <svg className={`h-6 w-6 ${
                setupStatus?.components.email.configured ? 'text-purple-600' : 'text-gray-500'
              }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
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
            <div className="p-2 bg-indigo-100 rounded-lg">
              <svg className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
            </div>
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
            <svg className="h-6 w-6 text-orange-600 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
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
                        <p className="text-xs text-orange-600 font-medium">→ {recommendation.action}</p>
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
          <svg className="h-5 w-5 mr-2 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => router.push('/admin/settings/telegram')}
            className="flex items-center p-4 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors text-left"
          >
            <div className="p-2 bg-blue-100 rounded-lg mr-3">
              <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
            </div>
            <div>
              <div className="font-medium text-gray-900">Configure Telegram</div>
              <div className="text-xs text-gray-600">Setup bot token and connection</div>
            </div>
          </button>

          <button
            onClick={() => router.push('/admin/settings/payment')}
            className="flex items-center p-4 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg transition-colors text-left"
          >
            <div className="p-2 bg-green-100 rounded-lg mr-3">
              <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div>
              <div className="font-medium text-gray-900">Configure Payment</div>
              <div className="text-xs text-gray-600">Setup Paystack and Stripe</div>
            </div>
          </button>

          <button
            onClick={() => router.push('/admin/settings/email')}
            className="flex items-center p-4 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors text-left"
          >
            <div className="p-2 bg-purple-100 rounded-lg mr-3">
              <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
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
