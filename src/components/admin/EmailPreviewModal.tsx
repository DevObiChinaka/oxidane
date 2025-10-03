'use client';

import { useState, useEffect } from 'react';
import { adminAPI } from '../../utils/api';

interface EmailTemplate {
  id: string;
  name: string;
  template_type: string;
  template_type_display: string;
  subject_template: string;
  html_content: string;
}

interface PreviewData {
  success: boolean;
  subject: string;
  html_content: string;
  variables_used: Record<string, string>;
  template_name: string;
}

interface EmailPreviewModalProps {
  template: EmailTemplate | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function EmailPreviewModal({ template, isOpen, onClose }: EmailPreviewModalProps) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'variables' | 'test'>('preview');
  const [testEmail, setTestEmail] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Sample data for different template types
  const getSampleDataForType = (templateType: string) => {
    const baseData = {
      user: {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com'
      }
    };

    const typeSpecificData = {
      subscription_success: {
        subscription: {
          plan_type: 'monthly',
          amount_paid: 99.00,
          currency: 'USD',
          start_date: new Date().toISOString(),
          end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          reference: 'PAY_ABC123'
        }
      },
      payment_failed: {
        payment: {
          amount: 99.00,
          reference: 'PAY_FAILED_123',
          date: new Date().toISOString(),
          status: 'failed'
        }
      },
      renewal_reminder: {
        subscription: {
          plan_type: 'monthly',
          amount_paid: 99.00,
          end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        custom: {
          days_remaining: 7,
          renewal_link: 'https://oxiworld.com/renew/123'
        }
      }
    };

    return {
      ...baseData,
      ...(typeSpecificData[templateType as keyof typeof typeSpecificData] || {})
    };
  };

  const loadPreview = async () => {
    if (!template) return;

    setLoading(true);
    try {
      const sampleData = getSampleDataForType(template.template_type);
      
      const response = await adminAPI.previewEmailTemplate(template.id, {
        sample_data: sampleData
      });

      if (response.success) {
        setPreviewData(response);
      } else {
        console.error('Failed to load preview:', response);
      }
    } catch (error) {
      console.error('Failed to load preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    if (!template || !testEmail) return;

    setSendingTest(true);
    setTestResult(null);

    try {
      const sampleData = getSampleDataForType(template.template_type);
      
      const response = await adminAPI.sendTestEmail(template.id, {
        recipient_email: testEmail,
        sample_data: sampleData
      });

      if (response.success) {
        setTestResult({
          success: true,
          message: `Test email sent successfully to ${testEmail}`
        });
        setTestEmail('');
      } else {
        setTestResult({
          success: false,
          message: response.error || 'Failed to send test email'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Failed to send test email'
      });
    } finally {
      setSendingTest(false);
    }
  };

  // Load preview when template changes
  useEffect(() => {
    if (template && isOpen) {
      loadPreview();
    }
  }, [template, isOpen]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setPreviewData(null);
      setActiveTab('preview');
      setTestEmail('');
      setTestResult(null);
    }
  }, [isOpen]);

  if (!isOpen || !template) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-4 mx-auto p-5 border w-11/12 max-w-5xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Email Preview</h3>
            <p className="text-sm text-gray-600">{template.name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-4">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                type="button"
                onClick={() => setActiveTab('preview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'preview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Preview
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('variables')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'variables'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Variables Used
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('test')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'test'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Send Test Email
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="mt-4">
            {activeTab === 'preview' && (
              <div>
                {loading ? (
                  <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                  </div>
                ) : previewData ? (
                  <div className="space-y-4">
                    {/* Subject Preview */}
                    <div className="bg-gray-50 p-4 rounded-lg border">
                      <div className="text-sm font-medium text-gray-700 mb-2">Email Subject:</div>
                      <div className="text-lg font-semibold text-gray-900">{previewData.subject}</div>
                    </div>

                    {/* Email Content Preview */}
                    <div className="border border-gray-300 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b border-gray-300">
                        <div className="text-sm font-medium text-gray-700">Email Content:</div>
                      </div>
                      <div className="bg-white">
                        <iframe
                          srcDoc={previewData.html_content}
                          className="w-full h-96 border-none"
                          title="Email Preview"
                          sandbox="allow-same-origin"
                        />
                      </div>
                    </div>

                    {/* Template Info */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <div className="flex items-center">
                        <svg className="w-5 h-5 text-blue-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="text-sm text-blue-800">
                          <strong>Template:</strong> {template.template_type_display} • 
                          <strong> Type:</strong> {template.template_type}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-96 text-gray-500">
                    <div className="text-center">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <p className="mt-2">Failed to load preview</p>
                      <button
                        onClick={loadPreview}
                        className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
                      >
                        Try Again
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'variables' && (
              <div>
                {previewData ? (
                  <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Variables Used in This Preview:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(previewData.variables_used).map(([key, value]) => (
                          <div key={key} className="bg-white p-3 rounded border">
                            <div className="text-xs font-mono text-blue-600 mb-1">
                              {`{{${key}}}`}
                            </div>
                            <div className="text-sm text-gray-900 break-words">
                              {String(value)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <div className="flex">
                        <svg className="w-5 h-5 text-blue-400 mt-0.5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="text-sm text-blue-800">
                          <strong>Note:</strong> This preview uses sample data. Actual emails will use real user and subscription data from your database.
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-48 text-gray-500">
                    <div className="text-center">
                      <p>Load preview first to see variables</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'test' && (
              <div className="space-y-4">
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <div className="flex">
                    <svg className="w-5 h-5 text-yellow-400 mt-0.5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <div className="text-sm text-yellow-800">
                      <strong>Test Mode:</strong> This will send a real email using sample data to the specified address.
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="test-email" className="block text-sm font-medium text-gray-700 mb-2">
                    Send test email to:
                  </label>
                  <div className="flex space-x-3">
                    <input
                      type="email"
                      id="test-email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter email address"
                    />
                    <button
                      onClick={sendTestEmail}
                      disabled={!testEmail || sendingTest}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {sendingTest ? 'Sending...' : 'Send Test'}
                    </button>
                  </div>
                </div>

                {testResult && (
                  <div className={`p-4 rounded-lg ${
                    testResult.success 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex">
                      <svg 
                        className={`w-5 h-5 mt-0.5 mr-2 flex-shrink-0 ${
                          testResult.success ? 'text-green-400' : 'text-red-400'
                        }`} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        {testResult.success ? (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        )}
                      </svg>
                      <div className={`text-sm ${
                        testResult.success ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {testResult.message}
                      </div>
                    </div>
                  </div>
                )}

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Sample Data Used:</h4>
                  <pre className="text-xs text-gray-600 bg-white p-3 rounded border overflow-auto">
                    {JSON.stringify(getSampleDataForType(template.template_type), null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end pt-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md text-sm font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}