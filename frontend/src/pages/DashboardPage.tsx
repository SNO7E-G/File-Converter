import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../utils/api';
import { Conversion, ConversionsResponse, StatisticsData } from '../utils/api';
import { AxiosResponse } from 'axios';
import {
  ArrowUpTrayIcon,
  DocumentDuplicateIcon,
  ClockIcon,
  ChartBarIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

// Define response interface types for local use
interface DashboardStats {
  today: number;
  total: number;
  remaining: number;
  mostUsedFormat: string;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [recentConversions, setRecentConversions] = useState<Conversion[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    today: 0,
    total: 0,
    remaining: 0,
    mostUsedFormat: '-',
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch recent conversions - properly handle the response types
        const conversionsData = await api.get<ConversionsResponse>('/api/conversions', {
          params: { page: 1, limit: 5 },
        });
        
        // Now conversionsData is directly the response data object
        if (conversionsData && conversionsData.conversions) {
          setRecentConversions(conversionsData.conversions);
        }
        
        // Fetch statistics - statsData is directly the response data
        const statsData = await api.get<StatisticsData>('/api/statistics');
        
        // Properly access the statistics data fields
        if (statsData) {
          setStats({
            today: statsData.conversions_today || 0,
            total: statsData.total_conversions || 0,
            remaining: user?.tier === 'premium' 
              ? 100 - (statsData.conversions_today || 0)
              : 5 - (statsData.conversions_today || 0),
            mostUsedFormat: statsData.most_used_format || '-',
          });
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);
  
  // Quick action cards
  const quickActions = [
    {
      name: 'Convert File',
      description: 'Convert a single file to another format',
      icon: ArrowUpTrayIcon,
      to: '/app/convert',
      color: 'bg-primary-500',
    },
    {
      name: 'Batch Convert',
      description: 'Convert multiple files at once',
      icon: DocumentDuplicateIcon,
      to: '/app/batch',
      color: 'bg-secondary-500',
    },
    {
      name: 'Schedule Conversion',
      description: 'Schedule conversions for later',
      icon: ClockIcon,
      to: '/app/schedule',
      color: 'bg-green-500',
    },
    {
      name: 'View Templates',
      description: 'Download format templates',
      icon: DocumentTextIcon,
      to: '/app/templates',
      color: 'bg-yellow-500',
    },
    {
      name: 'View Statistics',
      description: 'See detailed usage statistics',
      icon: ChartBarIcon,
      to: '/app/statistics',
      color: 'bg-purple-500',
    },
  ];
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Welcome section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.username || 'User'}!
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          {user?.tier === 'premium' 
            ? 'You have premium access to all features.' 
            : 'You are on the free plan. Consider upgrading for more features.'}
        </p>
      </div>
      
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-500 dark:text-gray-400">Today's Conversions</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{stats.today}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-500 dark:text-gray-400">Total Conversions</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{stats.total}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-500 dark:text-gray-400">Remaining Today</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{stats.remaining}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-500 dark:text-gray-400">Most Used Format</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{stats.mostUsedFormat}</p>
        </div>
      </div>
      
      {/* Quick actions */}
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-6">
        {quickActions.map((action) => (
          <Link 
            key={action.name}
            to={action.to}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
          >
            <div className={`${action.color} h-2`}></div>
            <div className="p-6">
              <div className="flex items-center">
                <div className={`p-2 rounded-lg ${action.color} bg-opacity-10 dark:bg-opacity-20`}>
                  <action.icon className={`h-6 w-6 ${action.color} text-white opacity-80`} />
                </div>
                <h3 className="ml-3 font-medium text-gray-900 dark:text-white">{action.name}</h3>
              </div>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{action.description}</p>
            </div>
          </Link>
        ))}
      </div>
      
      {/* Recent conversions */}
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Recent Conversions</h2>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : recentConversions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Source</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Target</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {recentConversions.map((conversion) => (
                  <tr key={conversion.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {conversion.source_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {conversion.target_format.toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${conversion.status === 'completed' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                          : conversion.status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        }`}
                      >
                        {conversion.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {formatDate(conversion.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link 
                        to={`/app/history/${conversion.id}`}
                        className="text-primary-600 dark:text-primary-400 hover:text-primary-900 dark:hover:text-primary-300"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No recent conversions found. Start by converting a file!
          </div>
        )}
        
        <div className="bg-gray-50 dark:bg-gray-900 px-6 py-4">
          <Link 
            to="/app/history"
            className="text-primary-600 dark:text-primary-400 font-medium hover:text-primary-900 dark:hover:text-primary-300"
          >
            View all conversions →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; 