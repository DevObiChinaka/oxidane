'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface TelegramConfig {
  id?: number;
  bot_token?: string;  // write-only, only used when setting new token
  masked_token?: string;  // read-only, displayed to user
  bot_username: string;
  is_enabled: boolean;
  is_connected: boolean;
  connection_error: string;
  last_health_check: string | null;
  auto_add_enabled: boolean;
  auto_remove_enabled: boolean;
  welcome_message: string;
  removal_message: string;
  max_retries: number;
  retry_delay_seconds: number;
  rate_limit_per_minute: number;
  has_valid_token_format?: boolean;  // read-only
  is_healthy?: boolean;  // read-only
}

interface BotInfo {
  id: number;
  username: string;
  first_name: string;
  can_join_groups: boolean;
  can_read_all_group_messages: boolean;
}

export default function TelegramConfigurationPage() {
  const [config, setConfig] = useState<TelegramConfig | null>(null);
  const [editedConfig, setEditedConfig] = useState<Partial<TelegramConfig>>({});
  const [newBotToken, setNewBotToken] = useState<string>('');  // Track new token input
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [botInfo, setBotInfo] = useState<BotInfo | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null);

  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://127.0.0.1:8000/api/admin/telegram/config/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Failed to load configuration');

      const data = await response.json();
      // API returns a list with one item (singleton pattern)
      const configData = Array.isArray(data) ? data[0] : data;
      setConfig(configData);
      setEditedConfig(configData);
    } catch (error) {
      console.error('Failed to load Telegram configuration:', error);
      setMessage({ type: 'error', text: 'Failed to load Telegram configuration' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      const token = localStorage.getItem('access_token');

      // Prepare payload - include new bot token if it was changed
      const payload = { ...editedConfig };
      if (newBotToken) {
        payload.bot_token = newBotToken;
      }

      const response = await fetch('http://127.0.0.1:8000/api/admin/telegram/config/', {
        method: 'POST',  // Use POST for singleton create-or-update
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to save configuration');

      const data = await response.json();
      // POST returns single object (not a list)
      setConfig(data);
      setEditedConfig(data);
      setNewBotToken('');  // Clear the new token input after save
      setMessage({ type: 'success', text: 'Telegram configuration saved successfully' });
    } catch (error) {
      console.error('Failed to save configuration:', error);
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      setMessage({ type: 'info', text: 'Testing bot connection...' });
      const token = localStorage.getItem('access_token');

      const response = await fetch('http://127.0.0.1:8000/api/admin/telegram/config/test-connection/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        setBotInfo(data.bot_info);
        setMessage({ 
          type: 'success', 
          text: `Bot connected successfully! (@${data.bot_info.username})` 
        });
        // Reload config to get updated connection status
        await loadConfiguration();
      } else {
        setMessage({ type: 'error', text: data.error || 'Connection test failed' });
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setMessage({ type: 'error', text: 'Failed to test connection' });
    } finally {
      setTesting(false);
    }
  };

  const hasChanges = () => {
    if (!config) return false;
    // Check if config fields changed OR if new bot token was entered
    return newBotToken.trim() !== '' || JSON.stringify(config) !== JSON.stringify(editedConfig);
  };

  const handleReset = () => {
    if (config) {
      setEditedConfig({ ...config });
      setNewBotToken('');  // Clear new token input
      setMessage(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                {/* Official Telegram Paper Plane Icon */}
                <svg className="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Telegram Bot Configuration
                </h1>
                <p className="text-gray-600 mt-0.5 text-sm">Automate group member management with your Telegram bot</p>
              </div>
            </div>
          </div>
          <Link 
            href="/admin/telegram-groups"
            className="px-5 py-2.5 bg-white text-gray-700 rounded-xl hover:bg-gray-50 transition-all text-sm font-semibold border border-gray-200 shadow-sm hover:shadow flex items-center gap-2"
          >
            <span>Manage Groups</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        {/* Connection Status Banner */}
        {config && (
          <div className={`rounded-xl p-6 shadow-sm border-2 ${
            config.is_connected 
              ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300' 
              : 'bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-300'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  config.is_connected ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300' : 'bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-300'
                }`}>
                  {config.is_connected ? (
                    <div className="w-3 h-3 bg-green-500 rounded-full shadow-lg animate-pulse"></div>
                  ) : (
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  )}
                </div>
                <div>
                  <p className="text-lg font-bold text-gray-900">
                    {config.is_connected ? 'Bot Connected & Active' : 'Bot Not Connected'}
                  </p>
                  {config.is_connected && config.bot_username && (
                    <p className="text-sm font-medium text-gray-700 mt-0.5">@{config.bot_username}</p>
                  )}
                  {!config.is_connected && (
                    <p className="text-sm text-gray-700 mt-0.5">Configure your bot token below and test the connection</p>
                  )}
                </div>
              </div>
              {config.last_health_check && (
                <div className="text-right">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Last Checked</p>
                  <p className="text-sm font-medium text-gray-700 mt-0.5">
                    {new Date(config.last_health_check).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Messages */}
        {message && (
          <div className={`rounded-xl p-5 shadow-sm border-l-4 ${
            message.type === 'success' ? 'bg-green-50 border-green-500' :
            message.type === 'error' ? 'bg-red-50 border-red-500' :
            message.type === 'warning' ? 'bg-yellow-50 border-yellow-500' :
            'bg-blue-50 border-blue-500'
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 ${
                  message.type === 'success' ? 'text-green-600' :
                  message.type === 'error' ? 'text-red-600' :
                  message.type === 'warning' ? 'text-yellow-600' :
                  'text-blue-600'
                }`}>
                  {message.type === 'success' && (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  )}
                  {message.type === 'error' && (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                  {message.type === 'warning' && (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  )}
                  {message.type === 'info' && (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <p className={`text-sm font-medium leading-relaxed ${
                  message.type === 'success' ? 'text-green-900' :
                  message.type === 'error' ? 'text-red-900' :
                  message.type === 'warning' ? 'text-yellow-900' :
                  'text-blue-900'
                }`}>
                  {message.text}
                </p>
              </div>
              <button 
                onClick={() => setMessage(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

      {/* Setup Instructions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-2">
            <span className="text-2xl">📖</span>
            <div>
              <h3 className="font-semibold text-gray-900">Setup Instructions</h3>
              <p className="text-sm text-gray-600">How to create and configure your Telegram bot</p>
            </div>
          </div>
          <span className="text-gray-400">{showInstructions ? '▼' : '▶'}</span>
        </button>

        {showInstructions && (
          <div className="mt-6 space-y-4 text-sm">
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <h4 className="font-semibold text-gray-900">1️⃣ Create Your Telegram Bot</h4>
              <ol className="list-decimal list-inside space-y-1 text-gray-700 ml-2">
                <li>Open Telegram and search for <code className="bg-gray-200 px-1.5 py-0.5 rounded">@BotFather</code></li>
                <li>Send the command <code className="bg-gray-200 px-1.5 py-0.5 rounded">/newbot</code></li>
                <li>Choose a name for your bot (e.g., "MyPlatform Signals Bot")</li>
                <li>Choose a username ending in "bot" (e.g., "myplatform_bot")</li>
                <li>Copy the API token (format: <code className="bg-gray-200 px-1.5 py-0.5 rounded">123456:ABC-DEF...</code>)</li>
              </ol>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <h4 className="font-semibold text-gray-900">2️⃣ Configure Bot Token</h4>
              <ol className="list-decimal list-inside space-y-1 text-gray-700 ml-2">
                <li>Paste the API token in the "Bot Token" field below</li>
                <li>Click "Save Configuration" to store the token</li>
                <li>Click "Test Connection" to verify it works</li>
              </ol>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <h4 className="font-semibold text-gray-900">3️⃣ Create Telegram Groups</h4>
              <ol className="list-decimal list-inside space-y-1 text-gray-700 ml-2">
                <li>Create groups in Telegram for your subscribers</li>
                <li>Add your bot to each group (search by username)</li>
                <li>Promote the bot to Admin with "Add Members" permission</li>
                <li>Go to <Link href="/admin/telegram-groups" className="text-blue-600 hover:underline font-medium">Telegram Groups</Link> to register them</li>
              </ol>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <p className="font-semibold text-blue-900">💡 Pro Tips</p>
              <ul className="list-disc list-inside space-y-1 text-blue-800 mt-2 ml-2 text-sm">
                <li>Use a descriptive bot name that represents your platform</li>
                <li>The bot token is sensitive - keep it secure</li>
                <li>Test connection after any configuration changes</li>
                <li>Enable automation settings after verifying bot works</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Bot Credentials */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🔑</span>
          <div>
            <h3 className="font-semibold text-gray-900">Bot Credentials</h3>
            <p className="text-sm text-gray-600">Your Telegram bot API token from @BotFather</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bot Token <span className="text-red-500">*</span>
            </label>
            {config?.masked_token && config.masked_token !== '(not set)' ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={config.masked_token}
                    disabled
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
                  />
                  <button
                    onClick={() => setNewBotToken('')}
                    className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50"
                  >
                    Change Token
                  </button>
                </div>
                <p className="text-xs text-gray-500">
                  Token is set and encrypted. Click "Change Token" to update it.
                </p>
              </div>
            ) : (
              <div>
                <input
                  type="password"
                  value={newBotToken}
                  onChange={(e) => setNewBotToken(e.target.value)}
                  placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Get this from @BotFather when you create your bot
                </p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bot Username
            </label>
            <input
              type="text"
              value={editedConfig.bot_username || ''}
              onChange={(e) => setEditedConfig({ ...editedConfig, bot_username: e.target.value })}
              placeholder="@yourplatform_bot"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
            />
            <p className="text-xs text-gray-500 mt-1">
              Optional: Will be auto-detected when you test connection
            </p>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleTestConnection}
              disabled={testing || !(config?.masked_token !== '(not set)' || newBotToken) || hasChanges()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {testing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Testing...</span>
                </>
              ) : (
                <>
                  <span>🔌</span>
                  <span>Test Connection</span>
                </>
              )}
            </button>
            {hasChanges() && (
              <p className="text-sm text-yellow-600">⚠️ Save changes first before testing</p>
            )}
          </div>

          {botInfo && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
              <p className="font-semibold text-green-900 mb-2">✅ Bot Information</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-600">Username:</span>
                  <span className="ml-2 font-medium text-gray-900">@{botInfo.username}</span>
                </div>
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium text-gray-900">{botInfo.first_name}</span>
                </div>
                <div>
                  <span className="text-gray-600">Can Join Groups:</span>
                  <span className="ml-2 font-medium text-gray-900">{botInfo.can_join_groups ? '✅ Yes' : '❌ No'}</span>
                </div>
                <div>
                  <span className="text-gray-600">Can Read Messages:</span>
                  <span className="ml-2 font-medium text-gray-900">{botInfo.can_read_all_group_messages ? '✅ Yes' : '❌ No'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Automation Settings */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 space-y-6">
        <div className="flex items-start gap-4 pb-4 border-b border-gray-100">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Automation Settings</h3>
            <p className="text-sm text-gray-600 mt-1">Control how your bot manages Telegram group memberships</p>
          </div>
        </div>

        <div className="space-y-5">
          <label className="flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-purple-200 hover:bg-purple-50/30 transition-all cursor-pointer group">
            <input
              type="checkbox"
              checked={editedConfig.is_enabled ?? true}
              onChange={(e) => setEditedConfig({ ...editedConfig, is_enabled: e.target.checked })}
              className="mt-1 w-5 h-5 rounded border-gray-300 text-purple-600 focus:ring-purple-500 focus:ring-offset-2 cursor-pointer"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 text-base">Enable Telegram Integration</span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                  editedConfig.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {editedConfig.is_enabled ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-sm text-gray-700 mt-1 leading-relaxed">
                Master switch for all Telegram automation features. When disabled, no automatic group operations will occur.
              </p>
            </div>
          </label>

          <label className="flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-blue-200 hover:bg-blue-50/30 transition-all cursor-pointer group">
            <input
              type="checkbox"
              checked={editedConfig.auto_add_enabled ?? true}
              onChange={(e) => setEditedConfig({ ...editedConfig, auto_add_enabled: e.target.checked })}
              className="mt-1 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 text-base">Auto-Add to Groups</span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                  editedConfig.auto_add_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {editedConfig.auto_add_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="text-sm text-gray-700 mt-1 leading-relaxed">
                Automatically add users to their subscribed Telegram groups when they complete payment. Users receive instant access.
              </p>
            </div>
          </label>

          <label className="flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-orange-200 hover:bg-orange-50/30 transition-all cursor-pointer group">
            <input
              type="checkbox"
              checked={editedConfig.auto_remove_enabled ?? true}
              onChange={(e) => setEditedConfig({ ...editedConfig, auto_remove_enabled: e.target.checked })}
              className="mt-1 w-5 h-5 rounded border-gray-300 text-orange-600 focus:ring-orange-500 focus:ring-offset-2 cursor-pointer"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 text-base">Auto-Remove Expired Users</span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                  editedConfig.auto_remove_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {editedConfig.auto_remove_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="text-sm text-gray-700 mt-1 leading-relaxed">
                Automatically remove users from groups when their subscription expires or is cancelled. Protects exclusive content.
              </p>
            </div>
          </label>
        </div>

        {(editedConfig.is_enabled === false) && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
            <svg className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-semibold text-amber-900 text-sm">Integration Disabled</p>
              <p className="text-sm text-amber-800 mt-0.5">
                Telegram integration is currently disabled. No automatic operations will occur until you enable it.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Welcome & Removal Messages */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">💬</span>
          <div>
            <h3 className="font-semibold text-gray-900">Automated Messages</h3>
            <p className="text-sm text-gray-600">Messages sent to users automatically</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Welcome Message
            </label>
            <textarea
              rows={3}
              value={editedConfig.welcome_message || ''}
              onChange={(e) => setEditedConfig({ ...editedConfig, welcome_message: e.target.value })}
              placeholder="Welcome to our premium signals group! You now have access to exclusive trading signals and market analysis."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
            />
            <p className="text-xs text-gray-500 mt-1">
              Sent to users when they're added to a group
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Removal Message
            </label>
            <textarea
              rows={3}
              value={editedConfig.removal_message || ''}
              onChange={(e) => setEditedConfig({ ...editedConfig, removal_message: e.target.value })}
              placeholder="Your subscription has expired. To continue receiving premium signals, please renew your subscription."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
            />
            <p className="text-xs text-gray-500 mt-1">
              Sent to users when they're removed due to expired subscription
            </p>
          </div>
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🛠️</span>
          <div>
            <h3 className="font-semibold text-gray-900">Advanced Settings</h3>
            <p className="text-sm text-gray-600">Queue and rate limit configuration</p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Retries
            </label>
            <input
              type="number"
              min="0"
              max="10"
              value={editedConfig.max_retries ?? 3}
              onChange={(e) => setEditedConfig({ ...editedConfig, max_retries: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            />
            <p className="text-xs text-gray-500 mt-1">
              Retry failed operations
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Retry Delay (seconds)
            </label>
            <input
              type="number"
              min="60"
              max="3600"
              step="60"
              value={editedConfig.retry_delay_seconds ?? 300}
              onChange={(e) => setEditedConfig({ ...editedConfig, retry_delay_seconds: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            />
            <p className="text-xs text-gray-500 mt-1">
              Delay between retries
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rate Limit (per minute)
            </label>
            <input
              type="number"
              min="10"
              max="60"
              value={editedConfig.rate_limit_per_minute ?? 30}
              onChange={(e) => setEditedConfig({ ...editedConfig, rate_limit_per_minute: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
            />
            <p className="text-xs text-gray-500 mt-1">
              API calls per minute
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="sticky bottom-0 z-10 bg-white border-t-2 border-gray-200 shadow-2xl rounded-t-xl">
        <div className="max-w-6xl mx-auto px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {hasChanges() && (
              <div className="flex items-center gap-2 text-amber-600 bg-amber-50 px-4 py-2 rounded-lg border border-amber-200">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="text-sm font-semibold">Unsaved Changes</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleReset}
              disabled={!hasChanges() || saving}
              className="px-6 py-2.5 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold text-sm hover:border-gray-400"
            >
              Reset Changes
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges() || saving}
              className="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold text-sm shadow-lg hover:shadow-xl flex items-center gap-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Saving Configuration...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  <span>Save Configuration</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
