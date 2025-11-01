'use client';

import { useEffect, useState } from 'react';
import { adminAPI } from '../../utils/api';
import { PlatformSetting } from '../../types/admin';
import { SettingsCard } from '../components/SettingsCard';
import { SettingInput } from '../components/SettingInput';

export default function EmailConfigurationPage() {
  const [settings, setSettings] = useState<PlatformSetting[]>([]);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response: any = await adminAPI.getSettings('email');
      if (response.success) {
        setSettings(response.settings);
        // Initialize edited values with current values
        const initialValues: Record<string, any> = {};
        response.settings.forEach((setting: PlatformSetting) => {
          initialValues[setting.key] = setting.value;
        });
        setEditedValues(initialValues);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: 'Failed to load email settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleValueChange = (key: string, value: any) => {
    setEditedValues(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const hasChanges = () => {
    return settings.some(setting => editedValues[setting.key] !== setting.value);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);

      // Find changed settings
      const changedSettings = settings
        .filter(setting => editedValues[setting.key] !== setting.value)
        .map(setting => ({
          key: setting.key,
          value: editedValues[setting.key]
        }));

      if (changedSettings.length === 0) {
        setMessage({ type: 'info', text: 'No changes to save' });
        return;
      }

      // Bulk update
      const response: any = await adminAPI.bulkUpdateSettings(
        changedSettings,
        'Updated email configuration via admin panel'
      );

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: `Successfully updated ${response.updated} email setting(s)` 
        });
        // Reload to get fresh data
        await loadSettings();
      } else {
        setMessage({ type: 'error', text: 'Failed to save email settings' });
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: 'Failed to save email settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    const initialValues: Record<string, any> = {};
    settings.forEach(setting => {
      initialValues[setting.key] = setting.value;
    });
    setEditedValues(initialValues);
    setMessage(null);
  };

  const handleTestEmail = async () => {
    if (!testEmail || !testEmail.includes('@')) {
      setMessage({ type: 'error', text: 'Please enter a valid email address' });
      return;
    }

    if (hasChanges()) {
      setMessage({ 
        type: 'error', 
        text: 'Please save your changes before testing email configuration' 
      });
      return;
    }

    try {
      setTesting(true);
      setMessage({ type: 'info', text: `Sending test email to ${testEmail}...` });

      const response: any = await adminAPI.testEmailConfiguration(testEmail);

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: `✅ Test email sent successfully to ${testEmail}! Check your inbox.` 
        });
        setTestEmail('');
      } else {
        setMessage({ 
          type: 'error', 
          text: `Failed to send test email: ${response.error || 'Unknown error'}` 
        });
      }
    } catch (error: any) {
      console.error('Failed to send test email:', error);
      setMessage({ 
        type: 'error', 
        text: `Failed to send test email: ${error.message || 'Connection error'}` 
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading email settings...</p>
        </div>
      </div>
    );
  }

  // Group settings by type
  const smtpSettings = settings.filter(s => 
    ['email_host', 'email_port', 'email_use_ssl', 'email_timeout'].includes(s.key)
  );
  const authSettings = settings.filter(s => 
    ['email_host_user', 'email_host_password'].includes(s.key)
  );
  const fromSettings = settings.filter(s => 
    ['default_from_email'].includes(s.key)
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email Configuration</h1>
          <p className="text-gray-600">Configure SMTP settings and test email delivery</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            disabled={!hasChanges() || saving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Reset Changes
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges() || saving}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Alert Messages */}
      {message && (
        <div className={`p-4 rounded-lg border ${
          message.type === 'success' 
            ? 'bg-green-50 border-green-200' 
            : message.type === 'error'
            ? 'bg-red-50 border-red-200'
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {message.type === 'success' && (
                <svg className="h-5 w-5 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              {message.type === 'error' && (
                <svg className="h-5 w-5 text-red-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              {message.type === 'info' && (
                <svg className="h-5 w-5 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              <span className={`text-sm font-medium ${
                message.type === 'success' ? 'text-green-800' : 
                message.type === 'error' ? 'text-red-800' : 'text-blue-800'
              }`}>
                {message.text}
              </span>
            </div>
            <button 
              onClick={() => setMessage(null)} 
              className={`ml-4 ${
                message.type === 'success' ? 'text-green-600 hover:text-green-800' : 
                message.type === 'error' ? 'text-red-600 hover:text-red-800' : 
                'text-blue-600 hover:text-blue-800'
              }`}
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Test Email Section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Test Email Configuration</h3>
            <p className="text-sm text-gray-600 mb-4">Send a test email to verify your SMTP settings are configured correctly</p>
            
            <div className="flex space-x-3">
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="recipient@example.com"
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                disabled={testing}
              />
              <button
                onClick={handleTestEmail}
                disabled={testing || !testEmail || hasChanges()}
                className="px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2 shadow-sm"
              >
                {testing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    <span>Send Test Email</span>
                  </>
                )}
              </button>
            </div>
            {hasChanges() && (
              <div className="mt-3 flex items-center text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-sm font-medium">Please save your changes before testing</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SMTP Server Settings */}
        <SettingsCard
          title="SMTP Server"
          description="Mail server connection settings"
          icon="🔧"
        >
          <div className="space-y-6">
            {smtpSettings.map(setting => (
              <SettingInput
                key={setting.key}
                setting={setting}
                value={editedValues[setting.key]}
                onChange={(value) => handleValueChange(setting.key, value)}
              />
            ))}
          </div>
        </SettingsCard>

        {/* Authentication Settings */}
        <SettingsCard
          title="Authentication"
          description="SMTP login credentials"
          icon="🔐"
        >
          <div className="space-y-6">
            {authSettings.map(setting => (
              <SettingInput
                key={setting.key}
                setting={setting}
                value={editedValues[setting.key]}
                onChange={(value) => handleValueChange(setting.key, value)}
              />
            ))}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-yellow-600 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <div className="text-sm text-yellow-800">
                  <p className="font-medium mb-1">Security Notice</p>
                  <p>Passwords are encrypted before storage. For Gmail, use an App Password instead of your account password.</p>
                </div>
              </div>
            </div>
          </div>
        </SettingsCard>
      </div>

      {/* Sender Settings */}
      <SettingsCard
        title="Sender Information"
        description="Default FROM email address for outgoing emails"
        icon="✉️"
      >
        <div className="space-y-6">
          {fromSettings.map(setting => (
            <SettingInput
              key={setting.key}
              setting={setting}
              value={editedValues[setting.key]}
              onChange={(value) => handleValueChange(setting.key, value)}
            />
          ))}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Formatting Tip</p>
                <p>Use format: <code className="bg-blue-100 px-2 py-0.5 rounded text-xs">"Display Name &lt;email@domain.com&gt;"</code> for better email appearance</p>
              </div>
            </div>
          </div>
        </div>
      </SettingsCard>
    </div>
  );
}
