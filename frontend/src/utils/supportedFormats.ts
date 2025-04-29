import { SupportedFormats } from './api';

/**
 * Comprehensive mapping of source formats to their available target formats
 */
export const supportedFormats: SupportedFormats = {
  // Document formats
  'pdf': ['docx', 'jpg', 'png', 'html', 'txt'],
  'docx': ['pdf', 'txt', 'html', 'epub', 'rtf'],
  'txt': ['pdf', 'docx', 'html', 'rtf'],
  'rtf': ['pdf', 'docx', 'txt', 'html'],
  'epub': ['pdf', 'docx', 'html'],
  'html': ['pdf', 'docx', 'txt'],
  
  // Image formats
  'jpg': ['png', 'webp', 'pdf', 'svg', 'gif'],
  'jpeg': ['png', 'webp', 'pdf', 'svg', 'gif'],
  'png': ['jpg', 'webp', 'pdf', 'svg', 'gif'],
  'gif': ['jpg', 'png', 'webp', 'mp4'],
  'svg': ['png', 'jpg', 'pdf'],
  'webp': ['jpg', 'png', 'pdf'],
  'bmp': ['jpg', 'png', 'pdf'],
  'tiff': ['jpg', 'png', 'pdf'],
  
  // Audio formats
  'mp3': ['wav', 'ogg', 'flac', 'aac'],
  'wav': ['mp3', 'ogg', 'flac', 'aac'],
  'flac': ['mp3', 'wav', 'ogg', 'aac'],
  'ogg': ['mp3', 'wav', 'flac', 'aac'],
  'aac': ['mp3', 'wav', 'ogg'],
  
  // Video formats
  'mp4': ['mkv', 'avi', 'webm', 'gif'],
  'mkv': ['mp4', 'avi', 'webm'],
  'avi': ['mp4', 'mkv', 'webm'],
  'webm': ['mp4', 'mkv', 'avi'],
  'mov': ['mp4', 'mkv', 'avi', 'webm'],
  
  // Archive formats
  'zip': ['7z', 'tar', 'rar', 'gz'],
  '7z': ['zip', 'tar', 'gz'],
  'rar': ['zip', '7z', 'tar', 'gz'],
  'tar': ['zip', '7z', 'gz'],
  'gz': ['zip', '7z', 'tar'],
  
  // Spreadsheet formats
  'xlsx': ['csv', 'pdf', 'html', 'json'],
  'xls': ['xlsx', 'csv', 'pdf', 'html', 'json'],
  'csv': ['xlsx', 'json', 'pdf', 'html'],
  
  // Presentation formats
  'pptx': ['pdf', 'jpg', 'png'],
  'ppt': ['pptx', 'pdf', 'jpg', 'png'],
  
  // CAD formats
  'dwg': ['pdf', 'dxf', 'svg'],
  'dxf': ['pdf', 'dwg', 'svg'],
  
  // 3D formats
  'obj': ['stl', 'fbx', 'glb'],
  'stl': ['obj', 'fbx', 'glb'],
  'fbx': ['obj', 'stl', 'glb'],
  'glb': ['obj', 'stl', 'fbx'],
};

/**
 * Format categories for grouping in UI
 */
export const formatCategories = {
  document: ['pdf', 'docx', 'txt', 'rtf', 'epub', 'html'],
  image: ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'tiff'],
  audio: ['mp3', 'wav', 'flac', 'ogg', 'aac'],
  video: ['mp4', 'mkv', 'avi', 'webm', 'mov'],
  archive: ['zip', '7z', 'rar', 'tar', 'gz'],
  spreadsheet: ['xlsx', 'xls', 'csv'],
  presentation: ['pptx', 'ppt'],
  cad: ['dwg', 'dxf'],
  threeD: ['obj', 'stl', 'fbx', 'glb'],
};

/**
 * Get file format from filename
 * @param filename - The name of the file
 * @returns The file format (extension) in lowercase
 */
export const getFileFormat = (filename: string): string => {
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
};

/**
 * Check if source format can be converted to target format
 * @param sourceFormat - The source format
 * @param targetFormat - The target format
 * @returns Boolean indicating if conversion is supported
 */
export const isConversionSupported = (sourceFormat: string, targetFormat: string): boolean => {
  const source = sourceFormat.toLowerCase();
  const target = targetFormat.toLowerCase();
  
  // Check if source format is supported
  if (!supportedFormats[source]) {
    return false;
  }
  
  // Check if target format is supported for the source
  return supportedFormats[source].includes(target);
};

/**
 * Get all target formats available for a source format
 * @param sourceFormat - The source format
 * @returns Array of available target formats, or empty array if source not supported
 */
export const getAvailableTargetFormats = (sourceFormat: string): string[] => {
  const source = sourceFormat.toLowerCase();
  return supportedFormats[source] || [];
};

/**
 * Get all supported source formats
 * @returns Array of all supported source formats
 */
export const getAllSourceFormats = (): string[] => {
  return Object.keys(supportedFormats);
};

/**
 * Check if a format is supported as a source
 * @param format - The format to check
 * @returns Boolean indicating if format is supported as a source
 */
export const isFormatSupported = (format: string): boolean => {
  return !!supportedFormats[format.toLowerCase()];
};

/**
 * Get file type icon name based on format
 * @param format - The file format
 * @returns Icon name for the format
 */
export const getFormatIconName = (format: string): string => {
  const lowerFormat = format.toLowerCase();
  
  // Document formats
  if (formatCategories.document.includes(lowerFormat)) {
    return 'document';
  }
  
  // Image formats
  if (formatCategories.image.includes(lowerFormat)) {
    return 'image';
  }
  
  // Audio formats
  if (formatCategories.audio.includes(lowerFormat)) {
    return 'audio';
  }
  
  // Video formats
  if (formatCategories.video.includes(lowerFormat)) {
    return 'video';
  }
  
  // Archive formats
  if (formatCategories.archive.includes(lowerFormat)) {
    return 'archive';
  }
  
  // Spreadsheet formats
  if (formatCategories.spreadsheet.includes(lowerFormat)) {
    return 'spreadsheet';
  }
  
  // Presentation formats
  if (formatCategories.presentation.includes(lowerFormat)) {
    return 'presentation';
  }
  
  // CAD formats
  if (formatCategories.cad.includes(lowerFormat)) {
    return 'cad';
  }
  
  // 3D formats
  if (formatCategories.threeD.includes(lowerFormat)) {
    return '3d';
  }
  
  // Default
  return 'file';
};

/**
 * Get human-readable format name
 * @param format - The file format
 * @returns Human-readable format name
 */
export const getFormatName = (format: string): string => {
  const formatMap: Record<string, string> = {
    'pdf': 'PDF Document',
    'docx': 'Word Document',
    'txt': 'Text File',
    'rtf': 'Rich Text Document',
    'epub': 'E-Book',
    'html': 'HTML Document',
    'jpg': 'JPEG Image',
    'jpeg': 'JPEG Image',
    'png': 'PNG Image',
    'gif': 'GIF Image',
    'svg': 'SVG Vector Image',
    'webp': 'WebP Image',
    'bmp': 'Bitmap Image',
    'tiff': 'TIFF Image',
    'mp3': 'MP3 Audio',
    'wav': 'WAV Audio',
    'flac': 'FLAC Audio',
    'ogg': 'OGG Audio',
    'aac': 'AAC Audio',
    'mp4': 'MP4 Video',
    'mkv': 'MKV Video',
    'avi': 'AVI Video',
    'webm': 'WebM Video',
    'mov': 'QuickTime Video',
    'zip': 'ZIP Archive',
    '7z': '7-Zip Archive',
    'rar': 'RAR Archive',
    'tar': 'TAR Archive',
    'gz': 'GZip Archive',
    'xlsx': 'Excel Spreadsheet',
    'xls': 'Excel Spreadsheet (Legacy)',
    'csv': 'CSV Spreadsheet',
    'pptx': 'PowerPoint Presentation',
    'ppt': 'PowerPoint Presentation (Legacy)',
    'dwg': 'AutoCAD Drawing',
    'dxf': 'CAD Exchange Format',
    'obj': '3D Object',
    'stl': '3D STL Model',
    'fbx': '3D FBX Model',
    'glb': '3D GLB Model',
  };
  
  return formatMap[format.toLowerCase()] || format.toUpperCase();
};

export default supportedFormats; 