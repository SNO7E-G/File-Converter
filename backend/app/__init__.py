import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_obj=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    if config_obj is None:
        from app.config import get_config
        config_obj = get_config()
    
    app.config.from_object(config_obj)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Setup CORS
    CORS(app, 
         resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}},
         supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', True))
    
    # Register blueprints
    from app.api.routes import api_bp
    from app.auth.routes import auth_bp
    from app.api.formats import formats_bp  # Add import for formats blueprint
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(formats_bp)  # Register formats blueprint
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200
    
    # Ensure upload directory exists
    upload_dir = app.config.get('UPLOAD_DIR')
    if upload_dir and not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    # Initialize converter factory
    from app.converters.converter_factory import converter_factory
    app.logger.info("Initializing converter factory...")
    converter_factory.reinitialize()
    
    # Register error handlers
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        if app.debug:
            # In development, let the default handler show the traceback
            raise e
        
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500
    
    # Register JWT token callbacks
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id if hasattr(user, 'id') else user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.models.user import User
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).one_or_none()
    
    # Register Celery tasks if enabled
    if app.config.get('CELERY_ENABLED', False):
        from app.tasks import init_celery
        init_celery(app)
    
    return app 