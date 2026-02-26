"""
Email Configuration for OTP Verification
IMPORTANT: Replace with your actual Gmail credentials
"""

# Gmail SMTP Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False

# TODO: Replace these with your actual credentials
MAIL_USERNAME = 'your-email@gmail.com'  # Your Gmail address
MAIL_PASSWORD = 'your-16-digit-app-password'  # Your 16-digit Gmail App Password

# Email sender details
MAIL_DEFAULT_SENDER = ('Attendo.AI', 'your-email@gmail.com')  # Display name and email

# OTP Configuration
OTP_EXPIRY_MINUTES = 5  # OTP expires after 5 minutes
OTP_LENGTH = 6  # 6-digit OTP code
