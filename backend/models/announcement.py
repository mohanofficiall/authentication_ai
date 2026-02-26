from database.db import db
from datetime import datetime
import uuid

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    announcement_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    author = db.relationship('User', backref=db.backref('announcements', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'announcement_id': self.announcement_id,
            'author_id': self.author_id,
            'author_name': self.author.name if self.author else 'Unknown',
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
