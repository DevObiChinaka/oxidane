'use client';

import { useState, useEffect } from 'react';
// import { useRevenueData } from '../../hooks/useAdminAPI'; // TODO: Implement when backend is ready

interface RevenueMetrics {
  totalRevenue: number;
  monthlyGrowth: number;
  activeSubscriptions: number;
  averageRevenuePerUser: number;
  monthlyRecurringRevenue: number;
  couponDiscountImpact: number;
  newStudentRevenue: number;
  retentionRevenue: number;
}

interface RevenueBreakdown {
  subscriptions: number;
  courses: number;
  mentorship: number;
  certifications: number;
}

interface DateRange {
  startDate: string;
  endDate: string;
  label: string;
}

const dateRanges: DateRange[] = [
  { startDate: new Date().toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0], label: 'Today' },
  { startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0], label: 'Last 7 Days' },
  { startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0], label: 'Last 30 Days' },
  { startDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], endDate: new Date().toISOString().split('T')[0], label: 'Last 90 Days' },
];

export default function RevenueReports() {
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>(dateRanges[2]); // Default to last 30 days
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Mock data - will be replaced with real API calls
  const revenueMetrics: RevenueMetrics = {
    totalRevenue: 45280.50,
    monthlyGrowth: 12.5,
    activeSubscriptions: 1247,
    averageRevenuePerUser: 36.31,
    monthlyRecurringRevenue: 38420.00,
    couponDiscountImpact: -2340.25,
    newStudentRevenue: 18750.00,
    retentionRevenue: 26530.50,
  };

  const revenueBreakdown: RevenueBreakdown = {
    subscriptions: 38420.00,
    courses: 4850.25,
    mentorship: 1650.00,
    certifications: 360.25,
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1)}%`;
  };

  const handleCustomDateRange = () => {
    if (customStartDate && customEndDate) {
      setSelectedDateRange({
        startDate: customStartDate,
        endDate: customEndDate,
        label: 'Custom Range'
      });
      setShowCustomDatePicker(false);
    }
  };

  const exportToPDF = async () => {
    setIsExporting(true);
    try {
      // TODO: Implement PDF export functionality
      console.log('Exporting to PDF...');
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('PDF export completed!');
    } catch (error) {
      console.error('PDF export failed:', error);
      alert('PDF export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const exportToExcel = async () => {
    setIsExporting(true);
    try {
      // TODO: Implement Excel export functionality
      console.log('Exporting to Excel...');
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('Excel export completed!');
    } catch (error) {
      console.error('Excel export failed:', error);
      alert('Excel export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Revenue Reports & Analytics</h1>
            <p className="mt-2 text-gray-600">
              Comprehensive financial insights and performance metrics
            </p>
          </div>
          
          {/* Export Controls */}
          <div className="flex space-x-3">
            <button
              onClick={exportToPDF}
              disabled={isExporting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {isExporting ? 'Exporting...' : 'Export PDF'}
            </button>
            
            <button
              onClick={exportToExcel}
              disabled={isExporting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {isExporting ? 'Exporting...' : 'Export Excel'}
            </button>
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Date Range:</span>
            {dateRanges.map((range) => (
              <button
                key={range.label}
                onClick={() => setSelectedDateRange(range)}
                className={`px-3 py-1 text-sm rounded-md border ${
                  selectedDateRange.label === range.label
                    ? 'bg-[#000ABE] text-white border-[#000ABE]'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {range.label}
              </button>
            ))}
            <button
              onClick={() => setShowCustomDatePicker(!showCustomDatePicker)}
              className="px-3 py-1 text-sm rounded-md border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            >
              Custom
            </button>
          </div>

          <div className="text-sm text-gray-500">
            Last updated: {new Date().toLocaleString()}
          </div>
        </div>

        {/* Custom Date Picker */}
        {showCustomDatePicker && (
          <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
            <div className="flex items-center space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-[#000ABE] focus:border-[#000ABE]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-[#000ABE] focus:border-[#000ABE]"
                />
              </div>
              <div className="pt-6">
                <button
                  onClick={handleCustomDateRange}
                  className="px-4 py-2 bg-[#000ABE] text-white text-sm rounded-md hover:bg-[#000ABE]/90"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Key Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Revenue */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Revenue</p>
              <p className="text-2xl font-semibold text-gray-900">{formatCurrency(revenueMetrics.totalRevenue)}</p>
              <p className="text-sm text-green-600">{formatPercentage(revenueMetrics.monthlyGrowth)} vs last period</p>
            </div>
          </div>
        </div>

        {/* Active Subscriptions */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Subscriptions</p>
              <p className="text-2xl font-semibold text-gray-900">{revenueMetrics.activeSubscriptions.toLocaleString()}</p>
              <p className="text-sm text-gray-600">Paying students</p>
            </div>
          </div>
        </div>

        {/* Monthly Recurring Revenue */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Monthly Recurring Revenue</p>
              <p className="text-2xl font-semibold text-gray-900">{formatCurrency(revenueMetrics.monthlyRecurringRevenue)}</p>
              <p className="text-sm text-gray-600">Subscription revenue</p>
            </div>
          </div>
        </div>

        {/* Average Revenue Per User */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Average Revenue Per User</p>
              <p className="text-2xl font-semibold text-gray-900">{formatCurrency(revenueMetrics.averageRevenuePerUser)}</p>
              <p className="text-sm text-gray-600">Per active student</p>
            </div>
          </div>
        </div>
      </div>

      {/* Revenue Breakdown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Revenue Streams */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Streams</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Subscription Revenue</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">{formatCurrency(revenueBreakdown.subscriptions)}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: `${(revenueBreakdown.subscriptions / revenueMetrics.totalRevenue) * 100}%`}}></div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Course Sales</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">{formatCurrency(revenueBreakdown.courses)}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: `${(revenueBreakdown.courses / revenueMetrics.totalRevenue) * 100}%`}}></div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Mentorship Programs</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">{formatCurrency(revenueBreakdown.mentorship)}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                  <div className="bg-purple-600 h-2 rounded-full" style={{width: `${(revenueBreakdown.mentorship / revenueMetrics.totalRevenue) * 100}%`}}></div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Certifications</span>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">{formatCurrency(revenueBreakdown.certifications)}</span>
                <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                  <div className="bg-orange-600 h-2 rounded-full" style={{width: `${(revenueBreakdown.certifications / revenueMetrics.totalRevenue) * 100}%`}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Student Revenue Analytics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Revenue Analytics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(revenueMetrics.newStudentRevenue)}</p>
              <p className="text-sm text-gray-600 mt-1">New Student Revenue</p>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{formatCurrency(revenueMetrics.retentionRevenue)}</p>
              <p className="text-sm text-gray-600 mt-1">Retention Revenue</p>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg col-span-2">
              <p className="text-2xl font-bold text-red-600">{formatCurrency(Math.abs(revenueMetrics.couponDiscountImpact))}</p>
              <p className="text-sm text-gray-600 mt-1">Revenue Impact from Coupons</p>
            </div>
          </div>
        </div>
      </div>

      {/* Coming Soon - Advanced Analytics */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Advanced Analytics Coming Soon</h3>
          <p className="mt-1 text-sm text-gray-500">
            Revenue trends, forecasting, cohort analysis, and more detailed insights will be available soon.
          </p>
        </div>
      </div>
    </div>
  );
}