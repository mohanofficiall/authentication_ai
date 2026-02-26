-- AI Smart Attendance System Database Schema
-- SQLite/PostgreSQL compatible schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'staff', 'admin')),
    student_id VARCHAR(50),
    staff_id VARCHAR(50),
    face_encoding BLOB,
    fingerprint_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    time_in TIMESTAMP NOT NULL,
    time_out TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'late', 'absent')),
    confidence_score REAL,
    geo_location VARCHAR(255),
    device_info TEXT,
    marked_by VARCHAR(20) CHECK (marked_by IN ('face', 'fingerprint', 'manual')),
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES attendance_sessions(session_id) ON DELETE SET NULL
);

-- Attendance sessions table
CREATE TABLE IF NOT EXISTS attendance_sessions (
    session_id TEXT PRIMARY KEY,
    staff_id TEXT NOT NULL,
    class_name VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    late_threshold_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Correction requests table
CREATE TABLE IF NOT EXISTS correction_requests (
    request_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    attendance_id TEXT,
    request_date DATE NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    review_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (attendance_id) REFERENCES attendance(attendance_id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Fraud alerts table
CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('duplicate', 'mismatch', 'unusual_pattern', 'device_change', 'location_anomaly')),
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    log_id TEXT PRIMARY KEY,
    user_id TEXT,
    action VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    device_id VARCHAR(255),
    user_agent TEXT,
    status VARCHAR(20),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    uploader_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,
    title TEXT,
    description TEXT,
    subject TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    announcement_id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_staff ON attendance_sessions(staff_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON attendance_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_corrections_user ON correction_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_corrections_status ON correction_requests(status);
CREATE INDEX IF NOT EXISTS idx_fraud_user ON fraud_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_fraud_severity ON fraud_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_logs_user ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_documents_uploader ON documents(uploader_id);
