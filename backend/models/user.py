"""
User model
"""
from database.db import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # student, staff, admin
    student_id = db.Column(db.String(50), nullable=True)
    staff_id = db.Column(db.String(50), nullable=True)
    face_encoding = db.Column(db.LargeBinary, nullable=True)  # Encrypted face encoding
    fingerprint_id = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # OTP verification fields
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are handled in the other models using backref, except where explicitly defined or circular
    # Note: Flask-SQLAlchemy handles backrefs automatically. 
    # We remove explicit definitions here if they are defined in other files with backref, 
    # OR we keep them but use string references.
    
    # However, to be safe and clean, we often define the 'one' side of relationship here for clarity, 
    # Relationships with cascade delete
    attendance_records = db.relationship('Attendance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('AttendanceSession', backref='staff', lazy='dynamic', foreign_keys='AttendanceSession.staff_id', cascade='all, delete-orphan')
    correction_requests = db.relationship('CorrectionRequest', foreign_keys='CorrectionRequest.user_id', backref='requester', lazy='dynamic', cascade='all, delete-orphan')
    reviewed_corrections = db.relationship('CorrectionRequest', foreign_keys='CorrectionRequest.reviewed_by', backref='reviewer', lazy='dynamic')
    fraud_alerts = db.relationship('FraudAlert', foreign_keys='FraudAlert.user_id', backref='target_user', lazy='dynamic', cascade='all, delete-orphan')
    resolved_alerts = db.relationship('FraudAlert', foreign_keys='FraudAlert.resolved_by', backref='resolver', lazy='dynamic')
    system_logs = db.relationship('SystemLog', backref='log_user', lazy='dynamic', cascade='all, delete-orphan')
    uploaded_documents = db.relationship('Document', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
    
    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'student_id': self.student_id,
            'staff_id': self.staff_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
