# 설치 및 실행 가이드

## 📋 사전 요구사항

### 1. Python 설치
- Python 3.8 이상이 필요합니다
- [Python 공식 웹사이트](https://www.python.org/downloads/)에서 다운로드
- 설치 시 "Add Python to PATH" 옵션 체크

### 2. Google Chrome 브라우저 설치
- Selenium이 Chrome을 사용하므로 필수입니다
- [Chrome 다운로드](https://www.google.com/chrome/)

## 🚀 설치 방법

### 1단계: 프로젝트 폴더로 이동
```bash
cd C:\Users\HOTSELLER\Desktop\Project\deepen1
```

### 2단계: 가상환경 생성 (선택사항이지만 권장)
```bash
python -m venv venv
```

### 3단계: 가상환경 활성화 (가상환경을 만든 경우)

**Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

### 4단계: 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

설치 중 오류가 발생하면:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## ▶️ 실행 방법

### 애플리케이션 시작
```bash
python app.py
```

성공적으로 실행되면 다음과 같은 메시지가 표시됩니다:
```
==================================================
구글/유튜브 모바일 검색 크롤러 시작
브라우저에서 http://localhost:5000 접속
==================================================
```

### 웹 브라우저에서 접속
브라우저를 열고 다음 주소로 접속:
```
http://localhost:5000
```

## 🎯 사용 방법

### 1. 검색하기
1. 메인 페이지에서 검색하고 싶은 키워드 입력
2. "검색" 버튼 클릭
3. 진행 상황을 확인하며 대기 (1-2분 소요)
4. 완료되면 자동으로 결과 페이지로 이동

### 2. 결과 보기
- **구글 결과**: 제목, URL, 설명, 썸네일, 순위
- **유튜브 결과**: 제목, URL, 채널명, 조회수, 업로드 날짜, 썸네일, 순위

### 3. 필터링하기
- **키워드 필터**: 제목이나 설명에서 특정 단어 검색
- **날짜 필터**: 특정 기간의 유튜브 영상만 보기
- **정렬**: 조회수 또는 날짜 기준으로 정렬

### 4. 검색 기록 관리
- 상단 메뉴에서 "검색 기록" 클릭
- 이전 검색 결과 확인
- 필요없는 기록 삭제

## ⚠️ 문제 해결

### 1. 포트가 이미 사용 중인 경우
```
Error: Address already in use
```

**해결 방법**: `app.py` 파일의 마지막 줄을 수정
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 5000 → 5001로 변경
```

### 2. Chrome 드라이버 오류
```
selenium.common.exceptions.WebDriverException
```

**해결 방법**:
- Chrome 브라우저가 최신 버전인지 확인
- 프로그램 재실행 (자동으로 드라이버 다운로드)

### 3. 크롤링이 너무 느린 경우
- 정상입니다. 50개씩 수집하는데 1-2분 소요
- 차단 방지를 위해 의도적으로 딜레이 적용

### 4. 결과가 50개보다 적은 경우
- 검색 키워드에 따라 실제 결과가 적을 수 있음
- 구글/유튜브의 동적 로딩 특성상 일부 누락 가능
- 광고가 자동으로 필터링되어 개수가 줄어들 수 있음

### 5. 패키지 설치 오류
```
ERROR: Could not find a version that satisfies the requirement
```

**해결 방법**:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 6. SQLite 데이터베이스 오류
데이터베이스 파일이 손상된 경우:
```bash
# database.db 파일 삭제 후 재실행
rm database.db  # Windows: del database.db
python app.py
```

## 🛑 종료 방법

터미널에서 `Ctrl + C` 키를 눌러 서버 종료

## 💾 데이터 백업

검색 기록을 백업하려면 `database.db` 파일을 복사하세요:
```bash
cp database.db database_backup.db
```

## 🔧 고급 설정

### 크롤링 개수 변경
`app.py` 파일에서 수정:
```python
results = crawl_all(keyword, google_max=50, youtube_max=50)
# 원하는 개수로 변경 (예: 100)
```

### 헤드리스 모드 끄기 (크롤링 과정 보기)
`crawler.py` 파일에서 수정:
```python
# chrome_options.add_argument('--headless')  # 이 줄을 주석 처리
```

### 크롤링 속도 조절
`crawler.py`의 `random_delay` 함수 호출 부분에서 시간 조절:
```python
self.random_delay(1, 2)  # 최소 1초, 최대 2초
# 더 빠르게: (0.5, 1)
# 더 안전하게: (2, 4)
```

## 📞 지원

문제가 계속되면:
1. Python 버전 확인: `python --version`
2. Chrome 버전 확인: Chrome 설정 → 정보
3. 오류 메시지 전체 복사하여 문의


