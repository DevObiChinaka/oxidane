import { useState } from 'react';

interface PricingPlan {
  id?: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  plan_category: 'signals' | 'mentorship' | 'vip';
  billing_cycle: 'one_time' | 'weekly' | 'monthly' | 'yearly';
  telegram_groups: string[];
  features_list?: string[];
  is_active: boolean;
  is_featured: boolean;
}

interface PricingPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (planData: Omit<PricingPlan, 'id'>) => Promise<void>;
  editingPlan?: PricingPlan | null;
  isLoading?: boolean;
}

export default function PricingPlanModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  editingPlan, 
  isLoading = false 
}: PricingPlanModalProps) {
  const [features, setFeatures] = useState<string[]>(editingPlan?.features_list || ['']);
  const [telegramGroups, setTelegramGroups] = useState<string[]>(editingPlan?.telegram_groups || ['']);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const planData: Omit<PricingPlan, 'id'> = {
      plan_type: formData.get('plan_type') as string,
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      price: parseFloat(formData.get('price') as string),
      currency: formData.get('currency') as string,
      plan_category: formData.get('plan_category') as 'signals' | 'mentorship' | 'vip',
      billing_cycle: formData.get('billing_cycle') as 'one_time' | 'weekly' | 'monthly' | 'yearly',
      telegram_groups: telegramGroups.filter(group => group.trim() !== ''),
      features_list: features.filter(feature => feature.trim() !== ''),
      is_active: formData.get('is_active') === 'on',
      is_featured: formData.get('is_featured') === 'on'
    };

    console.log('📋 Submitting plan data:', planData);

    try {
      setError(''); // Clear any previous errors
      setSuccess(''); // Clear any previous success messages
      await onSubmit(planData);
      
      // Show success message briefly before closing
      const actionText = editingPlan ? 'updated' : 'created';
      setSuccess(`✅ Pricing plan ${actionText} successfully!`);
      
      // Close modal after a short delay to show success message
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error: any) {
      console.error('❌ Failed to submit plan:', error);
      
      // Handle specific validation errors with user-friendly messages
      if (error?.response?.data) {
        const errorData = error.response.data;
        
        if (errorData.plan_type) {
          if (Array.isArray(errorData.plan_type)) {
            if (errorData.plan_type.includes('pricing plan with this plan type already exists.')) {
              setError('⚠️ This plan type is already in use. Each plan type must be unique. Please select a different plan type from the dropdown.');
            } else {
              setError(`Plan Type Error: ${errorData.plan_type.join(', ')}`);
            }
          } else {
            setError(`Plan Type Error: ${errorData.plan_type}`);
          }
        } else if (errorData.name) {
          setError(`Plan Name Error: ${Array.isArray(errorData.name) ? errorData.name.join(', ') : errorData.name}`);
        } else if (errorData.price) {
          setError(`Price Error: ${Array.isArray(errorData.price) ? errorData.price.join(', ') : errorData.price}`);
        } else if (errorData.telegram_groups) {
          setError(`Telegram Groups Error: ${Array.isArray(errorData.telegram_groups) ? errorData.telegram_groups.join(', ') : errorData.telegram_groups}`);
        } else if (errorData.features_list) {
          setError(`Features Error: ${Array.isArray(errorData.features_list) ? errorData.features_list.join(', ') : errorData.features_list}`);
        } else if (errorData.non_field_errors) {
          setError(`Validation Error: ${Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors.join(', ') : errorData.non_field_errors}`);
        } else {
          // Generic handling for other validation errors
          const errorMessages = Object.entries(errorData).map(([field, messages]: [string, any]) => {
            const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const messageText = Array.isArray(messages) ? messages.join(', ') : messages;
            return `${fieldName}: ${messageText}`;
          });
          setError(`Validation Errors:\n${errorMessages.join('\n')}`);
        }
      } else if (error?.message) {
        setError(`Network Error: ${error.message}`);
      } else {
        setError('❌ Failed to save pricing plan. Please check your connection and try again.');
      }
    }
  };

  const addFeature = () => {
    setFeatures([...features, '']);
  };

  const updateFeature = (index: number, value: string) => {
    const newFeatures = [...features];
    newFeatures[index] = value;
    setFeatures(newFeatures);
  };

  const removeFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index));
  };

  const addTelegramGroup = () => {
    setTelegramGroups([...telegramGroups, '']);
  };

  const updateTelegramGroup = (index: number, value: string) => {
    const newGroups = [...telegramGroups];
    newGroups[index] = value;
    setTelegramGroups(newGroups);
  };

  const removeTelegramGroup = (index: number) => {
    setTelegramGroups(telegramGroups.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              {editingPlan ? 'Edit Pricing Plan' : 'Add New Pricing Plan'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-red-800 mb-1">Validation Error</h3>
                    <div className="text-sm text-red-700 whitespace-pre-line">{error}</div>
                  </div>
                  <button
                    onClick={() => setError('')}
                    className="ml-2 text-red-400 hover:text-red-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-green-700 font-medium">{success}</div>
                </div>
              </div>
            )}

            {/* Basic Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plan Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    defaultValue={editingPlan?.name || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                    placeholder="Monthly Premium Signals"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plan Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="plan_type"
                    required
                    defaultValue={editingPlan?.plan_type || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  >
                    <option value="" disabled className="text-gray-400">Select plan type...</option>
                    
                    {/* Mentorship Plans */}
                    <optgroup label="Mentorship Plans">
                      <option value="mentorship_basic">Basic Mentorship</option>
                    </optgroup>
                    
                    {/* Signals Plans */}
                    <optgroup label="Signals Plans">
                      <option value="signals_weekly">Weekly Signals</option>
                      <option value="signals_monthly">Monthly Signals</option>
                      <option value="signals_yearly">Yearly Signals</option>
                    </optgroup>
                    
                    {/* VIP Plans */}
                    <optgroup label="VIP Plans">
                      <option value="vip_weekly">Weekly VIP</option>
                      <option value="vip_monthly">Monthly VIP</option>
                      <option value="vip_yearly">Yearly VIP</option>
                    </optgroup>
                    
                    {/* Legacy Plans */}
                    <optgroup label="Legacy Plans">
                      <option value="course">Individual Course</option>
                      <option value="course_bundle">Course Bundle</option>
                      <option value="combo_basic">Basic Combo</option>
                      <option value="combo_premium">Premium Combo</option>
                    </optgroup>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    💡 Each plan type must be unique. If you get an error, that plan type already exists.
                  </p>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    name="description"
                    required
                    rows={3}
                    defaultValue={editingPlan?.description || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                    placeholder="Comprehensive trading signals with expert analysis..."
                  />
                </div>
              </div>
            </div>

            {/* Pricing & Categories */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Pricing & Categories</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price <span className="text-red-500">*</span>
                  </label>
                  <div className="flex">
                    <select
                      name="currency"
                      defaultValue={editingPlan?.currency || 'USD'}
                      className="w-24 px-3 py-2 border border-gray-300 rounded-l-md focus:ring-[#000ABE] focus:border-[#000ABE] bg-gray-50 text-gray-900"
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                    </select>
                    <input
                      type="number"
                      name="price"
                      required
                      min="0"
                      step="0.01"
                      defaultValue={editingPlan?.price || ''}
                      className="flex-1 px-3 py-2 border border-l-0 border-gray-300 rounded-r-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                      placeholder="50.00"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plan Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="plan_category"
                    required
                    defaultValue={editingPlan?.plan_category || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  >
                    <option value="" disabled className="text-gray-400">Select a category...</option>
                    <option value="signals">Signals</option>
                    <option value="mentorship">Mentorship</option>
                    <option value="vip">VIP</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing Cycle <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="billing_cycle"
                    required
                    defaultValue={editingPlan?.billing_cycle || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  >
                    <option value="" disabled className="text-gray-400">Select billing cycle...</option>
                    <option value="one_time">One Time</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-900">Features</h4>
                <button
                  type="button"
                  onClick={addFeature}
                  className="text-sm text-[#000ABE] hover:text-[#000ABE]/80 font-medium"
                >
                  + Add Feature
                </button>
              </div>
              <div className="space-y-2">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={feature}
                      onChange={(e) => updateFeature(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                      placeholder="Live trading signals 24/7"
                    />
                    {features.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeFeature(index)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Telegram Groups */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-900">Telegram Groups Access</h4>
                <button
                  type="button"
                  onClick={addTelegramGroup}
                  className="text-sm text-[#000ABE] hover:text-[#000ABE]/80 font-medium"
                >
                  + Add Group
                </button>
              </div>
              <div className="space-y-2">
                {telegramGroups.map((group, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={group}
                      onChange={(e) => updateTelegramGroup(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                      placeholder="signals_main"
                    />
                    {telegramGroups.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTelegramGroup(index)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Status Options */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Status Options</h4>
              <div className="flex items-center space-x-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_active"
                    defaultChecked={editingPlan?.is_active ?? true}
                    className="rounded border-gray-300 text-[#000ABE] focus:ring-[#000ABE]"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active Plan</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_featured"
                    defaultChecked={editingPlan?.is_featured ?? false}
                    className="rounded border-gray-300 text-[#000ABE] focus:ring-[#000ABE]"
                  />
                  <span className="ml-2 text-sm text-gray-700">Featured Plan</span>
                </label>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-[#000ABE] text-white text-sm font-medium rounded-md hover:bg-[#000ABE]/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isLoading && (
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {editingPlan ? 'Update Plan' : 'Create Plan'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}