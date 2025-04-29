import os
import json
import yaml
import pandas as pd
from dicttoxml import dicttoxml
from app.converters.base_converter import BaseConverter

class JSONConverter(BaseConverter):
    """Converter for JSON format files"""
    
    @classmethod
    def supports_target_format(cls, target_format):
        """Check if JSON can be converted to the target format"""
        target_format = target_format.lower()
        return target_format in ['csv', 'xml', 'yaml', 'yml', 'xlsx', 'xls', 'pdf']
    
    def convert(self, source_path, target_path, options=None):
        """Convert JSON to the target format"""
        options = options or {}
        
        # Read JSON file
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading JSON file: {str(e)}")
        
        # Convert based on target format
        if self.target_format in ['csv']:
            self._convert_to_csv(data, target_path, options)
        elif self.target_format in ['xml']:
            self._convert_to_xml(data, target_path, options)
        elif self.target_format in ['yaml', 'yml']:
            self._convert_to_yaml(data, target_path, options)
        elif self.target_format in ['xlsx', 'xls']:
            self._convert_to_excel(data, target_path, options)
        elif self.target_format in ['pdf']:
            self._convert_to_pdf(data, target_path, options)
        else:
            raise ValueError(f"Unsupported target format: {self.target_format}")
        
        return True
    
    def _convert_to_csv(self, data, target_path, options):
        """Convert JSON to CSV"""
        if isinstance(data, list):
            # If it's a list of objects, convert directly to dataframe
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # If it's a dictionary, try to convert it to a dataframe
            # This depends on the structure of the JSON
            if options.get('dict_key_for_records'):
                # If a specific key is specified for the records
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    raise ValueError(f"Key '{key}' not found in JSON or is not a list")
            else:
                # Try to convert the dict to a dataframe directly
                # This might result in a single-row dataframe
                df = pd.DataFrame([data])
        else:
            raise ValueError("JSON data is not in a format convertible to CSV")
        
        # Save as CSV
        df.to_csv(target_path, index=False, **options.get('csv_options', {}))
    
    def _convert_to_xml(self, data, target_path, options):
        """Convert JSON to XML"""
        root_name = options.get('xml_root', 'data')
        
        # Convert dict to XML
        xml = dicttoxml(data, custom_root=root_name)
        
        with open(target_path, 'wb') as f:
            f.write(xml)
    
    def _convert_to_yaml(self, data, target_path, options):
        """Convert JSON to YAML"""
        with open(target_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def _convert_to_excel(self, data, target_path, options):
        """Convert JSON to Excel"""
        sheet_name = options.get('sheet_name', 'Sheet1')
        
        if isinstance(data, list):
            # If it's a list of objects, convert directly to dataframe
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try different approaches based on the JSON structure
            if options.get('dict_key_for_records'):
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    raise ValueError(f"Key '{key}' not found in JSON or is not a list")
            else:
                # Check if it's nested (multiple sheets)
                sheets = {}
                for key, value in data.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        sheets[key] = pd.DataFrame(value)
                
                if sheets:
                    writer = pd.ExcelWriter(target_path, engine='openpyxl')
                    for sheet_name, df in sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    writer.close()
                    return
                
                # Fallback to single dataframe conversion
                df = pd.DataFrame([data])
        else:
            raise ValueError("JSON data is not in a format convertible to Excel")
        
        # Save to Excel
        writer = pd.ExcelWriter(target_path, engine='openpyxl')
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
    
    def _convert_to_pdf(self, data, target_path, options):
        """Convert JSON to PDF"""
        # First convert to dataframe for easier handling
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            if options.get('dict_key_for_records'):
                key = options['dict_key_for_records']
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                else:
                    # Try to flatten the JSON for display
                    flattened = self._flatten_json(data)
                    df = pd.DataFrame([flattened])
            else:
                # Try to flatten the JSON for display
                flattened = self._flatten_json(data)
                df = pd.DataFrame([flattened])
        else:
            raise ValueError("JSON data is not in a format convertible to PDF")
        
        # Now convert the dataframe to PDF (similar to CSV converter)
        temp_html = os.path.splitext(target_path)[0] + '.html'
        
        try:
            # Generate HTML representation
            html_table = df.to_html(index=False, classes=['table', 'table-striped', 'table-bordered'])
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>JSON to PDF Conversion</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ padding: 8px 12px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h1>JSON Data</h1>
                {html_table}
            </body>
            </html>
            """
            
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Convert HTML to PDF
            try:
                import pdfkit
                pdfkit.from_file(temp_html, target_path)
            except Exception as e:
                # Fallback to reportlab
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
                
                doc = SimpleDocTemplate(target_path, pagesize=letter)
                table_data = [df.columns.tolist()] + df.values.tolist()
                
                # Convert all data to strings
                for i in range(len(table_data)):
                    table_data[i] = [str(item) for item in table_data[i]]
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                doc.build([table])
        finally:
            # Remove temporary HTML file
            if os.path.exists(temp_html):
                os.remove(temp_html)
    
    def _flatten_json(self, json_obj, parent_key='', sep='_'):
        """
        Flatten a nested JSON object into a single level dictionary
        """
        items = {}
        for k, v in json_obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_json(v, new_key, sep=sep))
            elif isinstance(v, list):
                # For lists, convert to string representation
                items[new_key] = str(v)
            else:
                items[new_key] = v
        return items 