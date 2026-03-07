@echo off
title GST Filing - Portal
echo ============================================
echo  GST Filing - Starting Portal
echo ============================================
echo.

cd /d "%~dp0"

:: Kill any old process on port 8000
echo Stopping any existing server on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Start backend
echo Starting backend...
start "GST Filing Backend" cmd /k "cd /d "%~dp0" && portal\backend\venv\Scripts\python -m uvicorn portal.backend.app.main:app --port 8000"
timeout /t 4 /nobreak >nul

:: Open browser
start http://localhost:8000

echo.
echo ============================================
echo  Portal running at http://localhost:8000
echo  Keep this window open while using the app.
echo  Close it when done.
echo ============================================
pause
