@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════╗
echo ║  구글 & 네이버 뉴스 크롤러 시작 중...         ║
echo ╚════════════════════════════════════════════════╝
echo.

REM 이미 실행 중인 프로세스 확인
tasklist | findstr /i "node.exe" > nul
if %errorlevel% equ 0 (
    echo ⚠️  이미 실행 중인 프로세스가 있습니다.
    echo 기존 프로세스를 종료하고 새로 시작합니다...
    taskkill /F /IM node.exe > nul 2>&1
    taskkill /F /IM python.exe > nul 2>&1
    timeout /t 3 /nobreak
)

REM npm 설치 확인
if not exist "node_modules" (
    echo 📦 의존성 설치 중...
    call npm install
)

REM 앱 실행
echo.
echo ✓ 앱을 시작합니다...
echo.

call npm start

pause
