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

interface CouponCodeCardProps {
  coupon: CouponCode;
  onEdit: (coupon: CouponCode) => void;
  onToggleActive: (id: string) => void;
  onDelete: (id: string) => void;
  isLoading: boolean;
}

export default function CouponCodeCard({ 
  coupon, 
  onEdit, 
  onToggleActive, 
  onDelete, 
  isLoading 
}: CouponCodeCardProps) {
  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDiscountDisplay = () => {
    if (coupon.discount_type === 'percentage') {
      return `${coupon.discount_value}% OFF`;
    } else {
      return `$${coupon.discount_value} OFF`;
    }
  };

  const getUsageStats = () => {
    if (coupon.usage_limit) {
      return `${coupon.usage_count} / ${coupon.usage_limit} uses`;
    }
    return `${coupon.usage_count} uses`;
  };

  const getStatusColor = () => {
    const now = new Date();
    const validFrom = new Date(coupon.valid_from);
    const validUntil = new Date(coupon.valid_until);

    if (!coupon.is_active) {
      return 'bg-gray-100 text-gray-600';
    } else if (now < validFrom) {
      return 'bg-yellow-100 text-yellow-800';
    } else if (now > validUntil) {
      return 'bg-red-100 text-red-800';
    } else {
      return 'bg-green-100 text-green-800';
    }
  };

  const getStatusText = () => {
    const now = new Date();
    const validFrom = new Date(coupon.valid_from);
    const validUntil = new Date(coupon.valid_until);

    if (!coupon.is_active) {
      return 'Inactive';
    } else if (now < validFrom) {
      return 'Scheduled';
    } else if (now > validUntil) {
      return 'Expired';
    } else {
      return 'Active';
    }
  };

  const isExpired = new Date() > new Date(coupon.valid_until);
  const isMaxUsesReached = coupon.usage_limit ? coupon.usage_count >= coupon.usage_limit : false;

  return (
    <div className={`bg-white rounded-xl shadow-sm border-2 hover:shadow-lg transition-all duration-200 ${
      coupon.is_active && !isExpired ? 'border-green-200' : 'border-gray-200'
    }`}>
      {/* Card Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
                <h4 className="text-lg font-bold text-gray-900 font-mono tracking-wide">{coupon.code}</h4>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${getStatusColor()}`}>
                {getStatusText()}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-600">{coupon.description}</p>
            
            {/* Discount Badge */}
            <div className="mt-3">
              <span className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800 text-sm font-bold rounded-lg">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
                {getDiscountDisplay()}
              </span>
            </div>
          </div>
          
          <div className="flex items-center ml-3">
            <div className={`w-3 h-3 rounded-full ${
              coupon.is_active && !isExpired && !isMaxUsesReached ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
          </div>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-6">
        {/* Validity Period */}
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
            <svg className="w-4 h-4 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Validity Period
          </h5>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">From:</span>
              <div className="font-medium text-gray-600">{formatDate(coupon.valid_from)}</div>
            </div>
            <div>
              <span className="text-gray-500">Until:</span>
              <div className="font-medium text-gray-600">{formatDate(coupon.valid_until)}</div>
            </div>
          </div>
        </div>

        {/* Restrictions */}
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
            <svg className="w-4 h-4 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.999-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Restrictions
          </h5>
          <div className="text-sm text-gray-600 space-y-1">
            {coupon.minimum_amount && (
              <div>Minimum order: ${coupon.minimum_amount}</div>
            )}
            {coupon.plans.length > 0 && (
              <div>Applies to: {coupon.plans.length} plan(s)</div>
            )}
          </div>
        </div>

        {/* Usage Statistics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-lg font-semibold text-gray-900">{coupon.usage_count}</div>
            <div className="text-xs text-gray-600 flex items-center justify-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Times Used
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <div className="text-lg font-semibold text-purple-600">
              {coupon.usage_limit ? `${coupon.usage_limit - coupon.usage_count}` : '∞'}
            </div>
            <div className="text-xs text-purple-600 flex items-center justify-center">
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Remaining
            </div>
          </div>
        </div>
      </div>

      {/* Card Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 rounded-b-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1">
            <button
              onClick={() => onEdit(coupon)}
              className="inline-flex items-center p-2 rounded-lg text-[#000ABE] hover:bg-[#000ABE]/10 transition-colors"
              title="Edit Coupon"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onToggleActive(coupon.id)}
              className={`inline-flex items-center p-2 rounded-lg transition-colors ${
                coupon.is_active 
                  ? 'text-red-600 hover:bg-red-50' 
                  : 'text-green-600 hover:bg-green-50'
              }`}
              disabled={isLoading}
              title={coupon.is_active ? 'Deactivate Coupon' : 'Activate Coupon'}
            >
              {coupon.is_active ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M15 14h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </button>
          </div>
          <button
            onClick={() => onDelete(coupon.id)}
            className="inline-flex items-center p-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
            disabled={isLoading}
            title="Delete Coupon"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}