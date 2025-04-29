import os
import json
import yaml
import pandas as pd
import dicttoxml
from dicttoxml import dicttoxml
from app.converters.base_converter import BaseConverter

class CSVConverter(BaseConverter):
    """Converter for CSV format files"""
    
    @classmethod
    def supports_target_format(cls, target_format):
        """Check if CSV can be converted to the target format"""
        target_format = target_format.lower()
        return target_format in ['json', 'xml', 'yaml', 'yml', 'xlsx', 'xls', 'pdf']
    
    def convert(self, source_path, target_path, options=None):
        """Convert CSV to the target format"""
        options = options or {}
        
        # Read CSV file into pandas DataFrame
        try:
            df = pd.read_csv(source_path, **options.get('read_options', {}))
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
        
        # Convert based on target format
        if self.target_format in ['json']:
            self._convert_to_json(df, target_path, options)
        elif self.target_format in ['xml']:
            self._convert_to_xml(df, target_path, options)
        elif self.target_format in ['yaml', 'yml']:
            self._convert_to_yaml(df, target_path, options)
        elif self.target_format in ['xlsx', 'xls']:
            self._convert_to_excel(df, target_path, options)
        elif self.target_format in ['pdf']:
            self._convert_to_pdf(df, target_path, options)
        else:
            raise ValueError(f"Unsupported target format: {self.target_format}")
        
        return True
    
    def _convert_to_json(self, df, target_path, options):
        """Convert DataFrame to JSON"""
        orient = options.get('json_orient', 'records')
        df_dict = df.to_dict(orient=orient)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(df_dict, f, indent=4, ensure_ascii=False)
    
    def _convert_to_xml(self, df, target_path, options):
        """Convert DataFrame to XML"""
        root_name = options.get('xml_root', 'data')
        row_name = options.get('xml_row', 'row')
        
        # Convert to dict first
        data_dict = df.to_dict(orient='records')
        
        # Convert dict to XML
        xml = dicttoxml(data_dict, custom_root=root_name, item_func=lambda x: row_name)
        
        with open(target_path, 'wb') as f:
            f.write(xml)
    
    def _convert_to_yaml(self, df, target_path, options):
        """Convert DataFrame to YAML"""
        # Convert to dict first
        data_dict = df.to_dict(orient='records')
        
        with open(target_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_dict, f, default_flow_style=False, allow_unicode=True)
    
    def _convert_to_excel(self, df, target_path, options):
        """Convert DataFrame to Excel"""
        sheet_name = options.get('sheet_name', 'Sheet1')
        
        writer = pd.ExcelWriter(target_path, engine='openpyxl')
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
    
    def _convert_to_pdf(self, df, target_path, options):
        """Convert DataFrame to PDF"""
        # Save as HTML first (temporary file)
        temp_html = os.path.splitext(target_path)[0] + '.html'
        
        try:
            # Generate a nice-looking HTML representation
            html_table = df.to_html(index=False, classes=['table', 'table-striped', 'table-bordered'])
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>CSV to PDF Conversion</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ padding: 8px 12px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h1>CSV Data</h1>
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
                # If pdfkit fails, try using reportlab as fallback
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