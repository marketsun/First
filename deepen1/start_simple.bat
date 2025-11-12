@echo off
chcp 65001 > nul
title 크롤러 서버

echo 서버를 시작합니다...
echo 브라우저가 자동으로 열립니다!
echo.

python app.py

pause


