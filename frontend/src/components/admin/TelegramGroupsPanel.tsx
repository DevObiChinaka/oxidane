'use client';

import React, { useState, useEffect } from 'react';
import { usePricingPlans } from '../../app/admin/hooks/useAdminAPI';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  UsersIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClipboardDocumentIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';

interface TelegramGroup {
  id: string;
  name: string;
  chat_id: string;
  invite_link: string;
  description?: string;
  member_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  permissions: {
    can_send_messages: boolean;
    can_add_users: boolean;
    can_remove_users: boolean;
    is_admin: boolean;
  };
}

interface TelegramGroupsStats {
  total_groups: number;
  active_groups: number;
  total_members: number;
  bot_status: 'connected' | 'disconnected' | 'error';
}

interface PricingPlan {
  id: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  current_price?: number;
  currency: string;
  plan_category: 'signals' | 'mentorship' | 'vip';
  billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
  telegram_groups: string[];
  is_active: boolean;
  is_featured: boolean;
  subscription_count?: number;
  revenue_total?: number;
  created_at: string;
  updated_at: string;
}

interface TelegramGroupsPanelProps {
  onRefresh: () => void;
}

export default function TelegramGroupsPanel({ onRefresh }: TelegramGroupsPanelProps) {
  const [groups, setGroups] = useState<TelegramGroup[]>([]);
  const [stats, setStats] = useState<TelegramGroupsStats>({
    total_groups: 0,
    active_groups: 0,
    total_members: 0,
    bot_status: 'connected'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<TelegramGroup | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState<TelegramGroup | null>(null);
  const [showPricingPlans, setShowPricingPlans] = useState(true);

  // Get pricing plans to show associated telegram groups
  const { data: pricingPlans, loading: plansLoading, error: plansError } = usePricingPlans({});

  useEffect(() => {
    loadGroupsData();
  }, []);

  const loadGroupsData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Mock data - replace with actual API calls
      const mockGroups: TelegramGroup[] = [
        {
          id: '1',
          name: 'Main Signals Group',
          chat_id: '-1001234567890',
          invite_link: 'https://t.me/+MainSignalsGroup123',
          description: 'Main signals group for all subscribers (weekly, monthly, yearly)',
          member_count: 4821,
          is_active: true,
          created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date().toISOString(),
          permissions: {
            can_send_messages: true,
            can_add_users: true,
            can_remove_users: true,
            is_admin: true
          }
        },
        {
          id: '2',
          name: 'VIP Main Group',
          chat_id: '-1001234567891',
          invite_link: 'https://t.me/+VIPMainGroup456',
          description: 'VIP group for premium subscribers with exclusive signals',
          member_count: 1247,
          is_active: true,
          created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          permissions: {
            can_send_messages: true,
            can_add_users: true,
            can_remove_users: true,
            is_admin: true
          }
        },
        {
          id: '3',
          name: 'Mentorship Group',
          chat_id: '-1001234567892',
          invite_link: 'https://t.me/+MentorshipGroup789',
          description: 'Group for mentorship program participants',
          member_count: 156,
          is_active: true,
          created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          permissions: {
            can_send_messages: true,
            can_add_users: true,
            can_remove_users: false,
            is_admin: false
          }
        },
        {
          id: '3',
          name: 'Test Group',
          chat_id: '-1001234567892',
          invite_link: 'https://t.me/+TestGroupInvite123',
          description: 'Testing group - inactive',
          member_count: 12,
          is_active: false,
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          permissions: {
            can_send_messages: false,
            can_add_users: false,
            can_remove_users: false,
            is_admin: true
          }
        }
      ];

      const mockStats: TelegramGroupsStats = {
        total_groups: mockGroups.length,
        active_groups: mockGroups.filter(g => g.is_active).length,
        total_members: mockGroups.reduce((sum, g) => sum + g.member_count, 0),
        bot_status: 'connected'
      };

      setGroups(mockGroups);
      setStats(mockStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load groups data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddGroup = async (formData: FormData) => {
    try {
      setError(null);
      
      const groupData = {
        name: formData.get('name') as string,
        chat_id: formData.get('chat_id') as string,
        description: formData.get('description') as string,
        is_active: true
      };

      // Validate required fields
      if (!groupData.name || !groupData.chat_id) {
        setError('Group name and Chat ID are required');
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch('/api/admin/telegram/groups', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(groupData)
      // });

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setShowAddModal(false);
      await loadGroupsData();
      
      // Show success notification
      alert('Group added successfully!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to add group';
      setError(errorMessage);
      console.error('Failed to add group:', error);
    }
  };

  const handleEditGroup = async (groupId: string, formData: FormData) => {
    try {
      setError(null);
      
      const updates = {
        name: formData.get('name') as string,
        description: formData.get('description') as string,
      };

      // Validate required fields
      if (!updates.name) {
        setError('Group name is required');
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/groups/${groupId}`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updates)
      // });

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setEditingGroup(null);
      await loadGroupsData();
      
      // Show success notification
      alert('Group updated successfully!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update group';
      setError(errorMessage);
      console.error('Failed to update group:', error);
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    try {
      setError(null);
      
      // Confirm deletion
      if (!window.confirm('Are you sure you want to delete this group? This action cannot be undone.')) {
        setShowDeleteModal(null);
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/groups/${groupId}`, {
      //   method: 'DELETE'
      // });

      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setShowDeleteModal(null);
      await loadGroupsData();
      
      // Show success notification
      alert('Group deleted successfully!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete group';
      setError(errorMessage);
      console.error('Failed to delete group:', error);
    }
  };

  const handleToggleGroupStatus = async (groupId: string, isActive: boolean) => {
    try {
      setError(null);
      
      const action = isActive ? 'activate' : 'deactivate';
      const confirmMessage = `Are you sure you want to ${action} this group?`;
      
      if (!window.confirm(confirmMessage)) {
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/groups/${groupId}/toggle`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ is_active: isActive })
      // });

      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Update the groups array locally for immediate feedback
      setGroups(prev => prev.map(group => 
        group.id === groupId 
          ? { ...group, is_active: isActive, updated_at: new Date().toISOString() }
          : group
      ));
      
      // Show success notification
      alert(`Group ${action}d successfully!`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to toggle group status';
      setError(errorMessage);
      console.error('Failed to toggle group status:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You might want to show a toast notification here
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive 
      ? "px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
      : "px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800";
  };

  const getBotStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading groups...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Bot Status & Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            {getBotStatusIcon(stats.bot_status)}
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Bot Status</p>
              <p className={`text-xs ${
                stats.bot_status === 'connected' ? 'text-green-600' : 
                stats.bot_status === 'error' ? 'text-red-600' : 'text-yellow-600'
              }`}>
                {stats.bot_status}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <UsersIcon className="h-5 w-5 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Total Groups</p>
              <p className="text-lg font-bold text-gray-900">{stats.total_groups}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Active Groups</p>
              <p className="text-lg font-bold text-gray-900">{stats.active_groups}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <UsersIcon className="h-5 w-5 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">Total Members</p>
              <p className="text-lg font-bold text-gray-900">{stats.total_members.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Plans & Telegram Groups */}
      {showPricingPlans && (
        <div className="bg-white border rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h4 className="text-lg font-medium text-gray-900">Pricing Plans & Telegram Groups</h4>
              <p className="text-sm text-gray-600 mt-1">
                View which telegram groups are associated with each pricing plan
              </p>
            </div>
            <button
              onClick={() => setShowPricingPlans(!showPricingPlans)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircleIcon className="h-5 w-5" />
            </button>
          </div>
          
          <div className="p-6">
            {plansLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading pricing plans...</span>
              </div>
            ) : plansError ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <p className="text-sm text-red-800">Error loading pricing plans: {plansError}</p>
                  </div>
                </div>
              </div>
            ) : pricingPlans && pricingPlans.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {pricingPlans.map((plan: PricingPlan) => (
                  <div key={plan.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h5 className="font-medium text-gray-900">{plan.name}</h5>
                        <p className="text-sm text-gray-600 mt-1">{plan.description}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CurrencyDollarIcon className="h-4 w-4 text-green-500" />
                        <span className="text-sm font-medium text-green-600">
                          ${plan.current_price || plan.price}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 mb-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        plan.plan_category === 'signals' ? 'bg-blue-100 text-blue-800' :
                        plan.plan_category === 'mentorship' ? 'bg-purple-100 text-purple-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {plan.plan_category}
                      </span>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        plan.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {plan.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {plan.is_featured && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Featured
                        </span>
                      )}
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Subscribers:</span>
                        <span className="font-medium">{plan.subscription_count || 0}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Revenue:</span>
                        <span className="font-medium text-green-600">${plan.revenue_total || 0}</span>
                      </div>
                    </div>

                    {plan.telegram_groups && plan.telegram_groups.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-700 mb-2">Telegram Groups:</p>
                        <div className="space-y-1">
                          {plan.telegram_groups.map((group: string, index: number) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 truncate">{group}</span>
                              <button
                                onClick={() => copyToClipboard(group)}
                                className="text-gray-400 hover:text-gray-600 ml-2"
                              >
                                <ClipboardDocumentIcon className="h-4 w-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CurrencyDollarIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No pricing plans found</p>
                <p className="text-sm text-gray-400">Create some pricing plans to see their telegram groups here</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Groups Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-medium text-gray-900">Telegram Groups</h4>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Group
        </button>
      </div>

      {/* Groups Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Group
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Members
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Permissions
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {groups.map((group) => (
                <tr key={group.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{group.name}</p>
                      <p className="text-xs text-gray-500">{group.description}</p>
                      <div className="flex items-center mt-1">
                        <p className="text-xs text-gray-400 mr-2">ID: {group.chat_id}</p>
                        <button
                          onClick={() => copyToClipboard(group.chat_id)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Copy Chat ID"
                        >
                          <ClipboardDocumentIcon className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-900">{group.member_count.toLocaleString()}</span>
                  </td>
                  
                  <td className="px-6 py-4">
                    <span className={getStatusBadge(group.is_active)}>
                      {group.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex space-x-1">
                      {group.permissions.is_admin && (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Admin
                        </span>
                      )}
                      {group.permissions.can_add_users && (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                          Add
                        </span>
                      )}
                      {group.permissions.can_remove_users && (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                          Remove
                        </span>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => copyToClipboard(group.invite_link)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                        title="Copy Invite Link"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => setEditingGroup(group)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm"
                        title="Edit Group"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleToggleGroupStatus(group.id, !group.is_active)}
                        className={`text-sm ${
                          group.is_active 
                            ? 'text-orange-600 hover:text-orange-800' 
                            : 'text-green-600 hover:text-green-800'
                        }`}
                        title={group.is_active ? 'Deactivate' : 'Activate'}
                      >
                        <Cog6ToothIcon className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => setShowDeleteModal(group)}
                        className="text-red-600 hover:text-red-800 text-sm"
                        title="Delete Group"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Group Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Group</h3>
              <p className="text-sm text-gray-600 mb-4">
                Add a new Telegram group to manage. Make sure the bot has admin permissions in the group.
              </p>
              
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                handleAddGroup(formData);
              }} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Group Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="VIP Signals Premium"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Chat ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="chat_id"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="-1001234567890"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use @userinfobot in the group to get the Chat ID
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Brief description of the group..."
                  />
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    Add Group
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Group Modal */}
      {editingGroup && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Group</h3>
              
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                handleEditGroup(editingGroup.id, formData);
              }} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Group Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    defaultValue={editingGroup.name}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="VIP Signals Premium"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Chat ID (readonly)
                  </label>
                  <input
                    type="text"
                    value={editingGroup.chat_id}
                    disabled
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Chat ID cannot be changed after creation
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    defaultValue={editingGroup.description || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Brief description of the group..."
                  />
                </div>
                
                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setEditingGroup(null)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                  >
                    Update Group
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center mb-4">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-medium text-gray-900">Delete Group</h3>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">
                Are you sure you want to delete "{showDeleteModal.name}"? This will remove all associated queue items and cannot be undone.
              </p>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteModal(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteGroup(showDeleteModal.id)}
                  className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}