'use client';

import { useState, useEffect } from 'react';
import { EmailTemplate } from '../../types/admin';
import { adminAPI } from '../../app/admin/utils/api';

interface SendEmailModalProps {
  template: EmailTemplate | null;
  isOpen: boolean;
  onClose: () => void;
  onSend: (recipients: SendEmailData) => void;
}

interface SendEmailData {
  recipientType: 'all_users' | 'active_subscribers' | 'inactive_users' | 'specific_users' | 'subscription_plan_only';
  specificUsers?: string[];
  subscriptionPlans?: string[];  // New: array of billing periods
  scheduleType: 'now' | 'later';
  scheduledDate?: string;
  scheduledTime?: string;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  subscription_status?: string;
  last_login?: string;
  is_active?: boolean;
  active_signal_subscriptions_count?: number;
  signal_subscriptions_count?: number;
}

export default function SendEmailModal({ template, isOpen, onClose, onSend }: SendEmailModalProps) {
  const [activeTab, setActiveTab] = useState<'quick' | 'users' | 'schedule'>('quick');
  const [sendData, setSendData] = useState<SendEmailData>({
    recipientType: 'all_users',
    subscriptionPlans: [],  // New: empty by default
    scheduleType: 'now'
  });
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [recipientCount, setRecipientCount] = useState(0);

  // Load users when modal opens
  useEffect(() => {
    if (isOpen) {
      loadUsers();
    }
  }, [isOpen]);

  // Calculate recipient count when users data changes or recipient type changes
  useEffect(() => {
    calculateRecipientCount();
  }, [users, sendData.recipientType, selectedUsers]);

  const loadUsers = async () => {
    try {

      const response = await adminAPI.getUsers({
        page: 1,
        per_page: 1000, // Get all users for now
        search: ''
      });

      if (response.success !== false && response.users) {
        // Handle direct response format
        setUsers(response.users || []);

      } else if (response.success && response.data) {
        // Handle wrapped response format
        setUsers(response.data.users || []);

      } else {

        // Use mock data as fallback
        const mockUsers: User[] = [
          { id: '1', email: 'admin@oxiworld.com', first_name: 'Admin', last_name: 'User', subscription_status: 'active' },
          { id: '3', email: 'inactive@oxiworld.com', first_name: 'Inactive', last_name: 'User', subscription_status: 'inactive' }
        ];
        setUsers(mockUsers);
      }
    } catch (error) {
      console.error('Error loading users:', error);
      // Fallback to mock data if API fails
      const mockUsers: User[] = [
        { id: '1', email: 'admin@oxiworld.com', first_name: 'Admin', last_name: 'User', subscription_status: 'active' },
        { id: '3', email: 'inactive@oxiworld.com', first_name: 'Inactive', last_name: 'User', subscription_status: 'inactive' }
      ];
      setUsers(mockUsers);

    }
  };

  const calculateRecipientCount = () => {
    if (!users || users.length === 0) {
      setRecipientCount(0);
      return;
    }

    let count = 0;
    switch (sendData.recipientType) {
      case 'all_users':
        count = users.length;
        break;
      case 'active_subscribers':
        count = users.filter(u => 
          u.subscription_status === 'active' || 
          (u.active_signal_subscriptions_count && u.active_signal_subscriptions_count > 0) ||
          u.is_active === true
        ).length;
        break;
      case 'inactive_users':
        count = users.filter(u => 
          u.subscription_status === 'inactive' || 
          u.is_active === false ||
          (!u.last_login)
        ).length;
        break;
      case 'specific_users':
        count = selectedUsers.length;
        break;
    }
    setRecipientCount(count);

  };

  const handleSend = () => {
    setLoading(true);
    onSend({
      ...sendData,
      specificUsers: sendData.recipientType === 'specific_users' ? selectedUsers : undefined,
      subscriptionPlans: sendData.subscriptionPlans && sendData.subscriptionPlans.length > 0 ? sendData.subscriptionPlans : undefined
    });
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen || !template) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Send Email Campaign</h2>
            <p className="text-sm text-gray-600 mt-1">Template: {template.name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('quick')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'quick'
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <svg className="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
              </svg>
              Quick Send
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <svg className="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
              </svg>
              Select Users
            </button>
            <button
              onClick={() => setActiveTab('schedule')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'schedule'
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <svg className="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5a2.25 2.25 0 0 0 2.25-2.25m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5a2.25 2.25 0 0 1 2.25 2.25v7.5m-9-6h.008v.008H12V12Z" />
              </svg>
              Schedule
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 max-h-96 overflow-y-auto">
          {activeTab === 'quick' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Choose Recipients</h3>
              
              {/* Recipient Count Summary */}
              {users.length > 0 && (
                <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 mb-4">
                  <h4 className="font-medium text-gray-900 mb-2">Recipient Overview</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-gray-900">
                      Total Users: <span className="font-medium">{users.length}</span>
                    </div>
                    <div className="text-gray-900">
                      Active Subscribers: <span className="font-medium">{users.filter(u => 
                        u.subscription_status === 'active' || 
                        (u.active_signal_subscriptions_count && u.active_signal_subscriptions_count > 0) ||
                        u.is_active === true
                      ).length}</span>
                    </div>
                    <div className="text-gray-900">
                      Inactive Users: <span className="font-medium">{users.filter(u => 
                        u.subscription_status === 'inactive' || 
                        u.is_active === false ||
                        (!u.last_login)
                      ).length}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 gap-3">
                {[
                  { 
                    value: 'all_users', 
                    label: 'All Users', 
                    description: 'Send to everyone in your system',
                    count: users.length 
                  },
                  { 
                    value: 'active_subscribers', 
                    label: 'Active Subscribers', 
                    description: 'Users with active subscriptions (optionally filter by plan below)',
                    count: users.filter(u => 
                      u.subscription_status === 'active' || 
                      (u.active_signal_subscriptions_count && u.active_signal_subscriptions_count > 0) ||
                      u.is_active === true
                    ).length
                  },
                  { 
                    value: 'inactive_users', 
                    label: 'Inactive Users', 
                    description: 'Users who haven\'t logged in recently',
                    count: users.filter(u => 
                      u.subscription_status === 'inactive' || 
                      u.is_active === false ||
                      (!u.last_login)
                    ).length
                  },
                  { 
                    value: 'subscription_plan_only', 
                    label: 'By Subscription Plan', 
                    description: 'Filter by specific subscription plan types (select below)',
                    count: 0  // Dynamic based on selected plans
                  }
                ].map((option) => (
                  <label key={option.value} className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name="recipientType"
                      value={option.value}
                      checked={sendData.recipientType === option.value}
                      onChange={(e) => setSendData({ ...sendData, recipientType: e.target.value as any })}
                      className="mt-1 h-4 w-4 text-gray-900 focus:ring-gray-500 border-gray-300"
                    />
                    <div className="ml-3 flex-grow">
                      <div className="flex items-center justify-between">
                        <div className="font-medium text-gray-900">{option.label}</div>
                        {option.value !== 'subscription_plan_only' && (
                          <div className="bg-gray-100 text-gray-900 text-xs font-medium px-2.5 py-0.5 rounded-full">
                            {option.count} recipients
                          </div>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">{option.description}</div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Subscription Plan Filters */}
              {(sendData.recipientType === 'active_subscribers' || sendData.recipientType === 'subscription_plan_only') && (
                <div className="mt-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <h4 className="font-medium text-gray-900 mb-3">Filter by Subscription Plan (Optional)</h4>
                  <p className="text-sm text-gray-600 mb-3">Select specific plan types to target</p>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { value: 'weekly', label: 'Weekly Plans' },
                      { value: 'monthly', label: 'Monthly Plans' },
                      { value: 'quarterly', label: 'Quarterly Plans' },
                      { value: 'yearly', label: 'Yearly Plans' },
                      { value: 'lifetime', label: 'Lifetime Plans' }
                    ].map((plan) => (
                      <label key={plan.value} className="flex items-center p-2 border border-gray-200 rounded bg-white hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={sendData.subscriptionPlans?.includes(plan.value) || false}
                          onChange={(e) => {
                            const currentPlans = sendData.subscriptionPlans || [];
                            const newPlans = e.target.checked
                              ? [...currentPlans, plan.value]
                              : currentPlans.filter(p => p !== plan.value);
                            setSendData({ ...sendData, subscriptionPlans: newPlans });
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-900">{plan.label}</span>
                      </label>
                    ))}
                  </div>
                  {sendData.subscriptionPlans && sendData.subscriptionPlans.length > 0 && (
                    <div className="mt-3 text-sm text-gray-700">
                      <strong>Selected:</strong> {sendData.subscriptionPlans.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Select Specific Users</h3>
                <div className="text-sm text-gray-500">
                  {selectedUsers.length} users selected
                </div>
              </div>
              
              {/* Search */}
              <div className="relative">
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-gray-500"
                />
              </div>

              {/* User List */}
              <div className="border border-gray-200 rounded-md max-h-60 overflow-y-auto">
                {filteredUsers.map((user) => (
                  <label key={user.id} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0">
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(user.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUsers([...selectedUsers, user.id]);
                          setSendData({ ...sendData, recipientType: 'specific_users' });
                        } else {
                          setSelectedUsers(selectedUsers.filter(id => id !== user.id));
                        }
                      }}
                      className="h-4 w-4 text-gray-900 focus:ring-gray-500 border-gray-300 rounded"
                    />
                    <div className="ml-3 flex-1">
                      <div className="font-medium text-gray-900">{user.first_name} {user.last_name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {user.subscription_status}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Schedule Delivery</h3>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="scheduleType"
                    value="now"
                    checked={sendData.scheduleType === 'now'}
                    onChange={(e) => setSendData({ ...sendData, scheduleType: e.target.value as any })}
                    className="h-4 w-4 text-gray-900 focus:ring-gray-500 border-gray-300"
                  />
                  <span className="ml-3 font-medium text-gray-900">Send immediately</span>
                </label>
                
                <label className="flex items-start">
                  <input
                    type="radio"
                    name="scheduleType"
                    value="later"
                    checked={sendData.scheduleType === 'later'}
                    onChange={(e) => setSendData({ ...sendData, scheduleType: e.target.value as any })}
                    className="mt-1 h-4 w-4 text-gray-900 focus:ring-gray-500 border-gray-300"
                  />
                  <div className="ml-3 space-y-3">
                    <span className="font-medium text-gray-900">Schedule for later</span>
                    {sendData.scheduleType === 'later' && (
                      <div className="flex space-x-3">
                        <input
                          type="date"
                          value={sendData.scheduledDate || ''}
                          onChange={(e) => setSendData({ ...sendData, scheduledDate: e.target.value })}
                          className="border border-gray-300 rounded-md px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-gray-500"
                        />
                        <input
                          type="time"
                          value={sendData.scheduledTime || ''}
                          onChange={(e) => setSendData({ ...sendData, scheduledTime: e.target.value })}
                          className="border border-gray-300 rounded-md px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-gray-500"
                        />
                      </div>
                    )}
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            Ready to send to <span className="font-semibold">{recipientCount} recipients</span>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={loading || recipientCount === 0}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
                  </svg>
                  {sendData.scheduleType === 'now' ? 'Send Now' : 'Schedule Email'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}