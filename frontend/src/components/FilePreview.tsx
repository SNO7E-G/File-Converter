import React, { useState } from 'react';
import { rawApi } from '../utils/api';

interface FilePreviewProps {
  fileUrl: string;
  fileName: string;
  fileType: string;
  className?: string;
}

const FilePreview: React.FC<FilePreviewProps> = ({ 
  fileUrl, 
  fileName, 
  fileType, 
  className = '' 
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper to determine the file category based on extension
  const getFileCategory = (): 'image' | 'audio' | 'video' | 'document' | 'other' => {
    const extension = fileName.split('.').pop()?.toLowerCase() || '';
    
    const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'];
    const audioExtensions = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'];
    const videoExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'];
    const documentExtensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'csv', 'xls', 'xlsx', 'json', 'xml', 'yaml', 'yml'];
    
    if (imageExtensions.includes(extension)) return 'image';
    if (audioExtensions.includes(extension)) return 'audio';
    if (videoExtensions.includes(extension)) return 'video';
    if (documentExtensions.includes(extension)) return 'document';
    
    return 'other';
  };

  const handleLoadStart = () => setIsLoading(true);
  const handleLoadComplete = () => setIsLoading(false);
  const handleError = () => {
    setIsLoading(false);
    setError('Failed to load preview');
  };

  const fileCategory = getFileCategory();
  const fullUrl = fileUrl.startsWith('http') ? fileUrl : `${rawApi.defaults.baseURL}${fileUrl}`;

  // Render based on file type
  const renderPreview = () => {
    switch (fileCategory) {
      case 'image':
        return (
          <div className="flex items-center justify-center">
            <img 
              src={fullUrl} 
              alt={fileName}
              className="max-w-full max-h-[500px] object-contain"
              onLoad={handleLoadComplete}
              onError={handleError}
            />
          </div>
        );
      
      case 'audio':
        return (
          <div className="p-4 flex flex-col items-center">
            <div className="w-full max-w-md">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6 flex flex-col items-center">
                <div className="rounded-full bg-primary-100 dark:bg-primary-900/30 p-4 mb-4">
                  <svg className="w-10 h-10 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{fileName}</h3>
                <audio 
                  controls 
                  className="w-full mt-2" 
                  onLoadStart={handleLoadStart}
                  onLoadedData={handleLoadComplete}
                  onError={handleError}
                >
                  <source src={fullUrl} type={`audio/${fileType}`} />
                  Your browser does not support the audio element.
                </audio>
              </div>
            </div>
          </div>
        );
      
      case 'video':
        return (
          <div className="p-4 flex flex-col items-center">
            <div className="w-full max-w-2xl">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{fileName}</h3>
              <video 
                controls 
                className="w-full rounded-lg shadow-lg" 
                onLoadStart={handleLoadStart}
                onLoadedData={handleLoadComplete}
                onError={handleError}
              >
                <source src={fullUrl} type={`video/${fileType}`} />
                Your browser does not support the video element.
              </video>
            </div>
          </div>
        );
      
      case 'document':
        if (fileType === 'pdf') {
          return (
            <div className="p-4 flex flex-col items-center">
              <div className="w-full h-[600px]">
                <iframe 
                  src={`${fullUrl}#toolbar=0`} 
                  className="w-full h-full border-none rounded-lg shadow-lg"
                  onLoad={handleLoadComplete}
                  onError={handleError}
                  title={fileName}
                />
              </div>
            </div>
          );
        }
        
        return (
          <div className="p-4 flex flex-col items-center">
            <div className="w-full max-w-md">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6 flex flex-col items-center">
                <div className="rounded-full bg-primary-100 dark:bg-primary-900/30 p-4 mb-4">
                  <svg className="w-10 h-10 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{fileName}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
                  Document preview not available
                </p>
                <a 
                  href={fullUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                  onClick={() => handleLoadComplete()}
                >
                  Open Document
                </a>
              </div>
            </div>
          </div>
        );
      
      default:
        // Generic file preview (download link)
        return (
          <div className="p-4 flex flex-col items-center">
            <div className="w-full max-w-md">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6 flex flex-col items-center">
                <div className="rounded-full bg-gray-200 dark:bg-gray-700 p-4 mb-4">
                  <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{fileName}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
                  Preview not available for this file type
                </p>
                <a 
                  href={fullUrl}
                  download={fileName}
                  className="btn btn-primary"
                  onClick={() => handleLoadComplete()}
                >
                  Download
                </a>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`relative ${className}`}>
      {renderPreview()}
      
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-gray-900/70">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-gray-900/70">
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 max-w-md">
            <p className="text-red-700 dark:text-red-300">{error}</p>
            <p className="text-sm text-red-500 dark:text-red-400 mt-2">
              Try downloading the file instead.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilePreview; 