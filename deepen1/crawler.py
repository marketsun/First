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
    """구글 모바일 검색 크롤러 - 개선된 버전 (crawler_test.py에서 이식)"""
    
    # 광고 및 필터링할 도메인 패턴
    AD_PATTERNS = [
        r'googleadservices\.com',
        r'/aclk\?',
        r'sponsored',
        r'ad_type',
        r'adurl',
        r'&ad=',
        r'\?ad=',
        r'advertisement',
    ]
    
    def crawl(self, keyword, screenshot_path=None):
        """
        구글 모바일 검색 결과 크롤링 (스크롤 끝까지)
        
        Args:
            keyword: 검색 키워드
            screenshot_path: 스크린샷 저장 경로 (옵션)
            
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
            
            # 스크린샷 저장 - 조금씩 스크롤하면서 이미지 로드 후 캡처
            if screenshot_path:
                try:
                    import base64
                    
                    print("[구글 크롤링] 스크린샷 준비: 이미지 로드를 위한 스크롤 시작...")
                    
                    # 1단계: 최상단으로 이동
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # 2단계: 전체 페이지 높이 확인 (고정)
                    total_height = self.driver.execute_script("return document.body.scrollHeight")
                    viewport_height = self.driver.execute_script("return window.innerHeight")
                    
                    print(f"  → 전체 높이: {total_height}px, 뷰포트: {viewport_height}px")
                    
                    # 3단계: 조금씩 스크롤하면서 이미지 로드
                    scroll_step = 350  # 350px씩 작게 스크롤
                    current_position = 0
                    scroll_count = 0
                    
                    while current_position < total_height:
                        current_position += scroll_step
                        self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                        scroll_count += 1
                        print(f"  [스크롤 {scroll_count}] 위치: {current_position}/{total_height}px")
                        
                        # 페이지 끝에 도달하면 중단
                        if current_position >= total_height:
                            break
                    
                    # 4단계: 마지막 대기 (모든 이미지 로드 완료)
                    print("  → 이미지 로드 대기 중...")
                    time.sleep(2)
                    
                    # 5단계: 다시 최상단으로 이동
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # 6단계: 전체 페이지 크기 가져오기
                    metrics = self.driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
                    width = metrics['contentSize']['width']
                    height = metrics['contentSize']['height']
                    
                    print(f"[구글 크롤링] 최종 페이지 크기: {width}x{height}")
                    
                    # 7단계: CDP를 사용하여 전체 페이지 스크린샷 캡처
                    screenshot = self.driver.execute_cdp_cmd('Page.captureScreenshot', {
                        'clip': {
                            'width': width,
                            'height': height,
                            'x': 0,
                            'y': 0,
                            'scale': 1
                        },
                        'captureBeyondViewport': True
                    })
                    
                    # Base64 디코딩 후 파일로 저장
                    with open(screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(screenshot['data']))
                    
                    print(f"[구글 크롤링] 전체 페이지 스크린샷 저장: {screenshot_path}")
                except Exception as e:
                    print(f"[구글 크롤링] 스크린샷 저장 실패: {e}")
                    import traceback
                    traceback.print_exc()
            
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
            position = 1
            general_results = []
            image_results = []
            
            # 위치 기반 중복 제거용
            processed_items = {}  # {(url, title): last_position} - URL + 제목 조합으로 중복 체크
            position_threshold = 10  # 10개 이내 거리면 같은 구간으로 간주
            valid_link_position = 0  # 유효한 링크만 카운트 (필터링 통과한 링크)
            last_collected_url = None  # 바로 이전 수집 URL
            last_collected_title = None  # 바로 이전 수집 제목
            
            # 1단계: 모든 링크 수집 (순서 유지)
            print("[구글 크롤링] 1단계: 모든 링크 수집 중...")
            
            # 검색 결과 메인 영역의 모든 div (순서대로)
            search_area = soup.find('div', id='search')
            if search_area:
                all_items = search_area.find_all('div', recursive=True)
            else:
                # 대체: body의 모든 div
                all_items = soup.find_all('div')
            
            print(f"  → 총 {len(all_items)}개 아이템 발견 (순서 유지)")
            
            for item in all_items:
                try:
                    # 먼저 링크가 있는지 확인 (링크 중심 접근)
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if not url:
                        continue
                    
                    # 디버깅: 모든 링크 출력 (필터링 전)
                    # print(f"  [디버그-원본링크] {url}")
                    
                    # URL 정제 (더 강력하게)
                    if '/url?q=' in url:
                        # /url?q= 또는 google.com/url?q= 모두 처리
                        url = url.split('/url?q=')[1].split('&')[0]
                    elif '/aclk?' in url:
                        # 구글 광고 리다이렉트: adurl= 파라미터에서 실제 목적지 추출
                        if 'adurl=' in url:
                            url = url.split('adurl=')[1].split('&')[0]
                    
                    # URL 디코딩
                    from urllib.parse import unquote
                    url = unquote(url)
                    
                    # http로 시작하지 않으면 건너뜀
                    if not url.startswith('http'):
                        print(f"  [http아님] {url}")
                        continue
                    
                    # 구글 링크 전부 제외 (정제 후에 체크)
                    if 'google.com' in url or 'goo.gl' in url:
                        print(f"  [구글링크제외] {url}")
                        continue
                    
                    # aria-expanded 팝업/드롭다운 내부 링크 제외
                    # 링크의 부모 요소들을 탐색하면서 aria-expanded 확인
                    is_in_popup = False
                    current_elem = link_elem
                    for _ in range(10):  # 최대 10단계 부모까지 확인
                        parent = current_elem.find_parent() if current_elem else None
                        if not parent:
                            break
                        
                        # aria-expanded 속성 확인
                        aria_expanded = parent.get('aria-expanded')
                        if aria_expanded is not None:
                            # aria-expanded가 있으면 팝업/드롭다운으로 간주
                            is_in_popup = True
                            if 'samsung' in url.lower():
                                print(f"  [팝업내부링크] {url} (aria-expanded={aria_expanded})")
                            break
                        
                        current_elem = parent
                    
                    if is_in_popup:
                        continue
                    
                    # 이제 링크를 기준으로 제목과 출처 찾기
                    title = ''
                    source = ''
                    
                    # 링크의 부모 컨테이너 찾기
                    container = link_elem.find_parent()
                    
                    # 방법 1: 링크 근처의 heading (가장 정확)
                    if container:
                        heading = container.find(role='heading')
                        if heading:
                            title = heading.get_text(strip=True)
                    
                    # 방법 2: 링크 근처의 line-clamp 스타일 div (뉴스 등)
                    if not title and container:
                        title_elem = container.find('div', attrs={'style': lambda x: x and 'line-clamp' in x})
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                    
                    # 방법 3: 링크의 aria-label
                    if not title:
                        aria_label = link_elem.get('aria-label')
                        if aria_label and len(aria_label) >= 2:  # 2자 이상
                            title = aria_label
                    
                    # 방법 4: 링크 내부의 가장 긴 텍스트
                    if not title:
                        # 링크 내부의 모든 텍스트 요소 찾기
                        inner_texts = []
                        for elem in link_elem.find_all(['div', 'span', 'h1', 'h2', 'h3', 'h4']):
                            text = elem.get_text(strip=True)
                            if len(text) >= 2 and 'http' not in text.lower():
                                inner_texts.append(text)
                        
                        # 가장 긴 텍스트 선택
                        if inner_texts:
                            title = max(inner_texts, key=len)
                    
                    # 방법 5: 링크 전체 텍스트 (마지막 수단)
                    if not title:
                        link_text = link_elem.get_text(strip=True)
                        if len(link_text) >= 2:
                            title = link_text
                    
                    # 제목이 없으면 건너뜀 (빈 문자열만 제외)
                    if not title:
                        print(f"  [제목없음] {url} (제목: '{title}')")
                        continue
                    
                    # 제목 정제: URL 프로토콜 및 불필요한 문자 제거
                    # https:, http:, www. 등 제거
                    title = title.replace('https://', '').replace('http://', '')
                    title = title.replace('https:', '').replace('http:', '')
                    title = title.replace('www.', '')
                    
                    # URL이 제목인 경우 도메인만 추출
                    if '.com' in title or '.net' in title or '.org' in title or '.co.kr' in title:
                        # 도메인에서 이름만 추출
                        domain_parts = title.split('/')[0].split('.')
                        if len(domain_parts) >= 2:
                            title = domain_parts[0]  # samsung.com -> samsung
                    
                    # 제목이 없으면 건너뜀 (빈 문자열만 제외)
                    if not title:
                        print(f"  [제목없음-정제후] {url} (제목: '{title}')")
                        continue
                    
                    # ========================================
                    # 여기까지 통과하면 유효한 링크!
                    # 이제 position 증가 및 중복 체크
                    # ========================================
                    
                    valid_link_position += 1  # 유효한 링크만 카운트
                    
                    # 1순위: 연속 중복 체크 (바로 이전 항목과 URL이 같으면 무조건 제거)
                    if url == last_collected_url:
                        if 'samsung' in url.lower() and 'tablet' in title.lower():
                            print(f"  [연속중복-samsung] {url} (제목: {title})")
                        else:
                            print(f"  [연속중복] {url} (제목: {title})")
                        continue
                    
                    # 2순위: 위치 기반 중복 체크 (URL + 제목 조합으로 같은 구간 내 중복 제거)
                    item_key = (url, title)  # URL + 제목 조합
                    
                    if item_key in processed_items:
                        last_position = processed_items[item_key]
                        distance = valid_link_position - last_position
                        
                        # 거리가 threshold 이내면 같은 구간 (중복 제거)
                        if distance < position_threshold:
                            print(f"  [구간중복] {url} - {title} (거리: {distance})")
                            continue
                    
                    # 현재 위치 저장
                    processed_items[item_key] = valid_link_position
                    last_collected_url = url
                    last_collected_title = title
                    
                    # 출처는 항상 URL 도메인에서 추출 (가장 정확함)
                    from urllib.parse import urlparse
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc.replace('www.', '')
                        
                        # 도메인을 더 읽기 쉽게 변환
                        # 예: news.naver.com -> 네이버 뉴스, m.inews24.com -> inews24
                        if 'naver.com' in domain:
                            source = '네이버'
                        elif 'daum.net' in domain:
                            source = '다음'
                        elif 'google.com' in domain:
                            source = '구글'
                        else:
                            # 일반 도메인: 서브도메인 제거하고 메인 도메인만
                            parts = domain.split('.')
                            if len(parts) >= 2:
                                # co.kr, com 등 제거
                                if parts[-1] in ['kr', 'com', 'net', 'org']:
                                    if len(parts) >= 3 and parts[-2] in ['co', 'or', 'go', 'ac']:
                                        source = parts[-3]  # samsung.co.kr -> samsung
                                    else:
                                        source = parts[-2]  # samsung.com -> samsung
                                else:
                                    source = parts[-1]
                            else:
                                source = domain
                    except:
                        source = '알 수 없음'
                    
                    # 타입 자동 구분 (HTML 구조 기반)
                    result_type = '일반'
                    
                    # 1순위: HTML 구조로 "주요 뉴스" 체크
                    # 링크 요소에서 부모로 올라가면서 형제 요소 중 "주요 뉴스" 헤더 찾기
                    is_major_news = False
                    current = link_elem
                    
                    for level in range(5):  # 최대 5단계까지만 올라감
                        parent = current.find_parent() if current else None
                        if not parent:
                            break
                        
                        # 현재 부모의 형제 요소들 중에서 "주요 뉴스" 텍스트가 있는 헤더 찾기
                        # 형제 요소는 같은 레벨에 있는 요소들
                        siblings = parent.find_previous_siblings() + parent.find_next_siblings()
                        
                        for sibling in siblings:
                            # span, div 등에서 "주요 뉴스" 텍스트 찾기
                            sibling_spans = sibling.find_all('span', limit=10)  # 최대 10개만 확인
                            for span in sibling_spans:
                                span_text = span.get_text(strip=True)
                                if span_text == '주요 뉴스' or span_text == '주요뉴스':
                                    is_major_news = True
                                    break
                            
                            if is_major_news:
                                break
                        
                        if is_major_news:
                            break
                        
                        current = parent
                    
                    if is_major_news:
                        result_type = '주요뉴스'
                    
                    # 2순위: HTML 구조로 "광고" 체크
                    if result_type == '일반':
                        is_ad = False
                        current = link_elem
                        
                        for level in range(5):  # 최대 5단계까지만 체크
                            parent = current.find_parent() if current else None
                            if not parent:
                                break
                            
                            # 부모의 형제 요소 중에서 "광고" 관련 텍스트 찾기
                            siblings = parent.find_previous_siblings() + parent.find_next_siblings()
                            
                            for sibling in siblings:
                                # 형제 요소의 직접적인 텍스트만 확인 (하위 요소 제외)
                                sibling_spans = sibling.find_all('span', limit=5)
                                for span in sibling_spans:
                                    span_text = span.get_text(strip=True)
                                    # "광고" 또는 "광고: 검색 결과" 정확히 매칭
                                    if span_text == '광고' or '광고:' in span_text or '광고 ·' in span_text:
                                        is_ad = True
                                        break
                                
                                if is_ad:
                                    break
                            
                            if is_ad:
                                break
                            
                            current = parent
                        
                        if is_ad:
                            result_type = '광고'
                    
                    # 3순위: 동영상
                    if result_type == '일반':
                        # YouTube 동영상 판별 (watch 포함 여부)
                        if 'youtube.com' in url:
                            if '/watch' in url:
                                result_type = '동영상'
                            # /watch 없으면 일반으로 유지
                        # YouTube 단축 URL
                        elif 'youtu.be/' in url:
                            result_type = '동영상'
                        # 틱톡 동영상
                        elif 'tiktok.com' in url and '/video/' in url:
                            result_type = '동영상'
                    
                    # 4순위: SNS
                    if result_type == '일반':
                        if 'instagram.com' in url or 'facebook.com' in url:
                            result_type = 'SNS'
                    
                    general_results.append({
                        'title': title,
                        'url': url,
                        'snippet': source,
                        'source': source,
                        'thumbnail': '',
                        'position': len(general_results) + 1,  # 실제 저장되는 결과 기준으로 1부터 순서 부여
                        'result_type': result_type,
                        'published_date': '',
                        'is_ad': is_ad
                    })
                    
                    print(f"  [{result_type:6s}] {len(general_results)}. {source:20s} - {title}")
                    
                except Exception as e:
                    print(f"  ⚠️ 아이템 처리 중 오류: {e}")
                    continue
            
            print(f"[1단계 완료] 모든 링크 {len(general_results)}개 수집")
            
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
                
                prev_url = None  # 연속 중복 체크용 변수 초기화
                img_count = 0
                for link in image_links:
                    try:
                        img_count += 1
                        
                        # 제목은 aria-label
                        title = link.get('aria-label', '').strip()
                        url = link.get('href', '')
                        
                        print(f"  [디버그 {img_count}] title={title}")
                        print(f"    → 원본 URL: {url}")
                        
                        # 제목이 없으면 "제목 없음"으로 표시
                        if not title or len(title) < 2:
                            title = "제목 없음"
                            print(f"    → 제목 없음 (그래도 수집)")
                        
                        # URL 정제
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                            print(f"    → 정제된 URL: {url}")
                        
                        # 유효성 검사 (최소한만)
                        if not url.startswith('http'):
                            print(f"    → http로 시작하지 않음 - 건너뜀")
                            continue
                        
                        # 구글 자체 서비스 링크 제외
                        google_services = [
                            'accounts.google.com',
                            'maps.google.com',
                            'support.google.com',
                            'search.app.goo.gl',
                            'policies.google.com',
                            'myaccount.google.com',
                            'play.google.com',
                            'mail.google.com',
                            'drive.google.com',
                            'calendar.google.com',
                            'translate.google.com',
                            'photos.google.com',
                            'news.google.com',
                            'shopping.google.com'
                        ]
                        
                        if any(service in url for service in google_services):
                            print(f"    → 구글 서비스 링크 제외")
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
                            source = '알 수 없음'
                        
                        # 출처가 없어도 수집
                        if not source:
                            source = '알 수 없음'
                            print(f"    → 출처 없음 (그래도 수집)")
                        
                        # 연속 중복 체크: 바로 직전 URL과 같으면 건너뜀
                        if url == prev_url:
                            print(f"    → 연속 중복 제거 (이미지): {url}")
                            continue
                        
                        result_type = '이미지'
                        
                        # 현재 URL 저장 (다음 반복에서 비교용)
                        prev_url = url
                        
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
                        
                        print(f"  ✅ [이미지 {position}] {source} - {title}")
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
        # 뉴스 도메인이면 광고 아님 (우선 제외)
        news_domains = [
            'news.naver.com', 'news.daum.net', 'news.google.com',
            'chosun.com', 'joongang.co.kr', 'donga.com', 'hankyung.com',
            'mk.co.kr', 'edaily.co.kr', 'mt.co.kr', 'etnews.com',
            'newsis.com', 'ytn.co.kr', 'sbs.co.kr', 'kbs.co.kr', 'mbc.co.kr',
            'jtbc.co.kr', 'news1.kr', 'newspim.com', 'inews24.com',
            'biz.chosun.com', 'thelec.kr', 'bloter.net', 'zdnet.co.kr',
            'v.daum.net', 'm.news.nate.com', 'mobile.newsis.com',
            'foeconomy.co.kr', 'theguru.co.kr', 'beyondpost.co.kr',
            'newsspace.kr', 'g-enews.com', 'seoulfn.com', 'investchosun.com',
            'biz.newdaily.co.kr', 'news.einfomax.co.kr', 'techm.kr',
            'biz.sbs.co.kr', 'kr.investing.com', 'm.sedaily.com',
            'm.ytn.co.kr', 'm.inews24.com'
        ]
        
        if any(domain in url for domain in news_domains):
            return False  # 뉴스는 광고 아님
        
        # URL 패턴 체크
        for pattern in self.AD_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # HTML 요소에서 광고 표시 체크
        if element:
            # 요소 자체의 텍스트 체크
            element_text = element.get_text()
            if '광고' in element_text or 'Ad' in element_text or 'Sponsored' in element_text:
                return True
            
            # 부모 요소들을 여러 단계 체크 (최대 5단계)
            current = element
            for _ in range(5):
                parent = current.find_parent() if current else None
                if not parent:
                    break
                
                parent_text = parent.get_text()
                # "광고" 텍스트가 앞쪽에 있는지 체크 (처음 200자)
                if '광고' in parent_text[:200]:
                    return True
                
                # 광고 관련 클래스나 속성 체크
                parent_class = parent.get('class', [])
                if parent_class:
                    class_str = ' '.join(parent_class)
                    if 'ad' in class_str.lower() or 'sponsor' in class_str.lower():
                        return True
                
                # data 속성 체크
                for attr in parent.attrs:
                    if 'ad' in attr.lower() or 'sponsor' in attr.lower():
                        return True
                
                current = parent
        
        return False





class YouTubeMobileCrawler(MobileCrawler):
    """유튜브 모바일 검색 크롤러 (일반 동영상 + Shorts)"""
    
    def crawl(self, keyword, max_regular=15, max_shorts_shelves=2, shorts_per_shelf=4, screenshot_path=None):
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
            
            # 이미지 로드 대기 (추가)
            print("[유튜브 크롤링] 썸네일 이미지 로딩 대기 중...")
            try:
                # 이미지가 로드될 때까지 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                # 추가 대기 시간 (이미지가 실제로 로드되도록)
                time.sleep(3)
                print("[유튜브 크롤링] 이미지 로드 완료")
            except Exception as e:
                print(f"[경고] 이미지 로드 대기 중 오류: {e}")
            
            # 스크린샷 저장 - 조금씩 스크롤하면서 이미지 로드 후 캡처
            if screenshot_path:
                try:
                    import base64
                    
                    print("[유튜브 크롤링] 스크린샷 준비: 이미지 로드를 위한 스크롤 시작...")
                    
                    # 1단계: 최상단으로 이동
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # 2단계: 조금씩 스크롤 (필요한 만큼만)
                    scroll_step = 350  # 350px씩 작게 스크롤
                    max_scrolls = 20   # 최대 20회 스크롤 (약 7000px, 충분한 양)
                    current_position = 0
                    
                    print(f"  → 스크롤 간격: {scroll_step}px, 최대: {max_scrolls}회")
                    
                    for i in range(max_scrolls):
                        current_position += scroll_step
                        self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                        print(f"  [스크롤 {i+1}/{max_scrolls}] 위치: {current_position}px")
                    
                    # 3단계: 마지막 대기 (모든 이미지 로드 완료)
                    print("  → 이미지 로드 대기 중...")
                    time.sleep(3)
                    
                    # 4단계: 다시 최상단으로 이동
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # 5단계: 스크린샷 영역 계산 (스크롤한 만큼만)
                    screenshot_height = current_position + 915  # 마지막 스크롤 위치 + 뷰포트 높이
                    width = 412  # 모바일 너비 고정
                    
                    print(f"[유튜브 크롤링] 스크린샷 크기: {width}x{screenshot_height}")
                    
                    # 6단계: CDP를 사용하여 스크린샷 캡처 (스크롤한 영역만)
                    screenshot = self.driver.execute_cdp_cmd('Page.captureScreenshot', {
                        'clip': {
                            'width': width,
                            'height': screenshot_height,
                            'x': 0,
                            'y': 0,
                            'scale': 1
                        },
                        'captureBeyondViewport': True
                    })
                    
                    # Base64 디코딩 후 파일로 저장
                    with open(screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(screenshot['data']))
                    
                    print(f"[유튜브 크롤링] 스크린샷 저장 완료: {screenshot_path}")
                except Exception as e:
                    print(f"[유튜브 크롤링] 스크린샷 저장 실패: {e}")
                    import traceback
                    traceback.print_exc()
            
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
                # 스크롤 후 이미지 로딩을 위한 대기 시간 증가
                time.sleep(3)
                
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
                            print(f"  [일반 영상 {video_count}/{max_regular}] {video_data['title']}")
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
        
        print(f"    [디버그] {len(shorts_in_shelf)}개 Shorts 발견 (정확히 {shorts_per_shelf}개 수집)")
        
        collected_count = 0
        for short in shorts_in_shelf:
            # 정확히 shorts_per_shelf(4)개만 수집
            if collected_count >= shorts_per_shelf:
                break
            
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
                
                # 중복 체크 (제거하지 않고 플래그만 설정)
                is_duplicate = video_id in processed_video_ids
                
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
                
                # 중복이 아닐 때만 processed_video_ids에 추가
                if not is_duplicate:
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
                    'is_duplicate': is_duplicate,
                    'short_shelf_index': 0,
                    'position_in_shelf': 0
                })
                
                collected_count += 1
                print(f"      [Shorts {collected_count}/{shorts_per_shelf}] {title} {'[중복]' if is_duplicate else ''}")
                
            except Exception as e:
                print(f"    [Shorts 파싱 오류] {e}")
                continue
        
        return shelf_data


def get_google_suggestions(keyword):
    """구글 자동완성 검색어 가져오기"""
    import requests
    
    url = "http://suggestqueries.google.com/complete/search"
    params = {
        "q": keyword,
        "client": "chrome",
        "hl": "ko"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        suggestions = response.json()[1]  # 두 번째 요소가 검색어 리스트
        return suggestions[:10]  # 상위 10개
    except Exception as e:
        print(f"[구글 자동완성 오류] {e}")
        return []


def get_youtube_suggestions(keyword):
    """유튜브 자동완성 검색어 가져오기"""
    import requests
    import json
    
    url = "http://suggestqueries.google.com/complete/search"
    params = {
        "q": keyword,
        "client": "youtube",
        "ds": "yt",
        "hl": "ko"
    }
    
    try:
        print(f"[DEBUG] 유튜브 자동완성 요청: {keyword}")
        response = requests.get(url, params=params, timeout=5)
        print(f"[DEBUG] 응답 상태: {response.status_code}")
        print(f"[DEBUG] 응답 내용 (처음 200자): {response.text[:200]}")
        
        # JSONP 형식 처리: window.google.ac.h(...) 제거
        text = response.text
        text = text.replace('window.google.ac.h(', '').rstrip(')')
        
        # JSON 파싱
        data = json.loads(text)
        print(f"[DEBUG] 파싱된 데이터 구조: {type(data)}, 길이: {len(data)}")
        
        # 중첩 배열에서 검색어만 추출: [["검색어", 0, [512]], ...] -> ["검색어", ...]
        suggestions = [item[0] for item in data[1] if isinstance(item, list) and len(item) > 0]
        print(f"[DEBUG] 추출된 검색어 개수: {len(suggestions)}")
        print(f"[DEBUG] 검색어 목록: {suggestions}")
        
        return suggestions[:10]
    except Exception as e:
        print(f"[유튜브 자동완성 오류] {e}")
        import traceback
        traceback.print_exc()
        return []


def crawl_all(keyword, google_screenshot_path=None, youtube_screenshot_path=None):
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
    results['google'] = google_crawler.crawl(keyword, screenshot_path=google_screenshot_path)
    
    # 유튜브 크롤링 (일반 15개 + Shorts 2구간x5개)
    print(f"\n{'='*50}")
    print(f"유튜브 검색 시작: {keyword}")
    print(f"{'='*50}")
    youtube_crawler = YouTubeMobileCrawler()
    results['youtube'] = youtube_crawler.crawl(keyword, max_regular=15, max_shorts_shelves=2, shorts_per_shelf=5, screenshot_path=youtube_screenshot_path)
    
    return results
