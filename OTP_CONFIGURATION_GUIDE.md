# OTP Email Verification - Configuration Guide

## ✅ Implementation Complete!

The OTP email verification system has been successfully implemented. Follow these steps to configure and test it.

---

## 📧 Step 1: Configure Email Credentials

You need to add your Gmail credentials to the configuration file.

### Option A: Using Environment Variables (Recommended)

1. Create a `.env` file in the `backend` folder:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-digit-app-password
   ```

2. The application will automatically load these credentials

### Option B: Direct Configuration

Edit `backend/config.py` and update lines 50-51:
```python
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-16-digit-app-password'
```

---

## 🔑 Step 2: Get Your Gmail App Password

If you haven't already, follow these steps:

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** if not already enabled
3. Scroll down and click **App passwords**
4. Select **Mail** and **Other (Custom name)**
5. Enter "Attendo.AI" as the name
6. Click **Generate**
7. Copy the 16-digit password (format: `abcd efgh ijkl mnop`)
8. Use this password in your configuration

---

## 🔄 Step 3: Restart the Server

After configuring your email credentials:

1. Stop the current server (Ctrl+C in the terminal)
2. Restart it:
   ```bash
   cd backend
   python app.py
   ```

---

## 🧪 Step 4: Test the OTP Flow

### Registration Flow:
1. Go to http://localhost:5000/register.html
2. Fill in all required fields (name, email, password, role, face image)
3. Click **Register**
4. You should see: "OTP sent to your email! Redirecting to verification..."
5. Check your email inbox for the OTP (6-digit code)
6. You'll be redirected to the OTP verification page
7. Enter the 6-digit OTP code
8. Click **Verify OTP**
9. On success, you'll be redirected to login

### Email Features:
- ✅ Professional "Attendo.AI One Time Password" branding
- ✅ 6-digit OTP code
- ✅ 5-minute expiration timer
- ✅ Resend OTP functionality
- ✅ Proper formatting to avoid spam folder

---

## 🎨 What's New

### Backend Changes:
- ✅ Added `otp_code`, `otp_expires_at`, `is_verified` fields to User model
- ✅ Created `EmailService` for sending professional OTP emails
- ✅ Modified `/api/auth/register` to send OTP instead of completing registration
- ✅ Added `/api/auth/verify-otp` endpoint
- ✅ Added `/api/auth/resend-otp` endpoint
- ✅ Installed Flask-Mail package

### Frontend Changes:
- ✅ Created `verify-otp.html` with 6-digit input fields
- ✅ Added countdown timer (5 minutes)
- ✅ Implemented auto-focus and paste functionality
- ✅ Added resend OTP button
- ✅ Updated registration flow to redirect to OTP page

### Email Template:
- ✅ Professional HTML email with Attendo.AI branding
- ✅ Dark theme matching your application design
- ✅ Large, centered OTP code
- ✅ Security notice
- ✅ Proper headers to ensure inbox delivery

---

## ⚠️ Troubleshooting

### Email not sending?
- Check your Gmail credentials are correct
- Ensure you're using the 16-digit App Password, not your regular Gmail password
- Verify 2-Step Verification is enabled on your Google account
- Check the server logs for error messages

### OTP not arriving?
- Check your spam/junk folder
- Wait a few seconds (email delivery can take 5-30 seconds)
- Try the "Resend OTP" button
- Verify your email address is correct

### Database errors?
- The database has been automatically migrated
- If issues persist, delete `backend/attendance.db` and restart the server

---

## 📝 Notes

- OTP codes expire after **5 minutes**
- Users must verify their email before they can login
- Unverified accounts are created but remain inactive until OTP verification
- Professional email template ensures delivery to inbox (not spam)

---

**Ready to test!** Configure your email credentials and restart the server to try the new OTP verification flow.
