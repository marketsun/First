from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from dateutil import parser


class MobileCrawler:
    """모바일 환경 크롤링을 위한 기본 클래스"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """모바일 User-Agent로 Chrome 드라이버 설정"""
        chrome_options = Options()
        
        # User-Agent 설정 (안드로이드 모바일)
        user_agent = "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        # 기타 옵션
        chrome_options.add_argument('--headless=new')  # 헤드리스 모드
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 봇 감지 우회
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # 화면 크기 설정 (안드로이드 모바일)
        chrome_options.add_argument('--window-size=412,915')  # Galaxy S22 Ultra 크기
        
        # 모바일 에뮬레이션 설정
        mobile_emulation = {
            "deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 3.0},
            "userAgent": user_agent
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            
    def random_delay(self, min_sec=1, max_sec=3):
        """랜덤 딜레이 (차단 방지)"""
        import random
        time.sleep(random.uniform(min_sec, max_sec))


class GoogleMobileCrawler(MobileCrawler):
    """구글 모바일 검색 크롤러"""
    
    # 광고 및 필터링할 도메인 패턴
    AD_PATTERNS = [
        r'googleadservices\.com',
        r'/aclk\?',
        r'sponsored',
    ]
    
    def crawl(self, keyword, max_results=50):
        """
        구글 모바일 검색 결과 크롤링
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수
            
        Returns:
            list: 검색 결과 딕셔너리 리스트
        """
        results = []
        
        try:
            self.setup_driver()
            
            # 구글 검색 (모바일 버전)
            search_url = f"https://www.google.com/search?q={keyword}&hl=ko&num=50"
            self.driver.get(search_url)
            
            # 페이지 로딩 대기 증가
            self.random_delay(3, 5)
            
            # 명시적 대기
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            position = 1
            scroll_count = 0
            max_scrolls = 10  # 최대 스크롤 횟수
            
            while len(results) < max_results and scroll_count < max_scrolls:
                # 페이지 소스 파싱
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 검색 결과 추출 (데스크톱 버전)
                # 모든 링크를 검사
                all_links = soup.find_all('a', href=True)
                
                processed_urls = set()
                
                for link in all_links:
                    if len(results) >= max_results:
                        break
                    
                    try:
                        url = link.get('href', '')
                        
                        # URL 정제
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        # 유효한 URL인지 확인
                        if not url.startswith('http'):
                            continue
                        
                        # 이미 처리한 URL인지 확인
                        if url in processed_urls:
                            continue
                        
                        # 광고 필터링
                        if self._is_ad(url, link):
                            continue
                        
                        # 구글 자체 링크 제외
                        if 'google.com' in url or 'youtube.com' in url:
                            continue
                        
                        # 제목 추출
                        title_elem = link.find(['h3', 'div'])
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        if not title:
                            continue
                        
                        # 스니펫 추출 (부모 요소에서)
                        snippet = ''
                        parent = link.find_parent(['div', 'article'])
                        if parent:
                            snippet_elem = parent.find(['div', 'span'], class_=re.compile(r'(VwiC3b|yXK7lf|MUxGbd)'))
                            if snippet_elem:
                                snippet = snippet_elem.get_text(strip=True)
                        
                        # 썸네일 추출
                        thumbnail = ''
                        img_elem = link.find('img')
                        if img_elem:
                            thumbnail = img_elem.get('src', '') or img_elem.get('data-src', '')
                        
                        processed_urls.add(url)
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'thumbnail': thumbnail,
                            'position': position,
                            'published_date': '',
                            'is_ad': False
                        })
                        
                        position += 1
                        
                    except Exception as e:
                        continue
                
                # 스크롤하여 더 많은 결과 로드
                if len(results) < max_results:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.random_delay(2, 3)
                    scroll_count += 1
                else:
                    break
            
            print(f"구글 크롤링 완료: {len(results)}개 결과")
            
        except Exception as e:
            print(f"구글 크롤링 오류: {e}")
        finally:
            self.close_driver()
        
        return results
    
    def _is_ad(self, url, element):
        """광고 여부 확인"""
        for pattern in self.AD_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False


class YouTubeMobileCrawler(MobileCrawler):
    """유튜브 모바일 검색 크롤러 (일반 동영상 + Shorts)"""
    
    def crawl(self, keyword, max_regular=15, max_shorts_shelves=2, shorts_per_shelf=5):
        """
        유튜브 모바일 검색 결과 크롤링 (실제 화면 순서대로)
        
        새로운 방식:
        1. HTML을 스캔하며 요소의 순서(order_map) 기록
        2. 각 타입별로 데이터 수집 (videos, shorts_shelves)
        3. order_map에 따라 최종 결과 조립
        
        Args:
            keyword: 검색 키워드
            max_regular: 최대 일반 동영상 수 (기본 15개)
            max_shorts_shelves: 최대 Shorts 구간 수 (기본 2구간)
            shorts_per_shelf: 구간당 Shorts 수 (기본 5개)
            
        Returns:
            list: 검색 결과 딕셔너리 리스트 (실제 화면 순서대로)
        """
        results = []
        processed_video_ids = set()
        
        try:
            self.setup_driver()
            
            # 유튜브 검색 (모바일 버전)
            search_url = f"https://m.youtube.com/results?search_query={keyword}"
            self.driver.get(search_url)
            
            print(f"[유튜브 크롤링] URL: {search_url}")
            
            # 페이지 로딩 대기
            self.random_delay(5, 7)
            
            # 명시적 대기
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "contents"))
                )
            except:
                pass
            
            # 충분히 스크롤하여 모든 요소 로드
            print("[유튜브 크롤링] 페이지 스크롤 중...")
            for i in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(1, 2)
            
            print("[유튜브 크롤링] 페이지 파싱 시작...")
            
            # 페이지 소스 파싱
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 1단계: 순서 맵 생성
            order_map = []  # [('video', element), ('reel', element), ...]
            contents = soup.find('div', id='contents')
            
            if not contents:
                print("[오류] contents 컨테이너를 찾을 수 없습니다.")
                return []
            
            print("[1단계] 요소 순서 스캔 중...")
            for element in contents.children:
                if not element.name:
                    continue
                
                if element.name == 'ytm-video-with-context-renderer':
                    order_map.append(('video', element))
                elif element.name == 'ytm-reel-shelf-renderer':
                    order_map.append(('reel', element))
            
            print(f"[1단계 완료] 총 {len(order_map)}개 요소 발견")
            
            # 2단계: 데이터 수집
            print("[2단계] 데이터 수집 중...")
            videos = []  # 일반 영상 리스트
            shorts_shelves = []  # Shorts 구간 리스트
            
            # 일반 영상 수집
            video_count = 0
            for item_type, element in order_map:
                if item_type == 'video' and video_count < max_regular:
                # 페이지 소스 파싱
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 컨텐츠 컨테이너 찾기
                contents = soup.find('div', id='contents')
                
                # Fallback: contents를 찾지 못하면 전체 페이지에서 검색
                if not contents:
                    print("[Fallback] contents 컨테이너를 찾을 수 없어 전체 페이지에서 검색합니다.")
                    
                    # 전체 페이지에서 일반 영상 검색
                    if regular_count < max_regular:
                        video_elements = soup.find_all(['ytm-video-with-context-renderer', 'ytm-compact-video-renderer'])
                        print(f"[Fallback] 일반 영상 {len(video_elements)}개 발견")
                        
                        for video in video_elements:
                            if regular_count >= max_regular:
                                break
                            
                            try:
                                video_id = self._extract_video_id(video)
                                if not video_id or video_id in processed_video_ids:
                                    continue
                                
                                # 제목 추출
                                title_elem = video.find(['h3', 'h4', 'span'], class_=re.compile(r'(video-title|media-item-headline)'))
                                if not title_elem:
                                    continue
                                title = title_elem.get('aria-label', '') or title_elem.get('title', '') or title_elem.get_text(strip=True)
                                
                                url = f"https://www.youtube.com/watch?v={video_id}"
                                
                                # 썸네일
                                thumbnail = ''
                                img_elem = video.find('img')
                                if img_elem:
                                    thumbnail = img_elem.get('src', '') or img_elem.get('data-src', '')
                                
                                # 채널명
                                channel_name = ''
                                byline_container = video.find('span', class_='YtmBadgeAndBylineRendererItemByline')
                                if byline_container:
                                    channel_span = byline_container.find('span', class_='yt-core-attributed-string')
                                    if channel_span:
                                        channel_name = channel_span.get_text(strip=True)
                                
                                # 조회수, 업로드일
                                view_count = ''
                                view_count_numeric = 0
                                upload_date = ''
                                upload_timestamp = None
                                
                                attributed_spans = video.find_all('span', class_='yt-core-attributed-string')
                                for span in attributed_spans:
                                    aria_label = span.get('aria-label', '')
                                    text = span.get_text(strip=True)
                                    
                                    if '조회수' in aria_label or '조회수' in text:
                                        view_text = aria_label if aria_label else text
                                        view_count = view_text.replace('조회수 ', '').replace('조회수', '')
                                        view_count_numeric = self._parse_view_count(view_text)
                                    elif span.get('role') == 'text' and '전' in text:
                                        upload_date = text
                                        upload_timestamp = self._parse_upload_date(text)
                                
                                duration_elem = video.find(['span'], class_=re.compile(r'(time-status|duration)'))
                                duration = duration_elem.get_text(strip=True) if duration_elem else ''
                                
                                processed_video_ids.add(video_id)
                                
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'video_id': video_id,
                                    'thumbnail': thumbnail,
                                    'channel_name': channel_name,
                                    'view_count': view_count,
                                    'view_count_numeric': view_count_numeric,
                                    'upload_date': upload_date,
                                    'upload_timestamp': upload_timestamp,
                                    'like_count': '',
                                    'duration': duration,
                                    'position': overall_position,
                                    'is_short': False,
                                    'short_shelf_index': None,
                                    'position_in_shelf': None
                                })
                                
                                overall_position += 1
                                regular_count += 1
                                print(f"[Fallback 일반 #{overall_position-1}] {title[:30]}...")
                                
                            except Exception as e:
                                print(f"[Fallback 일반 파싱 오류] {e}")
                                continue
                    
                    # 전체 페이지에서 Shorts 검색
                    if shorts_shelf_count < max_shorts_shelves:
                        shorts_shelves = soup.find_all('ytm-reel-shelf-renderer')
                        print(f"[Fallback] Shorts 구간 {len(shorts_shelves)}개 발견")
                        
                        for shelf in shorts_shelves:
                            if shorts_shelf_count >= max_shorts_shelves:
                                break
                            
                            try:
                                first_short = shelf.find('ytm-shorts-lockup-view-model')
                                if first_short:
                                    first_link = first_short.find('a', href=re.compile(r'/shorts/'))
                                    if first_link:
                                        first_short_id = first_link.get('href').split('/shorts/')[1].split('?')[0]
                                        if first_short_id in processed_video_ids:
                                            continue
                                
                                shorts_shelf_count += 1
                                shorts_in_shelf = shelf.find_all('ytm-shorts-lockup-view-model')
                                position_in_shelf = 1
                                
                                for short in shorts_in_shelf[:shorts_per_shelf]:
                                    try:
                                        # 링크 추출 (정확한 클래스명 사용)
                                        link = short.find('a', class_='shortsLockupViewModelHostEndpoint')
                                        if not link:
                                            link = short.find('a', href=re.compile(r'/shorts/'))
                                        if not link:
                                            continue
                                        
                                        short_url = link.get('href')
                                        if not short_url or '/shorts/' not in short_url:
                                            continue
                                        
                                        video_id = short_url.split('/shorts/')[1].split('?')[0]
                                        
                                        if video_id in processed_video_ids:
                                            continue
                                        
                                        # 제목 추출 (실제 구조에 맞게)
                                        title = ''
                                        title_h3 = short.find('h3', class_='shortsLockupViewModelHostMetadataTitle')
                                        if title_h3:
                                            title_span = title_h3.find('span', class_='yt-core-attributed-string')
                                            if title_span:
                                                title = title_span.get_text(strip=True)
                                        
                                        if not title:
                                            continue
                                        
                                        # 조회수 추출 (실제 구조에 맞게)
                                        view_count = ''
                                        view_count_numeric = 0
                                        subhead = short.find('div', class_='shortsLockupViewModelHostMetadataSubhead')
                                        if subhead:
                                            views_span = subhead.find('span', class_='yt-core-attributed-string')
                                            if views_span:
                                                view_text = views_span.get_text(strip=True)
                                                view_count = view_text.replace('조회수 ', '').replace('조회수', '').strip()
                                                view_count_numeric = self._parse_view_count(view_text)
                                        
                                        # 썸네일 추출
                                        thumbnail = ''
                                        img_elem = short.find('img', class_='shortsLockupViewModelHostThumbnail')
                                        if img_elem:
                                            thumbnail = img_elem.get('src', '')
                                        
                                        processed_video_ids.add(video_id)
                                        
                                        results.append({
                                            'title': title,
                                            'url': f"https://www.youtube.com{short_url}",
                                            'video_id': video_id,
                                            'thumbnail': thumbnail,
                                            'channel_name': '',
                                            'view_count': view_count,
                                            'view_count_numeric': view_count_numeric,
                                            'upload_date': '',
                                            'upload_timestamp': None,
                                            'like_count': '',
                                            'duration': '',
                                            'position': overall_position,
                                            'is_short': True,
                                            'short_shelf_index': shorts_shelf_count,
                                            'position_in_shelf': position_in_shelf
                                        })
                                        
                                        print(f"[Fallback 숏츠 {shorts_shelf_count}-{position_in_shelf} #{overall_position}] {title[:30]}...")
                                        
                                        overall_position += 1
                                        position_in_shelf += 1
                                        
                                    except Exception as e:
                                        print(f"[Fallback Shorts 파싱 오류] {e}")
                                        continue
                            
                            except Exception as e:
                                print(f"[Fallback Shorts 구간 오류] {e}")
                                continue
                    
                    # 스크롤 후 다음 반복
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.random_delay(2, 3)
                    scroll_count += 1
                    continue
                
                # 정상 경로: contents가 있는 경우 - 모든 자식 요소를 순서대로 처리
                for element in contents.children:
                    if not element.name:  # 텍스트 노드 스킵
                        continue
                    
                    # 목표 달성 확인
                    if regular_count >= max_regular and shorts_shelf_count >= max_shorts_shelves:
                        break
                    
                    # 1. 일반 동영상 처리
                    if element.name in ['ytm-video-with-context-renderer', 'ytm-compact-video-renderer']:
                        if regular_count >= max_regular:
                            continue
                        
                        try:
                            video_id = self._extract_video_id(element)
                            if not video_id or video_id in processed_video_ids:
                                continue
                            
                            # 제목 추출
                            title_elem = element.find(['h3', 'h4', 'span'], class_=re.compile(r'(video-title|media-item-headline)'))
                            if not title_elem:
                                continue
                            title = title_elem.get('aria-label', '') or title_elem.get('title', '') or title_elem.get_text(strip=True)
                            
                            # URL 생성
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            
                            # 썸네일 추출
                            thumbnail = ''
                            img_elem = element.find('img')
                            if img_elem:
                                thumbnail = img_elem.get('src', '') or img_elem.get('data-src', '')
                            
                            # 채널명 추출
                            channel_name = ''
                            byline_container = element.find('span', class_='YtmBadgeAndBylineRendererItemByline')
                            if byline_container:
                                channel_span = byline_container.find('span', class_='yt-core-attributed-string')
                                if channel_span:
                                    channel_name = channel_span.get_text(strip=True)
                            
                            # 메타데이터 추출 (조회수, 업로드일)
                            view_count = ''
                            view_count_numeric = 0
                            upload_date = ''
                            upload_timestamp = None
                            
                            attributed_spans = element.find_all('span', class_='yt-core-attributed-string')
                            for span in attributed_spans:
                                aria_label = span.get('aria-label', '')
                                text = span.get_text(strip=True)
                                
                                if '조회수' in aria_label or '조회수' in text:
                                    view_text = aria_label if aria_label else text
                                    view_count = view_text.replace('조회수 ', '').replace('조회수', '')
                                    view_count_numeric = self._parse_view_count(view_text)
                                elif span.get('role') == 'text' and '전' in text:
                                    upload_date = text
                                    upload_timestamp = self._parse_upload_date(text)
                            
                            # 영상 길이 추출
                            duration_elem = element.find(['span'], class_=re.compile(r'(time-status|duration)'))
                            duration = duration_elem.get_text(strip=True) if duration_elem else ''
                            
                            processed_video_ids.add(video_id)
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'video_id': video_id,
                                'thumbnail': thumbnail,
                                'channel_name': channel_name,
                                'view_count': view_count,
                                'view_count_numeric': view_count_numeric,
                                'upload_date': upload_date,
                                'upload_timestamp': upload_timestamp,
                                'like_count': '',
                                'duration': duration,
                                'position': overall_position,
                                'is_short': False,
                                'short_shelf_index': None,
                                'position_in_shelf': None
                            })
                            
                            overall_position += 1
                            regular_count += 1
                            print(f"[일반 #{overall_position-1}] {title[:30]}...")
                            
                        except Exception as e:
                            print(f"[일반 동영상 파싱 오류] {e}")
                            continue
                    
                    # 2. Shorts 구간 처리
                    elif element.name == 'ytm-reel-shelf-renderer':
                        if shorts_shelf_count >= max_shorts_shelves:
                            continue
                        
                        try:
                            # 이미 처리한 구간인지 확인
                            first_short = element.find('ytm-shorts-lockup-view-model')
                            if first_short:
                                first_link = first_short.find('a', href=re.compile(r'/shorts/'))
                                if first_link:
                                    first_short_id = first_link.get('href').split('/shorts/')[1].split('?')[0]
                                    if first_short_id in processed_video_ids:
                                        continue
                            
                            shorts_shelf_count += 1
                            shorts_in_shelf = element.find_all('ytm-shorts-lockup-view-model')
                            position_in_shelf = 1
                            
                            print(f"[Shorts 구간 {shorts_shelf_count}] {len(shorts_in_shelf)}개 발견")
                            
                            for short in shorts_in_shelf[:shorts_per_shelf]:
                                try:
                                    # 링크 추출 (정확한 클래스명 사용)
                                    link = short.find('a', class_='shortsLockupViewModelHostEndpoint')
                                    if not link:
                                        link = short.find('a', href=re.compile(r'/shorts/'))
                                    if not link:
                                        continue
                                    
                                    short_url = link.get('href')
                                    if not short_url or '/shorts/' not in short_url:
                                        continue
                                    
                                    video_id = short_url.split('/shorts/')[1].split('?')[0]
                                    
                                    if video_id in processed_video_ids:
                                        continue
                                    
                                    # 제목 추출 (실제 구조에 맞게)
                                    title = ''
                                    title_h3 = short.find('h3', class_='shortsLockupViewModelHostMetadataTitle')
                                    if title_h3:
                                        title_span = title_h3.find('span', class_='yt-core-attributed-string')
                                        if title_span:
                                            title = title_span.get_text(strip=True)
                                    
                                    if not title:
                                        continue
                                    
                                    # 조회수 추출 (실제 구조에 맞게)
                                    view_count = ''
                                    view_count_numeric = 0
                                    subhead = short.find('div', class_='shortsLockupViewModelHostMetadataSubhead')
                                    if subhead:
                                        views_span = subhead.find('span', class_='yt-core-attributed-string')
                                        if views_span:
                                            view_text = views_span.get_text(strip=True)
                                            view_count = view_text.replace('조회수 ', '').replace('조회수', '').strip()
                                            view_count_numeric = self._parse_view_count(view_text)
                                    
                                    # 썸네일 추출
                                    thumbnail = ''
                                    img_elem = short.find('img', class_='shortsLockupViewModelHostThumbnail')
                                    if img_elem:
                                        thumbnail = img_elem.get('src', '')
                                    
                                    processed_video_ids.add(video_id)
                                    
                                    results.append({
                                        'title': title,
                                        'url': f"https://www.youtube.com{short_url}",
                                        'video_id': video_id,
                                        'thumbnail': thumbnail,
                                        'channel_name': '',
                                        'view_count': view_count,
                                        'view_count_numeric': view_count_numeric,
                                        'upload_date': '',
                                        'upload_timestamp': None,
                                        'like_count': '',
                                        'duration': '',
                                        'position': overall_position,
                                        'is_short': True,
                                        'short_shelf_index': shorts_shelf_count,
                                        'position_in_shelf': position_in_shelf
                                    })
                                    
                                    print(f"[숏츠 {shorts_shelf_count}-{position_in_shelf} #{overall_position}] {title[:30]}...")
                                    
                                    overall_position += 1
                                    position_in_shelf += 1
                                    
                                except Exception as e:
                                    print(f"[Shorts 파싱 오류] {e}")
                                    continue
                        
                        except Exception as e:
                            print(f"[Shorts 구간 파싱 오류] {e}")
                            continue
                
                # 목표 달성 확인
                if regular_count >= max_regular and shorts_shelf_count >= max_shorts_shelves:
                    print(f"[유튜브 크롤링] 목표 달성! 일반 {regular_count}개 + Shorts {shorts_shelf_count}구간")
                    break
                
                # 스크롤하여 더 많은 결과 로드
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                scroll_count += 1
            
            print(f"[유튜브 크롤링] 완료: 총 {len(results)}개 (일반 {regular_count}개 + Shorts {len([r for r in results if r['is_short']])}개)")
            
        except Exception as e:
            print(f"[유튜브 크롤링] 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_driver()
        
        return results
    
    def _extract_video_id(self, element):
        """비디오 ID 추출"""
        try:
            # 링크에서 video_id 추출
            link = element.find('a', href=True)
            if link:
                href = link.get('href', '')
                if '/watch?v=' in href:
                    return href.split('/watch?v=')[1].split('&')[0]
                elif '/shorts/' in href:
                    return href.split('/shorts/')[1].split('?')[0]
        except:
            pass
        return None
    
    def _parse_view_count(self, text):
        """조회수 텍스트를 숫자로 변환"""
        try:
            # "조회수 1.5천회" -> 1500
            text = text.replace('조회수', '').replace('회', '').strip()
            
            if '만' in text:
                num = float(text.replace('만', ''))
                return int(num * 10000)
            elif '천' in text:
                num = float(text.replace('천', ''))
                return int(num * 1000)
            else:
                return int(re.sub(r'[^\d]', '', text))
        except:
            return 0
    
    def _parse_upload_date(self, text):
        """업로드 날짜 텍스트를 datetime으로 변환"""
        try:
            now = datetime.now()
            
            # "3일 전", "2주 전", "1개월 전", "1년 전" 등
            if '초 전' in text or 'second' in text.lower():
                return now
            elif '분 전' in text or 'minute' in text.lower():
                minutes = int(re.search(r'\d+', text).group())
                return now - timedelta(minutes=minutes)
            elif '시간 전' in text or 'hour' in text.lower():
                hours = int(re.search(r'\d+', text).group())
                return now - timedelta(hours=hours)
            elif '일 전' in text or 'day' in text.lower():
                days = int(re.search(r'\d+', text).group())
                return now - timedelta(days=days)
            elif '주 전' in text or 'week' in text.lower():
                weeks = int(re.search(r'\d+', text).group())
                return now - timedelta(weeks=weeks)
            elif '개월 전' in text or 'month' in text.lower():
                months = int(re.search(r'\d+', text).group())
                return now - timedelta(days=months*30)
            elif '년 전' in text or 'year' in text.lower():
                years = int(re.search(r'\d+', text).group())
                return now - timedelta(days=years*365)
        except:
            pass
        return None


def crawl_all(keyword, google_max=50, youtube_max=50):
    """구글과 유튜브를 동시에 크롤링"""
    results = {
        'google': [],
        'youtube': []
    }
    
    # 구글 크롤링
    print(f"\n{'='*50}")
    print(f"구글 검색 시작: {keyword}")
    print(f"{'='*50}")
    google_crawler = GoogleMobileCrawler()
    results['google'] = google_crawler.crawl(keyword, max_results=google_max)
    
    # 유튜브 크롤링 (일반 15개 + Shorts 2구간x5개)
    print(f"\n{'='*50}")
    print(f"유튜브 검색 시작: {keyword}")
    print(f"{'='*50}")
    youtube_crawler = YouTubeMobileCrawler()
    results['youtube'] = youtube_crawler.crawl(keyword, max_regular=15, max_shorts_shelves=2, shorts_per_shelf=5)
    
    return results

