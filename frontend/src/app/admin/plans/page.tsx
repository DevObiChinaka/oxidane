'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface Feature {
  id: string;
  name: string;
  key: string;
  description: string;
  category: string;
  icon: string;
  is_active: boolean;
}

interface TelegramGroup {
  id: string;
  name: string;
  group_key: string;
  description: string;
  chat_id: string;
  is_active: boolean;
  member_count: number;
  max_members: number | null;
}

interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  description: string;
  base_price: string;
  billing_period: 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'lifetime';
  trial_days: number;
  is_active: boolean;
  is_featured: boolean;
  sort_order: number;
  limits: Record<string, any>;
  paystack_plan_code: string;
  features: Feature[];
  telegram_groups: TelegramGroup[];
  created_at: string;
  updated_at: string;
}

interface PlanFormData {
  name: string;
  description: string;
  base_price: string;
  billing_period: string;
  trial_days: number;
  is_active: boolean;
  is_featured: boolean;
  sort_order: number;
  limits: string;
  paystack_plan_code: string;
  feature_ids: string[];
  telegram_group_ids: string[];
}

const CURRENCIES = ['USD', 'NGN', 'GBP', 'EUR', 'GHS', 'ZAR'];

export default function PlansPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [telegramGroups, setTelegramGroups] = useState<TelegramGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<SubscriptionPlan | null>(null);
  const [saving, setSaving] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({});

  const [formData, setFormData] = useState<PlanFormData>({
    name: '',
    description: '',
    base_price: '',
    billing_period: 'monthly',
    trial_days: 0,
    is_active: true,
    is_featured: false,
    sort_order: 0,
    limits: '{}',
    paystack_plan_code: '',
    feature_ids: [],
    telegram_group_ids: []
  });

  useEffect(() => {
    loadData();
  }, []);

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

      // Load plans
      const plansRes = await fetch('http://127.0.0.1:8000/api/admin/plans/', { headers });
      if (plansRes.ok) {
        const plansData = await plansRes.json();
        setPlans(plansData.results || plansData);
      }

      // Load features
      const featuresRes = await fetch('http://127.0.0.1:8000/api/admin/features/', { headers });
      if (featuresRes.ok) {
        const featuresData = await featuresRes.json();
        setFeatures(featuresData.results || featuresData);
      }

      // Load Telegram groups
      const groupsRes = await fetch('http://127.0.0.1:8000/api/admin/telegram/groups/', { headers });
      if (groupsRes.ok) {
        const groupsData = await groupsRes.json();
        setTelegramGroups(groupsData.results || groupsData);
      }

      // Note: Exchange rates are managed by backend automatically
      // No need to fetch them separately

    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load plans');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (plan?: SubscriptionPlan) => {
    if (plan) {
      setEditingPlan(plan);
      setFormData({
        name: plan.name,
        description: plan.description,
        base_price: plan.base_price,
        billing_period: plan.billing_period,
        trial_days: plan.trial_days,
        is_active: plan.is_active,
        is_featured: plan.is_featured,
        sort_order: plan.sort_order,
        limits: JSON.stringify(plan.limits, null, 2),
        paystack_plan_code: plan.paystack_plan_code || '',
        feature_ids: plan.features?.map(f => f.id) || [],
        telegram_group_ids: plan.telegram_groups?.map(g => g.id) || []
      });
    } else {
      setEditingPlan(null);
      setFormData({
        name: '',
        description: '',
        base_price: '',
        billing_period: 'monthly',
        trial_days: 0,
        is_active: true,
        is_featured: false,
        sort_order: 0,
        limits: '{}',
        paystack_plan_code: '',
        feature_ids: [],
        telegram_group_ids: []
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingPlan(null);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      // Parse limits JSON
      let limits = {};
      try {
        limits = JSON.parse(formData.limits);
      } catch (e) {
        setError('Invalid JSON in limits field');
        setSaving(false);
        return;
      }

      const payload = {
        name: formData.name,
        description: formData.description,
        base_price: parseFloat(formData.base_price),
        billing_period: formData.billing_period,
        trial_days: formData.trial_days,
        is_active: formData.is_active,
        is_featured: formData.is_featured,
        sort_order: formData.sort_order,
        limits,
        paystack_plan_code: formData.paystack_plan_code,
        feature_ids: formData.feature_ids,
        telegram_group_ids: formData.telegram_group_ids
      };

      const url = editingPlan
        ? `http://127.0.0.1:8000/api/admin/plans/${editingPlan.id}/`
        : 'http://127.0.0.1:8000/api/admin/plans/';

      const method = editingPlan ? 'PUT' : 'POST';

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
        throw new Error(errorData.detail || errorData.error || 'Failed to save plan');
      }

      await loadData();
      handleCloseModal();
    } catch (err: any) {
      console.error('Failed to save plan:', err);
      setError(err.message || 'Failed to save plan');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (planId: string) => {
    if (!confirm('Are you sure you want to delete this plan?')) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const response = await fetch(`http://127.0.0.1:8000/api/admin/plans/${planId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete plan');
      }

      await loadData();
    } catch (err: any) {
      console.error('Failed to delete plan:', err);
      setError(err.message || 'Failed to delete plan');
    }
  };

  const handleToggleActive = async (plan: SubscriptionPlan) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const action = plan.is_active ? 'deactivate' : 'activate';
      const response = await fetch(`http://127.0.0.1:8000/api/admin/plans/${plan.id}/${action}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} plan`);
      }

      await loadData();
    } catch (err: any) {
      console.error('Failed to toggle plan status:', err);
      setError(err.message || 'Failed to toggle plan status');
    }
  };

  const handleClone = async (plan: SubscriptionPlan) => {
    const newName = prompt('Enter name for cloned plan:', `${plan.name} (Copy)`);
    if (!newName) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`http://127.0.0.1:8000/api/admin/plans/${plan.id}/clone/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newName })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to clone plan');
      }

      await loadData();
    } catch (err: any) {
      console.error('Failed to clone plan:', err);
      setError(err.message || 'Failed to clone plan');
    }
  };

  const convertPrice = (usdPrice: string, currency: string): string => {
    const price = parseFloat(usdPrice);
    if (currency === 'USD' || !exchangeRates[currency]) {
      return price.toFixed(2);
    }
    return (price * exchangeRates[currency]).toFixed(2);
  };

  const formatCurrency = (amount: string, currency: string): string => {
    const symbols: Record<string, string> = {
      USD: '$',
      NGN: '₦',
      GBP: '£',
      EUR: '€',
      GHS: '₵',
      ZAR: 'R'
    };
    return `${symbols[currency] || currency} ${amount}`;
  };

  const getBillingPeriodLabel = (period: string): string => {
    const labels: Record<string, string> = {
      weekly: 'Weekly',
      monthly: 'Monthly',
      quarterly: 'Quarterly',
      yearly: 'Yearly',
      lifetime: 'Lifetime'
    };
    return labels[period] || period;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00B38F] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading plans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Subscription Plans</h1>
          <p className="text-gray-600">Manage pricing plans with features and Telegram group access</p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create Plan
        </button>
      </div>

      {/* Currency Selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Display Currency:</label>
            <select
              value={selectedCurrency}
              onChange={(e) => setSelectedCurrency(e.target.value)}
              className="w-32 px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 text-sm cursor-pointer"
            >
              {CURRENCIES.map(currency => (
                <option key={currency} value={currency} className="text-gray-900 py-2">
                  {currency}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Prices stored in USD, converted using live exchange rates</span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <p className="font-medium text-red-800">Error</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {plans.map(plan => (
          <div
            key={plan.id}
            className={`bg-white rounded-lg border transition-shadow hover:shadow-md ${
              plan.is_featured 
                ? 'border-green-400 ring-2 ring-green-100' 
                : 'border-gray-200'
            }`}
          >
            {/* Plan Header */}
            <div className="p-4 border-b border-gray-100">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                {plan.is_featured && (
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                    ⭐ Featured
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 line-clamp-2">{plan.description || 'No description'}</p>
            </div>

            {/* Pricing */}
            <div className="px-4 py-4 bg-gray-50">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">
                  {formatCurrency(convertPrice(plan.base_price, selectedCurrency), selectedCurrency)}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  per {getBillingPeriodLabel(plan.billing_period).toLowerCase()}
                </div>
                {plan.trial_days > 0 && (
                  <div className="mt-2 inline-block bg-green-100 text-green-700 text-xs font-medium px-2 py-1 rounded">
                    {plan.trial_days} days free trial
                  </div>
                )}
              </div>
            </div>

            {/* Features */}
            <div className="px-4 py-3">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Features ({plan.features?.length || 0})
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {plan.features && plan.features.length > 0 ? (
                  <>
                    {plan.features.slice(0, 4).map(feature => (
                      <div key={feature.id} className="flex items-center text-sm text-gray-700">
                        <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span className="truncate">{feature.name}</span>
                      </div>
                    ))}
                    {plan.features.length > 4 && (
                      <div className="text-xs text-gray-500 pl-6">
                        +{plan.features.length - 4} more
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-xs text-gray-500">No features assigned</div>
                )}
              </div>
            </div>

            {/* Telegram Groups */}
            <div className="px-4 py-3 border-t border-gray-200">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Telegram Groups ({plan.telegram_groups?.length || 0})
              </div>
              <div className="space-y-1">
                {plan.telegram_groups && plan.telegram_groups.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {plan.telegram_groups.map(group => (
                      <span key={group.id} className="inline-flex items-center bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
                        💬 {group.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-500">No groups assigned</div>
                )}
              </div>
            </div>

            {/* Status & Actions */}
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  plan.is_active 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {plan.is_active ? '● Active' : '○ Inactive'}
                </span>
                <span className="text-xs text-gray-500">
                  Order: {plan.sort_order}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleOpenModal(plan)}
                  className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleToggleActive(plan)}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                    plan.is_active
                      ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {plan.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  onClick={() => handleClone(plan)}
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-medium rounded hover:bg-gray-50 transition-colors"
                >
                  Clone
                </button>
                <button
                  onClick={() => handleDelete(plan.id)}
                  className="px-3 py-1.5 bg-white border border-red-300 text-red-600 text-xs font-medium rounded hover:bg-red-50 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}

        {plans.length === 0 && (
          <div className="col-span-full bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Plans Yet</h3>
            <p className="text-gray-600 mb-6">Create your first subscription plan to get started</p>
            <button
              onClick={() => handleOpenModal()}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create First Plan
            </button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  {editingPlan ? 'Edit Plan' : 'Create New Plan'}
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

            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
              {/* Basic Info */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Plan Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-[#00B38F] text-gray-900 font-medium"
                      placeholder="e.g., Premium Monthly"
                      required
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900"
                      placeholder="Describe what's included in this plan..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Base Price (USD) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.base_price}
                      onChange={(e) => setFormData({ ...formData, base_price: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900"
                      placeholder="29.99"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Billing Period <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.billing_period}
                      onChange={(e) => setFormData({ ...formData, billing_period: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900"
                    >
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                      <option value="yearly">Yearly</option>
                      <option value="lifetime">Lifetime</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Trial Days
                    </label>
                    <input
                      type="number"
                      value={formData.trial_days}
                      onChange={(e) => setFormData({ ...formData, trial_days: parseInt(e.target.value) || 0 })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900"
                      placeholder="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Sort Order
                    </label>
                    <input
                      type="number"
                      value={formData.sort_order}
                      onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-transparent text-gray-900"
                      placeholder="0"
                    />
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4 text-[#00B38F] border-gray-300 rounded focus:ring-[#00B38F]"
                    />
                    <span className="ml-2 text-sm text-gray-700">Active (available for purchase)</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                      className="w-4 h-4 text-[#00B38F] border-gray-300 rounded focus:ring-[#00B38F]"
                    />
                    <span className="ml-2 text-sm text-gray-700">Featured (highlight on pricing page)</span>
                  </label>
                </div>
              </div>

              {/* Features Selection */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
                <div className="border-2 border-gray-200 rounded-lg p-4 max-h-60 overflow-y-auto space-y-2 bg-gray-50">
                  {features.map(feature => (
                    <label key={feature.id} className="flex items-start p-3 hover:bg-white rounded-lg border border-transparent hover:border-gray-200 transition-all cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.feature_ids.includes(feature.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              feature_ids: [...formData.feature_ids, feature.id]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              feature_ids: formData.feature_ids.filter(id => id !== feature.id)
                            });
                          }
                        }}
                        className="w-5 h-5 mt-0.5 text-[#00B38F] border-2 border-gray-400 rounded focus:ring-[#00B38F] cursor-pointer"
                      />
                      <div className="ml-3">
                        <span className="text-sm font-medium text-gray-900">
                          {feature.icon} {feature.name}
                        </span>
                        <p className="text-xs text-gray-500">{feature.description}</p>
                      </div>
                    </label>
                  ))}
                  {features.length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4">
                      No features available. Create features first.
                    </p>
                  )}
                </div>
              </div>

              {/* Telegram Groups Selection */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Telegram Groups</h3>
                <div className="border-2 border-gray-200 rounded-lg p-4 max-h-60 overflow-y-auto space-y-2 bg-gray-50">
                  {telegramGroups.filter(g => g.is_active).map(group => (
                    <label key={group.id} className="flex items-start p-3 hover:bg-white rounded-lg border border-transparent hover:border-gray-200 transition-all cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.telegram_group_ids.includes(group.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              telegram_group_ids: [...formData.telegram_group_ids, group.id]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              telegram_group_ids: formData.telegram_group_ids.filter(id => id !== group.id)
                            });
                          }
                        }}
                        className="w-5 h-5 mt-0.5 text-[#00B38F] border-2 border-gray-400 rounded focus:ring-[#00B38F] cursor-pointer"
                      />
                      <div className="ml-3">
                        <span className="text-sm font-semibold text-gray-900 flex items-center gap-1">
                          <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                          </svg>
                          {group.name}
                        </span>
                        <p className="text-xs text-gray-600 mt-0.5">{group.description}</p>
                        <p className="text-xs text-gray-500 mt-1 font-medium">
                          {group.member_count} members
                          {group.max_members && ` (max: ${group.max_members})`}
                        </p>
                      </div>
                    </label>
                  ))}
                  {telegramGroups.filter(g => g.is_active).length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4 italic">
                      No active Telegram groups. Configure groups first.
                    </p>
                  )}
                </div>
              </div>

              {/* Advanced Settings */}
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Paystack Plan Code
                    </label>
                    <input
                      type="text"
                      value={formData.paystack_plan_code}
                      onChange={(e) => setFormData({ ...formData, paystack_plan_code: e.target.value })}
                      className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-[#00B38F] text-gray-900 font-medium"
                      placeholder="PLN_xxxxx (optional)"
                    />
                    <p className="text-xs text-gray-600 mt-1.5 flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Leave empty to create manually in Paystack dashboard
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Limits (JSON)
                    </label>
                    <textarea
                      value={formData.limits}
                      onChange={(e) => setFormData({ ...formData, limits: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-[#00B38F] focus:border-[#00B38F] font-mono text-sm text-gray-900 bg-gray-50"
                      placeholder='{"max_signals": 100, "max_courses": 5}'
                    />
                    <p className="text-xs text-gray-600 mt-1.5 flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Define plan limits as JSON (e.g., {`{"max_signals": 100}`})
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
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
                disabled={saving || !formData.name || !formData.base_price}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                <span>{saving ? 'Saving...' : (editingPlan ? 'Update Plan' : 'Create Plan')}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
