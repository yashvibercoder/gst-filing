@echo off
title GST Filing - Setup
echo ============================================
echo  GST Filing - Setup
echo ============================================
echo.

cd /d "%~dp0"

:: ── Check Python ───────────────────────────────
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    echo Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo    Python %PY_VER% found.
echo.

:: ── Check Node.js ──────────────────────────────
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo    Node.js %NODE_VER% found.
echo.

:: ── Install Python packages (global, no venv) ──
echo [3/4] Installing Python packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install -r portal\backend\requirements.txt --quiet
echo    Python packages installed.
echo.

:: ── Build frontend ─────────────────────────────
echo [4/4] Building frontend...
cd /d "%~dp0portal\frontend"
call npm install --silent
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed.
    pause
    exit /b 1
)
cd /d "%~dp0"
echo    Frontend built.
echo.

echo ============================================
echo  Setup complete!
echo  Run start-portal.bat to start the app.
echo ============================================
echo.
pause
