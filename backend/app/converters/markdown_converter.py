import os
import logging
from typing import Dict, Any, Optional, List
import tempfile
import subprocess
from werkzeug.datastructures import FileStorage

from app.converters.base_converter import BaseConverter, conversion_timer
from app.utils.file_utils import get_file_extension, generate_unique_filename

# Set up logging
logger = logging.getLogger(__name__)

class MarkdownConverter(BaseConverter):
    """
    Converter for Markdown files to various formats and vice versa
    """
    
    # Define supported source and target formats
    SOURCE_FORMATS = ['md', 'markdown']
    TARGET_FORMATS = ['html', 'pdf', 'docx', 'txt', 'epub', 'latex', 'tex']
    
    def __init__(self, source_format: str, target_format: str):
        """
        Initialize the Markdown converter
        
        Args:
            source_format (str): Source file format (md or markdown)
            target_format (str): Target file format
        """
        super().__init__(source_format, target_format)
        logger.info(f"Markdown converter initialized: {source_format} -> {target_format}")
    
    @staticmethod
    def supports_target_format(target_format: str) -> bool:
        """
        Check if the target format is supported by this converter
        
        Args:
            target_format (str): The target format to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return target_format.lower() in MarkdownConverter.TARGET_FORMATS
    
    def _ensure_dependencies(self):
        """
        Check if required dependencies are installed
        
        Raises:
            ValueError: If required dependencies are not available
        """
        try:
            import markdown
            import pdfkit
            from bs4 import BeautifulSoup
        except ImportError as e:
            missing_dep = str(e).split("'")[1] if "'" in str(e) else str(e)
            logger.error(f"Missing dependency: {missing_dep}")
            raise ValueError(f"Missing dependency: {missing_dep}. Please install the required packages.")
        
        # Check for Pandoc if converting to docx/epub
        if self.target_format in ['docx', 'epub', 'latex', 'tex']:
            try:
                result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
                if result.returncode != 0:
                    raise ValueError("Pandoc command failed. Please ensure Pandoc is installed correctly.")
            except FileNotFoundError:
                logger.error("Pandoc not found. Required for DOCX, EPUB, LaTeX conversions.")
                raise ValueError("Pandoc not found. Please install Pandoc to convert to DOCX, EPUB, or LaTeX formats.")
    
    @conversion_timer
    def convert(self, source_path: str, target_path: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Convert Markdown file to target format
        
        Args:
            source_path (str): Path to the source file
            target_path (str, optional): Path for the target file, generated if None
            options (Dict[str, Any], optional): Additional options for conversion
                - toc (bool): Whether to include a table of contents (default: False)
                - toc_depth (int): Depth of the table of contents (default: 3)
                - css (str): Path to a CSS file for styling HTML or PDF output
                - highlight_style (str): Code highlighting style (default: 'github')
                - template (str): Path to a template file for Pandoc conversions
                - include_metadata (bool): Whether to include YAML metadata (default: True)
                - pdf_options (Dict): Additional options for PDF conversion
            
        Returns:
            str: Path to the converted file
        """
        options = options or {}
        toc = options.get('toc', False)
        toc_depth = options.get('toc_depth', 3)
        css_path = options.get('css', None)
        highlight_style = options.get('highlight_style', 'github')
        template_path = options.get('template', None)
        include_metadata = options.get('include_metadata', True)
        pdf_options = options.get('pdf_options', {})
        
        # Generate target path if not provided
        if not target_path:
            target_dir = os.path.dirname(source_path)
            filename = generate_unique_filename(self.target_format)
            target_path = os.path.join(target_dir, filename)
        
        # Check dependencies
        self._ensure_dependencies()
        
        try:
            # Read markdown content
            with open(source_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # HTML conversion
            if self.target_format == 'html':
                self._convert_to_html(markdown_content, target_path, toc, toc_depth, css_path, highlight_style)
            
            # PDF conversion
            elif self.target_format == 'pdf':
                self._convert_to_pdf(markdown_content, target_path, toc, toc_depth, css_path, highlight_style, pdf_options)
            
            # Plain text conversion
            elif self.target_format == 'txt':
                self._convert_to_text(markdown_content, target_path)
            
            # DOCX, EPUB, LaTeX conversion using Pandoc
            elif self.target_format in ['docx', 'epub', 'latex', 'tex']:
                self._convert_with_pandoc(source_path, target_path, toc, toc_depth, template_path, highlight_style, include_metadata)
            
            else:
                raise ValueError(f"Unsupported target format: {self.target_format}")
            
            logger.info(f"Successfully converted Markdown to {self.target_format}: {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error converting Markdown to {self.target_format}: {e}")
            raise ValueError(f"Failed to convert Markdown to {self.target_format}: {e}")
    
    def _convert_to_html(self, markdown_content: str, target_path: str, toc: bool, toc_depth: int, 
                         css_path: Optional[str], highlight_style: str) -> None:
        """
        Convert Markdown to HTML
        
        Args:
            markdown_content (str): Markdown content to convert
            target_path (str): Path to save HTML output
            toc (bool): Whether to include a table of contents
            toc_depth (int): Depth of the table of contents
            css_path (str, optional): Path to a CSS file for styling
            highlight_style (str): Code highlighting style
        """
        import markdown
        from pygments.formatters import HtmlFormatter
        from bs4 import BeautifulSoup
        
        # Configure extensions
        extensions = [
            'markdown.extensions.extra',  # Includes tables, code blocks, etc.
            'markdown.extensions.codehilite',  # Code highlighting
            'markdown.extensions.smarty',  # Smart typography
            'markdown.extensions.sane_lists',  # Better list handling
        ]
        
        # Add TOC extension if requested
        if toc:
            extensions.append('markdown.extensions.toc')
        
        # Configure extension settings
        extension_configs = {
            'markdown.extensions.codehilite': {
                'pygments_style': highlight_style,
                'noclasses': False
            }
        }
        
        # Convert markdown to HTML
        html = markdown.markdown(
            markdown_content, 
            extensions=extensions,
            extension_configs=extension_configs
        )
        
        # Add table of contents if requested
        if toc:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find or create TOC div
            toc_div = soup.find('div', {'class': 'toc'})
            if not toc_div:
                # Create TOC by adding a marker and re-processing
                toc_marker = f'[TOC]\n\n'
                html = markdown.markdown(
                    toc_marker + markdown_content,
                    extensions=extensions,
                    extension_configs=extension_configs
                )
                soup = BeautifulSoup(html, 'html.parser')
        
        # Read CSS content if provided
        css_content = ""
        if css_path and os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        else:
            # Default CSS for syntax highlighting
            css_content = HtmlFormatter(style=highlight_style).get_style_defs('.codehilite')
            css_content += """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            pre {
                background-color: #f6f8fa;
                border-radius: 3px;
                padding: 16px;
                overflow: auto;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
                text-align: left;
            }
            blockquote {
                border-left: 4px solid #ddd;
                padding-left: 16px;
                margin-left: 0;
                color: #666;
            }
            img {
                max-width: 100%;
            }
            .toc {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 16px;
                margin-bottom: 24px;
            }
            .toc ul {
                list-style-type: none;
                padding-left: 20px;
            }
            .toc li {
                margin-bottom: 8px;
            }
            .toc a {
                text-decoration: none;
                color: #0366d6;
            }
            """
        
        # Create complete HTML document
        html_doc = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Converted Markdown</title>
            <style>
            {css_content}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        # Write HTML to file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(html_doc)
    
    def _convert_to_pdf(self, markdown_content: str, target_path: str, toc: bool, toc_depth: int, 
                        css_path: Optional[str], highlight_style: str, pdf_options: Dict[str, Any]) -> None:
        """
        Convert Markdown to PDF via HTML
        
        Args:
            markdown_content (str): Markdown content to convert
            target_path (str): Path to save PDF output
            toc (bool): Whether to include a table of contents
            toc_depth (int): Depth of the table of contents
            css_path (str, optional): Path to a CSS file for styling
            highlight_style (str): Code highlighting style
            pdf_options (Dict): Additional options for PDF conversion
        """
        # First convert to HTML
        temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
        try:
            temp_html.close()
            self._convert_to_html(markdown_content, temp_html.name, toc, toc_depth, css_path, highlight_style)
            
            # Convert HTML to PDF using pdfkit or WeasyPrint
            try:
                import pdfkit
                
                # Configure PDF options
                pdf_opts = {
                    'page-size': pdf_options.get('page_size', 'A4'),
                    'margin-top': pdf_options.get('margin_top', '20mm'),
                    'margin-right': pdf_options.get('margin_right', '20mm'),
                    'margin-bottom': pdf_options.get('margin_bottom', '20mm'),
                    'margin-left': pdf_options.get('margin_left', '20mm'),
                    'encoding': pdf_options.get('encoding', 'UTF-8'),
                    'no-outline': None if pdf_options.get('outline', True) else '',
                    'enable-local-file-access': ''
                }
                
                # Add custom header and footer if provided
                header_html = pdf_options.get('header_html')
                footer_html = pdf_options.get('footer_html')
                
                if header_html:
                    pdf_opts['header-html'] = header_html
                
                if footer_html:
                    pdf_opts['footer-html'] = footer_html
                
                # Generate PDF
                pdfkit.from_file(temp_html.name, target_path, options=pdf_opts)
                
            except ImportError:
                # Fall back to WeasyPrint if pdfkit is not available
                try:
                    from weasyprint import HTML
                    HTML(temp_html.name).write_pdf(target_path)
                except ImportError:
                    # Fall back to Pandoc as last resort
                    cmd = [
                        'pandoc', temp_html.name, 
                        '-o', target_path,
                        '--pdf-engine=wkhtmltopdf'
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise ValueError(f"Pandoc PDF conversion failed: {result.stderr}")
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_html.name):
                os.remove(temp_html.name)
    
    def _convert_to_text(self, markdown_content: str, target_path: str) -> None:
        """
        Convert Markdown to plain text
        
        Args:
            markdown_content (str): Markdown content to convert
            target_path (str): Path to save text output
        """
        # Try using html2text if available
        try:
            import html2text
            import markdown
            
            # First convert to HTML
            html = markdown.markdown(markdown_content, extensions=['markdown.extensions.extra'])
            
            # Then convert HTML to plain text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # No text wrapping
            
            text = h.handle(html)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
        except ImportError:
            # Simple fallback for basic markdown to text conversion
            import re
            
            # Remove headings markdown syntax
            text = re.sub(r'^#{1,6}\s+', '', markdown_content, flags=re.MULTILINE)
            
            # Remove emphasis markers
            text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
            text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
            
            # Replace links with their text
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
            
            # Replace images with their alt text
            text = re.sub(r'!\[(.*?)\]\(.*?\)', r'[Image: \1]', text)
            
            # Replace horizontal rules
            text = re.sub(r'^\s*[-*_]{3,}\s*$', '\n---\n', text, flags=re.MULTILINE)
            
            # Write to file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(text)
    
    def _convert_with_pandoc(self, source_path: str, target_path: str, toc: bool, toc_depth: int,
                            template_path: Optional[str], highlight_style: str, include_metadata: bool) -> None:
        """
        Convert Markdown to other formats using Pandoc
        
        Args:
            source_path (str): Path to the source markdown file
            target_path (str): Path to save the output file
            toc (bool): Whether to include a table of contents
            toc_depth (int): Depth of the table of contents
            template_path (str, optional): Path to a template file
            highlight_style (str): Code highlighting style
            include_metadata (bool): Whether to include YAML metadata
        """
        # Base Pandoc command
        cmd = ['pandoc', source_path, '-o', target_path]
        
        # Add table of contents if requested
        if toc:
            cmd.extend(['--toc', f'--toc-depth={toc_depth}'])
        
        # Add syntax highlighting
        cmd.extend(['--highlight-style', highlight_style])
        
        # Add template if provided
        if template_path and os.path.exists(template_path):
            cmd.extend(['--template', template_path])
        
        # Handle metadata
        if not include_metadata:
            cmd.append('--standalone')
        
        # Format-specific options
        if self.target_format == 'docx':
            cmd.append('--reference-doc=reference.docx') if os.path.exists('reference.docx') else None
        elif self.target_format == 'epub':
            cmd.extend(['--epub-cover-image=cover.jpg']) if os.path.exists('cover.jpg') else None
        elif self.target_format in ['latex', 'tex']:
            cmd.append('--pdf-engine=xelatex')
        
        # Run Pandoc
        logger.info(f"Running Pandoc command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Pandoc conversion failed: {result.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @staticmethod
    def extract_metadata(markdown_path: str) -> Dict[str, Any]:
        """
        Extract YAML metadata from a markdown file
        
        Args:
            markdown_path (str): Path to the markdown file
            
        Returns:
            Dict[str, Any]: Dictionary of metadata fields
        """
        try:
            import yaml
            
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for YAML frontmatter (between --- markers)
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            
            if frontmatter_match:
                yaml_text = frontmatter_match.group(1)
                metadata = yaml.safe_load(yaml_text)
                return metadata if metadata else {}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error extracting markdown metadata: {e}")
            return {}
    
    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """
        Convert HTML to Markdown
        
        Args:
            html_content (str): HTML content to convert
            
        Returns:
            str: Converted markdown content
        """
        try:
            import html2text
            
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # No text wrapping
            h.unicode_snob = True  # Use unicode instead of ASCII
            h.single_line_break = False  # Use two line breaks for new paragraphs
            
            markdown_content = h.handle(html_content)
            return markdown_content
            
        except ImportError:
            # If html2text is not available, try using pandoc
            try:
                with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as f:
                    f.write(html_content)
                    temp_html_path = f.name
                
                try:
                    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as out_f:
                        temp_md_path = out_f.name
                    
                    cmd = ['pandoc', temp_html_path, '-o', temp_md_path, '-f', 'html', '-t', 'markdown']
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    with open(temp_md_path, 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                    
                    return markdown_content
                    
                finally:
                    # Clean up temporary files
                    if os.path.exists(temp_html_path):
                        os.remove(temp_html_path)
                    if os.path.exists(temp_md_path):
                        os.remove(temp_md_path)
                        
            except Exception as e:
                logger.error(f"Error converting HTML to Markdown: {e}")
                raise ValueError(f"Failed to convert HTML to Markdown: {e}")
        
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {e}")
            raise ValueError(f"Failed to convert HTML to Markdown: {e}") 