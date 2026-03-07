@echo off
title GST Filing - Portal
cd /d "%~dp0"

:: Kill any old process on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Use venv python if it exists, otherwise use system python
if exist "portal\backend\venv\Scripts\python.exe" (
    set PYTHON="%~dp0portal\backend\venv\Scripts\python.exe"
) else (
    set PYTHON=python
)

echo Starting GST Filing Portal...
start "GST Filing Backend" cmd /k "cd /d "%~dp0" && %PYTHON% -m uvicorn portal.backend.app.main:app --port 8000"
timeout /t 4 /nobreak >nul
start http://localhost:8000

echo Portal running at http://localhost:8000
echo Close this window when done.
pause
