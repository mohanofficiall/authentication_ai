"""
System logging utilities
"""
import logging
from logging.handlers import RotatingFileHandler
from flask import request
from database.db import db
from models.logs import SystemLog

import uuid

def setup_logging(app):
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    import os
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
    
    # File handler
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    return app.logger

def log_action(user_id, action, status='success', details=None):
    """Log user action to database"""
    try:
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        log = SystemLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {str(e)}")

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def get_device_info():
    """Get device information from request"""
    return {
        'user_agent': request.headers.get('User-Agent'),
        'ip_address': get_client_ip(),
        'platform': request.user_agent.platform if hasattr(request, 'user_agent') else None,
        'browser': request.user_agent.browser if hasattr(request, 'user_agent') else None
    }
