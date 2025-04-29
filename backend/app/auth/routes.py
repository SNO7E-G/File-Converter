from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError
from app.models.db import db
from app.models.user import User
from app.models.blacklist import TokenBlacklist

auth_bp = Blueprint('auth', __name__)

# Schema for request validation
class RegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
    remember_me = fields.Boolean(required=False, default=False)

class ProfileUpdateSchema(Schema):
    username = fields.String(validate=validate.Length(min=3, max=80))
    email = fields.Email()
    avatar_url = fields.String()
    settings = fields.Dict()

@auth_bp.route('/register', methods=['POST'])
def register():
    schema = RegisterSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.password = data['password']
    
    db.session.add(user)
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Update login timestamp
    user.update_login_timestamp()
    
    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
        "token": access_token,
        "refreshToken": refresh_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.verify_password(data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Adjust token expiration based on remember_me flag
    expires_delta = None
    if data.get('remember_me', False):
        expires_delta = timedelta(days=30)
    
    # Create tokens
    access_token = create_access_token(
        identity=user.id,
        expires_delta=expires_delta
    )
    refresh_token = create_refresh_token(identity=user.id)
    
    # Update login timestamp
    user.update_login_timestamp()
    
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "token": access_token,
        "refreshToken": refresh_token
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    
    # Create new token
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "token": access_token,
        "message": "Token refreshed successfully"
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    schema = ProfileUpdateSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.messages}), 400
    
    # Check if username is being changed and if it's already taken
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 400
        user.username = data['username']
    
    # Check if email is being changed and if it's already taken
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already registered"}), 400
        user.email = data['email']
    
    # Update other fields
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    if 'settings' in data:
        user.settings = data['settings']
    
    db.session.commit()
    
    return jsonify({
        "message": "Profile updated successfully",
        "user": user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    if not user.verify_password(data['current_password']):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    if len(data['new_password']) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
    
    user.password = data['new_password']
    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"}), 200

@auth_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_account():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # In a real app, you would handle payment processing here
    # For now, just upgrade the user tier
    data = request.get_json() or {}
    tier = data.get('tier', 'premium')
    
    if tier not in ['premium', 'enterprise']:
        return jsonify({"error": "Invalid tier specified"}), 400
    
    user.tier = tier
    db.session.commit()
    
    return jsonify({
        "message": f"Account upgraded to {tier} successfully",
        "user": user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Get JWT information
    jwt_payload = get_jwt()
    user_id = get_jwt_identity()
    
    try:
        # Add token to blacklist
        TokenBlacklist.add_token_to_blacklist(jwt_payload, user_id)
        
        return jsonify({
            "message": "Successfully logged out",
            "status": "success"
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error during logout: {str(e)}")
        return jsonify({
            "error": "Logout failed", 
            "message": "An error occurred during logout"
        }), 500 