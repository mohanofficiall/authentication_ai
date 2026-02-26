"""
Database connection and initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import os

db = SQLAlchemy()
migrate = Migrate()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite"""
    if dbapi_connection.__class__.__module__ == 'sqlite3':
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'logs'), exist_ok=True)
    
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from models import user, attendance, logs, document
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        from models.user import User
        from werkzeug.security import generate_password_hash
        import uuid
        
        admin = User.query.filter_by(email='admin@attendance.com').first()
        if not admin:
            admin = User(
                user_id=str(uuid.uuid4()),
                name='System Administrator',
                email='admin@attendance.com',
                password_hash=generate_password_hash('Admin@123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("[OK] Default admin user created: admin@attendance.com / Admin@123")

def get_db():
    """Get database instance"""
    return db
