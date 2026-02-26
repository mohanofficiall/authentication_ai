from flask import Flask
from flask_mail import Mail, Message
import logging

app = Flask(__name__)

# Config from your config.py
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='garampalli@gmail.com',
    MAIL_PASSWORD='jethlpukxobliqgv',  # No spaces
    MAIL_DEFAULT_SENDER=('Attendo.AI', 'garampalli@gmail.com'),
    DEBUG=True
)

mail = Mail(app)

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    print("Testing email configuration...")
    print(f"User: {app.config['MAIL_USERNAME']}")
    print(f"Pass len: {len(app.config['MAIL_PASSWORD'])}")
    
    with app.app_context():
        try:
            msg = Message("Test OTP", recipients=["garampalli@gmail.com"])
            msg.body = "If you see this, email is working!"
            mail.send(msg)
            print("\n✅ SUCCESS: Email sent successfully!")
        except Exception as e:
            print(f"\n❌ FAILURE: {e}")
