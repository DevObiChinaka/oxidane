'use client';

import { useEffect, useState } from 'react';
import { adminAPI } from '../../utils/api';
import { PlatformSetting } from '../../types/admin';
import { SettingsCard } from '../components/SettingsCard';
import { SettingInput } from '../components/SettingInput';

export default function SystemHealthPage() {
  const [settings, setSettings] = useState<PlatformSetting[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsRes, statsRes]: any = await Promise.all([
        adminAPI.getSettings('system'),
        adminAPI.getSettingsStats()
      ]);

      if (settingsRes.success) {
        setSettings(settingsRes.settings);
        const initialValues: Record<string, any> = {};
        settingsRes.settings.forEach((setting: PlatformSetting) => {
          initialValues[setting.key] = setting.value;
        });
        setEditedValues(initialValues);
      }

      if (statsRes.success) {
        setStats(statsRes.stats);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      setMessage({ type: 'error', text: 'Failed to load system settings' });
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

      // Check if maintenance mode is being enabled
      const maintenanceModeChange = changedSettings.find(s => s.key === 'maintenance_mode');
      if (maintenanceModeChange && maintenanceModeChange.value === true) {
        if (!confirm('⚠️ WARNING: Enabling maintenance mode will block all non-admin users from accessing the platform. Continue?')) {
          setSaving(false);
          return;
        }
      }

      const response: any = await adminAPI.bulkUpdateSettings(
        changedSettings,
        'Updated system settings via admin panel'
      );

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: `Successfully updated ${response.updated} system setting(s)` 
        });
        await loadData();
      } else {
        setMessage({ type: 'error', text: 'Failed to save system settings' });
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: 'Failed to save system settings' });
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

  const maintenanceMode = editedValues['maintenance_mode'] || false;
  const cacheEnabled = editedValues['cache_enabled'] || false;

  // Group settings
  const maintenanceSettings = settings.filter(s => 
    ['maintenance_mode', 'maintenance_message'].includes(s.key)
  );
  const cacheSettings = settings.filter(s => 
    ['cache_enabled', 'cache_ttl'].includes(s.key)
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
          <p className="text-gray-600">Monitor platform status and manage system configuration</p>
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
            : message.type === 'warning'
            ? 'bg-orange-50 border-orange-200'
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
              {message.type === 'warning' && (
                <svg className="h-5 w-5 text-orange-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
              {message.type === 'info' && (
                <svg className="h-5 w-5 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              <span className={`text-sm font-medium ${
                message.type === 'success' ? 'text-green-800' : 
                message.type === 'error' ? 'text-red-800' : 
                message.type === 'warning' ? 'text-orange-800' : 
                'text-blue-800'
              }`}>
                {message.text}
              </span>
            </div>
            <button 
              onClick={() => setMessage(null)} 
              className={`ml-4 ${
                message.type === 'success' ? 'text-green-600 hover:text-green-800' : 
                message.type === 'error' ? 'text-red-600 hover:text-red-800' : 
                message.type === 'warning' ? 'text-orange-600 hover:text-orange-800' : 
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

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`rounded-lg border-2 p-6 transition-all ${
          maintenanceMode 
            ? 'bg-red-50 border-red-300' 
            : 'bg-green-50 border-green-300'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600 mb-1">Platform Status</p>
              <div className="flex items-center">
                {maintenanceMode ? (
                  <>
                    <div className="w-3 h-3 bg-red-500 rounded-full mr-2 animate-pulse"></div>
                    <span className="text-xl font-bold text-red-700">Maintenance Mode</span>
                  </>
                ) : (
                  <>
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-xl font-bold text-green-700">Online</span>
                  </>
                )}
              </div>
            </div>
            <div className={`p-3 rounded-lg ${maintenanceMode ? 'bg-red-100' : 'bg-green-100'}`}>
              <svg className={`h-8 w-8 ${maintenanceMode ? 'text-red-600' : 'text-green-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {maintenanceMode ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                )}
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 hover:border-blue-300 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600 mb-1">Cache Status</p>
              <div className="flex items-center">
                {cacheEnabled ? (
                  <>
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                    <span className="text-xl font-bold text-blue-700">Enabled</span>
                  </>
                ) : (
                  <>
                    <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                    <span className="text-xl font-bold text-gray-500">Disabled</span>
                  </>
                )}
              </div>
            </div>
            <div className={`p-3 rounded-lg ${cacheEnabled ? 'bg-blue-100' : 'bg-gray-100'}`}>
              <svg className={`h-8 w-8 ${cacheEnabled ? 'text-blue-600' : 'text-gray-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600 mb-1">Total Settings</p>
              <p className="text-3xl font-bold text-purple-700">
                {stats?.total_settings || 0}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="h-5 w-5 mr-2 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Platform Statistics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
              <div className="flex justify-center mb-2">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-blue-700">{stats.active_telegram_groups}</p>
              <p className="text-xs text-gray-600 mt-1">Active Groups</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-100">
              <div className="flex justify-center mb-2">
                <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-green-700">{stats.total_backups}</p>
              <p className="text-xs text-gray-600 mt-1">Total Backups</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-100">
              <div className="flex justify-center mb-2">
                <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-purple-700">{stats.encrypted_settings}</p>
              <p className="text-xs text-gray-600 mt-1">Encrypted</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-100">
              <div className="flex justify-center mb-2">
                <svg className="h-8 w-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-orange-700">{stats.recent_changes_7days}</p>
              <p className="text-xs text-gray-600 mt-1">Recent Changes</p>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Maintenance Mode */}
        <SettingsCard
          title="Maintenance Mode"
          description="Control platform availability"
          icon="�"
        >
          {maintenanceMode && (
            <div className="mb-6 bg-red-50 border-2 border-red-300 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="h-6 w-6 text-red-600 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              <div>
                <p className="font-bold text-red-900">Maintenance Mode is ACTIVE</p>
                <p className="text-sm text-red-800 mt-1">
                  All non-admin users are currently blocked from accessing the platform.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {maintenanceSettings.map(setting => (
            <SettingInput
              key={setting.key}
              setting={setting}
              value={editedValues[setting.key]}
              onChange={(value) => handleValueChange(setting.key, value)}
            />
          ))}
        </div>
      </SettingsCard>

        {/* Cache Configuration */}
        <SettingsCard
          title="Cache Configuration"
          description="Manage caching settings"
          icon="💾"
        >
          <div className="space-y-6">
            {cacheSettings.map(setting => (
              <SettingInput
                key={setting.key}
                setting={setting}
                value={editedValues[setting.key]}
                onChange={(value) => handleValueChange(setting.key, value)}
              />
            ))}

            {cacheEnabled && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Cache Information</p>
                    <p>
                      Caching improves performance by storing frequently accessed data. 
                      TTL (Time To Live) determines how long data stays cached before refresh.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </SettingsCard>
      </div>
    </div>
  );
}
