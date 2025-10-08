'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '../contexts/AdminAuthContext';
import { usePricingPlans } from '../hooks/useAdminAPI';
import TelegramQueueDashboard from '@/components/admin/TelegramQueueDashboard';
import TelegramManagementTable from '@/components/admin/TelegramManagementTable';
import TelegramBulkActions from '@/components/admin/TelegramBulkActions';
import TelegramGroupsPanel from '@/components/admin/TelegramGroupsPanel';
import { 
  UsersIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

interface TelegramStats {
  pending_additions: number;
  pending_removals: number;
  failed_operations: number;
  successful_operations_today: number;
  queue_processing_rate: number;
}

interface TelegramQueueItem {
  id: string;
  user: {
    id: string;
    username: string;
    email: string;
    telegram_username?: string;
  };
  subscription_id: string;
  action_type: 'add_to_group' | 'remove_from_group' | 'send_message';
  group_name: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying' | 'cancelled';
  attempts: number;
  max_attempts: number;
  error_message?: string;
  scheduled_for?: string;
  created_at: string;
  updated_at: string;
}

export default function TelegramManagementPage() {
  const router = useRouter();
  const { isAuthenticated, user, loading: authLoading, logout } = useAdminAuth();
  
  const [activeTab, setActiveTab] = useState<'queue' | 'management' | 'groups' | 'settings'>('queue');
  const [stats, setStats] = useState<TelegramStats>({
    pending_additions: 0,
    pending_removals: 0,
    failed_operations: 0,
    successful_operations_today: 0,
    queue_processing_rate: 0
  });
  const [queueItems, setQueueItems] = useState<TelegramQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  
  // Get pricing plans to show available telegram groups
  const { data: pricingPlans, loading: plansLoading } = usePricingPlans({ active_only: true });
  
  // Handle authentication
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/admin/login');
    }
  }, [isAuthenticated, authLoading, router]);

  // Load initial data
  useEffect(() => {
    if (isAuthenticated) {
      loadTelegramData();
    }
  }, [isAuthenticated]);

  const loadTelegramData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data - replace with actual API calls
      const mockStats: TelegramStats = {
        pending_additions: 12,
        pending_removals: 3,
        failed_operations: 5,
        successful_operations_today: 47,
        queue_processing_rate: 95.2
      };

      const mockQueueItems: TelegramQueueItem[] = [
        {
          id: '1',
          user: {
            id: '1',
            username: 'john_doe',
            email: 'john@example.com',
            telegram_username: '@johndoe'
          },
          subscription_id: 'sub_1',
          action_type: 'add_to_group',
          group_name: 'VIP Signals Premium',
          priority: 'high',
          status: 'pending',
          attempts: 0,
          max_attempts: 3,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          user: {
            id: '2',
            username: 'jane_smith',
            email: 'jane@example.com',
            telegram_username: '@janesmith'
          },
          subscription_id: 'sub_2',
          action_type: 'add_to_group',
          group_name: 'Weekly Signals',
          priority: 'normal',
          status: 'processing',
          attempts: 1,
          max_attempts: 3,
          created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '3',
          user: {
            id: '3',
            username: 'bob_wilson',
            email: 'bob@example.com',
            telegram_username: '@bobwilson'
          },
          subscription_id: 'sub_3',
          action_type: 'remove_from_group',
          group_name: 'VIP Signals Premium',
          priority: 'normal',
          status: 'failed',
          attempts: 3,
          max_attempts: 3,
          error_message: 'User not found in group',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
        }
      ];

      setStats(mockStats);
      setQueueItems(mockQueueItems);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Telegram data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadTelegramData();
  };

  const handleBulkAction = async (action: string, itemIds: string[]) => {
    try {
      setError(null);
      
      // Map action to API endpoint
      let apiAction = action;
      let requestBody: any = { item_ids: itemIds };
      
      switch (action) {
        case 'retry':
          apiAction = 'bulk-retry';
          break;
        case 'cancel':
          apiAction = 'bulk-cancel';
          requestBody.reason = 'Bulk cancellation by admin';
          break;
        case 'priority_high':
          apiAction = 'bulk-priority';
          requestBody.priority = 'high';
          break;
        case 'priority_normal':
          apiAction = 'bulk-priority';
          requestBody.priority = 'normal';
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/queue/${apiAction}`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(requestBody)
      // });
      
      console.log(`Performing ${action} on ${itemIds.length} items:`, itemIds);
      
      // Simulate API call with different durations based on action
      const delay = action === 'cancel' ? 500 : 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Update local state to show immediate feedback
      setQueueItems(prev => prev.map(item => {
        if (itemIds.includes(item.id)) {
          switch (action) {
            case 'retry':
              return { ...item, status: 'pending' as const, attempts: 0, error_message: undefined };
            case 'cancel':
              return { ...item, status: 'cancelled' as const };
            case 'priority_high':
              return { ...item, priority: 'high' as const };
            case 'priority_normal':
              return { ...item, priority: 'normal' as const };
            default:
              return item;
          }
        }
        return item;
      }));
      
      // Refresh data from server
      await loadTelegramData();
      setSelectedItems([]);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bulk action failed';
      setError(errorMessage);
      throw err; // Re-throw for the component to handle
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Telegram Management...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Telegram Management</h1>
                <p className="mt-1 text-sm text-gray-500">
                  Manage Telegram group operations and queue processing
                </p>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={handleRefresh}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Cog6ToothIcon className="w-4 h-4 mr-2" />
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Pending Additions</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pending_additions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UsersIcon className="h-8 w-8 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Pending Removals</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pending_removals}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Failed Operations</p>
                <p className="text-2xl font-bold text-gray-900">{stats.failed_operations}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Success Today</p>
                <p className="text-2xl font-bold text-gray-900">{stats.successful_operations_today}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-sm font-semibold text-blue-600">
                    {stats.queue_processing_rate.toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">{stats.queue_processing_rate.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {[
                { id: 'queue', name: 'Queue Management', icon: ClockIcon },
                { id: 'management', name: 'User Management', icon: UsersIcon },
                { id: 'groups', name: 'Group Settings', icon: Cog6ToothIcon },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                >
                  <tab.icon className="w-5 h-5 mr-2" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'queue' && (
              <div className="space-y-6">
                <TelegramQueueDashboard
                  queueItems={queueItems}
                  stats={stats}
                  onRefresh={handleRefresh}
                />
                
                {selectedItems.length > 0 && (
                  <TelegramBulkActions
                    selectedItems={selectedItems}
                    onAction={handleBulkAction}
                    onClearSelection={() => setSelectedItems([])}
                  />
                )}
                
                <TelegramManagementTable
                  queueItems={queueItems}
                  loading={loading}
                  selectedItems={selectedItems}
                  onSelectionChange={setSelectedItems}
                  onRefresh={handleRefresh}
                />
              </div>
            )}

            {activeTab === 'management' && (
              <div>
                <p className="text-gray-500 text-center py-8">
                  User-specific Telegram management features coming soon...
                </p>
              </div>
            )}

            {activeTab === 'groups' && (
              <TelegramGroupsPanel onRefresh={handleRefresh} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}