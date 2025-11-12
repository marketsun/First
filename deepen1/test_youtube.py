"""유튜브 모바일 크롤링 테스트 - HTML 구조 파악"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Chrome 옵션 설정
chrome_options = Options()

# 안드로이드 모바일 User-Agent
user_agent = 'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36'
chrome_options.add_argument(f'user-agent={user_agent}')

# 봇 탐지 우회
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# 모바일 화면 크기 (Galaxy S22 Ultra)
chrome_options.add_argument('--window-size=412,915')

# 모바일 에뮬레이션 설정
mobile_emulation = {
    "deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 3.0},
    "userAgent": user_agent
}
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

print("=" * 80)
print("브라우저를 시작합니다... (안드로이드 모바일 모드)")
print("=" * 80)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 검색 키워드
keyword = "모아담다"

# 유튜브 모바일 검색
search_url = f"https://m.youtube.com/results?search_query={keyword}"
print(f"\n🔍 유튜브 모바일 검색 중: {keyword}")
print(f"📍 URL: {search_url}\n")

driver.get(search_url)

print("⏳ 페이지 로딩 중... 10초 대기")
time.sleep(10)

print("\n📜 스크롤하여 Shorts 로드 중...")
for i in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    print(f"   스크롤 {i+1}/5 완료")

print("\n💾 HTML 파일 저장 중...")
# HTML 저장
with open('youtube_mobile.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

print("\n" + "=" * 80)
print("✅ 저장 완료: youtube_mobile.html")
print("=" * 80)
print("\n📋 다음 단계:")
print("1. youtube_mobile.html 파일을 텍스트 에디터로 열기")
print("2. 'shorts' 또는 'reel'로 검색하여 Shorts 관련 요소 찾기")
print("3. 'ytm-reel' 또는 'ytm-shorts'로 시작하는 태그명 확인")
print("4. Shorts 구간의 정확한 HTML 구조 파악")
print("\n🌐 브라우저 창:")
print("- 브라우저는 열어두었습니다")
print("- F12를 눌러 개발자 도구를 열고")
print("- Shorts 영역을 마우스로 선택(Inspect)하여 HTML 구조 확인")
print("- 일반 영상과 Shorts의 차이점 확인")
print("\n⌨️  확인이 끝나면 이 창에서 Enter를 누르세요...")

input()

print("\n🔚 브라우저를 닫습니다...")
driver.quit()
print("완료!")

