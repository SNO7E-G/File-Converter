"""
Configuration settings for the File Converter application.
Supports different environments (development, testing, production) and
configures databases, storage options, and other application settings.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class for the application"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database settings
    DB_TYPE = os.environ.get('DB_TYPE', 'postgresql')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/file_converter')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File storage settings
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 'local')
    UPLOAD_DIR = os.environ.get('UPLOAD_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))
    ALLOWED_EXTENSIONS = {
        # Document formats
        'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls', 'pdf', 'docx', 'txt', 'html',
        # Image formats
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'svg',
        # Audio formats
        'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'opus',
        # Video formats
        'mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', '3gp',
    }
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB limit for uploads
    TEMP_FILE_EXPIRY = 48  # Hours before temporary files are deleted
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # External API connections
    FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')
    
    # User tiers and limits
    USER_TIERS = {
        'free': {
            'daily_conversions': 5,
            'max_file_size': 25 * 1024 * 1024,  # 25 MB
            'batch_processing': False,
            'priority_processing': False,
        },
        'basic': {
            'daily_conversions': 20,
            'max_file_size': 100 * 1024 * 1024,  # 100 MB
            'batch_processing': True,
            'priority_processing': False,
        },
        'premium': {
            'daily_conversions': 100,
            'max_file_size': 500 * 1024 * 1024,  # 500 MB
            'batch_processing': True,
            'priority_processing': True,
        },
        'enterprise': {
            'daily_conversions': -1,  # Unlimited
            'max_file_size': 2 * 1024 * 1024 * 1024,  # 2 GB
            'batch_processing': True,
            'priority_processing': True,
        }
    }
    
    # S3 configuration
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'file-converter')
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
    S3_PREFIX = os.environ.get('S3_PREFIX', '')
    
    # Google Cloud Storage configuration
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'file-converter')
    GCS_PREFIX = os.environ.get('GCS_PREFIX', '')
    
    # Azure Blob Storage configuration
    AZURE_CONTAINER_NAME = os.environ.get('AZURE_CONTAINER_NAME', 'file-converter')
    AZURE_PREFIX = os.environ.get('AZURE_PREFIX', '')
    
    # MongoDB configuration (if needed)
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/file_converter')
    
    # MySQL configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'file_converter')
    
    # PostgreSQL configuration
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'file_converter')
    
    # SQLite configuration
    SQLITE_PATH = os.environ.get('SQLITE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'file_converter.db'))

class DevelopmentConfig(Config):
    """Configuration for development environment"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Use SQLite by default in development
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{Config.SQLITE_PATH}')
    
    # Use local file storage in development
    STORAGE_TYPE = os.environ.get('STORAGE_TYPE', 'local')

class TestingConfig(Config):
    """Configuration for testing environment"""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    DB_TYPE = 'sqlite'
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Use local file storage for testing
    STORAGE_TYPE = 'local'
    UPLOAD_DIR = '/tmp/file_converter_test'
    
    # Shorten JWT expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=10)

class ProductionConfig(Config):
    """Configuration for production environment"""
    
    # Production should use environment variables for all sensitive settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Force SSL in production
    PREFERRED_URL_SCHEME = 'https'
    
    # More restrictive CORS in production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Configuration dictionary for Flask app
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Helper function to get configuration by name
def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name[env] 