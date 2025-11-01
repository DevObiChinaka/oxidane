import { useState } from 'react';

interface CouponCode {
  id?: string;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed_amount';
  discount_value: number;
  minimum_amount?: number;
  usage_limit?: number;
  applicable_plans: string[];
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

interface CouponCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (couponData: Omit<CouponCode, 'id'>) => Promise<void>;
  editingCoupon?: CouponCode | null;
  isLoading?: boolean;
  availablePlans?: Array<{ id: string; name: string; }>;
}

export default function CouponCodeModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  editingCoupon, 
  isLoading = false,
  availablePlans = []
}: CouponCodeModalProps) {
  const [selectedPlans, setSelectedPlans] = useState<string[]>(editingCoupon?.applicable_plans || []);
  const [discountType, setDiscountType] = useState<'percentage' | 'fixed_amount'>(
    editingCoupon?.discount_type || 'percentage'
  );

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const couponData: Omit<CouponCode, 'id'> = {
      code: formData.get('code') as string,
      description: formData.get('description') as string,
      discount_type: discountType,
      discount_value: parseFloat(formData.get('discount_value') as string),
      minimum_amount: formData.get('minimum_amount') ? parseFloat(formData.get('minimum_amount') as string) : undefined,
      usage_limit: formData.get('usage_limit') ? parseInt(formData.get('usage_limit') as string) : undefined,
      applicable_plans: selectedPlans,
      valid_from: formData.get('valid_from') as string,
      valid_until: formData.get('valid_until') as string,
      is_active: formData.get('is_active') === 'on'
    };

    try {
      await onSubmit(couponData);
      onClose();
    } catch (error) {
      console.error('Failed to submit coupon:', error);
    }
  };

  const generateCouponCode = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const codeInput = document.querySelector('input[name="code"]') as HTMLInputElement;
    if (codeInput) {
      codeInput.value = result;
    }
  };

  const handlePlanSelection = (planId: string) => {
    setSelectedPlans(prev => 
      prev.includes(planId) 
        ? prev.filter(id => id !== planId)
        : [...prev, planId]
    );
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    return new Date(dateString).toISOString().slice(0, 16);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              {editingCoupon ? 'Edit Coupon Code' : 'Add New Coupon Code'}
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
            {/* Basic Information */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Coupon Code <span className="text-red-500">*</span>
                  </label>
                  <div className="flex">
                    <input
                      type="text"
                      name="code"
                      required
                      defaultValue={editingCoupon?.code || ''}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:ring-[#000ABE] focus:border-[#000ABE] uppercase text-gray-900"
                      placeholder="SUMMER2025"
                      style={{ textTransform: 'uppercase' }}
                    />
                    <button
                      type="button"
                      onClick={generateCouponCode}
                      className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md hover:bg-gray-200 text-sm"
                      title="Generate random code"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    name="description"
                    required
                    rows={3}
                    defaultValue={editingCoupon?.description || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                    placeholder="Summer discount for new subscribers..."
                  />
                </div>
              </div>
            </div>

            {/* Discount Configuration */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Discount Configuration</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Discount Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="discount_type"
                    required
                    value={discountType}
                    onChange={(e) => setDiscountType(e.target.value as 'percentage' | 'fixed_amount')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  >
                    <option value="percentage">Percentage</option>
                    <option value="fixed_amount">Fixed Amount</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Discount Value <span className="text-red-500">*</span>
                  </label>
                  <div className="flex">
                    <input
                      type="number"
                      name="discount_value"
                      required
                      min="0"
                      step={discountType === 'percentage' ? "1" : "0.01"}
                      max={discountType === 'percentage' ? "100" : undefined}
                      defaultValue={editingCoupon?.discount_value || ''}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                      placeholder={discountType === 'percentage' ? "10" : "5.00"}
                    />
                    <span className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md text-sm">
                      {discountType === 'percentage' ? '%' : '$'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Order Amount (optional)
                  </label>
                  <input
                    type="number"
                    name="minimum_amount"
                    min="0"
                    step="0.01"
                    defaultValue={editingCoupon?.minimum_amount || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                    placeholder="50.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Usage Limit (optional)
                  </label>
                  <input
                    type="number"
                    name="usage_limit"
                    min="1"
                    defaultValue={editingCoupon?.usage_limit || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                    placeholder="100"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for unlimited uses</p>
                </div>
              </div>
            </div>

            {/* Validity Period */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Validity Period</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valid From <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    name="valid_from"
                    required
                    defaultValue={editingCoupon ? formatDate(editingCoupon.valid_from) : ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valid Until <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    name="valid_until"
                    required
                    defaultValue={editingCoupon ? formatDate(editingCoupon.valid_until) : ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#000ABE] focus:border-[#000ABE] text-gray-900"
                  />
                </div>
              </div>
            </div>

            {/* Applicable Plans */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Applicable Plans</h4>
              <p className="text-sm text-gray-600 mb-4">Select which pricing plans this coupon can be applied to:</p>
              
              {availablePlans.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {availablePlans.map((plan) => (
                    <label key={plan.id} className="flex items-center p-3 border border-gray-200 rounded-md hover:bg-white cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedPlans.includes(plan.id)}
                        onChange={() => handlePlanSelection(plan.id)}
                        className="rounded border-gray-300 text-[#000ABE] focus:ring-[#000ABE]"
                      />
                      <span className="ml-2 text-sm text-gray-700">{plan.name}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-7 7-7-7" />
                  </svg>
                  <p className="text-sm">No pricing plans available</p>
                  <p className="text-xs">Create some pricing plans first to enable coupon targeting</p>
                </div>
              )}
            </div>

            {/* Status Options */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Status</h4>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  defaultChecked={editingCoupon?.is_active ?? true}
                  className="rounded border-gray-300 text-[#000ABE] focus:ring-[#000ABE]"
                />
                <span className="ml-2 text-sm text-gray-700">Active Coupon</span>
              </label>
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
                {editingCoupon ? 'Update Coupon' : 'Create Coupon'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}