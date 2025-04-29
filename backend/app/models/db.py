from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import Config

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Function to create and configure different database engines
def get_db_engine(db_type=None, connection_string=None):
    """
    Create a database engine based on type or connection string
    
    Args:
        db_type: Type of database ('sqlite', 'postgresql', 'mysql', 'mongodb')
        connection_string: Direct connection string (overrides db_type if provided)
        
    Returns:
        SQLAlchemy engine
    """
    if connection_string:
        return create_engine(connection_string)
    
    if not db_type:
        db_type = os.environ.get('DB_TYPE', 'postgresql')
    
    if db_type == 'sqlite':
        db_path = os.environ.get('SQLITE_PATH', '/tmp/file_converter.db')
        return create_engine(f'sqlite:///{db_path}')
    elif db_type == 'postgresql':
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        user = os.environ.get('POSTGRES_USER', 'postgres')
        password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
        database = os.environ.get('POSTGRES_DB', 'file_converter')
        return create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    elif db_type == 'mysql':
        host = os.environ.get('MYSQL_HOST', 'localhost')
        port = os.environ.get('MYSQL_PORT', '3306')
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', 'root')
        database = os.environ.get('MYSQL_DB', 'file_converter')
        return create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
    else:
        # Default to PostgreSQL
        return create_engine(Config.DATABASE_URL)

# Create base class for declarative models
Base = declarative_base()

# Create a session factory for db operations
def setup_db_session(app=None, engine=None):
    """
    Set up the database session
    
    Args:
        app: Flask application instance
        engine: SQLAlchemy engine
        
    Returns:
        SQLAlchemy session
    """
    if app:
        # Configure SQLAlchemy with Flask
        db.init_app(app)
        return db.session
    elif engine:
        # Create standalone session
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        return Session
    else:
        # Use default engine
        default_engine = get_db_engine()
        session_factory = sessionmaker(bind=default_engine)
        Session = scoped_session(session_factory)
        return Session 