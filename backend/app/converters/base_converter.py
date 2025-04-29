import os
import time
import logging
import hashlib
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List
from flask import current_app
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)

def conversion_timer(method):
    """Decorator to measure conversion time and log it"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = method(self, *args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"Conversion from {self.source_format} to {self.target_format} took {elapsed_time:.2f} seconds")
        # Store metrics in class variable for potential telemetry
        if not hasattr(BaseConverter, '_conversion_metrics'):
            BaseConverter._conversion_metrics = {}
        
        key = f"{self.source_format}_to_{self.target_format}"
        if key not in BaseConverter._conversion_metrics:
            BaseConverter._conversion_metrics[key] = {'count': 0, 'total_time': 0, 'failures': 0}
        
        BaseConverter._conversion_metrics[key]['count'] += 1
        BaseConverter._conversion_metrics[key]['total_time'] += elapsed_time
        
        if not result:
            BaseConverter._conversion_metrics[key]['failures'] += 1
        
        return result
    return wrapper

class BaseConverter(ABC):
    """Base class for all converters"""
    
    # Class variable to store conversion metrics
    _conversion_metrics = {}
    
    # Cache to store previously computed file hashes
    _file_hash_cache = {}
    
    def __init__(self, source_format: str, target_format: str):
        """
        Initialize the converter
        
        Args:
            source_format (str): The source file format
            target_format (str): The target file format
        """
        self.source_format = source_format.lower()
        self.target_format = target_format.lower()
        
    @classmethod
    @abstractmethod
    def supports_target_format(cls, target_format: str) -> bool:
        """
        Check if this converter supports converting to the target format
        
        Args:
            target_format (str): The target file format
            
        Returns:
            bool: True if conversion to target_format is supported, False otherwise
        """
        pass
    
    @conversion_timer
    @abstractmethod
    def convert(self, source_path: str, target_path: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Convert the file from source format to target format
        
        Args:
            source_path (str): Path to the source file
            target_path (str): Path where the converted file should be saved
            options (dict, optional): Additional options for the conversion
            
        Returns:
            bool: True if the conversion was successful, False otherwise
            
        Raises:
            Exception: If an error occurs during conversion
        """
        pass
    
    def validate_source_file(self, source_path: str) -> bool:
        """
        Validate that the source file exists and is of the correct format
        
        Args:
            source_path (str): Path to the source file
            
        Returns:
            bool: True if the file is valid, False otherwise
            
        Raises:
            FileNotFoundError: If the source file does not exist
            ValueError: If the file is not of the correct format
            ValueError: If the file is empty or corrupted
        """
        # Check if file exists
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file does not exist: {source_path}")
        
        # Check if file is empty
        if os.path.getsize(source_path) == 0:
            raise ValueError(f"Source file is empty: {source_path}")
        
        # Check file extension
        _, extension = os.path.splitext(source_path)
        if extension.lower()[1:] != self.source_format:
            logger.warning(f"File extension mismatch: expected {self.source_format}, got {extension[1:]}")
            # Not raising an error here as some files might have incorrect extensions
            # But we'll log a warning
        
        # Try to perform basic validation based on file type
        try:
            self._validate_file_content(source_path)
        except Exception as e:
            logger.warning(f"File content validation failed: {str(e)}")
        
        return True
    
    def _validate_file_content(self, file_path: str) -> bool:
        """
        Validate the content of the file based on its type
        This is a placeholder that can be implemented by subclasses
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if validation passes
            
        Raises:
            ValueError: If the file is corrupted or invalid
        """
        return True
    
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute a hash of the file contents for caching purposes
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Hash of the file contents
        """
        # Check if hash is already in cache
        if file_path in BaseConverter._file_hash_cache:
            return BaseConverter._file_hash_cache[file_path]
        
        # Compute hash if not cached
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        file_hash = hash_md5.hexdigest()
        
        # Cache the result
        BaseConverter._file_hash_cache[file_path] = file_hash
        
        return file_hash
    
    def safe_convert(self, source_path: str, target_path: str, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Safely convert the file, catching and logging any exceptions
        
        Args:
            source_path (str): Path to the source file
            target_path (str): Path where the converted file should be saved
            options (dict, optional): Additional options for the conversion
            
        Returns:
            tuple: (success, error_message) where success is a boolean indicating
                  if the conversion was successful, and error_message is a string
                  containing an error message if the conversion failed
        """
        try:
            # Validate the source file
            self.validate_source_file(source_path)
            
            # Ensure options is a dictionary
            if options is None:
                options = {}
            
            # Check for output directory and create if necessary
            target_dir = os.path.dirname(target_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            # Perform the conversion
            success = self.convert(source_path, target_path, options)
            
            # Validate the result
            if success and not os.path.exists(target_path):
                return False, "Conversion completed but output file was not created"
            
            if success and os.path.getsize(target_path) == 0:
                return False, "Conversion completed but output file is empty"
            
            return success, None
        except FileNotFoundError as e:
            error = f"File not found: {str(e)}"
            logger.error(error)
            return False, error
        except ValueError as e:
            error = f"Validation error: {str(e)}"
            logger.error(error)
            return False, error
        except Exception as e:
            error = f"Error converting {self.source_format} to {self.target_format}: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error(f"{error}\n{stack_trace}")
            return False, error
    
    @classmethod
    def get_conversion_metrics(cls) -> Dict[str, Dict[str, float]]:
        """
        Get metrics about all conversions performed
        
        Returns:
            Dict: Dictionary containing metrics about all conversions
        """
        metrics = {}
        
        for key, data in cls._conversion_metrics.items():
            count = data['count']
            metrics[key] = {
                'count': count,
                'total_time': data['total_time'],
                'failures': data['failures'],
                'success_rate': (count - data['failures']) / count if count > 0 else 0,
                'avg_time': data['total_time'] / count if count > 0 else 0
            }
        
        return metrics
    
    @classmethod
    def clear_metrics(cls) -> None:
        """Clear all conversion metrics"""
        cls._conversion_metrics = {}
    
    @classmethod
    def clear_file_hash_cache(cls) -> None:
        """Clear the file hash cache"""
        cls._file_hash_cache = {} 