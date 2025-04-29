import os
import uuid
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): Filename to check
        allowed_extensions (list): List of allowed extensions
        
    Returns:
        bool: True if file has an allowed extension, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_extension(filename):
    """
    Get file extension from filename
    
    Args:
        filename (str): Filename to check
        
    Returns:
        str: File extension without dot
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

def generate_unique_filename(filename, extension=None):
    """
    Generate a unique filename based on the original
    
    Args:
        filename (str): Original filename
        extension (str, optional): New extension to use. If None, uses original extension.
        
    Returns:
        str: Unique filename
    """
    # Get base filename without extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
    else:
        name = filename
        ext = ''
    
    # Use provided extension if available
    if extension:
        ext = extension
    
    # Generate a UUID to ensure uniqueness
    unique_id = uuid.uuid4().hex[:8]
    
    # Secure the filename to ensure it doesn't contain unsafe characters
    secure_name = secure_filename(name)
    
    # Combine with timestamp and UUID for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    if ext:
        return f"{secure_name}_{timestamp}_{unique_id}.{ext}"
    else:
        return f"{secure_name}_{timestamp}_{unique_id}"

def get_upload_path(filename, subfolder=None):
    """
    Get the full path to save a file in the upload folder
    
    Args:
        filename (str): Filename to save
        subfolder (str, optional): Subfolder within the upload folder
        
    Returns:
        str: Full path to save the file
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # If subfolder provided, create if it doesn't exist
    if subfolder:
        subfolder_path = os.path.join(upload_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path, exist_ok=True)
        return os.path.join(subfolder_path, filename)
    
    return os.path.join(upload_folder, filename)

def validate_file_size(file):
    """
    Check if a file is within the allowed size
    
    Args:
        file (FileStorage): File to check
        
    Returns:
        bool: True if file is within the allowed size, False otherwise
    """
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    return file_size <= current_app.config['MAX_CONTENT_LENGTH']

def get_mimetype_for_format(format_name):
    """
    Get the MIME type for a file format
    
    Args:
        format_name (str): File format (e.g., 'pdf', 'jpg')
        
    Returns:
        str: MIME type for the format
    """
    mime_types = {
        # Documents
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'html': 'text/html',
        'htm': 'text/html',
        'rtf': 'application/rtf',
        
        # Spreadsheets
        'csv': 'text/csv',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        
        # Data formats
        'json': 'application/json',
        'xml': 'application/xml',
        'yaml': 'application/x-yaml',
        'yml': 'application/x-yaml',
        
        # Images
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'svg': 'image/svg+xml',
        
        # Audio
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'aac': 'audio/aac',
        'm4a': 'audio/mp4',
        
        # Video
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'wmv': 'video/x-ms-wmv',
    }
    
    return mime_types.get(format_name.lower(), 'application/octet-stream')

def cleanup_expired_files():
    """
    Delete expired files from the upload folder
    
    This function is meant to be run periodically to clean up old files.
    """
    try:
        logger.info("Starting cleanup of expired files")
        upload_folder = current_app.config['UPLOAD_FOLDER']
        expiry_days = current_app.config.get('FILE_EXPIRY_DAYS', 7)
        expiry_date = datetime.now() - timedelta(days=expiry_days)
        
        # Get all conversions from the database
        from app.models.conversion import Conversion
        
        # Find expired conversions
        expired_conversions = Conversion.query.filter(
            Conversion.expires_at < datetime.utcnow()
        ).all()
        
        deleted_count = 0
        errors = 0
        
        for conversion in expired_conversions:
            # Delete source file
            try:
                if conversion.source_file_path and os.path.exists(conversion.source_file_path):
                    os.remove(conversion.source_file_path)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting source file {conversion.source_file_path}: {str(e)}")
                errors += 1
            
            # Delete target file
            try:
                if conversion.target_file_path and os.path.exists(conversion.target_file_path):
                    os.remove(conversion.target_file_path)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting target file {conversion.target_file_path}: {str(e)}")
                errors += 1
            
            # Mark conversion as expired in database
            conversion.status = 'expired'
        
        # Commit changes to database
        from app.models.db import db
        db.session.commit()
        
        logger.info(f"Cleanup completed: {deleted_count} files deleted, {errors} errors")
        return deleted_count, errors
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        return 0, 1 