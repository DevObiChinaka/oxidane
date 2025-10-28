'use client';

import React, { useState } from 'react';
import {
  ChevronUpDownIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  PlayCircleIcon,
  StopCircleIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

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

interface TelegramManagementTableProps {
  queueItems: TelegramQueueItem[];
  loading: boolean;
  selectedItems: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onRefresh: () => void;
}

export default function TelegramManagementTable({
  queueItems,
  loading,
  selectedItems,
  onSelectionChange,
  onRefresh
}: TelegramManagementTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');
  const [sortField, setSortField] = useState<keyof TelegramQueueItem>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [selectedItem, setSelectedItem] = useState<TelegramQueueItem | null>(null);

  // Filter and sort items
  const filteredAndSortedItems = React.useMemo(() => {
    let filtered = queueItems.filter(item => {
      const matchesSearch = !searchTerm || 
        item.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.group_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.user.telegram_username && item.user.telegram_username.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
      const matchesPriority = priorityFilter === 'all' || item.priority === priorityFilter;
      const matchesAction = actionFilter === 'all' || item.action_type === actionFilter;

      return matchesSearch && matchesStatus && matchesPriority && matchesAction;
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      // Handle nested object properties
      if (sortField === 'user') {
        aVal = a.user.username;
        bVal = b.user.username;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      if (aVal != null && bVal != null) {
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      }
      return 0;
    });

    return filtered;
  }, [queueItems, searchTerm, statusFilter, priorityFilter, actionFilter, sortField, sortDirection]);

  const handleSort = (field: keyof TelegramQueueItem) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(filteredAndSortedItems.map(item => item.id));
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectItem = (itemId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedItems, itemId]);
    } else {
      onSelectionChange(selectedItems.filter(id => id !== itemId));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'retrying':
        return <ArrowPathIcon className="h-4 w-4 text-yellow-500" />;
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-4 w-4 text-gray-500" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'processing':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'retrying':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-600`;
      case 'pending':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const getPriorityBadge = (priority: string) => {
    const baseClasses = "px-2 py-1 rounded text-xs font-medium";
    switch (priority) {
      case 'urgent':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'high':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      case 'normal':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'low':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'add_to_group':
        return '➕';
      case 'remove_from_group':
        return '➖';
      case 'send_message':
        return '💬';
      default:
        return '🔄';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handleRetryItem = async (itemId: string) => {
    try {
      if (!window.confirm('Are you sure you want to retry this queue item?')) {
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/queue/${itemId}/retry`, {
      //   method: 'POST'
      // });

      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Show success feedback
      alert('Queue item scheduled for retry!');
      onRefresh();
    } catch (error) {
      console.error('Failed to retry item:', error);
      alert('Failed to retry item. Please try again.');
    }
  };

  const handleCancelItem = async (itemId: string) => {
    try {
      if (!window.confirm('Are you sure you want to cancel this queue item? This action cannot be undone.')) {
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/queue/${itemId}/cancel`, {
      //   method: 'POST'
      // });

      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Show success feedback
      alert('Queue item cancelled successfully!');
      onRefresh();
    } catch (error) {
      console.error('Failed to cancel item:', error);
      alert('Failed to cancel item. Please try again.');
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <div className="bg-white rounded-lg border p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search users, groups, or Telegram usernames..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="retrying">Retrying</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Priority</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Actions</option>
              <option value="add_to_group">Add to Group</option>
              <option value="remove_from_group">Remove from Group</option>
              <option value="send_message">Send Message</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedItems.length === filteredAndSortedItems.length && filteredAndSortedItems.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('user')}
                >
                  <div className="flex items-center">
                    User
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('action_type')}
                >
                  <div className="flex items-center">
                    Action
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('group_name')}
                >
                  <div className="flex items-center">
                    Group
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('priority')}
                >
                  <div className="flex items-center">
                    Priority
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center">
                    Status
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attempts
                </th>
                
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                  onClick={() => handleSort('created_at')}
                >
                  <div className="flex items-center">
                    Created
                    <ChevronUpDownIcon className="ml-1 h-4 w-4" />
                  </div>
                </th>
                
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center">
                      <ArrowPathIcon className="h-5 w-5 animate-spin text-blue-500 mr-2" />
                      Loading queue items...
                    </div>
                  </td>
                </tr>
              ) : filteredAndSortedItems.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                    No queue items found matching your criteria
                  </td>
                </tr>
              ) : (
                filteredAndSortedItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id)}
                        onChange={(e) => handleSelectItem(item.id, e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{item.user.username}</p>
                        <p className="text-xs text-gray-500">{item.user.email}</p>
                        {item.user.telegram_username && (
                          <p className="text-xs text-blue-600">{item.user.telegram_username}</p>
                        )}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <span className="mr-2">{getActionIcon(item.action_type)}</span>
                        <span className="text-sm text-gray-900">
                          {item.action_type.replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900">{item.group_name}</span>
                    </td>
                    
                    <td className="px-6 py-4">
                      <span className={getPriorityBadge(item.priority)}>
                        {item.priority}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        {getStatusIcon(item.status)}
                        <span className={`ml-2 ${getStatusBadge(item.status)}`}>
                          {item.status}
                        </span>
                      </div>
                      {item.error_message && (
                        <p className="text-xs text-red-600 mt-1" title={item.error_message}>
                          {item.error_message.length > 30 
                            ? item.error_message.substring(0, 30) + '...' 
                            : item.error_message}
                        </p>
                      )}
                    </td>
                    
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900">
                        {item.attempts} / {item.max_attempts}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-500">
                        {formatDate(item.created_at)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        
                        {(item.status === 'failed' || item.status === 'pending' || item.status === 'cancelled') && (
                          <button
                            onClick={() => handleRetryItem(item.id)}
                            className="text-green-600 hover:text-green-800 text-sm"
                            title="Retry"
                          >
                            <PlayCircleIcon className="h-4 w-4" />
                          </button>
                        )}
                        
                        {(item.status === 'pending' || item.status === 'processing' || item.status === 'retrying') && (
                          <button
                            onClick={() => handleCancelItem(item.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                            title="Cancel"
                          >
                            <StopCircleIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Queue Item Details
              </h3>
              
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium text-gray-700">User:</span>
                  <p className="text-gray-900">{selectedItem.user.username} ({selectedItem.user.email})</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Telegram:</span>
                  <p className="text-gray-900">{selectedItem.user.telegram_username || 'Not provided'}</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Action:</span>
                  <p className="text-gray-900">{selectedItem.action_type.replace('_', ' ')}</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Group:</span>
                  <p className="text-gray-900">{selectedItem.group_name}</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Priority:</span>
                  <span className={getPriorityBadge(selectedItem.priority)}>
                    {selectedItem.priority}
                  </span>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <span className={getStatusBadge(selectedItem.status)}>
                    {selectedItem.status}
                  </span>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Attempts:</span>
                  <p className="text-gray-900">{selectedItem.attempts} of {selectedItem.max_attempts}</p>
                </div>
                
                {selectedItem.error_message && (
                  <div>
                    <span className="font-medium text-gray-700">Error:</span>
                    <p className="text-red-600">{selectedItem.error_message}</p>
                  </div>
                )}
                
                <div>
                  <span className="font-medium text-gray-700">Created:</span>
                  <p className="text-gray-900">{formatDate(selectedItem.created_at)}</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-700">Updated:</span>
                  <p className="text-gray-900">{formatDate(selectedItem.updated_at)}</p>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedItem(null)}
                  className="px-4 py-2 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}