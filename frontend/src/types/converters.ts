export interface FormatCategory {
  document: Record<string, FormatConversions>;
  image: Record<string, FormatConversions>;
  audio: Record<string, FormatConversions>;
  video: Record<string, FormatConversions>;
  data: Record<string, FormatConversions>;
}

export interface FormatConversions {
  can_convert_from: string[];
  can_convert_to: string[];
}

export interface ConversionOption {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select';
  label: string;
  description?: string;
  default?: any;
  min?: number;
  max?: number;
  options?: Array<{ value: any; label: string }>;
}

export interface FormatDetails {
  name: string;
  description: string;
  extensions: string[];
  mime_types: string[];
  category: string;
  options: Record<string, ConversionOption>;
}

// Mapping of file extensions to human-readable format names
export const FORMAT_NAMES: Record<string, string> = {
  // Document formats
  'pdf': 'PDF Document',
  'docx': 'Word Document',
  'doc': 'Word Document (Legacy)',
  'txt': 'Text File',
  'md': 'Markdown',
  'markdown': 'Markdown',
  'html': 'HTML Document',
  'rtf': 'Rich Text Format',
  
  // Data formats
  'json': 'JSON',
  'xml': 'XML',
  'yaml': 'YAML',
  'yml': 'YAML',
  'csv': 'CSV Spreadsheet',
  'xlsx': 'Excel Spreadsheet',
  'xls': 'Excel Spreadsheet (Legacy)',
  
  // Image formats
  'jpg': 'JPEG Image',
  'jpeg': 'JPEG Image',
  'png': 'PNG Image',
  'gif': 'GIF Image',
  'bmp': 'Bitmap Image',
  'webp': 'WebP Image',
  'svg': 'SVG Vector Image',
  'tiff': 'TIFF Image',
  'ico': 'Icon File',
  
  // Audio formats
  'mp3': 'MP3 Audio',
  'wav': 'WAV Audio',
  'ogg': 'OGG Audio',
  'flac': 'FLAC Audio',
  'aac': 'AAC Audio',
  
  // Video formats
  'mp4': 'MP4 Video',
  'avi': 'AVI Video',
  'mov': 'QuickTime Video',
  'wmv': 'Windows Media Video',
  'mkv': 'Matroska Video',
  'webm': 'WebM Video'
};

// Format category icons
export const CATEGORY_ICONS: Record<string, string> = {
  document: 'file-text',
  image: 'image',
  audio: 'music',
  video: 'video',
  data: 'database'
};

// Common conversion options by category
export const COMMON_OPTIONS: Record<string, Record<string, ConversionOption>> = {
  image: {
    quality: {
      name: 'quality',
      type: 'number',
      label: 'Quality',
      description: 'Image quality (1-100)',
      default: 90,
      min: 1,
      max: 100
    },
    resize: {
      name: 'resize',
      type: 'string',
      label: 'Resize',
      description: 'Resize image (WxH)',
      default: ''
    },
    grayscale: {
      name: 'grayscale',
      type: 'boolean',
      label: 'Grayscale',
      description: 'Convert to grayscale',
      default: false
    }
  },
  document: {
    toc: {
      name: 'toc',
      type: 'boolean',
      label: 'Table of Contents',
      description: 'Include table of contents',
      default: false
    }
  },
  audio: {
    bitrate: {
      name: 'bitrate',
      type: 'select',
      label: 'Bitrate',
      description: 'Audio bitrate',
      default: '192k',
      options: [
        { value: '128k', label: '128 kbps' },
        { value: '192k', label: '192 kbps' },
        { value: '256k', label: '256 kbps' },
        { value: '320k', label: '320 kbps' }
      ]
    }
  },
  video: {
    resolution: {
      name: 'resolution',
      type: 'select',
      label: 'Resolution',
      description: 'Video resolution',
      default: '720p',
      options: [
        { value: '480p', label: '480p' },
        { value: '720p', label: '720p (HD)' },
        { value: '1080p', label: '1080p (Full HD)' },
        { value: '2160p', label: '2160p (4K)' }
      ]
    }
  },
  data: {
    indent: {
      name: 'indent',
      type: 'number',
      label: 'Indentation',
      description: 'Number of spaces for indentation',
      default: 2,
      min: 0,
      max: 8
    }
  }
}; 