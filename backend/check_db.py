from app import create_app
from database.db import db
from models.user import User

app = create_app()
with app.app_context():
    try:
        admin = User.query.filter_by(email='admin@attendance.com').first()
        if admin:
            print(f"Admin found: {admin.name}, Active: {admin.is_active}")
        else:
            print("Admin NOT found!")
    except Exception as e:
        print(f"Database error: {e}")
