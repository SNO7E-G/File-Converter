from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.db import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_hash = db.Column(db.String(256), nullable=False)
    tier = db.Column(db.String(20), default='free')  # 'free', 'premium', or 'enterprise'
    avatar_url = db.Column(db.String(255), nullable=True)
    _settings = db.Column(db.Text, nullable=True)  # JSON string of user settings
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversions = db.relationship('Conversion', backref='user', lazy=True)
    # Templates relationship is defined in Template model
    # Add a relationship for shared conversions where this user is the sharer
    shared_by_me = db.relationship(
        'SharedConversion',
        foreign_keys='SharedConversion.shared_by',
        backref='shared_by_user',
        lazy=True
    )
    # Add a relationship for shared conversions where this user is the recipient
    shared_with_me = db.relationship(
        'SharedConversion',
        foreign_keys='SharedConversion.shared_with',
        backref='shared_with_user',
        lazy=True
    )
    
    @hybrid_property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)
    
    def get_daily_limit(self):
        from app.config import Config
        if self.tier == 'enterprise':
            return float('inf')  # Unlimited conversions
        elif self.tier == 'premium':
            return Config.PREMIUM_TIER_DAILY_LIMIT
        else:
            return Config.FREE_TIER_DAILY_LIMIT
    
    def get_daily_conversions_count(self):
        from app.models.conversion import Conversion
        from datetime import datetime, timedelta
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        return Conversion.query.filter(
            Conversion.user_id == self.id,
            Conversion.created_at >= yesterday
        ).count()
    
    def can_convert(self):
        return self.get_daily_conversions_count() < self.get_daily_limit()
    
    def update_login_timestamp(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def settings(self):
        import json
        if self._settings:
            return json.loads(self._settings)
        return {}
    
    @settings.setter
    def settings(self, value):
        import json
        if value is None:
            self._settings = None
        else:
            self._settings = json.dumps(value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'tier': self.tier,
            'avatar_url': self.avatar_url,
            'settings': self.settings,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<User {self.username}>' 