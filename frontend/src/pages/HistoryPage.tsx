import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import { Conversion, ConversionsResponse } from '../utils/api';
import {
  ArrowDownTrayIcon,
  TrashIcon,
  ShareIcon,
  DocumentMagnifyingGlassIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';

const HistoryPage: React.FC = () => {
  const { user } = useAuth();
  const [conversions, setConversions] = useState<Conversion[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [filters, setFilters] = useState({
    status: '',
    sourceFormat: '',
    targetFormat: '',
    dateRange: '',
  });
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [sharing, setSharing] = useState<number | null>(null);
  const [shareEmail, setShareEmail] = useState<string>('');
  const [sharePermission, setSharePermission] = useState<string>('view');
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [selectedConversion, setSelectedConversion] = useState<Conversion | null>(null);
  const [alertMessage, setAlertMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // Status options for filtering
  const statusOptions = ['all', 'pending', 'processing', 'completed', 'failed', 'scheduled'];
  
  // Format options for filtering
  const formatOptions = ['all', 'csv', 'json', 'xml', 'yaml', 'excel', 'pdf', 'docx'];

  // Date range options for filtering
  const dateRangeOptions = ['all', 'today', 'week', 'month'];

  // Load conversions
  useEffect(() => {
    fetchConversions();
  }, [currentPage, filters]);

  const fetchConversions = async () => {
    try {
      setLoading(true);
      
      // Prepare query parameters
      const params: Record<string, string | number> = {
        page: currentPage,
        limit: 10,
      };
      
      // Add filters if they are set
      if (filters.status && filters.status !== 'all') {
        params.status = filters.status;
      }
      if (filters.sourceFormat && filters.sourceFormat !== 'all') {
        params.source_format = filters.sourceFormat;
      }
      if (filters.targetFormat && filters.targetFormat !== 'all') {
        params.target_format = filters.targetFormat;
      }
      if (filters.dateRange && filters.dateRange !== 'all') {
        params.date_range = filters.dateRange;
      }
      if (searchTerm) {
        params.search = searchTerm;
      }
      
      const response = await api.get<ConversionsResponse>('/api/conversions', { params });
      
      setConversions(response.data.conversions);
      setTotalPages(response.data.pages);
    } catch (error) {
      console.error('Error fetching conversions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page on new search
    fetchConversions();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleDeleteConversion = async (id: number) => {
    try {
      setDeleting(id);
      await api.delete(`/api/conversions/${id}`);
      
      // Remove the deleted conversion from the list
      setConversions((prev) => prev.filter(conv => conv.id !== id));
      
    } catch (error) {
      console.error('Error deleting conversion:', error);
    } finally {
      setDeleting(null);
    }
  };

  const handleShareConversion = async (id: number) => {
    if (!shareEmail) return;
    
    try {
      setSharing(id);
      await api.post(`/api/conversions/${id}/share`, {
        shared_with_id: shareEmail,
        permission: sharePermission,
      });
      
      // Close share dialog after successful share
      setSharing(null);
      setShareEmail('');
      
    } catch (error) {
      console.error('Error sharing conversion:', error);
    } finally {
      setSharing(null);
    }
  };

  const handleDownload = (id: number) => {
    window.open(`${api.defaults.baseURL}/api/conversions/${id}/download`, '_blank');
  };

  const openShareModal = (conversion: Conversion) => {
    setSelectedConversion(conversion);
    setShareEmail('');
    setSharePermission('view');
    setShowShareModal(true);
  };

  const closeShareModal = () => {
    setShowShareModal(false);
    setSelectedConversion(null);
  };

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedConversion) return;
    
    try {
      await api.post('/api/share', {
        conversion_id: selectedConversion.id,
        email: shareEmail,
        permission: sharePermission
      });
      
      showAlert('success', `Conversion shared with ${shareEmail}`);
      closeShareModal();
    } catch (err) {
      console.error('Error sharing conversion:', err);
      showAlert('error', 'Failed to share conversion');
    }
  };

  const showAlert = (type: 'success' | 'error', text: string) => {
    setAlertMessage({ type, text });
    setTimeout(() => setAlertMessage(null), 5000);
  };

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

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 lg:mb-0">Conversion History</h1>
        
        <div className="w-full lg:w-auto flex flex-col sm:flex-row gap-4">
          {/* Search box */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <input
                type="text"
                placeholder="Search by filename..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <button
                type="submit"
                className="absolute inset-y-0 right-0 px-3 flex items-center bg-primary-500 text-white rounded-r-md"
              >
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          </form>
          
          {/* Filter toggle button */}
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>
      </div>
      
      {/* Filters */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                id="status"
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
              >
                {statusOptions.map((option) => (
                  <option key={option} value={option === 'all' ? '' : option}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="sourceFormat" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Source Format
              </label>
              <select
                id="sourceFormat"
                name="sourceFormat"
                value={filters.sourceFormat}
                onChange={handleFilterChange}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
              >
                {formatOptions.map((option) => (
                  <option key={option} value={option === 'all' ? '' : option}>
                    {option === 'all' ? 'All Formats' : option.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="targetFormat" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Target Format
              </label>
              <select
                id="targetFormat"
                name="targetFormat"
                value={filters.targetFormat}
                onChange={handleFilterChange}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
              >
                {formatOptions.map((option) => (
                  <option key={option} value={option === 'all' ? '' : option}>
                    {option === 'all' ? 'All Formats' : option.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date Range
              </label>
              <select
                id="dateRange"
                name="dateRange"
                value={filters.dateRange}
                onChange={handleFilterChange}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
              >
                {dateRangeOptions.map((option) => (
                  <option key={option} value={option === 'all' ? '' : option}>
                    {option === 'all' ? 'All Time' : option === 'today' ? 'Today' : `Last ${option}`}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => {
                setFilters({ status: '', sourceFormat: '', targetFormat: '', dateRange: '' });
                setSearchTerm('');
                setCurrentPage(1);
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-500 dark:hover:text-gray-400"
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}
      
      {/* Conversions table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : conversions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Source File</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Formats</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {conversions.map((conversion) => (
                  <tr key={conversion.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {conversion.source_filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      <div className="flex items-center">
                        <span className="font-medium">{conversion.source_format.toUpperCase()}</span>
                        <svg className="h-4 w-4 mx-2 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium">{conversion.target_format.toUpperCase()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${conversion.status === 'completed' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                          : conversion.status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            : conversion.status === 'scheduled'
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        }`}
                      >
                        {conversion.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {formatDate(conversion.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex justify-center space-x-3">
                        <Link
                          to={`/app/history/${conversion.id}`}
                          className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                          title="View Details"
                        >
                          <DocumentMagnifyingGlassIcon className="h-5 w-5" />
                        </Link>
                        
                        {conversion.status === 'completed' && (
                          <button
                            onClick={() => handleDownload(conversion.id)}
                            className="text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-300"
                            title="Download"
                          >
                            <ArrowDownTrayIcon className="h-5 w-5" />
                          </button>
                        )}
                        
                        {user?.tier === 'premium' && (
                          <button
                            onClick={() => openShareModal(conversion)}
                            className="text-secondary-600 dark:text-secondary-400 hover:text-secondary-800 dark:hover:text-secondary-300"
                            title="Share"
                          >
                            <ShareIcon className="h-5 w-5" />
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDeleteConversion(conversion.id)}
                          disabled={deleting === conversion.id}
                          className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 disabled:opacity-50"
                          title="Delete"
                        >
                          {deleting === conversion.id ? (
                            <div className="h-5 w-5 border-t-2 border-b-2 border-red-600 rounded-full animate-spin"></div>
                          ) : (
                            <TrashIcon className="h-5 w-5" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No conversions found. Start by converting a file!
          </div>
        )}
        
        {/* Pagination */}
        {conversions.length > 0 && totalPages > 1 && (
          <div className="bg-gray-50 dark:bg-gray-900 px-6 py-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Showing page <span className="font-medium">{currentPage}</span> of{' '}
                <span className="font-medium">{totalPages}</span>
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                // Calculate which page numbers to show
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={i}
                    onClick={() => handlePageChange(pageNum)}
                    className={`px-3 py-1 border rounded-md text-sm font-medium ${
                      currentPage === pageNum
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                        : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Share Modal */}
      {showShareModal && selectedConversion && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Share Conversion
            </h2>
            
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Share "{selectedConversion.source_filename}" with others by email.
            </p>
            
            <form onSubmit={handleShare}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  className="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm px-4 py-2 focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-400 dark:focus:border-primary-400"
                  placeholder="person@example.com"
                  required
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Permission</label>
                <select
                  value={sharePermission}
                  onChange={(e) => setSharePermission(e.target.value as 'view' | 'download' | 'edit')}
                  className="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 shadow-sm px-4 py-2 focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-400 dark:focus:border-primary-400"
                >
                  <option value="view">View only</option>
                  <option value="download">View and download</option>
                  <option value="edit">View, download and edit</option>
                </select>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={closeShareModal}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:focus:ring-offset-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:focus:ring-offset-gray-800"
                >
                  Share
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPage; 