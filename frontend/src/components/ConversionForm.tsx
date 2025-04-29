import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { SupportedFormats } from '../utils/api';
import api from '../utils/api';
import { Spinner } from './Spinner';

// Define format categories
const FORMAT_CATEGORIES = {
  'Document': ['csv', 'json', 'xml', 'yaml', 'xlsx', 'xls', 'pdf', 'docx', 'txt'],
  'Image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff'],
  'Audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
  'Video': ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv']
};

interface ConversionFormProps {
  onConversionStart?: () => void;
  onConversionComplete?: (result: any) => void;
  onConversionError?: (error: any) => void;
}

const ConversionForm: React.FC<ConversionFormProps> = ({
  onConversionStart,
  onConversionComplete,
  onConversionError
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceFormat, setSourceFormat] = useState<string>('');
  const [targetFormat, setTargetFormat] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [formats, setFormats] = useState<SupportedFormats | null>(null);
  const [advancedOptions, setAdvancedOptions] = useState<boolean>(false);
  const [options, setOptions] = useState<Record<string, any>>({});
  const [currentCategory, setCurrentCategory] = useState<string>('Document');
  const [progress, setProgress] = useState<number>(0);

  // Fetch supported formats on mount
  useEffect(() => {
    const fetchFormats = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/formats');
        setFormats(response.data.formats);
      } catch (err) {
        setError('Failed to load supported formats');
        console.error('Error fetching formats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFormats();
  }, []);

  // Setup dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: acceptedFiles => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setSelectedFile(file);
        
        // Try to determine the source format from file extension
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (extension && formats && Object.keys(formats).includes(extension)) {
          setSourceFormat(extension);
          
          // Set current category based on extension
          for (const [category, formatList] of Object.entries(FORMAT_CATEGORIES)) {
            if (formatList.includes(extension)) {
              setCurrentCategory(category);
              break;
            }
          }
        }
      }
    },
    multiple: false,
  });

  // Handle conversion
  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile || !sourceFormat || !targetFormat) {
      setError('Please select a file, source format, and target format');
      return;
    }
    
    try {
      setLoading(true);
      setProgress(0);
      setError(null);
      setSuccess(false);
      
      if (onConversionStart) {
        onConversionStart();
      }
      
      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('source_format', sourceFormat);
      formData.append('target_format', targetFormat);
      
      // Add options if any
      if (Object.keys(options).length > 0) {
        formData.append('options', JSON.stringify(options));
      }
      
      // Setup upload progress tracking
      const config = {
        onUploadProgress: (progressEvent: any) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      };
      
      // Send conversion request
      const response = await api.upload('/api/convert', formData, config);
      
      // Handle success
      setSuccess(true);
      
      if (onConversionComplete) {
        onConversionComplete(response);
      }
      
    } catch (err: any) {
      setError(err.userMessage || 'Failed to convert file');
      
      if (onConversionError) {
        onConversionError(err);
      }
    } finally {
      setLoading(false);
    }
  };

  // Helper to get available target formats for current source format
  const getAvailableTargetFormats = () => {
    if (!formats || !sourceFormat) return [];
    return formats[sourceFormat] || [];
  };

  // Reset form
  const handleReset = () => {
    setSelectedFile(null);
    setSourceFormat('');
    setTargetFormat('');
    setError(null);
    setSuccess(false);
    setOptions({});
    setAdvancedOptions(false);
  };

  // Handle option change
  const handleOptionChange = (name: string, value: any) => {
    setOptions(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Render format-specific options
  const renderFormatOptions = () => {
    if (!advancedOptions) return null;
    
    // Options for images
    if (FORMAT_CATEGORIES.Image.includes(sourceFormat)) {
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
            <div>
              <label className="form-label">Grayscale</label>
              <div className="mt-1">
                <input
                  type="checkbox"
                  className="form-checkbox"
                  checked={options.grayscale || false}
                  onChange={(e) => handleOptionChange('grayscale', e.target.checked)}
                />
              </div>
            </div>
            <div>
              <label className="form-label">Rotate (degrees)</label>
              <input
                type="number"
                className="form-input mt-1"
                value={options.rotate || 0}
                onChange={(e) => handleOptionChange('rotate', parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>
      );
    }
    
    // Options for audio
    if (FORMAT_CATEGORIES.Audio.includes(sourceFormat)) {
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
                <option value="320k">320 kbps (Very High)</option>
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
                <option value="96000">96 kHz (Studio Quality)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Channels</label>
              <select
                className="form-select mt-1"
                value={options.channels || '2'}
                onChange={(e) => handleOptionChange('channels', parseInt(e.target.value))}
              >
                <option value="1">Mono (1)</option>
                <option value="2">Stereo (2)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Volume Adjustment</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                className="w-full mt-1"
                value={options.volume || 1}
                onChange={(e) => handleOptionChange('volume', parseFloat(e.target.value))}
              />
              <div className="text-xs text-center mt-1">{options.volume || 1}x</div>
            </div>
          </div>
        </div>
      );
    }
    
    // Options for video
    if (FORMAT_CATEGORIES.Video.includes(sourceFormat)) {
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
                <option value="3840x2160">4K (3840x2160)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Quality</label>
              <select
                className="form-select mt-1"
                value={options.crf || '23'}
                onChange={(e) => handleOptionChange('crf', parseInt(e.target.value))}
              >
                <option value="18">High (18)</option>
                <option value="23">Medium (23)</option>
                <option value="28">Low (28)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Frame Rate</label>
              <select
                className="form-select mt-1"
                value={options.fps || ''}
                onChange={(e) => handleOptionChange('fps', e.target.value ? parseInt(e.target.value) : '')}
              >
                <option value="">Original</option>
                <option value="24">24 fps (Film)</option>
                <option value="30">30 fps (Standard)</option>
                <option value="60">60 fps (High)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Speed</label>
              <select
                className="form-select mt-1"
                value={options.preset || 'medium'}
                onChange={(e) => handleOptionChange('preset', e.target.value)}
              >
                <option value="ultrafast">Ultrafast (Lowest quality)</option>
                <option value="superfast">Superfast</option>
                <option value="veryfast">Very fast</option>
                <option value="faster">Faster</option>
                <option value="fast">Fast</option>
                <option value="medium">Medium (Balanced)</option>
                <option value="slow">Slow</option>
                <option value="slower">Slower</option>
                <option value="veryslow">Very slow (Highest quality)</option>
              </select>
            </div>
          </div>
        </div>
      );
    }
    
    return null;
  };

  return (
    <div className="w-full">
      <form onSubmit={handleConvert} className="space-y-6">
        {/* File Upload */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            1. Select a file to convert
          </label>
          <div
            {...getRootProps()}
            className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md cursor-pointer
              ${isDragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-300 dark:border-gray-700'}`}
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
              <div className="flex text-sm text-gray-600 dark:text-gray-400">
                <span className="relative rounded-md font-medium text-primary-600 dark:text-primary-400 hover:text-primary-500">
                  Upload a file
                </span>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {selectedFile ? selectedFile.name : 'Any file supported by our converters'}
              </p>
            </div>
          </div>
        </div>

        {/* Format Categories */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            2. File Type Category
          </label>
          <div className="mt-1 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.keys(FORMAT_CATEGORIES).map((category) => (
              <button
                key={category}
                type="button"
                className={`px-3 py-2 text-sm font-medium rounded-md transition-colors
                  ${currentCategory === category
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                onClick={() => {
                  setCurrentCategory(category);
                  setSourceFormat('');
                  setTargetFormat('');
                }}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Source Format */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            3. Source Format
          </label>
          <select
            className="form-select"
            value={sourceFormat}
            onChange={(e) => {
              setSourceFormat(e.target.value);
              setTargetFormat('');
            }}
            disabled={!formats || loading}
          >
            <option value="">Select source format</option>
            {formats && FORMAT_CATEGORIES[currentCategory].filter(format => Object.keys(formats).includes(format)).map((format) => (
              <option key={format} value={format}>
                {format.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {/* Target Format */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            4. Target Format
          </label>
          <select
            className="form-select"
            value={targetFormat}
            onChange={(e) => setTargetFormat(e.target.value)}
            disabled={!sourceFormat || !formats || loading}
          >
            <option value="">Select target format</option>
            {sourceFormat && formats && getAvailableTargetFormats().map((format) => (
              <option key={format} value={format}>
                {format.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        
        {/* Advanced Options Toggle */}
        <div className="flex items-center">
          <button
            type="button"
            className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-500 focus:outline-none focus:underline"
            onClick={() => setAdvancedOptions(!advancedOptions)}
          >
            {advancedOptions ? '- Hide advanced options' : '+ Show advanced options'}
          </button>
        </div>
        
        {/* Format-specific Options */}
        {renderFormatOptions()}
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}
        
        {/* Progress Bar */}
        {loading && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>Converting...</span>
              <span>{progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4 text-sm text-green-600 dark:text-green-400">
            File converted successfully!
          </div>
        )}

        {/* Form Actions */}
        <div className="flex space-x-3">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!selectedFile || !sourceFormat || !targetFormat || loading}
          >
            {loading ? <Spinner size="sm" /> : 'Convert'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={handleReset}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConversionForm; 