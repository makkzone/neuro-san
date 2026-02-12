@echo off
REM Neuro-SAN Server Startup Script for Windows
REM This script handles all necessary steps to launch the neuro-san server

setlocal enabledelayedexpansion

echo ===============================================
echo   Neuro-SAN Server Startup
echo ===============================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
cd /d "%PROJECT_DIR%"

echo Project directory: %PROJECT_DIR%
echo.

REM Check if virtual environment exists
if not exist "venv" if not exist ".venv" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
if exist ".venv" (
    set VENV_DIR=.venv
) else (
    set VENV_DIR=venv
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Set PYTHONPATH
set PYTHONPATH=%PROJECT_DIR%
echo PYTHONPATH set to: %PYTHONPATH%
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import neuro_san" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed
) else (
    echo Dependencies already installed
)
echo.

REM Check for API keys
if not defined OPENAI_API_KEY (
    echo WARNING: OPENAI_API_KEY environment variable is not set!
    echo Some features may not work without API keys.
    echo Set it with: set OPENAI_API_KEY=your-key-here
    echo.
)

REM Enable CORS headers for web applications
set AGENT_ALLOW_CORS_HEADERS=1
echo CORS headers enabled
echo.

REM Start the server
echo ===============================================
echo   Starting Neuro-SAN Server on port 8080
echo ===============================================
echo.
echo Server will be available at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo.

python -m neuro_san.service.main_loop.server_main_loop
