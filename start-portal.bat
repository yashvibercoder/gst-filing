@echo off
title GST Filing - Portal
echo ============================================
echo  GST Filing - Starting Portal
echo ============================================
echo.

cd /d "%~dp0"

echo Starting backend on http://localhost:8000 ...
start "GST Filing Backend" cmd /k "portal\backend\venv\Scripts\python -m uvicorn portal.backend.app.main:app --port 8000"

timeout /t 3 /nobreak >nul

start http://localhost:8000

echo Portal is running at http://localhost:8000
echo Keep this window open. Close it when done.
echo.
pause
