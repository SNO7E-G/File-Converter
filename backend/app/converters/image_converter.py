import os
import logging
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage

from app.converters.base_converter import BaseConverter, conversion_timer
from app.utils.file_utils import get_file_extension, generate_unique_filename

# Set up logging
logger = logging.getLogger(__name__)

class ImageConverter(BaseConverter):
    """
    Converter for image files between various formats
    """
    
    # Define supported source and target formats
    SOURCE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg']
    TARGET_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'pdf', 'ico']
    
    def __init__(self, source_format: str, target_format: str):
        """
        Initialize the image converter
        
        Args:
            source_format (str): Source file format
            target_format (str): Target file format
        """
        super().__init__(source_format, target_format)
        logger.info(f"Image converter initialized: {source_format} -> {target_format}")
    
    @staticmethod
    def supports_target_format(target_format: str) -> bool:
        """
        Check if the target format is supported by this converter
        
        Args:
            target_format (str): The target format to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return target_format.lower() in ImageConverter.TARGET_FORMATS
    
    def _ensure_dependencies(self):
        """
        Check if required dependencies are installed
        
        Raises:
            ValueError: If required dependencies are not available
        """
        try:
            from PIL import Image, ImageOps
            import cairosvg
        except ImportError as e:
            missing_dep = str(e).split("'")[1] if "'" in str(e) else str(e)
            logger.error(f"Missing dependency: {missing_dep}")
            raise ValueError(f"Missing dependency: {missing_dep}. Please install the required packages.")
    
    @conversion_timer
    def convert(self, source_path: str, target_path: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Convert image file to target format
        
        Args:
            source_path (str): Path to the source file
            target_path (str, optional): Path for the target file, generated if None
            options (Dict[str, Any], optional): Additional options for conversion
                - quality (int): Image quality for lossy formats (1-100, default: 90)
                - resize (tuple): Target size as (width, height)
                - dpi (int): DPI for the output image (default: 300)
                - optimize (bool): Whether to optimize the image (default: True)
                - grayscale (bool): Convert to grayscale (default: False)
                - rotate (int): Rotation angle in degrees (default: 0)
                - flip (str): Flip image ('horizontal', 'vertical', or None)
            
        Returns:
            str: Path to the converted file
        """
        options = options or {}
        quality = options.get('quality', 90)
        resize = options.get('resize', None)
        dpi = options.get('dpi', 300)
        optimize = options.get('optimize', True)
        grayscale = options.get('grayscale', False)
        rotate = options.get('rotate', 0)
        flip = options.get('flip', None)
        
        # Generate target path if not provided
        if not target_path:
            target_dir = os.path.dirname(source_path)
            filename = generate_unique_filename(self.target_format)
            target_path = os.path.join(target_dir, filename)
        
        # Check dependencies
        self._ensure_dependencies()
        
        try:
            # SVG to other formats using cairosvg
            if self.source_format.lower() == 'svg' and self.target_format.lower() != 'svg':
                import cairosvg
                
                if self.target_format.lower() == 'png':
                    cairosvg.svg2png(url=source_path, write_to=target_path, dpi=dpi)
                elif self.target_format.lower() == 'pdf':
                    cairosvg.svg2pdf(url=source_path, write_to=target_path)
                elif self.target_format.lower() in ['jpg', 'jpeg']:
                    # Convert to PNG first, then to JPEG
                    temp_png = f"{target_path}.temp.png"
                    cairosvg.svg2png(url=source_path, write_to=temp_png, dpi=dpi)
                    
                    from PIL import Image
                    img = Image.open(temp_png)
                    if img.mode == 'RGBA':
                        # JPEG doesn't support alpha channel, convert to RGB
                        img = img.convert('RGB')
                    img.save(target_path, quality=quality, optimize=optimize)
                    
                    # Remove temporary file
                    if os.path.exists(temp_png):
                        os.remove(temp_png)
                else:
                    # For other formats, convert to PNG first and then use PIL
                    temp_png = f"{target_path}.temp.png"
                    cairosvg.svg2png(url=source_path, write_to=temp_png, dpi=dpi)
                    
                    from PIL import Image
                    img = Image.open(temp_png)
                    self._apply_transformations(img, target_path, grayscale, resize, rotate, flip, quality, optimize)
                    
                    # Remove temporary file
                    if os.path.exists(temp_png):
                        os.remove(temp_png)
            
            # All other image conversions using PIL
            else:
                from PIL import Image, ImageOps
                
                # Open the image
                img = Image.open(source_path)
                
                # Apply transformations and save the image
                self._apply_transformations(img, target_path, grayscale, resize, rotate, flip, quality, optimize)
            
            logger.info(f"Successfully converted image to {self.target_format}: {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error converting image to {self.target_format}: {e}")
            raise ValueError(f"Failed to convert image to {self.target_format}: {e}")
    
    def _apply_transformations(self, img, target_path: str, grayscale: bool, resize, rotate: int, 
                               flip: Optional[str], quality: int, optimize: bool):
        """
        Apply transformations to the image and save it
        
        Args:
            img: PIL Image object
            target_path (str): Path to save the transformed image
            grayscale (bool): Whether to convert to grayscale
            resize: Target size as (width, height) or None
            rotate (int): Rotation angle in degrees
            flip (str): Direction to flip the image ('horizontal', 'vertical', or None)
            quality (int): Image quality for lossy formats
            optimize (bool): Whether to optimize the image
            
        Returns:
            None
        """
        from PIL import Image, ImageOps
        
        # Convert to grayscale if requested
        if grayscale:
            img = img.convert('L')
        
        # Resize the image if requested
        if resize and isinstance(resize, (tuple, list)) and len(resize) == 2:
            img = img.resize(resize, Image.Resampling.LANCZOS)
        
        # Rotate the image if requested
        if rotate:
            img = img.rotate(rotate, expand=True)
        
        # Flip the image if requested
        if flip:
            if flip.lower() == 'horizontal':
                img = ImageOps.mirror(img)
            elif flip.lower() == 'vertical':
                img = ImageOps.flip(img)
        
        # Ensure RGB mode for JPG (which doesn't support alpha)
        if self.target_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Save the image with appropriate options
        save_kwargs = {'quality': quality, 'optimize': optimize} if self.target_format.lower() in ['jpg', 'jpeg'] else {}
        
        # Special handling for specific formats
        if self.target_format.lower() == 'gif':
            save_kwargs = {}  # GIF doesn't support quality and optimize
        elif self.target_format.lower() == 'png':
            save_kwargs = {'optimize': optimize}
        elif self.target_format.lower() == 'ico':
            # ICO requires specific sizes
            if not resize:
                # Default to 32x32 for ICO if no resize specified
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                
        # Save the image
        img.save(target_path, **save_kwargs)
    
    @staticmethod
    def get_image_info(image_path: str) -> Dict[str, Any]:
        """
        Get information about an image file
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            Dict[str, Any]: Dictionary with image information
        """
        try:
            from PIL import Image, ExifTags
            
            img = Image.open(image_path)
            info = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
            }
            
            # Try to get EXIF data
            exif_data = {}
            if hasattr(img, '_getexif') and img._getexif():
                for tag, value in img._getexif().items():
                    if tag in ExifTags.TAGS:
                        exif_data[ExifTags.TAGS[tag]] = value
            
            info['exif'] = exif_data
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise ValueError(f"Failed to get image info: {e}")
    
    @staticmethod
    def create_thumbnail(image_path: str, output_path: str, size: tuple = (128, 128), 
                         format: Optional[str] = None, quality: int = 90) -> str:
        """
        Create a thumbnail from an image file
        
        Args:
            image_path (str): Path to the image file
            output_path (str): Path for the output thumbnail
            size (tuple): Target size as (width, height)
            format (str, optional): Output format, inferred from output_path if None
            quality (int): Image quality for lossy formats
            
        Returns:
            str: Path to the created thumbnail
        """
        try:
            from PIL import Image
            
            # Open the image
            img = Image.open(image_path)
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Determine format
            if format:
                output_format = format.upper()
            else:
                output_format = os.path.splitext(output_path)[1][1:].upper()
                if output_format == 'JPG':
                    output_format = 'JPEG'
            
            # Convert to RGB for JPEG
            if output_format == 'JPEG' and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Save thumbnail
            save_kwargs = {'quality': quality} if output_format == 'JPEG' else {}
            img.save(output_path, output_format, **save_kwargs)
            
            logger.info(f"Successfully created thumbnail: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise ValueError(f"Failed to create thumbnail: {e}")
    
    @staticmethod
    def create_collage(image_paths: List[str], output_path: str, grid_size: tuple = None, 
                       margin: int = 10, background_color: tuple = (255, 255, 255)) -> str:
        """
        Create a collage from multiple images
        
        Args:
            image_paths (List[str]): Paths to the image files
            output_path (str): Path for the output collage
            grid_size (tuple, optional): Grid size as (columns, rows), auto-calculated if None
            margin (int): Margin between images
            background_color (tuple): RGB color tuple for the background
            
        Returns:
            str: Path to the created collage
        """
        try:
            from PIL import Image
            from math import ceil, sqrt
            
            # Determine grid size if not provided
            if not grid_size:
                num_images = len(image_paths)
                cols = ceil(sqrt(num_images))
                rows = ceil(num_images / cols)
                grid_size = (cols, rows)
            else:
                cols, rows = grid_size
            
            # Open all images
            images = []
            for path in image_paths:
                try:
                    img = Image.open(path)
                    # Ensure consistent mode
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                except Exception as e:
                    logger.warning(f"Could not open image {path}: {e}")
            
            if not images:
                raise ValueError("No valid images provided for collage")
            
            # Determine cell size (use the median size to avoid extremes)
            widths = [img.width for img in images]
            heights = [img.height for img in images]
            widths.sort()
            heights.sort()
            cell_width = widths[len(widths) // 2] if widths else 100
            cell_height = heights[len(heights) // 2] if heights else 100
            
            # Create the collage image
            collage_width = cols * cell_width + (cols + 1) * margin
            collage_height = rows * cell_height + (rows + 1) * margin
            collage = Image.new('RGB', (collage_width, collage_height), background_color)
            
            # Place images in the grid
            for i, img in enumerate(images):
                if i >= cols * rows:
                    break  # Skip if we have more images than cells
                
                # Calculate position in grid
                row = i // cols
                col = i % cols
                
                # Resize image to fit cell
                img_resized = img.copy()
                img_resized.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
                
                # Calculate position in collage
                x = col * cell_width + (col + 1) * margin + (cell_width - img_resized.width) // 2
                y = row * cell_height + (row + 1) * margin + (cell_height - img_resized.height) // 2
                
                # Paste image into collage
                collage.paste(img_resized, (x, y))
            
            # Save collage
            collage.save(output_path)
            
            logger.info(f"Successfully created collage from {len(images)} images: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating collage: {e}")
            raise ValueError(f"Failed to create collage: {e}") 