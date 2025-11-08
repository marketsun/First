# -*- coding: utf-8 -*-
"""
웹 버전 Flask 앱 (포트: 8855)
Electron 버전과 동일한 크롤링 방식
Google News: RSS 파싱
Naver News: Selenium 크롤링
"""

# 앱 버전
APP_VERSION = "1.0.7"

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re
import sys
import os
from urllib.parse import quote
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# 환경변수 로드
load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
application_path = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(application_path, 'database.db')
template_folder = os.path.join(application_path, 'public')
static_folder = os.path.join(application_path, 'static')

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
CORS(app)

# ============================================================================
# 뉴스 본문 크롤링 및 요약 함수
# ============================================================================

def crawl_article_content(url):
    """
    뉴스 기사 본문 크롤링
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 본문 추출 (여러 패턴 시도)
        content = None
        
        # 네이버 뉴스
        if 'naver.com' in url:
            article = soup.find('article', id='dic_area')
            if article:
                content = article.get_text(strip=True, separator=' ')
        
        # 일반 뉴스 사이트 (article 태그)
        if not content:
            article = soup.find('article')
            if article:
                content = article.get_text(strip=True, separator=' ')
        
        # div.article-body, div.news-body 등
        if not content:
            for selector in ['.article-body', '.news-body', '.article_body', '.news_body', '#articleBody']:
                elem = soup.select_one(selector)
                if elem:
                    content = elem.get_text(strip=True, separator=' ')
                    break
        
        # p 태그들 모으기 (최후의 수단)
        if not content:
            paragraphs = soup.find_all('p')
            if len(paragraphs) > 3:
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])
        
        if content and len(content) > 100:
            # 너무 긴 경우 앞부분만
            return content[:2000]
        
        return content or "본문을 가져올 수 없습니다."
    
    except Exception as e:
        print(f"[본문 크롤링 오류] {url}: {str(e)}")
        return "본문을 가져올 수 없습니다."

def summarize_with_ai(content, title=""):
    """
    본문 요약 (무료 버전: 첫 문단 발췌, 130자 제한)
    """
    try:
        # 본문이 너무 짧으면 그대로 반환
        if len(content) < 50:
            return content
        
        # 줄바꿈 기준으로 문단 분리
        paragraphs = content.split('\n\n')
        
        # 첫 번째 문단 추출
        first_paragraph = paragraphs[0].strip()
        
        # 첫 문단이 너무 짧으면 두 번째 문단도 포함
        if len(first_paragraph) < 100 and len(paragraphs) > 1:
            second_paragraph = paragraphs[1].strip()
            if second_paragraph:
                first_paragraph = first_paragraph + ' ' + second_paragraph
        
        # 단일 줄바꿈도 시도 (문단 구분이 없는 경우)
        if len(first_paragraph) < 100:
            lines = content.split('\n')
            first_paragraph = ' '.join(lines[:3]).strip()
        
        # 200자 제한 (공백 포함)
        if len(first_paragraph) > 200:
            # 197자까지 자르고 "..."로 200자 맞춤
            first_paragraph = first_paragraph[:197] + '...'
        
        return first_paragraph
    
    except Exception as e:
        print(f"[요약 오류] {str(e)}")
        return content[:197] + "..."

def send_to_slack(webhook_url, message):
    """
    Slack 웹훅으로 메시지 전송
    """
    try:
        payload = {
            "text": message
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        response.raise_for_status()
        return True
    
    except Exception as e:
        print(f"[Slack 전송 오류] {str(e)}")
        return False

# 시간 파싱 함수
def parse_published_time(time_str):
    """
    published_time 문자열을 실제 datetime 객체로 변환
    예: "1시간 전" -> datetime 객체
    """
    if not time_str or time_str == '시간 정보 없음':
        return None
    
    now = datetime.now()
    time_str = time_str.strip()
    
    try:
        # "N분 전"
        if '분 전' in time_str or '분전' in time_str:
            minutes = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(minutes=minutes)
        
        # "N시간 전"
        elif '시간 전' in time_str or '시간전' in time_str:
            hours = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(hours=hours)
        
        # "N일 전"
        elif '일 전' in time_str or '일전' in time_str:
            days = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(days=days)
        
        # "N주 전"
        elif '주 전' in time_str or '주전' in time_str:
            weeks = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(weeks=weeks)
        
        # "N개월 전"
        elif '개월 전' in time_str or '개월전' in time_str:
            months = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(days=months * 30)
        
        # "N년 전"
        elif '년 전' in time_str or '년전' in time_str:
            years = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(days=years * 365)
        
        # "YYYY. M. D." 형식
        elif re.match(r'\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?', time_str):
            # "2025. 7. 2." -> "2025-07-02"
            date_match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?', time_str)
            if date_match:
                year, month, day = date_match.groups()
                return datetime(int(year), int(month), int(day))
        
        # 파싱 실패 시 현재 시간 반환
        return now
    
    except Exception as e:
        print(f"[파싱 오류] {time_str}: {str(e)}")
        return now

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 뉴스 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            source TEXT,
            published_time TEXT,
            published_date TIMESTAMP,
            keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # published_date 컬럼이 없는 경우 추가 (기존 DB 호환)
    try:
        c.execute('ALTER TABLE news ADD COLUMN published_date TIMESTAMP')
        print("[DB] published_date 컬럼 추가됨")
    except sqlite3.OperationalError:
        pass  # 이미 존재하는 경우
    
    # 저장 목록 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 저장된 뉴스 항목 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            source TEXT,
            published_time TEXT,
            FOREIGN KEY (list_id) REFERENCES saved_lists(id) ON DELETE CASCADE
        )
    ''')
    
    # 클리핑 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS clippings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            keywords TEXT NOT NULL,
            repeat_type TEXT DEFAULT 'daily',
            repeat_days TEXT,
            send_time TEXT DEFAULT '09:00',
            max_articles INTEGER DEFAULT 10,
            include_summary BOOLEAN DEFAULT 1,
            include_links BOOLEAN DEFAULT 1,
            slack_webhook_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # is_active 컬럼이 없는 경우 추가 (기존 DB 호환)
    try:
        c.execute('ALTER TABLE clippings ADD COLUMN is_active BOOLEAN DEFAULT 1')
        print("[DB] clippings.is_active 컬럼 추가됨")
    except sqlite3.OperationalError:
        pass  # 이미 존재하는 경우
    
    conn.commit()
    conn.close()

init_db()

# ============================================================================
# 라우트
# ============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html', version=APP_VERSION)

@app.route('/clipping')
def clipping():
    """클리핑 페이지"""
    return render_template('clipping.html')

@app.route('/clipping-detail')
def clipping_detail():
    """클리핑 상세 페이지"""
    return render_template('clipping-detail.html')

# ============================================================================
# API 엔드포인트
# ============================================================================

@app.route('/api/crawl', methods=['POST'])
def crawl_news():
    """뉴스 크롤링 (Google News RSS + Naver Selenium)"""
    try:
        data = request.json
        keyword = data.get('keyword', '')
        logs = []
        
        def log(msg):
            logs.append(msg)
            print(msg)
        
        log(f"\n{'='*80}")
        log(f"[크롤링 시작] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"[검색어] '{keyword}'")
        log(f"{'='*80}")
        
        # 기존 뉴스 삭제
        conn_clear = sqlite3.connect(DB_PATH)
        c_clear = conn_clear.cursor()
        c_clear.execute('DELETE FROM news')
        conn_clear.commit()
        conn_clear.close()
        
        google_news = []
        naver_news = []
        
        # ================================================================
        # 1. Google Search (requests + BeautifulSoup)
        # ================================================================
        try:
            log(f"\n[Google] HTTP 요청 시작...")
            
            encoded_keyword = quote(keyword)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            saved_count = 0
            
            # 10페이지까지 크롤링
            for page in range(0, 10):
                try:
                    # start 파라미터: 0, 10, 20, 30, ...
                    start = page * 10
                    google_url = f"https://www.google.com/search?q={encoded_keyword}&tbm=nws&hl=ko&gl=KR&start={start}"
                    
                    log(f"[Google] {page + 1}페이지 요청: start={start}")
                    response = requests.get(google_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    log(f"[Google] {page + 1}페이지 응답: 200 OK ({len(response.content)} bytes)")
                    
                    # BeautifulSoup 파싱
                    soup = BeautifulSoup(response.content, 'html.parser')
                    articles = soup.find_all('div', class_='SoaBEf')
                    
                    log(f"[Google] {page + 1}페이지 발견: {len(articles)}개 항목")
                    
                    if len(articles) == 0:
                        log(f"[Google] {page + 1}페이지에 기사 없음, 중단")
                        break
                    
                    page_saved = 0
                    for article in articles:
                        try:
                            # 제목 찾기 (div[role="heading"])
                            title_elem = article.find('div', {'role': 'heading'})
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            if not title or len(title) < 5:
                                continue
                            
                            # 키워드 필터
                            if keyword.lower() not in title.lower():
                                continue
                            
                            # 링크 찾기 (a href)
                            link_elem = article.find('a', href=True)
                            if not link_elem:
                                continue
                            
                            link = link_elem.get('href', '')
                            if not link or not link.startswith('http'):
                                continue
                            
                            # 출처 찾기 (span 첫 번째)
                            source = '구글뉴스'
                            spans = article.find_all('span')
                            if spans and len(spans) > 0:
                                source_text = spans[0].get_text(strip=True)
                                if source_text:
                                    source = source_text
                            
                            # 시간 찾기 (span 세 번째, 마지막)
                            published_time = '시간 정보 없음'
                            if spans and len(spans) >= 3:
                                time_text = spans[-1].get_text(strip=True)
                                if time_text:
                                    published_time = time_text
                            
                            # 시간 파싱
                            published_date = parse_published_time(published_time)
                            
                            # 저장
                            c.execute('''
                                INSERT INTO news (title, link, source, published_time, published_date, keyword)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (title, link, source, published_time, published_date, keyword))
                            saved_count += 1
                            page_saved += 1
                            
                            if saved_count <= 3:
                                log(f"[Google] ✓ {saved_count}: {title[:40]}...")
                            
                        except sqlite3.IntegrityError:
                            pass
                        except Exception as e:
                            continue
                    
                    log(f"[Google] {page + 1}페이지에서 {page_saved}개 저장")
                    
                    # 페이지 간 딜레이 (봇 감지 방지)
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    log(f"[Google] {page + 1}페이지 오류: {str(e)[:50]}")
                    continue
            
            conn.commit()
            conn.close()
            
            log(f"[Google] 완료: 총 {saved_count}개 저장")
            
        except Exception as e:
            log(f"[Google] 오류: {str(e)}")
        
        # ================================================================
        # 2. Naver News (Selenium)
        # ================================================================
        try:
            log(f"\n[Naver] Selenium 크롤링 시작...")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 브라우저 창 숨김
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            try:
                saved_count = 0
                
                for page in range(1, 6):  # 1, 2, 3, 4, 5 페이지
                    retry_count = 0
                    max_retries = 2
                    success = False
                    
                    while retry_count < max_retries and not success:
                        try:
                            search_url = f"https://search.naver.com/search.naver?where=news&ssc=tab.news.all&query={quote(keyword)}&start={(page-1)*10+1}"
                            log(f"[Naver] {page}페이지 시도 (재시도: {retry_count})")
                            
                            driver.get(search_url)
                            
                            # WebDriverWait로 동적 콘텐츠 로드 대기
                            wait = WebDriverWait(driver, 10)
                            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-heatmap-target=".tit"]')))
                            
                            # 추가 대기
                            import time
                            time.sleep(5)
                            
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            news_items = soup.select('a[data-heatmap-target=".tit"]')
                            
                            log(f"[Naver] {page}페이지: {len(news_items)}개 발견")
                            
                            if len(news_items) > 0:
                                success = True
                            
                            for news_item in news_items:
                                try:
                                    # 제목
                                    title = news_item.get_text(strip=True)
                                    if not title or len(title) < 5:
                                        continue
                                    
                                    # 링크
                                    link = news_item.get('href', '')
                                    if not link or not link.startswith('http'):
                                        continue
                                    
                                    # 출처 (Naver는 항상 "네이버뉴스"로 통일)
                                    source = '네이버뉴스'
                                    parent = news_item
                                    source_found = False
                                    for _ in range(10):
                                        parent = parent.parent
                                        if parent is None:
                                            break
                                        source_span = parent.select_one('span.sds-comps-profile-info-title-text')
                                        if source_span:
                                            source_text = source_span.get_text(strip=True)
                                            if source_text:
                                                source = f"네이버뉴스 ({source_text})"
                                                source_found = True
                                            break
                                    # source_found가 False면 기본값 '네이버뉴스' 유지
                                    
                                    # 시간
                                    published_time = '시간 정보 없음'
                                    parent = news_item
                                    for _ in range(10):
                                        parent = parent.parent
                                        if parent is None:
                                            break
                                        time_elem = parent.select_one('.sds-comps-profile-info-subtext')
                                        if time_elem:
                                            published_time = time_elem.get_text(strip=True)
                                            break
                                    
                                    # 시간 파싱
                                    published_date = parse_published_time(published_time)
                                    
                                    # 저장
                                    c.execute('''
                                        INSERT INTO news (title, link, source, published_time, published_date, keyword)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    ''', (title, link, source, published_time, published_date, keyword))
                                    saved_count += 1
                                    
                                    if saved_count <= 3:
                                        log(f"[Naver] ✓ {saved_count}: {title[:40]}...")
                                    
                                except sqlite3.IntegrityError:
                                    pass
                                except Exception as e:
                                    continue
                        
                        except Exception as e:
                            log(f"[Naver] {page}페이지 오류 ({retry_count+1}/{max_retries}): {str(e)[:50]}")
                            retry_count += 1
                            if retry_count < max_retries:
                                import time
                                time.sleep(2)
                
                conn.commit()
                log(f"[Naver] 완료: {saved_count}개 저장")
                
            finally:
                driver.quit()
                conn.close()
            
        except Exception as e:
            log(f"[Naver] 크롤링 오류: {str(e)}")
        
        # 뉴스 반환 (published_date 기준 최신순 정렬)
        conn_read = sqlite3.connect(DB_PATH)
        c_read = conn_read.cursor()
        c_read.execute('''
            SELECT id, title, link, source, published_time, created_at, published_date 
            FROM news 
            ORDER BY published_date DESC, created_at DESC
        ''')
        rows = c_read.fetchall()
        conn_read.close()
        
        # Google과 Naver 분리
        google_news = []
        naver_news = []
        
        for row in rows:
            news_item = {
                'id': row[0], 
                'title': row[1], 
                'link': row[2], 
                'source': row[3], 
                'published_time': row[4], 
                'created_at': row[5],
                'published_date': row[6]
            }
            
            # source에 "네이버" 또는 "naver" 포함되면 naver_news에
            if '네이버' in row[3].lower() or 'naver' in row[3].lower():
                naver_news.append(news_item)
            else:
                # 그 외 모두 google_news에
                google_news.append(news_item)
        
        log(f"\n[완료] Google {len(google_news)}개, Naver {len(naver_news)}개 뉴스")
        log(f"{'='*80}\n")
        
        return jsonify({'success': True, 'google_news': google_news, 'naver_news': naver_news, 'logs': logs})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'logs': logs if 'logs' in locals() else []}), 500

# 저장된 목록 API
@app.route('/api/saved-lists', methods=['GET'])
def get_saved_lists():
    """저장된 목록 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, created_at FROM saved_lists ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()
        
        lists = [{'id': row[0], 'name': row[1], 'created_at': row[2]} for row in rows]
        return jsonify({'success': True, 'lists': lists})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists', methods=['POST'])
def create_saved_list():
    """저장된 목록 생성"""
    try:
        data = request.json
        name = data.get('name', '')
        
        if not name:
            return jsonify({'success': False, 'error': '목록 이름이 필요합니다'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO saved_lists (name) VALUES (?)', (name,))
        conn.commit()
        
        list_id = c.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': list_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists/<int:list_id>', methods=['GET'])
def get_saved_list_details(list_id):
    """저장된 목록 상세 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 목록 정보
        c.execute('SELECT id, name, created_at FROM saved_lists WHERE id = ?', (list_id,))
        list_row = c.fetchone()
        
        if not list_row:
            conn.close()
            return jsonify({'success': False, 'error': '목록을 찾을 수 없습니다'}), 404
        
        # 항목들
        c.execute('SELECT id, title, link, source, published_time FROM saved_list_items WHERE list_id = ?', (list_id,))
        items = c.fetchall()
        conn.close()
        
        items_list = [{'id': item[0], 'title': item[1], 'link': item[2], 'source': item[3], 'published_time': item[4]} for item in items]
        
        return jsonify({
            'success': True,
            'list': {
                'id': list_row[0],
                'name': list_row[1],
                'created_at': list_row[2],
                'items': items_list
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists/<int:list_id>', methods=['DELETE'])
def delete_saved_list(list_id):
    """저장된 목록 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM saved_lists WHERE id = ?', (list_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists/all', methods=['DELETE'])
def delete_all_saved_lists():
    """모든 저장된 목록 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM saved_list_items')
        c.execute('DELETE FROM saved_lists')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists/<int:list_id>/items', methods=['POST'])
def add_to_saved_list(list_id):
    """저장된 목록에 항목 추가"""
    try:
        data = request.json
        title = data.get('title', '')
        link = data.get('link', '')
        source = data.get('source', '')
        published_time = data.get('published_time', '')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO saved_list_items (list_id, title, link, source, published_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (list_id, title, link, source, published_time))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-lists/<int:list_id>/items/<int:item_id>', methods=['DELETE'])
def delete_from_saved_list(list_id, item_id):
    """저장된 목록에서 항목 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM saved_list_items WHERE id = ? AND list_id = ?', (item_id, list_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# 클리핑 API
# ============================================================================

@app.route('/api/clipping/list', methods=['GET'])
def get_clipping_list():
    """클리핑 목록 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT id, name, keywords, repeat_type, send_time, is_active, created_at 
            FROM clippings 
            ORDER BY created_at DESC
        ''')
        rows = c.fetchall()
        conn.close()
        
        clippings = []
        for row in rows:
            keywords_list = row[2].split(',') if row[2] else []
            clippings.append({
                'id': row[0],
                'name': row[1],
                'keywords': keywords_list,
                'repeat_type': row[3],
                'send_time': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6]
            })
        
        return jsonify({'success': True, 'data': clippings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/create', methods=['POST'])
def create_clipping():
    """클리핑 생성"""
    try:
        data = request.json
        name = data.get('name', '')
        keywords = data.get('keywords', [])
        repeat_type = data.get('repeat_type', 'daily')
        repeat_days = data.get('repeat_days', [])
        send_time = data.get('send_time', '09:00')
        max_articles = data.get('max_articles', 10)
        include_summary = data.get('include_summary', True)
        include_links = data.get('include_links', True)
        slack_webhook_url = data.get('slack_webhook_url', '')
        
        # keywords를 문자열로 변환
        keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
        repeat_days_str = ','.join(map(str, repeat_days)) if isinstance(repeat_days, list) else ''
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO clippings (
                name, keywords, repeat_type, repeat_days, send_time, 
                max_articles, include_summary, include_links, slack_webhook_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, keywords_str, repeat_type, repeat_days_str, send_time, 
              max_articles, include_summary, include_links, slack_webhook_url))
        
        clipping_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': clipping_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/<int:clipping_id>', methods=['GET'])
def get_clipping_detail(clipping_id):
    """클리핑 상세 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT id, name, keywords, repeat_type, repeat_days, send_time, 
                   max_articles, include_summary, include_links, slack_webhook_url, 
                   is_active, created_at
            FROM clippings 
            WHERE id = ?
        ''', (clipping_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': '클리핑을 찾을 수 없습니다'}), 404
        
        keywords_list = row[2].split(',') if row[2] else []
        repeat_days_list = [int(d) for d in row[4].split(',') if d] if row[4] else []
        
        clipping = {
            'id': row[0],
            'name': row[1],
            'keywords': keywords_list,
            'repeat_type': row[3],
            'repeat_days': repeat_days_list,
            'send_time': row[5],
            'max_articles': row[6],
            'include_summary': bool(row[7]),
            'include_links': bool(row[8]),
            'slack_webhook_url': row[9],
            'is_active': bool(row[10]),
            'created_at': row[11]
        }
        
        return jsonify({'success': True, 'data': clipping})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/<int:clipping_id>', methods=['PUT'])
def update_clipping(clipping_id):
    """클리핑 수정"""
    try:
        data = request.json
        name = data.get('name', '')
        keywords = data.get('keywords', [])
        repeat_type = data.get('repeat_type', 'daily')
        repeat_days = data.get('repeat_days', [])
        send_time = data.get('send_time', '09:00')
        max_articles = data.get('max_articles', 10)
        include_summary = data.get('include_summary', True)
        include_links = data.get('include_links', True)
        slack_webhook_url = data.get('slack_webhook_url', '')
        
        # keywords를 문자열로 변환
        keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
        repeat_days_str = ','.join(map(str, repeat_days)) if isinstance(repeat_days, list) else ''
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            UPDATE clippings 
            SET name = ?, keywords = ?, repeat_type = ?, repeat_days = ?, 
                send_time = ?, max_articles = ?, include_summary = ?, 
                include_links = ?, slack_webhook_url = ?
            WHERE id = ?
        ''', (name, keywords_str, repeat_type, repeat_days_str, send_time, 
              max_articles, include_summary, include_links, slack_webhook_url, clipping_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/<int:clipping_id>', methods=['DELETE'])
def delete_clipping(clipping_id):
    """클리핑 삭제"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM clippings WHERE id = ?', (clipping_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/<int:clipping_id>/toggle', methods=['PATCH'])
def toggle_clipping_active(clipping_id):
    """클리핑 활성화/비활성화 토글"""
    try:
        data = request.json
        is_active = data.get('is_active', True)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE clippings SET is_active = ? WHERE id = ?', (is_active, clipping_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clipping/<int:clipping_id>/send', methods=['POST'])
def send_clipping(clipping_id):
    """클리핑 실행 및 Slack 전송"""
    try:
        # 클리핑 정보 조회
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT name, keywords, max_articles, include_summary, include_links, slack_webhook_url
            FROM clippings 
            WHERE id = ?
        ''', (clipping_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': '클리핑을 찾을 수 없습니다'}), 404
        
        name = row[0]
        keywords_str = row[1]
        max_articles = row[2]
        include_summary = row[3]
        include_links = row[4]
        webhook_url = row[5]
        
        if not webhook_url:
            return jsonify({'success': False, 'error': 'Slack 웹훅 URL이 설정되지 않았습니다'}), 400
        
        keywords = keywords_str.split(',') if keywords_str else []
        
        print(f"[클리핑 전송] 키워드: {keywords}")
        print(f"[클리핑 전송] 최대 기사 수: {max_articles}")
        
        # 각 키워드로 뉴스 크롤링 (메인 크롤링과 동일한 방식 사용)
        all_news = []
        
        # Selenium 사용
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                for keyword in keywords:
                    keyword = keyword.strip()
                    print(f"[크롤링] '{keyword}' 검색 중...")
                    
                    # 구글 뉴스 크롤링
                    try:
                        encoded_keyword = quote(keyword)
                        google_url = f"https://www.google.com/search?q={encoded_keyword}&tbm=nws&hl=ko&gl=KR"
                        
                        print(f"[Google] '{keyword}' 검색 시작")
                        driver.get(google_url)
                        
                        # 페이지 로딩 대기
                        import time
                        time.sleep(2)
                        
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        articles = soup.find_all('div', class_='SoaBEf')
                        print(f"[Google] '{keyword}' 검색 결과: {len(articles)}개 발견")
                        
                        for article in articles[:10]:
                            try:
                                title_elem = article.find('div', {'role': 'heading'})
                                if not title_elem:
                                    continue
                                
                                title = title_elem.get_text(strip=True)
                                if not title or len(title) < 5:
                                    continue
                                
                                link_elem = article.find('a', href=True)
                                if not link_elem:
                                    continue
                                
                                link = link_elem.get('href', '')
                                if not link or not link.startswith('http'):
                                    continue
                                
                                all_news.append({
                                    'title': title,
                                    'link': link,
                                    'keyword': keyword,
                                    'source': 'Google'
                                })
                                
                                # 키워드당 구글 3개
                                if len([n for n in all_news if n['keyword'] == keyword and n['source'] == 'Google']) >= 3:
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"[Google] '{keyword}' 검색 오류: {str(e)}")
                    
                    # 네이버 뉴스 크롤링
                    try:
                        naver_url = f"https://search.naver.com/search.naver?where=news&ssc=tab.news.all&query={quote(keyword)}"
                        
                        print(f"[Naver] '{keyword}' 검색 시작")
                        driver.get(naver_url)
                        
                        # 페이지 로딩 대기
                        time.sleep(3)
                        
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        news_items = soup.select('a[data-heatmap-target=".tit"]')
                        print(f"[Naver] '{keyword}' 검색 결과: {len(news_items)}개 발견")
                        
                        for news_item in news_items[:10]:
                            try:
                                title = news_item.get_text(strip=True)
                                if not title or len(title) < 5:
                                    continue
                                
                                link = news_item.get('href', '')
                                if not link or not link.startswith('http'):
                                    continue
                                
                                all_news.append({
                                    'title': title,
                                    'link': link,
                                    'keyword': keyword,
                                    'source': 'Naver'
                                })
                                
                                # 키워드당 네이버 3개
                                if len([n for n in all_news if n['keyword'] == keyword and n['source'] == 'Naver']) >= 3:
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"[Naver] '{keyword}' 검색 오류: {str(e)}")
            finally:
                driver.quit()
        except Exception as e:
            print(f"[크롤링] Selenium 초기화 오류: {str(e)}")
            return jsonify({'success': False, 'error': f'크롤링 초기화 실패: {str(e)}'}), 500
        
        print(f"[크롤링] 총 {len(all_news)}개 뉴스 수집")
        
        # 최대 개수만큼만
        all_news = all_news[:max_articles]
        
        if len(all_news) == 0:
            print("[오류] 뉴스를 찾을 수 없습니다")
            return jsonify({'success': False, 'error': '뉴스를 찾을 수 없습니다. 키워드를 확인해주세요.'}), 404
        
        # Slack 메시지 생성
        today = datetime.now()
        month = today.month
        day = today.day
        keywords_display = ', '.join([k.strip() for k in keywords])
        
        message = f"■ {month}월 {day}일 \"{keywords_display}\" 뉴스클리핑\n\n"
        
        for idx, news in enumerate(all_news, 1):
            message += f"{idx}. {news['title']}\n\n"
            
            # 요약 포함
            if include_summary:
                print(f"[{idx}/{len(all_news)}] 본문 크롤링 중: {news['title'][:30]}...")
                content = crawl_article_content(news['link'])
                
                print(f"[{idx}/{len(all_news)}] 요약 생성 중...")
                summary = summarize_with_ai(content, news['title'])
                message += f"{summary}\n"
            
            # 링크 포함
            if include_links:
                message += f"{news['link']}\n"
            
            message += "\n"
        
        # Slack 전송
        print(f"[Slack] 전송 중... (총 {len(all_news)}개 뉴스)")
        success = send_to_slack(webhook_url, message)
        
        if success:
            return jsonify({'success': True, 'message': f'{len(all_news)}개 뉴스 전송 완료'})
        else:
            return jsonify({'success': False, 'error': 'Slack 전송 실패'}), 500
    
    except Exception as e:
        print(f"[클리핑 전송 오류] {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# 자동 전송 스케줄러
# ============================================================================

def check_clipping_schedule():
    """
    매 분마다 실행되어 전송할 클리핑 확인 및 자동 전송
    """
    try:
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_day = now.weekday()  # 0=월요일, 6=일요일
        
        print(f"[스케줄러] 체크 시작 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 활성화된 클리핑 조회
        cursor.execute('''
            SELECT id, name, send_time, repeat_type, repeat_days 
            FROM clippings 
            WHERE is_active = 1
        ''')
        
        clippings = cursor.fetchall()
        print(f"[스케줄러] 활성화된 클리핑: {len(clippings)}개")
        
        for row in clippings:
            clipping_id, name, send_time, repeat_type, repeat_days = row
            
            # 시간 일치 확인
            if send_time == current_time:
                print(f"[스케줄러] 시간 일치 - 클리핑 '{name}' (ID: {clipping_id})")
                
                # 반복 타입 확인
                should_send = False
                
                if repeat_type == 'daily':
                    should_send = True
                    print(f"[스케줄러] 반복 타입: 매일 → 전송")
                elif repeat_type == 'weekly' and repeat_days:
                    days = [int(d) for d in repeat_days.split(',') if d]
                    if current_day in days:
                        should_send = True
                        print(f"[스케줄러] 반복 타입: 주간 (요일: {days}) → 전송")
                    else:
                        print(f"[스케줄러] 반복 타입: 주간 (요일: {days}) → 오늘은 전송 안 함")
                
                if should_send:
                    print(f"[자동전송 시작] 클리핑 '{name}' (ID: {clipping_id})")
                    try:
                        # 전송 로직 실행 (내부 함수 호출)
                        send_clipping_internal(clipping_id)
                        print(f"[자동전송 완료] 클리핑 '{name}' (ID: {clipping_id})")
                    except Exception as e:
                        print(f"[자동전송 오류] 클리핑 '{name}' (ID: {clipping_id}): {str(e)}")
        
        conn.close()
        
    except Exception as e:
        print(f"[스케줄러 오류] {str(e)}")

def send_clipping_internal(clipping_id):
    """
    클리핑 전송 내부 함수 (스케줄러용)
    기존 API와 동일한 로직 사용
    """
    try:
        # 클리핑 정보 조회
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT name, keywords, max_articles, include_summary, include_links, slack_webhook_url
            FROM clippings 
            WHERE id = ?
        ''', (clipping_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise Exception('클리핑을 찾을 수 없습니다')
        
        name = row[0]
        keywords_str = row[1]
        max_articles = row[2]
        include_summary = row[3]
        include_links = row[4]
        webhook_url = row[5]
        
        if not webhook_url:
            raise Exception('Slack 웹훅 URL이 설정되지 않았습니다')
        
        keywords = keywords_str.split(',') if keywords_str else []
        
        print(f"[클리핑 전송] 키워드: {keywords}")
        print(f"[클리핑 전송] 최대 기사 수: {max_articles}")
        
        # 각 키워드로 뉴스 크롤링 (메인 크롤링과 동일한 방식 사용)
        all_news = []
        
        # Selenium 사용
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                for keyword in keywords:
                    keyword = keyword.strip()
                    print(f"[크롤링] '{keyword}' 검색 중...")
                    
                    # 구글 뉴스 크롤링
                    try:
                        encoded_keyword = quote(keyword)
                        google_url = f"https://www.google.com/search?q={encoded_keyword}&tbm=nws&hl=ko&gl=KR"
                        
                        print(f"[Google] '{keyword}' 검색 시작")
                        driver.get(google_url)
                        
                        # 페이지 로딩 대기
                        import time
                        time.sleep(2)
                        
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        articles = soup.find_all('div', class_='SoaBEf')
                        print(f"[Google] '{keyword}' 검색 결과: {len(articles)}개 발견")
                        
                        for article in articles[:10]:
                            try:
                                title_elem = article.find('div', {'role': 'heading'})
                                if not title_elem:
                                    continue
                                
                                title = title_elem.get_text(strip=True)
                                if not title or len(title) < 5:
                                    continue
                                
                                link_elem = article.find('a', href=True)
                                if not link_elem:
                                    continue
                                
                                link = link_elem.get('href', '')
                                if not link or not link.startswith('http'):
                                    continue
                                
                                all_news.append({
                                    'title': title,
                                    'link': link,
                                    'keyword': keyword,
                                    'source': 'Google'
                                })
                                
                                # 키워드당 구글 3개
                                if len([n for n in all_news if n['keyword'] == keyword and n['source'] == 'Google']) >= 3:
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"[Google] '{keyword}' 검색 오류: {str(e)}")
                    
                    # 네이버 뉴스 크롤링
                    try:
                        naver_url = f"https://search.naver.com/search.naver?where=news&ssc=tab.news.all&query={quote(keyword)}"
                        
                        print(f"[Naver] '{keyword}' 검색 시작")
                        driver.get(naver_url)
                        
                        # 페이지 로딩 대기
                        time.sleep(3)
                        
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        news_items = soup.select('a[data-heatmap-target=".tit"]')
                        print(f"[Naver] '{keyword}' 검색 결과: {len(news_items)}개 발견")
                        
                        for news_item in news_items[:10]:
                            try:
                                title = news_item.get_text(strip=True)
                                if not title or len(title) < 5:
                                    continue
                                
                                link = news_item.get('href', '')
                                if not link or not link.startswith('http'):
                                    continue
                                
                                all_news.append({
                                    'title': title,
                                    'link': link,
                                    'keyword': keyword,
                                    'source': 'Naver'
                                })
                                
                                # 키워드당 네이버 3개
                                if len([n for n in all_news if n['keyword'] == keyword and n['source'] == 'Naver']) >= 3:
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"[Naver] '{keyword}' 검색 오류: {str(e)}")
            finally:
                driver.quit()
        except Exception as e:
            print(f"[크롤링] Selenium 초기화 오류: {str(e)}")
            raise Exception(f'크롤링 초기화 실패: {str(e)}')
        
        print(f"[크롤링] 총 {len(all_news)}개 뉴스 수집")
        
        # 최대 개수만큼만
        all_news = all_news[:max_articles]
        
        if len(all_news) == 0:
            print("[오류] 뉴스를 찾을 수 없습니다")
            raise Exception('뉴스를 찾을 수 없습니다. 키워드를 확인해주세요.')
        
        # Slack 메시지 생성
        today = datetime.now()
        month = today.month
        day = today.day
        keywords_display = ', '.join([k.strip() for k in keywords])
        
        message = f"■ {month}월 {day}일 \"{keywords_display}\" 뉴스클리핑\n\n"
        
        for idx, news in enumerate(all_news, 1):
            message += f"{idx}. {news['title']}\n\n"
            
            # 요약 포함
            if include_summary:
                print(f"[{idx}/{len(all_news)}] 본문 크롤링 중: {news['title'][:30]}...")
                content = crawl_article_content(news['link'])
                
                print(f"[{idx}/{len(all_news)}] 요약 생성 중...")
                summary = summarize_with_ai(content, news['title'])
                message += f"{summary}\n"
            
            # 링크 포함
            if include_links:
                message += f"{news['link']}\n"
            
            message += "\n"
        
        # Slack 전송
        print(f"[Slack] 전송 중... (총 {len(all_news)}개 뉴스)")
        success = send_to_slack(webhook_url, message)
        
        if success:
            print(f"[자동전송 완료] 클리핑 '{name}' - {len(all_news)}개 뉴스 전송 완료")
        else:
            raise Exception('Slack 전송 실패')
            
    except Exception as e:
        print(f"[자동전송 오류] {str(e)}")
        raise

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_clipping_schedule,
    trigger='cron',
    minute='*',  # 매 분마다 실행
    id='clipping_scheduler',
    replace_existing=True
)

# ============================================================================
# 서버 시작
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("구글&네이버 뉴스 크롤러 - 웹 버전")
    print("포트: http://localhost:8855")
    print("="*80 + "\n")
    
    # 스케줄러 시작
    scheduler.start()
    print("[스케줄러] 자동 전송 스케줄러 시작됨")
    
    # 앱 종료 시 스케줄러 종료
    atexit.register(lambda: scheduler.shutdown())
    
    app.run(host='0.0.0.0', port=8855, debug=False)
