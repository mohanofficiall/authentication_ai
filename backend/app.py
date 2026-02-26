"""
Flask Application Entry Point
AI Smart Attendance System
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import config
from database.db import init_db
from utils.logger import setup_logging
import os

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__, 
                static_folder='../frontend',
                static_url_path='')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Setup logging
    setup_logging(app)
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-Mail
    from services.email_service import mail
    mail.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.staff import staff_bp
    from routes.admin import admin_bp
    from routes.chatbot import chatbot_bp
    from routes.public import public_bp
    from routes.documents import documents_bp
    from routes.announcements import announcements_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(announcements_bp)
    
    # Serve frontend files
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    app.logger.info('[OK] AI Smart Attendance System initialized')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
