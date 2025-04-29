import React, { useState, useEffect } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import api from '../utils/api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface StatisticsData {
  conversions_by_date: Record<string, number>;
  conversions_by_format: Record<string, number>;
  source_formats: Record<string, number>;
  target_formats: Record<string, number>;
  conversions_by_status: Record<string, number>;
  peak_usage_hours: Record<string, number>;
}

const StatisticsPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<StatisticsData | null>(null);

  const timeRangeOptions = [
    { value: 'week', label: 'Last 7 Days' },
    { value: 'month', label: 'Last 30 Days' },
    { value: 'year', label: 'Last 12 Months' },
  ];

  useEffect(() => {
    fetchStatistics();
  }, [timeRange]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/api/statistics?range=${timeRange}`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      setError('Failed to load statistics data');
    } finally {
      setLoading(false);
    }
  };

  // Process data for the line chart (conversions over time)
  const conversionsOverTimeData = () => {
    if (!stats?.conversions_by_date) return null;
    
    const dates = Object.keys(stats.conversions_by_date);
    const counts = Object.values(stats.conversions_by_date);
    
    return {
      labels: dates,
      datasets: [
        {
          label: 'Conversions',
          data: counts,
          borderColor: 'rgb(14, 165, 233)',
          backgroundColor: 'rgba(14, 165, 233, 0.1)',
          fill: true,
          tension: 0.3,
        },
      ],
    };
  };

  // Process data for the bar chart (source formats)
  const sourceFormatsData = () => {
    if (!stats?.source_formats) return null;
    
    const formats = Object.keys(stats.source_formats);
    const counts = Object.values(stats.source_formats);
    
    return {
      labels: formats.map(f => f.toUpperCase()),
      datasets: [
        {
          label: 'Source Formats',
          data: counts,
          backgroundColor: [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
          ],
          borderColor: [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
            'rgba(199, 199, 199, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  // Process data for the pie chart (target formats)
  const targetFormatsData = () => {
    if (!stats?.target_formats) return null;
    
    const formats = Object.keys(stats.target_formats);
    const counts = Object.values(stats.target_formats);
    
    return {
      labels: formats.map(f => f.toUpperCase()),
      datasets: [
        {
          label: 'Target Formats',
          data: counts,
          backgroundColor: [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
          ],
          borderColor: [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
            'rgba(199, 199, 199, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  // Process data for the bar chart (conversion status)
  const conversionStatusData = () => {
    if (!stats?.conversions_by_status) return null;
    
    const statuses = Object.keys(stats.conversions_by_status);
    const counts = Object.values(stats.conversions_by_status);
    
    const statusColors: Record<string, string> = {
      completed: 'rgba(34, 197, 94, 0.7)',
      failed: 'rgba(239, 68, 68, 0.7)',
      pending: 'rgba(245, 158, 11, 0.7)',
      processing: 'rgba(59, 130, 246, 0.7)',
      scheduled: 'rgba(139, 92, 246, 0.7)',
    };
    
    const statusBorderColors: Record<string, string> = {
      completed: 'rgb(22, 163, 74)',
      failed: 'rgb(220, 38, 38)',
      pending: 'rgb(217, 119, 6)',
      processing: 'rgb(37, 99, 235)',
      scheduled: 'rgb(124, 58, 237)',
    };
    
    return {
      labels: statuses.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
      datasets: [
        {
          label: 'Conversion Status',
          data: counts,
          backgroundColor: statuses.map(status => statusColors[status] || 'rgba(156, 163, 175, 0.7)'),
          borderColor: statuses.map(status => statusBorderColors[status] || 'rgb(107, 114, 128)'),
          borderWidth: 1,
        },
      ],
    };
  };

  // Process data for the line chart (peak usage hours)
  const peakUsageData = () => {
    if (!stats?.peak_usage_hours) return null;
    
    const hours = Object.keys(stats.peak_usage_hours).sort((a, b) => parseInt(a) - parseInt(b));
    const counts = hours.map(hour => stats.peak_usage_hours[hour]);
    
    // Format hours as 12-hour format
    const formattedHours = hours.map(hour => {
      const hourNum = parseInt(hour);
      if (hourNum === 0) return '12 AM';
      if (hourNum === 12) return '12 PM';
      return hourNum < 12 ? `${hourNum} AM` : `${hourNum - 12} PM`;
    });
    
    return {
      labels: formattedHours,
      datasets: [
        {
          label: 'Conversions by Hour',
          data: counts,
          borderColor: 'rgb(139, 92, 246)',
          backgroundColor: 'rgba(139, 92, 246, 0.5)',
          borderWidth: 2,
          pointBackgroundColor: 'rgb(139, 92, 246)',
          tension: 0.1,
        },
      ],
    };
  };

  // Chart options
  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Conversions Over Time',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Conversions',
        },
      },
    },
  };

  const barChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Source Formats',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Conversions',
        },
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Target Formats',
      },
    },
  };

  const statusChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Conversion Status',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Conversions',
        },
      },
    },
  };

  const peakUsageOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Peak Usage Hours',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Conversions',
        },
      },
    },
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 md:mb-0">
          Conversion Statistics
        </h1>
        
        <div className="inline-flex rounded-md shadow-sm">
          {timeRangeOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setTimeRange(option.value as 'week' | 'month' | 'year')}
              className={`px-4 py-2 text-sm font-medium ${
                timeRange === option.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              } ${
                option.value === 'week'
                  ? 'rounded-l-md'
                  : option.value === 'year'
                  ? 'rounded-r-md'
                  : ''
              } border border-gray-300 dark:border-gray-700`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      
      {loading ? (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversions over time */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            {conversionsOverTimeData() && (
              <Line data={conversionsOverTimeData()!} options={lineChartOptions} />
            )}
          </div>
          
          {/* Source formats */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            {sourceFormatsData() && (
              <Bar data={sourceFormatsData()!} options={barChartOptions} />
            )}
          </div>
          
          {/* Target formats */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            {targetFormatsData() && (
              <Pie data={targetFormatsData()!} options={pieChartOptions} />
            )}
          </div>
          
          {/* Conversion status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
            {conversionStatusData() && (
              <Bar data={conversionStatusData()!} options={statusChartOptions} />
            )}
          </div>
          
          {/* Peak usage hours */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 lg:col-span-2">
            {peakUsageData() && (
              <Line data={peakUsageData()!} options={peakUsageOptions} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StatisticsPage; 