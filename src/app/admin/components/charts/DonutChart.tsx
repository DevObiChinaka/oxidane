'use client';

import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { ChartData } from 'chart.js';
import { donutChartOptions, brandColors } from './ChartConfig';

interface DonutChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  title?: string;
  height?: number;
  showLegend?: boolean;
}

const DonutChart: React.FC<DonutChartProps> = ({ 
  data, 
  title, 
  height = 280, 
  showLegend = true 
}) => {
  // Default colors for data points
  const defaultColors = [
    brandColors.primary,
    brandColors.secondary,
    brandColors.accent,
    brandColors.danger,
    brandColors.primaryLight,
    brandColors.secondaryLight,
  ];

  // Prepare chart data
  const chartData: ChartData<'doughnut'> = {
    labels: data.map(item => item.label),
    datasets: [
      {
        data: data.map(item => item.value),
        backgroundColor: data.map((item, index) => 
          item.color || defaultColors[index % defaultColors.length]
        ),
        borderColor: data.map((item, index) => 
          item.color || defaultColors[index % defaultColors.length]
        ),
        borderWidth: 0,
        hoverBackgroundColor: data.map((item, index) => {
          const color = item.color || defaultColors[index % defaultColors.length];
          return color + 'DD'; // Add transparency for hover
        }),
        hoverBorderColor: brandColors.surface,
        hoverBorderWidth: 3,
      },
    ],
  };

  // Calculate total for center display
  const total = data.reduce((sum, item) => sum + item.value, 0);

  const options = {
    ...donutChartOptions,
    cutout: '70%', // Larger cutout for better center space
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
      ...donutChartOptions.plugins,
      legend: {
        ...donutChartOptions.plugins?.legend,
        display: false, // We'll use custom legend
      },
      tooltip: {
        ...donutChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed;
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="relative w-full overflow-hidden" style={{ height: `${height}px` }}>
      {title && (
        <h3 className="text-sm font-medium text-gray-600 mb-3 text-center">
          {title}
        </h3>
      )}
      
      <div className="relative w-full flex items-center justify-center" style={{ height: showLegend ? `${height - 80}px` : `${height - 20}px` }}>
        <div className="w-full h-full">
          <Doughnut data={chartData} options={options} />
        </div>
        
        {/* Center text showing total - positioned absolutely in the center */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10">
          <div className="text-center">
            <div className="text-xl font-bold text-gray-900 leading-tight">
              {total.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 font-medium">
              Total
            </div>
          </div>
        </div>
      </div>

      {/* Custom legend with percentages */}
      {showLegend && (
        <div className="mt-3 space-y-1 max-h-20 overflow-y-auto">
          {data.map((item, index) => {
            const color = item.color || defaultColors[index % defaultColors.length];
            const percentage = total > 0 ? ((item.value / total) * 100).toFixed(1) : '0.0';
            
            return (
              <div key={item.label} className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-gray-700 font-medium">{item.label}</span>
                </div>
                <div className="text-gray-600">
                  <span className="font-semibold">{item.value}</span>
                  <span className="text-gray-500 ml-1">({percentage}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DonutChart;