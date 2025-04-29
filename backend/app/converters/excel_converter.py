import pandas as pd
import os
import logging
from typing import Dict, Any, List, Optional
import openpyxl
from werkzeug.datastructures import FileStorage

from app.converters.base_converter import BaseConverter, conversion_timer
from app.utils.file_utils import get_file_extension, generate_unique_filename

# Set up logging
logger = logging.getLogger(__name__)

class ExcelConverter(BaseConverter):
    """
    Converter for Excel files (xlsx, xls) to various formats and vice versa
    """
    
    # Define supported source and target formats
    SOURCE_FORMATS = ['xlsx', 'xls']
    TARGET_FORMATS = ['csv', 'json', 'xml', 'yaml', 'pdf', 'html', 'txt']
    
    def __init__(self, source_format: str, target_format: str):
        """
        Initialize the Excel converter
        
        Args:
            source_format (str): Source file format (xlsx, xls)
            target_format (str): Target file format
        """
        super().__init__(source_format, target_format)
        logger.info(f"Excel converter initialized: {source_format} -> {target_format}")
    
    @staticmethod
    def supports_target_format(target_format: str) -> bool:
        """
        Check if the target format is supported by this converter
        
        Args:
            target_format (str): The target format to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return target_format.lower() in ExcelConverter.TARGET_FORMATS
    
    def _read_excel(self, source_path: str) -> Dict[str, pd.DataFrame]:
        """
        Read Excel file into pandas DataFrames
        
        Args:
            source_path (str): Path to the source Excel file
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping sheet names to DataFrames
        """
        try:
            # Check how many sheets the file has
            xl = pd.ExcelFile(source_path)
            sheet_names = xl.sheet_names
            
            # Read each sheet into a separate DataFrame
            sheets = {}
            for sheet_name in sheet_names:
                sheets[sheet_name] = pd.read_excel(source_path, sheet_name=sheet_name)
                
            return sheets
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise ValueError(f"Failed to read Excel file: {e}")
    
    @conversion_timer
    def convert(self, source_path: str, target_path: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Convert Excel file to target format
        
        Args:
            source_path (str): Path to the source file
            target_path (str, optional): Path for the target file, generated if None
            options (Dict[str, Any], optional): Additional options for conversion
                - sheet_index (int): Index of the sheet to convert (default: 0)
                - sheet_name (str): Name of the sheet to convert (prioritized over sheet_index)
                - na_rep (str): String to use for missing values
                - include_index (bool): Whether to include DataFrame index in output
            
        Returns:
            str: Path to the converted file
        """
        options = options or {}
        sheet_index = options.get('sheet_index', 0)
        sheet_name = options.get('sheet_name', None)
        na_rep = options.get('na_rep', '')
        include_index = options.get('include_index', False)
        
        # Generate target path if not provided
        if not target_path:
            target_dir = os.path.dirname(source_path)
            filename = generate_unique_filename(self.target_format)
            target_path = os.path.join(target_dir, filename)
        
        # Read Excel file
        sheets = self._read_excel(source_path)
        
        # Determine which sheet to use
        if sheet_name and sheet_name in sheets:
            df = sheets[sheet_name]
        else:
            # Use the sheet at the specified index, default to first sheet
            sheet_names = list(sheets.keys())
            if 0 <= sheet_index < len(sheet_names):
                df = sheets[sheet_names[sheet_index]]
            else:
                df = sheets[sheet_names[0]]
                logger.warning(f"Sheet index {sheet_index} out of range, using first sheet")
        
        # Perform conversion based on target format
        try:
            if self.target_format == 'csv':
                df.to_csv(target_path, index=include_index, na_rep=na_rep)
            
            elif self.target_format == 'json':
                # Convert DataFrame to JSON
                df.to_json(target_path, orient=options.get('orient', 'records'))
            
            elif self.target_format == 'xml':
                # Convert DataFrame to XML
                xml_content = df.to_xml(index=include_index)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
            
            elif self.target_format == 'yaml' or self.target_format == 'yml':
                # Convert DataFrame to YAML using appropriate library
                import yaml
                data = df.to_dict(orient='records')
                with open(target_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, sort_keys=False, allow_unicode=True)
            
            elif self.target_format == 'html':
                # Convert to HTML
                html_content = df.to_html(index=include_index, na_rep=na_rep)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Excel Conversion</title>
                        <style>
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <h2>Excel Sheet: {sheet_name or f"Sheet {sheet_index}"}</h2>
                        {html_content}
                    </body>
                    </html>
                    """)
            
            elif self.target_format == 'pdf':
                # Convert to PDF using additional libraries
                try:
                    from weasyprint import HTML
                    
                    # First convert to HTML
                    html_content = df.to_html(index=include_index, na_rep=na_rep)
                    html_string = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Excel Conversion</title>
                        <style>
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <h2>Excel Sheet: {sheet_name or f"Sheet {sheet_index}"}</h2>
                        {html_content}
                    </body>
                    </html>
                    """
                    
                    # Create a temporary HTML file
                    temp_html_path = f"{target_path}.temp.html"
                    with open(temp_html_path, 'w', encoding='utf-8') as f:
                        f.write(html_string)
                    
                    # Convert HTML to PDF
                    HTML(temp_html_path).write_pdf(target_path)
                    
                    # Remove the temporary HTML file
                    if os.path.exists(temp_html_path):
                        os.remove(temp_html_path)
                        
                except ImportError:
                    logger.error("WeasyPrint library not available for PDF conversion")
                    raise ValueError("PDF conversion requires WeasyPrint library")
            
            elif self.target_format == 'txt':
                # Convert to plain text
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(f"Excel Sheet: {sheet_name or f'Sheet {sheet_index}'}\n\n")
                    f.write(df.to_string(index=include_index, na_rep=na_rep))
            
            else:
                raise ValueError(f"Unsupported target format: {self.target_format}")
            
            logger.info(f"Successfully converted Excel to {self.target_format}: {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error converting Excel to {self.target_format}: {e}")
            raise ValueError(f"Failed to convert Excel to {self.target_format}: {e}")
    
    @classmethod
    def from_other_format(cls, source_file: FileStorage, source_format: str, options: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Convert from other formats to Excel DataFrame
        
        Args:
            source_file (FileStorage): Source file to convert
            source_format (str): Format of the source file
            options (Dict[str, Any], optional): Additional options for conversion
            
        Returns:
            pd.DataFrame: DataFrame representation of the source file
        """
        options = options or {}
        
        try:
            if source_format == 'csv':
                return pd.read_csv(source_file, **options)
            
            elif source_format == 'json':
                return pd.read_json(source_file, **options)
            
            elif source_format == 'xml':
                return pd.read_xml(source_file, **options)
            
            elif source_format in ['yaml', 'yml']:
                import yaml
                with open(source_file, 'r') as f:
                    data = yaml.safe_load(f)
                return pd.DataFrame(data)
            
            else:
                raise ValueError(f"Conversion from {source_format} to Excel not supported")
        
        except Exception as e:
            logger.error(f"Error converting {source_format} to Excel: {e}")
            raise ValueError(f"Failed to convert {source_format} to Excel: {e}") 