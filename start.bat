@echo off
echo Starting Echo AI Voice Assistant...
echo.
echo Step 1: Checking Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)

echo Step 2: Installing dependencies
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 3: Starting backend server...
echo The server will start on http://127.0.0.1:5000
echo.
echo Once you see "Server running", open your browser to:
echo http://127.0.0.1:5000
echo.
cd backend
python app.py
pause
