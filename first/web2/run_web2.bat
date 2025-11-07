@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================
echo  Web News Crawler v2 - Starting...
echo  Port: 8855
echo ============================================
echo.

REM Check and kill port 8855
netstat -ano | findstr ":8855" > nul
if %errorlevel% equ 0 (
    echo Checking port 8855...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8855"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak > nul
)

REM Check Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not installed
    pause
    exit /b 1
)

REM Check Flask
python -c "import flask" > nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Flask...
    pip install -r requirements.txt
)

REM Start Flask server
echo.
echo Starting Flask server on port 8855...
echo.

start /B python web2_app.py

timeout /t 4 /nobreak > nul

echo Opening browser...
start http://localhost:8855

echo.
echo ============================================
echo  App started! 
echo  URL: http://localhost:8855
echo  Press Ctrl+C to stop
echo ============================================
echo.

pause > nul
