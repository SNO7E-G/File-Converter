from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required

from app.converters.converter_factory import converter_factory

formats_bp = Blueprint('formats', __name__, url_prefix='/api/formats')

@formats_bp.route('', methods=['GET'])
def get_formats():
    """
    Returns all supported formats and available conversion paths
    """
    try:
        formats = {
            'supported_formats': converter_factory.get_supported_formats(),
            'conversion_paths': converter_factory.get_all_conversion_paths()
        }
        return jsonify(formats), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving formats: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve formats", "message": str(e)}), 500

@formats_bp.route('/conversions', methods=['GET'])
def get_conversion_paths():
    """
    Returns all supported conversion paths
    """
    try:
        conversion_paths = converter_factory.get_all_conversion_paths()
        return jsonify(conversion_paths), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving conversion paths: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve conversion paths", "message": str(e)}), 500

@formats_bp.route('/options', methods=['GET'])
def get_conversion_options():
    """
    Returns available conversion options for specific source and target formats
    """
    source_format = request.args.get('source')
    target_format = request.args.get('target')
    
    if not source_format or not target_format:
        return jsonify({"error": "Missing parameters", "message": "Both source and target formats are required"}), 400
    
    try:
        # Get options based on source and target format
        options = _get_conversion_options(source_format, target_format)
        return jsonify(options), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving conversion options: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve conversion options", "message": str(e)}), 500

def _get_conversion_options(source_format, target_format):
    """
    Get conversion options for specific source and target formats
    """
    # Common options for all conversions
    common_options = {
        "preserve_metadata": {
            "type": "boolean",
            "default": True,
            "label": "Preserve Metadata",
            "description": "Maintain original file metadata in the converted file"
        }
    }
    
    # Specific options based on source and target formats
    specific_options = {}
    
    # PDF-specific options
    if target_format == 'pdf':
        specific_options.update({
            "dpi": {
                "type": "number",
                "default": 300,
                "min": 72,
                "max": 1200,
                "label": "DPI",
                "description": "Resolution in dots per inch"
            },
            "pdf_version": {
                "type": "select",
                "default": "1.7",
                "options": ["1.4", "1.5", "1.6", "1.7", "2.0"],
                "label": "PDF Version",
                "description": "PDF specification version to use"
            }
        })
    
    # Image-specific options
    if target_format in ['jpg', 'jpeg', 'png', 'webp', 'tiff']:
        specific_options.update({
            "quality": {
                "type": "number",
                "default": 90,
                "min": 1,
                "max": 100,
                "label": "Quality",
                "description": "Image quality (higher is better but larger file size)"
            },
            "resize": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "default": False
                    },
                    "width": {
                        "type": "number",
                        "default": 0,
                        "min": 0,
                        "description": "Width in pixels (0 for auto)"
                    },
                    "height": {
                        "type": "number",
                        "default": 0,
                        "min": 0,
                        "description": "Height in pixels (0 for auto)"
                    },
                    "maintain_aspect_ratio": {
                        "type": "boolean",
                        "default": True
                    }
                },
                "label": "Resize",
                "description": "Resize the image during conversion"
            }
        })
    
    # Markdown-specific options
    if source_format == 'md' or target_format == 'md':
        specific_options.update({
            "markdown_flavor": {
                "type": "select",
                "default": "github",
                "options": ["common", "github", "strict"],
                "label": "Markdown Flavor",
                "description": "Markdown dialect to use for parsing/rendering"
            }
        })
    
    # Excel-specific options
    if source_format in ['xlsx', 'xls'] or target_format in ['xlsx', 'xls']:
        specific_options.update({
            "sheet_name": {
                "type": "string",
                "default": "Sheet1",
                "label": "Sheet Name",
                "description": "Name of the sheet to convert (for source) or create (for target)"
            },
            "include_header": {
                "type": "boolean",
                "default": True,
                "label": "Include Header Row",
                "description": "Treat first row as header"
            }
        })
    
    # Audio-specific options
    if target_format in ['mp3', 'wav', 'ogg', 'flac']:
        specific_options.update({
            "audio_bitrate": {
                "type": "select",
                "default": "192k",
                "options": ["64k", "128k", "192k", "256k", "320k"],
                "label": "Bitrate",
                "description": "Audio quality (higher is better but larger file size)"
            },
            "audio_channels": {
                "type": "select",
                "default": "2",
                "options": ["1", "2"],
                "label": "Channels",
                "description": "Mono (1) or Stereo (2)"
            }
        })
    
    # Video-specific options
    if target_format in ['mp4', 'webm', 'avi', 'mov']:
        specific_options.update({
            "video_quality": {
                "type": "select",
                "default": "medium",
                "options": ["low", "medium", "high", "very_high"],
                "label": "Video Quality",
                "description": "Video quality preset"
            },
            "video_framerate": {
                "type": "number",
                "default": 30,
                "min": 10,
                "max": 60,
                "label": "Framerate",
                "description": "Frames per second"
            }
        })
    
    # Merge common and specific options
    return {**common_options, **specific_options} 