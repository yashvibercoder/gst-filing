@echo off
title GST Portal Launcher
echo ============================================
echo  GST Portal - ngrok Sharing Mode
echo ============================================
echo.

:: Step 1: Build frontend
echo [1/3] Building frontend (one-time)...
cd /d "%~dp0portal\frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Frontend build failed! Check Node.js is installed.
    pause
    exit /b 1
)
echo Frontend built successfully.
echo.

:: Step 2: Start backend (serves frontend + API on port 8000)
echo [2/3] Starting backend server...
cd /d "%~dp0"
start "GST Backend (port 8000)" cmd /k "portal\backend\venv\Scripts\python -m uvicorn portal.backend.app.main:app --port 8000"
timeout /t 4 /nobreak >nul

:: Step 3: Start ngrok tunnel on port 8000
echo [3/3] Starting ngrok tunnel...
start "GST ngrok tunnel" cmd /k "ngrok http 8000"
timeout /t 5 /nobreak >nul

:: Get the public ngrok URL via its local API
echo Fetching public URL...
for /f "delims=" %%i in ('powershell -Command "(Invoke-RestMethod http://localhost:4040/api/tunnels).tunnels | Where-Object { $_.proto -eq \"https\" } | Select-Object -First 1 -ExpandProperty public_url"') do set NGROK_URL=%%i

echo.
echo ============================================
echo  Local:   http://localhost:8000
echo  Public:  %NGROK_URL%
echo.
echo  Share the PUBLIC URL with any device!
echo ============================================
echo.

:: Open public URL in browser
if defined NGROK_URL (
    start %NGROK_URL%
) else (
    echo Could not fetch ngrok URL. Check the ngrok window.
    start http://localhost:8000
)

echo Press any key to close this window (servers keep running).
pause >nul
