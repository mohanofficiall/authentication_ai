"""
Admin Routes
Handles admin-specific operations
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from utils.jwt_handler import token_required, role_required
from models.user import User
from models.attendance import Attendance, AttendanceSession, CorrectionRequest
from models.logs import FraudAlert, SystemLog
from database.db import db
from utils.logger import log_action
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func
import uuid
from services.attendance_service import AttendanceService
from services.export_service import ExportService
from utils.validators import validate_email

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/analytics', methods=['GET'])
@token_required
@role_required(['admin'])
def get_analytics():
    """Get system-wide analytics"""
    try:
        # Total users by role
        total_students = User.query.filter_by(role='student').count()
        total_staff = User.query.filter_by(role='staff').count()
        total_admins = User.query.filter_by(role='admin').count()
        
        # Today's attendance
        today = date.today()
        today_attendance = Attendance.query.filter_by(date=today).count()
        today_present = Attendance.query.filter_by(date=today, status='present').count()
        today_late = Attendance.query.filter_by(date=today, status='late').count()
        
        # Active sessions
        active_sessions = AttendanceSession.query.filter_by(is_active=True).count()
        
        # Unresolved fraud alerts
        unresolved_alerts = FraudAlert.query.filter_by(is_resolved=False).count()
        high_severity_alerts = FraudAlert.query.filter_by(
            is_resolved=False,
            severity='high'
        ).count()
        
        # Last 30 days attendance trend
        thirty_days_ago = date.today() - timedelta(days=30)
        attendance_trend = db.session.query(
            Attendance.date,
            func.count(Attendance.attendance_id).label('count')
        ).filter(
            Attendance.date >= thirty_days_ago
        ).group_by(Attendance.date).order_by(Attendance.date).all()
        
        return jsonify({
            'users': {
                'students': total_students,
                'staff': total_staff,
                'admins': total_admins,
                'total': total_students + total_staff + total_admins
            },
            'today': {
                'total_attendance': today_attendance,
                'present': today_present,
                'late': today_late,
                'percentage': round((today_present / total_students * 100), 2) if total_students > 0 else 0
            },
            'active_sessions': active_sessions,
            'fraud_alerts': {
                'unresolved': unresolved_alerts,
                'high_severity': high_severity_alerts
            },
            'attendance_trend': [
                {'date': str(record.date), 'count': record.count}
                for record in attendance_trend
            ]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required(['admin'])
def get_users():
    """Get all users with pagination and filters"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        search = request.args.get('search')
        
        query = User.query
        
        # Apply filters
        if role_filter:
            query = query.filter_by(role=role_filter)
        
        if search:
            query = query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%'))
            )
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@admin_bp.route('/users', methods=['POST'])
@token_required
@role_required(['admin'])
def create_user():
    """Create a new user (admin only)"""
    try:
        admin_id = request.current_user['user_id']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if email exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user
        user = User(
            user_id=str(uuid.uuid4()),
            name=data['name'],
            email=data['email'].lower(),
            password_hash=generate_password_hash(data['password']),
            role=data['role'],
            student_id=data.get('student_id'),
            staff_id=data.get('staff_id'),
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        log_action(admin_id, 'create_user', 'success', f'Created user: {user.email}')
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create user error: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_user(user_id):
    """Update user details"""
    try:
        admin_id = request.current_user['user_id']
        data = request.get_json()
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update fields
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email'].lower()
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'password' in data:
            user.password_hash = generate_password_hash(data['password'])
        
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(admin_id, 'update_user', 'success', f'Updated user: {user.email}')
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/attendance/manual-override', methods=['POST'])
@token_required
@role_required(['admin'])
def manual_attendance_override():
    """Manually mark/update attendance"""
    try:
        admin_id = request.current_user['user_id']
        data = request.get_json()
        
        required = ['user_id', 'status']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        date_obj = None
        if 'date' in data:
            try:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        success, message, result = AttendanceService.manual_attendance_override(
            admin_id=admin_id,
            user_id=data['user_id'],
            status=data['status'],
            date_obj=date_obj,
            session_id=data.get('session_id')
        )
        
        if success:
            return jsonify({'message': message, 'attendance': result}), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Manual override error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_user(user_id):
    """Delete a user"""
    try:
        admin_id = request.current_user['user_id']
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Prevent deleting yourself
        if user_id == admin_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        email = user.email
        db.session.delete(user)
        db.session.commit()
        
        log_action(admin_id, 'delete_user', 'success', f'Deleted user: {email}')
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete user error: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/fraud-alerts', methods=['GET'])
@token_required
@role_required(['admin'])
def get_fraud_alerts():
    """Get fraud alerts"""
    try:
        # Query parameters
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        severity = request.args.get('severity')
        
        query = FraudAlert.query
        
        if not resolved:
            query = query.filter_by(is_resolved=False)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        alerts = query.order_by(FraudAlert.created_at.desc()).limit(100).all()
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Fraud alerts error: {str(e)}")
        return jsonify({'error': 'Failed to fetch fraud alerts'}), 500

@admin_bp.route('/fraud-alerts/<alert_id>/resolve', methods=['POST'])
@token_required
@role_required(['admin'])
def resolve_fraud_alert(alert_id):
    """Resolve a fraud alert"""
    try:
        admin_id = request.current_user['user_id']
        
        alert = FraudAlert.query.get(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.is_resolved = True
        alert.resolved_by = admin_id
        alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(admin_id, 'resolve_fraud_alert', 'success')
        
        return jsonify({
            'message': 'Alert resolved successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resolve alert error: {str(e)}")
        return jsonify({'error': 'Failed to resolve alert'}), 500

@admin_bp.route('/logs', methods=['GET'])
@token_required
@role_required(['admin'])
def get_system_logs():
    """Get system logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        pagination = SystemLog.query.order_by(
            SystemLog.timestamp.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"System logs error: {str(e)}")
        return jsonify({'error': 'Failed to fetch logs'}), 500

@admin_bp.route('/attendance/export', methods=['GET'])
@token_required
def export_attendance():
    """Export attendance data"""
    try:
        if request.current_user['role'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        format_type = request.args.get('format', 'csv')
        start_date_str = request.args.get('from')
        end_date_str = request.args.get('to')
        
        query = Attendance.query
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date >= start_date)
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date <= end_date)
            except ValueError:
                pass
        
        records = query.all()
        
        # Convert to dict list for export
        data = []
        for r in records:
            data.append({
                'Name': r.user.name if r.user else 'Unknown',
                'Role': r.user.role if r.user else 'N/A',
                'Date': r.date.strftime('%Y-%m-%d'),
                'Status': r.status,
                'Time In': r.time_in.strftime('%H:%M:%S') if r.time_in else 'N/A',
                'Confidence': f"{r.confidence_score}%" if r.confidence_score else 'N/A'
            })
            
        if not data:
             return jsonify({'error': 'No attendance records found for the selected period.'}), 400

        if format_type == 'csv':
            output, filename, mimetype = ExportService.to_csv(data)
        elif format_type == 'excel':
            output, filename, mimetype = ExportService.to_excel(data)
        elif format_type == 'pdf':
            output, filename, mimetype = ExportService.to_pdf(data, title="Attendance Report")
        else:
            return jsonify({'error': 'Invalid format. Use csv, excel, or pdf'}), 400
            
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Export error: {str(e)}")
        return jsonify({'error': 'Failed to export attendance'}), 500
