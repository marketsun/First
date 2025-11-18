"""
구글 크롤러 V2 - 테스트 버전
모든 링크를 수집하는 새로운 방식
기존 crawler.py는 건드리지 않음
"""

import sys
import io

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, unquote

class GoogleCrawlerV2:
    """구글 검색 크롤러 V2 - 모든 링크 수집"""
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        # chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_experimental_option("detach", True)
        
        # 모바일 에뮬레이션
        mobile_emulation = {
            "deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 2.625},
            "userAgent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def crawl(self, keyword):
        """
        구글 검색 크롤링 - 새로운 방식
        모든 <a> 태그를 찾아서 검색 결과 링크만 필터링
        """
        try:
            self.setup_driver()
            url = f"https://www.google.com/search?q={keyword}&hl=ko"
            
            print(f"=" * 60)
            print(f"[구글 V2] 크롤링 시작: {keyword}")
            print(f"[구글 V2] URL: {url}")
            print(f"=" * 60)
            
            self.driver.get(url)
            print("  페이지 로딩 대기 중...")
            time.sleep(5)  # 더 긴 대기
            
            # 페이지 로드 확인
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("  페이지 로드 완료")
            except:
                print("  ⚠️ 페이지 로드 대기 시간 초과")
            
            # 스크롤
            print("\n[구글 V2] 스크롤 중...")
            for i in range(5):  # 스크롤 횟수 증가
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 더 긴 대기
                print(f"  스크롤 {i+1}회 완료")
            
            print("\n[구글 V2] 페이지 파싱 시작...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 전략: 모든 <a> 태그를 찾고, 검색 결과 링크만 필터링
            all_links = soup.find_all('a', href=True)
            print(f"  → 총 {len(all_links)}개 <a> 태그 발견")
            
            results = []
            processed_urls = {}  # {(url, position): result_type}
            position = 1
            
            print(f"\n[구글 V2] 링크 분석 중...")
            
            # 디버그: 처음 10개 href 출력
            print(f"\n[디버그] 처음 10개 href 샘플:")
            for i, link in enumerate(all_links[:10], 1):
                href = link.get('href', '')
                print(f"  {i}. {href[:100]}")
            
            for idx, link in enumerate(all_links, 1):
                try:
                    href = link.get('href', '')
                    
                    # 구글 검색 결과 링크만 처리
                    # /url?q= 또는 /url?sa=로 시작하는 링크
                    if not (href.startswith('/url?q=') or href.startswith('/url?sa=')):
                        continue
                    
                    # URL 추출 및 정제
                    url = href
                    if '/url?q=' in url:
                        url = url.split('/url?q=')[1].split('&')[0]
                    elif '/url?sa=' in url:
                        # /url?sa=t&url= 형태
                        if '&url=' in url:
                            url = url.split('&url=')[1].split('&')[0]
                        else:
                            continue
                    
                    # URL 디코딩
                    try:
                        url = unquote(url)
                    except:
                        pass
                    
                    # 유효성 검사
                    if not url.startswith('http'):
                        continue
                    
                    # 제목 찾기 (여러 방법 시도)
                    title = ''
                    
                    # 방법 1: 링크 내부 텍스트
                    title = link.get_text(strip=True)
                    
                    # 방법 2: aria-label
                    if not title or len(title) < 2:
                        title = link.get('aria-label', '')
                    
                    # 방법 3: 부모에서 제목 찾기
                    if not title or len(title) < 2:
                        parent = link.find_parent()
                        if parent:
                            # role="heading" 찾기
                            heading = parent.find(role='heading')
                            if heading:
                                title = heading.get_text(strip=True)
                            
                            # data-snf="GuLy6c" 찾기
                            if not title:
                                title_div = parent.find('div', {'data-snf': 'GuLy6c'})
                                if title_div:
                                    title = title_div.get_text(strip=True)
                    
                    # 제목이 너무 짧거나 없으면 제외
                    if not title or len(title) < 2:
                        continue
                    
                    # 출처 추출
                    source = ''
                    
                    # 방법 1: 부모에서 출처 찾기
                    parent = link.find_parent()
                    if parent:
                        # data-snf="dqs64d" 찾기
                        source_div = parent.find('div', {'data-snf': 'dqs64d'})
                        if source_div:
                            source_elem = source_div.find('div', class_='GkAmnd')
                            if source_elem:
                                source = source_elem.get_text(strip=True)
                        
                        # 다른 패턴 시도
                        if not source:
                            source_elem = parent.find('div', class_='GkAmnd')
                            if source_elem:
                                source = source_elem.get_text(strip=True)
                    
                    # 방법 2: URL에서 도메인 추출
                    if not source:
                        try:
                            parsed = urlparse(url)
                            source = parsed.netloc.replace('www.', '')
                        except:
                            source = '알 수 없음'
                    
                    # 타입 자동 구분
                    result_type = '일반'
                    
                    if 'youtube.com' in url or 'youtu.be' in url:
                        result_type = '동영상'
                    elif 'instagram.com' in url:
                        result_type = 'SNS'
                    
                    # 이미지 섹션 확인
                    if link.find_parent('div', attrs={'data-attrid': 'images universal'}):
                        result_type = '이미지'
                    
                    # 중복 체크 (URL + position)
                    key = (url, position)
                    if key in processed_urls:
                        continue
                    
                    processed_urls[key] = result_type
                    
                    result = {
                        'title': title,
                        'url': url,
                        'snippet': source,
                        'source': source,
                        'thumbnail': '',
                        'position': position,
                        'result_type': result_type,
                        'published_date': '',
                        'is_ad': False
                    }
                    
                    results.append(result)
                    
                    print(f"  [{result_type:6s}] {position:2d}. {source:20s} - {title[:40]}")
                    
                    position += 1
                    
                except Exception as e:
                    continue
            
            print(f"\n[구글 V2] 크롤링 완료: {len(results)}개 수집")
            
            # 타입별 통계
            type_counts = {}
            for r in results:
                rt = r['result_type']
                type_counts[rt] = type_counts.get(rt, 0) + 1
            
            print(f"\n[구글 V2] 타입별 통계:")
            for rt, count in type_counts.items():
                print(f"  - {rt}: {count}개")
            
            return results
            
        finally:
            if self.driver:
                print(f"\n브라우저를 5초 후 종료합니다...")
                time.sleep(5)
                self.driver.quit()


def test_crawler_v2(keyword):
    """V2 크롤러 테스트"""
    crawler = GoogleCrawlerV2()
    results = crawler.crawl(keyword)
    
    print(f"\n" + "=" * 60)
    print(f"📊 최종 결과")
    print(f"=" * 60)
    print(f"총 수집: {len(results)}개")
    
    print(f"\n📋 전체 목록:")
    for r in results:
        print(f"{r['position']:2d}. [{r['result_type']:6s}] {r['source']:25s} - {r['title'][:50]}")
    
    return results


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 구글 크롤러 V2 테스트")
    print("=" * 60)
    print("특징:")
    print("  - 모든 <a> 태그 검색")
    print("  - /url?q= 패턴으로 필터링")
    print("  - 제목/출처 다양한 방법으로 추출")
    print("  - 타입 자동 구분 (일반/동영상/이미지)")
    print("=" * 60)
    
    # 테스트 키워드 (하드코딩)
    keyword = '삼성'
    print(f"\n테스트 키워드: {keyword}")
    
    results = test_crawler_v2(keyword)
    
    print(f"\n\n✅ 테스트 완료!")
    print(f"V2 방식으로 총 {len(results)}개 링크 수집")

