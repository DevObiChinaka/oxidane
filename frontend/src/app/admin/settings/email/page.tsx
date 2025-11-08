'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface EmailConfig {
  id: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  masked_smtp_password?: string;
  use_tls: boolean;
  use_ssl: boolean;
  from_email: string;
  from_name: string;
  is_configured: boolean;
  created_at: string;
  updated_at: string;
}

interface Message {
  type: 'success' | 'error';
  text: string;
}

export default function EmailConfigPage() {
  const router = useRouter();
  const [config, setConfig] = useState<EmailConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordInput, setShowPasswordInput] = useState(false);
  
  const [formData, setFormData] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password_write: '',
    use_tls: true,
    use_ssl: false,
    from_email: '',
    from_name: '',
  });

  const [testEmail, setTestEmail] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/admin/login');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/admin/email/config/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📧 Email Config Response:', data);
        
        // Handle both single object and array response (singleton pattern)
        const configData = Array.isArray(data) ? data[0] : data;
        console.log('📧 Processed Config Data:', configData);
        console.log('📧 Masked Password:', configData?.masked_smtp_password);
        
        setConfig(configData);
        
        // Always populate formData if we have config data, regardless of is_configured
        if (configData) {
          setFormData({
            smtp_host: configData.smtp_host || '',
            smtp_port: configData.smtp_port || 587,
            smtp_username: configData.smtp_username || '',
            use_tls: configData.use_tls ?? true,
            use_ssl: configData.use_ssl ?? false,
            from_email: configData.from_email || '',
            from_name: configData.from_name || '',
            smtp_password_write: '',
          });
        }
      } else if (response.status === 404) {
        setConfig(null);
      } else if (response.status === 401) {
        localStorage.removeItem('access_token');
        router.push('/admin/login');
      }
    } catch (error) {
      console.error('Error fetching email config:', error);
      setMessage({ type: 'error', text: 'Failed to load email configuration' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    setMessage(null);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/admin/email/config/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setConfig(data);
        // Directly set formData with saved values (not using prev)
        setFormData({
          smtp_host: data.smtp_host || '',
          smtp_port: data.smtp_port || 587,
          smtp_username: data.smtp_username || '',
          use_tls: data.use_tls ?? true,
          use_ssl: data.use_ssl ?? false,
          from_email: data.from_email || '',
          from_name: data.from_name || '',
          smtp_password_write: '', // Clear password after save
        });
        setMessage({ type: 'success', text: 'Email configuration saved successfully' });
      } else {
        setMessage({ 
          type: 'error', 
          text: data.error || data.detail || 'Failed to save configuration' 
        });
      }
    } catch (error) {
      console.error('Error saving email config:', error);
      setMessage({ type: 'error', text: 'Failed to save email configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config?.id) {
      setMessage({ type: 'error', text: 'Please save configuration before testing connection' });
      return;
    }

    setTesting(true);
    setMessage(null);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/admin/email/config/${config.id}/test-connection/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage({ 
          type: 'success', 
          text: `✅ Connection successful! Connected to ${data.host}:${data.port} using ${data.encryption}` 
        });
      } else {
        setMessage({ 
          type: 'error', 
          text: data.message || 'Connection test failed' 
        });
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      setMessage({ type: 'error', text: 'Failed to test SMTP connection' });
    } finally {
      setTesting(false);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      setMessage({ type: 'error', text: 'Please enter a test email address' });
      return;
    }

    if (!config?.id) {
      setMessage({ type: 'error', text: 'Please save email configuration first before sending test email' });
      return;
    }

    setTesting(true);
    setMessage(null);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/admin/email/config/${config.id}/send-test/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipient: testEmail,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ 
          type: 'success', 
          text: data.message || 'Test email sent successfully! Check your inbox.' 
        });
      } else {
        setMessage({ 
          type: 'error', 
          text: data.message || data.error || data.detail || 'Failed to send test email' 
        });
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      setMessage({ type: 'error', text: 'Failed to send test email' });
    } finally {
      setTesting(false);
    }
  };

  const handleUseGmail = () => {
    setFormData(prev => ({
      ...prev,
      smtp_host: 'smtp.gmail.com',
      smtp_port: 587,
      use_tls: true,
      use_ssl: false,
    }));
    setMessage({ 
      type: 'success', 
      text: 'Gmail SMTP settings applied. Please enter your Gmail address and App Password.' 
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading email configuration...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Email Configuration</h1>
              <p className="text-gray-600 mt-1">
                Configure SMTP settings for sending transactional emails
              </p>
            </div>
          </div>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            <span className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {message.text}
            </span>
          </div>
        )}

        {/* Configuration Status Card */}
        {config && (
          <div className={`mb-6 p-5 rounded-xl border-2 ${
            config.is_configured 
              ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200' 
              : 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {config.is_configured ? (
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                )}
                <div>
                  <h3 className={`font-semibold ${config.is_configured ? 'text-green-900' : 'text-yellow-900'}`}>
                    {config.is_configured ? 'Email Configured' : 'Email Not Configured'}
                  </h3>
                  <p className={`text-sm mt-0.5 ${config.is_configured ? 'text-green-700' : 'text-yellow-700'}`}>
                    {config.is_configured 
                      ? `Active SMTP: ${config.smtp_host}:${config.smtp_port} ${config.use_tls ? '(TLS)' : config.use_ssl ? '(SSL)' : ''}` 
                      : 'Complete the form below to enable email functionality'}
                  </p>
                </div>
              </div>
              {config.is_configured && (
                <div className="text-right">
                  <p className="text-xs text-green-600 font-medium">Last Updated</p>
                  <p className="text-sm text-green-700 font-semibold">
                    {new Date(config.updated_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Configuration Form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Section Header */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <h2 className="text-lg font-semibold text-gray-900">SMTP Configuration</h2>
              </div>
              {config?.is_configured && (
                <button
                  onClick={handleTestEmail}
                  disabled={testing || !config?.is_configured}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {testing ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Testing...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Test Connection
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          <div className="p-6">
            {/* Quick Setup */}
            <div className="mb-8 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">Quick Setup</h3>
                  <p className="text-xs text-blue-700 mb-3">Pre-configure settings for popular email providers</p>
                  <button
                    onClick={handleUseGmail}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"/>
                    </svg>
                    Use Gmail SMTP
                  </button>
                  <p className="text-xs text-blue-600 mt-2 flex items-start gap-1">
                    <svg className="w-3 h-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Requires App Password, not your regular Gmail password</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Port 587 Blocked Warning */}
            {formData.smtp_host === 'smtp.gmail.com' && formData.smtp_port === 587 && formData.use_tls && (
              <div className="mb-8 p-5 bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-orange-900 mb-1">Connection Timeout Issues?</h3>
                    <p className="text-xs text-orange-700 mb-3">
                      Many ISPs and firewalls block port 587. If you're experiencing connection timeouts, try switching to SSL on port 465 instead.
                    </p>
                    <button
                      onClick={() => setFormData(prev => ({ 
                        ...prev, 
                        smtp_port: 465, 
                        use_tls: false, 
                        use_ssl: true 
                      }))}
                      className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Switch to SSL (Port 465)
                    </button>
                  </div>
                </div>
              </div>
            )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Host
              </label>
              <input
                type="text"
                value={formData.smtp_host}
                onChange={(e) => setFormData(prev => ({ ...prev, smtp_host: e.target.value }))}
                placeholder="smtp.gmail.com"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Port
              </label>
              <input
                type="number"
                value={formData.smtp_port}
                onChange={(e) => setFormData(prev => ({ ...prev, smtp_port: parseInt(e.target.value) || 587 }))}
                placeholder="587"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
              />
              <p className="mt-2 text-sm text-gray-500">
                Common ports: 587 (TLS), 465 (SSL), 25 (unencrypted)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Username
              </label>
              <input
                type="text"
                value={formData.smtp_username}
                onChange={(e) => setFormData(prev => ({ ...prev, smtp_username: e.target.value }))}
                placeholder="your-email@gmail.com"
                autoComplete="username"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Password
              </label>
              
              {config?.masked_smtp_password && config.masked_smtp_password !== '(not set)' ? (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={config.masked_smtp_password}
                        readOnly
                        className="w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-lg bg-gray-50 font-mono text-base text-gray-600"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      >
                        {showPassword ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        )}
                      </button>
                    </div>
                    <button
                      onClick={() => {
                        setFormData(prev => ({ ...prev, smtp_password_write: '' }));
                        setConfig(prev => prev ? { ...prev, masked_smtp_password: '' } : null);
                      }}
                      className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      Change Password
                    </button>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type={showPasswordInput ? "text" : "password"}
                    value={formData.smtp_password_write}
                    onChange={(e) => setFormData(prev => ({ ...prev, smtp_password_write: e.target.value }))}
                    placeholder="Enter SMTP password or App Password"
                    autoComplete="new-password"
                    className="w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswordInput(!showPasswordInput)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPasswordInput ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              )}
              <p className="mt-2 text-sm text-gray-500">
                For Gmail, use an App Password, not your regular password
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use_tls"
                  checked={formData.use_tls}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    use_tls: e.target.checked,
                    use_ssl: e.target.checked ? false : prev.use_ssl 
                  }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="use_tls" className="ml-2 text-sm text-gray-700">
                  Use TLS (Port 587)
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use_ssl"
                  checked={formData.use_ssl}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    use_ssl: e.target.checked,
                    use_tls: e.target.checked ? false : prev.use_tls 
                  }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="use_ssl" className="ml-2 text-sm text-gray-700">
                  Use SSL (Port 465)
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default From Email
              </label>
              <input
                type="email"
                value={formData.from_email}
                onChange={(e) => setFormData(prev => ({ ...prev, from_email: e.target.value }))}
                placeholder="noreply@yourdomain.com"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
              />
              <p className="mt-2 text-sm text-gray-500">
                Email address that will appear in the "From" field
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default From Name
              </label>
              <input
                type="text"
                value={formData.from_name}
                onChange={(e) => setFormData(prev => ({ ...prev, from_name: e.target.value }))}
                placeholder="OxiWorld Academy"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
              />
              <p className="mt-2 text-sm text-gray-500">
                Name that will appear in the "From" field
              </p>
            </div>

            <div className="pt-4">
              <div className="flex gap-3">
                <button
                  onClick={handleTestConnection}
                  disabled={testing || !config?.id}
                  className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {testing ? (
                    <>
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Testing...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Test Connection
                    </>
                  )}
                </button>
                <button
                  onClick={handleSaveConfig}
                  disabled={saving}
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                      </svg>
                      Save Configuration
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {config?.is_configured && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Email</h2>
            <p className="text-gray-600 mb-4">
              Send a test email to verify your SMTP configuration is working correctly
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recipient Email Address
                </label>
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="test@example.com"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base text-gray-900 placeholder-gray-400 bg-white"
                />
              </div>

              <button
                onClick={handleTestEmail}
                disabled={testing || !testEmail}
                className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {testing ? 'Sending Test Email...' : 'Send Test Email'}
              </button>
            </div>
          </div>
        )}

        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">Gmail Setup Instructions</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
                <li>Go to your Google Account settings</li>
                <li>Navigate to Security → 2-Step Verification (enable if not already)</li>
                <li>Go to Security → App passwords</li>
                <li>Generate a new app password for "Mail"</li>
                <li>Use your Gmail address as username and the generated password here</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
}
