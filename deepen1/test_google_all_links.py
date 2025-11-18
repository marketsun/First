"""
구글 검색 결과 - 모든 링크 수집 테스트
필터링을 최소화하고 페이지의 모든 링크를 수집해봅니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    # chrome_options.add_argument('--headless=new')  # 헤드리스 해제
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
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def test_all_links(keyword):
    """모든 링크 수집 테스트"""
    driver = setup_driver()
    
    try:
        url = f"https://www.google.com/search?q={keyword}&hl=ko"
        print(f"=" * 60)
        print(f"테스트 시작: {keyword}")
        print(f"URL: {url}")
        print(f"=" * 60)
        
        driver.get(url)
        time.sleep(3)
        
        # 스크롤
        print("\n[스크롤 중...]")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            print(f"  스크롤 {i+1}회 완료")
        
        print("\n[페이지 파싱 중...]")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 방법 1: kb0PBd 클래스로 모든 아이템 찾기
        all_items = soup.find_all('div', class_='kb0PBd')
        print(f"\n📦 총 {len(all_items)}개 아이템 발견")
        
        results = []
        position = 1
        
        print(f"\n" + "=" * 60)
        print("모든 아이템 분석 시작")
        print("=" * 60)
        
        for idx, item in enumerate(all_items, 1):
            try:
                # 제목 찾기 (여러 방법 시도)
                title = ''
                
                # 방법 1: data-snf="GuLy6c"
                title_container = item.find('div', {'data-snf': 'GuLy6c'})
                if title_container:
                    title_elem = title_container.find('span')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # 방법 2: role="heading"
                if not title:
                    heading = item.find(role='heading')
                    if heading:
                        title = heading.get_text(strip=True)
                
                # 방법 3: 특정 클래스 패턴
                if not title:
                    title_elem = item.find('div', class_='F0FGWb')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                if not title:
                    print(f"\n[아이템 {idx}] ❌ 제목 없음 - 건너뜀")
                    continue
                
                # URL 찾기 (클래스 조건 없이)
                url = ''
                link_elem = None
                
                # 부모를 거슬러 올라가며 <a> 태그 찾기
                parent = item.find_parent(['div', 'a'])
                search_depth = 0
                max_depth = 5
                
                while parent and not link_elem and search_depth < max_depth:
                    # 모든 <a> 태그 찾기 (클래스 조건 없음)
                    link_elem = parent.find('a', href=True)
                    if link_elem:
                        break
                    parent = parent.find_parent(['div'])
                    search_depth += 1
                
                if not link_elem:
                    print(f"\n[아이템 {idx}] ❌ URL 없음")
                    print(f"  제목: {title[:50]}")
                    continue
                
                url = link_elem.get('href', '')
                
                # URL 정제
                original_url = url
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]
                
                # URL 유효성 검사 (최소한만)
                if not url or not url.startswith('http'):
                    print(f"\n[아이템 {idx}] ❌ 유효하지 않은 URL")
                    print(f"  제목: {title[:50]}")
                    print(f"  URL: {url[:80]}")
                    continue
                
                # 출처 찾기
                source = ''
                
                # 방법 1: data-snf="dqs64d"
                source_container = item.find_parent(['div'])
                if source_container:
                    source_div = source_container.find('div', {'data-snf': 'dqs64d'})
                    if source_div:
                        source_elem = source_div.find('div', class_='GkAmnd')
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
                if item.find_parent('div', attrs={'data-attrid': 'images universal'}):
                    result_type = '이미지'
                
                result = {
                    'position': position,
                    'title': title,
                    'url': url,
                    'source': source,
                    'result_type': result_type
                }
                
                results.append(result)
                
                print(f"\n[아이템 {idx}] ✅ 수집 성공")
                print(f"  순서: {position}")
                print(f"  타입: {result_type}")
                print(f"  출처: {source}")
                print(f"  제목: {title[:50]}")
                print(f"  URL: {url[:80]}")
                
                position += 1
                
            except Exception as e:
                print(f"\n[아이템 {idx}] ⚠️ 예외 발생: {e}")
                continue
        
        # 결과 요약
        print(f"\n" + "=" * 60)
        print("📊 수집 결과 요약")
        print(f"=" * 60)
        print(f"총 발견: {len(all_items)}개")
        print(f"수집 성공: {len(results)}개")
        print(f"수집률: {len(results)/len(all_items)*100:.1f}%")
        
        # 타입별 통계
        type_counts = {}
        for r in results:
            rt = r['result_type']
            type_counts[rt] = type_counts.get(rt, 0) + 1
        
        print(f"\n📈 타입별 통계:")
        for rt, count in type_counts.items():
            print(f"  - {rt}: {count}개")
        
        print(f"\n" + "=" * 60)
        print("📋 전체 결과 목록")
        print(f"=" * 60)
        for r in results:
            print(f"{r['position']:2d}. [{r['result_type']:6s}] {r['source']:20s} - {r['title'][:40]}")
        
        return results
        
    finally:
        print(f"\n\n브라우저를 5초 후 종료합니다...")
        time.sleep(5)
        driver.quit()

if __name__ == '__main__':
    # 테스트 키워드
    keyword = '삼성'
    
    print("=" * 60)
    print("🧪 구글 검색 - 모든 링크 수집 테스트")
    print("=" * 60)
    print(f"키워드: {keyword}")
    print(f"목표: 필터링 최소화, 모든 링크 수집")
    print("=" * 60)
    
    results = test_all_links(keyword)
    
    print(f"\n\n✅ 테스트 완료!")
    print(f"총 {len(results)}개 링크 수집됨")

