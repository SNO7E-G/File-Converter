import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, CancelToken } from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Define constant keys for tokens
const TOKEN_KEY = 'token';
const REFRESH_TOKEN_KEY = 'refreshToken';

// Add cache constants
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes
const CACHE_KEY_PREFIX = 'api_cache_';

// Define supported formats type
export interface SupportedFormats {
  [key: string]: string[];
}

// Define user type
export interface User {
  id: number;
  username: string;
  email: string;
  avatar_url?: string;
  settings?: Record<string, any>;
  tier: string; // Changed from plan to tier to match backend
  created_at: string;
  last_login?: string;
}

// Define conversion type
export interface Conversion {
  id: number;
  user_id: number;
  source_format: string;
  target_format: string;
  source_filename: string;
  target_filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'scheduled' | 'expired';
  created_at: string;
  completed_at?: string;
  scheduled_at?: string;
  expires_at: string;
  error_message?: string;
}

// Define conversion options type
export interface ConversionOptions {
  quality?: number;
  resolution?: string;
  compression?: boolean;
  maintain_aspect_ratio?: boolean;
  [key: string]: any;
}

// Get the base URL from environment variables or default to localhost
const getBaseUrl = () => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined') {
    // For browser environments, use environment variables if available
    // Try to access from window.env first (common pattern for injected env vars)
    // or fall back to a REACT_APP prefixed var in window
    return (window as any).env?.API_URL || 
           (window as any).REACT_APP_API_URL || 
           'http://localhost:8000';
  }
  // For non-browser environments
  return 'http://localhost:8000';
};

// Create axios instance without interceptors for internal use
export const rawApi = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Create axios instance with interceptors for public use
const api = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // This enables sending cookies with requests
  timeout: 30000, // 30 seconds timeout
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Create a flag to prevent multiple simultaneous token refreshes
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];
// Store the timestamp of the last refresh to avoid rapid refresh attempts
let lastRefreshAttempt = 0;

// Function to add callbacks to subscribers
const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

// Function to notify subscribers about new token
const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
};

// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    // Make sure error is an Axios error and has the expected properties
    if (!axios.isAxiosError(error)) {
      return Promise.reject(error);
    }
    
    // Cast with the correct type
    const axiosError = error as AxiosError<any>;
    const originalRequest = axiosError.config as AxiosRequestConfig & { _retry?: boolean };
    
    // If the request was cancelled, don't retry
    if (axios.isCancel(error)) {
      return Promise.reject(axiosError);
    }
    
    // If error is 401 Unauthorized and not a retry and not the refresh endpoint
    if (axiosError.response?.status === 401 && 
        !originalRequest._retry && 
        originalRequest.url !== '/api/auth/refresh') {
      
      // Check if we've attempted a refresh recently (within last 5 seconds)
      // This prevents rapid refresh attempts if multiple requests fail simultaneously
      const now = Date.now();
      const minRefreshInterval = 5000; // 5 seconds
      
      if (now - lastRefreshAttempt < minRefreshInterval) {
        // If recent refresh attempt failed, just reject the request
        if (!isRefreshing) {
          return Promise.reject(axiosError);
        }
      }
      
      // If already refreshing, add the request to subscribers
      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh(token => {
            // Replace the expired token and retry
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(originalRequest));
          });
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      lastRefreshAttempt = now;
      
      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        // Create a new instance to avoid interceptors loop
        const refreshApi = axios.create({
          baseURL: getBaseUrl(),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refreshToken}`,
          },
          timeout: 10000, // Shorter timeout for token refresh
        });
        
        // Request token refresh
        const response = await refreshApi.post('/api/auth/refresh');
        const { token: newToken, refreshToken: newRefreshToken } = response.data;
        
        // Store the new token
        localStorage.setItem(TOKEN_KEY, newToken);
        
        // If a new refresh token was provided, store it
        if (newRefreshToken) {
          localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
        }
        
        // Notify subscribers about new token
        onTokenRefreshed(newToken);
        
        // Reset refreshing flag
        isRefreshing = false;
        
        // Retry the original request with the new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Reset refreshing flag
        isRefreshing = false;
        
        // Clear tokens on failure
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem('user_data');
        
        // Redirect to login after a short delay
        setTimeout(() => {
          window.location.href = '/login?session=expired';
        }, 100);
        
        return Promise.reject(refreshError);
      }
    }
    
    // For network errors, provide more user-friendly messages
    if (!axiosError.response) {
      const networkError = {
        message: 'Network error. Please check your internet connection.',
        code: 'NETWORK_ERROR',
        original: axiosError
      };
      return Promise.reject(networkError);
    }
    
    // For 5xx server errors
    if (axiosError.response.status >= 500) {
      const serverError = {
        message: 'Server error. Please try again later.',
        code: 'SERVER_ERROR',
        status: axiosError.response.status,
        original: axiosError
      };
      return Promise.reject(serverError);
    }
    
    return Promise.reject(axiosError);
  }
);

// Type for user-friendly error messages
export interface ApiErrorDetails {
  message: string;
  code?: string;
  field?: string;
  details?: Record<string, string[]>;
  original?: any;
}

// Cache implementation
interface CacheItem<T> {
  data: T;
  expiry: number;
}

class RequestCache {
  // Clear expired items from cache
  static cleanup() {
    if (typeof window === 'undefined') return;
    
    const now = Date.now();
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        try {
          const item = JSON.parse(localStorage.getItem(key) || '');
          if (item.expiry < now) {
            localStorage.removeItem(key);
          }
        } catch (e) {
          localStorage.removeItem(key);
        }
      }
    });
  }
  
  // Get item from cache
  static get<T>(key: string): T | null {
    if (typeof window === 'undefined') return null;
    
    const cacheKey = CACHE_KEY_PREFIX + key;
    const data = localStorage.getItem(cacheKey);
    
    if (!data) return null;
    
    try {
      const item: CacheItem<T> = JSON.parse(data);
      if (item.expiry < Date.now()) {
        localStorage.removeItem(cacheKey);
        return null;
      }
      return item.data;
    } catch (e) {
      localStorage.removeItem(cacheKey);
      return null;
    }
  }
  
  // Set item in cache
  static set<T>(key: string, data: T, expiryTime = CACHE_EXPIRY): void {
    if (typeof window === 'undefined') return;
    
    const cacheKey = CACHE_KEY_PREFIX + key;
    const item: CacheItem<T> = {
      data,
      expiry: Date.now() + expiryTime
    };
    
    localStorage.setItem(cacheKey, JSON.stringify(item));
  }
  
  // Remove item from cache
  static remove(key: string): void {
    if (typeof window === 'undefined') return;
    
    const cacheKey = CACHE_KEY_PREFIX + key;
    localStorage.removeItem(cacheKey);
  }
}

// Run cache cleanup every minute
if (typeof window !== 'undefined') {
  setInterval(() => RequestCache.cleanup(), 60000);
}

// Enhanced API method wrappers with error handling, caching, and retries
const apiService = {
  get: async <T>(url: string, config?: AxiosRequestConfig & { 
    useCache?: boolean, 
    cacheTime?: number, 
    retry?: number 
  }): Promise<T> => {
    // Parse extra config options
    const { useCache = false, cacheTime = CACHE_EXPIRY, retry = 0, ...axiosConfig } = config || {};
    
    // Generate cache key if using cache
    const cacheKey = useCache ? url + (axiosConfig.params ? JSON.stringify(axiosConfig.params) : '') : '';
    
    // Try to get from cache first
    if (useCache) {
      const cachedData = RequestCache.get<T>(cacheKey);
      if (cachedData) return cachedData;
    }
    
    // If not in cache or not using cache, make actual request
    try {
      const response = await api.get<T>(url, axiosConfig);
      
      // Store in cache if using cache
      if (useCache) {
        RequestCache.set(cacheKey, response.data, cacheTime);
      }
      
      return response.data;
    } catch (error: any) {
      // Implement retry logic
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        console.log(`Retrying GET request to ${url}. Retries left: ${retry - 1}`);
        // Add exponential backoff delay
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, config!.retry! - retry)));
        return apiService.get(url, { ...config, retry: retry - 1 });
      }
      
      const apiError = handleApiError(error);
      throw apiError;
    }
  },
  
  // Enhanced post method with retry
  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig & { 
    retry?: number 
  }): Promise<T> => {
    // Parse extra config options
    const { retry = 0, ...axiosConfig } = config || {};
    
    try {
      const response = await api.post<T>(url, data, axiosConfig);
      return response.data;
    } catch (error: any) {
      // Implement retry logic (only for safe idempotent operations)
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        console.log(`Retrying POST request to ${url}. Retries left: ${retry - 1}`);
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, config!.retry! - retry)));
        return apiService.post(url, data, { ...config, retry: retry - 1 });
      }
      
      const apiError = handleApiError(error);
      throw apiError;
    }
  },
  
  // Specialized methods for file conversion operations
  conversions: {
    // Get a list of all user's conversions
    getAll: async (page = 1, limit = 20, filters?: { status?: string, search?: string }) => {
      const params = { page, limit, ...filters };
      return apiService.get<{conversions: Conversion[], total: number, pages: number}>(
        '/api/conversions',
        { params, useCache: true, cacheTime: 60000 } // 1 minute cache
      );
    },
    
    // Get details of a specific conversion
    getById: async (id: number) => {
      return apiService.get<{conversion: Conversion}>(
        `/api/conversions/${id}`,
        { useCache: true, cacheTime: 30000 } // 30 second cache
      );
    },
    
    // Upload and convert a file
    convert: async (
      file: File, 
      targetFormat: string,
      options?: ConversionOptions,
      onProgress?: (percentage: number) => void,
      scheduling?: { scheduled_at: string } | null
    ) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('target_format', targetFormat);
      
      if (options) {
        formData.append('options', JSON.stringify(options));
      }
      
      if (scheduling) {
        formData.append('scheduled_at', scheduling.scheduled_at);
      }
      
      const requestId = uuidv4();
      formData.append('request_id', requestId); // For tracking and deduplication
      
      return apiService.upload<{conversion_id: number, message: string, status: string}>(
        '/api/upload', 
        formData,
        onProgress
      );
    },
    
    // New: Batch conversion of multiple files
    batchConvert: async (
      files: File[], 
      targetFormat: string,
      options?: ConversionOptions,
      onProgress?: (percentage: number, fileIndex: number) => void
    ) => {
      const formData = new FormData();
      
      // Append all files
      files.forEach((file, index) => {
        formData.append(`files[${index}]`, file);
      });
      
      formData.append('target_format', targetFormat);
      
      if (options) {
        formData.append('options', JSON.stringify(options));
      }
      
      const requestId = uuidv4();
      formData.append('request_id', requestId);
      
      return apiService.upload<{batch_id: string, conversion_ids: number[], message: string}>(
        '/api/batch-upload', 
        formData,
        onProgress && ((percentage) => onProgress(percentage, 0)) // Simplified progress
      );
    },
    
    // New: Get batch conversion status
    getBatchStatus: async (batchId: string) => {
      return apiService.get<{
        batch_id: string,
        total: number,
        completed: number,
        failed: number,
        processing: number,
        conversions: Conversion[]
      }>(`/api/batch/${batchId}`, { retry: 2 });
    },
    
    // Download a converted file
    download: async (conversionId: number, filename?: string) => {
      if (filename) {
        return apiService.download(`/api/conversions/${conversionId}/download`, filename);
      }
      
      // Legacy direct download
      window.location.href = `${getBaseUrl()}/api/conversions/${conversionId}/download`;
    },
    
    // Download all files from a batch as ZIP
    downloadBatch: async (batchId: string, filename = 'conversions.zip') => {
      return apiService.download(`/api/batch/${batchId}/download`, filename);
    },
    
    // Share a conversion with another user
    share: async (conversionId: number, sharedWithId: number, permission: 'view' | 'download' | 'edit') => {
      return apiService.post<{message: string}>(`/api/conversions/${conversionId}/share`, {
        shared_with_id: sharedWithId,
        permission
      });
    },
    
    // New: Cancel a pending or processing conversion
    cancel: async (conversionId: number) => {
      return apiService.post<{message: string}>(`/api/conversions/${conversionId}/cancel`);
    },
    
    // New: Retry a failed conversion
    retry: async (conversionId: number, options?: ConversionOptions) => {
      const data = options ? { options } : {};
      return apiService.post<{message: string, status: string}>(
        `/api/conversions/${conversionId}/retry`,
        data
      );
    }
  },
  
  // Get all supported formats with caching
  getSupportedFormats: async () => {
    return apiService.get<{supported_formats: SupportedFormats, conversion_paths: any}>(
      '/api/formats',
      { useCache: true, cacheTime: 24 * 60 * 60 * 1000 } // Cache for 24 hours
    );
  },
  
  // New: Get conversion options for specific formats
  getConversionOptions: async (sourceFormat: string, targetFormat: string) => {
    return apiService.get<Record<string, any>>(
      `/api/formats/options?source=${sourceFormat}&target=${targetFormat}`,
      { useCache: true, cacheTime: 24 * 60 * 60 * 1000 } // Cache for 24 hours
    );
  },
  
  // Method for uploading files with progress tracking
  upload: async <T>(
    url: string, 
    formData: FormData, 
    onProgress?: (percentage: number) => void,
    cancelToken?: CancelToken,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const uploadConfig: AxiosRequestConfig = {
        ...config,
        headers: {
          ...config?.headers,
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentage);
          }
        },
        cancelToken
      };
      
      const response = await api.post<T>(url, formData, uploadConfig);
      return response.data;
    } catch (error: any) {
      if (axios.isCancel(error)) {
        throw {
          message: 'Upload cancelled',
          code: 'UPLOAD_CANCELLED',
          original: error
        };
      }
      
      const apiError = handleApiError(error);
      throw apiError;
    }
  },
  
  // Method for downloading files with progress tracking
  download: async (
    url: string,
    filename: string,
    onProgress?: (percentage: number) => void,
    cancelToken?: CancelToken,
    config?: AxiosRequestConfig
  ): Promise<Blob> => {
    try {
      const downloadConfig: AxiosRequestConfig = {
        ...config,
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentage);
          }
        },
        cancelToken
      };
      
      const response = await api.get(url, downloadConfig);
      
      // Create download link and trigger download
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(link);
      
      return blob;
    } catch (error: any) {
      if (axios.isCancel(error)) {
        throw {
          message: 'Download cancelled',
          code: 'DOWNLOAD_CANCELLED',
          original: error
        };
      }
      
      const apiError = handleApiError(error);
      throw apiError;
    }
  },
  
  // Utility to create a cancel token
  getCancelToken: () => {
    return axios.CancelToken.source();
  },
  
  // Utility to check if error was a cancellation
  isCancel: (error: any): boolean => {
    return axios.isCancel(error);
  }
};

// Helper function to handle API errors
const handleApiError = (error: unknown): ApiErrorDetails => {
  // Check if it's an Axios error
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    
    // Network errors (no response)
    if (!axiosError.response) {
      return {
        message: axiosError.message || 'Network error. Please check your internet connection.',
        code: 'NETWORK_ERROR',
        original: axiosError
      };
    }
    
    // Server errors (5xx)
    if (axiosError.response.status >= 500) {
      return {
        message: 'Server error. Please try again later.',
        code: 'SERVER_ERROR',
        original: axiosError
      };
    }
    
    // Client errors with response data
    if (axiosError.response.data) {
      const { data } = axiosError.response;
      
      // If the API returns a specific error message
      if (data.message || data.error) {
        return {
          message: data.message || data.error,
          code: data.code,
          field: data.field,
          details: data.details,
          original: axiosError
        };
      }
      
      // Validation errors with field details
      if (data.errors || data.details) {
        const details = data.errors || data.details;
        let message = 'Validation error';
        
        // Try to extract a more specific message from the first error
        if (typeof details === 'object') {
          const firstField = Object.keys(details)[0];
          if (firstField && Array.isArray(details[firstField]) && details[firstField].length > 0) {
            message = `${firstField}: ${details[firstField][0]}`;
          }
        }
        
        return {
          message,
          code: 'VALIDATION_ERROR',
          details,
          original: axiosError
        };
      }
    }
  }
  
  // Default error handling for non-Axios errors
  return {
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
    code: 'UNKNOWN_ERROR',
    original: error
  };
};

// Export common response and error types
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface ApiError {
  error: string;
  details?: Record<string, string[]>;
  status?: number;
}

// Auth related types
export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
  message?: string;
}

// Conversion API types
export interface ConversionRequest {
  target_format: string;
  options?: Record<string, any>;
  webhook_url?: string;
  scheduled_time?: string;
}

export interface ConversionsResponse {
  conversions: Conversion[];
  total: number;
  pages: number;
  current_page: number;
}

// Template types
export interface Template {
  id: number;
  user_id: number;
  name: string;
  description: string;
  source_format: string;
  target_format: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
  used_count: number;
}

export interface TemplatesResponse {
  templates: Template[];
  total: number;
}

// Sharing types
export interface SharedConversion {
  id: number;
  conversion_id: number;
  shared_by: {
    id: number;
    username: string;
    email: string;
  };
  shared_with: {
    id: number;
    username: string;
    email: string;
  };
  permission: 'view' | 'download' | 'edit';
  created_at: string;
  updated_at: string;
  conversion: Conversion;
}

export interface SharedConversionsResponse {
  shared_conversions: SharedConversion[];
  total: number;
}

// Statistics types
export interface StatisticsData {
  conversions_today: number;
  total_conversions: number;
  conversions_by_date: Record<string, number>;
  conversions_by_format: Record<string, number>;
  source_formats: Record<string, number>;
  target_formats: Record<string, number>;
  conversions_by_status: Record<string, number>;
  peak_usage_hours: Record<string, number>;
  most_used_format: string;
}

export default apiService; 