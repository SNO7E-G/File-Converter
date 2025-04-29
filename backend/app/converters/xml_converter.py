import os
import json
import yaml
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict
from app.converters.base_converter import BaseConverter

class XMLConverter(BaseConverter):
    """Converter for XML format files"""
    
    @classmethod
    def supports_target_format(cls, target_format):
        """Check if XML can be converted to the target format"""
        target_format = target_format.lower()
        return target_format in ['csv', 'json', 'yaml', 'yml', 'xlsx', 'xls', 'pdf', 'txt']
    
    def convert(self, source_path, target_path, options=None):
        """Convert XML to the target format"""
        options = options or {}
        
        # Parse XML file
        try:
            tree = ET.parse(source_path)
            root = tree.getroot()
            
            # Convert XML to Python dict
            data = self._xml_to_dict(root, options)
        except Exception as e:
            raise ValueError(f"Error reading XML file: {str(e)}")
        
        # Convert based on target format
        if self.target_format in ['json']:
            self._convert_to_json(data, target_path, options)
        elif self.target_format in ['yaml', 'yml']:
            self._convert_to_yaml(data, target_path, options)
        elif self.target_format in ['csv']:
            self._convert_to_csv(data, target_path, options)
        elif self.target_format in ['xlsx', 'xls']:
            self._convert_to_excel(data, target_path, options)
        elif self.target_format in ['pdf']:
            self._convert_to_pdf(data, target_path, options)
        elif self.target_format in ['txt']:
            self._convert_to_txt(data, target_path, options)
        else:
            raise ValueError(f"Unsupported target format: {self.target_format}")
        
        return True
    
    def _xml_to_dict(self, element, options):
        """Convert XML element to Python dict"""
        # Option to preserve attributes
        preserve_attrs = options.get('preserve_attrs', True)
        # Option to use a specific key for repeated elements
        items_key = options.get('items_key', None)
        
        result = {}
        
        # Add attributes if present and requested
        if preserve_attrs and element.attrib:
            result['@attrs'] = dict(element.attrib)
        
        # Process child elements
        children_by_tag = defaultdict(list)
        for child in element:
            tag = child.tag
            child_data = self._xml_to_dict(child, options)
            children_by_tag[tag].append(child_data)
        
        # Handle repeated elements
        for tag, items in children_by_tag.items():
            if len(items) == 1:
                result[tag] = items[0]
            else:
                if items_key:
                    result[tag] = {items_key: items}
                else:
                    result[tag] = items
        
        # Add text content if present and element has no children
        text = element.text
        if text and text.strip() and not children_by_tag:
            if preserve_attrs and element.attrib:
                result['#text'] = text.strip()
            else:
                return text.strip()
        
        return result
    
    def _convert_to_json(self, data, target_path, options):
        """Convert dict to JSON"""
        indent = options.get('indent', 4)
        ensure_ascii = options.get('ensure_ascii', False)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    def _convert_to_yaml(self, data, target_path, options):
        """Convert dict to YAML"""
        with open(target_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def _convert_to_csv(self, data, target_path, options):
        """Convert dict to CSV"""
        # Extract the relevant data for CSV conversion
        rows = self._extract_rows_from_xml_dict(data, options)
        
        if not rows:
            raise ValueError("Could not extract tabular data from XML structure")
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(rows)
        df.to_csv(target_path, index=False, **options.get('csv_options', {}))
    
    def _extract_rows_from_xml_dict(self, data, options):
        """Extract rows for CSV conversion from XML dict structure"""
        rows = []
        
        # Option to specify the path to the rows in the XML structure
        row_path = options.get('row_path', None)
        
        if row_path:
            # Navigate to the specified path
            current = data
            for path_part in row_path.split('.'):
                if not current or path_part not in current:
                    return []
                current = current[path_part]
            
            # Handle both list and dict cases
            if isinstance(current, list):
                rows = current
            elif isinstance(current, dict):
                # Try to extract a list if there's an obvious list inside
                for key, value in current.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        rows = value
                        break
        else:
            # Auto-detect: look for the first list of dictionaries
            self._find_list_of_dicts(data, rows)
            
        return rows
    
    def _find_list_of_dicts(self, data, result, max_depth=5, current_depth=0):
        """Recursively search for a list of dictionaries in the data structure"""
        if current_depth > max_depth or result:
            return
        
        if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
            result.extend(data)
            return
        
        if isinstance(data, dict):
            for value in data.values():
                self._find_list_of_dicts(value, result, max_depth, current_depth + 1)
    
    def _convert_to_excel(self, data, target_path, options):
        """Convert dict to Excel"""
        # Extract the relevant data for Excel conversion
        rows = self._extract_rows_from_xml_dict(data, options)
        
        if not rows:
            raise ValueError("Could not extract tabular data from XML structure")
        
        # Convert to DataFrame and save as Excel
        df = pd.DataFrame(rows)
        sheet_name = options.get('sheet_name', 'Sheet1')
        
        writer = pd.ExcelWriter(target_path, engine='openpyxl')
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
    
    def _convert_to_pdf(self, data, target_path, options):
        """Convert dict to PDF"""
        # Extract the relevant data for PDF conversion
        rows = self._extract_rows_from_xml_dict(data, options)
        
        if not rows:
            raise ValueError("Could not extract tabular data from XML structure")
        
        # Convert to DataFrame for PDF generation
        df = pd.DataFrame(rows)
        
        # Import optional dependencies here to avoid forcing all users to install them
        try:
            from fpdf import FPDF
        except ImportError:
            raise ImportError("Converting to PDF requires the 'fpdf' package. Install it using 'pip install fpdf'.")
        
        # Create PDF object
        pdf = FPDF()
        pdf.add_page()
        
        # Document title
        title = options.get('title', 'XML to PDF Conversion')
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
        """Convert dict to TXT"""
        indent = options.get('indent', 2)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            self._write_dict_to_txt(data, f, indent=indent)
    
    def _write_dict_to_txt(self, data, file, indent=2, level=0):
        """Helper function to write dictionary data to text file"""
        if isinstance(data, dict):
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
        elif isinstance(data, list):
            spaces = ' ' * (level * indent)
            for i, item in enumerate(data):
                file.write(f"{spaces}{i+1}.\n")
                self._write_dict_to_txt(item, file, indent, level + 1)
        else:
            spaces = ' ' * (level * indent)
            file.write(f"{spaces}{data}\n") 