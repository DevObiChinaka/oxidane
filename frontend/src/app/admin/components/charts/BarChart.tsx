'use client';

import React from 'react';
import { Bar } from 'react-chartjs-2';
import { ChartData } from 'chart.js';
import { barChartOptions, brandColors, generateGradient } from './ChartConfig';

interface BarChartData {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarChartData[];
  title?: string;
  height?: number;
  horizontal?: boolean;
  showValues?: boolean;
  maxBars?: number;
}

const BarChart: React.FC<BarChartProps> = ({ 
  data, 
  title, 
  height = 300, 
  horizontal = false,
  showValues = true,
  maxBars = 10
}) => {
  // Limit and sort data if needed
  const processedData = data
    .sort((a, b) => b.value - a.value) // Sort by value descending
    .slice(0, maxBars); // Limit number of bars

  // Default colors
  const defaultColors = [
    brandColors.primary,
    brandColors.secondary,
    brandColors.accent,
    brandColors.danger,
    brandColors.primaryLight,
    brandColors.secondaryLight,
    brandColors.accentLight,
    brandColors.dangerLight,
    brandColors.gray,
    brandColors.grayLight,
  ];

  // Prepare chart data
  const chartData: ChartData<'bar'> = {
    labels: processedData.map(item => item.label),
    datasets: [
      {
        label: title || 'Values',
        data: processedData.map(item => item.value),
        backgroundColor: processedData.map((item, index) => {
          const color = item.color || defaultColors[index % defaultColors.length];
          return color + '80'; // Add transparency
        }),
        borderColor: processedData.map((item, index) => 
          item.color || defaultColors[index % defaultColors.length]
        ),
        borderWidth: 2,
        hoverBackgroundColor: processedData.map((item, index) => {
          const color = item.color || defaultColors[index % defaultColors.length];
          return color + 'CC'; // More opaque on hover
        }),
        hoverBorderColor: processedData.map((item, index) => 
          item.color || defaultColors[index % defaultColors.length]
        ),
        hoverBorderWidth: 3,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    ...barChartOptions,
    indexAxis: horizontal ? 'y' as const : 'x' as const,
    plugins: {
      ...barChartOptions.plugins,
      legend: {
        display: false, // Hide legend for bar charts
      },
      tooltip: {
        ...barChartOptions.plugins?.tooltip,
        callbacks: {
          title: (context: any) => {
            return `${context[0].label}`;
          },
          label: (context: any) => {
            const value = context.parsed[horizontal ? 'x' : 'y'];
            return `${title || 'Value'}: ${value.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: !horizontal,
          color: '#F3F4F6',
        },
        ticks: {
          color: brandColors.gray,
          font: {
            size: 10,
            family: 'Inter, system-ui, sans-serif',
          },
          maxRotation: horizontal ? 0 : 0,
          callback: function(value: any, index: number) {
            if (horizontal) {
              return typeof value === 'number' ? value.toLocaleString() : value;
            }
            const label = processedData[index]?.label || '';
            return label.length > 12 ? label.substring(0, 9) + '...' : label;
          },
        },
        ...(horizontal && {
          beginAtZero: true,
        }),
      },
      y: {
        grid: {
          display: horizontal,
          color: '#F3F4F6',
        },
        ticks: {
          color: brandColors.gray,
          font: {
            size: 11,
            family: 'Inter, system-ui, sans-serif',
          },
          callback: function(value: any) {
            if (!horizontal) {
              return typeof value === 'number' ? value.toLocaleString() : value;
            }
            // For horizontal bars, show full labels
            return value;
          },
        },
        ...(!horizontal && {
          beginAtZero: true,
        }),
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
      
      <div className="relative w-full h-full">
        <Bar 
          data={chartData} 
          options={options}
          plugins={[
            // Plugin to show values on bars
            ...(showValues ? [{
              id: 'barValues',
              afterDatasetsDraw: (chart: any) => {
                const ctx = chart.ctx;
                chart.data.datasets.forEach((dataset: any, datasetIndex: number) => {
                  const meta = chart.getDatasetMeta(datasetIndex);
                  meta.data.forEach((bar: any, index: number) => {
                    const value = dataset.data[index];
                    if (value > 0) {
                      ctx.save();
                      ctx.font = '12px Inter, system-ui, sans-serif';
                      ctx.fillStyle = brandColors.gray;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'middle';
                      
                      let x, y;
                      if (horizontal) {
                        x = bar.x + 10;
                        y = bar.y;
                      } else {
                        x = bar.x;
                        y = bar.y - 10;
                      }
                      
                      ctx.fillText(value.toLocaleString(), x, y);
                      ctx.restore();
                    }
                  });
                });
              },
            }] : [])
          ]}
        />
      </div>

      {/* Data summary */}
      <div className="mt-4 flex justify-between text-sm text-gray-600">
        <span>Showing top {Math.min(maxBars, data.length)} items</span>
        <span>
          Total: {processedData.reduce((sum, item) => sum + item.value, 0).toLocaleString()}
        </span>
      </div>
    </div>
  );
};

export default BarChart;