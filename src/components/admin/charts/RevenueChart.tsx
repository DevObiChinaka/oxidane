'use client';

import React from 'react';
import { SubscriptionAnalytics } from '@/types/subscription';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface RevenueChartProps {
  analytics: SubscriptionAnalytics;
  period: 'daily' | 'weekly' | 'monthly';
}

export default function RevenueChart({ analytics, period }: RevenueChartProps) {
  // Generate mock time series data based on current analytics
  const generateTimeSeriesData = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const baseRevenue = analytics.total_revenue || 0;
    const baseSubscriptions = analytics.total_subscriptions || 0;
    
    return {
      labels: months,
      revenue: months.map((_, index) => 
        Math.floor(baseRevenue * (0.6 + (index * 0.1) + Math.random() * 0.3))
      ),
      subscriptions: months.map((_, index) => 
        Math.floor(baseSubscriptions * (0.5 + (index * 0.15) + Math.random() * 0.2))
      ),
    };
  };

  const data = generateTimeSeriesData();
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Revenue ($)',
        data: data.revenue,
        borderColor: '#000ABE',
        backgroundColor: 'rgba(0, 10, 190, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#000ABE',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
      {
        label: 'New Subscriptions',
        data: data.subscriptions,
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#10B981',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        yAxisID: 'y1',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: 'normal' as const,
          },
        },
      },
      title: {
        display: true,
        text: `Revenue & Subscriptions Trend (${period.charAt(0).toUpperCase() + period.slice(1)})`,
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
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            if (context.datasetIndex === 0) {
              return `Revenue: $${context.parsed.y.toLocaleString()}`;
            } else {
              return `New Subscriptions: ${context.parsed.y}`;
            }
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
        },
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        grid: {
          color: 'rgba(229, 231, 235, 0.5)',
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return '$' + Number(value).toLocaleString();
          },
        },
        title: {
          display: true,
          text: 'Revenue ($)',
          color: '#000ABE',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
        },
        title: {
          display: true,
          text: 'Subscriptions',
          color: '#10B981',
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
      <Line data={chartData} options={options} />
    </div>
  );
}