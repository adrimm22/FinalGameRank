@echo off
echo ====================================
echo GameRank - Setup and Run Script
echo ====================================
echo.

echo Step 1: Installing dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Running migrations...
python manage.py migrate
echo.

echo Step 3: Starting development server...
echo.
echo Server will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver

