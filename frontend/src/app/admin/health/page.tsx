'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface HealthMetrics {
  status: 'ok' | 'error';
  message: string;
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
      connection_status: string;
      last_check: string | null;
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

export default function SystemHealthPage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthMetrics | null>(null);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  useEffect(() => {
    checkAuth();
    fetchHealthData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchHealthData(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const checkAuth = () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/admin/login');
    }
  };

  const fetchHealthData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      // Fetch basic health check
      const healthRes = await fetch('http://127.0.0.1:8000/api/health/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealth(healthData);
      }

      // Fetch setup status
      const setupRes = await fetch('http://127.0.0.1:8000/api/admin/setup/status/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (setupRes.ok) {
        const setupData = await setupRes.json();
        setSetupStatus(setupData);
      }

      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to fetch health data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusColor = (status: boolean | string): string => {
    if (typeof status === 'boolean') {
      return status ? 'green' : 'red';
    }
    if (status === 'connected') return 'green';
    if (status === 'disconnected') return 'red';
    return 'yellow';
  };

  const getStatusIcon = (status: boolean) => {
    if (status) {
      return (
        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    return (
      <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading system health...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">System Health</h1>
            <p className="text-gray-600">Monitor platform status and system components</p>
          </div>
          <button
            onClick={() => fetchHealthData()}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <svg className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        {lastChecked && (
          <p className="text-sm text-gray-500 mt-2">
            Last checked: {lastChecked.toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Overall Status Card */}
      {health && (
        <div className={`mb-8 p-6 rounded-xl border-2 ${
          health.status === 'ok' 
            ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'
            : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200'
        }`}>
          <div className="flex items-center gap-4">
            <div className={`w-16 h-16 rounded-full ${
              health.status === 'ok' ? 'bg-green-100' : 'bg-red-100'
            } flex items-center justify-center`}>
              {health.status === 'ok' ? (
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${
                health.status === 'ok' ? 'text-green-900' : 'text-red-900'
              }`}>
                {health.status === 'ok' ? 'All Systems Operational' : 'System Issues Detected'}
              </h2>
              <p className={`text-lg ${
                health.status === 'ok' ? 'text-green-700' : 'text-red-700'
              }`}>
                {health.message}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Setup Completion */}
      {setupStatus && (
        <div className="mb-8 p-6 bg-white rounded-xl border-2 border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-gray-900">Platform Setup</h3>
            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
              setupStatus.setup_complete
                ? 'bg-green-100 text-green-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {setupStatus.completion_percentage}% Complete
            </span>
          </div>
          
          {/* Progress Bar */}
          <div className="mb-6">
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all duration-500 ${
                  setupStatus.completion_percentage === 100
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                    : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                }`}
                style={{ width: `${setupStatus.completion_percentage}%` }}
              />
            </div>
            <div className="flex justify-between text-sm text-gray-600 mt-2">
              <span>{setupStatus.summary.completed_checks} of {setupStatus.summary.total_checks} checks passed</span>
              <span>{setupStatus.summary.pending_checks} remaining</span>
            </div>
          </div>

          {/* Component Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Telegram Component */}
            <div className={`p-4 rounded-lg border-2 ${
              setupStatus.components.telegram.configured
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Telegram</h4>
                {getStatusIcon(setupStatus.components.telegram.configured)}
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.telegram.has_token ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-700">Bot Token</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.telegram.has_username ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-700">Bot Username</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.telegram.connection_status === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-700 capitalize">{setupStatus.components.telegram.connection_status}</span>
                </div>
              </div>
            </div>

            {/* Payment Component */}
            <div className={`p-4 rounded-lg border-2 ${
              setupStatus.components.payment.configured
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Payment</h4>
                {getStatusIcon(setupStatus.components.payment.configured)}
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.payment.paystack_configured ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <span className="text-gray-700">Paystack</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.payment.stripe_configured ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <span className="text-gray-700">Stripe</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.payment.test_mode ? 'bg-yellow-500' : 'bg-green-500'
                  }`} />
                  <span className="text-gray-700">
                    {setupStatus.components.payment.test_mode ? 'Test Mode' : 'Live Mode'}
                  </span>
                </div>
              </div>
            </div>

            {/* Email Component */}
            <div className={`p-4 rounded-lg border-2 ${
              setupStatus.components.email.configured
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Email</h4>
                {getStatusIcon(setupStatus.components.email.configured)}
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.email.has_host ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-700">SMTP Host</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.email.has_credentials ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-gray-700">Credentials</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    setupStatus.components.email.connection_status === 'connected' ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <span className="text-gray-700 capitalize">{setupStatus.components.email.connection_status.replace('_', ' ')}</span>
                </div>
              </div>
            </div>

            {/* Database Component */}
            <div className={`p-4 rounded-lg border-2 ${
              setupStatus.components.database.ready
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-gray-900">Database</h4>
                {getStatusIcon(setupStatus.components.database.ready)}
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Plans:</span>
                  <span className="font-semibold">{setupStatus.components.database.plans_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Features:</span>
                  <span className="font-semibold">{setupStatus.components.database.features_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">Groups:</span>
                  <span className="font-semibold">{setupStatus.components.database.active_groups_count}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {setupStatus && setupStatus.recommendations.length > 0 && (
        <div className="mb-8 p-6 bg-gradient-to-br from-orange-50 to-yellow-50 border-2 border-orange-200 rounded-xl">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Recommendations ({setupStatus.recommendations.length})
          </h3>
          <div className="space-y-3">
            {setupStatus.recommendations.map((rec, index) => (
              <div key={index} className="p-4 bg-white rounded-lg border border-orange-200">
                <div className="flex items-start gap-3">
                  <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded uppercase">
                    {rec.component}
                  </span>
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium">{rec.message}</p>
                    <p className="text-sm text-gray-600 mt-1">{rec.action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button
          onClick={() => router.push('/admin/settings/telegram')}
          className="p-6 bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all text-left group"
        >
          <div className="flex items-center gap-4 mb-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <svg className="w-7 h-7 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18.717-.962 3.928-1.36 5.213-.168.544-.5.726-.818.744-.693.064-1.22-.46-1.893-.9-1.056-.693-1.653-1.124-2.678-1.8-1.185-.781-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.248-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.442-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635.099-.001.321.023.465.141.121.099.155.233.171.326.016.093.037.305.021.471z"/>
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Telegram Settings</h3>
              <p className="text-sm text-gray-600">Configure bot and groups</p>
            </div>
          </div>
        </button>

        <button
          onClick={() => router.push('/admin/settings/payment')}
          className="p-6 bg-white rounded-xl border-2 border-gray-200 hover:border-green-400 hover:shadow-lg transition-all text-left group"
        >
          <div className="flex items-center gap-4 mb-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <svg className="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Payment Settings</h3>
              <p className="text-sm text-gray-600">Manage payment gateways</p>
            </div>
          </div>
        </button>

        <button
          onClick={() => router.push('/admin/settings/email')}
          className="p-6 bg-white rounded-xl border-2 border-gray-200 hover:border-purple-400 hover:shadow-lg transition-all text-left group"
        >
          <div className="flex items-center gap-4 mb-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <svg className="w-7 h-7 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Email Settings</h3>
              <p className="text-sm text-gray-600">Configure SMTP settings</p>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
}
