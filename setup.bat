@echo off
title GST Filing - First Time Setup
echo ============================================
echo  GST Filing - Setup
echo ============================================
echo.
echo This will install all required dependencies.
echo Run this once after cloning or pulling updates.
echo.

:: ── Check Python ──────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Download Python 3.11 or newer from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo    Python %PY_VER% found.
echo.

:: ── Check Node.js ─────────────────────────────
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found.
    echo Download Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo    Node.js %NODE_VER% found.
echo.

:: ── Main Python venv ──────────────────────────
echo [3/5] Setting up main Python environment...
if not exist "venv\" (
    python -m venv venv
    echo    Created venv.
) else (
    echo    venv already exists, skipping creation.
)
call venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo    Main dependencies installed.
echo.

:: ── Portal backend venv ───────────────────────
echo [4/5] Setting up portal backend environment...
if not exist "portal\backend\venv\" (
    python -m venv portal\backend\venv
    echo    Created portal venv.
) else (
    echo    Portal venv already exists, skipping creation.
)
call portal\backend\venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r portal\backend\requirements.txt
echo    Portal backend dependencies installed.
echo.

:: ── Frontend build ────────────────────────────
echo [5/5] Building frontend...
cd /d "%~dp0portal\frontend"
call npm install --silent
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed.
    pause
    exit /b 1
)
cd /d "%~dp0"
echo    Frontend built successfully.
echo.

echo ============================================
echo  Setup complete!
echo.
echo  To start the portal, run: start-portal.bat
echo  To update later, run:     git pull
echo                 then:      setup.bat
echo ============================================
echo.
pause
