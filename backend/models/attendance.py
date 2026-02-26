"""
Attendance models
"""
from database.db import db
from datetime import datetime
import uuid

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    attendance_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False)  # present, late, absent
    confidence_score = db.Column(db.Float, nullable=True)
    geo_location = db.Column(db.String(255), nullable=True)
    device_info = db.Column(db.Text, nullable=True)
    marked_by = db.Column(db.String(20), nullable=True)  # face, fingerprint, manual
    session_id = db.Column(db.String(36), db.ForeignKey('attendance_sessions.session_id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.user_id} on {self.date} - {self.status}>'
    
    def to_dict(self):
        return {
            'attendance_id': self.attendance_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'date': self.date.isoformat() if self.date else None,
            'time_in': self.time_in.isoformat() if self.time_in else None,
            'time_out': self.time_out.isoformat() if self.time_out else None,
            'status': self.status,
            'confidence_score': self.confidence_score,
            'marked_by': self.marked_by,
            'session_id': self.session_id
        }

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    
    session_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    staff_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    class_name = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    late_threshold_minutes = db.Column(db.Integer, default=15)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<Session {self.class_name} - {self.subject}>'
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'staff_id': self.staff_id,
            'staff_name': self.staff.name if self.staff else None,
            'class_name': self.class_name,
            'subject': self.subject,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'late_threshold_minutes': self.late_threshold_minutes
        }

class CorrectionRequest(db.Model):
    __tablename__ = 'correction_requests'
    
    request_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    attendance_id = db.Column(db.String(36), db.ForeignKey('attendance.attendance_id', ondelete='SET NULL'), nullable=True)
    request_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    reviewed_by = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    review_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships are now centralized in models/user.py
    
    def __repr__(self):
        return f'<CorrectionRequest {self.request_id} - {self.status}>'
    
    def to_dict(self):
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'user_name': self.requester.name if self.requester else None,
            'attendance_id': self.attendance_id,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'reason': self.reason,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewer_name': self.reviewer.name if self.reviewer else None,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
