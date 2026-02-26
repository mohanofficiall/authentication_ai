import os
import sys
from datetime import datetime, date

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from database.db import db
from models.user import User
from models.attendance import Attendance
import uuid

def verify_cascade():
    app = create_app()
    with app.app_context():
        # 1. Create a test user
        test_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            user_id=str(uuid.uuid4()),
            name="Test User",
            email=test_email,
            password_hash="dummy_hash",
            role="student",
            is_active=True
        )
        db.session.add(user)
        
        # 2. Add an attendance record
        attendance = Attendance(
            attendance_id=str(uuid.uuid4()),
            user_id=user.user_id,
            date=date.today(),
            time_in=datetime.utcnow(),
            status="present"
        )
        db.session.add(attendance)
        db.session.commit()
        
        user_id = user.user_id
        attendance_id = attendance.attendance_id
        
        print(f"Created user {user_id} and attendance {attendance_id}")
        
        # 3. Verify they exist
        u = User.query.get(user_id)
        a = Attendance.query.get(attendance_id)
        if not u or not a:
            print("FAILED: Setup failed, records not found.")
            return

        # 4. Delete the user
        db.session.delete(u)
        db.session.commit()
        print(f"Deleted user {user_id}")
        
        # 5. Check if attendance record is still there
        a_after = Attendance.query.get(attendance_id)
        if a_after:
            print("FAILED: Attendance record still exists!")
        else:
            print("SUCCESS: Attendance record was deleted automatically.")

if __name__ == "__main__":
    verify_cascade()
