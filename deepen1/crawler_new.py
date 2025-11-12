# YouTubeMobileCrawler의 새로운 crawl 메서드

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
                
                # Shorts 구간의 모든 영상 추가
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
        self.close_driver()
    
    return results


def _parse_video(self, element, processed_video_ids):
    """일반 영상 파싱"""
    video_id = self._extract_video_id(element)
    if not video_id or video_id in processed_video_ids:
        return None
    
    # 제목 추출
    title_elem = element.find(['h3', 'h4', 'span'], class_=re.compile(r'(video-title|media-item-headline)'))
    if not title_elem:
        return None
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
            view_count = view_text.replace('조회수 ', '').replace('조회수', '').strip()
            view_count_numeric = self._parse_view_count(view_text)
        elif span.get('role') == 'text' and '전' in text:
            upload_date = text
            upload_timestamp = self._parse_upload_date(text)
    
    # 영상 길이 추출
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
        'position': 0,  # 나중에 설정
        'is_short': False,
        'short_shelf_index': None,
        'position_in_shelf': None
    }


def _parse_shorts_shelf(self, element, processed_video_ids, shorts_per_shelf):
    """Shorts 구간 파싱"""
    shelf_data = []
    shorts_in_shelf = element.find_all('ytm-shorts-lockup-view-model')
    
    for short in shorts_in_shelf[:shorts_per_shelf]:
        try:
            # 링크 추출
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
            
            # 제목 추출
            title = ''
            title_h3 = short.find('h3', class_='shortsLockupViewModelHostMetadataTitle')
            if title_h3:
                title_span = title_h3.find('span', class_='yt-core-attributed-string')
                if title_span:
                    title = title_span.get_text(strip=True)
            
            if not title:
                continue
            
            # 조회수 추출
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
            
            shelf_data.append({
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
                'position': 0,  # 나중에 설정
                'is_short': True,
                'short_shelf_index': 0,  # 나중에 설정
                'position_in_shelf': 0  # 나중에 설정
            })
            
        except Exception as e:
            print(f"    [Shorts 파싱 오류] {e}")
            continue
    
    return shelf_data
