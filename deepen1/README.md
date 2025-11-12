# 구글/유튜브 모바일 검색 크롤러

브랜드 키워드를 검색하고 구글과 유튜브의 모바일 검색 결과를 크롤링하여 분석하는 웹 애플리케이션입니다.

## 주요 기능

- 🔍 구글 및 유튜브 동시 검색 (모바일 버전)
- 📊 검색 결과 크롤링 (각 50개)
  - **구글**: 제목, URL, 설명, 썸네일
  - **유튜브**: 제목, URL, 조회수, 업로드 날짜, 썸네일, 채널명, 좋아요 수
- 💾 검색 기록 저장 및 관리
- 🎯 광고 및 무관 링크 자동 필터링
- 🔎 키워드, 기간, 조회수 기준 필터링 및 정렬

## 설치 방법

### 1. Python 설치
Python 3.8 이상이 필요합니다.

### 2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. Chrome 브라우저 설치
Selenium이 Chrome을 사용하므로 Chrome 브라우저가 설치되어 있어야 합니다.

## 실행 방법

### 가장 쉬운 방법 (추천!)
**Windows:** `start.bat` 파일 더블클릭
**Mac/Linux:** 터미널에서 `./start.sh` 실행

### 수동 실행
```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

**자세한 내용:** `서버실행방법.md` 참고

## 프로젝트 구조

```
deepen1/
├── app.py                 # Flask 메인 애플리케이션
├── models.py              # 데이터베이스 모델
├── crawler.py             # 크롤링 로직
├── requirements.txt       # 의존성 패키지
├── database.db           # SQLite 데이터베이스 (자동 생성)
├── static/               # 정적 파일 (CSS, JS)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/            # HTML 템플릿
    ├── index.html        # 메인 페이지
    ├── results.html      # 검색 결과 페이지
    └── history.html      # 검색 기록 페이지
```

## 기술 스택

- **백엔드**: Python, Flask
- **크롤링**: Selenium, BeautifulSoup4
- **데이터베이스**: SQLite
- **프론트엔드**: HTML, CSS, JavaScript

## 주의사항

- 과도한 크롤링은 IP 차단의 원인이 될 수 있습니다.
- 검색 결과 수집에 시간이 소요될 수 있습니다 (50개당 1-2분).
- 로컬 환경에서만 사용 가능합니다.

