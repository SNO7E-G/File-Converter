from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from app.models.db import db
from app.models.template import Template
from app.models.user import User

templates_bp = Blueprint('templates', __name__)

@templates_bp.route('', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all templates for the current user"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    
    try:
        templates_query = Template.query.filter_by(user_id=current_user_id)
        pagination = templates_query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'templates': [template.to_dict() for template in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<int:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a specific template"""
    current_user_id = get_jwt_identity()
    
    template = Template.query.filter_by(id=template_id, user_id=current_user_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify({'template': template.to_dict()}), 200

@templates_bp.route('', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new template"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'source_format', 'target_format']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        template = Template(
            user_id=current_user_id,
            name=data['name'],
            description=data.get('description', ''),
            source_format=data['source_format'],
            target_format=data['target_format'],
            settings=data.get('settings', {})
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'message': 'Template created successfully',
            'template': template.to_dict()
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update an existing template"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    template = Template.query.filter_by(id=template_id, user_id=current_user_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    try:
        # Update fields
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'source_format' in data:
            template.source_format = data['source_format']
        if 'target_format' in data:
            template.target_format = data['target_format']
        if 'settings' in data:
            template.settings = data['settings']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Template updated successfully',
            'template': template.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a template"""
    current_user_id = get_jwt_identity()
    
    template = Template.query.filter_by(id=template_id, user_id=current_user_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    try:
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'message': 'Template deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<int:template_id>/use', methods=['POST'])
@jwt_required()
def use_template(template_id):
    """Increment the usage count for a template and return its settings for use in a conversion"""
    current_user_id = get_jwt_identity()
    
    template = Template.query.filter_by(id=template_id, user_id=current_user_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    try:
        template.increment_usage()
        
        return jsonify({
            'message': 'Template usage recorded',
            'template': template.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 