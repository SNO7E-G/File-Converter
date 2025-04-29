import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import FileDropzone from '../components/FileDropzone';
import SupportedFormats from '../components/SupportedFormats';
import { SupportedFormats as SupportedFormatsType, ConversionRequest } from '../utils/api';
import api from '../utils/api';

const ConvertPage: React.FC = () => {
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceFormat, setSourceFormat] = useState<string>('');
  const [targetFormat, setTargetFormat] = useState<string>('');
  const [availableTargetFormats, setAvailableTargetFormats] = useState<string[]>([]);
  const [supportedFormats, setSupportedFormats] = useState<SupportedFormatsType | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [conversionResult, setConversionResult] = useState<{ id: number, downloadUrl: string } | null>(null);

  // When supported formats are loaded, store them
  const handleFormatsChange = (formats: SupportedFormatsType) => {
    setSupportedFormats(formats);
  };

  // When file is selected, determine its format and available target formats
  useEffect(() => {
    if (selectedFile) {
      const format = getSourceFormatName();
      setSourceFormat(format);
      
      const targetFormats = getAvailableTargetFormats();
      setAvailableTargetFormats(targetFormats);
      
      if (targetFormats.length > 0) {
        setTargetFormat(targetFormats[0]);
      }
    } else {
      setSourceFormat('');
      setTargetFormat('');
      setAvailableTargetFormats([]);
    }
  }, [selectedFile, supportedFormats]);

  const getAvailableTargetFormats = (): string[] => {
    if (!selectedFile || !supportedFormats) return [];
    
    const format = getSourceFormatName();
    return supportedFormats[format] || [];
  };

  const handleFileSelect = (files: File[]) => {
    setSelectedFile(files[0] || null);
    setConversionResult(null);
    setConversionError(null);
  };

  const handleConvert = async () => {
    if (!selectedFile || !targetFormat) return;
    
    setIsConverting(true);
    setConversionError(null);
    
    // Create form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const requestData: ConversionRequest = {
      target_format: targetFormat,
    };
    
    formData.append('data', JSON.stringify(requestData));
    
    try {
      const response = await api.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setConversionResult({
        id: response.data.conversion.id,
        downloadUrl: `/api/conversions/${response.data.conversion.id}/download`,
      });
    } catch (error: any) {
      console.error('Conversion error:', error);
      setConversionError(error.response?.data?.error || 'An error occurred during conversion');
    } finally {
      setIsConverting(false);
    }
  };

  const handleDownload = () => {
    if (!conversionResult) return;
    
    window.open(`${api.defaults.baseURL}${conversionResult.downloadUrl}`, '_blank');
  };

  const getSourceFormatName = (): string => {
    if (!selectedFile) return '';
    
    const extension = selectedFile.name.split('.').pop()?.toLowerCase() || '';
    
    // Map extension to format name
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

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Convert Files</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Select a File to Convert
          </h2>
          
          <FileDropzone
            onFileSelect={handleFileSelect}
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
          
          {selectedFile && sourceFormat && (
            <div className="mt-6">
              <h3 className="text-md font-medium text-gray-900 dark:text-white mb-3">
                Convert to:
              </h3>
              
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                {availableTargetFormats.map((format) => (
                  <div key={format} className="relative">
                    <input
                      type="radio"
                      id={`format-${format}`}
                      name="targetFormat"
                      value={format}
                      checked={targetFormat === format}
                      onChange={() => setTargetFormat(format)}
                      className="peer sr-only"
                    />
                    <label
                      htmlFor={`format-${format}`}
                      className="flex items-center justify-center p-3 border-2 rounded-lg cursor-pointer text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:text-gray-600 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 peer-checked:border-primary-500 peer-checked:text-primary-600 dark:peer-checked:text-primary-400"
                    >
                      {format.toUpperCase()}
                    </label>
                  </div>
                ))}
              </div>
              
              <div className="mt-6">
                <button
                  type="button"
                  onClick={handleConvert}
                  disabled={isConverting || !targetFormat}
                  className="btn btn-primary w-full"
                >
                  {isConverting ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Converting...
                    </div>
                  ) : (
                    `Convert to ${targetFormat.toUpperCase()}`
                  )}
                </button>
              </div>
            </div>
          )}
          
          {conversionError && (
            <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-sm text-red-600 dark:text-red-400">
              {conversionError}
            </div>
          )}
          
          {conversionResult && (
            <div className="mt-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
              <h3 className="text-md font-medium text-green-800 dark:text-green-200 mb-2">
                Conversion Complete!
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300 mb-4">
                Your file has been successfully converted.
              </p>
              <button
                type="button"
                onClick={handleDownload}
                className="btn btn-success"
              >
                Download Converted File
              </button>
            </div>
          )}
        </div>
        
        <SupportedFormats onFormatChange={handleFormatsChange} />
        
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Conversion Limits
          </h2>
          
          <div className="text-sm text-gray-600 dark:text-gray-300">
            <p>
              {user?.tier === 'premium' 
                ? 'Premium tier: Up to 100 conversions per day.' 
                : 'Free tier: Up to 5 conversions per day. Upgrade to Premium for more!'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConvertPage; 