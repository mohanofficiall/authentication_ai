"""
Debug Email Script
This script tests Gmail SMTP connection and authentication directly.
It helps verify if the email and app password are correct.
"""
import smtplib
import socket

# Configuration to test
EMAIL = 'garampalli@gmail.com'
PASSWORD = 'jeth lpuk xobl iqgv'  # The one you entered

def test_smtp(email, password, use_ssl=False):
    server = 'smtp.gmail.com'
    port = 465 if use_ssl else 587
    
    print(f"\n--- Testing connection to {server}:{port} ({'SSL' if use_ssl else 'TLS'}) ---")
    print(f"Email: {email}")
    print(f"Password length: {len(password)}")
    
    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
            
        print("✓ Connection established")
        print("✓ TLS/SSL handshake successful")
        
        # Try login
        try:
            # Try as is
            print(f"Attempting login with password: '{password}'")
            smtp.login(email, password)
            print("✅ LOGIN SUCCESSFUL! The credentials are correct.")
            smtp.quit()
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Login FAILED: {e}")
            
            # Try without spaces if there are spaces
            if ' ' in password:
                clean_pass = password.replace(' ', '')
                print(f"\nRetrying with spaces removed: '{clean_pass}'")
                try:
                    smtp.login(email, clean_pass)
                    print("✅ LOGIN SUCCESSFUL (without spaces)! Please remove spaces in config.")
                    smtp.quit()
                    return True
                except smtplib.SMTPAuthenticationError as e:
                     print(f"❌ Login FAILED (without spaces): {e}")
            
            smtp.quit()
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing credentials for: {EMAIL}")
    
    # Test 1: Standard TLS (Port 587)
    success = test_smtp(EMAIL, PASSWORD, use_ssl=False)
    
    if not success:
        # Test 2: SSL (Port 465)
        test_smtp(EMAIL, PASSWORD, use_ssl=True)
