from flask import current_app
import os
import logging
import time
from functools import lru_cache
from typing import Dict, List, Type, Optional
import importlib
import inspect

from app.converters.base_converter import BaseConverter

# Set up logging
logger = logging.getLogger(__name__)

class ConverterFactory:
    """
    Factory class for file converters.
    This class manages the registration and retrieval of converters.
    It also helps determine the best conversion path between formats.
    """
    
    _instance = None
    _converters = {}
    _converter_classes = {}
    _conversion_graph = {}
    
    # Supported formats grouped by type
    DOCUMENT_FORMATS = ['pdf', 'docx', 'doc', 'odt', 'txt', 'md', 'markdown', 'html', 'rtf']
    IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg']
    AUDIO_FORMATS = ['mp3', 'wav', 'ogg', 'flac', 'aac']
    VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm']
    DATA_FORMATS = ['json', 'xml', 'yaml', 'yml', 'csv', 'xlsx', 'xls']
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConverterFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the factory and register all available converters"""
        self._converters = {}
        self._converter_classes = {}
        self._conversion_graph = {}
        
        # Auto-discover converters in the converters package
        self._discover_converters()
    
    def _discover_converters(self):
        """
        Automatically discover and register converter classes in the converters package
        """
        import app.converters
        
        converters_dir = os.path.dirname(app.converters.__file__)
        
        for filename in os.listdir(converters_dir):
            if filename.endswith('_converter.py') and filename != 'base_converter.py' and filename != 'chained_converter.py':
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    module = importlib.import_module(f'app.converters.{module_name}')
                    
                    # Find converter classes in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseConverter) and 
                            obj is not BaseConverter and 
                            hasattr(obj, 'SOURCE_FORMATS') and 
                            hasattr(obj, 'TARGET_FORMATS')):
                            
                            # Register the converter class
                            converter_name = name
                            self._converter_classes[converter_name] = obj
                            
                            # Register format support
                            for source_format in obj.SOURCE_FORMATS:
                                for target_format in obj.TARGET_FORMATS:
                                    self.register_converter(source_format.lower(), target_format.lower(), obj)
                            
                            logger.info(f"Discovered converter: {converter_name}")
                    
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error loading converter module {module_name}: {e}")
        
        # Build the conversion graph
        self._build_conversion_graph()
        logger.info(f"Registered {len(self._converter_classes)} converter classes supporting {len(self._converters)} format combinations")
    
    def register_converter(self, source_format: str, target_format: str, converter_class: Type[BaseConverter]) -> None:
        """
        Register a converter for a specific source and target format
        
        Args:
            source_format (str): Source file format
            target_format (str): Target file format
            converter_class (Type[BaseConverter]): Converter class to use
        """
        key = (source_format.lower(), target_format.lower())
        self._converters[key] = converter_class
        
        # Update the conversion graph
        if source_format not in self._conversion_graph:
            self._conversion_graph[source_format] = set()
        self._conversion_graph[source_format].add(target_format)
        
        logger.debug(f"Registered converter for {source_format} -> {target_format}")
    
    def _build_conversion_graph(self) -> None:
        """
        Build the conversion graph from registered converters
        This graph represents possible conversion paths between formats
        """
        self._conversion_graph = {}
        
        for (source_format, target_format) in self._converters:
            if source_format not in self._conversion_graph:
                self._conversion_graph[source_format] = set()
            self._conversion_graph[source_format].add(target_format)
    
    def get_converter(self, source_format: str, target_format: str) -> Optional[BaseConverter]:
        """
        Get a converter instance for the specified formats
        
        Args:
            source_format (str): Source file format
            target_format (str): Target file format
            
        Returns:
            BaseConverter: Converter instance or None if no converter is found
        """
        source_format = source_format.lower()
        target_format = target_format.lower()
        
        # Direct converter available
        key = (source_format, target_format)
        if key in self._converters:
            converter_class = self._converters[key]
            return converter_class(source_format, target_format)
        
        # Try to find a conversion path
        conversion_path = self.find_conversion_path(source_format, target_format)
        if conversion_path and len(conversion_path) > 1:
            # Create a ChainedConverter
            from app.converters.chained_converter import ChainedConverter
            return ChainedConverter(source_format, target_format, conversion_path)
        
        logger.warning(f"No converter found for {source_format} -> {target_format}")
        return None
    
    def find_conversion_path(self, source_format: str, target_format: str) -> Optional[List[str]]:
        """
        Find the shortest path to convert from source_format to target_format
        
        Args:
            source_format (str): Source file format
            target_format (str): Target file format
            
        Returns:
            List[str]: List of formats representing the conversion path or None if no path exists
        """
        source_format = source_format.lower()
        target_format = target_format.lower()
        
        # Same format, no conversion needed
        if source_format == target_format:
            return [source_format]
        
        # Direct conversion available
        if (source_format, target_format) in self._converters:
            return [source_format, target_format]
        
        # Use breadth-first search to find the shortest path
        visited = set()
        queue = [(source_format, [source_format])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current in self._conversion_graph:
                for next_format in self._conversion_graph[current]:
                    if next_format == target_format:
                        return path + [next_format]
                    
                    if next_format not in visited:
                        visited.add(next_format)
                        queue.append((next_format, path + [next_format]))
        
        return None
    
    def create_conversion_chain(self, conversion_path: List[str]) -> List[BaseConverter]:
        """
        Create a chain of converters based on a conversion path
        
        Args:
            conversion_path (List[str]): List of formats representing the conversion path
            
        Returns:
            List[BaseConverter]: List of converter instances
        """
        if not conversion_path or len(conversion_path) < 2:
            return []
        
        converters = []
        for i in range(len(conversion_path) - 1):
            source = conversion_path[i]
            target = conversion_path[i + 1]
            
            converter = self.get_converter(source, target)
            if not converter:
                raise ValueError(f"No converter found for {source} -> {target}")
            
            converters.append(converter)
        
        return converters
    
    def get_supported_source_formats(self) -> List[str]:
        """
        Get a list of all supported source formats
        
        Returns:
            List[str]: List of supported source formats
        """
        return sorted(list(set([source for source, _ in self._converters.keys()])))
    
    def get_supported_target_formats(self, source_format: str = None) -> List[str]:
        """
        Get a list of supported target formats for a specific source format
        If source_format is None, returns all supported target formats
        
        Args:
            source_format (str, optional): Source format to check
            
        Returns:
            List[str]: List of supported target formats
        """
        if source_format:
            source_format = source_format.lower()
            return sorted(list(set([target for src, target in self._converters.keys() if src == source_format])))
        else:
            return sorted(list(set([target for _, target in self._converters.keys()])))
    
    def get_format_details(self) -> Dict:
        """
        Get detailed information about supported formats grouped by type
        
        Returns:
            Dict: Dictionary with format information
        """
        format_details = {
            'document': {fmt: self._get_format_conversions(fmt) for fmt in self.DOCUMENT_FORMATS},
            'image': {fmt: self._get_format_conversions(fmt) for fmt in self.IMAGE_FORMATS},
            'audio': {fmt: self._get_format_conversions(fmt) for fmt in self.AUDIO_FORMATS},
            'video': {fmt: self._get_format_conversions(fmt) for fmt in self.VIDEO_FORMATS},
            'data': {fmt: self._get_format_conversions(fmt) for fmt in self.DATA_FORMATS},
        }
        
        # Filter out formats with no conversions
        for category in format_details:
            format_details[category] = {fmt: info for fmt, info in format_details[category].items() 
                                       if info['can_convert_from'] or info['can_convert_to']}
        
        return format_details
    
    def _get_format_conversions(self, format_name: str) -> Dict:
        """
        Get conversion information for a specific format
        
        Args:
            format_name (str): Format to check
            
        Returns:
            Dict: Dictionary with conversion information
        """
        format_name = format_name.lower()
        
        can_convert_from = set()
        can_convert_to = set()
        
        # Check what formats can be converted from this format
        for src, target in self._converters.keys():
            if src == format_name:
                can_convert_to.add(target)
            if target == format_name:
                can_convert_from.add(src)
        
        return {
            'can_convert_from': sorted(list(can_convert_from)),
            'can_convert_to': sorted(list(can_convert_to))
        }
    
    def is_conversion_supported(self, source_format: str, target_format: str) -> bool:
        """
        Check if conversion between the specified formats is supported
        
        Args:
            source_format (str): Source file format
            target_format (str): Target file format
            
        Returns:
            bool: True if conversion is supported, False otherwise
        """
        source_format = source_format.lower()
        target_format = target_format.lower()
        
        # Same format, no conversion needed
        if source_format == target_format:
            return True
        
        # Direct conversion available
        if (source_format, target_format) in self._converters:
            return True
        
        # Try to find a conversion path
        conversion_path = self.find_conversion_path(source_format, target_format)
        return conversion_path is not None and len(conversion_path) > 1
    
    def get_converter_classes(self) -> Dict[str, Type[BaseConverter]]:
        """
        Get all registered converter classes
        
        Returns:
            Dict[str, Type[BaseConverter]]: Dictionary mapping converter names to classes
        """
        return self._converter_classes
    
    def register_converters_from_config(self, config: Dict) -> None:
        """
        Register converters from a configuration dictionary
        
        Args:
            config (Dict): Configuration dictionary with converter mappings
        """
        if not config or 'converters' not in config:
            return
        
        for converter_info in config['converters']:
            source_format = converter_info.get('source_format')
            target_format = converter_info.get('target_format')
            converter_class_name = converter_info.get('converter_class')
            
            if not all([source_format, target_format, converter_class_name]):
                logger.warning(f"Invalid converter configuration: {converter_info}")
                continue
            
            try:
                # Import the converter class
                module_name, class_name = converter_class_name.rsplit('.', 1)
                module = importlib.import_module(module_name)
                converter_class = getattr(module, class_name)
                
                # Register the converter
                self.register_converter(source_format, target_format, converter_class)
                logger.info(f"Registered converter from config: {source_format} -> {target_format}")
                
            except (ImportError, AttributeError) as e:
                logger.error(f"Error registering converter {converter_class_name}: {e}")
    
    def clear_converters(self) -> None:
        """
        Clear all registered converters
        Useful for testing and reinitialization
        """
        self._converters = {}
        self._converter_classes = {}
        self._conversion_graph = {}
        
    def reinitialize(self) -> None:
        """
        Reinitialize the factory and rediscover all converters
        """
        self.clear_converters()
        self._initialize()

# Create a singleton instance
converter_factory = ConverterFactory() 