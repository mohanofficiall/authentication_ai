"""
Attendance Service
Handles attendance marking, validation, and fraud detection
"""
from datetime import datetime, timedelta, date
from database.db import db
from models.user import User
from models.attendance import Attendance, AttendanceSession, CorrectionRequest
from models.logs import FraudAlert, SystemLog
from services.face_recognition_service import FaceRecognitionService
import uuid
import json

class AttendanceService:
    
    @staticmethod
    def mark_attendance(user_id, image_data, geo_location=None, device_info=None):
        """
        Mark attendance for a user using face recognition
        Returns: (success, message, attendance_data)
        """
        try:
            # Get user
            user = User.query.get(user_id)
            if not user:
                return False, "User not found", None
            
            if not user.face_encoding:
                return False, "No face encoding found. Please register your face first", None
            
            # Check if there's an active session
            active_session = AttendanceSession.query.filter_by(is_active=True).first()
            if not active_session:
                return False, "No active attendance session. Please contact staff", None
            
            # Check attendance cooldown
            today = date.today()
            recent_attendance = Attendance.query.filter(
                Attendance.user_id == user_id,
                Attendance.date == today,
                Attendance.time_in >= datetime.utcnow() - timedelta(hours=1)
            ).first()
            
            if recent_attendance:
                # Create fraud alert for duplicate attempt
                AttendanceService._create_fraud_alert(
                    user_id,
                    'duplicate',
                    f"Duplicate attendance attempt within cooldown period",
                    'medium'
                )
                return False, "Attendance already marked within the last hour", None
            
            # Extract face encoding from live image
            success, encoding_or_error = FaceRecognitionService.extract_face_encoding(image_data)
            if not success:
                return False, encoding_or_error, None
            
            live_encoding = encoding_or_error
            
            # Decrypt stored encoding
            stored_encoding = FaceRecognitionService.decrypt_encoding(user.face_encoding)
            
            # Match faces
            is_match, confidence_score = FaceRecognitionService.match_face(live_encoding, stored_encoding)
            
            if not is_match:
                # Create fraud alert for face mismatch
                AttendanceService._create_fraud_alert(
                    user_id,
                    'mismatch',
                    f"Face mismatch detected. Confidence: {confidence_score}",
                    'high'
                )
                return False, f"Face verification failed. Confidence: {confidence_score:.2%}", None
            
            # Determine status (present or late)
            time_diff = (datetime.utcnow() - active_session.start_time).total_seconds() / 60
            status = 'late' if time_diff > active_session.late_threshold_minutes else 'present'
            
            # Create attendance record
            attendance = Attendance(
                attendance_id=str(uuid.uuid4()),
                user_id=user_id,
                date=today,
                time_in=datetime.utcnow(),
                status=status,
                confidence_score=confidence_score,
                geo_location=geo_location,
                device_info=json.dumps(device_info) if device_info else None,
                marked_by='face',
                session_id=active_session.session_id
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            message = f"Attendance marked successfully as {status.upper()}. Confidence: {confidence_score:.2%}"
            
            return True, message, attendance.to_dict()
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error marking attendance: {str(e)}", None
    
    @staticmethod
    def manual_attendance_override(admin_id, user_id, status, date_obj=None, session_id=None):
        """
        Manually mark attendance for a user (Admin only)
        Returns: (success, message, attendance_data)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found", None
            
            target_date = date_obj or date.today()
            
            # Check if attendance already exists for this date/session
            existing = None
            if session_id:
                existing = Attendance.query.filter_by(user_id=user_id, session_id=session_id).first()
            else:
                existing = Attendance.query.filter_by(user_id=user_id, date=target_date).first()
            
            if existing:
                existing.status = status
                existing.marked_by = 'manual'
                # Log action via helper
                from utils.logger import log_action
                log_action(admin_id, 'manual_attendance_update', 'success', f'Updated attendance for {user.email} to {status}')
                db.session.commit()
                return True, f"Attendance updated to {status}", existing.to_dict()
            
            # Create new manual record
            attendance = Attendance(
                attendance_id=str(uuid.uuid4()),
                user_id=user_id,
                date=target_date,
                time_in=datetime.combine(target_date, datetime.now().time()),
                status=status,
                marked_by='manual',
                session_id=session_id
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            from utils.logger import log_action
            log_action(admin_id, 'manual_attendance_mark', 'success', f'Manually marked {user.email} as {status}')
            
            return True, f"Attendance marked as {status}", attendance.to_dict()
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error in manual override: {str(e)}", None
    
    @staticmethod
    def get_user_attendance(user_id, start_date=None, end_date=None):
        """Get attendance records for a user"""
        try:
            query = Attendance.query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(Attendance.date >= start_date)
            if end_date:
                query = query.filter(Attendance.date <= end_date)
            
            records = query.order_by(Attendance.date.desc()).all()
            
            return True, [record.to_dict() for record in records]
            
        except Exception as e:
            return False, f"Error fetching attendance: {str(e)}"
    
    @staticmethod
    def calculate_attendance_percentage(user_id, start_date=None, end_date=None):
        """Calculate attendance percentage for a user"""
        try:
            query = Attendance.query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(Attendance.date >= start_date)
            if end_date:
                query = query.filter(Attendance.date <= end_date)
            
            total_days = query.count()
            if total_days == 0:
                return 0.0
            
            present_days = query.filter(
                Attendance.status.in_(['present', 'late'])
            ).count()
            
            percentage = (present_days / total_days) * 100
            
            return round(percentage, 2)
            
        except Exception as e:
            print(f"Error calculating percentage: {str(e)}")
            return 0.0
    
    @staticmethod
    def get_today_status(user_id):
        """Get today's attendance status for a user"""
        try:
            today = date.today()
            attendance = Attendance.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if attendance:
                return {
                    'status': attendance.status,
                    'time_in': attendance.time_in.isoformat() if attendance.time_in else None,
                    'marked': True
                }
            else:
                return {
                    'status': 'absent',
                    'time_in': None,
                    'marked': False
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'time_in': None,
                'marked': False
            }
    
    @staticmethod
    def _create_fraud_alert(user_id, alert_type, description, severity):
        """Create a fraud alert"""
        try:
            alert = FraudAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=alert_type,
                description=description,
                severity=severity
            )
            db.session.add(alert)
            db.session.commit()
        except Exception as e:
            print(f"Error creating fraud alert: {str(e)}")
    
    @staticmethod
    def check_unusual_patterns(user_id):
        """Check for unusual attendance patterns"""
        try:
            # Get last 30 days of attendance
            thirty_days_ago = date.today() - timedelta(days=30)
            records = Attendance.query.filter(
                Attendance.user_id == user_id,
                Attendance.date >= thirty_days_ago
            ).all()
            
            if len(records) < 10:
                return  # Not enough data
            
            # Check for sudden 100% attendance after poor attendance
            recent_10 = records[-10:]
            older_10 = records[-20:-10] if len(records) >= 20 else []
            
            if older_10:
                old_percentage = sum(1 for r in older_10 if r.status in ['present', 'late']) / len(older_10)
                new_percentage = sum(1 for r in recent_10 if r.status in ['present', 'late']) / len(recent_10)
                
                if old_percentage < 0.5 and new_percentage == 1.0:
                    AttendanceService._create_fraud_alert(
                        user_id,
                        'unusual_pattern',
                        f"Sudden change in attendance pattern: {old_percentage:.0%} to {new_percentage:.0%}",
                        'medium'
                    )
            
        except Exception as e:
            print(f"Error checking patterns: {str(e)}")

class SessionService:
    
    @staticmethod
    def start_session(staff_id, class_name, subject, duration_minutes=60, late_threshold=15):
        """Start a new attendance session"""
        try:
            # Check if staff exists
            staff = User.query.get(staff_id)
            if not staff or staff.role != 'staff':
                return False, "Invalid staff user", None
            
            # Check if there's already an active session
            active_session = AttendanceSession.query.filter_by(is_active=True).first()
            if active_session:
                return False, "An attendance session is already active", None
            
            # Create new session
            session = AttendanceSession(
                session_id=str(uuid.uuid4()),
                staff_id=staff_id,
                class_name=class_name,
                subject=subject,
                start_time=datetime.utcnow(),
                is_active=True,
                late_threshold_minutes=late_threshold
            )
            
            db.session.add(session)
            db.session.commit()
            
            return True, "Session started successfully", session.to_dict()
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error starting session: {str(e)}", None
    
    @staticmethod
    def stop_session(session_id, staff_id):
        """Stop an active attendance session"""
        try:
            session = AttendanceSession.query.get(session_id)
            
            if not session:
                return False, "Session not found"
            
            if session.staff_id != staff_id:
                return False, "Unauthorized to stop this session"
            
            if not session.is_active:
                return False, "Session is already stopped"
            
            session.is_active = False
            session.end_time = datetime.utcnow()
            
            db.session.commit()
            
            # Get attendance summary
            total_attendance = Attendance.query.filter_by(session_id=session_id).count()
            present_count = Attendance.query.filter_by(
                session_id=session_id,
                status='present'
            ).count()
            late_count = Attendance.query.filter_by(
                session_id=session_id,
                status='late'
            ).count()
            
            summary = {
                'total': total_attendance,
                'present': present_count,
                'late': late_count,
                'absent': 0  # Would need total student count
            }
            
            return True, "Session stopped successfully", summary
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error stopping session: {str(e)}", None
    
    @staticmethod
    def get_active_session():
        """Get currently active session"""
        try:
            session = AttendanceSession.query.filter_by(is_active=True).first()
            return session.to_dict() if session else None
        except Exception as e:
            print(f"Error getting active session: {str(e)}")
            return None
