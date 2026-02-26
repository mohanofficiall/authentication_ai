"""
System Logs and Alerts models
"""
from database.db import db
from datetime import datetime
import uuid

class FraudAlert(db.Model):
    __tablename__ = 'fraud_alerts'
    
    alert_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # duplicate, mismatch, unusual_pattern, device_change, location_anomaly
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium', index=True)  # low, medium, high, critical
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships are now centralized in models/user.py
    
    def __repr__(self):
        return f'<FraudAlert {self.alert_type} - {self.severity}>'
    
    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'alert_type': self.alert_type,
            'description': self.description,
            'severity': self.severity,
            'is_resolved': self.is_resolved,
            'resolved_by': self.resolved_by,
            'resolver_name': self.resolver.name if self.resolver else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    device_id = db.Column(db.String(255), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships are now centralized in models/user.py

    def __repr__(self):
        return f'<SystemLog {self.action} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'ip_address': self.ip_address,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
