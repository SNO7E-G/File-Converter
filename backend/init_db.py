import os
import sys
from app import create_app
from app.models.db import db
from app.models.user import User
from app.models.conversion import Conversion, SharedConversion, Webhook

def init_db():
    """Initialize the database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("Database tables created.")
        
        # Check if we need to create sample data
        if '--with-sample-data' in sys.argv:
            create_sample_data()
            print("Sample data created.")

def create_sample_data():
    """Create sample data for development purposes"""
    # Create test users
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            tier='premium'
        )
        admin_user.password = 'Password123!'
        db.session.add(admin_user)
    
    regular_user = User.query.filter_by(email='user@example.com').first()
    if not regular_user:
        regular_user = User(
            username='user',
            email='user@example.com',
            tier='free'
        )
        regular_user.password = 'Password123!'
        db.session.add(regular_user)
    
    db.session.commit()
    print("Sample users created.")

if __name__ == '__main__':
    init_db() 