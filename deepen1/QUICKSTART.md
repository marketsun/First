# 🚀 빠른 시작 가이드

## 3단계로 시작하기

### 1️⃣ 패키지 설치
```bash
pip install -r requirements.txt
```

### 2️⃣ 서버 실행
```bash
python app.py
```

### 3️⃣ 브라우저 접속
```
http://localhost:5000
```

---

## ✅ 체크리스트

설치 전 확인사항:
- [ ] Python 3.8 이상 설치됨
- [ ] Google Chrome 브라우저 설치됨
- [ ] 인터넷 연결 확인

---

## 💡 첫 검색 해보기

1. 메인 페이지에서 키워드 입력 (예: "맛집")
2. "검색" 버튼 클릭
3. 1-2분 대기
4. 결과 확인!

---

## 🎯 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 동시 검색 | 구글 + 유튜브 한 번에 |
| 📱 모바일 크롤링 | 모바일 검색 결과 수집 |
| 💾 자동 저장 | 모든 결과 자동 저장 |
| 🎯 필터링 | 키워드/날짜/조회수 필터 |
| 🗑️ 기록 관리 | 검색 기록 삭제/수정 |

---

## ⚡ 문제 발생 시

**패키지 설치 오류:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**포트 충돌:**
`app.py` 마지막 줄의 `port=5000`을 `port=5001`로 변경

**자세한 내용은 `INSTALL.md` 참고**

---

## 📁 프로젝트 구조

```
deepen1/
├── app.py              # Flask 서버
├── crawler.py          # 크롤링 로직
├── models.py           # 데이터베이스 모델
├── requirements.txt    # 필요 패키지
├── static/             # CSS, JS
└── templates/          # HTML 템플릿
```

---

## 🎉 준비 완료!

이제 검색을 시작하세요! 🚀


