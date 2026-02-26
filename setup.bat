@echo off
echo ========================================
echo AI Smart Attendance System - Setup
echo ========================================
echo.

echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.

echo [2/5] Creating virtual environment...
cd backend
python -m venv venv
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate
echo.

echo [4/5] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [5/5] Installing dependencies...
echo This may take 5-10 minutes (dlib compilation)...
pip install -r requirements.txt
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server:
echo   1. cd backend
echo   2. venv\Scripts\activate
echo   3. python app.py
echo.
echo Then open: http://localhost:5000
echo.
echo Default Admin: admin@attendance.com / Admin@123
echo.
pause
