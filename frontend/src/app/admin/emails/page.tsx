'use client';

import { useState, useEffect } from 'react';
import { adminAPI } from '../utils/api';
import EnhancedEmailTemplateEditor from '../../../components/admin/EnhancedEmailTemplateEditor';
import EmailPreviewModal from '../../../components/admin/EmailPreviewModal';
import SendEmailModal from '../../../components/admin/SendEmailModal';
import DeleteConfirmModal from '../../../components/admin/DeleteConfirmModal';
import { EmailTemplate, EmailTemplateType, EmailAnalytics, EmailLog } from '../../../types/admin';

export default function EmailTemplatesPage() {
  // Active tab: system_emails, custom_templates, recent_activity
  const [activeTab, setActiveTab] = useState<'system_emails' | 'custom_templates' | 'recent_activity'>('system_emails');
  
  // State management
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [systemTemplates, setSystemTemplates] = useState<EmailTemplate[]>([]);
  const [customTemplates, setCustomTemplates] = useState<EmailTemplate[]>([]);
  const [templateTypes, setTemplateTypes] = useState<EmailTemplateType[]>([]);
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [recentEmails, setRecentEmails] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [logsLoading, setLogsLoading] = useState(false);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // Selected items
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null);
  const [templateToDelete, setTemplateToDelete] = useState<EmailTemplate | null>(null);
  const [templateToSend, setTemplateToSend] = useState<EmailTemplate | null>(null);
  
  // Notification state
  const [notification, setNotification] = useState<{
    show: boolean;
    type: 'success' | 'error';
    title: string;
    message: string;
    details?: { sent: number; failed: number; total: number };
  }>({
    show: false,
    type: 'success',
    title: '',
    message: ''
  });
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');

  // Load data on mount
  useEffect(() => {
    loadTemplates();
    loadAnalytics();
    loadTemplateTypes();
  }, []);

  // Load email logs when Recent Activity tab is active
  useEffect(() => {
    if (activeTab === 'recent_activity') {
      loadEmailLogs();
    }
  }, [activeTab]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getEmailTemplates();
      
      if (response.success && response.templates) {
        const allTemplates = response.templates;
        setTemplates(allTemplates);
        
        // Separate system and custom templates
        const system = allTemplates.filter((t: EmailTemplate) => t.is_system_email);
        const custom = allTemplates.filter((t: EmailTemplate) => !t.is_system_email);
        
        setSystemTemplates(system);
        setCustomTemplates(custom);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      showNotification('error', 'Error', 'Failed to load email templates');
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await adminAPI.getEmailAnalytics();
      if (response.success && response.analytics) {
        setAnalytics(response.analytics);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const loadTemplateTypes = async () => {
    try {
      const response = await adminAPI.getEmailTemplateTypes();
      if (response.success && response.types) {
        setTemplateTypes(response.types);
      }
    } catch (error) {
      console.error('Error loading template types:', error);
      // Fallback to basic types if API fails
      setTemplateTypes([
        { value: 'welcome', label: 'Welcome Email', description: 'Welcome new users' },
        { value: 'verification', label: 'Email Verification', description: 'Verify email addresses' },
        { value: 'password_reset', label: 'Password Reset', description: 'Reset password requests' },
        { value: 'notification', label: 'Notification', description: 'General notifications' }
      ]);
    }
  };

  const loadEmailLogs = async () => {
    try {
      setLogsLoading(true);
      const response = await adminAPI.getEmailLogs({ limit: 50 });
      if (response.success && response.logs) {
        setEmailLogs(response.logs);
      }
    } catch (error) {
      console.error('Error loading email logs:', error);
    } finally {
      setLogsLoading(false);
    }
  };

  const showNotification = (
    type: 'success' | 'error',
    title: string,
    message: string,
    details?: { sent: number; failed: number; total: number }
  ) => {
    setNotification({
      show: true,
      type,
      title,
      message,
      details
    });
    setTimeout(() => {
      setNotification(prev => ({ ...prev, show: false }));
    }, 5000);
  };

  // Template actions
  const handleCreateTemplate = async (templateData: any) => {
    try {
      const response = await adminAPI.createEmailTemplate(templateData);
      if (response.success) {
        showNotification('success', 'Template Created', 'Email template has been created successfully');
        setShowCreateModal(false);
        
        // Immediately add the new template to state for instant feedback
        if (response.template) {
          const newTemplate = response.template;
          setTemplates(prev => [...prev, newTemplate]);
          
          // Add to appropriate list (system or custom)
          if (newTemplate.is_system_email) {
            setSystemTemplates(prev => [...prev, newTemplate]);
          } else {
            setCustomTemplates(prev => [...prev, newTemplate]);
          }
        }
        
        // Still reload to ensure consistency with backend
        loadTemplates();
      } else {
        showNotification('error', 'Error', response.error || 'Failed to create template');
      }
    } catch (error) {
      showNotification('error', 'Error', 'An error occurred while creating the template');
    }
  };

  const handleUpdateTemplate = async (templateData: any) => {
    if (!selectedTemplate || !selectedTemplate.id) return;
    
    try {
      const response = await adminAPI.updateEmailTemplate(selectedTemplate.id, templateData);
      if (response.success) {
        showNotification('success', 'Template Updated', 'Email template has been updated successfully');
        setShowEditModal(false);
        setSelectedTemplate(null);
        loadTemplates();
      } else {
        showNotification('error', 'Error', response.error || 'Failed to update template');
      }
    } catch (error) {
      showNotification('error', 'Error', 'An error occurred while updating the template');
    }
  };

  const handleDeleteTemplate = async () => {
    if (!templateToDelete || !templateToDelete.id) return;
    
    try {
      const response = await adminAPI.deleteEmailTemplate(templateToDelete.id);
      if (response.success) {
        showNotification('success', 'Template Deleted', 'Email template has been deleted successfully');
        setShowDeleteConfirm(false);
        setTemplateToDelete(null);
        loadTemplates();
      } else {
        showNotification('error', 'Error', response.error || 'Failed to delete template');
      }
    } catch (error: any) {
      showNotification('error', 'Error', error.message || 'An error occurred while deleting the template');
    }
  };

  const handleSendEmail = async (sendData: any) => {
    if (!templateToSend || !templateToSend.id) return;
    
    try {
      const response = await adminAPI.sendBulkEmail(templateToSend.id, sendData);
      if (response.success) {
        showNotification(
          'success',
          'Email Sent',
          `Email campaign sent successfully`,
          {
            sent: response.sent_count || 0,
            failed: response.failed_count || 0,
            total: response.total_recipients || 0
          }
        );
        setShowSendModal(false);
        setTemplateToSend(null);
        loadAnalytics();
      } else {
        showNotification('error', 'Error', response.error || 'Failed to send email');
      }
    } catch (error) {
      showNotification('error', 'Error', 'An error occurred while sending the email');
    }
  };

  const handlePreview = (template: EmailTemplate) => {
    setPreviewTemplate(template);
    setShowPreviewModal(true);
  };

  const handleEdit = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setShowEditModal(true);
  };

  const handleSend = (template: EmailTemplate) => {
    setTemplateToSend(template);
    setShowSendModal(true);
  };

  const handleDelete = (template: EmailTemplate) => {
    setTemplateToDelete(template);
    setShowDeleteConfirm(true);
  };

  // Filter templates based on search
  const filteredSystemTemplates = systemTemplates.filter(t =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredCustomTemplates = customTemplates.filter(t =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Template type icon helper
  const getTemplateTypeIcon = (templateType: string) => {
    const iconClass = "w-5 h-5 text-white";
    
    switch (templateType) {
      case 'email_verification':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
      case 'password_reset':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>;
      case 'signin_notification':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>;
      case 'payment_success':
      case 'subscription_success':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
      case 'payment_failed':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
      case 'subscription_expiry':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
      case 'telegram_added':
      case 'telegram_removed':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>;
      default:
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification Toast */}
      {notification.show && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <div className={`rounded-lg shadow-lg p-4 ${
            notification.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {notification.type === 'success' ? (
                  <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                )}
              </div>
              <div className="ml-3 flex-1">
                <h3 className={`text-sm font-medium ${
                  notification.type === 'success' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {notification.title}
                </h3>
                <p className={`mt-1 text-sm ${
                  notification.type === 'success' ? 'text-green-700' : 'text-red-700'
                }`}>
                  {notification.message}
                </p>
                {notification.details && (
                  <div className="mt-2 text-sm text-green-700">
                    <p>Sent: {notification.details.sent} / Failed: {notification.details.failed} / Total: {notification.details.total}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header - Mobile Responsive */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6">
          <div className="md:flex md:items-center md:justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Email Management</h1>
              <p className="mt-1 text-xs sm:text-sm text-gray-600">
                Manage system emails and send campaigns to users
              </p>
            </div>
            {activeTab === 'custom_templates' && (
              <div className="mt-3 md:mt-0">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="w-full md:w-auto inline-flex items-center justify-center px-3 sm:px-4 py-2 border border-transparent rounded-md shadow-sm text-xs sm:text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                  Create Template
                </button>
              </div>
            )}
          </div>

          {/* Analytics Cards - Mobile Responsive */}
          {analytics && (
            <div className="mt-4 sm:mt-6 grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Total Templates</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{analytics.total_templates}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Emails Sent</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{analytics.total_sent}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Success Rate</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{analytics.success_rate}%</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 overflow-hidden shadow rounded-lg border border-gray-200">
                <div className="p-3 sm:p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 hidden sm:block">
                      <svg className="h-5 w-5 sm:h-6 sm:w-6 text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="sm:ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-xs sm:text-sm font-medium text-gray-600 truncate">Recent (30d)</dt>
                        <dd className="text-base sm:text-lg font-semibold text-gray-900">{analytics.recent_sent}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs - Mobile Responsive */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 mt-4 sm:mt-6">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="-mb-px flex space-x-4 sm:space-x-8 min-w-max">
            <button
              onClick={() => setActiveTab('system_emails')}
              className={`${
                activeTab === 'system_emails'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
            >
              <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              <span className="hidden sm:inline">System Emails</span>
              <span className="sm:hidden">System</span>
              <span className="ml-1 sm:ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full">
                {systemTemplates.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('custom_templates')}
              className={`${
                activeTab === 'custom_templates'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
            >
              <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
              </svg>
              <span className="hidden sm:inline">Custom Templates</span>
              <span className="sm:hidden">Custom</span>
              <span className="ml-1 sm:ml-2 bg-gray-100 text-gray-800 text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full">
                {customTemplates.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('recent_activity')}
              className={`${
                activeTab === 'recent_activity'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
              } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center`}
            >
              <svg className="h-4 w-4 sm:h-5 sm:w-5 mr-1 sm:mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="hidden sm:inline">Recent Activity</span>
              <span className="sm:hidden">Activity</span>
            </button>
          </nav>
        </div>

        {/* Search Bar */}
        {(activeTab === 'system_emails' || activeTab === 'custom_templates') && (
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="mt-6 pb-12">
          {/* System Emails Tab */}
          {activeTab === 'system_emails' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">System Email Templates</h3>
                    <p className="mt-1 text-sm text-gray-600">
                      Critical emails that are always active and cannot be deleted
                    </p>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Always Active
                  </span>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4">
                  {loading ? (
                    <div className="text-center py-12">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-600">Loading templates...</p>
                    </div>
                  ) : filteredSystemTemplates.length === 0 ? (
                    <div className="text-center py-12">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No system templates found</h3>
                      <p className="mt-1 text-sm text-gray-600">Run the seed_system_emails command to create them</p>
                    </div>
                  ) : (
                    filteredSystemTemplates.map((template) => (
                      <div
                        key={template.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                          <div className="flex items-start space-x-3 sm:space-x-4 flex-1">
                            <div className="flex-shrink-0">
                              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                                {getTemplateTypeIcon(template.template_type)}
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-medium text-gray-900">{template.name}</h4>
                              <p className="mt-1 text-xs sm:text-sm text-gray-600 line-clamp-2">{template.description || 'No description'}</p>
                              <div className="mt-2 flex flex-col sm:flex-row sm:items-center sm:space-x-4 text-xs text-gray-500 space-y-1 sm:space-y-0">
                                <span className="truncate">Subject: {template.subject_template}</span>
                                <span className="hidden sm:inline">•</span>
                                <span>Sent {template.sent_count || 0} times</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 sm:ml-4">
                            <button
                              onClick={() => handleEdit(template)}
                              className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                              </svg>
                              Edit
                            </button>
                            <button
                              onClick={() => handlePreview(template)}
                              className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              Preview
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Custom Templates Tab */}
          {activeTab === 'custom_templates' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Custom Email Templates</h3>
                    <p className="mt-1 text-sm text-gray-600">
                      Create and manage your own email campaigns
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4">
                  {loading ? (
                    <div className="text-center py-12">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-600">Loading templates...</p>
                    </div>
                  ) : filteredCustomTemplates.length === 0 ? (
                    <div className="text-center py-12">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No custom templates yet</h3>
                      <p className="mt-1 text-sm text-gray-600">Get started by creating your first email template</p>
                      <div className="mt-6">
                        <button
                          onClick={() => setShowCreateModal(true)}
                          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                          </svg>
                          Create Template
                        </button>
                      </div>
                    </div>
                  ) : (
                    filteredCustomTemplates.map((template) => (
                      <div
                        key={template.id}
                        className="border border-gray-200 rounded-lg p-3 sm:p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                          <div className="flex items-start space-x-3 sm:space-x-4 flex-1">
                            <div className="flex-shrink-0">
                              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-600 rounded-lg flex items-center justify-center">
                                {getTemplateTypeIcon(template.template_type)}
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <h4 className="text-sm font-medium text-gray-900">{template.name}</h4>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                  template.status === 'active' ? 'bg-green-100 text-green-800' :
                                  template.status === 'inactive' ? 'bg-red-100 text-red-800' :
                                  'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {template.status}
                                </span>
                              </div>
                              <p className="mt-1 text-xs sm:text-sm text-gray-600 line-clamp-2">{template.description || 'No description'}</p>
                              <div className="mt-2 flex flex-col sm:flex-row sm:items-center sm:space-x-4 text-xs text-gray-500 space-y-1 sm:space-y-0">
                                <span className="truncate">Subject: {template.subject_template}</span>
                                <span className="hidden sm:inline">•</span>
                                <span>Sent {template.sent_count || 0} times</span>
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 sm:flex sm:items-center gap-2 sm:ml-4">center gap-2 sm:ml-4">
                            <button
                              onClick={() => handleSend(template)}
                              className="inline-flex items-center justify-center px-2 sm:px-3 py-1.5 border border-transparent shadow-sm text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                              </svg>
                              Send
                            </button>
                            <button
                              onClick={() => handleEdit(template)}
                              className="inline-flex items-center justify-center px-2 sm:px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                              </svg>
                              Edit
                            </button>
                            <button
                              onClick={() => handlePreview(template)}
                              className="inline-flex items-center justify-center px-2 sm:px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                              <svg className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              <span className="hidden sm:inline">Preview</span>
                              <span className="sm:hidden">View</span>
                            </button>
                            <button
                              onClick={() => handleDelete(template)}
                              className="inline-flex items-center justify-center px-2 sm:px-3 py-1.5 border border-red-300 shadow-sm text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                              <svg className="h-3.5 w-3.5 sm:h-4 sm:w-4 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                              </svg>
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Recent Activity Tab */}
          {activeTab === 'recent_activity' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Recent Email Activity</h3>
                    <p className="mt-1 text-sm text-gray-600">
                      Last 50 emails sent from the system
                    </p>
                  </div>
                  <button
                    onClick={loadEmailLogs}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                    </svg>
                    Refresh
                  </button>
                </div>

                {logsLoading ? (
                  <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2 text-sm text-gray-600">Loading email logs...</p>
                  </div>
                ) : emailLogs.length === 0 ? (
                  <div className="text-center py-12">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No emails sent yet</h3>
                    <p className="mt-1 text-sm text-gray-600">
                      Email activity will appear here once you start sending campaigns
                    </p>
                  </div>
                ) : (
                  <div className="mt-6 overflow-x-auto -mx-4 sm:mx-0">
                    <div className="inline-block min-w-full align-middle">
                      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-3 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                                Recipient
                              </th>
                              <th className="px-3 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                                Template
                              </th>
                              <th className="px-3 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider hidden md:table-cell">
                                Subject
                              </th>
                              <th className="px-3 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                                Status
                              </th>
                              <th className="px-3 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider hidden lg:table-cell">
                                Sent At
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                        {emailLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-3 sm:px-4 py-3 sm:py-4 whitespace-nowrap">
                              <div className="text-xs sm:text-sm font-medium text-gray-900 truncate max-w-[120px] sm:max-w-none">
                                {log.recipient_name || log.recipient_email}
                              </div>
                              {log.recipient_name && (
                                <div className="text-xs text-gray-500 truncate max-w-[120px] sm:max-w-none">{log.recipient_email}</div>
                              )}
                            </td>
                            <td className="px-3 sm:px-4 py-3 sm:py-4 whitespace-nowrap">
                              <div className="text-xs sm:text-sm text-gray-900 truncate max-w-[100px] sm:max-w-none">{log.template_name}</div>
                              <div className="text-xs text-gray-500 truncate max-w-[100px] sm:max-w-none">{log.template_type}</div>
                            </td>
                            <td className="px-3 sm:px-4 py-3 sm:py-4 hidden md:table-cell">
                              <div className="text-xs sm:text-sm text-gray-900 max-w-xs truncate">
                                {log.subject}
                              </div>
                            </td>
                            <td className="px-3 sm:px-4 py-3 sm:py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                log.status === 'sent' || log.status === 'delivered' ? 'bg-green-100 text-green-800' :
                                log.status === 'failed' || log.status === 'bounced' ? 'bg-red-100 text-red-800' :
                                log.status === 'opened' ? 'bg-blue-100 text-blue-800' :
                                log.status === 'clicked' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                              </span>
                            </td>
                            <td className="px-3 sm:px-4 py-3 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-600 hidden lg:table-cell">
                              {log.sent_at ? new Date(log.sent_at).toLocaleString() : 
                               log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <EnhancedEmailTemplateEditor
        isOpen={showCreateModal || showEditModal}
        onClose={() => {
          setShowCreateModal(false);
          setShowEditModal(false);
          setSelectedTemplate(null);
        }}
        onSave={showEditModal ? handleUpdateTemplate : handleCreateTemplate}
        template={selectedTemplate}
        templateTypes={templateTypes}
      />

      <EmailPreviewModal
        template={previewTemplate}
        isOpen={showPreviewModal}
        onClose={() => {
          setShowPreviewModal(false);
          setPreviewTemplate(null);
        }}
      />

      <SendEmailModal
        template={templateToSend}
        isOpen={showSendModal}
        onClose={() => {
          setShowSendModal(false);
          setTemplateToSend(null);
        }}
        onSend={handleSendEmail}
      />

      <DeleteConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setTemplateToDelete(null);
        }}
        onConfirm={handleDeleteTemplate}
        template={templateToDelete}
      />
    </div>
  );
}
