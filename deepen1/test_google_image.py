"""구글 이미지 링크 HTML 구조 확인"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("detach", True)

# 모바일 에뮬레이션
mobile_emulation = {
    "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
    "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
}
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

# 드라이버 생성
driver = webdriver.Chrome(options=chrome_options)

try:
    # 검색어 설정
    keyword = "아이폰"
    print(f"검색어: {keyword}")
    
    # 구글 검색
    search_url = f"https://www.google.com/search?q={keyword}"
    driver.get(search_url)
    print(f"[구글 검색] URL: {search_url}")
    
    # 페이지 로딩 대기
    time.sleep(5)
    
    # 스크롤
    print("[스크롤 중...]")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # HTML 파싱
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 모든 검색 결과 아이템 찾기
    all_items = soup.find_all('div', {'data-snf': True})
    print(f"\n[발견된 아이템] 총 {len(all_items)}개")
    
    # 일반 링크 찾기
    print("\n" + "="*80)
    print("[일반 링크 분석]")
    print("="*80)
    general_items = soup.find_all('div', {'data-snf': 'GuLy6c'})
    print(f"일반 링크 개수: {len(general_items)}")
    
    for idx, item in enumerate(general_items[:3], 1):
        print(f"\n--- 일반 링크 #{idx} ---")
        title_elem = item.find('span')
        if title_elem:
            print(f"제목: {title_elem.get_text(strip=True)[:50]}")
        
        # 부모에서 URL 찾기
        parent = item.find_parent(['div', 'a'])
        link_elem = None
        depth = 0
        while parent and not link_elem and depth < 10:
            link_elem = parent.find('a', class_='rTyHce', href=True)
            if not link_elem:
                parent = parent.find_parent(['div'])
            depth += 1
        
        if link_elem:
            print(f"URL: {link_elem.get('href', '')[:80]}")
    
    # 이미지 링크 찾기
    print("\n" + "="*80)
    print("[이미지 링크 분석]")
    print("="*80)
    
    # 방법 1: class="HwReM" 찾기
    image_items_1 = soup.find_all('div', class_='HwReM')
    print(f"방법 1 (class='HwReM'): {len(image_items_1)}개")
    
    for idx, item in enumerate(image_items_1[:3], 1):
        print(f"\n--- 이미지 링크 #{idx} (방법1) ---")
        print(f"HTML 구조:\n{item.prettify()[:500]}")
        
        # 제목 찾기
        title_elem = item.find('span', class_='Yt787')
        if title_elem:
            print(f"제목: {title_elem.get_text(strip=True)[:50]}")
        else:
            print("제목을 찾을 수 없음")
        
        # URL 찾기
        link_elem = item.find_parent(['div']).find('a', class_='c30Ztd', href=True) if item.find_parent(['div']) else None
        if link_elem:
            print(f"URL: {link_elem.get('href', '')[:80]}")
        else:
            print("URL을 찾을 수 없음")
    
    # 방법 2: 이미지 관련 다른 클래스 찾기
    print(f"\n\n[다른 이미지 관련 클래스 탐색]")
    
    # 이미지가 포함된 모든 요소 찾기
    img_containers = soup.find_all('div', class_=lambda x: x and 'image' in x.lower() if x else False)
    print(f"'image' 포함 클래스: {len(img_containers)}개")
    
    # 특정 패턴 찾기
    potential_image_links = soup.find_all('a', class_=lambda x: x and ('image' in x.lower() or 'img' in x.lower()) if x else False)
    print(f"이미지 관련 링크: {len(potential_image_links)}개")
    
    if potential_image_links:
        print(f"\n첫 번째 이미지 링크 HTML:\n{potential_image_links[0].prettify()[:500]}")
    
    print("\n\n[대기 중... 브라우저를 확인하고 Enter를 누르세요]")
    input()

except Exception as e:
    print(f"[오류] {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()

