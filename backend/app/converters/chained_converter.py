import os
import tempfile
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.converters.base_converter import BaseConverter

# Set up logging
logger = logging.getLogger(__name__)

class ChainedConverter(BaseConverter):
    """
    A converter that chains multiple converters together to perform multi-step conversions.
    This allows for conversions between formats that don't have a direct conversion path.
    """
    
    def __init__(self, converters: List[BaseConverter], source_format: str, target_format: str):
        """
        Initialize the chained converter with a list of converters
        
        Args:
            converters (List[BaseConverter]): List of converters to chain
            source_format (str): The original source format
            target_format (str): The final target format
        """
        super().__init__(source_format, target_format)
        self.converters = converters
        
        # Validate the chain
        if not converters:
            raise ValueError("Converter chain cannot be empty")
        
        # Validate that the chain links properly
        for i in range(len(converters) - 1):
            current = converters[i]
            next_converter = converters[i + 1]
            
            if current.target_format != next_converter.source_format:
                raise ValueError(
                    f"Invalid converter chain: {current.source_format}->{current.target_format} "
                    f"cannot connect to {next_converter.source_format}->{next_converter.target_format}"
                )
    
    @staticmethod
    def supports_target_format(target_format: str) -> bool:
        """
        The ChainedConverter doesn't directly support any format.
        It's created dynamically based on conversion paths.
        
        Args:
            target_format (str): The target format to check
            
        Returns:
            bool: Always False for ChainedConverter
        """
        return False
    
    def convert(self, source_file: str, target_file: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Convert the source file to the target format using a chain of converters
        
        Args:
            source_file (str): Path to the source file
            target_file (str): Path to save the converted file
            options (Dict[str, Any], optional): Conversion options
            
        Returns:
            bool: True if conversion was successful, False otherwise
        """
        if not options:
            options = {}
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            current_source = source_file
            
            # Execute each converter in the chain
            for i, converter in enumerate(self.converters):
                # For the last converter, use the target file as output
                if i == len(self.converters) - 1:
                    current_target = target_file
                else:
                    # Create an intermediate file for this stage
                    intermediate_ext = converter.target_format
                    temp_filename = f"intermediate_{i}.{intermediate_ext}"
                    current_target = os.path.join(temp_dir, temp_filename)
                
                # Get converter-specific options
                converter_options = self._extract_options_for_converter(options, converter)
                
                # Log conversion step
                logger.info(
                    f"Chained conversion step {i+1}/{len(self.converters)}: "
                    f"{converter.source_format} -> {converter.target_format}"
                )
                
                # Perform conversion
                success = converter.convert(current_source, current_target, converter_options)
                
                # If any step fails, the whole chain fails
                if not success:
                    logger.error(
                        f"Chained conversion failed at step {i+1}/{len(self.converters)}: "
                        f"{converter.source_format} -> {converter.target_format}"
                    )
                    return False
                
                # Use the current target as the source for the next converter
                current_source = current_target
            
            return True
    
    def safe_convert(self, source_file: str, target_file: str, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Safely convert the source file to the target format, catching any exceptions
        
        Args:
            source_file (str): Path to the source file
            target_file (str): Path to save the converted file
            options (Dict[str, Any], optional): Conversion options
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            success = self.convert(source_file, target_file, options)
            if not success:
                return False, "Conversion failed during processing"
            return True, None
        except Exception as e:
            logger.exception(f"Error in chained conversion: {e}")
            return False, str(e)
    
    def _extract_options_for_converter(self, options: Dict[str, Any], converter: BaseConverter) -> Dict[str, Any]:
        """
        Extract relevant options for a specific converter in the chain
        
        Args:
            options (Dict[str, Any]): The full options dictionary
            converter (BaseConverter): The converter to extract options for
            
        Returns:
            Dict[str, Any]: Options relevant to the specific converter
        """
        # Get format-specific options if available
        source_format = converter.source_format
        target_format = converter.target_format
        
        # Try to find format-specific options
        specific_key = f"{source_format}_to_{target_format}"
        if specific_key in options:
            return options[specific_key]
        
        # Return general options
        return options 