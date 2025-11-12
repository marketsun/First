@echo off
chcp 65001 > nul
title 구글/유튜브 검색 크롤러

echo ================================================
echo   구글/유튜브 모바일 검색 크롤러
echo ================================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] Python 버전 확인 중...
python --version
echo.

REM 필요한 패키지 설치 확인
echo [2/3] 필요한 패키지 확인 중...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo.
    echo [알림] 필요한 패키지를 설치합니다...
    echo 이 작업은 최초 1회만 수행됩니다.
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [오류] 패키지 설치 실패
        echo 다음 명령어를 수동으로 실행해주세요:
        echo pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [완료] 패키지 설치 완료!
    echo.
) else (
    echo [확인] 패키지가 이미 설치되어 있습니다.
    echo.
)

REM Chrome 설치 확인 (경고만 표시)
echo [3/3] Chrome 브라우저 확인 중...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [확인] Chrome 브라우저가 설치되어 있습니다.
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [확인] Chrome 브라우저가 설치되어 있습니다.
) else (
    echo [경고] Chrome 브라우저를 찾을 수 없습니다.
    echo Chrome이 설치되어 있지 않으면 크롤링이 작동하지 않습니다.
    echo https://www.google.com/chrome/
)
echo.

echo ================================================
echo   서버를 시작합니다...
echo ================================================
echo.
echo 브라우저가 자동으로 열립니다!
echo 만약 열리지 않으면 다음 주소로 접속하세요:
echo.
echo     http://localhost:5000
echo.
echo 서버를 종료하려면 Ctrl+C를 누르세요.
echo ================================================
echo.

REM Flask 서버 실행
python app.py

REM 서버 종료 시
echo.
echo ================================================
echo   서버가 종료되었습니다.
echo ================================================
pause


