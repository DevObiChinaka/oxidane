'use client';

import React from 'react';
import { SubscriptionAnalytics } from '@/types/subscription';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PlanDistributionChartProps {
  analytics: SubscriptionAnalytics;
}

export default function PlanDistributionChart({ analytics }: PlanDistributionChartProps) {
  // Use the plan_type_breakdown from analytics
  const data = analytics.plan_type_breakdown || {};
  const planColors = {
    weekly: '#F59E0B',
    monthly: '#000ABE', 
    vip: '#7C3AED',
    premium: '#059669',
    yearly: '#DC2626',
    lifetime: '#6366F1',
  };

  const labels = Object.keys(data);
  const counts = labels.map(plan => data[plan]?.count || 0);
  const revenues = labels.map(plan => data[plan]?.revenue || 0);

  const chartData = {
    labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
    datasets: [
      {
        label: 'Subscriptions',
        data: counts,
        backgroundColor: labels.map(plan => planColors[plan as keyof typeof planColors] || '#6B7280'),
        borderColor: '#ffffff',
        borderWidth: 3,
        hoverBorderWidth: 4,
        hoverOffset: 8,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: 'normal' as const,
          },
          generateLabels: function(chart: any) {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label: string, i: number) => {
                const count = counts[i];
                const revenue = revenues[i];
                return {
                  text: `${label}: ${count} ($${revenue.toLocaleString()})`,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  strokeStyle: data.datasets[0].borderColor,
                  lineWidth: data.datasets[0].borderWidth,
                  pointStyle: 'circle',
                  index: i,
                };
              });
            }
            return [];
          },
        },
      },
      title: {
        display: true,
        text: 'Subscription Plan Distribution',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#374151',
        padding: {
          bottom: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#374151',
        bodyColor: '#374151',
        borderColor: '#E5E7EB',
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const count = context.parsed;
            const revenue = revenues[context.dataIndex];
            const total = counts.reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : '0.0';
            return [
              `${label}: ${count} subscriptions (${percentage}%)`,
              `Revenue: $${revenue.toLocaleString()}`
            ];
          },
        },
      },
    },
    cutout: '50%',
  };

  const totalSubscriptions = counts.reduce((a, b) => a + b, 0);
  const totalRevenue = revenues.reduce((a, b) => a + b, 0);

  return (
    <div className="relative">
      <div className="h-80">
        <Doughnut data={chartData} options={options} />
      </div>
      
      {/* Center Stats */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            {totalSubscriptions.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Plans</div>
          <div className="text-lg font-semibold text-[#000ABE] mt-1">
            ${totalRevenue.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}