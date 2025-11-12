#!/bin/bash

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================"
echo "  구글/유튜브 모바일 검색 크롤러"
echo "================================================"
echo ""

# Python 설치 확인
echo "[1/3] Python 버전 확인 중..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}[오류] Python이 설치되어 있지 않습니다.${NC}"
    echo "Python 3.8 이상을 설치해주세요."
    echo "https://www.python.org/downloads/"
    exit 1
fi

# Python 명령어 확인
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

$PYTHON_CMD --version
echo ""

# 필요한 패키지 설치 확인
echo "[2/3] 필요한 패키지 확인 중..."
if ! $PIP_CMD show flask &> /dev/null; then
    echo ""
    echo -e "${YELLOW}[알림] 필요한 패키지를 설치합니다...${NC}"
    echo "이 작업은 최초 1회만 수행됩니다."
    echo ""
    $PIP_CMD install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[오류] 패키지 설치 실패${NC}"
        echo "다음 명령어를 수동으로 실행해주세요:"
        echo "$PIP_CMD install -r requirements.txt"
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[완료] 패키지 설치 완료!${NC}"
    echo ""
else
    echo -e "${GREEN}[확인] 패키지가 이미 설치되어 있습니다.${NC}"
    echo ""
fi

# Chrome 설치 확인 (경고만 표시)
echo "[3/3] Chrome 브라우저 확인 중..."
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || [ -d "/Applications/Google Chrome.app" ]; then
    echo -e "${GREEN}[확인] Chrome 브라우저가 설치되어 있습니다.${NC}"
else
    echo -e "${YELLOW}[경고] Chrome 브라우저를 찾을 수 없습니다.${NC}"
    echo "Chrome이 설치되어 있지 않으면 크롤링이 작동하지 않습니다."
    echo "https://www.google.com/chrome/"
fi
echo ""

echo "================================================"
echo "  서버를 시작합니다..."
echo "================================================"
echo ""
echo "브라우저가 자동으로 열립니다!"
echo "만약 열리지 않으면 다음 주소로 접속하세요:"
echo ""
echo -e "    ${BLUE}http://localhost:5000${NC}"
echo ""
echo "서버를 종료하려면 Ctrl+C를 누르세요."
echo "================================================"
echo ""

# Flask 서버 실행
$PYTHON_CMD app.py

# 서버 종료 시
echo ""
echo "================================================"
echo "  서버가 종료되었습니다."
echo "================================================"


