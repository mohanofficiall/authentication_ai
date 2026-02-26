"""
Email Service for sending OTP verification emails
"""
from flask_mail import Mail, Message
from flask import current_app
import random
from datetime import datetime, timedelta

mail = Mail()

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    @staticmethod
    def send_otp_email(recipient_email, recipient_name, otp_code):
        """
        Send OTP verification email with professional Attendo.AI branding
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Name of the recipient
            otp_code: 6-digit OTP code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create professional HTML email
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendo.AI - One Time Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 32px; font-weight: 700; margin-bottom: 10px;">
                                Attendo.AI
                            </div>
                            <h1 style="color: #f1f5f9; font-size: 24px; font-weight: 600; margin: 0;">One Time Password</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #cbd5e1; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Hello <strong style="color: #f1f5f9;">{recipient_name}</strong>,
                            </p>
                            <p style="color: #cbd5e1; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                Thank you for registering with Attendo.AI Smart Attendance System. Please use the following One Time Password (OTP) to complete your registration:
                            </p>
                            
                            <!-- OTP Box -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 30px 0;">
                                        <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 12px; padding: 20px 40px; display: inline-block;">
                                            <div style="color: #ffffff; font-size: 42px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                                {otp_code}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #cbd5e1; font-size: 16px; line-height: 1.6; margin: 20px 0;">
                                This OTP will expire in <strong style="color: #f1f5f9;">5 minutes</strong>. Please do not share this code with anyone.
                            </p>
                            
                            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                <p style="color: #fca5a5; font-size: 14px; margin: 0;">
                                    <strong>Security Notice:</strong> If you did not request this OTP, please ignore this email or contact our support team.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid rgba(99, 102, 241, 0.2);">
                            <p style="color: #64748b; font-size: 14px; text-align: center; margin: 0;">
                                This is an automated email from Attendo.AI Smart Attendance System.<br>
                                Please do not reply to this email.
                            </p>
                            <p style="color: #475569; font-size: 12px; text-align: center; margin: 15px 0 0;">
                                © 2024 Attendo.AI. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
            
            # Plain text fallback
            text_body = f"""
Attendo.AI - One Time Password

Hello {recipient_name},

Thank you for registering with Attendo.AI Smart Attendance System.

Your One Time Password (OTP) is: {otp_code}

This OTP will expire in 5 minutes. Please do not share this code with anyone.

If you did not request this OTP, please ignore this email.

---
This is an automated email from Attendo.AI Smart Attendance System.
© 2024 Attendo.AI. All rights reserved.
"""
            
            # Create message
            msg = Message(
                subject='Attendo.AI - One Time Password',
                recipients=[recipient_email],
                html=html_body,
                body=text_body
            )
            
            # Send email
            mail.send(msg)
            current_app.logger.info(f'OTP email sent successfully to {recipient_email}')
            return True
            
        except Exception as e:
            current_app.logger.error(f'Failed to send OTP email to {recipient_email}: {str(e)}')
            return False
    
    @staticmethod
    def get_otp_expiry():
        """Get OTP expiry datetime (5 minutes from now)"""
        return datetime.utcnow() + timedelta(minutes=5)
