'use client';

import React from 'react';
import { SubscriptionAnalytics } from '@/types/subscription';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface PaymentStatusChartProps {
  analytics: SubscriptionAnalytics;
}

export default function PaymentStatusChart({ analytics }: PaymentStatusChartProps) {
  // Calculate refunded count from amount (rough estimation)
  const refundedCount = Math.floor((analytics.refunded_amount || 0) / 100); // Assuming avg $100 per refund
  
  const data = {
    verified: analytics.verified_payments || 0,
    pending: analytics.pending_payments || 0,
    failed: analytics.failed_payments || 0,
    refunded: refundedCount,
  };
  const chartData = {
    labels: ['Verified', 'Pending', 'Failed', 'Refunded'],
    datasets: [
      {
        label: 'Payments',
        data: [data.verified || 0, data.pending || 0, data.failed || 0, data.refunded || 0],
        backgroundColor: [
          '#10B981', // Verified - Green
          '#F59E0B', // Pending - Amber
          '#EF4444', // Failed - Red
          '#6B7280', // Refunded - Gray
        ],
        borderColor: [
          '#059669',
          '#D97706', 
          '#DC2626',
          '#4B5563',
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Payment Status Breakdown',
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
            const total = chartData.datasets[0].data.reduce((a: number, b: number) => a + b, 0);
            const percentage = total > 0 ? ((context.parsed.y / total) * 100).toFixed(1) : '0.0';
            return `${context.label}: ${context.parsed.y} (${percentage}%)`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(229, 231, 235, 0.5)',
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          precision: 0,
        },
        title: {
          display: true,
          text: 'Number of Payments',
          color: '#374151',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
      },
    },
  };

  return (
    <div className="h-80">
      <Bar data={chartData} options={options} />
    </div>
  );
}