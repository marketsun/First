"""구글 검색 결과 HTML 구조 상세 분석"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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

driver = webdriver.Chrome(options=chrome_options)

try:
    keyword = "핫셀러"
    search_url = f"https://www.google.com/search?q={keyword}"
    driver.get(search_url)
    print(f"[구글 검색] {keyword}")
    
    time.sleep(5)
    
    # 스크롤
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 모든 링크 찾기 (href 속성이 있는 a 태그)
    all_links = soup.find_all('a', href=True)
    
    print(f"\n총 {len(all_links)}개 링크 발견\n")
    print("="*100)
    
    # 일반 링크와 이미지 링크 분석
    general_count = 0
    image_count = 0
    
    for idx, link in enumerate(all_links[:30], 1):  # 처음 30개만
        href = link.get('href', '')
        
        # 구글 내부 링크 제외
        if not href.startswith('/url?') and not href.startswith('http'):
            continue
        
        # 이미지 태그 확인
        img = link.find('img')
        has_image = img is not None
        
        if has_image:
            image_count += 1
            print(f"\n[{idx}] 🖼️ 이미지 링크")
        else:
            general_count += 1
            print(f"\n[{idx}] 📄 일반 링크")
        
        print(f"  href: {href[:80]}")
        
        # aria-label
        aria_label = link.get('aria-label', '')
        if aria_label:
            print(f"  aria-label: {aria_label[:60]}")
        
        # 링크 텍스트
        text = link.get_text(strip=True)[:60]
        if text:
            print(f"  텍스트: {text}")
        
        # 클래스
        classes = link.get('class', [])
        if classes:
            print(f"  클래스: {' '.join(classes)}")
        
        # 부모 구조
        parent = link.find_parent()
        if parent:
            parent_classes = parent.get('class', [])
            if parent_classes:
                print(f"  부모 클래스: {' '.join(parent_classes)}")
            
            # data 속성들
            data_attrs = {k: v for k, v in parent.attrs.items() if k.startswith('data-')}
            if data_attrs:
                print(f"  부모 data 속성: {list(data_attrs.keys())}")
        
        # 이미지가 있으면 이미지 정보
        if has_image:
            print(f"  이미지 alt: {img.get('alt', '')[:60]}")
            print(f"  이미지 src: {img.get('src', '')[:80]}")
        
        print("-" * 100)
    
    print(f"\n\n📊 통계:")
    print(f"  일반 링크: {general_count}개")
    print(f"  이미지 링크: {image_count}개")
    
    # 더 구체적인 패턴 찾기
    print(f"\n\n🔍 패턴 분석:")
    
    # 이미지가 있는 링크들의 공통 구조
    image_links = [link for link in all_links if link.find('img')]
    print(f"\n이미지 링크 {len(image_links)}개의 공통 패턴:")
    
    if image_links:
        # 첫 번째 이미지 링크의 전체 HTML 구조
        print(f"\n첫 번째 이미지 링크 전체 HTML:")
        print(image_links[0].prettify()[:1000])
        
        # 부모 구조
        parent = image_links[0].find_parent()
        if parent:
            print(f"\n부모 요소:")
            print(f"  태그: {parent.name}")
            print(f"  클래스: {parent.get('class', [])}")
            print(f"  data 속성: {[k for k in parent.attrs.keys() if k.startswith('data-')]}")
    
    print("\n\n[대기 중... 브라우저를 확인하고 Enter를 누르세요]")
    input()

except Exception as e:
    print(f"[오류] {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()

