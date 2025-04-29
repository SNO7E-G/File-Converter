from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import uuid

from app.models.db import db
from app.models.user import User
from app.models.conversion import Conversion, SharedConversion, Webhook
from app.converters.converter_factory import ConverterFactory
from app.converters.base_converter import BaseConverter
from app.utils.file_utils import (
    allowed_file, 
    get_file_extension, 
    generate_unique_filename,
    get_upload_path,
    validate_file_size,
    get_mimetype_for_format,
    cleanup_expired_files
)
from app.api.template_routes import templates_bp

api_bp = Blueprint('api', __name__)

# Register sub-blueprints
api_bp.register_blueprint(templates_bp, url_prefix='/templates')

# Schemas for request validation
class ConversionSchema(Schema):
    target_format = fields.String(required=True)
    options = fields.Dict(required=False)
    webhook_url = fields.URL(required=False)
    scheduled_time = fields.DateTime(required=False)

class BatchConversionSchema(Schema):
    target_format = fields.String(required=True)
    options = fields.Dict(required=False)
    webhook_url = fields.URL(required=False)
    scheduled_time = fields.DateTime(required=False)

class WebhookSchema(Schema):
    url = fields.URL(required=True)

class ShareConversionSchema(Schema):
    shared_with_id = fields.Integer(required=True)
    permission = fields.String(
        required=True, 
        validate=validate.OneOf(['view', 'download', 'edit'])
    )

@api_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get all supported conversion formats"""
    return jsonify({
        "supported_formats": ConverterFactory.get_supported_formats()
    }), 200

@api_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file for conversion"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user has reached their daily limit
    if not user.can_convert():
        return jsonify({
            "error": "Daily conversion limit reached",
            "limit": user.get_daily_limit(),
            "upgrade": "Upgrade to premium for higher limits"
        }), 403
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400
    
    # Get the source format
    source_format = get_file_extension(file.filename)
    if not source_format:
        return jsonify({"error": "Could not determine file format"}), 400
    
    # Check if format is allowed
    allowed_extensions = []
    for ext_list in current_app.config['ALLOWED_EXTENSIONS'].values():
        allowed_extensions.extend(ext_list)
    
    if not allowed_file(file.filename, allowed_extensions):
        return jsonify({
            "error": "File format not allowed",
            "allowed_formats": list(current_app.config['ALLOWED_EXTENSIONS'].keys())
        }), 400
    
    # Check file size
    if not validate_file_size(file):
        max_size_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        return jsonify({
            "error": f"File too large. Maximum size is {max_size_mb} MB"
        }), 400
    
    # Save the file
    filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(filename)
    
    upload_path = get_upload_path(unique_filename, subfolder=str(current_user_id))
    file.save(upload_path)
    
    # Get conversion parameters
    schema = ConversionSchema()
    try:
        if 'conversion_data' in request.form:
            data = schema.loads(request.form['conversion_data'])
        else:
            data = schema.load(request.form)
    except ValidationError as err:
        # Delete the uploaded file if validation fails
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    # Validate conversion format
    target_format = data['target_format'].lower()
    if not ConverterFactory.validate_conversion(source_format, target_format):
        # Delete the uploaded file if conversion is not valid
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({
            "error": f"Conversion from {source_format} to {target_format} is not supported",
            "supported_formats": ConverterFactory.get_supported_formats()
        }), 400
    
    # Generate a unique filename for the target file
    target_filename = generate_unique_filename(filename, target_format)
    target_path = get_upload_path(target_filename, subfolder=str(current_user_id))
    
    # Create conversion record
    conversion = Conversion(
        user_id=current_user_id,
        source_format=source_format,
        target_format=target_format,
        source_filename=filename,
        target_filename=target_filename,
        source_file_path=upload_path,
        target_file_path=target_path,
        status='pending'
    )
    
    # Handle scheduled conversion
    if 'scheduled_time' in data and data['scheduled_time']:
        conversion.scheduled_at = data['scheduled_time']
        conversion.status = 'scheduled'
    
    # Set expiry time for the files
    conversion.set_expiry()
    
    db.session.add(conversion)
    db.session.commit()
    
    # Add webhook if provided
    if 'webhook_url' in data and data['webhook_url']:
        webhook = Webhook(
            conversion_id=conversion.id,
            url=data['webhook_url']
        )
        db.session.add(webhook)
        db.session.commit()
    
    # If scheduled, return success response
    if conversion.status == 'scheduled':
        return jsonify({
            "message": "Conversion scheduled successfully",
            "conversion_id": conversion.id,
            "scheduled_at": conversion.scheduled_at.isoformat(),
            "status": conversion.status
        }), 201
    
    # Perform conversion immediately in this simple implementation
    # In a real app, this would be handled by a background task using Celery
    try:
        conversion.status = 'processing'
        db.session.commit()
        
        # Get converter instance
        converter = ConverterFactory.get_converter(source_format, target_format)
        
        # Convert the file
        success, error = converter.safe_convert(upload_path, target_path, data.get('options'))
        
        if success:
            conversion.status = 'completed'
            conversion.completed_at = datetime.utcnow()
        else:
            conversion.status = 'failed'
            conversion.error_message = error
        
        db.session.commit()
        
        # Trigger webhooks if conversion is complete
        if success and conversion.webhooks:
            for webhook in conversion.webhooks:
                webhook.is_triggered = True
                webhook.triggered_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            "message": "Conversion completed successfully" if success else "Conversion failed",
            "conversion_id": conversion.id,
            "status": conversion.status,
            "error": conversion.error_message
        }), 200 if success else 500
    
    except Exception as e:
        conversion.status = 'failed'
        conversion.error_message = str(e)
        db.session.commit()
        
        return jsonify({
            "error": "Conversion failed",
            "details": str(e),
            "conversion_id": conversion.id,
            "status": conversion.status
        }), 500

@api_bp.route('/conversions', methods=['GET'])
@jwt_required()
def get_conversions():
    """Get all conversions for the current user"""
    current_user_id = get_jwt_identity()
    
    # Get query parameters
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Build query
    query = Conversion.query.filter_by(user_id=current_user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Order by creation date, newest first
    query = query.order_by(Conversion.created_at.desc())
    
    # Paginate results
    conversions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Build response
    return jsonify({
        "conversions": [conversion.to_dict() for conversion in conversions.items],
        "total": conversions.total,
        "pages": conversions.pages,
        "current_page": conversions.page
    }), 200

@api_bp.route('/conversions/<int:conversion_id>', methods=['GET'])
@jwt_required()
def get_conversion(conversion_id):
    """Get a specific conversion"""
    current_user_id = get_jwt_identity()
    
    # Check if user owns the conversion or has it shared with them
    conversion = Conversion.query.get(conversion_id)
    
    if not conversion:
        return jsonify({"error": "Conversion not found"}), 404
    
    # Check ownership or sharing
    if conversion.user_id != current_user_id:
        # Check if conversion is shared with user
        shared = SharedConversion.query.filter_by(
            conversion_id=conversion_id,
            shared_with=current_user_id
        ).first()
        
        if not shared:
            return jsonify({"error": "You do not have permission to access this conversion"}), 403
    
    return jsonify({
        "conversion": conversion.to_dict()
    }), 200

@api_bp.route('/conversions/<int:conversion_id>/download', methods=['GET'])
@jwt_required()
def download_converted_file(conversion_id):
    """Download a converted file"""
    current_user_id = get_jwt_identity()
    
    # Check if user owns the conversion or has it shared with download permission
    conversion = Conversion.query.get(conversion_id)
    
    if not conversion:
        return jsonify({"error": "Conversion not found"}), 404
    
    # Check if conversion is completed
    if conversion.status != 'completed':
        return jsonify({
            "error": "Conversion is not completed",
            "status": conversion.status
        }), 400
    
    # Check ownership or sharing with download permission
    if conversion.user_id != current_user_id:
        # Check if conversion is shared with user with download permission
        shared = SharedConversion.query.filter_by(
            conversion_id=conversion_id,
            shared_with=current_user_id
        ).first()
        
        if not shared or shared.permission not in ['download', 'edit']:
            return jsonify({"error": "You do not have permission to download this file"}), 403
    
    # Check if file exists
    if not os.path.exists(conversion.target_file_path):
        return jsonify({"error": "Converted file not found"}), 404
    
    # Get mime type
    mimetype = get_mimetype_for_format(conversion.target_format)
    
    # Return the file
    return send_file(
        conversion.target_file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=conversion.target_filename
    )

@api_bp.route('/conversions/<int:conversion_id>/share', methods=['POST'])
@jwt_required()
def share_conversion(conversion_id):
    """Share a conversion with another user"""
    current_user_id = get_jwt_identity()
    
    # Check if user owns the conversion
    conversion = Conversion.query.get(conversion_id)
    
    if not conversion:
        return jsonify({"error": "Conversion not found"}), 404
    
    if conversion.user_id != current_user_id:
        return jsonify({"error": "You do not own this conversion"}), 403
    
    # Validate request data
    schema = ShareConversionSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    # Check if the user to share with exists
    shared_with_user = User.query.get(data['shared_with_id'])
    
    if not shared_with_user:
        return jsonify({"error": "User to share with not found"}), 404
    
    # Check if already shared
    existing_share = SharedConversion.query.filter_by(
        conversion_id=conversion_id,
        shared_with=data['shared_with_id']
    ).first()
    
    if existing_share:
        # Update permission if already shared
        existing_share.permission = data['permission']
        db.session.commit()
        
        return jsonify({
            "message": "Sharing permission updated successfully",
            "share": existing_share.to_dict()
        }), 200
    
    # Create new share
    share = SharedConversion(
        conversion_id=conversion_id,
        shared_by=current_user_id,
        shared_with=data['shared_with_id'],
        permission=data['permission']
    )
    
    db.session.add(share)
    db.session.commit()
    
    return jsonify({
        "message": "Conversion shared successfully",
        "share": share.to_dict()
    }), 201

@api_bp.route('/conversions/<int:conversion_id>/preview', methods=['GET'])
@jwt_required()
def preview_conversion(conversion_id):
    """Get a preview of a converted file"""
    current_user_id = get_jwt_identity()
    
    # Check if user has access to the conversion
    conversion = Conversion.query.get(conversion_id)
    
    if not conversion:
        return jsonify({"error": "Conversion not found"}), 404
    
    # Check ownership or sharing
    has_access = False
    if conversion.user_id == current_user_id:
        has_access = True
    else:
        # Check if conversion is shared with user
        shared = SharedConversion.query.filter_by(
            conversion_id=conversion_id,
            shared_with=current_user_id
        ).first()
        
        if shared:
            has_access = True
    
    if not has_access:
        return jsonify({"error": "You do not have permission to access this conversion"}), 403
    
    # Check if conversion is completed
    if conversion.status != 'completed':
        return jsonify({
            "error": "Conversion is not completed",
            "status": conversion.status
        }), 400
    
    # Check if file exists
    if not os.path.exists(conversion.target_file_path):
        return jsonify({"error": "Converted file not found"}), 404
    
    # For simplicity, we'll just return the first few lines/entries of the file
    # In a real app, you would implement proper preview generation for each format
    preview_data = None
    
    try:
        if conversion.target_format in ['csv', 'json', 'xml', 'yaml', 'yml']:
            with open(conversion.target_file_path, 'r', encoding='utf-8') as f:
                preview_data = f.read(1024)  # First 1KB
        elif conversion.target_format in ['xlsx', 'xls']:
            df = pd.read_excel(conversion.target_file_path, nrows=10)
            preview_data = df.to_dict(orient='records')
        elif conversion.target_format in ['pdf']:
            preview_data = "PDF preview not available in this simple implementation"
        else:
            preview_data = "Preview not available for this format"
    except Exception as e:
        return jsonify({
            "error": "Error generating preview",
            "details": str(e)
        }), 500
    
    return jsonify({
        "conversion_id": conversion.id,
        "source_format": conversion.source_format,
        "target_format": conversion.target_format,
        "preview": preview_data
    }), 200

@api_bp.route('/batch-upload', methods=['POST'])
@jwt_required()
def batch_upload():
    """Upload multiple files for batch conversion"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if files are in request
    if 'files[]' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400
    
    files = request.files.getlist('files[]')
    
    # Check if there are files
    if len(files) == 0:
        return jsonify({"error": "No files selected for uploading"}), 400
    
    # Get conversion parameters
    schema = BatchConversionSchema()
    try:
        if 'conversion_data' in request.form:
            data = schema.loads(request.form['conversion_data'])
        else:
            data = schema.load(request.form)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    target_format = data['target_format'].lower()
    
    # Process each file
    conversions = []
    for file in files:
        # Check if filename is empty
        if file.filename == '':
            continue
        
        # Get the source format
        source_format = get_file_extension(file.filename)
        if not source_format:
            continue
        
        # Check if format is allowed
        allowed_extensions = []
        for ext_list in current_app.config['ALLOWED_EXTENSIONS'].values():
            allowed_extensions.extend(ext_list)
        
        if not allowed_file(file.filename, allowed_extensions):
            continue
        
        # Check file size
        if not validate_file_size(file):
            continue
        
        # Validate conversion format
        if not ConverterFactory.validate_conversion(source_format, target_format):
            continue
        
        # Check daily limit
        if not user.can_convert():
            return jsonify({
                "error": "Daily conversion limit reached",
                "limit": user.get_daily_limit(),
                "upgrade": "Upgrade to premium for higher limits",
                "conversions_created": len(conversions)
            }), 403
        
        # Save the file
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        
        upload_path = get_upload_path(unique_filename, subfolder=str(current_user_id))
        file.save(upload_path)
        
        # Generate a unique filename for the target file
        target_filename = generate_unique_filename(filename, target_format)
        target_path = get_upload_path(target_filename, subfolder=str(current_user_id))
        
        # Create conversion record
        conversion = Conversion(
            user_id=current_user_id,
            source_format=source_format,
            target_format=target_format,
            source_filename=filename,
            target_filename=target_filename,
            source_file_path=upload_path,
            target_file_path=target_path,
            status='pending'
        )
        
        # Handle scheduled conversion
        if 'scheduled_time' in data and data['scheduled_time']:
            conversion.scheduled_at = data['scheduled_time']
            conversion.status = 'scheduled'
        
        # Set expiry time for the files
        conversion.set_expiry()
        
        db.session.add(conversion)
        db.session.commit()
        
        # Add webhook if provided
        if 'webhook_url' in data and data['webhook_url']:
            webhook = Webhook(
                conversion_id=conversion.id,
                url=data['webhook_url']
            )
            db.session.add(webhook)
            db.session.commit()
        
        conversions.append(conversion.to_dict())
    
    # Return response
    if len(conversions) == 0:
        return jsonify({
            "error": "No valid files provided for batch conversion"
        }), 400
    
    return jsonify({
        "message": f"Batch conversion created with {len(conversions)} files",
        "conversions": conversions
    }), 201

@api_bp.route('/templates/<format_name>', methods=['GET'])
def get_template(format_name):
    """Get a template file for a specific format"""
    format_name = format_name.lower()
    
    # Check if format is supported
    allowed_formats = [
        'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls'
    ]
    
    if format_name not in allowed_formats:
        return jsonify({
            "error": "Template not available for this format",
            "supported_formats": allowed_formats
        }), 400
    
    # Templates path
    templates_path = os.path.join(current_app.root_path, 'templates')
    
    # Get template file path
    template_filename = f"template.{format_name}"
    template_path = os.path.join(templates_path, template_filename)
    
    # Check if template exists
    if not os.path.exists(template_path):
        return jsonify({
            "error": f"Template for {format_name} not found"
        }), 404
    
    # Get mime type
    mimetype = get_mimetype_for_format(format_name)
    
    # Return the template file
    return send_file(
        template_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=template_filename
    )

@api_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get statistics for the current user"""
    current_user_id = get_jwt_identity()
    
    # Total conversions
    total_conversions = Conversion.query.filter_by(user_id=current_user_id).count()
    
    # Conversions by status
    status_counts = {}
    for status in ['pending', 'processing', 'completed', 'failed', 'scheduled']:
        count = Conversion.query.filter_by(
            user_id=current_user_id, status=status
        ).count()
        status_counts[status] = count
    
    # Conversions by format
    source_format_counts = {}
    target_format_counts = {}
    
    formats = [
        'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls', 'pdf', 'docx'
    ]
    
    for format_name in formats:
        source_count = Conversion.query.filter_by(
            user_id=current_user_id, source_format=format_name
        ).count()
        source_format_counts[format_name] = source_count
        
        target_count = Conversion.query.filter_by(
            user_id=current_user_id, target_format=format_name
        ).count()
        target_format_counts[format_name] = target_count
    
    # Recent conversions
    recent_conversions = Conversion.query.filter_by(
        user_id=current_user_id
    ).order_by(Conversion.created_at.desc()).limit(5).all()
    
    # Conversions by day (last 7 days)
    today = datetime.utcnow().date()
    daily_counts = []
    
    for i in range(7):
        day = today - timedelta(days=i)
        start_of_day = datetime.combine(day, datetime.min.time())
        end_of_day = datetime.combine(day, datetime.max.time())
        
        count = Conversion.query.filter(
            Conversion.user_id == current_user_id,
            Conversion.created_at >= start_of_day,
            Conversion.created_at <= end_of_day
        ).count()
        
        daily_counts.append({
            "date": day.isoformat(),
            "count": count
        })
    
    # Build response
    return jsonify({
        "total_conversions": total_conversions,
        "status_counts": status_counts,
        "source_format_counts": source_format_counts,
        "target_format_counts": target_format_counts,
        "recent_conversions": [conv.to_dict() for conv in recent_conversions],
        "daily_counts": daily_counts,
        "daily_limit": User.query.get(current_user_id).get_daily_limit(),
        "daily_used": User.query.get(current_user_id).get_daily_conversions_count()
    }), 200

@api_bp.route('/webhooks/<int:conversion_id>', methods=['POST'])
@jwt_required()
def create_webhook(conversion_id):
    """Create a webhook for a conversion"""
    current_user_id = get_jwt_identity()
    
    # Check if user owns the conversion
    conversion = Conversion.query.get(conversion_id)
    
    if not conversion:
        return jsonify({"error": "Conversion not found"}), 404
    
    if conversion.user_id != current_user_id:
        return jsonify({"error": "You do not own this conversion"}), 403
    
    # Validate request data
    schema = WebhookSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    # Create webhook
    webhook = Webhook(
        conversion_id=conversion_id,
        url=data['url']
    )
    
    db.session.add(webhook)
    db.session.commit()
    
    return jsonify({
        "message": "Webhook created successfully",
        "webhook": webhook.to_dict()
    }), 201

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring systems
    
    Returns:
        JSON response with status and version information
    """
    status = {
        'status': 'healthy',
        'version': current_app.config.get('VERSION', '1.0.0'),
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.engine.pool.checkedout() >= 0 else 'error'
    }
    
    # Check if storage is accessible
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        status['storage'] = 'accessible'
    except Exception as e:
        status['storage'] = 'error'
        status['storage_error'] = str(e)
    
    return jsonify(status), 200

@api_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    """
    Get system metrics (restricted to admin users)
    
    Returns:
        JSON response with system metrics
    """
    # Only allow admins to access metrics
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != 'admin':
        return jsonify({"error": "Unauthorized. Admin access required."}), 403
    
    # Get system metrics
    metrics = {
        'conversion_stats': {
            'total_conversions': Conversion.query.count(),
            'pending_conversions': Conversion.query.filter_by(status='pending').count(),
            'completed_conversions': Conversion.query.filter_by(status='completed').count(),
            'failed_conversions': Conversion.query.filter_by(status='failed').count(),
            'scheduled_conversions': Conversion.query.filter_by(status='scheduled').count(),
        },
        'user_stats': {
            'total_users': User.query.count(),
            'premium_users': User.query.filter_by(plan='premium').count(),
            'basic_users': User.query.filter_by(plan='basic').count(),
        },
        'converter_metrics': BaseConverter.get_conversion_metrics(),
        'storage': {
            'upload_dir_size': get_directory_size(current_app.config['UPLOAD_FOLDER']),
        }
    }
    
    # Add format-specific metrics
    format_metrics = {}
    for conversion in Conversion.query.all():
        source_format = conversion.source_format
        target_format = conversion.target_format
        key = f"{source_format}_to_{target_format}"
        
        if key not in format_metrics:
            format_metrics[key] = {
                'count': 0,
                'completed': 0,
                'failed': 0
            }
        
        format_metrics[key]['count'] += 1
        if conversion.status == 'completed':
            format_metrics[key]['completed'] += 1
        elif conversion.status == 'failed':
            format_metrics[key]['failed'] += 1
    
    metrics['format_metrics'] = format_metrics
    
    return jsonify(metrics), 200

def get_directory_size(path):
    """Calculate the size of a directory in MB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0 