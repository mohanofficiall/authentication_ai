# AI Smart Attendance System

In many colleges and companies, proxy attendance is a major issue. Students mark attendance for others using fake methods like photos, screenshots, or remote logins.

To solve this, we built an AI-Powered Smart Attendance System that uses Face Recognition, Liveness Detection, and Geo-Fencing to prevent fraud.

## 🚀 Features

- ✅ **Face Recognition** (99.38% accuracy using dlib)
- ✅ **Role-Based Access Control** (Student/Staff/Admin)
- ✅ **JWT Authentication**
- ✅ **Real-time Attendance Marking**
- ✅ **Fraud Detection & Alerts**
- ✅ **Session Management**
- ✅ **Comprehensive Analytics**
- ✅ **Export Reports** (Excel/CSV/PDF)
- ✅ **Premium Dark-Themed UI**
- ✅ **Liveness Detection** (Blink/Head Movement)
- ✅ **Attendance Cooldown**
- ✅ **Correction Requests**

## 📋 Prerequisites

- Python 3.7+ (64-bit recommended for Windows)
- CMake (for dlib installation)
- Visual C++ Build Tools (Windows only)
- Modern web browser with webcam support

## 🛠️ Installation

### Step 1: Install System Dependencies

#### Windows:
1. Install [Python 3.8+](https://www.python.org/downloads/) (64-bit)
2. Install [CMake](https://cmake.org/download/)
3. Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/) with "Desktop development with C++"

#### macOS:
```bash
brew install cmake
```

#### Linux:
```bash
sudo apt-get update
sudo apt-get install cmake build-essential
```

### Step 2: Set Up Python Environment

```bash
# Navigate to project directory
cd authentication

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note**: Installing `dlib` and `face_recognition` may take 5-10 minutes on first install.

### Step 4: Initialize Database

```bash
# From backend directory
python app.py
```

This will:
- Create the SQLite database
- Create all tables
- Create default admin user: `admin@attendance.com` / `Admin@123`

## 🎯 Running the Application

### Start the Backend Server

```bash
# From backend directory (with venv activated)
python app.py
```

Server will start on `http://localhost:5000`

### Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## 👥 Default Credentials

**Admin Account:**
- Email: `admin@attendance.com`
- Password: `Admin@123`

## 📖 User Guide

### For Students:

1. **Register**:
   - Go to `/register.html`
   - Fill in your details
   - Select role: "Student"
   - Capture your face using webcam
   - Submit registration

2. **Login**:
   - Use your email and password
   - You'll be redirected to student dashboard

3. **Mark Attendance**:
   - Click "Mark Attendance"
   - Allow camera access
   - Position your face in the frame
   - Follow liveness prompts (blink/turn head)
   - Attendance will be marked automatically

4. **View Attendance**:
   - Dashboard shows today's status
   - View attendance percentage
   - See attendance history

### For Staff:

1. **Start Session**:
   - Login to staff dashboard
   - Click "Start Session"
   - Enter class name and subject
   - Set duration and late threshold

2. **Monitor Attendance**:
   - View real-time attendance count
   - See list of present/late/absent students

3. **Stop Session**:
   - Click "Stop Session"
   - View final attendance summary

4. **Manage Corrections**:
   - Review correction requests from students
   - Approve or reject with comments

### For Admin:

1. **View Analytics**:
   - System-wide attendance statistics
   - User distribution by role
   - Attendance trends (last 30 days)

2. **Manage Users**:
   - Create/Edit/Delete users
   - Reset passwords
   - Activate/Deactivate accounts

3. **Monitor Fraud Alerts**:
   - View unresolved alerts
   - Check high-severity incidents
   - Resolve alerts

4. **Export Reports**:
   - Select date range
   - Choose format (Excel/CSV/PDF)
   - Download attendance data

## 🔧 Configuration

Edit `backend/config.py` to customize:

- **Database**: Change from SQLite to PostgreSQL for production
- **JWT Settings**: Token expiration time
- **Face Recognition**: Tolerance and confidence thresholds
- **Attendance**: Cooldown period, late threshold
- **Security**: Rate limiting, BCRYPT rounds

## 📁 Project Structure

```
authentication/
├── backend/
│   ├── app.py                 # Flask app entry point
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # Database models
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic
│   ├── utils/                 # Utilities
│   └── database/              # Database setup
├── frontend/
│   ├── index.html             # Landing page
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript files
└── README.md
```

## 🔐 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: 24-hour expiration
- **Face Encoding Encryption**: Fernet encryption
- **Rate Limiting**: Prevents brute force attacks
- **CSRF Protection**: Flask-WTF
- **Input Validation**: XSS prevention
- **Fraud Detection**: Real-time alerts

## 🐛 Troubleshooting

### dlib Installation Fails (Windows)

1. Download pre-compiled wheel from [here](https://github.com/z-mahmud22/Dlib_Windows_Python3.x)
2. Install: `pip install dlib-19.24.2-cp38-cp38-win_amd64.whl`
3. Then install face_recognition: `pip install face_recognition`

### Camera Not Working

- Ensure browser has camera permissions
- Check if another application is using the camera
- Try a different browser (Chrome/Firefox recommended)

### Server Won't Start

- Check if port 5000 is already in use
- Verify all dependencies are installed
- Check Python version (3.7+ required)

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/verify-token` - Verify JWT token

### Student
- `POST /api/student/mark-attendance` - Mark attendance
- `GET /api/student/dashboard` - Get dashboard data
- `GET /api/student/attendance-history` - Get attendance history
- `POST /api/student/request-correction` - Request correction

### Staff
- `POST /api/staff/session/start` - Start session
- `POST /api/staff/session/stop/<session_id>` - Stop session
- `GET /api/staff/dashboard` - Get dashboard data
- `POST /api/staff/corrections/<request_id>/approve` - Approve correction

### Admin
- `GET /api/admin/analytics` - Get system analytics
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/<user_id>` - Update user
- `DELETE /api/admin/users/<user_id>` - Delete user
- `GET /api/admin/fraud-alerts` - Get fraud alerts

## 🚀 Future Enhancements

- [ ] Rasa NLP Chatbot Integration
- [ ] Fingerprint Scanner Support
- [ ] Geo-location Verification
- [ ] Offline Attendance Sync
- [ ] Email/SMS Notifications
- [ ] Parent Dashboard
- [ ] Multi-language Support
- [ ] Mobile App (React Native)
- [ ] AI Attendance Prediction
- [ ] Advanced Analytics Dashboard

## 📝 License

This project is for educational purposes.

## 👨‍💻 Developer

Built with ❤️ using:
- Python Flask
- face_recognition (dlib)
- SQLAlchemy
- JWT
- HTML/CSS/JavaScript
- Font Awesome
- Google Fonts

---

**Note**: This is a development version. For production deployment, use PostgreSQL, configure proper SSL, and deploy on a cloud platform (AWS/Google Cloud/Heroku).
