import React, { useEffect, useState } from 'react';
import { SupportedFormats } from '../utils/api';
import api from '../utils/api';

interface SupportedFormatsProps {
  onFormatChange?: (formats: SupportedFormats) => void;
}

const SupportedFormats: React.FC<SupportedFormatsProps> = ({ onFormatChange }) => {
  const [formats, setFormats] = useState<SupportedFormats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFormats = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/formats');
        setFormats(response.data.formats);
        if (onFormatChange) {
          onFormatChange(response.data.formats);
        }
      } catch (err) {
        setError('Failed to load supported formats');
        console.error('Error fetching formats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFormats();
  }, [onFormatChange]);

  if (loading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-sm text-red-600 dark:text-red-400">
        {error}
      </div>
    );
  }

  if (!formats) {
    return null;
  }

  return (
    <div className="mt-4">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
        Supported Conversion Formats
      </h3>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        {Object.entries(formats).map(([sourceFormat, targetFormats]) => (
          <div key={sourceFormat} className="mb-4 last:mb-0">
            <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-2">
              From {sourceFormat.toUpperCase()}:
            </h4>
            <div className="flex flex-wrap gap-2">
              {targetFormats.map((format) => (
                <span 
                  key={format} 
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-800 dark:text-primary-100"
                >
                  {format.toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SupportedFormats; 