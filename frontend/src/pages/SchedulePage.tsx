import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../utils/api';
import { SupportedFormats, Conversion } from '../utils/api';
import FileDropzone from '../components/FileDropzone';
import {
  CalendarDaysIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

interface ScheduledConversion extends Conversion {
  scheduled_time_friendly?: string;
}

const SchedulePage: React.FC = () => {
  const { user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [targetFormat, setTargetFormat] = useState<string>('');
  const [scheduleDate, setScheduleDate] = useState<string>('');
  const [scheduleTime, setScheduleTime] = useState<string>('');
  const [availableFormats, setAvailableFormats] = useState<string[]>([]);
  const [supportedFormats, setSupportedFormats] = useState<SupportedFormats | null>(null);
  const [scheduledConversions, setScheduledConversions] = useState<ScheduledConversion[]>([]);
  const [isScheduling, setIsScheduling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Set minimum date to today and minimum time to current time if today
  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  const currentHour = now.getHours().toString().padStart(2, '0');
  const currentMinute = now.getMinutes().toString().padStart(2, '0');
  const currentTime = `${currentHour}:${currentMinute}`;

  // Fetch supported formats and scheduled conversions on mount
  useEffect(() => {
    fetchSupportedFormats();
    fetchScheduledConversions();
  }, []);

  // Fetch supported formats from API
  const fetchSupportedFormats = async () => {
    try {
      const response = await api.get('/api/formats');
      setSupportedFormats(response.data.formats);
    } catch (err) {
      console.error('Error fetching supported formats:', err);
      setError('Failed to load supported formats');
    }
  };

  // Fetch scheduled conversions from API
  const fetchScheduledConversions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/conversions', {
        params: {
          status: 'scheduled',
          limit: 100,
        },
      });
      
      // Add friendly date format
      const conversions: ScheduledConversion[] = response.data.conversions.map((conv: Conversion) => {
        let friendly = 'Unknown';
        if (conv.scheduled_at) {
          const date = new Date(conv.scheduled_at);
          friendly = date.toLocaleString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          });
        }
        return {
          ...conv,
          scheduled_time_friendly: friendly,
        };
      });
      
      setScheduledConversions(conversions);
    } catch (err) {
      console.error('Error fetching scheduled conversions:', err);
      setError('Failed to load scheduled conversions');
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection and update available target formats
  const handleFileSelect = (files: File[]) => {
    setFile(files[0] || null);
    setTargetFormat('');
    
    if (files[0] && supportedFormats) {
      const sourceFormat = getSourceFormat(files[0]);
      if (sourceFormat && supportedFormats[sourceFormat]) {
        setAvailableFormats(supportedFormats[sourceFormat]);
        if (supportedFormats[sourceFormat].length > 0) {
          setTargetFormat(supportedFormats[sourceFormat][0]);
        }
      } else {
        setAvailableFormats([]);
      }
    } else {
      setAvailableFormats([]);
    }
  };

  // Get source format from file extension
  const getSourceFormat = (file: File): string => {
    const extension = file.name.split('.').pop()?.toLowerCase() || '';
    
    // Map extension to format
    const formatMap: Record<string, string> = {
      'csv': 'csv',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
      'xlsx': 'excel',
      'xls': 'excel',
      'pdf': 'pdf',
      'docx': 'docx',
    };
    
    return formatMap[extension] || '';
  };

  // Validate scheduled date and time
  const validateSchedule = (): boolean => {
    const scheduleDateTime = new Date(`${scheduleDate}T${scheduleTime}`);
    const currentDateTime = new Date();
    
    if (scheduleDateTime <= currentDateTime) {
      setError('Scheduled time must be in the future');
      return false;
    }
    
    return true;
  };

  // Handle schedule conversion
  const handleScheduleConversion = async () => {
    if (!file || !targetFormat || !scheduleDate || !scheduleTime) {
      setError('Please fill in all fields');
      return;
    }
    
    if (!validateSchedule()) {
      return;
    }
    
    setError(null);
    setSuccess(null);
    setIsScheduling(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const scheduledDateTime = new Date(`${scheduleDate}T${scheduleTime}`).toISOString();
      
      formData.append('data', JSON.stringify({
        target_format: targetFormat,
        scheduled_time: scheduledDateTime,
      }));
      
      const response = await api.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setSuccess('Conversion scheduled successfully');
      setFile(null);
      setTargetFormat('');
      setScheduleDate('');
      setScheduleTime('');
      
      // Refresh scheduled conversions
      fetchScheduledConversions();
    } catch (err: any) {
      console.error('Error scheduling conversion:', err);
      setError(err.response?.data?.error || 'Failed to schedule conversion');
    } finally {
      setIsScheduling(false);
    }
  };

  // Handle delete scheduled conversion
  const handleDeleteScheduled = async (id: number) => {
    try {
      setDeleting(id);
      await api.delete(`/api/conversions/${id}`);
      
      // Remove from list
      setScheduledConversions(prev => prev.filter(conv => conv.id !== id));
      
      setSuccess('Scheduled conversion deleted');
    } catch (err) {
      console.error('Error deleting scheduled conversion:', err);
      setError('Failed to delete scheduled conversion');
    } finally {
      setDeleting(null);
    }
  };

  // Close alerts after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">Schedule Conversions</h1>
          <p className="text-gray-600 dark:text-gray-300 mb-4 lg:mb-0">
            Upload a file and schedule its conversion for a future time.
          </p>
        </div>
        
        {user?.tier !== 'premium' && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-3 max-w-lg">
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              <strong>Note:</strong> Scheduling conversions is a premium feature. 
              {user ? ' Please upgrade your account to unlock it.' : ' Please sign in with a premium account to use this feature.'}
            </p>
          </div>
        )}
      </div>
      
      {/* Success and error alerts */}
      {success && (
        <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4 relative">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-500 dark:text-green-400 mr-2" />
            <p className="text-sm text-green-700 dark:text-green-300">{success}</p>
          </div>
          <button 
            className="absolute top-4 right-4 text-green-500 dark:text-green-400"
            onClick={() => setSuccess(null)}
          >
            <XCircleIcon className="h-5 w-5" />
          </button>
        </div>
      )}
      
      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 relative">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-500 dark:text-red-400 mr-2" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
          <button 
            className="absolute top-4 right-4 text-red-500 dark:text-red-400"
            onClick={() => setError(null)}
          >
            <XCircleIcon className="h-5 w-5" />
          </button>
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Scheduling form */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <CalendarDaysIcon className="h-5 w-5 mr-2 text-primary-500" />
                Schedule a New Conversion
              </h2>
              
              <div className="space-y-6">
                {/* File upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Select File
                  </label>
                  <FileDropzone
                    onFileSelect={handleFileSelect}
                    disabled={user?.tier !== 'premium'}
                    accept={{
                      'application/json': ['.json'],
                      'text/csv': ['.csv'],
                      'text/xml': ['.xml'],
                      'application/xml': ['.xml'],
                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                      'application/vnd.ms-excel': ['.xls'],
                      'text/yaml': ['.yaml', '.yml'],
                      'application/pdf': ['.pdf'],
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                    }}
                  />
                </div>
                
                {/* Target format */}
                <div>
                  <label htmlFor="targetFormat" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Target Format
                  </label>
                  <select
                    id="targetFormat"
                    value={targetFormat}
                    onChange={(e) => setTargetFormat(e.target.value)}
                    disabled={availableFormats.length === 0 || user?.tier !== 'premium'}
                    className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400"
                  >
                    {availableFormats.length === 0 ? (
                      <option value="">Select a file first</option>
                    ) : (
                      availableFormats.map((format) => (
                        <option key={format} value={format}>
                          {format.toUpperCase()}
                        </option>
                      ))
                    )}
                  </select>
                </div>
                
                {/* Schedule date and time */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="scheduleDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Date
                    </label>
                    <input
                      type="date"
                      id="scheduleDate"
                      min={today}
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      disabled={user?.tier !== 'premium'}
                      className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400"
                    />
                  </div>
                  <div>
                    <label htmlFor="scheduleTime" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Time
                    </label>
                    <input
                      type="time"
                      id="scheduleTime"
                      min={scheduleDate === today ? currentTime : undefined}
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      disabled={user?.tier !== 'premium'}
                      className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400"
                    />
                  </div>
                </div>
                
                {/* Submit button */}
                <div>
                  <button
                    type="button"
                    onClick={handleScheduleConversion}
                    disabled={!file || !targetFormat || !scheduleDate || !scheduleTime || user?.tier !== 'premium' || isScheduling}
                    className="w-full px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isScheduling ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                        Scheduling...
                      </div>
                    ) : (
                      'Schedule Conversion'
                    )}
                  </button>
                </div>
                
                {user?.tier !== 'premium' && (
                  <div className="text-center">
                    <Link to="/app/profile" className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300">
                      Upgrade to Premium
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Scheduled conversions */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <ClockIcon className="h-5 w-5 mr-2 text-primary-500" />
                Scheduled Conversions
              </h2>
              
              {loading ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
                </div>
              ) : scheduledConversions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">File</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Format</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Scheduled For</th>
                        <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {scheduledConversions.map((conversion) => (
                        <tr key={conversion.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                            {conversion.source_filename}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded">
                                {conversion.source_format.toUpperCase()}
                              </span>
                              <svg className="h-4 w-4 mx-2 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              <span className="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 px-2 py-1 rounded">
                                {conversion.target_format.toUpperCase()}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                            {conversion.scheduled_time_friendly}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                            <button
                              onClick={() => handleDeleteScheduled(conversion.id)}
                              disabled={deleting === conversion.id}
                              className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 disabled:opacity-50 focus:outline-none"
                              title="Cancel Scheduled Conversion"
                            >
                              {deleting === conversion.id ? (
                                <div className="h-5 w-5 border-t-2 border-b-2 border-red-600 rounded-full animate-spin"></div>
                              ) : (
                                <TrashIcon className="h-5 w-5" />
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-8 text-center text-gray-500 dark:text-gray-400">
                  <p className="mb-2">No scheduled conversions found.</p>
                  <p className="text-sm">Use the form to schedule a new conversion.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchedulePage; 