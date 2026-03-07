@echo off
title GST Filing - Portal
echo ============================================
echo  GST Filing - Starting Portal
echo ============================================
echo.

:: Build frontend if dist folder doesn't exist
if not exist "%~dp0portal\frontend\dist\" (
    echo Building frontend (first run, takes 1-2 minutes)...
    cd /d "%~dp0portal\frontend"
    call npm run build
    if errorlevel 1 (
        echo.
        echo ERROR: Frontend build failed!
        pause
        exit /b 1
    )
    echo Frontend built successfully.
    echo.
)

:: Start backend
echo Starting portal on http://localhost:8000 ...
cd /d "%~dp0"
start "GST Filing Backend" cmd /k "portal\backend\venv\Scripts\python -m uvicorn portal.backend.app.main:app --port 8000"
timeout /t 3 /nobreak >nul

:: Open browser
start http://localhost:8000

echo.
echo ============================================
echo  Portal is running at http://localhost:8000
echo  Open that address in any browser.
echo.
echo  Keep this window open while using the app.
echo  Close it when you are done.
echo ============================================
echo.
pause >nul
