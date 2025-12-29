'use client';

import { useState, useEffect } from 'react';
import { 
  usePricingPlans, 
  useCouponCodes,
  usePricingPlanActions,
  useCouponActions 
} from '../hooks/useAdminAPI';
import PricingPlanModal from '../../../components/admin/PricingPlanModal';
import CouponCodeModal from '../../../components/admin/CouponCodeModal';
import CouponCodeCard from '../../../components/admin/CouponCodeCard';

interface PricingPlan {
  id: string;
  plan_type: string;
  name: string;
  description: string;
  price: number;
  current_price?: number;
  currency: string;
  plan_category: 'signals' | 'mentorship';
  billing_cycle: 'one_time' | 'weekly' | 'monthly';
  duration_days: number | null;
  gives_course_access: boolean;
  gives_signals_access: boolean;
  telegram_group_key: string;
  features_list?: string[];
  is_active: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

interface CouponCode {
  id: string;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed_amount';
  discount_value: number;
  minimum_amount?: number;
  usage_limit?: number;
  usage_count: number;
  plans: string[];
  valid_from: string;
  valid_until: string;
  is_active: boolean;
  created_at: string;
  usage_percentage?: number;
}

// Pricing Plan Card Component
function PricingPlanCard({ 
  plan, 
  onEdit, 
  onToggleActive, 
  onToggleFeatured, 
  onDelete, 
  isLoading 
}: {
  plan: PricingPlan;
  onEdit: (plan: PricingPlan) => void;
  onToggleActive: (id: string) => void;
  onToggleFeatured: (id: string) => void;
  onDelete: (id: string) => void;
  isLoading: boolean;
}) {
  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const getPlanCategoryBadge = (category: string) => {
    const colors = {
      signals: 'bg-blue-100 text-blue-800 border border-blue-200',
      mentorship: 'bg-purple-100 text-purple-800 border border-purple-200'
    };
    
    const displayText = category.charAt(0).toUpperCase() + category.slice(1);
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colors[category as keyof typeof colors]}`}>
        {displayText}
      </span>
    );
  };

  const getBillingCycleBadge = (cycle: string) => {
    const config = {
      one_time: { 
        color: 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 border border-purple-200', 
        text: 'LIFETIME'
      },
      weekly: { 
        color: 'bg-green-100 text-green-800 border border-green-200', 
        text: 'WEEKLY'
      },
      monthly: { 
        color: 'bg-blue-100 text-blue-800 border border-blue-200', 
        text: 'MONTHLY'
      }
    };

    const cycleConfig = config[cycle as keyof typeof config] || config.monthly;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${cycleConfig.color}`}>
        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        {cycleConfig.text}
      </span>
    );
  };

  const getDurationBadge = (durationDays: number | null) => {
    if (durationDays === null) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 border border-purple-200">
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
          Lifetime
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 border border-gray-200">
        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {durationDays} days
      </span>
    );
  };

  const getPlanTypeIcon = (category: string) => {
    const iconClass = "w-5 h-5 text-white";
    
    switch (category) {
      case 'signals':
        return (
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
        );
      case 'mentorship':
        return (
          <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.168 18.477 18.582 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gradient-to-r from-gray-500 to-gray-600 rounded-lg flex items-center justify-center">
            <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border-2 hover:shadow-lg transition-all duration-200 ${
      plan.is_featured ? 'border-yellow-300 ring-2 ring-yellow-200' : 'border-gray-200 hover:border-gray-300'
    }`}>
      {/* Card Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              {getPlanTypeIcon(plan.plan_category)}
              <h4 className="text-base font-semibold text-gray-900">{plan.name}</h4>
              {plan.is_featured && (
                <div className="flex items-center px-1.5 py-0.5 bg-gradient-to-r from-yellow-100 to-orange-100 rounded-full">
                  <svg className="w-3 h-3 text-yellow-600 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  <span className="text-xs font-medium text-yellow-700">Featured</span>
                </div>
              )}
            </div>
            {plan.description && plan.description.length > 60 ? (
              <p className="mt-1 text-xs text-gray-600">{plan.description.substring(0, 60)}...</p>
            ) : (
              <p className="mt-1 text-xs text-gray-600">{plan.description}</p>
            )}
          </div>
          <div className="flex items-center ml-3">
            <div className={`w-3 h-3 rounded-full ${plan.is_active ? 'bg-green-400' : 'bg-red-400'}`}></div>
          </div>
        </div>
        
        {/* Price */}
        <div className="mt-3">
          <div className="flex items-baseline space-x-2">
            <span className="text-xl font-bold text-gray-900">
              {formatCurrency(plan.current_price || plan.price, plan.currency)}
            </span>
            <span className="text-xs font-medium text-gray-500">
              / {plan.billing_cycle.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center flex-wrap gap-2 mt-2">
            {getPlanCategoryBadge(plan.plan_category)}
            {getBillingCycleBadge(plan.billing_cycle)}
            {getDurationBadge(plan.duration_days)}
          </div>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4">
        {/* Access Permissions */}
        <div className="mb-3">
          <h5 className="text-xs font-medium text-gray-900 mb-2 flex items-center">
            <svg className="w-3 h-3 text-blue-500 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Access
          </h5>
          <div className="flex flex-wrap gap-1.5">
            {plan.gives_course_access && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.168 18.477 18.582 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Courses
              </span>
            )}
            {plan.gives_signals_access && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Signals
              </span>
            )}
            {plan.telegram_group_key && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-50 text-gray-700 border border-gray-200">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                {plan.telegram_group_key}
              </span>
            )}
          </div>
        </div>

        {/* Features - Show max 2 */}
        {plan.features_list && plan.features_list.length > 0 && (
          <div className="mb-3">
            <h5 className="text-xs font-medium text-gray-900 mb-2 flex items-center">
              <svg className="w-3 h-3 text-green-500 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Features
            </h5>
            <ul className="space-y-1">
              {plan.features_list.slice(0, 2).map((feature, index) => (
                <li key={index} className="text-xs text-gray-600 flex items-start">
                  <svg className="w-3 h-3 text-green-500 mr-1.5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="line-clamp-1">{feature}</span>
                </li>
              ))}
              {plan.features_list.length > 2 && (
                <li className="text-xs text-gray-500 ml-4">
                  +{plan.features_list.length - 2} more
                </li>
              )}
            </ul>
          </div>
        )}

      </div>

      {/* Card Actions */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 rounded-b-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onEdit(plan)}
              className="inline-flex items-center p-1.5 rounded-lg text-[#000ABE] hover:bg-[#000ABE]/10 transition-colors"
              title="Edit Plan"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onToggleActive(plan.id)}
              className={`inline-flex items-center p-1.5 rounded-lg transition-colors ${
                plan.is_active 
                  ? 'text-red-600 hover:bg-red-50' 
                  : 'text-green-600 hover:bg-green-50'
              }`}
              disabled={isLoading}
              title={plan.is_active ? 'Deactivate Plan' : 'Activate Plan'}
            >
              {plan.is_active ? (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M15 14h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </button>
            <button
              onClick={() => onToggleFeatured(plan.id)}
              className="inline-flex items-center p-1.5 rounded-lg text-yellow-600 hover:bg-yellow-50 transition-colors"
              disabled={isLoading}
              title={plan.is_featured ? 'Remove from Featured' : 'Mark as Featured'}
            >
              {plan.is_featured ? (
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              )}
            </button>
          </div>
          <button
            onClick={() => onDelete(plan.id)}
            className="inline-flex items-center p-1.5 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
            disabled={isLoading}
            title="Delete Plan"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PricingManagement() {
  const [activeTab, setActiveTab] = useState<'plans' | 'coupons'>('plans');
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [selectedCoupon, setSelectedCoupon] = useState<CouponCode | null>(null);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showCouponModal, setShowCouponModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [couponToDelete, setCouponToDelete] = useState<CouponCode | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // API Hooks
  const { data: pricingPlans, loading: plansLoading, error: plansError, refetch: refetchPlans } = usePricingPlans({});
  const { data: couponCodes, loading: couponsLoading, error: couponsError, refetch: refetchCoupons } = useCouponCodes({});
  const planActions = usePricingPlanActions();
  const couponActions = useCouponActions();

  // Ensure we have arrays to work with
  const plansList = Array.isArray(pricingPlans) ? pricingPlans : [];
  const couponsList = Array.isArray(couponCodes) ? couponCodes : [];

  // Refresh data when needed
  useEffect(() => {
    if (refreshTrigger > 0) {
      refetchPlans();
      refetchCoupons();
    }
  }, [refreshTrigger, refetchPlans, refetchCoupons]);

  const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

  // Handle plan actions
  const handleTogglePlanActive = async (planId: string) => {
    try {
      await planActions.toggleActive(planId);
      triggerRefresh();
    } catch (error) {
          }
  };

  const handleTogglePlanFeatured = async (planId: string) => {
    try {
      await planActions.toggleFeatured(planId);
      triggerRefresh();
    } catch (error) {
          }
  };

  const handleDeletePlan = async (planId: string) => {
    if (window.confirm('Are you sure you want to delete this pricing plan?')) {
      try {
        await planActions.deletePlan(planId);
        triggerRefresh();
      } catch (error) {
              }
    }
  };

  const handleCreatePlan = async (planData: any) => {
    try {
      await planActions.createPlan(planData);
      triggerRefresh();
    } catch (error) {
            throw error;
    }
  };

  const handleUpdatePlan = async (planData: any) => {
    if (!selectedPlan?.id) return;
    try {
      await planActions.updatePlan(selectedPlan.id, planData);
      setSelectedPlan(null);
      triggerRefresh();
    } catch (error) {
            throw error;
    }
  };

  // Handle coupon actions
  const handleToggleCouponActive = async (couponId: string) => {
    try {
      await couponActions.toggleActive(couponId);
      triggerRefresh();
    } catch (error) {
          }
  };

  const handleDeleteCoupon = async (couponId: string) => {
    const coupon = couponsList.find((c: CouponCode) => c.id === couponId);
    if (coupon) {
      setCouponToDelete(coupon);
      setShowDeleteModal(true);
    }
  };

  const confirmDeleteCoupon = async () => {
    if (couponToDelete) {
      try {
        await couponActions.deleteCoupon(couponToDelete.id);
        setShowDeleteModal(false);
        setCouponToDelete(null);
        triggerRefresh();
      } catch (error) {
              }
    }
  };

  const cancelDeleteCoupon = () => {
    setShowDeleteModal(false);
    setCouponToDelete(null);
  };

  const handleCreateCoupon = async (couponData: any) => {
    try {
      await couponActions.createCoupon(couponData);
      triggerRefresh();
    } catch (error) {
            throw error;
    }
  };

  const handleUpdateCoupon = async (couponData: any) => {
    if (!selectedCoupon?.id) return;
    try {
      await couponActions.updateCoupon(selectedCoupon.id, couponData);
      setSelectedCoupon(null);
      triggerRefresh();
    } catch (error) {
            throw error;
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="md:flex md:items-center md:justify-between">
              <div className="min-w-0 flex-1">
                <h1 className="text-3xl font-bold text-gray-900">Pricing Management</h1>
                <p className="mt-2 text-sm text-gray-600">
                  Manage subscription plans and coupon codes with professional interface
                </p>
              </div>
              <div className="mt-4 flex md:ml-4 md:mt-0 space-x-3">
                <button
                  onClick={() => setShowPlanModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#000ABE] hover:bg-[#000ABE]/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#000ABE]"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add Pricing Plan
                </button>
                <button
                  onClick={() => setShowCouponModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#000ABE]"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  Add Coupon Code
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-6">
              <nav className="flex space-x-8" aria-label="Tabs">
                {[
                  { key: 'plans', label: 'Pricing Plans', count: plansList.length },
                  { key: 'coupons', label: 'Coupon Codes', count: couponsList.length }
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as any)}
                    className={`${
                      activeTab === tab.key
                        ? 'border-[#000ABE] text-[#000ABE]'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    } whitespace-nowrap border-b-2 py-2 px-1 text-sm font-medium flex items-center`}
                  >
                    {tab.label}
                    {tab.count !== null && (
                      <span className="ml-2 rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                        {tab.count}
                      </span>
                    )}
                  </button>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'plans' && (
          <div className="space-y-6">
            {/* Pricing Plans Cards */}
            <div>
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Pricing Plans</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Manage your subscription plans and pricing structure
                </p>
              </div>
              
              {plansLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((n) => (
                    <div key={n} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
                      <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : plansError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                  <p className="text-red-600">Error loading pricing plans: {plansError}</p>
                </div>
              ) : (
                <>
                  {/* Featured Plans Section */}
                  {plansList.some((plan: PricingPlan) => plan.is_featured) && (
                    <div className="mb-8">
                      <div className="flex items-center mb-4">
                        <div className="w-6 h-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center mr-3">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        </div>
                        <h3 className="text-xl font-bold text-gray-900">Featured Plans</h3>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {plansList.filter((plan: PricingPlan) => plan.is_featured).map((plan: PricingPlan) => (
                          <PricingPlanCard 
                            key={plan.id} 
                            plan={plan}
                            onEdit={(plan) => {
                              setSelectedPlan(plan);
                              setShowPlanModal(true);
                            }}
                            onToggleActive={handleTogglePlanActive}
                            onToggleFeatured={handleTogglePlanFeatured}
                            onDelete={handleDeletePlan}
                            isLoading={planActions.loading}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Plans by Category */}
                  {['mentorship', 'signals'].map((category) => {
                    const categoryPlans = plansList.filter(
                      (plan: PricingPlan) => plan.plan_category === category
                    );
                    
                    if (categoryPlans.length === 0) return null;

                    return (
                      <div key={category} className="mb-8">
                        <div className="mb-4">
                          <h3 className="text-xl font-bold text-gray-900">
                            {category.charAt(0).toUpperCase() + category.slice(1)} Plans
                          </h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {categoryPlans.map((plan: PricingPlan) => (
                            <PricingPlanCard 
                              key={plan.id} 
                              plan={plan}
                              onEdit={(plan) => {
                                setSelectedPlan(plan);
                                setShowPlanModal(true);
                              }}
                              onToggleActive={handleTogglePlanActive}
                              onToggleFeatured={handleTogglePlanFeatured}
                              onDelete={handleDeletePlan}
                              isLoading={planActions.loading}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  {/* Empty State - No Plans */}
                  {plansList.length === 0 && (
                    <div className="text-center py-12">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No pricing plans</h3>
                      <p className="mt-1 text-sm text-gray-500">Get started by creating your first pricing plan.</p>
                      <div className="mt-6">
                        <button
                          onClick={() => setShowPlanModal(true)}
                          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-[#000ABE] hover:bg-[#000ABE]/90"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          Create Pricing Plan
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {activeTab === 'coupons' && (
          <div className="space-y-6">
            {/* Coupon Codes Section */}
            <div>
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Coupon Codes</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Manage discount codes and promotional offers
                </p>
              </div>

              {couponsLoading ? (
                <div className="text-center py-8">Loading coupon codes...</div>
              ) : couponsError ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                  <p className="text-red-600">Error loading coupon codes: {couponsError}</p>
                </div>
              ) : couponsList.length === 0 ? (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                  <div className="text-gray-500 mb-2 text-4xl">🎫</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No coupon codes yet</h3>
                  <p className="text-gray-600 mb-4">Create your first discount code to boost sales</p>
                  <button
                    onClick={() => setShowCouponModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#000ABE] hover:bg-[#000ABE]/90"
                  >
                    Create Coupon Code
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {couponsList.map((coupon: CouponCode) => (
                    <CouponCodeCard
                      key={coupon.id}
                      coupon={coupon}
                      onEdit={(coupon) => {
                        setSelectedCoupon(coupon);
                        setShowCouponModal(true);
                      }}
                      onToggleActive={handleToggleCouponActive}
                      onDelete={handleDeleteCoupon}
                      isLoading={couponActions.loading}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Pricing Plan Modal */}
      <PricingPlanModal
        isOpen={showPlanModal}
        onClose={() => {
          setShowPlanModal(false);
          setSelectedPlan(null);
        }}
        onSubmit={selectedPlan ? handleUpdatePlan : handleCreatePlan}
        editingPlan={selectedPlan}
        isLoading={planActions.loading}
      />

      {/* Coupon Code Modal */}
      <CouponCodeModal
        isOpen={showCouponModal}
        onClose={() => {
          setShowCouponModal(false);
          setSelectedCoupon(null);
        }}
        onSubmit={selectedCoupon ? handleUpdateCoupon : handleCreateCoupon}
        editingCoupon={selectedCoupon}
        isLoading={couponActions.loading}
        availablePlans={plansList.map((plan: PricingPlan) => ({
          id: plan.id,
          name: plan.name
        }))}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteModal && couponToDelete && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              {/* Icon */}
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              
              {/* Content */}
              <div className="mt-5 text-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Delete Coupon Code
                </h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    Are you sure you want to delete the coupon code <span className="font-semibold text-gray-900">"{couponToDelete.code}"</span>?
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    This action cannot be undone and will permanently remove this coupon code from the system.
                  </p>
                </div>
                
                {/* Actions */}
                <div className="flex justify-center space-x-4 mt-6">
                  <button
                    onClick={cancelDeleteCoupon}
                    className="px-4 py-2 bg-gray-300 text-gray-800 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmDeleteCoupon}
                    disabled={couponActions.loading}
                    className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {couponActions.loading ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}