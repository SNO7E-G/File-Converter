import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { ArrowUpTrayIcon, DocumentArrowUpIcon, XMarkIcon, TrashIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import apiService, { SupportedFormats } from '../utils/api';
import { Spinner } from '../components/Spinner';

// Format Categories
const FORMAT_CATEGORIES = {
  'Document': ['csv', 'json', 'xml', 'yaml', 'xlsx', 'xls', 'pdf', 'docx', 'txt'],
  'Image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff'],
  'Audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
  'Video': ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv']
};

interface BatchFile {
  id: string;
  file: File;
  sourceFormat: string;
  targetFormat: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: string;
  downloadUrl?: string;
}

const BatchConvertPage: React.FC = () => {
  const [files, setFiles] = useState<BatchFile[]>([]);
  const [formats, setFormats] = useState<SupportedFormats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [targetFormat, setTargetFormat] = useState('');
  const [currentCategory, setCurrentCategory] = useState('Document');
  const [advancedOptions, setAdvancedOptions] = useState(false);
  const [options, setOptions] = useState<Record<string, any>>({});
  const [batchStatus, setBatchStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle');
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState(0);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [overallProgress, setOverallProgress] = useState(0);

  // Fetch supported formats on mount
  useEffect(() => {
    const fetchFormats = async () => {
      try {
        const response = await apiService.get('/api/formats');
        setFormats(response.data.formats);
      } catch (err) {
        console.error('Error fetching formats:', err);
      }
    };

    fetchFormats();
  }, []);

  // Setup dropzone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => {
      // Get the file extension
      const extension = file.name.split('.').pop()?.toLowerCase() || '';
      
      // Find which category this file belongs to
      let fileCategory = 'Document';
      for (const [category, extensions] of Object.entries(FORMAT_CATEGORIES)) {
        if (extensions.includes(extension)) {
          fileCategory = category;
          break;
        }
      }
      
      // Update current category if this is the first file
      if (files.length === 0) {
        setCurrentCategory(fileCategory);
      }
      
      return {
        id: `${Date.now()}-${file.name}`,
        file,
        sourceFormat: extension,
        targetFormat: '',
        status: 'pending' as const,
        progress: 0
      };
    });
    
    setFiles(prev => [...prev, ...newFiles]);
  }, [files.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    multiple: true
  });

  // Remove a file from the batch
  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id));
  };

  // Clear all files
  const clearFiles = () => {
    setFiles([]);
    setBatchStatus('idle');
    setBatchId(null);
    setBatchProgress(0);
    setProcessingTime(null);
  };

  // Start batch conversion
  const startBatchConversion = async () => {
    if (files.length === 0 || !targetFormat) return;
    
    // Check if all files have a source format
    const invalidFiles = files.filter(file => !file.sourceFormat);
    if (invalidFiles.length > 0) {
      alert(`Some files don't have a valid source format: ${invalidFiles.map(f => f.file.name).join(', ')}`);
      return;
    }

    try {
      setBatchStatus('uploading');
      const startTime = Date.now();
      
      // Create FormData with all files
      const formData = new FormData();
      
      // Add each file
      files.forEach((fileObj, index) => {
        formData.append(`files[${index}]`, fileObj.file);
        formData.append(`sourceFormats[${index}]`, fileObj.sourceFormat);
      });
      
      // Add common target format
      formData.append('targetFormat', targetFormat);
      
      // Add options if available
      if (Object.keys(options).length > 0) {
        formData.append('options', JSON.stringify(options));
      }
      
      // Upload config to track progress
      const config = {
        onUploadProgress: (progressEvent: any) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
          setOverallProgress(percentCompleted * 0.5); // Upload is 50% of overall progress
        }
      };
      
      // Start batch conversion
      const response = await apiService.upload('/api/batch-convert', formData, config);
      
      // Update state with batch ID
      setBatchId(response.data.batchId);
      setBatchStatus('processing');
      
      // Start polling for batch status
      pollBatchStatus(response.data.batchId);
      
      // Update files with initial status
      setFiles(prevFiles => 
        prevFiles.map(file => ({
          ...file,
          targetFormat,
          status: 'processing',
          progress: 0
        }))
      );
      
    } catch (err: any) {
      console.error('Error starting batch conversion:', err);
      setBatchStatus('failed');
      alert(err.userMessage || 'Failed to start batch conversion');
    }
  };

  // Poll batch status
  const pollBatchStatus = async (batchId: string) => {
    try {
      const response = await apiService.get(`/api/batch-convert/${batchId}`);
      const batchData = response.data;
      
      // Update batch progress
      setBatchProgress(batchData.progress);
      setOverallProgress(50 + (batchData.progress * 0.5)); // Processing is the second 50%
      
      // Update individual file statuses
      if (batchData.tasks) {
        setFiles(prevFiles => 
          prevFiles.map(file => {
            const matchingTask = batchData.tasks.find((task: any) => 
              task.originalFilename === file.file.name
            );
            
            if (matchingTask) {
              return {
                ...file,
                status: matchingTask.status,
                progress: matchingTask.progress,
                error: matchingTask.error,
                downloadUrl: matchingTask.downloadUrl
              };
            }
            
            return file;
          })
        );
      }
      
      // Check if batch is complete
      if (batchData.status === 'completed') {
        setBatchStatus('completed');
        const endTime = Date.now();
        setProcessingTime((endTime - batchData.startTime) / 1000);
        setOverallProgress(100);
      } else if (batchData.status === 'failed') {
        setBatchStatus('failed');
      } else {
        // Continue polling
        setTimeout(() => pollBatchStatus(batchId), 1000);
      }
      
    } catch (err) {
      console.error('Error polling batch status:', err);
      setTimeout(() => pollBatchStatus(batchId), 3000); // Retry with longer delay
    }
  };

  // Handle option change
  const handleOptionChange = (name: string, value: any) => {
    setOptions(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Render format-specific options
  const renderOptions = () => {
    if (!advancedOptions) return null;
    
    // Get the common options based on the selected category
    switch (currentCategory) {
      case 'Image':
        return (
          <div className="mt-4 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium mb-3">Image Options</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Quality (1-100)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  className="form-input mt-1"
                  value={options.quality || 85}
                  onChange={(e) => handleOptionChange('quality', parseInt(e.target.value))}
                />
              </div>
              <div>
                <label className="form-label">Resize</label>
                <div className="flex space-x-2 mt-1">
                  <input
                    type="number"
                    placeholder="Width"
                    className="form-input w-1/2"
                    value={options.resize ? options.resize[0] : ''}
                    onChange={(e) => {
                      const width = e.target.value ? parseInt(e.target.value) : '';
                      const height = options.resize ? options.resize[1] : '';
                      handleOptionChange('resize', width !== '' && height !== '' ? [width, height] : null);
                    }}
                  />
                  <input
                    type="number"
                    placeholder="Height"
                    className="form-input w-1/2"
                    value={options.resize ? options.resize[1] : ''}
                    onChange={(e) => {
                      const height = e.target.value ? parseInt(e.target.value) : '';
                      const width = options.resize ? options.resize[0] : '';
                      handleOptionChange('resize', width !== '' && height !== '' ? [width, height] : null);
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'Audio':
        return (
          <div className="mt-4 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium mb-3">Audio Options</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Bitrate</label>
                <select
                  className="form-select mt-1"
                  value={options.bitrate || '192k'}
                  onChange={(e) => handleOptionChange('bitrate', e.target.value)}
                >
                  <option value="64k">64 kbps (Low)</option>
                  <option value="128k">128 kbps (Medium)</option>
                  <option value="192k">192 kbps (Standard)</option>
                  <option value="256k">256 kbps (High)</option>
                </select>
              </div>
              <div>
                <label className="form-label">Sample Rate</label>
                <select
                  className="form-select mt-1"
                  value={options.sample_rate || '44100'}
                  onChange={(e) => handleOptionChange('sample_rate', parseInt(e.target.value))}
                >
                  <option value="22050">22.05 kHz</option>
                  <option value="44100">44.1 kHz (CD Quality)</option>
                  <option value="48000">48 kHz</option>
                </select>
              </div>
            </div>
          </div>
        );
        
      case 'Video':
        return (
          <div className="mt-4 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium mb-3">Video Options</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Resolution</label>
                <select
                  className="form-select mt-1"
                  value={options.resolution || ''}
                  onChange={(e) => handleOptionChange('resolution', e.target.value)}
                >
                  <option value="">Original</option>
                  <option value="640x480">SD (640x480)</option>
                  <option value="1280x720">HD (1280x720)</option>
                  <option value="1920x1080">Full HD (1920x1080)</option>
                </select>
              </div>
              <div>
                <label className="form-label">Quality</label>
                <select
                  className="form-select mt-1"
                  value={options.quality || 'medium'}
                  onChange={(e) => handleOptionChange('quality', e.target.value)}
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  // Calculate status counts
  const statusCounts = files.reduce((acc, file) => {
    acc[file.status] = (acc[file.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-4">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Batch Conversion</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Convert multiple files at once to the same target format
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden mb-6">
        <div className="p-6">
          {/* File drop area */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-md p-6 ${
              isDragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-300 dark:border-gray-700'
            }`}
          >
            <div className="space-y-1 text-center">
              <input {...getInputProps()} />
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
                aria-hidden="true"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H8m36-12h-4m4 0H20"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="flex text-sm text-gray-600 dark:text-gray-400 justify-center">
                <label
                  htmlFor="file-upload"
                  className="relative cursor-pointer rounded-md font-medium text-primary-600 dark:text-primary-400 hover:text-primary-500 focus-within:outline-none"
                >
                  <span>Upload multiple files</span>
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {currentCategory === 'Document' 
                  ? 'Documents like PDF, DOCX, XLSX, CSV, JSON, XML, etc.' 
                  : currentCategory === 'Image' 
                    ? 'Images like JPG, PNG, GIF, WEBP, etc.' 
                    : currentCategory === 'Audio' 
                      ? 'Audio files like MP3, WAV, OGG, etc.' 
                      : 'Video files like MP4, AVI, MOV, etc.'}
              </p>
            </div>
          </div>

          {/* Format selection */}
          {files.length > 0 && (
            <div className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Category
                </label>
                <div className="mt-1 grid grid-cols-4 gap-2">
                  {Object.keys(FORMAT_CATEGORIES).map((category) => (
                    <button
                      key={category}
                      type="button"
                      className={`px-3 py-2 text-sm font-medium rounded-md ${
                        currentCategory === category
                          ? 'bg-primary-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                      onClick={() => {
                        setCurrentCategory(category);
                        setTargetFormat('');
                      }}
                      disabled={batchStatus !== 'idle'}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="target-format" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Target Format (for all files)
                </label>
                <select
                  id="target-format"
                  className="form-select mt-1"
                  value={targetFormat}
                  onChange={(e) => setTargetFormat(e.target.value)}
                  disabled={batchStatus !== 'idle' || !formats}
                >
                  <option value="">Select target format</option>
                  {formats && 
                    Array.from(new Set(
                      Object.entries(formats)
                        .filter(([sourceFormat]) => FORMAT_CATEGORIES[currentCategory].includes(sourceFormat))
                        .flatMap(([_, targetFormats]) => targetFormats)
                    ))
                    .sort()
                    .map(format => (
                      <option key={format} value={format}>{format.toUpperCase()}</option>
                    ))
                  }
                </select>
              </div>

              {/* Advanced options toggle */}
              <div className="flex items-center">
                <button
                  type="button"
                  className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-500 focus:outline-none focus:underline"
                  onClick={() => setAdvancedOptions(!advancedOptions)}
                  disabled={batchStatus !== 'idle'}
                >
                  {advancedOptions ? '- Hide advanced options' : '+ Show advanced options'}
                </button>
              </div>
              
              {/* Format-specific options */}
              {renderOptions()}
            </div>
          )}

          {/* File list */}
          {files.length > 0 && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Files to Convert</h3>
                <div className="flex space-x-2">
                  {batchStatus === 'idle' && (
                    <button
                      onClick={clearFiles}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <TrashIcon className="mr-1.5 h-4 w-4 text-gray-500 dark:text-gray-400" />
                      Clear All
                    </button>
                  )}
                  {batchStatus === 'idle' && (
                    <button
                      onClick={startBatchConversion}
                      disabled={files.length === 0 || !targetFormat}
                      className={`inline-flex items-center px-4 py-1.5 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                        files.length === 0 || !targetFormat
                          ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
                          : 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500'
                      }`}
                    >
                      <DocumentArrowUpIcon className="mr-1.5 h-4 w-4" />
                      Start Conversion
                    </button>
                  )}
                </div>
              </div>
              
              {/* Status summary */}
              {files.length > 0 && (
                <div className="flex space-x-4 mb-2 text-sm">
                  <div className="text-gray-500 dark:text-gray-400">
                    Total: {files.length} files
                  </div>
                  {statusCounts.completed && (
                    <div className="text-green-600 dark:text-green-400">
                      Completed: {statusCounts.completed}
                    </div>
                  )}
                  {statusCounts.processing && (
                    <div className="text-blue-600 dark:text-blue-400">
                      Processing: {statusCounts.processing}
                    </div>
                  )}
                  {statusCounts.failed && (
                    <div className="text-red-600 dark:text-red-400">
                      Failed: {statusCounts.failed}
                    </div>
                  )}
                  {statusCounts.pending && (
                    <div className="text-yellow-600 dark:text-yellow-400">
                      Pending: {statusCounts.pending}
                    </div>
                  )}
                </div>
              )}
              
              {/* Overall progress bar */}
              {batchStatus !== 'idle' && (
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>Overall Progress</span>
                    <span>{Math.round(overallProgress)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-bar-fill" 
                      style={{ width: `${overallProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}
              
              {/* Processing info */}
              {batchStatus === 'completed' && processingTime !== null && (
                <div className="mb-4 p-2 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded text-sm">
                  Batch conversion completed in {processingTime.toFixed(1)} seconds.
                </div>
              )}
              
              {/* File list */}
              <div className="mt-2 border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
                <ul role="list" className="divide-y divide-gray-200 dark:divide-gray-700 max-h-96 overflow-y-auto">
                  {files.map((file) => (
                    <li key={file.id} className="px-4 py-3 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-800">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center min-w-0 flex-1">
                          <div className="flex-shrink-0">
                            {file.status === 'completed' ? (
                              <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            ) : file.status === 'failed' ? (
                              <XMarkIcon className="h-5 w-5 text-red-500" />
                            ) : file.status === 'processing' ? (
                              <Spinner size="sm" />
                            ) : (
                              <DocumentArrowUpIcon className="h-5 w-5 text-gray-400" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1 px-4">
                            <div className="flex items-center">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {file.file.name}
                              </p>
                              <p className="ml-2 flex-shrink-0 text-xs text-gray-500 dark:text-gray-400">
                                {(file.file.size / 1024).toFixed(0)} KB
                              </p>
                            </div>
                            <div className="mt-1">
                              {file.status === 'pending' && (
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  Waiting to start
                                </p>
                              )}
                              {file.status === 'processing' && (
                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                                  <div 
                                    className="bg-blue-500 h-1.5 rounded-full" 
                                    style={{ width: `${file.progress}%` }}
                                  ></div>
                                </div>
                              )}
                              {file.status === 'completed' && (
                                <p className="text-xs text-green-600 dark:text-green-400">
                                  Conversion successful
                                </p>
                              )}
                              {file.status === 'failed' && (
                                <p className="text-xs text-red-600 dark:text-red-400">
                                  {file.error || 'Conversion failed'}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex-shrink-0 flex space-x-2">
                          {file.status === 'completed' && file.downloadUrl && (
                            <a
                              href={file.downloadUrl}
                              download
                              className="inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded text-primary-700 bg-primary-100 hover:bg-primary-200 dark:bg-primary-900/30 dark:text-primary-300 dark:hover:bg-primary-800/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                            >
                              <ArrowUpTrayIcon className="mr-1 h-4 w-4" />
                              Download
                            </a>
                          )}
                          
                          {batchStatus === 'idle' && (
                            <button
                              onClick={() => removeFile(file.id)}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none"
                            >
                              <XMarkIcon className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BatchConvertPage; 