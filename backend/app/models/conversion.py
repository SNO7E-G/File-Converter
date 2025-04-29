from datetime import datetime
import os
from app.models.db import db
from app.config import Config

class Conversion(db.Model):
    __tablename__ = 'conversions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_format = db.Column(db.String(20), nullable=False)
    target_format = db.Column(db.String(20), nullable=False)
    source_filename = db.Column(db.String(255), nullable=False)
    target_filename = db.Column(db.String(255), nullable=False)
    source_file_path = db.Column(db.String(512), nullable=False)
    target_file_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    task_id = db.Column(db.String(36), nullable=True)  # For Celery task tracking
    scheduled_at = db.Column(db.DateTime, nullable=True)  # For scheduled conversions
    expires_at = db.Column(db.DateTime, nullable=True)  # When the file will be deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    webhooks = db.relationship('Webhook', backref='conversion', lazy=True)
    shared_with = db.relationship('SharedConversion', backref='conversion', lazy=True)
    
    def set_expiry(self):
        """Set the expiry time for this conversion's files"""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=Config.TEMP_FILE_EXPIRY)
    
    def cleanup_files(self):
        """Delete the physical files associated with this conversion"""
        if os.path.exists(self.source_file_path):
            os.remove(self.source_file_path)
        if os.path.exists(self.target_file_path):
            os.remove(self.target_file_path)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_format': self.source_format,
            'target_format': self.target_format,
            'source_filename': self.source_filename,
            'target_filename': self.target_filename,
            'status': self.status,
            'error_message': self.error_message,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f'<Conversion {self.id}: {self.source_format} to {self.target_format}>'


class SharedConversion(db.Model):
    """Model to track shared conversions between users"""
    __tablename__ = 'shared_conversions'
    
    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey('conversions.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='view')  # view, download, edit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversion_id': self.conversion_id,
            'shared_by': self.shared_by,
            'shared_with': self.shared_with,
            'permission': self.permission,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Webhook(db.Model):
    """Model to store webhook URLs for conversion notifications"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey('conversions.id'), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    is_triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversion_id': self.conversion_id,
            'url': self.url,
            'is_triggered': self.is_triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        } 