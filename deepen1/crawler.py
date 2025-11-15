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
        # chrome_options.add_argument('--headless=new')  # 헤드리스 모드 (디버깅용 비활성화)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')  # 최대화 창으로 시작
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("detach", True)  # 브라우저 유지
        
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
    
    def crawl(self, keyword):
        """
        구글 모바일 검색 결과 크롤링 (스크롤 끝까지)
        
        Args:
            keyword: 검색 키워드
            
        Returns:
            list: 검색 결과 딕셔너리 리스트
        """
        results = []
        
        try:
            self.setup_driver()
            
            # 구글 검색 (모바일 버전)
            search_url = f"https://www.google.com/search?q={keyword}&hl=ko"
            self.driver.get(search_url)
            print(f"[구글 크롤링] URL: {search_url}")
            
            # 페이지 로딩 대기
            print("[구글 크롤링] 페이지 로딩 대기 중...")
            self.random_delay(3, 5)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            # 스크롤하여 모든 결과 로드
            print("[구글 크롤링] 페이지 스크롤 중...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 10
            
            while scroll_count < max_scrolls:
                # 스크롤 다운
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                
                # 새로운 높이 확인
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    # 더 이상 로드할 내용이 없으면 종료
                    break
                
                last_height = new_height
                scroll_count += 1
                print(f"  [스크롤] {scroll_count}회 완료")
            
            print("[구글 크롤링] 페이지 파싱 시작...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 검색 결과 수집
            processed_urls = {}  # {(url, position): result_type} 형태로 저장 (URL+position 조합)
            position = 1
            general_results = []
            image_results = []
            
            # 1단계: 일반 링크 수집
            print("[구글 크롤링] 1단계: 일반 링크 수집 중...")
            all_items = soup.find_all('div', class_='kb0PBd')
            print(f"  → {len(all_items)}개 아이템 발견")
            
            for item in all_items:
                try:
                    # 일반 링크 확인 (data-snf="GuLy6c")
                    title_container = item.find('div', {'data-snf': 'GuLy6c'})
                    if not title_container:
                        continue
                    
                    title_elem = title_container.find('span')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # URL 찾기 (부모에서)
                    parent = item.find_parent(['div', 'a'])
                    link_elem = None
                    while parent and not link_elem:
                        link_elem = parent.find('a', class_='rTyHce', href=True)
                        if not link_elem:
                            parent = parent.find_parent(['div'])
                    
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    
                    # URL 정제
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    # 유효성 검사
                    if not url.startswith('http'):
                        continue
                    
                    # 중복 체크: 같은 URL + position 조합이 이미 있으면 제외
                    key = (url, position)
                    if key in processed_urls:
                        continue
                    
                    # 광고 필터링
                    if self._is_ad(url, item):
                        continue
                    
                    # 출처 찾기 (data-snf="dqs64d")
                    source = ''
                    source_container = item.find_parent(['div']).find('div', {'data-snf': 'dqs64d'})
                    if source_container:
                        source_elem = source_container.find('div', class_='GkAmnd')
                        if source_elem:
                            source = source_elem.get_text(strip=True)
                    
                    processed_urls[key] = '일반'
                    
                    general_results.append({
                        'title': title,
                        'url': url,
                        'snippet': source,
                        'source': source,
                        'thumbnail': '',
                        'position': position,
                        'result_type': '일반',
                        'published_date': '',
                        'is_ad': False
                    })
                    
                    print(f"  [일반] {len(general_results)}. {source} - {title[:40]}...")
                    position += 1
                    
                except Exception as e:
                    continue
            
            print(f"[1단계 완료] 일반 링크 {len(general_results)}개 수집")
            
            # 2단계: 이미지 링크 수집
            print("[구글 크롤링] 2단계: 이미지 링크 수집 중...")
            
            # 모든 이미지 섹션 찾기 (data-attrid="images universal")
            image_sections = soup.find_all('div', attrs={'data-attrid': 'images universal'})
            
            if not image_sections:
                print("  → 이미지 섹션을 찾을 수 없음")
            else:
                print(f"  → {len(image_sections)}개 이미지 섹션 발견")
                
                # 모든 섹션에서 aria-label이 있는 <a> 태그 수집
                image_links = []
                for section in image_sections:
                    links = section.find_all('a', attrs={'aria-label': True, 'href': True})
                    image_links.extend(links)
                
                print(f"  → 총 {len(image_links)}개 이미지 링크 발견")
                
                img_count = 0
                for link in image_links:
                    try:
                        img_count += 1
                        
                        # 제목은 aria-label
                        title = link.get('aria-label', '').strip()
                        url = link.get('href', '')
                        
                        print(f"  [디버그 {img_count}] title={title[:50]}")
                        print(f"    → 원본 URL: {url[:80]}...")
                        
                        if not title or len(title) < 2:
                            print(f"    → 제목이 너무 짧아서 제외")
                            continue
                        
                        # URL 정제
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                            print(f"    → 정제된 URL: {url[:80]}...")
                        
                        # 유효성 검사
                        if not url.startswith('http'):
                            print(f"    → http로 시작하지 않음")
                            continue
                        
                        # 출처는 URL에서 추출
                        from urllib.parse import urlparse
                        source = ''
                        try:
                            parsed = urlparse(url)
                            source = parsed.netloc.replace('www.', '')
                            print(f"    → 출처: {source}")
                        except Exception as e:
                            print(f"    → 출처 추출 실패: {e}")
                            source = ''
                        
                        if not source:
                            print(f"    → 출처가 없어서 제외")
                            continue
                        
                        # 중복 체크: 같은 URL + position 조합이 이미 있으면 제외
                        key = (url, position)
                        if key in processed_urls:
                            print(f"    → 중복 URL+position (이미지)")
                            continue
                        
                        processed_urls[key] = '이미지'
                        
                        # 썸네일 이미지 찾기 (같은 부모 안에서)
                        thumbnail = ''
                        parent = link.find_parent()
                        if parent:
                            img_elem = parent.find('img')
                            if img_elem:
                                thumbnail = img_elem.get('src', '')
                        
                        image_results.append({
                            'title': title,
                            'url': url,
                            'snippet': source,
                            'source': source,
                            'thumbnail': thumbnail,
                            'position': position,
                            'result_type': '이미지',
                            'published_date': '',
                            'is_ad': False
                        })
                        
                        print(f"  ✅ [이미지 {len(image_results)}] {source} - {title[:40]}...")
                        position += 1
                        
                        # 처음 10개만 상세 로그
                        if img_count >= 10:
                            print(f"  [디버그] 10개 이상 처리됨, 상세 로그 생략...")
                            break
                        
                    except Exception as e:
                        print(f"    → 예외 발생: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                # 나머지 이미지도 조용히 처리
                if img_count >= 10:
                    for link in image_links[10:]:
                        try:
                            title = link.get('aria-label', '').strip()
                            url = link.get('href', '')
                            
                            if not title or len(title) < 2:
                                continue
                            
                            if url.startswith('/url?q='):
                                url = url.split('/url?q=')[1].split('&')[0]
                            
                            if not url.startswith('http'):
                                continue
                            
                            from urllib.parse import urlparse
                            source = ''
                            try:
                                parsed = urlparse(url)
                                source = parsed.netloc.replace('www.', '')
                            except:
                                source = ''
                            
                            if not source:
                                continue
                            
                            # 중복 체크: 같은 URL + position 조합이 이미 있으면 제외
                            key = (url, position)
                            if key in processed_urls:
                                continue
                            
                            processed_urls[key] = '이미지'
                            
                            thumbnail = ''
                            parent = link.find_parent()
                            if parent:
                                img_elem = parent.find('img')
                                if img_elem:
                                    thumbnail = img_elem.get('src', '')
                            
                            image_results.append({
                                'title': title,
                                'url': url,
                                'snippet': source,
                                'source': source,
                                'thumbnail': thumbnail,
                                'result_type': '이미지',
                                'published_date': '',
                                'is_ad': False
                            })
                            
                        except Exception as e:
                            continue
            
            print(f"[2단계 완료] 이미지 링크 {len(image_results)}개 수집")
            
            # 3단계: 결과 합치기 (일반 + 이미지)
            print("[구글 크롤링] 3단계: 결과 합치기...")
            all_results = general_results + image_results
            
            for result in all_results:
                result['position'] = position
                results.append(result)
                position += 1
            
            print(f"[구글 크롤링 완료] 총 {len(results)}개 결과 (일반 {len(general_results)}개 + 이미지 {len(image_results)}개)")
            
        except Exception as e:
            print(f"[구글 크롤링 오류] {e}")
            import traceback
            traceback.print_exc()
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
            
            # 스마트 스크롤: 목표 개수에 도달할 때까지만 스크롤
            print("[유튜브 크롤링] 스마트 스크롤 시작...")
            target_videos = max_regular
            target_shorts = max_shorts_shelves
            
            scroll_count = 0
            max_scroll = 10  # 최대 스크롤 횟수 (안전장치)
            last_height = 0
            
            while scroll_count < max_scroll:
                # 현재 페이지 높이
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # 스크롤 실행
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scroll_count += 1
                print(f"  [스크롤 {scroll_count}회] 높이: {current_height}")
                self.random_delay(1.5, 2)
                
                # 현재까지 수집된 아이템 개수 체크
                soup_temp = BeautifulSoup(self.driver.page_source, 'html.parser')
                contents_temp = soup_temp.find('div', id='contents')
                if not contents_temp:
                    contents_temp = soup_temp.find('ytm-item-section-renderer')
                if not contents_temp:
                    contents_temp = soup_temp.find('div', {'role': 'main'})
                if not contents_temp:
                    contents_temp = soup_temp.find('body')
                
                if contents_temp:
                    items_temp = contents_temp.find_all(class_='item')
                    video_count = sum(1 for item in items_temp if item.name == 'ytm-video-with-context-renderer')
                    shorts_count = sum(1 for item in items_temp if item.name in ['ytm-reel-shelf-renderer', 'grid-shelf-view-model'])
                    
                    print(f"    → 현재: 일반 {video_count}개, Shorts {shorts_count}개 발견")
                    
                    # 목표 개수 도달 확인
                    if video_count >= target_videos and shorts_count >= target_shorts:
                        print(f"  ✅ 목표 달성! (일반 {target_videos}개, Shorts {target_shorts}개)")
                        break
                
                # 더 이상 스크롤되지 않으면 중단
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print(f"  ⚠️ 더 이상 스크롤 불가 (페이지 끝)")
                    break
                last_height = new_height
            
            print(f"[스크롤 완료] 총 {scroll_count}회 스크롤")
            
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


def crawl_all(keyword):
    """구글과 유튜브를 동시에 크롤링"""
    results = {
        'google': [],
        'youtube': []
    }
    
    # 구글 크롤링 (화면에 보이는 만큼만)
    print(f"\n{'='*50}")
    print(f"구글 검색 시작: {keyword}")
    print(f"{'='*50}")
    google_crawler = GoogleMobileCrawler()
    results['google'] = google_crawler.crawl(keyword)
    
    # 유튜브 크롤링 (일반 15개 + Shorts 2구간x5개)
    print(f"\n{'='*50}")
    print(f"유튜브 검색 시작: {keyword}")
    print(f"{'='*50}")
    youtube_crawler = YouTubeMobileCrawler()
    results['youtube'] = youtube_crawler.crawl(keyword, max_regular=15, max_shorts_shelves=2, shorts_per_shelf=5)
    
    return results
