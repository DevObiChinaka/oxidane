'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface ReferralCode {
  id: string;
  code: string;
  referrer: {
    id: string;
    username: string;
    email: string;
  };
  referrer_discount_type: 'percentage' | 'fixed';
  referrer_discount_value: string;
  referee_discount_type: 'percentage' | 'fixed';
  referee_discount_value: string;
  max_uses: number | null;
  current_uses: number;
  valid_from: string;
  valid_until: string | null;
  is_active: boolean;
  description: string;
  created_at: string;
  updated_at: string;
}

interface ReferralFormData {
  code: string;
  referrer_discount_type: 'percentage' | 'fixed';
  referrer_discount_value: string;
  referee_discount_type: 'percentage' | 'fixed';
  referee_discount_value: string;
  max_uses: string;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
  description: string;
}

export default function ReferralsPage() {
  const router = useRouter();
  const [referrals, setReferrals] = useState<ReferralCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingReferral, setEditingReferral] = useState<ReferralCode | null>(null);
  const [saving, setSaving] = useState(false);
  const [filterActive, setFilterActive] = useState<string>('all');
  const [selectedReferrals, setSelectedReferrals] = useState<string[]>([]);

  const [formData, setFormData] = useState<ReferralFormData>({
    code: '',
    referrer_discount_type: 'percentage',
    referrer_discount_value: '10.00',
    referee_discount_type: 'percentage',
    referee_discount_value: '10.00',
    max_uses: '',
    valid_from: new Date().toISOString().slice(0, 16),
    valid_until: '',
    is_active: true,
    description: ''
  });

  useEffect(() => {
    loadReferrals();
  }, [filterActive]);

  const loadReferrals = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      let url = 'http://127.0.0.1:8000/api/admin/referrals/codes/';
      if (filterActive !== 'all') {
        url += `?is_active=${filterActive === 'active'}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReferrals(data.results || data);
      } else if (response.status === 401) {
        router.push('/admin/login');
      }

    } catch (err: any) {
      console.error('Failed to load referrals:', err);
      setError(err.message || 'Failed to load referral codes');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (referral?: ReferralCode) => {
    if (referral) {
      setEditingReferral(referral);
      setFormData({
        code: referral.code,
        referrer_discount_type: referral.referrer_discount_type,
        referrer_discount_value: referral.referrer_discount_value,
        referee_discount_type: referral.referee_discount_type,
        referee_discount_value: referral.referee_discount_value,
        max_uses: referral.max_uses?.toString() || '',
        valid_from: referral.valid_from.slice(0, 16),
        valid_until: referral.valid_until?.slice(0, 16) || '',
        is_active: referral.is_active,
        description: referral.description
      });
    } else {
      setEditingReferral(null);
      setFormData({
        code: '',
        referrer_discount_type: 'percentage',
        referrer_discount_value: '10.00',
        referee_discount_type: 'percentage',
        referee_discount_value: '10.00',
        max_uses: '',
        valid_from: new Date().toISOString().slice(0, 16),
        valid_until: '',
        is_active: true,
        description: ''
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingReferral(null);
  };

  const handleSave = async () => {
    if (!formData.code) {
      setError('Code is required');
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

      const payload = {
        code: formData.code.toUpperCase(),
        referrer_discount_type: formData.referrer_discount_type,
        referrer_discount_value: formData.referrer_discount_value,
        referee_discount_type: formData.referee_discount_type,
        referee_discount_value: formData.referee_discount_value,
        max_uses: formData.max_uses ? parseInt(formData.max_uses) : null,
        valid_from: formData.valid_from,
        valid_until: formData.valid_until || null,
        is_active: formData.is_active,
        description: formData.description
      };

      const url = editingReferral
        ? `http://127.0.0.1:8000/api/admin/referrals/codes/${editingReferral.id}/`
        : 'http://127.0.0.1:8000/api/admin/referrals/codes/';

      const method = editingReferral ? 'PUT' : 'POST';

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
        throw new Error(errorData.detail || errorData.error || 'Failed to save referral code');
      }

      await loadReferrals();
      handleCloseModal();
    } catch (err: any) {
      setError(err.message || 'Failed to save referral code');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (referralId: string) => {
    if (!confirm('Are you sure you want to delete this referral code?')) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`http://127.0.0.1:8000/api/admin/referrals/codes/${referralId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete referral code');
      }

      await loadReferrals();
    } catch (err: any) {
      setError(err.message || 'Failed to delete referral code');
    }
  };

  const handleToggleActive = async (referral: ReferralCode) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`http://127.0.0.1:8000/api/admin/referrals/codes/${referral.id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !referral.is_active })
      });

      if (response.ok) {
        await loadReferrals();
      }
    } catch (err: any) {
      console.error('Failed to toggle referral:', err);
    }
  };

  const formatDiscount = (type: string, value: string): string => {
    return type === 'percentage' ? `${value}%` : `$${value}`;
  };

  const getRemainingUses = (referral: ReferralCode): string => {
    if (!referral.max_uses) return 'Unlimited';
    const remaining = referral.max_uses - referral.current_uses;
    return remaining > 0 ? remaining.toString() : '0';
  };

  const isExpired = (referral: ReferralCode): boolean => {
    if (!referral.valid_until) return false;
    return new Date(referral.valid_until) < new Date();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading referral codes...</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Referral Codes</h1>
            <p className="mt-2 text-gray-600">Manage referral codes and track commission rewards</p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Referral Code
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Status:</label>
            <select
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value)}
              className="w-32 px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 text-sm cursor-pointer"
            >
              <option value="all" className="text-gray-900 py-2">All Codes</option>
              <option value="active" className="text-gray-900 py-2">Active Only</option>
              <option value="inactive" className="text-gray-900 py-2">Inactive Only</option>
            </select>
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

      {/* Referral Codes List */}
      {referrals.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Referral Codes Yet</h3>
          <p className="text-gray-600 mb-6">Create your first referral code to get started</p>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create First Referral Code
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {referrals.map(referral => (
            <div key={referral.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-xl font-bold text-gray-900 font-mono">{referral.code}</h3>
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      referral.is_active && !isExpired(referral)
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {isExpired(referral) ? 'Expired' : (referral.is_active ? 'Active' : 'Inactive')}
                    </span>
                    {referral.max_uses && referral.current_uses >= referral.max_uses && (
                      <span className="text-xs font-semibold px-2 py-1 rounded bg-orange-100 text-orange-700">
                        Exhausted
                      </span>
                    )}
                  </div>

                  {referral.description && (
                    <p className="text-sm text-gray-600 mb-4">{referral.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Referrer Reward</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {formatDiscount(referral.referrer_discount_type, referral.referrer_discount_value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Referee Discount</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {formatDiscount(referral.referee_discount_type, referral.referee_discount_value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Usage</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {referral.current_uses} / {referral.max_uses || '∞'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Remaining</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {getRemainingUses(referral)}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                    <span>Owner: {referral.referrer.username}</span>
                    <span>•</span>
                    <span>Created: {new Date(referral.created_at).toLocaleDateString()}</span>
                    {referral.valid_until && (
                      <>
                        <span>•</span>
                        <span className={isExpired(referral) ? 'text-red-600 font-semibold' : ''}>
                          Expires: {new Date(referral.valid_until).toLocaleDateString()}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleOpenModal(referral)}
                    className="px-3 py-1.5 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleActive(referral)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      referral.is_active
                        ? 'text-gray-700 border border-gray-300 hover:bg-gray-50'
                        : 'text-white bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {referral.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    onClick={() => handleDelete(referral.id)}
                    className="px-3 py-1.5 text-sm text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  {editingReferral ? 'Edit Referral Code' : 'Create New Referral Code'}
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

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Referral Code */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Referral Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-mono uppercase"
                  placeholder="e.g., JOHN2024"
                  required
                  disabled={!!editingReferral}
                />
                <p className="text-xs text-gray-500 mt-1">Uppercase letters, numbers, and underscores only (min 3 chars)</p>
              </div>

              {/* Referrer Discount */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Referrer Reward (Code Owner)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select
                      value={formData.referrer_discount_type}
                      onChange={(e) => setFormData({ ...formData, referrer_discount_type: e.target.value as 'percentage' | 'fixed' })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
                    >
                      <option value="percentage">Percentage (%)</option>
                      <option value="fixed">Fixed Amount ($)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Value</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.referrer_discount_value}
                      onChange={(e) => setFormData({ ...formData, referrer_discount_value: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Referee Discount */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Referee Discount (Person Using Code)</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select
                      value={formData.referee_discount_type}
                      onChange={(e) => setFormData({ ...formData, referee_discount_type: e.target.value as 'percentage' | 'fixed' })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
                    >
                      <option value="percentage">Percentage (%)</option>
                      <option value="fixed">Fixed Amount ($)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Value</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.referee_discount_value}
                      onChange={(e) => setFormData({ ...formData, referee_discount_value: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Usage Limits and Validity */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">Max Uses</label>
                  <input
                    type="number"
                    value={formData.max_uses}
                    onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    placeholder="Unlimited"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for unlimited uses</p>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">Expires On</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for no expiry</p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  placeholder="Optional description..."
                />
              </div>

              {/* Active Status */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active (code can be used)</span>
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
                disabled={saving || !formData.code}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                <span>{saving ? 'Saving...' : (editingReferral ? 'Update Code' : 'Create Code')}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
