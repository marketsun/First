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
            pass  # 드라이버를 유지하여 연속 크롤링 가능
        
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
        """유튜브 모바일 검색 결과 크롤링 (실제 화면 순서대로)"""
        results = []
        
        try:
            self.setup_driver()
            search_url = f"https://m.youtube.com/results?search_query={keyword}"
            self.driver.get(search_url)
            print(f"[유튜브 크롤링] URL: {search_url}")
            
            # 페이지 로딩 대기 (증가)
            print("[유튜브 크롤링] 페이지 로딩 대기 중...")
            print(f"[디버그] 브라우저 창이 열렸습니다!")
            print(f"[디버그] URL: {search_url}")
            self.random_delay(10, 12)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print(f"[디버그] 페이지 제목: {self.driver.title}")
            except Exception as e:
                print(f"[경고] 페이지 로딩 대기 중 오류: {e}")
            
            # 충분히 스크롤
            print("[유튜브 크롤링] 페이지 스크롤 중...")
            for i in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(1, 2)
            
            print("[유튜브 크롤링] 페이지 파싱 시작...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 1단계: 순서 맵 생성
            order_map = []
            
            # 다양한 방법으로 컨테이너 찾기
            contents = soup.find('div', id='contents')
            if not contents:
                print("[시도 1] id='contents' 찾기 실패, 다른 방법 시도 중...")
                contents = soup.find('ytm-item-section-renderer')
            if not contents:
                print("[시도 2] ytm-item-section-renderer 찾기 실패, 다른 방법 시도 중...")
                contents = soup.find('div', {'role': 'main'})
            if not contents:
                print("[시도 3] role='main' 찾기 실패, body 전체 사용...")
                contents = soup.find('body')
            
            if not contents:
                print("[오류] 어떤 컨테이너도 찾을 수 없습니다.")
                return []
            
            print(f"[성공] 컨테이너 발견: {contents.name}")
            
            print("[1단계] 요소 순서 스캔 중...")
            # class="item"인 모든 요소 찾기
            items = contents.find_all(class_='item')
            print(f"  [디버그] 총 {len(items)}개 item 발견")
            
            for element in items:
                if not element.name:
                    continue
                if element.name == 'ytm-video-with-context-renderer':
                    order_map.append(('video', element))
                    print(f"  [디버그] 일반 영상 발견")
                elif element.name == 'ytm-reel-shelf-renderer':
                    order_map.append(('reel', element))
                    print(f"  [디버그] Shorts 구간 발견 (ytm-reel-shelf-renderer)")
                elif element.name == 'grid-shelf-view-model':
                    order_map.append(('reel', element))
                    print(f"  [디버그] Shorts 구간 발견 (grid-shelf-view-model)")
            
            print(f"[1단계 완료] 총 {len(order_map)}개 요소 발견 (일반/Shorts 합계)")
            
            # 2단계: 데이터 수집
            print("[2단계] 데이터 수집 중...")
            videos = []
            shorts_shelves = []
            processed_video_ids = set()
            
            # 일반 영상 수집
            video_count = 0
            for item_type, element in order_map:
                if item_type == 'video' and video_count < max_regular:
                    try:
                        video_data = self._parse_video(element, processed_video_ids)
                        if video_data:
                            videos.append(video_data)
                            video_count += 1
                            print(f"  [일반 영상 {video_count}/{max_regular}] {video_data['title'][:30]}...")
                    except Exception as e:
                        print(f"  [일반 영상 파싱 오류] {e}")
                        continue
            
            # Shorts 구간 수집
            shorts_count = 0
            for item_type, element in order_map:
                if item_type == 'reel' and shorts_count < max_shorts_shelves:
                    try:
                        shelf_data = self._parse_shorts_shelf(element, processed_video_ids, shorts_per_shelf)
                        if shelf_data:
                            shorts_shelves.append(shelf_data)
                            shorts_count += 1
                            print(f"  [Shorts 구간 {shorts_count}/{max_shorts_shelves}] {len(shelf_data)}개 수집")
                    except Exception as e:
                        print(f"  [Shorts 구간 파싱 오류] {e}")
                        continue
            
            print(f"[2단계 완료] 일반 {len(videos)}개, Shorts 구간 {len(shorts_shelves)}개")
            
            # 3단계: 순서대로 조립
            print("[3단계] 결과 조립 중...")
            video_idx = 0
            reel_idx = 0
            overall_position = 1
            
            for item_type, _ in order_map:
                if item_type == 'video' and video_idx < len(videos):
                    video = videos[video_idx]
                    video['position'] = overall_position
                    results.append(video)
                    overall_position += 1
                    video_idx += 1
                    
                elif item_type == 'reel' and reel_idx < len(shorts_shelves):
                    shelf = shorts_shelves[reel_idx]
                    reel_idx += 1
                    
                    for position_in_shelf, short in enumerate(shelf, 1):
                        short['position'] = overall_position
                        short['short_shelf_index'] = reel_idx
                        short['position_in_shelf'] = position_in_shelf
                        results.append(short)
                        overall_position += 1
            
            print(f"[3단계 완료] 총 {len(results)}개 결과 조립")
            print(f"[유튜브 크롤링 완료] 일반 {video_idx}개 + Shorts {sum(len(s) for s in shorts_shelves)}개 = 총 {len(results)}개")
            
        except Exception as e:
            print(f"[유튜브 크롤링 오류] {e}")
            import traceback
            traceback.print_exc()
        finally:
            pass  # 드라이버를 유지하여 연속 크롤링 가능
        
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
    
    def _parse_video(self, element, processed_video_ids):
        """일반 영상 파싱"""
        video_id = self._extract_video_id(element)
        if not video_id or video_id in processed_video_ids:
            return None
        
        title_elem = element.find(['h3', 'h4', 'span'], class_=re.compile(r'(video-title|media-item-headline)'))
        if not title_elem:
            return None
        title = title_elem.get('aria-label', '') or title_elem.get('title', '') or title_elem.get_text(strip=True)
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        thumbnail = ''
        img_elem = element.find('img')
        if img_elem:
            thumbnail = img_elem.get('src', '') or img_elem.get('data-src', '')
        
        channel_name = ''
        byline_container = element.find('span', class_='YtmBadgeAndBylineRendererItemByline')
        if byline_container:
            channel_span = byline_container.find('span', class_='yt-core-attributed-string')
            if channel_span:
                channel_name = channel_span.get_text(strip=True)
        
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
                view_count = view_text.replace('조회수 ', '').replace('조회수', '').strip()
                view_count_numeric = self._parse_view_count(view_text)
            elif span.get('role') == 'text' and '전' in text:
                upload_date = text
                upload_timestamp = self._parse_upload_date(text)
        
        duration_elem = element.find(['span'], class_=re.compile(r'(time-status|duration)'))
        duration = duration_elem.get_text(strip=True) if duration_elem else ''
        
        processed_video_ids.add(video_id)
        
        return {
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
            'position': 0,
            'is_short': False,
            'short_shelf_index': None,
            'position_in_shelf': None
        }
    
    def _parse_shorts_shelf(self, element, processed_video_ids, shorts_per_shelf):
        """Shorts 구간 파싱 (ytm-reel-shelf-renderer 또는 grid-shelf-view-model)"""
        shelf_data = []
        
        # 두 가지 구조 모두 지원
        # 1) ytm-reel-shelf-renderer 내부의 ytm-shorts-lockup-view-model
        # 2) grid-shelf-view-model 내부의 ytm-shorts-lockup-view-model
        shorts_in_shelf = element.find_all('ytm-shorts-lockup-view-model')
        
        if not shorts_in_shelf:
            print(f"    [경고] Shorts 아이템을 찾을 수 없습니다. element: {element.name}")
            return []
        
        print(f"    [디버그] {len(shorts_in_shelf)}개 Shorts 발견 (최대 {shorts_per_shelf}개 수집)")
        
        for short in shorts_in_shelf[:shorts_per_shelf]:
            try:
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
                
                title = ''
                title_h3 = short.find('h3', class_='shortsLockupViewModelHostMetadataTitle')
                if title_h3:
                    title_span = title_h3.find('span', class_='yt-core-attributed-string')
                    if title_span:
                        title = title_span.get_text(strip=True)
                
                if not title:
                    continue
                
                # 조회수 추출 (인라인 메타데이터)
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
                
                # 채널명 추출 (외부 메타데이터)
                channel_name = ''
                outside_metadata = short.find('div', class_='shortsLockupViewModelHostOutsideMetadata')
                if outside_metadata:
                    channel_title = outside_metadata.find('h3', class_='shortsLockupViewModelHostOutsideMetadataTitle')
                    if channel_title:
                        channel_span = channel_title.find('span', class_='yt-core-attributed-string')
                        if channel_span:
                            channel_name = channel_span.get_text(strip=True)
                
                # 업로드 날짜 추출 (외부 메타데이터)
                upload_date = ''
                upload_timestamp = None
                if outside_metadata:
                    date_div = outside_metadata.find('div', class_='shortsLockupViewModelHostOutsideMetadataSubhead')
                    if date_div:
                        date_span = date_div.find('span', class_='yt-core-attributed-string')
                        if date_span:
                            upload_date = date_span.get_text(strip=True)
                            upload_timestamp = self._parse_upload_date(upload_date)
                
                processed_video_ids.add(video_id)
                
                shelf_data.append({
                    'title': title,
                    'url': f"https://www.youtube.com{short_url}",
                    'video_id': video_id,
                    'thumbnail': thumbnail,
                    'channel_name': channel_name,
                    'view_count': view_count,
                    'view_count_numeric': view_count_numeric,
                    'upload_date': upload_date,
                    'upload_timestamp': upload_timestamp,
                    'like_count': '',
                    'duration': '',
                    'position': 0,
                    'is_short': True,
                    'short_shelf_index': 0,
                    'position_in_shelf': 0
                })
                
            except Exception as e:
                print(f"    [Shorts 파싱 오류] {e}")
                continue
        
        return shelf_data


def crawl_all(keyword, google_max=10, youtube_max=25):
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
