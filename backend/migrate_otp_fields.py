"""
Database Migration Script - Add OTP fields to User table
Run this script to update the database schema with OTP verification fields
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), 'attendance.db')

print(f"Updating database: {db_path}")

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add otp_code column if it doesn't exist
    if 'otp_code' not in columns:
        print("Adding otp_code column...")
        cursor.execute("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)")
        print("✓ Added otp_code column")
    else:
        print("✓ otp_code column already exists")
    
    # Add otp_expires_at column if it doesn't exist
    if 'otp_expires_at' not in columns:
        print("Adding otp_expires_at column...")
        cursor.execute("ALTER TABLE users ADD COLUMN otp_expires_at DATETIME")
        print("✓ Added otp_expires_at column")
    else:
        print("✓ otp_expires_at column already exists")
    
    # Add is_verified column if it doesn't exist
    if 'is_verified' not in columns:
        print("Adding is_verified column...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
        print("✓ Added is_verified column")
    else:
        print("✓ is_verified column already exists")
    
    # Commit changes
    conn.commit()
    print("\n✅ Database migration completed successfully!")
    
    # Show updated schema
    cursor.execute("PRAGMA table_info(users)")
    print("\nUpdated User table schema:")
    for column in cursor.fetchall():
        print(f"  - {column[1]} ({column[2]})")
    
except Exception as e:
    print(f"\n❌ Error during migration: {str(e)}")
    conn.rollback()
finally:
    conn.close()
