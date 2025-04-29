import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Slider,
  TextField,
  FormControlLabel,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Tooltip,
  IconButton,
  Paper
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { ConversionOption, COMMON_OPTIONS } from '../types/converters';
import apiService from '../utils/api';

interface ConversionOptionsProps {
  sourceFormat: string;
  targetFormat: string;
  onChange: (options: Record<string, any>) => void;
}

const ConversionOptions: React.FC<ConversionOptionsProps> = ({ 
  sourceFormat, 
  targetFormat, 
  onChange 
}) => {
  const [options, setOptions] = useState<Record<string, ConversionOption>>({});
  const [values, setValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Reset options when formats change
    setValues({});
    setError(null);
    
    if (!sourceFormat || !targetFormat) {
      return;
    }
    
    // Determine category based on formats
    const determineCategory = (format: string): string => {
      // These checks are simplified - in a real app, you might want to 
      // fetch this information from the backend
      const format_categories: Record<string, string[]> = {
        document: ['pdf', 'docx', 'doc', 'txt', 'md', 'markdown', 'html', 'rtf'],
        image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico'],
        audio: ['mp3', 'wav', 'ogg', 'flac', 'aac'],
        video: ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm'],
        data: ['json', 'xml', 'yaml', 'yml', 'csv', 'xlsx', 'xls']
      };
      
      for (const [category, formats] of Object.entries(format_categories)) {
        if (formats.includes(format)) {
          return category;
        }
      }
      return 'other';
    };
    
    const sourceCategory = determineCategory(sourceFormat);
    const targetCategory = determineCategory(targetFormat);
    
    // Get common options for this conversion type
    let defaultOptions: Record<string, ConversionOption> = {};
    
    if (sourceCategory === 'image' && targetCategory === 'image') {
      defaultOptions = { ...COMMON_OPTIONS.image };
    } else if (sourceCategory === 'document' || targetCategory === 'document') {
      defaultOptions = { ...COMMON_OPTIONS.document };
    } else if (sourceCategory === 'audio' && targetCategory === 'audio') {
      defaultOptions = { ...COMMON_OPTIONS.audio };
    } else if (sourceCategory === 'video' && targetCategory === 'video') {
      defaultOptions = { ...COMMON_OPTIONS.video };
    } else if (sourceCategory === 'data' && targetCategory === 'data') {
      defaultOptions = { ...COMMON_OPTIONS.data };
    }
    
    // Special case for specific format conversions
    if (sourceFormat === 'pdf' && targetCategory === 'image') {
      defaultOptions.dpi = {
        name: 'dpi',
        type: 'number',
        label: 'DPI',
        description: 'Resolution in dots per inch',
        default: 200,
        min: 72,
        max: 600
      };
      defaultOptions.page_numbers = {
        name: 'page_numbers',
        type: 'string',
        label: 'Pages',
        description: 'Page numbers to convert (e.g., 1,3-5)',
        default: ''
      };
    } else if (sourceFormat === 'markdown' && targetFormat === 'pdf') {
      defaultOptions.toc = {
        name: 'toc',
        type: 'boolean',
        label: 'Table of Contents',
        description: 'Include table of contents',
        default: false
      };
      defaultOptions.highlight_style = {
        name: 'highlight_style',
        type: 'select',
        label: 'Code Highlighting Style',
        description: 'Style for code highlighting',
        default: 'github',
        options: [
          { value: 'github', label: 'GitHub' },
          { value: 'monokai', label: 'Monokai' },
          { value: 'solarized-light', label: 'Solarized Light' },
          { value: 'solarized-dark', label: 'Solarized Dark' }
        ]
      };
    } else if (sourceFormat === 'xlsx' || sourceFormat === 'xls') {
      defaultOptions.sheet_name = {
        name: 'sheet_name',
        type: 'string',
        label: 'Sheet Name',
        description: 'Name of sheet to convert (optional)',
        default: ''
      };
      defaultOptions.sheet_index = {
        name: 'sheet_index',
        type: 'number',
        label: 'Sheet Index',
        description: 'Index of sheet to convert (starting from 0)',
        default: 0,
        min: 0
      };
    }
    
    // Set default options before API call
    setOptions(defaultOptions);
    
    // Set default values
    const defaultValues: Record<string, any> = {};
    Object.values(defaultOptions).forEach(option => {
      defaultValues[option.name] = option.default;
    });
    
    setValues(defaultValues);
    
    // Notify parent component about default values
    onChange(defaultValues);
    
    // Fetch specific conversion options from backend
    setLoading(true);
    apiService.get<Record<string, any>>(
      `/api/formats/options?source=${sourceFormat}&target=${targetFormat}`
    )
    .then(response => {
      // Convert API response to our format if needed
      const apiOptions: Record<string, ConversionOption> = {};
      
      Object.entries(response).forEach(([key, value]) => {
        // Ensure the value has the expected structure
        if (typeof value === 'object' && value !== null && 'type' in value) {
          const option = value as any;
          apiOptions[key] = {
            name: key,
            type: option.type,
            label: option.label || key,
            description: option.description || '',
            default: option.default,
            min: option.min,
            max: option.max,
            options: Array.isArray(option.options) 
              ? option.options.map((opt: string) => ({ value: opt, label: opt }))
              : undefined
          };
        }
      });
      
      // Merge with default options, with API taking precedence
      const mergedOptions = { ...defaultOptions, ...apiOptions };
      setOptions(mergedOptions);
      
      // Update values with API defaults
      const newValues = { ...defaultValues };
      Object.values(apiOptions).forEach(option => {
        if (option.default !== undefined) {
          newValues[option.name] = option.default;
        }
      });
      
      setValues(newValues);
      onChange(newValues);
      setError(null);
    })
    .catch(error => {
      console.error('Failed to fetch conversion options:', error);
      setError('Failed to load options from server. Using defaults instead.');
      // We still have the default options set above
    })
    .finally(() => {
      setLoading(false);
    });
  }, [sourceFormat, targetFormat, onChange]);

  const handleOptionChange = (name: string, value: any) => {
    setValues(prev => {
      const newValues = { ...prev, [name]: value };
      onChange(newValues);
      return newValues;
    });
  };

  const resetToDefaults = () => {
    const defaultValues: Record<string, any> = {};
    Object.values(options).forEach(option => {
      defaultValues[option.name] = option.default;
    });
    
    setValues(defaultValues);
    onChange(defaultValues);
  };

  const renderOption = (option: ConversionOption) => {
    switch (option.type) {
      case 'number':
        return (
          <Box key={option.name} sx={{ my: 2 }}>
            <Box display="flex" alignItems="center">
              <Typography gutterBottom>{option.label}</Typography>
              <Tooltip title={option.description || ''}>
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoOutlinedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            {option.min !== undefined && option.max !== undefined ? (
              <>
                <Slider
                  value={values[option.name] !== undefined ? values[option.name] : option.default}
                  onChange={(_, value) => handleOptionChange(option.name, value)}
                  min={option.min}
                  max={option.max}
                  valueLabelDisplay="auto"
                  aria-labelledby={`${option.name}-slider`}
                />
                <Typography variant="caption" color="text.secondary">
                  {values[option.name] !== undefined ? values[option.name] : option.default}
                </Typography>
              </>
            ) : (
              <TextField
                type="number"
                value={values[option.name] !== undefined ? values[option.name] : option.default}
                onChange={(e) => handleOptionChange(option.name, Number(e.target.value))}
                fullWidth
                variant="outlined"
                size="small"
              />
            )}
          </Box>
        );
        
      case 'string':
        return (
          <Box key={option.name} sx={{ my: 2 }}>
            <Box display="flex" alignItems="center">
              <Typography gutterBottom>{option.label}</Typography>
              <Tooltip title={option.description || ''}>
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoOutlinedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            <TextField
              value={values[option.name] !== undefined ? values[option.name] : (option.default || '')}
              onChange={(e) => handleOptionChange(option.name, e.target.value)}
              fullWidth
              variant="outlined"
              size="small"
              placeholder={option.description}
            />
          </Box>
        );
        
      case 'boolean':
        return (
          <Box key={option.name} sx={{ my: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={values[option.name] !== undefined ? values[option.name] : (option.default || false)}
                  onChange={(e) => handleOptionChange(option.name, e.target.checked)}
                />
              }
              label={
                <Box display="flex" alignItems="center">
                  <Typography>{option.label}</Typography>
                  <Tooltip title={option.description || ''}>
                    <IconButton size="small" sx={{ ml: 1 }}>
                      <InfoOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              }
            />
          </Box>
        );
        
      case 'select':
        return (
          <Box key={option.name} sx={{ my: 2 }}>
            <Box display="flex" alignItems="center">
              <Typography gutterBottom>{option.label}</Typography>
              <Tooltip title={option.description || ''}>
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoOutlinedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            <FormControl fullWidth size="small">
              <Select
                value={values[option.name] !== undefined ? values[option.name] : option.default}
                onChange={(e) => handleOptionChange(option.name, e.target.value)}
                displayEmpty
              >
                {option.options?.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        );
        
      default:
        return null;
    }
  };

  if (Object.keys(options).length === 0 && !loading) {
    return null;
  }

  return (
    <Paper elevation={0} sx={{ my: 2, p: 0, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
      <Accordion defaultExpanded>
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon />}
          sx={{ 
            borderBottom: '1px solid',
            borderColor: 'divider',
            '&.Mui-expanded': {
              minHeight: 48,
            }
          }}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
            <Typography variant="subtitle1">Conversion Options</Typography>
            {Object.keys(options).length > 0 && (
              <Tooltip title="Reset to defaults">
                <IconButton 
                  size="small" 
                  onClick={(e) => {
                    e.stopPropagation();
                    resetToDefaults();
                  }}
                  sx={{ mr: 2 }}
                >
                  <RestartAltIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 2 }}>
          {loading ? (
            <Box display="flex" alignItems="center" justifyContent="center" p={2}>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              <Typography>Loading options...</Typography>
            </Box>
          ) : error ? (
            <Box sx={{ bgcolor: 'error.light', p: 2, borderRadius: 1 }}>
              <Typography color="error">{error}</Typography>
            </Box>
          ) : Object.keys(options).length === 0 ? (
            <Typography>No options available for this conversion.</Typography>
          ) : (
            Object.values(options).map(option => renderOption(option))
          )}
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
};

export default ConversionOptions; 