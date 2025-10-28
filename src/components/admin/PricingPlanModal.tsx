import { useState, useEffect } from 'react';

interface PricingPlan {
  id?: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  plan_category: 'signals' | 'mentorship';
  billing_cycle: 'one_time' | 'weekly' | 'monthly';
  duration_days?: number | null;
  gives_course_access: boolean;
  gives_signals_access: boolean;
  telegram_group_key: string;
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
  const [planCategory, setPlanCategory] = useState<'signals' | 'mentorship'>(
    editingPlan?.plan_category || 'mentorship'
  );
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Update category when editing plan changes
  useEffect(() => {
    if (editingPlan) {
      setPlanCategory(editingPlan.plan_category);
      setFeatures(editingPlan.features_list || ['']);
    } else {
      setPlanCategory('mentorship');
      setFeatures(['']);
    }
  }, [editingPlan]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    // Get duration_days - only for signals plans
    const durationDays = planCategory === 'signals' 
      ? parseInt(formData.get('duration_days') as string) || null
      : null;
    
    const planData: Omit<PricingPlan, 'id'> = {
      plan_type: formData.get('plan_type') as string,
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      price: parseFloat(formData.get('price') as string),
      currency: formData.get('currency') as string,
      plan_category: planCategory,
      billing_cycle: formData.get('billing_cycle') as 'one_time' | 'weekly' | 'monthly',
      duration_days: durationDays,
      gives_course_access: planCategory === 'mentorship',
      gives_signals_access: planCategory === 'signals',
      telegram_group_key: formData.get('telegram_group_key') as string,
      features_list: features.filter(feature => feature.trim() !== ''),
      is_active: formData.get('is_active') === 'on',
      is_featured: formData.get('is_featured') === 'on'
    };

    try {
      setError('');
      setSuccess('');
      await onSubmit(planData);
      
      const actionText = editingPlan ? 'updated' : 'created';
      setSuccess(`✅ Pricing plan ${actionText} successfully!`);
      
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error: any) {
      console.error('❌ Failed to submit plan:', error);
      
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
        } else if (errorData.duration_days) {
          setError(`Duration Error: ${Array.isArray(errorData.duration_days) ? errorData.duration_days.join(', ') : errorData.duration_days}`);
        } else if (errorData.telegram_group_key) {
          setError(`Telegram Group Error: ${Array.isArray(errorData.telegram_group_key) ? errorData.telegram_group_key.join(', ') : errorData.telegram_group_key}`);
        } else if (errorData.features_list) {
          setError(`Features Error: ${Array.isArray(errorData.features_list) ? errorData.features_list.join(', ') : errorData.features_list}`);
        } else if (errorData.non_field_errors) {
          setError(`Validation Error: ${Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors.join(', ') : errorData.non_field_errors}`);
        } else {
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

            {/* Product Type Selection - Professional Design */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border-2 border-blue-100">
              <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Product Category
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setPlanCategory('mentorship')}
                  className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                    planCategory === 'mentorship'
                      ? 'border-purple-500 bg-purple-100 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-purple-300'
                  }`}
                >
                  <div className="flex items-center justify-center mb-2">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      planCategory === 'mentorship' 
                        ? 'bg-gradient-to-r from-purple-500 to-purple-600' 
                        : 'bg-gray-200'
                    }`}>
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.168 18.477 18.582 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                  </div>
                  <h5 className="text-sm font-bold text-gray-900 text-center">Mentorship</h5>
                  <p className="text-xs text-gray-600 text-center mt-1">One-time, Lifetime Access</p>
                </button>
                
                <button
                  type="button"
                  onClick={() => setPlanCategory('signals')}
                  className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                    planCategory === 'signals'
                      ? 'border-blue-500 bg-blue-100 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }`}
                >
                  <div className="flex items-center justify-center mb-2">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      planCategory === 'signals' 
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                        : 'bg-gray-200'
                    }`}>
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                  </div>
                  <h5 className="text-sm font-bold text-gray-900 text-center">Signals</h5>
                  <p className="text-xs text-gray-600 text-center mt-1">Duration-based Subscription</p>
                </button>
              </div>
            </div>

            {/* Basic Information */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
              <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Basic Information
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Plan Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    defaultValue={editingPlan?.name || ''}
                    className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-medium transition-all"
                    placeholder={planCategory === 'mentorship' ? 'Mentorship Program' : 'Monthly Premium Signals'}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Plan Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="plan_type"
                    required
                    defaultValue={editingPlan?.plan_type || ''}
                    className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-medium transition-all"
                  >
                    <option value="" disabled className="text-gray-400">Select plan type...</option>
                    
                    {planCategory === 'mentorship' ? (
                      <>
                        <option value="mentorship">Mentorship Program</option>
                      </>
                    ) : (
                      <>
                        <option value="signals_weekly">Weekly Signals</option>
                        <option value="signals_monthly">Monthly Signals</option>
                        <option value="vip_monthly">VIP Signals (Monthly)</option>
                      </>
                    )}
                  </select>
                  <p className="mt-1.5 text-xs text-gray-500 flex items-start">
                    <svg className="w-3 h-3 mr-1 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    Each plan type must be unique
                  </p>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    name="description"
                    required
                    rows={3}
                    defaultValue={editingPlan?.description || ''}
                    className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 transition-all"
                    placeholder={
                      planCategory === 'mentorship' 
                        ? 'Complete mentorship program with lifetime access to all premium courses...' 
                        : 'Premium trading signals with expert analysis and live support...'
                    }
                  />
                </div>
              </div>
            </div>

            {/* Pricing Configuration */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
              <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Pricing & Billing
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Price <span className="text-red-500">*</span>
                  </label>
                  <div className="flex">
                    <select
                      name="currency"
                      defaultValue={editingPlan?.currency || 'USD'}
                      className="w-24 px-3 py-2.5 border-2 border-gray-300 rounded-l-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] bg-gray-50 text-gray-900 font-bold transition-all"
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
                      className="flex-1 px-4 py-2.5 border-2 border-l-0 border-gray-300 rounded-r-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-bold text-lg transition-all"
                      placeholder={planCategory === 'mentorship' ? '799.00' : '99.00'}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Billing Cycle <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="billing_cycle"
                    required
                    value={planCategory === 'mentorship' ? 'one_time' : editingPlan?.billing_cycle || 'monthly'}
                    disabled={planCategory === 'mentorship'}
                    className={`w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-medium transition-all ${
                      planCategory === 'mentorship' ? 'bg-gray-100 cursor-not-allowed' : ''
                    }`}
                  >
                    {planCategory === 'mentorship' ? (
                      <option value="one_time">One Time (Lifetime)</option>
                    ) : (
                      <>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </>
                    )}
                  </select>
                </div>

                {/* Duration - Only for Signals */}
                {planCategory === 'signals' && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Duration (Days) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      name="duration_days"
                      required={planCategory === 'signals'}
                      min="1"
                      defaultValue={editingPlan?.duration_days || ''}
                      className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-medium transition-all"
                      placeholder="7, 30, 90..."
                    />
                    <p className="mt-1.5 text-xs text-gray-500">
                      Number of days the subscription lasts
                    </p>
                  </div>
                )}

                {/* Lifetime Badge - Only for Mentorship */}
                {planCategory === 'mentorship' && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Access Duration
                    </label>
                    <div className="px-4 py-2.5 bg-gradient-to-r from-purple-100 to-pink-100 border-2 border-purple-300 rounded-lg flex items-center">
                      <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                      </svg>
                      <span className="text-sm font-bold text-purple-900">LIFETIME ACCESS</span>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Telegram Group Key <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="telegram_group_key"
                    required
                    defaultValue={editingPlan?.telegram_group_key || ''}
                    className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900 font-medium transition-all"
                    placeholder={planCategory === 'mentorship' ? 'mentorship' : 'signals, vip'}
                  />
                  <p className="mt-1.5 text-xs text-gray-500">
                    Key for Telegram group access (e.g., 'mentorship', 'signals', 'vip')
                  </p>
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