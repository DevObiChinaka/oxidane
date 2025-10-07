'use client';

import React from 'react';
import {
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon
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

interface TelegramStats {
  pending_additions: number;
  pending_removals: number;
  failed_operations: number;
  successful_operations_today: number;
  queue_processing_rate: number;
}

interface TelegramQueueDashboardProps {
  queueItems: TelegramQueueItem[];
  stats: TelegramStats;
  onRefresh: () => void;
}

export default function TelegramQueueDashboard({
  queueItems,
  stats,
  onRefresh
}: TelegramQueueDashboardProps) {
  const [queueStatus, setQueueStatus] = React.useState<'running' | 'paused'>('running');
  
  const recentItems = queueItems
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'retrying':
        return <ArrowPathIcon className="h-5 w-5 text-yellow-500" />;
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
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

  const toggleQueueStatus = async () => {
    try {
      const newStatus = queueStatus === 'running' ? 'paused' : 'running';
      const action = newStatus === 'running' ? 'resume' : 'pause';
      
      if (!window.confirm(`Are you sure you want to ${action} the queue processing?`)) {
        return;
      }

      // TODO: Replace with actual API call
      // const response = await fetch(`/api/admin/telegram/queue/${action}`, {
      //   method: 'POST'
      // });
      
      console.log(`${action} queue processing`);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setQueueStatus(newStatus);
      
      // Show success message
      alert(`Queue processing ${newStatus === 'running' ? 'resumed' : 'paused'} successfully!`);
      
    } catch (error) {
      console.error('Failed to toggle queue status:', error);
      alert(`Failed to ${queueStatus === 'running' ? 'pause' : 'resume'} queue processing.`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Queue Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-medium text-gray-900">Queue Status</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              queueStatus === 'running' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className={`text-sm font-medium ${
              queueStatus === 'running' ? 'text-green-600' : 'text-red-600'
            }`}>
              {queueStatus === 'running' ? 'Processing' : 'Paused'}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={toggleQueueStatus}
            className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              queueStatus === 'running'
                ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                : 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
            }`}
          >
            {queueStatus === 'running' ? (
              <>
                <PauseIcon className="h-4 w-4 mr-2" />
                Pause Queue
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Resume Queue
              </>
            )}
          </button>
          
          <button
            onClick={onRefresh}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Queue Progress */}
      <div className="bg-white rounded-lg border p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Processing Overview</h4>
        
        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Processing Rate</span>
              <span>{stats.queue_processing_rate.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${stats.queue_processing_rate}%` }}
              ></div>
            </div>
          </div>

          {/* Queue Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-gray-900">
                {queueItems.filter(item => item.status === 'pending').length}
              </p>
              <p className="text-xs text-gray-600">Pending</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-blue-600">
                {queueItems.filter(item => item.status === 'processing').length}
              </p>
              <p className="text-xs text-gray-600">Processing</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-green-600">
                {queueItems.filter(item => item.status === 'completed').length}
              </p>
              <p className="text-xs text-gray-600">Completed</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-red-600">
                {queueItems.filter(item => item.status === 'failed').length}
              </p>
              <p className="text-xs text-gray-600">Failed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Recent Queue Activity</h4>
        
        {recentItems.length > 0 ? (
          <div className="space-y-3">
            {recentItems.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(item.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {getActionIcon(item.action_type)} {item.action_type.replace('_', ' ')} - {item.group_name}
                    </p>
                    <p className="text-xs text-gray-600">
                      User: {item.user.username} ({item.user.telegram_username || 'No Telegram'})
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={getPriorityBadge(item.priority)}>
                    {item.priority}
                  </span>
                  <span className={getStatusBadge(item.status)}>
                    {item.status}
                  </span>
                  <span className="text-xs text-gray-500">
                    {item.attempts}/{item.max_attempts}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No recent queue activity</p>
        )}
      </div>
    </div>
  );
}