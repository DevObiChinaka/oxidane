'use client';

import React from 'react';
import { Line } from 'react-chartjs-2';
import { ChartData, ChartOptions } from 'chart.js';
import { growthChartOptions, brandColors, generateGradient } from './ChartConfig';

interface GrowthTrendData {
  month: string;
  courses_created: number;
  users_registered: number;
  growth_rate: number;
}

interface GrowthChartProps {
  data: GrowthTrendData[];
  height?: number;
}

const GrowthChart: React.FC<GrowthChartProps> = ({ data, height = 300 }) => {

  // Prepare chart data
  const chartData: ChartData<'line'> = {
    labels: data.map(item => {
      const [year, month] = item.month.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1);
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    }),
    datasets: [
      {
        label: 'Courses Created',
        data: data.map(item => item.courses_created),
        borderColor: brandColors.primary,
        backgroundColor: brandColors.primary + '20',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: brandColors.primary,
        pointBorderColor: brandColors.surface,
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: brandColors.primary,
        pointHoverBorderColor: brandColors.surface,
        pointHoverBorderWidth: 3,
      },
      {
        label: 'Users Registered',
        data: data.map(item => item.users_registered),
        borderColor: brandColors.secondary,
        backgroundColor: brandColors.secondary + '20',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: brandColors.secondary,
        pointBorderColor: brandColors.surface,
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointHoverBackgroundColor: brandColors.secondary,
        pointHoverBorderColor: brandColors.surface,
        pointHoverBorderWidth: 3,
      },
      {
        label: 'Growth Rate (%)',
        data: data.map(item => item.growth_rate),
        borderColor: brandColors.accent,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        pointBackgroundColor: brandColors.accent,
        pointBorderColor: brandColors.surface,
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: brandColors.accent,
        pointHoverBorderColor: brandColors.surface,
        pointHoverBorderWidth: 3,
        yAxisID: 'y1',
      },
    ],
  };

  // Custom options with dual y-axis
  const options: ChartOptions<'line'> = {
    ...growthChartOptions,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    scales: {
      x: {
        grid: {
          display: true,
          color: '#F3F4F6',
        },
        ticks: {
          color: brandColors.gray,
          font: {
            size: 11,
            family: 'Inter, system-ui, sans-serif',
          },
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        grid: {
          display: true,
          color: '#F3F4F6',
        },
        ticks: {
          color: brandColors.gray,
          font: {
            size: 11,
            family: 'Inter, system-ui, sans-serif',
          },
        },
        title: {
          display: true,
          text: 'Count',
          color: brandColors.gray,
          font: {
            size: 12,
            weight: 500,
            family: 'Inter, system-ui, sans-serif',
          },
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          color: brandColors.accent,
          font: {
            size: 11,
            family: 'Inter, system-ui, sans-serif',
          },
          callback: function(value) {
            return typeof value === 'number' ? value.toFixed(1) + '%' : value;
          },
        },
        title: {
          display: true,
          text: 'Growth Rate (%)',
          color: brandColors.accent,
          font: {
            size: 12,
            weight: 500,
            family: 'Inter, system-ui, sans-serif',
          },
        },
      },
    },
    plugins: {
      tooltip: {
        backgroundColor: brandColors.surface,
        titleColor: brandColors.gray,
        bodyColor: brandColors.gray,
        borderColor: brandColors.grayLight,
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        padding: 12,
        callbacks: {
          title: (context) => {
            return `Growth Trends - ${context[0].label}`;
          },
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            if (label.includes('Growth Rate')) {
              return `${label}: ${value.toFixed(1)}%`;
            }
            return `${label}: ${value}`;
          },
        },
      },
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            family: 'Inter, system-ui, sans-serif',
          },
          color: brandColors.gray,
        },
      },
    },
  };

  return (
    <div className="relative w-full overflow-hidden" style={{ height: `${height}px` }}>
      <Line
        data={chartData}
        options={options}
        plugins={[
          {
            id: 'customCanvasBackgroundColor',
            beforeDraw: (chart) => {
              const ctx = chart.canvas.getContext('2d');
              if (ctx) {
                ctx.save();
                ctx.globalCompositeOperation = 'destination-over';
                ctx.fillStyle = brandColors.surface;
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
              }
            },
          },
        ]}
      />
    </div>
  );
};

export default GrowthChart;