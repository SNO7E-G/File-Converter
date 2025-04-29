from datetime import datetime
from app.models.db import db

class TokenBlacklist(db.Model):
    """Model for tracking revoked tokens"""
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    token_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'
    
    @classmethod
    def add_token_to_blacklist(cls, jwt_payload, user_id=None):
        """Add a token to the blacklist"""
        jti = jwt_payload['jti']
        token_type = jwt_payload['type']
        expires_at = datetime.fromtimestamp(jwt_payload['exp'])
        
        token = cls(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        
        db.session.add(token)
        db.session.commit()
        
        return token
    
    @classmethod
    def is_token_revoked(cls, jti):
        """Check if a token is revoked"""
        return cls.query.filter_by(jti=jti).first() is not None
    
    @classmethod
    def prune_database(cls):
        """Delete expired tokens"""
        now = datetime.utcnow()
        expired = cls.query.filter(cls.expires_at < now).delete()
        db.session.commit()
        
        return expired 