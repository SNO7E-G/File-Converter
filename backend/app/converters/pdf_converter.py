import os
import logging
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage

from app.converters.base_converter import BaseConverter, conversion_timer
from app.utils.file_utils import get_file_extension, generate_unique_filename

# Set up logging
logger = logging.getLogger(__name__)

class PDFConverter(BaseConverter):
    """
    Converter for PDF files to various formats and vice versa
    """
    
    # Define supported source and target formats
    SOURCE_FORMATS = ['pdf']
    TARGET_FORMATS = ['png', 'jpg', 'jpeg', 'tiff', 'txt', 'html', 'docx']
    
    def __init__(self, source_format: str, target_format: str):
        """
        Initialize the PDF converter
        
        Args:
            source_format (str): Source file format (pdf)
            target_format (str): Target file format
        """
        super().__init__(source_format, target_format)
        logger.info(f"PDF converter initialized: {source_format} -> {target_format}")
    
    @staticmethod
    def supports_target_format(target_format: str) -> bool:
        """
        Check if the target format is supported by this converter
        
        Args:
            target_format (str): The target format to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return target_format.lower() in PDFConverter.TARGET_FORMATS
    
    def _ensure_dependencies(self):
        """
        Check if required dependencies are installed
        
        Raises:
            ValueError: If required dependencies are not available
        """
        dependencies = {
            'pdf2image': 'Convert PDF to images',
            'pytesseract': 'OCR capabilities',
            'PyPDF2': 'PDF manipulation',
            'pdf2docx': 'Convert PDF to DOCX',
        }
        
        missing_deps = []
        for dep, purpose in dependencies.items():
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(f"{dep} ({purpose})")
        
        if missing_deps:
            error_msg = f"Missing dependencies: {', '.join(missing_deps)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @conversion_timer
    def convert(self, source_path: str, target_path: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Convert PDF file to target format
        
        Args:
            source_path (str): Path to the source file
            target_path (str, optional): Path for the target file, generated if None
            options (Dict[str, Any], optional): Additional options for conversion
                - page_numbers (List[int]): List of page numbers to convert (1-indexed)
                - dpi (int): DPI for image conversion (default: 200)
                - quality (int): Quality for JPG conversion (0-100, default: 90)
                - ocr (bool): Whether to use OCR for text extraction (default: True)
                - ocr_lang (str): Language for OCR (default: 'eng')
            
        Returns:
            str: Path to the converted file
        """
        options = options or {}
        page_numbers = options.get('page_numbers', None)  # None means all pages
        dpi = options.get('dpi', 200)
        quality = options.get('quality', 90)
        use_ocr = options.get('ocr', True)
        ocr_lang = options.get('ocr_lang', 'eng')
        
        # Generate target path if not provided
        if not target_path:
            target_dir = os.path.dirname(source_path)
            filename = generate_unique_filename(self.target_format)
            target_path = os.path.join(target_dir, filename)
        
        # Check dependencies
        self._ensure_dependencies()
        
        # Perform conversion based on target format
        try:
            # Image formats (png, jpg, tiff)
            if self.target_format in ['png', 'jpg', 'jpeg', 'tiff']:
                from pdf2image import convert_from_path
                
                # Convert PDF to images
                images = convert_from_path(
                    source_path, 
                    dpi=dpi,
                    first_page=page_numbers[0] if page_numbers else None,
                    last_page=page_numbers[-1] if page_numbers else None
                )
                
                # Handle single page or multiple pages
                if len(images) == 1 or (page_numbers and len(page_numbers) == 1):
                    # Save single image
                    if self.target_format in ['jpg', 'jpeg']:
                        images[0].save(target_path, 'JPEG', quality=quality)
                    elif self.target_format == 'png':
                        images[0].save(target_path, 'PNG')
                    elif self.target_format == 'tiff':
                        images[0].save(target_path, 'TIFF')
                else:
                    # Save multiple images with page numbers
                    base_path, ext = os.path.splitext(target_path)
                    saved_paths = []
                    
                    for i, image in enumerate(images):
                        page_path = f"{base_path}_page_{i+1}{ext}"
                        if self.target_format in ['jpg', 'jpeg']:
                            image.save(page_path, 'JPEG', quality=quality)
                        elif self.target_format == 'png':
                            image.save(page_path, 'PNG')
                        elif self.target_format == 'tiff':
                            image.save(page_path, 'TIFF')
                        saved_paths.append(page_path)
                    
                    # Return the directory or first file
                    return saved_paths[0]
            
            # Text extraction
            elif self.target_format == 'txt':
                if use_ocr:
                    # Use OCR for text extraction
                    import pytesseract
                    from pdf2image import convert_from_path
                    
                    # Convert PDF to images
                    images = convert_from_path(
                        source_path,
                        dpi=dpi,
                        first_page=page_numbers[0] if page_numbers else None,
                        last_page=page_numbers[-1] if page_numbers else None
                    )
                    
                    # Extract text from each image
                    with open(target_path, 'w', encoding='utf-8') as f:
                        for i, image in enumerate(images):
                            if page_numbers is None or (i + 1) in page_numbers:
                                page_text = pytesseract.image_to_string(image, lang=ocr_lang)
                                f.write(f"--- Page {i + 1} ---\n{page_text}\n\n")
                else:
                    # Use PyPDF2 for text extraction (less accurate but faster)
                    import PyPDF2
                    
                    with open(source_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        num_pages = len(reader.pages)
                        
                        with open(target_path, 'w', encoding='utf-8') as f:
                            for i in range(num_pages):
                                if page_numbers is None or (i + 1) in page_numbers:
                                    page = reader.pages[i]
                                    f.write(f"--- Page {i + 1} ---\n{page.extract_text()}\n\n")
            
            # HTML conversion
            elif self.target_format == 'html':
                import PyPDF2
                from pdf2image import convert_from_path
                import base64
                from io import BytesIO
                
                # Convert PDF to images for embedding
                images = convert_from_path(
                    source_path,
                    dpi=dpi,
                    first_page=page_numbers[0] if page_numbers else None,
                    last_page=page_numbers[-1] if page_numbers else None
                )
                
                # Extract text using PyPDF2
                with open(source_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    
                    # Create HTML content
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write("""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>PDF Conversion</title>
                            <style>
                                body { font-family: Arial, sans-serif; line-height: 1.6; }
                                .page { margin-bottom: 20px; border: 1px solid #ddd; padding: 20px; }
                                .page-image { max-width: 100%; height: auto; }
                                .page-text { margin-top: 10px; }
                            </style>
                        </head>
                        <body>
                            <h1>PDF Conversion</h1>
                        """)
                        
                        for i, image in enumerate(images):
                            if page_numbers is None or (i + 1) in page_numbers:
                                # Convert image to base64 for embedding
                                buffered = BytesIO()
                                image.save(buffered, format="PNG")
                                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                
                                # Extract text
                                page_text = ""
                                if i < len(reader.pages):
                                    page_text = reader.pages[i].extract_text()
                                
                                # Write page to HTML
                                f.write(f"""
                                <div class="page">
                                    <h2>Page {i + 1}</h2>
                                    <img class="page-image" src="data:image/png;base64,{img_base64}" alt="Page {i + 1}">
                                    <div class="page-text">
                                        <pre>{page_text}</pre>
                                    </div>
                                </div>
                                """)
                        
                        f.write("""
                        </body>
                        </html>
                        """)
            
            # DOCX conversion
            elif self.target_format == 'docx':
                from pdf2docx import Converter
                
                # Convert PDF to DOCX
                cv = Converter(source_path)
                cv.convert(target_path, start=page_numbers[0] if page_numbers else None, 
                          end=page_numbers[-1] if page_numbers else None)
                cv.close()
            
            else:
                raise ValueError(f"Unsupported target format: {self.target_format}")
            
            logger.info(f"Successfully converted PDF to {self.target_format}: {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error converting PDF to {self.target_format}: {e}")
            raise ValueError(f"Failed to convert PDF to {self.target_format}: {e}")
    
    @staticmethod
    def create_pdf_from_images(images: List[str], output_path: str, options: Dict[str, Any] = None) -> str:
        """
        Create a PDF from a list of image files
        
        Args:
            images (List[str]): List of image file paths
            output_path (str): Path for the output PDF file
            options (Dict[str, Any], optional): Additional options
                - quality (int): Quality for PDF conversion (0-100, default: 90)
            
        Returns:
            str: Path to the created PDF file
        """
        options = options or {}
        quality = options.get('quality', 90)
        
        try:
            from PIL import Image
            
            # Convert images to PDF
            image_list = []
            first_image = None
            
            for img_path in images:
                img = Image.open(img_path)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                if first_image is None:
                    first_image = img
                else:
                    image_list.append(img)
            
            if first_image:
                first_image.save(
                    output_path, 
                    save_all=True,
                    append_images=image_list,
                    quality=quality
                )
                
                logger.info(f"Successfully created PDF from {len(images)} images: {output_path}")
                return output_path
            else:
                raise ValueError("No valid images provided")
                
        except Exception as e:
            logger.error(f"Error creating PDF from images: {e}")
            raise ValueError(f"Failed to create PDF from images: {e}")
    
    @staticmethod
    def create_pdf_from_html(html_file: str, output_path: str, options: Dict[str, Any] = None) -> str:
        """
        Create a PDF from an HTML file
        
        Args:
            html_file (str): Path to the HTML file
            output_path (str): Path for the output PDF file
            options (Dict[str, Any], optional): Additional options
            
        Returns:
            str: Path to the created PDF file
        """
        options = options or {}
        
        try:
            # Try using WeasyPrint (pure Python)
            try:
                from weasyprint import HTML
                HTML(html_file).write_pdf(output_path)
            except ImportError:
                # Fall back to wkhtmltopdf command line tool
                try:
                    subprocess.run(
                        ['wkhtmltopdf', html_file, output_path],
                        check=True,
                        capture_output=True
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    raise ValueError("No PDF generation library available (install WeasyPrint or wkhtmltopdf)")
            
            logger.info(f"Successfully created PDF from HTML: {output_path}")
            return output_path
                
        except Exception as e:
            logger.error(f"Error creating PDF from HTML: {e}")
            raise ValueError(f"Failed to create PDF from HTML: {e}")
    
    @staticmethod
    def create_pdf_from_text(text_file: str, output_path: str, options: Dict[str, Any] = None) -> str:
        """
        Create a PDF from a text file
        
        Args:
            text_file (str): Path to the text file
            output_path (str): Path for the output PDF file
            options (Dict[str, Any], optional): Additional options
                - font_size (int): Font size (default: 12)
                - font_family (str): Font family (default: 'Helvetica')
            
        Returns:
            str: Path to the created PDF file
        """
        options = options or {}
        font_size = options.get('font_size', 12)
        font_family = options.get('font_family', 'Helvetica')
        
        try:
            # Try using FPDF (pure Python)
            try:
                from fpdf import FPDF
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font(font_family, size=font_size)
                
                # Read text file
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Handle line breaks and write to PDF
                for line in text.split('\n'):
                    pdf.cell(0, 10, line, ln=True)
                
                pdf.output(output_path)
                
            except ImportError:
                # Fall back to creating an HTML file and converting it
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Create temporary HTML file
                with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
                    temp_html_path = temp.name
                    temp.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Text to PDF</title>
                        <style>
                            body {{ font-family: {font_family}; font-size: {font_size}pt; line-height: 1.6; }}
                            pre {{ white-space: pre-wrap; }}
                        </style>
                    </head>
                    <body>
                        <pre>{text}</pre>
                    </body>
                    </html>
                    """.encode('utf-8'))
                
                # Convert HTML to PDF
                result = PDFConverter.create_pdf_from_html(temp_html_path, output_path)
                
                # Clean up
                if os.path.exists(temp_html_path):
                    os.remove(temp_html_path)
                
                return result
            
            logger.info(f"Successfully created PDF from text: {output_path}")
            return output_path
                
        except Exception as e:
            logger.error(f"Error creating PDF from text: {e}")
            raise ValueError(f"Failed to create PDF from text: {e}")
    
    @staticmethod
    def merge_pdfs(pdf_files: List[str], output_path: str) -> str:
        """
        Merge multiple PDF files into a single PDF
        
        Args:
            pdf_files (List[str]): List of PDF file paths to merge
            output_path (str): Path for the output merged PDF file
            
        Returns:
            str: Path to the merged PDF file
        """
        try:
            import PyPDF2
            
            writer = PyPDF2.PdfWriter()
            
            # Add pages from each PDF
            for pdf_file in pdf_files:
                with open(pdf_file, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        writer.add_page(page)
            
            # Write merged PDF to output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Successfully merged {len(pdf_files)} PDFs: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            raise ValueError(f"Failed to merge PDFs: {e}") 