@echo off
setlocal enabledelayedexpansion
title GST Filing - Full Installer
echo ============================================
echo  GST Filing - Full Installer
echo  Installs Python, Node.js, Git + app deps
echo ============================================
echo.

:: ── Check winget ───────────────────────────────
echo Checking Windows Package Manager (winget)...
winget --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: winget not found.
    echo winget is built into Windows 11. Make sure your Windows is up to date.
    pause
    exit /b 1
)
echo    winget found.
echo.

:: ── Refresh PATH from registry (no restart needed) ──
:: This lets us detect newly installed tools in the same session
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USR_PATH=%%b"
if defined USR_PATH (set "PATH=%SYS_PATH%;%USR_PATH%") else (set "PATH=%SYS_PATH%")
:: Also add common Python install locations
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python310"
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
set "PATH=%PATH%;%APPDATA%\npm;%ProgramFiles%\nodejs"

:: ── Install Git ─────────────────────────────────
echo [1/3] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo    Installing Git...
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
    :: Add Git to PATH for this session
    set "PATH=%PATH%;%ProgramFiles%\Git\cmd;%ProgramFiles(x86)%\Git\cmd"
    git --version >nul 2>&1
    if errorlevel 1 (
        echo    Git installed. Please close this window, open a new PowerShell and run install.bat again.
        pause
        exit /b 0
    )
) else (
    echo    Git already installed.
)
echo.

:: ── Install Python ──────────────────────────────
echo [2/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    Python not found in PATH. Checking common install locations...
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
        echo    Found Python 3.12 at AppData location.
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
        echo    Found Python 3.11 at AppData location.
    ) else (
        echo    Installing Python 3.12...
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    )
)
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo    ERROR: Python still not found.
    echo    Please close this window, open a new PowerShell and run install.bat again.
    pause
    exit /b 0
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    %%v found.
echo.

:: ── Install Node.js ─────────────────────────────
echo [3/3] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo    Installing Node.js...
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    :: Add Node to PATH for this session
    set "PATH=%ProgramFiles%\nodejs;%PATH%"
    node --version >nul 2>&1
    if errorlevel 1 (
        echo    Node.js installed. Please close this window, open a new PowerShell and run install.bat again.
        pause
        exit /b 0
    )
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo    Node.js %%v found.
echo.

:: ── All ready — run setup ───────────────────────
echo All prerequisites ready. Running setup...
echo.
call "%~dp0setup.bat"
