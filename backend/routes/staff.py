"""
Staff Routes
Handles staff-specific operations
"""
from flask import Blueprint, request, jsonify, current_app
from utils.jwt_handler import token_required, role_required
from services.attendance_service import SessionService
from models.user import User
from models.attendance import Attendance, AttendanceSession, CorrectionRequest
from database.db import db
from utils.logger import log_action
from datetime import datetime, date
from sqlalchemy import func

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')

@staff_bp.route('/session/start', methods=['POST'])
@token_required
@role_required(['staff'])
def start_session():
    """Start a new attendance session"""
    try:
        staff_id = request.current_user['user_id']
        data = request.get_json()
        
        class_name = data.get('class_name')
        subject = data.get('subject')
        duration = data.get('duration_minutes', 60)
        late_threshold = data.get('late_threshold_minutes', 15)
        
        if not class_name:
            return jsonify({'error': 'Class name is required'}), 400
        
        success, message, session_data = SessionService.start_session(
            staff_id,
            class_name,
            subject,
            duration,
            late_threshold
        )
        
        if success:
            log_action(staff_id, 'start_session', 'success')
            return jsonify({
                'message': message,
                'session': session_data
            }), 201
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Start session error: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500

@staff_bp.route('/session/stop/<session_id>', methods=['POST'])
@token_required
@role_required(['staff'])
def stop_session(session_id):
    """Stop an active attendance session"""
    try:
        staff_id = request.current_user['user_id']
        
        success, message, summary = SessionService.stop_session(session_id, staff_id)
        
        if success:
            log_action(staff_id, 'stop_session', 'success')
            return jsonify({
                'message': message,
                'summary': summary
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Stop session error: {str(e)}")
        return jsonify({'error': 'Failed to stop session'}), 500

@staff_bp.route('/session/active', methods=['GET'])
@token_required
@role_required(['staff'])
def get_active_session():
    """Get currently active session"""
    try:
        session = SessionService.get_active_session()
        
        if session:
            # Get attendance count for this session
            attendance_count = Attendance.query.filter_by(session_id=session['session_id']).count()
            session['attendance_count'] = attendance_count
            
            return jsonify({'session': session}), 200
        else:
            return jsonify({'session': None}), 200
            
    except Exception as e:
        current_app.logger.error(f"Get active session error: {str(e)}")
        return jsonify({'error': 'Failed to fetch active session'}), 500

@staff_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['staff'])
def get_dashboard():
    """Get staff dashboard data"""
    try:
        staff_id = request.current_user['user_id']
        
        # Get active session
        active_session = SessionService.get_active_session()
        
        # Get today's attendance summary
        today = date.today()
        today_attendance = db.session.query(
            func.count(Attendance.attendance_id).label('total'),
            func.sum(func.case((Attendance.status == 'present', 1), else_=0)).label('present'),
            func.sum(func.case((Attendance.status == 'late', 1), else_=0)).label('late')
        ).filter(Attendance.date == today).first()
        
        # Get pending correction requests
        pending_corrections = CorrectionRequest.query.filter_by(status='pending').count()
        
        # Get staff's recent sessions
        recent_sessions = AttendanceSession.query.filter_by(
            staff_id=staff_id
        ).order_by(AttendanceSession.created_at.desc()).limit(5).all()
        
        return jsonify({
            'active_session': active_session,
            'today_summary': {
                'total': today_attendance.total or 0,
                'present': today_attendance.present or 0,
                'late': today_attendance.late or 0
            },
            'pending_corrections': pending_corrections,
            'recent_sessions': [s.to_dict() for s in recent_sessions]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Staff dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard'}), 500

@staff_bp.route('/attendance/session/<session_id>', methods=['GET'])
@token_required
@role_required(['staff'])
def get_session_attendance(session_id):
    """Get attendance for a specific session"""
    try:
        attendance_records = Attendance.query.filter_by(session_id=session_id).all()
        
        return jsonify({
            'attendance': [record.to_dict() for record in attendance_records]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Session attendance error: {str(e)}")
        return jsonify({'error': 'Failed to fetch session attendance'}), 500

@staff_bp.route('/corrections/pending', methods=['GET'])
@token_required
@role_required(['staff'])
def get_pending_corrections():
    """Get pending correction requests"""
    try:
        corrections = CorrectionRequest.query.filter_by(status='pending').all()
        
        return jsonify({
            'corrections': [c.to_dict() for c in corrections]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Pending corrections error: {str(e)}")
        return jsonify({'error': 'Failed to fetch corrections'}), 500

@staff_bp.route('/corrections/<request_id>/approve', methods=['POST'])
@token_required
@role_required(['staff'])
def approve_correction(request_id):
    """Approve a correction request"""
    try:
        staff_id = request.current_user['user_id']
        data = request.get_json()
        comment = data.get('comment', '')
        
        correction = CorrectionRequest.query.get(request_id)
        
        if not correction:
            return jsonify({'error': 'Correction request not found'}), 404
        
        correction.status = 'approved'
        correction.reviewed_by = staff_id
        correction.review_comment = comment
        correction.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(staff_id, 'approve_correction', 'success')
        
        return jsonify({
            'message': 'Correction request approved',
            'correction': correction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Approve correction error: {str(e)}")
        return jsonify({'error': 'Failed to approve correction'}), 500

@staff_bp.route('/corrections/<request_id>/reject', methods=['POST'])
@token_required
@role_required(['staff'])
def reject_correction(request_id):
    """Reject a correction request"""
    try:
        staff_id = request.current_user['user_id']
        data = request.get_json()
        comment = data.get('comment', '')
        
        correction = CorrectionRequest.query.get(request_id)
        
        if not correction:
            return jsonify({'error': 'Correction request not found'}), 404
        
        correction.status = 'rejected'
        correction.reviewed_by = staff_id
        correction.review_comment = comment
        correction.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(staff_id, 'reject_correction', 'success')
        
        return jsonify({
            'message': 'Correction request rejected',
            'correction': correction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reject correction error: {str(e)}")
        return jsonify({'error': 'Failed to reject correction'}), 500
