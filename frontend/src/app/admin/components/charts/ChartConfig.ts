// Chart.js configuration and utilities
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler,
  ChartOptions,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler
);

// Brand colors for consistent theming
export const brandColors = {
  primary: '#3B82F6',      // Blue-500
  primaryLight: '#60A5FA', // Blue-400
  secondary: '#10B981',    // Emerald-500
  secondaryLight: '#34D399', // Emerald-400
  accent: '#F59E0B',       // Amber-500
  accentLight: '#FBBF24',  // Amber-400
  danger: '#EF4444',       // Red-500
  dangerLight: '#F87171',  // Red-400
  gray: '#6B7280',         // Gray-500
  grayLight: '#9CA3AF',    // Gray-400
  background: '#F9FAFB',   // Gray-50
  surface: '#FFFFFF',      // White
};

// Common chart options
export const defaultChartOptions: Partial<ChartOptions> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index',
  },
  plugins: {
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
    tooltip: {
      backgroundColor: brandColors.surface,
      titleColor: brandColors.gray,
      bodyColor: brandColors.gray,
      borderColor: brandColors.grayLight,
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
      padding: 12,
      titleFont: {
        size: 14,
        weight: 600,
        family: 'Inter, system-ui, sans-serif',
      },
      bodyFont: {
        size: 13,
        family: 'Inter, system-ui, sans-serif',
      },
    },
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
  },
};

// Growth chart specific options
export const growthChartOptions: ChartOptions<'line'> = {
  ...defaultChartOptions,
  elements: {
    line: {
      tension: 0.3,
      borderWidth: 3,
    },
    point: {
      radius: 6,
      hoverRadius: 8,
      borderWidth: 2,
    },
  },
  scales: {
    ...defaultChartOptions.scales,
    y: {
      ...defaultChartOptions.scales?.y,
      beginAtZero: true,
      ticks: {
        color: brandColors.gray,
        font: {
          size: 11,
          family: 'Inter, system-ui, sans-serif',
        },
        callback: function(value) {
          return typeof value === 'number' ? Math.round(value).toString() : value;
        },
      },
    },
  },
  plugins: {
    ...defaultChartOptions.plugins,
    tooltip: {
      ...defaultChartOptions.plugins?.tooltip,
      callbacks: {
        title: (context) => {
          return `Month: ${context[0].label}`;
        },
        label: (context) => {
          const label = context.dataset.label || '';
          const value = context.parsed.y;
          return `${label}: ${value}`;
        },
      },
    },
  },
} as ChartOptions<'line'>;

// Donut chart options
export const donutChartOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '60%',
  plugins: {
    legend: {
      display: true,
      position: 'bottom',
      labels: {
        usePointStyle: true,
        padding: 15,
        font: {
          size: 12,
          family: 'Inter, system-ui, sans-serif',
        },
        color: brandColors.gray,
      },
    },
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
        label: (context) => {
          const label = context.label || '';
          const value = context.parsed;
          const total = context.dataset.data.reduce((a, b) => a + b, 0);
          const percentage = ((value / total) * 100).toFixed(1);
          return `${label}: ${value} (${percentage}%)`;
        },
      },
    },
  },
} as ChartOptions<'doughnut'>;

// Bar chart options
export const barChartOptions: ChartOptions<'bar'> = {
  ...defaultChartOptions,
  scales: {
    ...defaultChartOptions.scales,
    y: {
      ...defaultChartOptions.scales?.y,
      beginAtZero: true,
      ticks: {
        color: brandColors.gray,
        font: {
          size: 11,
          family: 'Inter, system-ui, sans-serif',
        },
      },
    },
  },
  plugins: {
    ...defaultChartOptions.plugins,
    tooltip: {
      ...defaultChartOptions.plugins?.tooltip,
      callbacks: {
        label: (context) => {
          const label = context.dataset.label || '';
          const value = context.parsed.y;
          return `${label}: ${value}`;
        },
      },
    },
  },
} as ChartOptions<'bar'>;

// Utility functions
export const generateGradient = (ctx: CanvasRenderingContext2D, colorStart: string, colorEnd: string) => {
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, colorStart);
  gradient.addColorStop(1, colorEnd);
  return gradient;
};

export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};