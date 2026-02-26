from database.db import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'
    
    document_id = db.Column(db.String(36), primary_key=True)
    uploader_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_type = db.Column(db.String(50))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    subject = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship is now centralized in models/user.py
    
    def to_dict(self):
        return {
            'document_id': self.document_id,
            'uploader_id': self.uploader_id,
            'uploader_name': self.uploader.name if self.uploader else 'Unknown',
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'title': self.title,
            'description': self.description,
            'subject': self.subject,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
