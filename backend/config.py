"""
Configuration settings for the AI Smart Attendance System
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "attendance.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'faces')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Face recognition settings - STRICT for security
    FACE_RECOGNITION_TOLERANCE = 0.4  # Lower is more strict (0.4 = very strict)
    FACE_MIN_CONFIDENCE = 0.7  # High confidence required (70%)
    FACE_MIN_RESOLUTION = (640, 480)
    
    # Attendance settings
    ATTENDANCE_COOLDOWN_MINUTES = 60  # Prevent duplicate marking within 1 hour
    LATE_THRESHOLD_MINUTES = 15  # Mark as late if > 15 min after session start
    
    # Security settings
    BCRYPT_LOG_ROUNDS = 12
    RATE_LIMIT_ATTENDANCE = "5 per minute"
    RATE_LIMIT_LOGIN = "10 per minute"
    
    # Rasa chatbot settings
    RASA_API_URL = os.environ.get('RASA_API_URL') or 'http://localhost:5005'
    
    # Email settings for OTP verification
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'garampallitharun@gmail.com'
    MAIL_PASSWORD = 'jethlpukxobliqgv'
    MAIL_DEFAULT_SENDER = ('Attendo.AI', 'garampalli@gmail.com')
    
    # Logging settings
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # OpenRouter AI Chatbot settings
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or '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'
    OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL') or 'meta-llama/llama-3.2-3b-instruct:free'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
