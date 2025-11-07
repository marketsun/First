# -*- coding: utf-8 -*-
"""
웹 버전 Flask 앱 (포트: 8855)
Electron 버전과 동일한 크롤링 방식
Google News: RSS 파싱
Naver News: Selenium 크롤링
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
import sys
import os
from urllib.parse import quote
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
application_path = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(application_path, 'database.db')
template_folder = os.path.join(application_path, 'public')
static_folder = os.path.join(application_path, 'static')

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
CORS(app)

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
            keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    conn.commit()
    conn.close()

init_db()

# ============================================================================
# 라우트
# ============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

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
        # 1. Google News (RSS 파싱)
        # ================================================================
        try:
            log(f"\n[Google] RSS 파싱 시작...")
            
            encoded_keyword = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            log(f"[Google] RSS 응답: 200 OK ({len(response.content)} bytes)")
            
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            log(f"[Google] 발견: {len(items)}개 항목")
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            saved_count = 0
            filtered_count = 0
            
            for item in items:
                try:
                    # 제목
                    title_elem = item.find('title')
                    if title_elem is None or title_elem.text is None:
                        continue
                    
                    title = title_elem.text.strip()
                    if not title or len(title) < 5:
                        continue
                    
                    # 키워드 필터
                    if keyword.lower() not in title.lower():
                        filtered_count += 1
                        continue
                    
                    # 링크
                    link_elem = item.find('link')
                    if link_elem is None or link_elem.text is None:
                        continue
                    link = link_elem.text.strip()
                    if not link:
                        continue
                    
                    # 출처
                    source = '구글뉴스'
                    description_elem = item.find('description')
                    if description_elem is not None and description_elem.text:
                        desc = description_elem.text
                        font_match = re.search(r'<font[^>]*>([^<]+)</font>', desc)
                        if font_match:
                            source = font_match.group(1).strip()
                    
                    # 시간
                    published_time = '시간 정보 없음'
                    if description_elem is not None and description_elem.text:
                        desc = description_elem.text
                        time_match = re.search(r'(\d+\s*(?:초|분|시간|일|주|개월|년)\s*전)', desc)
                        if time_match:
                            published_time = time_match.group(1)
                    
                    # 저장
                    c.execute('''
                        INSERT INTO news (title, link, source, published_time, keyword)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (title, link, source, published_time, keyword))
                    saved_count += 1
                    
                    if saved_count <= 3:
                        log(f"[Google] ✓ {saved_count}: {title[:40]}...")
                    
                except sqlite3.IntegrityError:
                    pass
                except Exception as e:
                    continue
            
            conn.commit()
            conn.close()
            
            log(f"[Google] 완료: {saved_count}개 저장, {filtered_count}개 필터")
            
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
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            try:
                saved_count = 0
                
                for page in range(1, 4):
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
                                    
                                    # 출처
                                    source = '네이버뉴스'
                                    parent = news_item
                                    for _ in range(10):
                                        parent = parent.parent
                                        if parent is None:
                                            break
                                        source_span = parent.select_one('span.sds-comps-profile-info-title-text')
                                        if source_span:
                                            source = source_span.get_text(strip=True)
                                            break
                                    
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
                                    
                                    # 저장
                                    c.execute('''
                                        INSERT INTO news (title, link, source, published_time, keyword)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (title, link, source, published_time, keyword))
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
        
        # 뉴스 반환
        conn_read = sqlite3.connect(DB_PATH)
        c_read = conn_read.cursor()
        c_read.execute('SELECT id, title, link, source, published_time FROM news ORDER BY created_at DESC')
        rows = c_read.fetchall()
        conn_read.close()
        
        # Google과 Naver 분리
        google_news = []
        naver_news = []
        
        for row in rows:
            news_item = {'id': row[0], 'title': row[1], 'link': row[2], 'source': row[3], 'published_time': row[4]}
            
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
# 서버 시작
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("구글&네이버 뉴스 크롤러 - 웹 버전")
    print("포트: http://localhost:8855")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=8855, debug=False)
