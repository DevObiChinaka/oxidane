'use client';

import { useEffect, useState } from 'react';
import { adminAPI } from '../../utils/api';
import { PlatformSetting, TelegramGroup, TelegramAccessLevel } from '../../types/admin';
import { SettingsCard } from '../components/SettingsCard';
import { SettingInput } from '../components/SettingInput';

export default function TelegramIntegrationPage() {
  const [settings, setSettings] = useState<PlatformSetting[]>([]);
  const [groups, setGroups] = useState<TelegramGroup[]>([]);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [showAddGroup, setShowAddGroup] = useState(false);
  const [editingGroup, setEditingGroup] = useState<TelegramGroup | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsRes, groupsRes]: any = await Promise.all([
        adminAPI.getSettings('telegram'),
        adminAPI.getTelegramGroups()
      ]);

      if (settingsRes.success) {
        setSettings(settingsRes.settings);
        const initialValues: Record<string, any> = {};
        settingsRes.settings.forEach((setting: PlatformSetting) => {
          initialValues[setting.key] = setting.value;
        });
        setEditedValues(initialValues);
      }

      if (groupsRes.success) {
        setGroups(groupsRes.groups);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      setMessage({ type: 'error', text: 'Failed to load Telegram settings' });
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

      const response: any = await adminAPI.bulkUpdateSettings(
        changedSettings,
        'Updated Telegram bot configuration via admin panel'
      );

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: `Successfully updated ${response.updated} bot setting(s)` 
        });
        await loadData();
      } else {
        setMessage({ type: 'error', text: 'Failed to save bot settings' });
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: 'Failed to save bot settings' });
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

  const handleTestBot = async () => {
    if (hasChanges()) {
      setMessage({ type: 'error', text: 'Please save your changes before testing bot connection' });
      return;
    }

    try {
      setTesting(true);
      setMessage({ type: 'info', text: 'Testing bot connection...' });

      const response: any = await adminAPI.testBotConnection();

      if (response.success) {
        const bot = response.bot_info;
        setMessage({ 
          type: 'success', 
          text: `✅ Bot connected! @${bot.username} (${bot.first_name}) - Can join groups: ${bot.can_join_groups ? 'Yes' : 'No'}` 
        });
      } else {
        setMessage({ type: 'error', text: `Failed: ${response.error}` });
      }
    } catch (error: any) {
      console.error('Failed to test bot:', error);
      setMessage({ type: 'error', text: `Connection error: ${error.message}` });
    } finally {
      setTesting(false);
    }
  };

  const handleSyncMembers = async (groupId: number) => {
    try {
      const response: any = await adminAPI.syncGroupMembers(groupId);
      if (response.success) {
        setMessage({ type: 'success', text: `Synced! Member count: ${response.member_count}` });
        await loadData();
      } else {
        setMessage({ type: 'error', text: response.error });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: `Sync failed: ${error.message}` });
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm('Are you sure you want to remove this group reference? (This will not delete the actual Telegram group)')) {
      return;
    }

    try {
      const response: any = await adminAPI.deleteTelegramGroup(groupId);
      if (response.success) {
        setMessage({ type: 'success', text: 'Group removed successfully' });
        await loadData();
      } else {
        setMessage({ type: 'error', text: 'Failed to remove group' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to remove group' });
    }
  };

  const handleSaveGroup = async (groupData: Partial<TelegramGroup>) => {
    try {
      const response: any = editingGroup
        ? await adminAPI.updateTelegramGroup(editingGroup.id, groupData)
        : await adminAPI.createTelegramGroup(groupData);

      if (response.success) {
        setMessage({ 
          type: 'success', 
          text: editingGroup ? 'Group updated successfully' : 'Group added successfully' 
        });
        setShowAddGroup(false);
        setEditingGroup(null);
        await loadData();
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to save group' });
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to save group' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading Telegram settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Telegram Integration</h1>
          <p className="text-gray-600">Manage bot configuration and group memberships</p>
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
                <span>💾</span>
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Alert Messages */}
      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-800' 
            : message.type === 'error'
            ? 'bg-red-50 border border-red-200 text-red-800'
            : 'bg-blue-50 border border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="mr-2">
                {message.type === 'success' ? '✅' : message.type === 'error' ? '❌' : 'ℹ️'}
              </span>
              {message.text}
            </div>
            <button onClick={() => setMessage(null)} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Setup Instructions */}
      <SettingsCard
        title="Setup Instructions"
        description="How to configure your Telegram bot and groups"
        icon="📖"
      >
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="text-blue-600 hover:text-blue-700 font-medium text-sm flex items-center"
        >
          {showInstructions ? '▼' : '▶'} {showInstructions ? 'Hide' : 'Show'} Instructions
        </button>

        {showInstructions && (
          <div className="mt-4 space-y-4 text-sm text-gray-700">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">1. Create a Telegram Bot</h4>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Open Telegram and search for <code className="bg-gray-200 px-1">@BotFather</code></li>
                <li>Send <code className="bg-gray-200 px-1">/newbot</code> command</li>
                <li>Follow the prompts to set bot name and username</li>
                <li>Copy the API token provided</li>
                <li>Paste the token in the "Bot Token" field below</li>
              </ol>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">2. Create Telegram Groups</h4>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Create a new group in Telegram</li>
                <li>Add your bot as a member (search by username)</li>
                <li>Promote the bot to Admin with "Add Members" permission</li>
                <li>For private groups, disable invite links</li>
              </ol>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">3. Get Chat ID</h4>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Add <code className="bg-gray-200 px-1">@userinfobot</code> to your group</li>
                <li>The bot will display the group's Chat ID</li>
                <li>Copy the ID (including the minus sign, e.g., -1002920074390)</li>
                <li>Use this Chat ID when registering the group below</li>
              </ol>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
              <p className="font-semibold text-yellow-800">⚠️ Important Notes:</p>
              <ul className="list-disc list-inside space-y-1 ml-2 text-yellow-700 mt-2">
                <li>Private groups must have "Invite via link" disabled</li>
                <li>Bot must be admin to add/remove members automatically</li>
                <li>Public groups can have invite links for manual joining</li>
                <li>This panel only manages references - groups must be created on Telegram first</li>
              </ul>
            </div>
          </div>
        )}
      </SettingsCard>

      {/* Test Bot Connection */}
      <SettingsCard
        title="Test Bot Connection"
        description="Verify your bot token is working"
        icon="🔌"
      >
        <div className="flex items-center space-x-3">
          <button
            onClick={handleTestBot}
            disabled={testing || hasChanges()}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {testing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Testing...</span>
              </>
            ) : (
              <>
                <span>🤖</span>
                <span>Test Bot Connection</span>
              </>
            )}
          </button>
          {hasChanges() && (
            <p className="text-xs text-orange-600">⚠️ Save changes first</p>
          )}
        </div>
      </SettingsCard>

      {/* Bot Configuration */}
      <SettingsCard
        title="Bot Configuration"
        description="Configure your Telegram bot settings"
        icon="🤖"
      >
        <div className="space-y-6">
          {settings.map(setting => (
            <SettingInput
              key={setting.key}
              setting={setting}
              value={editedValues[setting.key]}
              onChange={(value) => handleValueChange(setting.key, value)}
            />
          ))}
        </div>
      </SettingsCard>

      {/* Save Bot Settings */}
      <div className="flex items-center justify-end space-x-3 bg-white px-6 py-4 rounded-lg border border-gray-200">
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
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Saving...</span>
            </>
          ) : (
            <>
              <span>💾</span>
              <span>Save Bot Settings</span>
            </>
          )}
        </button>
      </div>

      {/* Telegram Groups */}
      <SettingsCard
        title="Telegram Groups Registry"
        description={`Manage references to your ${groups.length} Telegram group(s)`}
        icon="👥"
        actions={
          <button
            onClick={() => { setShowAddGroup(true); setEditingGroup(null); }}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
          >
            + Add Group
          </button>
        }
      >
        <div className="space-y-4">
          {groups.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg mb-2">📭 No groups registered yet</p>
              <p className="text-sm">Click "Add Group" to register your first Telegram group</p>
            </div>
          ) : (
            groups.map((group) => (
              <GroupCard
                key={group.id}
                group={group}
                onEdit={(g) => { setEditingGroup(g); setShowAddGroup(true); }}
                onDelete={handleDeleteGroup}
                onSync={handleSyncMembers}
              />
            ))
          )}
        </div>
      </SettingsCard>

      {/* Add/Edit Group Modal */}
      {showAddGroup && (
        <GroupModal
          group={editingGroup}
          onSave={handleSaveGroup}
          onClose={() => { setShowAddGroup(false); setEditingGroup(null); }}
        />
      )}
    </div>
  );
}

// Group Card Component
function GroupCard({ group, onEdit, onDelete, onSync }: {
  group: TelegramGroup;
  onEdit: (group: TelegramGroup) => void;
  onDelete: (id: number) => void;
  onSync: (id: number) => void;
}) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    await onSync(group.id);
    setSyncing(false);
  };

  return (
    <div className="border border-gray-200 rounded-lg p-5 hover:border-blue-300 transition-colors bg-white">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h4 className="font-semibold text-lg text-gray-900">{group.name}</h4>
            {group.is_public && <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded font-medium">PUBLIC</span>}
            {!group.is_active && <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded font-medium">INACTIVE</span>}
          </div>
          
          <p className="text-sm text-gray-600 mb-3">{group.description || 'No description'}</p>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 font-medium">Chat ID:</span>
              <code className="ml-2 bg-gray-100 px-2 py-1 rounded text-xs text-gray-900">{group.chat_id}</code>
            </div>
            <div>
              <span className="text-gray-500 font-medium">Key:</span>
              <code className="ml-2 bg-gray-100 px-2 py-1 rounded text-xs text-gray-900">{group.group_key}</code>
            </div>
            <div>
              <span className="text-gray-500 font-medium">Access Level:</span>
              <span className="ml-2 font-medium text-gray-900">{group.access_level_display}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium">Members:</span>
              <span className="ml-2 font-medium text-gray-900">{group.member_count}</span>
              {group.last_sync_at && (
                <span className="ml-1 text-xs text-gray-500">
                  (synced {new Date(group.last_sync_at).toLocaleDateString()})
                </span>
              )}
            </div>
          </div>

          {group.is_public && group.invite_link && (
            <div className="mt-3">
              <a
                href={group.invite_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center font-medium"
              >
                🔗 {group.invite_link}
              </a>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
            title="Sync member count"
          >
            {syncing ? (
              <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full"></div>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
          </button>
          <button
            onClick={() => onEdit(group)}
            className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
            title="Edit group"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={() => {
              if (confirm(`Are you sure you want to remove "${group.name}"?`)) {
                onDelete(group.id);
              }
            }}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Remove group"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

// Group Modal Component
function GroupModal({ group, onSave, onClose }: {
  group: TelegramGroup | null;
  onSave: (data: Partial<TelegramGroup>) => void;
  onClose: () => void;
}) {
  const [formData, setFormData] = useState({
    name: group?.name || '',
    chat_id: group?.chat_id || '',
    group_key: group?.group_key || '',
    access_level: (group?.access_level || 'monthly') as TelegramAccessLevel,
    description: group?.description || '',
    is_active: group?.is_active ?? true,
    auto_add_users: group?.auto_add_users ?? true,
    auto_remove_expired: group?.auto_remove_expired ?? true,
    welcome_message_enabled: group?.welcome_message_enabled ?? true,
    welcome_message_template: group?.welcome_message_template || '',
    is_public: group?.is_public ?? false,
    invite_link: group?.invite_link || '',
    sort_order: group?.sort_order || 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">
              {group ? 'Edit Group' : 'Add New Group'}
            </h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Basic Info */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Group Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Chat ID * (e.g., -1002920074390)
              </label>
              <input
                type="text"
                value={formData.chat_id}
                onChange={(e) => setFormData({ ...formData, chat_id: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="-1234567890"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Group Key * (lowercase_underscore)
              </label>
              <input
                type="text"
                value={formData.group_key}
                onChange={(e) => setFormData({ ...formData, group_key: e.target.value.toLowerCase() })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="premium_signals"
                pattern="[a-z_]+"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Access Level
              </label>
              <select
                value={formData.access_level}
                onChange={(e) => setFormData({ ...formData, access_level: e.target.value as TelegramAccessLevel })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="all">All Paid Subscribers</option>
                <option value="weekly">Weekly+ Subscribers</option>
                <option value="monthly">Monthly+ Subscribers</option>
                <option value="vip">VIP Only</option>
                <option value="mentorship">Mentorship Members</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Display Order
              </label>
              <input
                type="number"
                value={formData.sort_order}
                onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                min="0"
              />
            </div>
          </div>

          {/* Public Group Settings */}
          <div className="border border-gray-200 rounded-lg p-4">
            <label className="flex items-center space-x-2 mb-3">
              <input
                type="checkbox"
                checked={formData.is_public}
                onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm font-medium text-gray-900">This is a public group (users can join via invite link)</span>
            </label>

            {formData.is_public && (
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">
                  Invite Link
                </label>
                <input
                  type="url"
                  value={formData.invite_link}
                  onChange={(e) => setFormData({ ...formData, invite_link: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="https://t.me/joinchat/..."
                />
              </div>
            )}
          </div>

          {/* Automation Settings */}
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            <h4 className="font-medium text-sm text-gray-900">Automation Settings</h4>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-900">Group is active</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.auto_add_users}
                onChange={(e) => setFormData({ ...formData, auto_add_users: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-900">Auto-add verified users</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.auto_remove_expired}
                onChange={(e) => setFormData({ ...formData, auto_remove_expired: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-900">Auto-remove expired subscriptions</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.welcome_message_enabled}
                onChange={(e) => setFormData({ ...formData, welcome_message_enabled: e.target.checked })}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-900">Send welcome message</span>
            </label>
          </div>

          {/* Welcome Message Template */}
          {formData.welcome_message_enabled && (
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Welcome Message Template
              </label>
              <textarea
                value={formData.welcome_message_template}
                onChange={(e) => setFormData({ ...formData, welcome_message_template: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm text-gray-900"
                rows={4}
                placeholder="Welcome {{user_name}} to {group_name}! You have access as a {{plan_type}} subscriber."
              />
              <p className="mt-1 text-xs text-gray-500">
                Use variables: {'{'}{'{'} user_name {'}'}{'}'},  {'{'}{'{'} plan_type {'}'}{'}'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              {group ? 'Update Group' : 'Add Group'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
