import os
import json
import yaml
import pandas as pd
from dicttoxml import dicttoxml
from app.converters.base_converter import BaseConverter

class YAMLConverter(BaseConverter):
    """Converter for YAML format files"""
    
    @classmethod
    def supports_target_format(cls, target_format):
        """Check if YAML can be converted to the target format"""
        target_format = target_format.lower()
        return target_format in ['csv', 'json', 'xml', 'xlsx', 'xls', 'pdf', 'txt']
    
    def convert(self, source_path, target_path, options=None):
        """Convert YAML to the target format"""
        options = options or {}
        
        # Read YAML file
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Error reading YAML file: {str(e)}")
        
        # Convert based on target format
        if self.target_format in ['csv']:
            self._convert_to_csv(data, target_path, options)
        elif self.target_format in ['json']:
            self._convert_to_json(data, target_path, options)
        elif self.target_format in ['xml']:
            self._convert_to_xml(data, target_path, options)
        elif self.target_format in ['xlsx', 'xls']:
            self._convert_to_excel(data, target_path, options)
        elif self.target_format in ['pdf']:
            self._convert_to_pdf(data, target_path, options)
        elif self.target_format in ['txt']:
            self._convert_to_txt(data, target_path, options)
        else:
            raise ValueError(f"Unsupported target format: {self.target_format}")
        
        return True
    
    def _convert_to_csv(self, data, target_path, options):
        """Convert YAML to CSV"""
        if isinstance(data, list):
            # If it's a list of objects, convert directly to dataframe
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # If it's a dictionary, try to convert it to a dataframe
            if options.get('dict_key_for_records'):
                # If a specific key is specified for the records
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    raise ValueError(f"Key '{key}' not found in YAML or is not a list")
            else:
                # Try to convert the dict to a dataframe directly
                # This might result in a single-row dataframe
                df = pd.DataFrame([data])
        else:
            raise ValueError("YAML data is not in a format convertible to CSV")
        
        # Save as CSV
        df.to_csv(target_path, index=False, **options.get('csv_options', {}))
    
    def _convert_to_json(self, data, target_path, options):
        """Convert YAML to JSON"""
        indent = options.get('indent', 4)
        ensure_ascii = options.get('ensure_ascii', False)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    def _convert_to_xml(self, data, target_path, options):
        """Convert YAML to XML"""
        root_name = options.get('xml_root', 'data')
        
        # Convert dict to XML
        xml = dicttoxml(data, custom_root=root_name)
        
        with open(target_path, 'wb') as f:
            f.write(xml)
    
    def _convert_to_excel(self, data, target_path, options):
        """Convert YAML to Excel"""
        sheet_name = options.get('sheet_name', 'Sheet1')
        
        if isinstance(data, list):
            # If it's a list of objects, convert directly to dataframe
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # If it's a dictionary, try to convert it to a dataframe
            if options.get('dict_key_for_records'):
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    raise ValueError(f"Key '{key}' not found in YAML or is not a list")
            else:
                # Try to convert the dict to a dataframe directly
                df = pd.DataFrame([data])
        else:
            raise ValueError("YAML data is not in a format convertible to Excel")
        
        writer = pd.ExcelWriter(target_path, engine='openpyxl')
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
    
    def _convert_to_pdf(self, data, target_path, options):
        """Convert YAML to PDF"""
        # Convert to data frame first
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            if options.get('dict_key_for_records'):
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    raise ValueError(f"Key '{key}' not found in YAML or is not a list")
            else:
                df = pd.DataFrame([data])
        else:
            raise ValueError("YAML data is not in a format convertible to PDF")
        
        # Import optional dependencies here to avoid forcing all users to install them
        try:
            from fpdf import FPDF
        except ImportError:
            raise ImportError("Converting to PDF requires the 'fpdf' package. Install it using 'pip install fpdf'.")
        
        # Create PDF object
        pdf = FPDF()
        pdf.add_page()
        
        # Document title
        title = options.get('title', 'YAML to PDF Conversion')
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(10)
        
        # Set up table
        pdf.set_font('Arial', 'B', 12)
        
        # Calculate column width (based on number of columns)
        columns = df.columns
        col_width = (pdf.w - 20) / len(columns)
        
        # Add headers
        for col in columns:
            pdf.cell(col_width, 10, str(col), 1, 0, 'C')
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 10)
        for _, row in df.iterrows():
            for col in columns:
                pdf.cell(col_width, 10, str(row[col])[:30], 1, 0, 'C')
            pdf.ln()
        
        # Save PDF file
        pdf.output(target_path)
    
    def _convert_to_txt(self, data, target_path, options):
        """Convert YAML to TXT"""
        indent = options.get('indent', 2)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            if isinstance(data, dict):
                self._write_dict_to_txt(data, f, indent=indent)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    f.write(f"Item {i+1}:\n")
                    if isinstance(item, dict):
                        self._write_dict_to_txt(item, f, indent=indent, level=1)
                    else:
                        f.write(f"  {item}\n")
            else:
                f.write(str(data))
    
    def _write_dict_to_txt(self, data, file, indent=2, level=0):
        """Helper function to write dictionary data to text file"""
        for key, value in data.items():
            spaces = ' ' * (level * indent)
            if isinstance(value, dict):
                file.write(f"{spaces}{key}:\n")
                self._write_dict_to_txt(value, file, indent, level + 1)
            elif isinstance(value, list):
                file.write(f"{spaces}{key}:\n")
                for item in value:
                    if isinstance(item, dict):
                        file.write(f"{spaces}{' ' * indent}- \n")
                        self._write_dict_to_txt(item, file, indent, level + 2)
                    else:
                        file.write(f"{spaces}{' ' * indent}- {item}\n")
            else:
                file.write(f"{spaces}{key}: {value}\n") 