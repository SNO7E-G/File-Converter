import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface FileDropzoneProps {
  onFileSelect: (files: File[]) => void;
  multiple?: boolean;
  maxFiles?: number;
  maxSize?: number;
  accept?: Record<string, string[]>;
  className?: string;
  disabled?: boolean;
}

const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFileSelect,
  multiple = false,
  maxFiles = 1,
  maxSize = 50 * 1024 * 1024, // 50MB
  accept,
  className = '',
  disabled = false,
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errorMessages = rejectedFiles.map(({ file, errors }) => {
        return errors.map((e: any) => {
          if (e.code === 'file-too-large') {
            return `"${file.name}" is too large. Max size is ${formatBytes(maxSize)}.`;
          }
          if (e.code === 'file-invalid-type') {
            return `"${file.name}" has an invalid file type.`;
          }
          if (e.code === 'too-many-files') {
            return `Too many files. Max is ${maxFiles}.`;
          }
          return `"${file.name}": ${e.message}`;
        }).join(', ');
      }).join('. ');

      setError(errorMessages);
      return;
    }

    setError(null);

    // If not multiple, replace files
    const newFiles = multiple ? [...files, ...acceptedFiles] : acceptedFiles;
    
    // Limit to maxFiles
    const limitedFiles = newFiles.slice(0, maxFiles);
    
    setFiles(limitedFiles);
    onFileSelect(limitedFiles);
  }, [files, maxFiles, maxSize, multiple, onFileSelect]);

  const removeFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
    onFileSelect(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple,
    maxFiles,
    maxSize,
    accept,
    disabled,
  });

  // Format bytes to readable format
  function formatBytes(bytes: number, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  return (
    <div className={`w-full ${className}`}>
      <div
        {...getRootProps()}
        className={`flex flex-col items-center justify-center w-full border-2 border-dashed rounded-lg p-6 
          ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
            : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}
      >
        <input {...getInputProps()} />
        <CloudArrowUpIcon className="h-12 w-12 text-gray-400 dark:text-gray-500 mb-3" />
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {disabled 
            ? 'File upload disabled'
            : isDragActive
              ? 'Drop the files here...'
              : `Drag & drop ${multiple ? 'files' : 'a file'} here, or click to select ${multiple ? 'files' : 'a file'}`}
        </p>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          {multiple ? `Up to ${maxFiles} files` : 'Only one file'}, max {formatBytes(maxSize)} each
        </p>
      </div>

      {error && (
        <div className="mt-2 text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {files.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Selected {files.length} {files.length === 1 ? 'file' : 'files'}:
          </h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded p-2">
                <div className="flex items-center overflow-hidden">
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                      {file.name.split('.').pop() || 'file'}
                    </span>
                  </div>
                  <div className="ml-2 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatBytes(file.size)}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-2 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
                  disabled={disabled}
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default FileDropzone; 