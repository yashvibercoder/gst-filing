@echo off
setlocal enabledelayedexpansion
title GST Filing - Full Installer
echo ============================================
echo  GST Filing - Full Installer
echo  Installs Python, Node.js, Git + app deps
echo ============================================
echo.

:: ── Check winget (built into Windows 11) ──────
echo Checking Windows Package Manager (winget)...
winget --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget not found.
    echo winget is built into Windows 11. Make sure your Windows is up to date.
    echo Alternatively, install it from: https://aka.ms/getwinget
    pause
    exit /b 1
)
echo    winget found.
echo.

:: ── Install Git ───────────────────────────────
echo [1/3] Installing Git...
git --version >nul 2>&1
if errorlevel 1 (
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
    echo    Git installed. Refreshing PATH...
    call refreshenv >nul 2>&1
) else (
    echo    Git already installed, skipping.
)
echo.

:: ── Install Python ────────────────────────────
echo [2/3] Installing Python 3.12...
python --version >nul 2>&1
if errorlevel 1 (
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    echo    Python installed.
    echo    NOTE: Close and reopen this window, then run install.bat again to continue.
    echo    (PATH needs to refresh after Python install)
    pause
    exit /b 0
) else (
    echo    Python already installed, skipping.
)
echo.

:: ── Install Node.js ───────────────────────────
echo [3/3] Installing Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    echo    Node.js installed.
    echo    NOTE: Close and reopen this window, then run install.bat again to continue.
    echo    (PATH needs to refresh after Node.js install)
    pause
    exit /b 0
) else (
    echo    Node.js already installed, skipping.
)
echo.

:: ── All prerequisites ready, run setup ────────
echo All prerequisites are installed.
echo Running application setup...
echo.
call "%~dp0setup.bat"
