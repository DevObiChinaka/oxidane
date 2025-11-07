'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface Coupon {
  id: string;
  code: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: string;
  description: string;
  valid_from: string;
  valid_until: string | null;
  max_uses: number | null;
  max_uses_per_user: number;
  current_uses: number;
  is_active: boolean;
  plans: string[];
  created_at: string;
  updated_at: string;
}

interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
}

interface CouponFormData {
  code: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: string;
  description: string;
  valid_from: string;
  valid_until: string;
  max_uses: string;
  max_uses_per_user: number;
  is_active: boolean;
  plan_ids: string[];
}

export default function CouponsPage() {
  const router = useRouter();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState<Coupon | null>(null);
  const [saving, setSaving] = useState(false);
  const [selectedCoupons, setSelectedCoupons] = useState<string[]>([]);
  const [filterActive, setFilterActive] = useState<string>('all');

  const [formData, setFormData] = useState<CouponFormData>({
    code: '',
    discount_type: 'percentage',
    discount_value: '',
    description: '',
    valid_from: new Date().toISOString().slice(0, 16),
    valid_until: '',
    max_uses: '',
    max_uses_per_user: 1,
    is_active: true,
    plan_ids: []
  });

  useEffect(() => {
    loadData();
  }, [filterActive]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load coupons
      let couponsUrl = 'http://127.0.0.1:8000/api/admin/coupons/';
      if (filterActive !== 'all') {
        couponsUrl += `?is_active=${filterActive === 'active'}`;
      }
      
      const couponsRes = await fetch(couponsUrl, { headers });
      if (couponsRes.ok) {
        const couponsData = await couponsRes.json();
        setCoupons(couponsData.results || couponsData);
      } else if (couponsRes.status === 401) {
        router.push('/admin/login');
        return;
      }

      // Load plans for the form
      const plansRes = await fetch('http://127.0.0.1:8000/api/admin/plans/', { headers });
      if (plansRes.ok) {
        const plansData = await plansRes.json();
        setPlans(plansData.results || plansData);
      }

    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load coupons');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (coupon?: Coupon) => {
    if (coupon) {
      setEditingCoupon(coupon);
      setFormData({
        code: coupon.code,
        discount_type: coupon.discount_type,
        discount_value: coupon.discount_value,
        description: coupon.description,
        valid_from: coupon.valid_from.slice(0, 16),
        valid_until: coupon.valid_until ? coupon.valid_until.slice(0, 16) : '',
        max_uses: coupon.max_uses?.toString() || '',
        max_uses_per_user: coupon.max_uses_per_user,
        is_active: coupon.is_active,
        plan_ids: coupon.plans
      });
    } else {
      setEditingCoupon(null);
      setFormData({
        code: '',
        discount_type: 'percentage',
        discount_value: '',
        description: '',
        valid_from: new Date().toISOString().slice(0, 16),
        valid_until: '',
        max_uses: '',
        max_uses_per_user: 1,
        is_active: true,
        plan_ids: []
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingCoupon(null);
  };

  const handleSave = async () => {
    if (!formData.code || !formData.discount_value) {
      setError('Code and discount value are required');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const url = editingCoupon
        ? `http://127.0.0.1:8000/api/admin/coupons/${editingCoupon.id}/`
        : 'http://127.0.0.1:8000/api/admin/coupons/';

      const method = editingCoupon ? 'PUT' : 'POST';

      const payload = {
        ...formData,
        max_uses: formData.max_uses ? parseInt(formData.max_uses) : null,
        valid_until: formData.valid_until || null
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Failed to save coupon');
      }

      await loadData();
      handleCloseModal();
    } catch (err: any) {
      setError(err.message || 'Failed to save coupon');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (couponId: string) => {
    if (!confirm('Are you sure you want to delete this coupon? This action cannot be undone.')) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const response = await fetch(`http://127.0.0.1:8000/api/admin/coupons/${couponId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete coupon');
      }

      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to delete coupon');
    }
  };

  const handleToggleActive = async (coupon: Coupon) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`http://127.0.0.1:8000/api/admin/coupons/${coupon.id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !coupon.is_active })
      });

      if (response.ok) {
        await loadData();
      }
    } catch (err: any) {
      console.error('Failed to toggle coupon:', err);
    }
  };

  const handleBulkAction = async (action: 'activate' | 'deactivate') => {
    if (selectedCoupons.length === 0) {
      alert('Please select coupons first');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const endpoint = action === 'activate' ? 'bulk_activate' : 'bulk_deactivate';
      const response = await fetch(`http://127.0.0.1:8000/api/admin/coupons/${endpoint}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: selectedCoupons })
      });

      if (response.ok) {
        setSelectedCoupons([]);
        await loadData();
      }
    } catch (err: any) {
      console.error(`Failed to ${action} coupons:`, err);
    }
  };

  const getDiscountDisplay = (coupon: Coupon): string => {
    if (coupon.discount_type === 'percentage') {
      return `${parseFloat(coupon.discount_value)}% off`;
    } else {
      return `$${parseFloat(coupon.discount_value)} off`;
    }
  };

  const getExpiryStatus = (coupon: Coupon): { status: 'active' | 'expired' | 'upcoming'; label: string; color: string } => {
    const now = new Date();
    const validFrom = new Date(coupon.valid_from);
    const validUntil = coupon.valid_until ? new Date(coupon.valid_until) : null;

    if (now < validFrom) {
      return { status: 'upcoming', label: 'Upcoming', color: 'bg-blue-100 text-blue-700' };
    }
    if (validUntil && now > validUntil) {
      return { status: 'expired', label: 'Expired', color: 'bg-red-100 text-red-700' };
    }
    return { status: 'active', label: 'Active Period', color: 'bg-green-100 text-green-700' };
  };

  const getUsagePercentage = (coupon: Coupon): number => {
    if (!coupon.max_uses) return 0;
    return (coupon.current_uses / coupon.max_uses) * 100;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading coupons...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Coupons</h1>
            <p className="mt-2 text-gray-600">Manage discount codes and promotional offers</p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Coupon
          </button>
        </div>

        {/* Filters and Bulk Actions */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-center gap-4 justify-between">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Status:</label>
              <select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value)}
                className="w-32 px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 text-sm cursor-pointer"
              >
                <option value="all" className="text-gray-900 py-2">All Coupons</option>
                <option value="active" className="text-gray-900 py-2">Active Only</option>
                <option value="inactive" className="text-gray-900 py-2">Inactive Only</option>
              </select>
            </div>

            {selectedCoupons.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">{selectedCoupons.length} selected</span>
                <button
                  onClick={() => handleBulkAction('activate')}
                  className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Activate
                </button>
                <button
                  onClick={() => handleBulkAction('deactivate')}
                  className="px-3 py-1.5 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Deactivate
                </button>
                <button
                  onClick={() => setSelectedCoupons([])}
                  className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-500 text-red-800 px-4 py-3 rounded-lg flex items-start">
          <svg className="w-5 h-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <p className="font-semibold">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700 font-bold text-lg">
            ✕
          </button>
        </div>
      )}

      {/* Coupons List */}
      {coupons.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Coupons Yet</h3>
          <p className="text-gray-600 mb-6">Create your first discount coupon to start offering promotions</p>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create First Coupon
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {coupons.map(coupon => {
            const expiryStatus = getExpiryStatus(coupon);
            const usagePercent = getUsagePercentage(coupon);

            return (
              <div key={coupon.id} className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
                <div className="p-6">
                  {/* Header with checkbox and code */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3 flex-1">
                      <input
                        type="checkbox"
                        checked={selectedCoupons.includes(coupon.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCoupons([...selectedCoupons, coupon.id]);
                          } else {
                            setSelectedCoupons(selectedCoupons.filter(id => id !== coupon.id));
                          }
                        }}
                        className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-2xl font-bold font-mono text-gray-900">{coupon.code}</h3>
                          <span className={`text-xs font-semibold px-2 py-1 rounded ${
                            coupon.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {coupon.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span className={`text-xs font-semibold px-2 py-1 rounded ${expiryStatus.color}`}>
                            {expiryStatus.label}
                          </span>
                        </div>
                        <p className="text-lg font-semibold text-blue-600">{getDiscountDisplay(coupon)}</p>
                        {coupon.description && (
                          <p className="text-sm text-gray-600 mt-2">{coupon.description}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Usage Stats */}
                  <div className="mb-4 bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-gray-600">Usage</span>
                      <span className="font-semibold text-gray-900">
                        {coupon.current_uses} {coupon.max_uses ? `/ ${coupon.max_uses}` : ''}
                        {!coupon.max_uses && <span className="text-gray-500 ml-1">(unlimited)</span>}
                      </span>
                    </div>
                    {coupon.max_uses && (
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all ${
                            usagePercent >= 90 ? 'bg-red-500' :
                            usagePercent >= 70 ? 'bg-amber-500' :
                            'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(usagePercent, 100)}%` }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Validity Period */}
                  <div className="mb-4 text-sm">
                    <div className="flex items-center text-gray-600 mb-1">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="font-medium">Valid from:</span>
                      <span className="ml-2">{formatDate(coupon.valid_from)}</span>
                    </div>
                    {coupon.valid_until && (
                      <div className="flex items-center text-gray-600">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="font-medium">Expires:</span>
                        <span className="ml-2">{formatDate(coupon.valid_until)}</span>
                      </div>
                    )}
                  </div>

                  {/* Plans */}
                  {coupon.plans.length > 0 && (
                    <div className="mb-4 text-sm">
                      <span className="text-gray-600 font-medium">Applies to:</span>
                      <span className="ml-2 text-gray-900">{coupon.plans.length} plan(s)</span>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="grid grid-cols-2 gap-2 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => handleOpenModal(coupon)}
                      className="px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleToggleActive(coupon)}
                      className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                        coupon.is_active
                          ? 'text-gray-700 border border-gray-300 hover:bg-gray-50'
                          : 'text-white bg-green-600 hover:bg-green-700'
                      }`}
                    >
                      {coupon.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => handleDelete(coupon.id)}
                      className="col-span-2 px-3 py-2 text-sm text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  {editingCoupon ? 'Edit Coupon' : 'Create New Coupon'}
                </h2>
                <button
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Coupon Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase().replace(/[^A-Z0-9_-]/g, '') })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-mono text-lg"
                  placeholder="e.g., SAVE20, SUMMER2024"
                  required
                  disabled={!!editingCoupon}
                />
                <p className="text-xs text-gray-500 mt-1">Uppercase letters, numbers, underscores, and hyphens only. Cannot be changed after creation.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Discount Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.discount_type}
                    onChange={(e) => setFormData({ ...formData, discount_type: e.target.value as 'percentage' | 'fixed' })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed">Fixed Amount ($)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Discount Value <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max={formData.discount_type === 'percentage' ? '100' : undefined}
                    value={formData.discount_value}
                    onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder={formData.discount_type === 'percentage' ? '0-100' : '0.00'}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  placeholder="Internal description or notes about this coupon..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Valid From <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.valid_from}
                    onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Valid Until
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Max Total Uses
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.max_uses}
                    onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="Unlimited"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for unlimited</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Max Uses Per User
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_uses_per_user}
                    onChange={(e) => setFormData({ ...formData, max_uses_per_user: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Applicable Plans
                </label>
                <div className="border-2 border-gray-300 rounded-lg p-3 max-h-40 overflow-y-auto">
                  {plans.length === 0 ? (
                    <p className="text-sm text-gray-500">No plans available</p>
                  ) : (
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.plan_ids.length === 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({ ...formData, plan_ids: [] });
                            }
                          }}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700 font-semibold">All Plans</span>
                      </label>
                      {plans.map(plan => (
                        <label key={plan.id} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.plan_ids.includes(plan.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setFormData({ ...formData, plan_ids: [...formData.plan_ids, plan.id] });
                              } else {
                                setFormData({ ...formData, plan_ids: formData.plan_ids.filter(id => id !== plan.id) });
                              }
                            }}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">{plan.name}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">Select specific plans or leave all unchecked to apply to all plans</p>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active (coupon is available for use)</span>
                </label>
              </div>
            </div>

            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex items-center justify-end space-x-3">
              <button
                onClick={handleCloseModal}
                disabled={saving}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formData.code || !formData.discount_value}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                <span>{saving ? 'Saving...' : (editingCoupon ? 'Update Coupon' : 'Create Coupon')}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
