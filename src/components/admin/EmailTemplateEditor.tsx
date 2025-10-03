'use client';

import { useState, useEffect } from 'react';
import { adminAPI } from '../../utils/api';

interface EmailTemplate {
  id?: string;
  name: string;
  template_type: string;
  template_type_display?: string;
  status: 'active' | 'inactive' | 'draft';
  subject_template: string;
  html_content: string;
  text_content: string;
  description: string;
  is_default: boolean;
  from_email?: string;
  from_name?: string;
  available_variables?: Record<string, string>;
}

interface EmailTemplateType {
  value: string;
  label: string;
  description: string;
}

interface EmailTemplateEditorProps {
  template: EmailTemplate | null;
  templateTypes: EmailTemplateType[];
  isOpen: boolean;
  onClose: () => void;
  onSave: (template: EmailTemplate) => void;
}

export default function EmailTemplateEditor({
  template,
  templateTypes,
  isOpen,
  onClose,
  onSave
}: EmailTemplateEditorProps) {
  const [formData, setFormData] = useState<EmailTemplate>({
    name: '',
    template_type: '',
    status: 'draft',
    subject_template: '',
    html_content: '',
    text_content: '',
    description: '',
    is_default: false,
    from_email: '',
    from_name: ''
  });

  const [availableVariables, setAvailableVariables] = useState<Record<string, string>>({});
  const [showVariables, setShowVariables] = useState(false);
  const [activeTab, setActiveTab] = useState<'html' | 'text' | 'preview'>('html');
  const [previewData, setPreviewData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize form when template changes
  useEffect(() => {
    if (template) {
      setFormData({
        ...template,
        from_email: template.from_email || '',
        from_name: template.from_name || ''
      });
      setAvailableVariables(template.available_variables || {});
    } else {
      setFormData({
        name: '',
        template_type: '',
        status: 'draft',
        subject_template: '',
        html_content: '',
        text_content: '',
        description: '',
        is_default: false,
        from_email: '',
        from_name: ''
      });
      setAvailableVariables({});
    }
    setErrors({});
  }, [template]);

  // Load available variables when template type changes
  useEffect(() => {
    if (formData.template_type && !template) {
      loadVariablesForType(formData.template_type);
    }
  }, [formData.template_type]);

  const loadVariablesForType = async (templateType: string) => {
    try {
      // Create a temporary template to get default variables
      const tempTemplate = await adminAPI.createEmailTemplate({
        name: 'temp',
        template_type: templateType,
        subject_template: 'temp',
        html_content: 'temp',
        status: 'draft'
      });
      
      if (tempTemplate.success) {
        // Get the template details to see available variables
        const details = await adminAPI.getEmailTemplate(tempTemplate.template.id);
        if (details.success) {
          setAvailableVariables(details.template.available_variables || {});
        }
        
        // Delete the temporary template
        await adminAPI.deleteEmailTemplate(tempTemplate.template.id);
      }
    } catch (error) {
      console.error('Failed to load variables:', error);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when field is modified
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const insertVariable = (variable: string) => {
    const variableTag = `{{${variable}}}`;
    
    if (activeTab === 'html') {
      const textarea = document.getElementById('html-content') as HTMLTextAreaElement;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const newText = text.substring(0, start) + variableTag + text.substring(end);
        
        setFormData(prev => ({ ...prev, html_content: newText }));
        
        // Restore cursor position
        setTimeout(() => {
          textarea.focus();
          textarea.setSelectionRange(start + variableTag.length, start + variableTag.length);
        }, 0);
      }
    } else if (activeTab === 'text') {
      const textarea = document.getElementById('text-content') as HTMLTextAreaElement;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const newText = text.substring(0, start) + variableTag + text.substring(end);
        
        setFormData(prev => ({ ...prev, text_content: newText }));
        
        setTimeout(() => {
          textarea.focus();
          textarea.setSelectionRange(start + variableTag.length, start + variableTag.length);
        }, 0);
      }
    } else {
      // For subject line
      const input = document.getElementById('subject-template') as HTMLInputElement;
      if (input) {
        const start = input.selectionStart || 0;
        const end = input.selectionEnd || 0;
        const text = input.value;
        const newText = text.substring(0, start) + variableTag + text.substring(end);
        
        setFormData(prev => ({ ...prev, subject_template: newText }));
        
        setTimeout(() => {
          input.focus();
          input.setSelectionRange(start + variableTag.length, start + variableTag.length);
        }, 0);
      }
    }
  };

  const generatePreview = async () => {
    if (!formData.id && !formData.template_type) return;
    
    try {
      let templateId = formData.id;
      
      // If creating new template, we need to save it first to preview
      if (!templateId) {
        const tempTemplate = await adminAPI.createEmailTemplate({
          ...formData,
          name: formData.name || 'Preview Template',
          status: 'draft'
        });
        
        if (!tempTemplate.success) {
          console.error('Failed to create temp template for preview');
          return;
        }
        
        templateId = tempTemplate.template.id;
      }
      
      const response = await adminAPI.previewEmailTemplate(templateId, {
        sample_data: {
          user: {
            first_name: 'John',
            last_name: 'Doe',
            email: 'john.doe@example.com'
          },
          subscription: {
            plan_type: 'monthly',
            amount_paid: 99.00,
            currency: 'USD'
          },
          custom: {
            renewal_link: 'https://oxiworld.com/renew/123',
            days_remaining: 7
          }
        }
      });
      
      if (response.success) {
        setPreviewData(response);
      }
      
      // Clean up temp template if we created one
      if (!formData.id && templateId) {
        await adminAPI.deleteEmailTemplate(templateId);
      }    } catch (error) {
      console.error('Failed to generate preview:', error);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    }
    
    if (!formData.template_type) {
      newErrors.template_type = 'Template type is required';
    }
    
    if (!formData.subject_template.trim()) {
      newErrors.subject_template = 'Subject template is required';
    }
    
    if (!formData.html_content.trim()) {
      newErrors.html_content = 'HTML content is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    
    try {
      let response;
      
      if (template?.id) {
        // Update existing template
        response = await adminAPI.put(`/users/admin/email-templates/${template.id}/`, formData);
      } else {
        // Create new template
        response = await adminAPI.post('/users/admin/email-templates/', formData);
      }
      
      if (response.success) {
        onSave(response.template || formData);
        onClose();
      } else {
        setErrors({ general: 'Failed to save template' });
      }
    } catch (error) {
      console.error('Failed to save template:', error);
      setErrors({ general: 'Failed to save template' });
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-4 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b">
          <h3 className="text-lg font-medium text-gray-900">
            {template ? 'Edit Email Template' : 'Create Email Template'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Panel - Form Fields */}
          <div className="lg:col-span-1 space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Template Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`mt-1 block w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter template name"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="template_type" className="block text-sm font-medium text-gray-700">
                Template Type *
              </label>
              <select
                id="template_type"
                value={formData.template_type}
                onChange={(e) => handleInputChange('template_type', e.target.value)}
                className={`mt-1 block w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.template_type ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select type</option>
                {templateTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {errors.template_type && <p className="mt-1 text-sm text-red-600">{errors.template_type}</p>}
            </div>

            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                Status
              </label>
              <select
                id="status"
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => handleInputChange('is_default', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-sm text-gray-700">Set as default for this type</span>
              </label>
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                id="description"
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe when this template is used"
              />
            </div>

            <div>
              <label htmlFor="from_name" className="block text-sm font-medium text-gray-700">
                From Name
              </label>
              <input
                type="text"
                id="from_name"
                value={formData.from_name}
                onChange={(e) => handleInputChange('from_name', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., OxiWorld Support"
              />
            </div>

            <div>
              <label htmlFor="from_email" className="block text-sm font-medium text-gray-700">
                From Email
              </label>
              <input
                type="email"
                id="from_email"
                value={formData.from_email}
                onChange={(e) => handleInputChange('from_email', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Leave blank to use default"
              />
            </div>

            {/* Variables Panel */}
            {Object.keys(availableVariables).length > 0 && (
              <div className="border-t pt-4">
                <button
                  type="button"
                  onClick={() => setShowVariables(!showVariables)}
                  className="flex items-center justify-between w-full text-sm font-medium text-gray-700"
                >
                  <span>Available Variables</span>
                  <svg
                    className={`w-4 h-4 transform transition-transform ${showVariables ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showVariables && (
                  <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                    {Object.entries(availableVariables).map(([key, description]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => insertVariable(key)}
                        className="w-full text-left px-2 py-1 text-xs bg-gray-50 hover:bg-gray-100 rounded border"
                        title={description}
                      >
                        <code className="text-blue-600">{`{{${key}}}`}</code>
                        <div className="text-gray-500 truncate">{description}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Content Editor */}
          <div className="lg:col-span-3">
            {/* Subject Line */}
            <div className="mb-4">
              <label htmlFor="subject-template" className="block text-sm font-medium text-gray-700">
                Email Subject *
              </label>
              <input
                type="text"
                id="subject-template"
                value={formData.subject_template}
                onChange={(e) => handleInputChange('subject_template', e.target.value)}
                className={`mt-1 block w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.subject_template ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter email subject with variables like {{user.first_name}}"
              />
              {errors.subject_template && <p className="mt-1 text-sm text-red-600">{errors.subject_template}</p>}
            </div>

            {/* Content Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                <button
                  type="button"
                  onClick={() => setActiveTab('html')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'html'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  HTML Content
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('text')}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'text'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Text Content
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('preview');
                    generatePreview();
                  }}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'preview'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Preview
                </button>
              </nav>
            </div>

            {/* Content Area */}
            <div className="mt-4">
              {activeTab === 'html' && (
                <div>
                  <textarea
                    id="html-content"
                    rows={20}
                    value={formData.html_content}
                    onChange={(e) => handleInputChange('html_content', e.target.value)}
                    className={`block w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.html_content ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter HTML email content with variables"
                  />
                  {errors.html_content && <p className="mt-1 text-sm text-red-600">{errors.html_content}</p>}
                </div>
              )}

              {activeTab === 'text' && (
                <div>
                  <textarea
                    id="text-content"
                    rows={20}
                    value={formData.text_content}
                    onChange={(e) => handleInputChange('text_content', e.target.value)}
                    className="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter plain text version (optional - will be auto-generated if empty)"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Plain text version for email clients that don't support HTML
                  </p>
                </div>
              )}

              {activeTab === 'preview' && (
                <div className="border border-gray-300 rounded-md p-4 bg-gray-50 min-h-96">
                  {previewData ? (
                    <div>
                      <div className="mb-4 p-3 bg-white rounded border">
                        <div className="text-sm text-gray-600">Subject:</div>
                        <div className="font-medium">{previewData.subject}</div>
                      </div>
                      <div className="bg-white rounded border">
                        <iframe
                          srcDoc={previewData.html_content}
                          className="w-full h-96 border-none"
                          title="Email Preview"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-96 text-gray-500">
                      <div className="text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <p className="mt-2">Click Preview to see how your email will look</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex items-center justify-between pt-4 border-t">
          <div>
            {errors.general && (
              <p className="text-sm text-red-600">{errors.general}</p>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : (template ? 'Update Template' : 'Create Template')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}