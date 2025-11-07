'use client';

import { useState, useEffect } from 'react';

interface PaymentConfig {
  id: string;
  paystack_public_key: string;
  paystack_secret_key: string;
  paystack_webhook_secret: string;
  paystack_webhook_url: string;
  paystack_enabled: boolean;
  stripe_publishable_key: string;
  stripe_secret_key: string;
  stripe_webhook_secret: string;
  stripe_webhook_url: string;
  stripe_enabled: boolean;
  primary_provider: 'paystack' | 'stripe';
  is_test_mode: boolean;
  supported_currencies: string[];
  created_at: string;
  updated_at: string;
  masked_paystack_public?: string;
  masked_paystack_secret?: string;
  masked_stripe_publishable?: string;
  masked_stripe_secret?: string;
}

interface Message {
  type: 'success' | 'error' | 'warning';
  text: string;
}

export default function PaymentConfigPage() {
  const [activeTab, setActiveTab] = useState<'paystack' | 'stripe' | 'general'>('general');
  const [config, setConfig] = useState<PaymentConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<'paystack' | 'stripe' | null>(null);
  const [message, setMessage] = useState<Message | null>(null);
  
  // Form states
  const [formData, setFormData] = useState({
    // Paystack
    paystack_public_key: '',
    paystack_secret_key: '',
    paystack_webhook_secret: '',
    paystack_enabled: true,
    // Stripe
    stripe_publishable_key: '',
    stripe_secret_key: '',
    stripe_webhook_secret: '',
    stripe_enabled: false,
    // General
    primary_provider: 'paystack' as 'paystack' | 'stripe',
    is_test_mode: true,
    supported_currencies: ['NGN', 'USD'],
  });

  const [currencyInput, setCurrencyInput] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://127.0.0.1:8000/api/admin/payment/config/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const configData = Array.isArray(data) ? data[0] : data;
        setConfig(configData);
        
        // Update form with existing data
        setFormData({
          paystack_public_key: configData.paystack_public_key || '',
          paystack_secret_key: configData.paystack_secret_key || '',
          paystack_webhook_secret: configData.paystack_webhook_secret || '',
          paystack_enabled: configData.paystack_enabled ?? true,
          stripe_publishable_key: configData.stripe_publishable_key || '',
          stripe_secret_key: configData.stripe_secret_key || '',
          stripe_webhook_secret: configData.stripe_webhook_secret || '',
          stripe_enabled: configData.stripe_enabled ?? false,
          primary_provider: configData.primary_provider || 'paystack',
          is_test_mode: configData.is_test_mode ?? true,
          supported_currencies: configData.supported_currencies || ['NGN', 'USD'],
        });
      }
    } catch (error) {
      console.error('Error loading payment config:', error);
      setMessage({ type: 'error', text: 'Failed to load payment configuration' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      setMessage(null);
      const token = localStorage.getItem('access_token');
      
      const endpoint = config?.id 
        ? `http://127.0.0.1:8000/api/admin/payment/config/${config.id}/`
        : 'http://127.0.0.1:8000/api/admin/payment/config/';
      
      const response = await fetch(endpoint, {
        method: config?.id ? 'PATCH' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      
      if (response.ok) {
        setConfig(data);
        setMessage({ type: 'success', text: 'Payment configuration saved successfully' });
        await loadConfig();
      } else {
        const errorMessage = typeof data === 'object' 
          ? JSON.stringify(data) 
          : data.message || 'Failed to save configuration';
        setMessage({ type: 'error', text: errorMessage });
      }
    } catch (error: any) {
      console.error('Error saving payment config:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to save payment configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (provider: 'paystack' | 'stripe') => {
    if (!config?.id) {
      setMessage({ type: 'warning', text: 'Please save the configuration first before testing' });
      return;
    }

    try {
      setTesting(provider);
      setMessage(null);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(
        `http://127.0.0.1:8000/api/admin/payment/config/${config.id}/test-${provider}/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();
      
      if (response.ok && data.success) {
        setMessage({ 
          type: 'success', 
          text: `${provider === 'paystack' ? 'Paystack' : 'Stripe'} connection successful! ${data.message || ''}` 
        });
      } else {
        setMessage({ 
          type: 'error', 
          text: data.message || `Failed to connect to ${provider}` 
        });
      }
    } catch (error: any) {
      console.error(`Error testing ${provider}:`, error);
      setMessage({ 
        type: 'error', 
        text: `Failed to test ${provider} connection: ${error.message}` 
      });
    } finally {
      setTesting(null);
    }
  };

  const handleAddCurrency = () => {
    const currency = currencyInput.trim().toUpperCase();
    
    if (!currency) {
      setMessage({ type: 'warning', text: 'Please enter a currency code' });
      return;
    }
    
    if (currency.length !== 3) {
      setMessage({ type: 'error', text: 'Currency code must be exactly 3 letters (e.g., NGN, USD)' });
      return;
    }
    
    if (!/^[A-Z]{3}$/.test(currency)) {
      setMessage({ type: 'error', text: 'Currency code must contain only uppercase letters' });
      return;
    }
    
    if (formData.supported_currencies.includes(currency)) {
      setMessage({ type: 'warning', text: `${currency} is already in the list` });
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      supported_currencies: [...prev.supported_currencies, currency]
    }));
    setCurrencyInput('');
    setMessage({ type: 'success', text: `${currency} added successfully` });
  };

  const handleRemoveCurrency = (currency: string) => {
    setFormData(prev => ({
      ...prev,
      supported_currencies: prev.supported_currencies.filter(c => c !== currency)
    }));
    setMessage({ type: 'success', text: `${currency} removed successfully` });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading payment configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Gateway Configuration</h1>
          <p className="text-gray-600">
            Configure Paystack and Stripe payment providers for your platform
          </p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg border ${
            message.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
            message.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
            'bg-yellow-50 border-yellow-200 text-yellow-800'
          }`}>
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                {message.type === 'success' ? (
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                ) : message.type === 'error' ? (
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                ) : (
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                )}
              </svg>
              <span>{message.text}</span>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <nav className="flex border-b border-gray-200" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('general')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'general'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              General Settings
            </button>
            <button
              onClick={() => setActiveTab('paystack')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'paystack'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              Paystack Configuration
              {formData.paystack_enabled && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                  Active
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('stripe')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'stripe'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              Stripe Configuration
              {formData.stripe_enabled && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                  Active
                </span>
              )}
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {/* General Settings Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">General Payment Settings</h2>
                <p className="text-gray-600 mb-6">
                  Configure your primary payment provider and supported currencies
                </p>
              </div>

              {/* Primary Provider */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Payment Provider
                </label>
                <select
                  value={formData.primary_provider}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    primary_provider: e.target.value as 'paystack' | 'stripe' 
                  }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="paystack">Paystack (Nigerian Market)</option>
                  <option value="stripe">Stripe (International)</option>
                </select>
                <p className="mt-2 text-sm text-gray-500">
                  This provider will be used as the default for payment processing
                </p>
              </div>

              {/* Test Mode */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_test_mode}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_test_mode: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700">
                    Enable Test Mode (Sandbox)
                  </span>
                </label>
                <p className="mt-2 ml-7 text-sm text-gray-500">
                  Use test API keys for development. Disable for production.
                </p>
              </div>

              {/* Supported Currencies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Supported Currencies
                </label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={currencyInput}
                    onChange={(e) => setCurrencyInput(e.target.value.toUpperCase())}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddCurrency()}
                    placeholder="e.g., GBP, EUR"
                    maxLength={3}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    onClick={handleAddCurrency}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {formData.supported_currencies.map(currency => (
                    <span
                      key={currency}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                    >
                      {currency}
                      <button
                        onClick={() => handleRemoveCurrency(currency)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </span>
                  ))}
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  Common currencies: NGN (Naira), USD (Dollar), GBP (Pound), EUR (Euro)
                </p>
              </div>

              {/* Provider Status Overview */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Payment Provider Status</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                    <div>
                      <div className="text-sm font-medium text-gray-900">Paystack</div>
                      <div className="text-xs text-gray-600">Nigerian Market</div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      formData.paystack_enabled 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {formData.paystack_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                    <div>
                      <div className="text-sm font-medium text-gray-900">Stripe</div>
                      <div className="text-xs text-gray-600">International</div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      formData.stripe_enabled 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {formData.stripe_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Paystack Configuration Tab */}
          {activeTab === 'paystack' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Paystack Configuration</h2>
                <p className="text-gray-600 mb-6">
                  Configure Paystack payment gateway for Nigerian market payments
                </p>
              </div>

              {/* Enable Paystack */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.paystack_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, paystack_enabled: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-900">
                    Enable Paystack Payment Gateway
                  </span>
                </label>
              </div>

              {/* Public Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Public Key
                </label>
                <input
                  type="text"
                  value={formData.paystack_public_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, paystack_public_key: e.target.value }))}
                  placeholder="pk_test_... or pk_live_..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                {config?.masked_paystack_public && (
                  <p className="mt-2 text-sm text-gray-500">
                    Current: {config.masked_paystack_public}
                  </p>
                )}
              </div>

              {/* Secret Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secret Key
                </label>
                <input
                  type="password"
                  value={formData.paystack_secret_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, paystack_secret_key: e.target.value }))}
                  placeholder="sk_test_... or sk_live_..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                {config?.masked_paystack_secret && (
                  <p className="mt-2 text-sm text-gray-500">
                    Current: {config.masked_paystack_secret}
                  </p>
                )}
                <p className="mt-2 text-sm text-gray-500">
                  This key will be encrypted when saved
                </p>
              </div>

              {/* Webhook Secret */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook Secret
                </label>
                <input
                  type="password"
                  value={formData.paystack_webhook_secret}
                  onChange={(e) => setFormData(prev => ({ ...prev, paystack_webhook_secret: e.target.value }))}
                  placeholder="Webhook secret from Paystack dashboard"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Used for verifying webhook signatures
                </p>
              </div>

              {/* Webhook URL */}
              {config?.paystack_webhook_url && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Webhook URL
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={config.paystack_webhook_url}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(config.paystack_webhook_url);
                        setMessage({ type: 'success', text: 'Webhook URL copied to clipboard' });
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Configure this URL in your Paystack dashboard
                  </p>
                </div>
              )}

              {/* Test Connection */}
              <div>
                <button
                  onClick={() => handleTestConnection('paystack')}
                  disabled={testing === 'paystack' || !config?.id}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing === 'paystack' ? (
                    <>
                      <div className="w-4 h-4 border-2 border-gray-700 border-t-transparent rounded-full animate-spin mr-2"></div>
                      <span>Testing Connection...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Test Connection</span>
                    </>
                  )}
                </button>
                <p className="mt-2 text-sm text-gray-500">
                  Verify your Paystack API credentials
                </p>
              </div>

              {/* Help Links */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Getting Started with Paystack</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Get your API keys from <a href="https://dashboard.paystack.com/#/settings/developer" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Paystack Dashboard → Settings → API Keys & Webhooks</a></span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Use test keys (pk_test_/sk_test_) for development and testing</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Switch to live keys (pk_live_/sk_live_) when ready for production</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* Stripe Configuration Tab */}
          {activeTab === 'stripe' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Stripe Configuration</h2>
                <p className="text-gray-600 mb-6">
                  Configure Stripe payment gateway for international payments
                </p>
              </div>

              {/* Enable Stripe */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.stripe_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, stripe_enabled: e.target.checked }))}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-900">
                    Enable Stripe Payment Gateway
                  </span>
                </label>
              </div>

              {/* Publishable Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Publishable Key
                </label>
                <input
                  type="text"
                  value={formData.stripe_publishable_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, stripe_publishable_key: e.target.value }))}
                  placeholder="pk_test_... or pk_live_..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                {config?.masked_stripe_publishable && (
                  <p className="mt-2 text-sm text-gray-500">
                    Current: {config.masked_stripe_publishable}
                  </p>
                )}
              </div>

              {/* Secret Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secret Key
                </label>
                <input
                  type="password"
                  value={formData.stripe_secret_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, stripe_secret_key: e.target.value }))}
                  placeholder="sk_test_... or sk_live_..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                {config?.masked_stripe_secret && (
                  <p className="mt-2 text-sm text-gray-500">
                    Current: {config.masked_stripe_secret}
                  </p>
                )}
                <p className="mt-2 text-sm text-gray-500">
                  This key will be encrypted when saved
                </p>
              </div>

              {/* Webhook Secret */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook Secret
                </label>
                <input
                  type="password"
                  value={formData.stripe_webhook_secret}
                  onChange={(e) => setFormData(prev => ({ ...prev, stripe_webhook_secret: e.target.value }))}
                  placeholder="whsec_..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Used for verifying webhook signatures
                </p>
              </div>

              {/* Webhook URL */}
              {config?.stripe_webhook_url && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Webhook URL
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={config.stripe_webhook_url}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono text-sm"
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(config.stripe_webhook_url);
                        setMessage({ type: 'success', text: 'Webhook URL copied to clipboard' });
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Configure this URL in your Stripe dashboard
                  </p>
                </div>
              )}

              {/* Test Connection */}
              <div>
                <button
                  onClick={() => handleTestConnection('stripe')}
                  disabled={testing === 'stripe' || !config?.id}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing === 'stripe' ? (
                    <>
                      <div className="w-4 h-4 border-2 border-gray-700 border-t-transparent rounded-full animate-spin mr-2"></div>
                      <span>Testing Connection...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Test Connection</span>
                    </>
                  )}
                </button>
                <p className="mt-2 text-sm text-gray-500">
                  Verify your Stripe API credentials
                </p>
              </div>

              {/* Help Links */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Getting Started with Stripe</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Get your API keys from <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Stripe Dashboard → Developers → API Keys</a></span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Use test keys (pk_test_/sk_test_) for development and testing</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Switch to live keys (pk_live_/sk_live_) when ready for production</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>Configure webhooks at <a href="https://dashboard.stripe.com/webhooks" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Stripe Dashboard → Developers → Webhooks</a></span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Save Button (Fixed at bottom) */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={loadConfig}
            disabled={loading}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
          >
            Reset
          </button>
          <button
            onClick={handleSaveConfig}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 flex items-center"
          >
            {saving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                <span>Saving...</span>
              </>
            ) : (
              <span>Save Configuration</span>
            )}
          </button>
        </div>

        {/* Configuration Info */}
        {config && (
          <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="text-xs text-gray-500">
              <div className="flex items-center justify-between">
                <span>Last Updated: {new Date(config.updated_at).toLocaleString()}</span>
                <span>Configuration ID: {config.id.slice(0, 8)}...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
