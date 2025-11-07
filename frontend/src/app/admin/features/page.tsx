'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface Feature {
  id: string;
  key: string;
  name: string;
  description: string;
  category: 'signals' | 'telegram' | 'courses' | 'support' | 'api' | 'analytics';
  icon: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface FeatureFormData {
  key: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
}

const CATEGORIES = [
  { value: 'signals', label: 'Signals & Trading' },
  { value: 'telegram', label: 'Telegram Groups' },
  { value: 'courses', label: 'Courses & Education' },
  { value: 'support', label: 'Support & Mentorship' },
  { value: 'api', label: 'API & Integrations' },
  { value: 'analytics', label: 'Analytics & Reporting' },
];

const COMMON_ICONS = ['✨', '📊', '💬', '📚', '🎓', '💰', '🔒', '🎯', '⚡', '🚀', '💡', '🛠️', '📈', '🔔', '👥', '📱'];

export default function FeaturesPage() {
  const router = useRouter();
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingFeature, setEditingFeature] = useState<Feature | null>(null);
  const [saving, setSaving] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  const [formData, setFormData] = useState<FeatureFormData>({
    key: '',
    name: '',
    description: '',
    category: 'signals',
    icon: '✨',
    sort_order: 0,
    is_active: true
  });

  useEffect(() => {
    loadFeatures();
  }, [selectedCategory]);

  const loadFeatures = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      let url = 'http://127.0.0.1:8000/api/admin/features/';
      if (selectedCategory !== 'all') {
        url += `?category=${selectedCategory}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFeatures(data.results || data);
      } else if (response.status === 401) {
        router.push('/admin/login');
      }

    } catch (err: any) {
      console.error('Failed to load features:', err);
      setError(err.message || 'Failed to load features');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (feature?: Feature) => {
    if (feature) {
      setEditingFeature(feature);
      setFormData({
        key: feature.key,
        name: feature.name,
        description: feature.description,
        category: feature.category,
        icon: feature.icon,
        sort_order: feature.sort_order,
        is_active: feature.is_active
      });
    } else {
      setEditingFeature(null);
      setFormData({
        key: '',
        name: '',
        description: '',
        category: 'signals',
        icon: '✨',
        sort_order: 0,
        is_active: true
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingFeature(null);
  };

  const handleSave = async () => {
    if (!formData.name || !formData.key) {
      setError('Name and key are required');
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

      const url = editingFeature
        ? `http://127.0.0.1:8000/api/admin/features/${editingFeature.id}/`
        : 'http://127.0.0.1:8000/api/admin/features/';

      const method = editingFeature ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || errorData.error || 'Failed to save feature');
      }

      await loadFeatures();
      handleCloseModal();
    } catch (err: any) {
      setError(err.message || 'Failed to save feature');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (featureId: string) => {
    if (!confirm('Are you sure you want to delete this feature? This action cannot be undone.')) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/admin/login');
        return;
      }

      const response = await fetch(`http://127.0.0.1:8000/api/admin/features/${featureId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete feature');
      }

      await loadFeatures();
    } catch (err: any) {
      setError(err.message || 'Failed to delete feature');
    }
  };

  const handleToggleActive = async (feature: Feature) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch(`http://127.0.0.1:8000/api/admin/features/${feature.id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !feature.is_active })
      });

      if (response.ok) {
        await loadFeatures();
      }
    } catch (err: any) {
      console.error('Failed to toggle feature:', err);
    }
  };

  const handleBulkAction = async (action: 'activate' | 'deactivate') => {
    if (selectedFeatures.length === 0) {
      alert('Please select features first');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const endpoint = action === 'activate' ? 'bulk_activate' : 'bulk_deactivate';
      const response = await fetch(`http://127.0.0.1:8000/api/admin/features/${endpoint}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: selectedFeatures })
      });

      if (response.ok) {
        setSelectedFeatures([]);
        await loadFeatures();
      }
    } catch (err: any) {
      console.error(`Failed to ${action} features:`, err);
    }
  };

  const getCategoryLabel = (category: string): string => {
    return CATEGORIES.find(c => c.value === category)?.label || category;
  };

  const groupedFeatures = features.reduce((acc, feature) => {
    if (!acc[feature.category]) {
      acc[feature.category] = [];
    }
    acc[feature.category].push(feature);
    return acc;
  }, {} as Record<string, Feature[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading features...</p>
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
            <h1 className="text-3xl font-bold text-gray-900">Features</h1>
            <p className="mt-2 text-gray-600">Manage platform capabilities and feature flags</p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Feature
          </button>
        </div>

        {/* Filters and Bulk Actions */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-center gap-4 justify-between">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Category:</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 text-sm"
              >
                <option value="all">All Categories</option>
                {CATEGORIES.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>

            {selectedFeatures.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">{selectedFeatures.length} selected</span>
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
                  onClick={() => setSelectedFeatures([])}
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

      {/* Features List */}
      {features.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Features Yet</h3>
          <p className="text-gray-600 mb-6">Create your first feature to get started</p>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create First Feature
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedFeatures).map(([category, categoryFeatures]) => (
            <div key={category} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">{getCategoryLabel(category)}</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {categoryFeatures.map(feature => (
                  <div key={feature.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1">
                        <input
                          type="checkbox"
                          checked={selectedFeatures.includes(feature.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedFeatures([...selectedFeatures, feature.id]);
                            } else {
                              setSelectedFeatures(selectedFeatures.filter(id => id !== feature.id));
                            }
                          }}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <div className="text-2xl">{feature.icon}</div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <h3 className="text-base font-semibold text-gray-900">{feature.name}</h3>
                            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                              {feature.key}
                            </span>
                            <span className={`text-xs font-semibold px-2 py-1 rounded ${
                              feature.is_active
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {feature.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{feature.description || 'No description'}</p>
                          <p className="text-xs text-gray-400 mt-1">Sort order: {feature.sort_order}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleOpenModal(feature)}
                          className="px-3 py-1.5 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleToggleActive(feature)}
                          className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                            feature.is_active
                              ? 'text-gray-700 border border-gray-300 hover:bg-gray-50'
                              : 'text-white bg-green-600 hover:bg-green-700'
                          }`}
                        >
                          {feature.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDelete(feature.id)}
                          className="px-3 py-1.5 text-sm text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
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
                  {editingFeature ? 'Edit Feature' : 'Create New Feature'}
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
                  Feature Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  placeholder="e.g., Premium Signals Access"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Feature Key <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '_') })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-mono"
                  placeholder="e.g., premium_signals_access"
                  required
                  disabled={!!editingFeature}
                />
                <p className="text-xs text-gray-500 mt-1">Unique identifier (lowercase, underscores only). Cannot be changed after creation.</p>
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
                  placeholder="Describe what this feature provides..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
                  >
                    {CATEGORIES.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Sort Order
                  </label>
                  <input
                    type="number"
                    value={formData.sort_order}
                    onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">Icon</label>
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    className="w-20 px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 text-center text-2xl"
                    maxLength={2}
                  />
                  <span className="text-sm text-gray-600">or choose from common icons:</span>
                </div>
                <div className="grid grid-cols-8 gap-2">
                  {COMMON_ICONS.map(icon => (
                    <button
                      key={icon}
                      type="button"
                      onClick={() => setFormData({ ...formData, icon })}
                      className={`p-2 text-2xl rounded-lg border-2 hover:border-blue-500 transition-colors ${
                        formData.icon === icon ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                      }`}
                    >
                      {icon}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active (feature is available)</span>
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
                disabled={saving || !formData.name || !formData.key}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {saving && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                <span>{saving ? 'Saving...' : (editingFeature ? 'Update Feature' : 'Create Feature')}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
