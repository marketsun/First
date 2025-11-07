@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo.
echo ============================================
echo  Web News Crawler - Starting...
echo ============================================
echo.

REM Check and kill port 8888
netstat -ano | findstr ":8888" > nul
if %errorlevel% equ 0 (
    echo Checking port 8888...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8888"') do (
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
echo Starting Flask server on port 8888...
echo.

start /B python web_app.py

timeout /t 4 /nobreak > nul

echo Opening browser...
start http://localhost:8888

echo.
echo ============================================
echo  App started! 
echo  URL: http://localhost:8888
echo  Press Ctrl+C to stop
echo ============================================
echo.

pause > nul

