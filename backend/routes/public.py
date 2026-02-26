"""
Public Routes
Handles operations accessible without login (like Kiosk attendance)
"""
from flask import Blueprint, request, jsonify, current_app
from services.face_recognition_service import FaceRecognitionService
from services.attendance_service import AttendanceService
from models.user import User
from utils.logger import log_action, get_device_info

public_bp = Blueprint('public', __name__, url_prefix='/api/public')

@public_bp.route('/user/<student_id>', methods=['GET'])
def get_user_by_id(student_id):
    """Get user profile by student ID for kiosk verification"""
    try:
        # Find user by student_id, staff_id, email or user_id
        user = User.query.filter(
            (User.student_id == student_id) | 
            (User.staff_id == student_id) |
            (User.email.like(f'{student_id}%')) | 
            (User.user_id == student_id)
        ).first()
        
        if not user:
            return jsonify({'error': 'Student ID not found'}), 404
            
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
            
        if not user.face_encoding:
            return jsonify({'error': 'No face registered for this ID. Please contact admin.'}), 400
            
        return jsonify({
            'user_id': user.user_id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'display_id': user.student_id if user.role == 'student' else user.staff_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user by ID error: {str(e)}")
        return jsonify({'error': 'System error'}), 500


@public_bp.route('/identify', methods=['POST'])
def identify_for_attendance():
    """Identify user by face and mark attendance without login"""
    try:
        data = request.get_json()
        face_image = data.get('face_image')
        geo_location = data.get('geo_location')
        
        if not face_image:
            return jsonify({'error': 'Face image is required'}), 400
            
        # 1. Identify User
        success, result, confidence = FaceRecognitionService.identify_user(face_image)
        
        if not success:
            # result contains the specific error message (e.g., "Face not recognized...")
            return jsonify({'error': result}), 401
            
        user_id = result
        user = User.query.get(user_id)
        
        # 2. Mark Attendance
        device_info = get_device_info()
        att_success, message, att_data = AttendanceService.mark_attendance(
            user_id,
            face_image,
            geo_location,
            device_info
        )
        
        if att_success:
            log_action(user_id, 'kiosk_attendance', 'success')
            display_id = user.student_id if user.role == 'student' else user.staff_id
            return jsonify({
                'message': f"Attendance marked for {display_id}",
                'user': display_id,
                'status': att_data['status']
            }), 200
        else:
            log_action(user_id, 'kiosk_attendance', 'failed', message)
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Kiosk identification error: {str(e)}")
        return jsonify({'error': 'System error during identification'}), 500

@public_bp.route('/verify', methods=['POST'])
def verify_and_mark_attendance():
    """Verify user face against their stored photo and mark attendance"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        face_image = data.get('face_image')
        geo_location = data.get('geo_location')
        
        if not user_id or not face_image:
            return jsonify({'error': 'User ID and face image are required'}), 400
            
        # 1. Get user
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid user'}), 404
            
        if not user.face_encoding:
            return jsonify({'error': 'No face registered for this user'}), 400
        
        # 2. Mark Attendance (this already does face verification internally)
        device_info = get_device_info()
        att_success, message, att_data = AttendanceService.mark_attendance(
            user_id,
            face_image,
            geo_location,
            device_info
        )
        
        if att_success:
            log_action(user_id, 'kiosk_attendance', 'success')
            display_id = user.student_id if user.role == 'student' else user.staff_id
            return jsonify({
                'message': f"✓ Attendance marked for {display_id}",
                'user': display_id,
                'status': att_data['status'],
                'confidence': att_data.get('confidence_score', 0)
            }), 200
        else:
            log_action(user_id, 'kiosk_attendance', 'failed', message)
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Kiosk verification error: {str(e)}")
        return jsonify({'error': 'System error during verification'}), 500
