"""
Authentication Routes
Handles user registration and login with OTP verification
"""
from flask import Blueprint, request, jsonify, current_app
from database.db import db
from models.user import User
from utils.jwt_handler import generate_token
from utils.validators import validate_email, validate_password, validate_role
from utils.logger import log_action
from services.face_recognition_service import FaceRecognitionService
from services.email_service import EmailService
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user - Step 1: Send OTP"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        role = data['role'].lower()
        student_id = data.get('student_id', '').strip() if role == 'student' else None
        staff_id = data.get('staff_id', '').strip() if role == 'staff' else None
        face_image = data.get('face_image')  # Base64 encoded image
        
        # Validate email
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate role
        if not validate_role(role):
            return jsonify({'error': 'Invalid role. Must be student, staff, or admin'}), 400
        
        # Validate and extract face encoding
        face_encoding_encrypted = None
        if face_image:
            success, encoding_or_error = FaceRecognitionService.extract_face_encoding(face_image)
            if not success:
                return jsonify({'error': f'Face validation failed: {encoding_or_error}'}), 400
            
            # Encrypt face encoding
            face_encoding_encrypted = FaceRecognitionService.encrypt_encoding(encoding_or_error)
        else:
            return jsonify({'error': 'Face image is required for registration'}), 400
        
        # Generate OTP
        otp_code = EmailService.generate_otp()
        otp_expires_at = EmailService.get_otp_expiry()
        
        # Create new user (not verified yet, inactive)
        user = User(
            user_id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            student_id=student_id,
            staff_id=staff_id,
            face_encoding=face_encoding_encrypted,
            is_active=False,  # Not active until OTP verified
            is_verified=False,  # Not verified yet
            otp_code=otp_code,
            otp_expires_at=otp_expires_at
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send OTP email
        email_sent = EmailService.send_otp_email(email, name, otp_code)
        
        if not email_sent:
            # Rollback user creation if email fails
            db.session.delete(user)
            db.session.commit()
            return jsonify({'error': 'Failed to send OTP email. Please try again.'}), 500
        
        # Log action
        log_action(user.user_id, 'otp_sent', 'success')
        
        return jsonify({
            'message': 'OTP sent to your email. Please verify to complete registration.',
            'email': email
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed. Please try again'}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and complete registration - Step 2"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'otp' not in data:
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        email = data['email'].strip().lower()
        otp_code = data['otp'].strip()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already verified
        if user.is_verified:
            return jsonify({'error': 'Email already verified'}), 400
        
        # Check if OTP matches
        if user.otp_code != otp_code:
            log_action(user.user_id, 'otp_verification_failed', 'failed', 'Invalid OTP')
            return jsonify({'error': 'Invalid OTP code'}), 401
        
        # Check if OTP expired
        if datetime.utcnow() > user.otp_expires_at:
            log_action(user.user_id, 'otp_verification_failed', 'failed', 'OTP expired')
            return jsonify({'error': 'OTP has expired. Please request a new one.'}), 401
        
        # Activate user account
        user.is_verified = True
        user.is_active = True
        user.otp_code = None  # Clear OTP
        user.otp_expires_at = None
        
        db.session.commit()
        
        # Log action
        log_action(user.user_id, 'user_registration_completed', 'success')
        
        return jsonify({
            'message': 'Email verified successfully! Registration complete.',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"OTP verification error: {str(e)}")
        return jsonify({'error': 'Verification failed. Please try again'}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user's email"""
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].strip().lower()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already verified
        if user.is_verified:
            return jsonify({'error': 'Email already verified'}), 400
        
        # Generate new OTP
        otp_code = EmailService.generate_otp()
        otp_expires_at = EmailService.get_otp_expiry()
        
        user.otp_code = otp_code
        user.otp_expires_at = otp_expires_at
        
        db.session.commit()
        
        # Send OTP email
        email_sent = EmailService.send_otp_email(email, user.name, otp_code)
        
        if not email_sent:
            return jsonify({'error': 'Failed to send OTP email. Please try again.'}), 500
        
        # Log action
        log_action(user.user_id, 'otp_resent', 'success')
        
        return jsonify({
            'message': 'New OTP sent to your email'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({'error': 'Failed to resend OTP. Please try again'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            log_action(None, 'login_failed', 'failed', f'User not found: {email}')
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active
        if not user.is_active:
            log_action(user.user_id, 'login_failed', 'failed', 'Account inactive')
            return jsonify({'error': 'Account is inactive. Please contact administrator'}), 403
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            log_action(user.user_id, 'login_failed', 'failed', 'Invalid password')
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token = generate_token(user.user_id, user.role, user.email)
        
        if not token:
            return jsonify({'error': 'Failed to generate token'}), 500
        
        # Log successful login
        log_action(user.user_id, 'login_success', 'success')
        
        # Determine redirect URL based on role
        redirect_urls = {
            'student': '/student/dashboard.html',
            'staff': '/staff/dashboard.html',
            'admin': '/admin/dashboard.html'
        }
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict(),
            'redirect_url': redirect_urls.get(user.role, '/index.html')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        from utils.jwt_handler import decode_token
        
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        payload = decode_token(token)
        
        if 'error' in payload:
            return jsonify({'error': payload['error'], 'valid': False}), 401
        
        return jsonify({
            'valid': True,
            'user_id': payload['user_id'],
            'role': payload['role'],
            'email': payload['email']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Token verification failed', 'valid': False}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In JWT, logout is handled client-side by removing the token
        # We just log the action
        
        from utils.jwt_handler import token_required
        
        # Get user from token if available
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                from utils.jwt_handler import decode_token
                payload = decode_token(token)
                if 'user_id' in payload:
                    log_action(payload['user_id'], 'logout', 'success')
            except:
                pass
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500
