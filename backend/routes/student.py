"""
Student Routes
Handles student-specific operations
"""
from flask import Blueprint, request, jsonify, current_app
from utils.jwt_handler import token_required, role_required
from services.attendance_service import AttendanceService
from models.user import User
from models.attendance import Attendance, CorrectionRequest
from database.db import db
from utils.logger import log_action, get_device_info
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
import uuid

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

@student_bp.route('/mark-attendance', methods=['POST'])
@token_required
@role_required(['student'])
def mark_attendance():
    """Mark attendance using face recognition"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        face_image = data.get('face_image')
        geo_location = data.get('geo_location')
        
        if not face_image:
            return jsonify({'error': 'Face image is required'}), 400
        
        # Get device info
        device_info = get_device_info()
        
        # Mark attendance
        success, message, attendance_data = AttendanceService.mark_attendance(
            user_id,
            face_image,
            geo_location,
            device_info
        )
        
        if success:
            log_action(user_id, 'mark_attendance', 'success')
            return jsonify({
                'message': message,
                'attendance': attendance_data
            }), 200
        else:
            log_action(user_id, 'mark_attendance', 'failed', message)
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Mark attendance error: {str(e)}")
        return jsonify({'error': 'Failed to mark attendance'}), 500

@student_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['student'])
def get_dashboard():
    """Get student dashboard data"""
    try:
        user_id = request.current_user['user_id']
        
        # Get today's status
        today_status = AttendanceService.get_today_status(user_id)
        
        # Get attendance percentage (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        percentage = AttendanceService.calculate_attendance_percentage(
            user_id,
            thirty_days_ago,
            date.today()
        )
        
        # Get recent attendance (last 10 records)
        success, records = AttendanceService.get_user_attendance(user_id)
        recent_attendance = records[:10] if success else []
        
        # Get user info
        user = User.query.get(user_id)
        
        return jsonify({
            'user': user.to_dict(),
            'today_status': today_status,
            'attendance_percentage': percentage,
            'recent_attendance': recent_attendance
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard'}), 500

@student_bp.route('/attendance-history', methods=['GET'])
@token_required
@role_required(['student'])
def get_attendance_history():
    """Get attendance history with optional date range"""
    try:
        user_id = request.current_user['user_id']
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        success, records = AttendanceService.get_user_attendance(user_id, start_date, end_date)
        
        if success:
            return jsonify({'attendance': records}), 200
        else:
            return jsonify({'error': records}), 500
            
    except Exception as e:
        current_app.logger.error(f"Attendance history error: {str(e)}")
        return jsonify({'error': 'Failed to fetch attendance history'}), 500

@student_bp.route('/request-correction', methods=['POST'])
@token_required
@role_required(['student'])
def request_correction():
    """Request attendance correction"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        request_date_str = data.get('date')
        reason = data.get('reason')
        
        if not request_date_str or not reason:
            return jsonify({'error': 'Date and reason are required'}), 400
        
        request_date = datetime.strptime(request_date_str, '%Y-%m-%d').date()
        
        # Create correction request
        correction = CorrectionRequest(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            request_date=request_date,
            reason=reason,
            status='pending'
        )
        
        db.session.add(correction)
        db.session.commit()
        
        log_action(user_id, 'request_correction', 'success')
        
        return jsonify({
            'message': 'Correction request submitted successfully',
            'request': correction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Correction request error: {str(e)}")
        return jsonify({'error': 'Failed to submit correction request'}), 500

@student_bp.route('/profile', methods=['GET'])
@token_required
@role_required(['student'])
def get_profile():
    """Get student profile details"""
    try:
        user_id = request.current_user['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@student_bp.route('/profile', methods=['PUT'])
@token_required
@role_required(['student'])
def update_profile():
    """Update student profile details"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if 'name' in data:
            user.name = data['name']
            
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
            
        db.session.commit()
        log_action(user_id, 'update_profile', 'success')
        
        return jsonify({'message': 'Profile updated successfully', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@student_bp.route('/profile/photo', methods=['POST'])
@token_required
@role_required(['student'])
def update_photo():
    """Update student face photo"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        face_image = data.get('face_image')
        
        if not face_image:
            return jsonify({'error': 'Face image is required'}), 400
            
        # Re-encode face
        from services.face_recognition_service import FaceRecognitionService
        success, result = FaceRecognitionService.extract_face_encoding(face_image)
        
        if not success:
            return jsonify({'error': result}), 400
            
        encoding = result
            
        # Encrypt and save
        from services.face_recognition_service import FaceRecognitionService
        encrypted_encoding = FaceRecognitionService.encrypt_encoding(encoding)
        
        user = User.query.get(user_id)
        user.face_encoding = encrypted_encoding
        db.session.commit()
        
        log_action(user_id, 'update_photo', 'success')
        
        return jsonify({'message': 'Photo updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update photo error: {str(e)}")
        return jsonify({'error': 'Failed to update photo'}), 500
