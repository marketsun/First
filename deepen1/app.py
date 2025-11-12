from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, SearchHistory, GoogleResult, YouTubeResult
from crawler import crawl_all
from datetime import datetime
import os
import sys
import threading

# Windows 콘솔 UTF-8 인코딩 설정 (이모지 및 특수문자 지원)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)

# 데이터베이스 설정
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# 데이터베이스 초기화
db.init_app(app)

# 크롤링 상태 및 로그 저장
crawling_status = {}
crawling_logs = {}  # 크롤링 로그 저장


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """검색 실행"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': '키워드를 입력해주세요.'}), 400
    
    # 크롤링 시작
    try:
        # 크롤링 ID 생성
        crawl_id = f"{keyword}_{datetime.now().timestamp()}"
        crawling_status[crawl_id] = {'status': 'running', 'progress': 0}
        
        # 백그라운드에서 크롤링 실행
        thread = threading.Thread(target=perform_crawling, args=(keyword, crawl_id))
        thread.start()
        
        return jsonify({
            'message': '크롤링을 시작했습니다.',
            'crawl_id': crawl_id
        })
        
    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500


def perform_crawling(keyword, crawl_id):
    """실제 크롤링 수행 (백그라운드)"""
    # 로그 초기화
    crawling_logs[crawl_id] = []
    
    def add_log(message):
        """로그 추가"""
        crawling_logs[crawl_id].append(message)
        print(message)
    
    try:
        add_log(f"=" * 50)
        add_log(f"[시작] 키워드 '{keyword}' 크롤링 시작")
        add_log(f"[DEBUG] crawl_id: {crawl_id}")
        add_log(f"=" * 50)
        
        crawling_status[crawl_id]['progress'] = 10
        add_log(f"[진행] 진행률: 10%")
        
        add_log(f"")
        add_log(f"[1/3] 구글 검색 시작...")
        add_log(f"- URL: https://www.google.com/search?q={keyword}")
        
        # 크롤링 실행
        import sys
        import io
        
        # 표준 출력 캡처
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            results = crawl_all(keyword, google_max=50, youtube_max=50)
            
            # 캡처된 출력 가져오기
            output = captured_output.getvalue()
            sys.stdout = old_stdout
            
            # 캡처된 로그를 라인별로 추가
            for line in output.split('\n'):
                if line.strip():
                    add_log(line)
        except Exception as e:
            sys.stdout = old_stdout
            raise e
        
        add_log(f"")
        add_log(f"[완료] 구글 크롤링 완료: {len(results['google'])}개 결과")
        add_log(f"[완료] 유튜브 크롤링 완료: {len(results['youtube'])}개 결과")
        
        crawling_status[crawl_id]['progress'] = 60
        add_log(f"[진행] 진행률: 60%")
        
        add_log(f"")
        add_log(f"[2/3] 데이터베이스에 저장 중...")
        # 데이터베이스에 저장
        with app.app_context():
            # 검색 기록 생성
            search_history = SearchHistory(keyword=keyword)
            db.session.add(search_history)
            db.session.flush()  # ID 생성
            
            # 구글 결과 저장
            for result in results['google']:
                google_result = GoogleResult(
                    search_id=search_history.id,
                    title=result['title'],
                    url=result['url'],
                    snippet=result.get('snippet', ''),
                    thumbnail=result.get('thumbnail', ''),
                    position=result.get('position', 0),
                    published_date=result.get('published_date', ''),
                    is_ad=result.get('is_ad', False)
                )
                db.session.add(google_result)
            
            crawling_status[crawl_id]['progress'] = 80
            
            # 유튜브 결과 저장
            for result in results['youtube']:
                youtube_result = YouTubeResult(
                    search_id=search_history.id,
                    title=result['title'],
                    url=result['url'],
                    video_id=result.get('video_id', ''),
                    thumbnail=result.get('thumbnail', ''),
                    channel_name=result.get('channel_name', ''),
                    view_count=result.get('view_count', ''),
                    view_count_numeric=result.get('view_count_numeric', 0),
                    upload_date=result.get('upload_date', ''),
                    upload_timestamp=result.get('upload_timestamp'),
                    like_count=result.get('like_count', ''),
                    duration=result.get('duration', ''),
                    position=result.get('position', 0),
                    is_short=result.get('is_short', False),
                    short_shelf_index=result.get('short_shelf_index'),
                    position_in_shelf=result.get('position_in_shelf')
                )
                db.session.add(youtube_result)
            
            db.session.commit()
            
            add_log(f"[완료] 데이터베이스 저장 완료!")
            add_log(f"  - 검색 ID: {search_history.id}")
            add_log(f"  - 구글 결과: {len(results['google'])}개")
            add_log(f"  - 유튜브 결과: {len(results['youtube'])}개")
            
            crawling_status[crawl_id]['progress'] = 80
            add_log(f"[진행] 진행률: 80%")
            
            add_log(f"")
            add_log(f"[3/3] 상태 업데이트 중...")
            crawling_status[crawl_id]['progress'] = 100
            crawling_status[crawl_id]['status'] = 'completed'
            crawling_status[crawl_id]['search_id'] = search_history.id
            
            add_log(f"[DEBUG] 최종 상태:")
            add_log(f"  - status: {crawling_status[crawl_id]['status']}")
            add_log(f"  - search_id: {crawling_status[crawl_id]['search_id']}")
            add_log(f"  - progress: {crawling_status[crawl_id]['progress']}%")
            
            add_log(f"")
            add_log(f"=" * 50)
            add_log(f"[성공] 크롤링 완료!")
            add_log(f"=" * 50)
            
    except Exception as e:
        import traceback
        error_msg = f"[오류] 크롤링 오류: {e}"
        add_log(error_msg)
        add_log(f"[오류] 상세:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                add_log(f"  {line}")
        print(error_msg)
        print(traceback.format_exc())
        crawling_status[crawl_id]['status'] = 'error'
        crawling_status[crawl_id]['error'] = str(e)


@app.route('/crawl-status/<crawl_id>')
def crawl_status(crawl_id):
    """크롤링 상태 확인"""
    status = crawling_status.get(crawl_id, {'status': 'not_found'})
    print(f"[API] /crawl-status/{crawl_id} 호출 - 응답: {status}")
    return jsonify(status)


@app.route('/api/logs/<crawl_id>')
def get_logs(crawl_id):
    """크롤링 로그 조회"""
    logs = crawling_logs.get(crawl_id, [])
    return jsonify({'logs': logs})


@app.route('/results/<int:search_id>')
def results(search_id):
    """검색 결과 페이지"""
    search = SearchHistory.query.get_or_404(search_id)
    return render_template('results.html', search=search)


@app.route('/api/results/<int:search_id>')
def api_results(search_id):
    """검색 결과 API (필터링 지원)"""
    search = SearchHistory.query.get_or_404(search_id)
    
    # 필터 파라미터
    keyword_filter = request.args.get('keyword', '').strip().lower()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort_by', '')  # 'view_asc', 'view_desc', 'date_asc', 'date_desc'
    
    # 구글 결과 필터링
    google_results = search.google_results
    if keyword_filter:
        google_results = [r for r in google_results 
                         if keyword_filter in r.title.lower() or 
                            keyword_filter in r.snippet.lower()]
    
    # 유튜브 결과 필터링
    youtube_results = search.youtube_results
    
    # 키워드 필터
    if keyword_filter:
        youtube_results = [r for r in youtube_results 
                          if keyword_filter in r.title.lower() or 
                             keyword_filter in r.channel_name.lower()]
    
    # 날짜 필터
    if date_from or date_to:
        filtered = []
        for r in youtube_results:
            if r.upload_timestamp:
                if date_from and r.upload_timestamp < datetime.strptime(date_from, '%Y-%m-%d'):
                    continue
                if date_to and r.upload_timestamp > datetime.strptime(date_to, '%Y-%m-%d'):
                    continue
                filtered.append(r)
        youtube_results = filtered
    
    # 정렬
    if sort_by == 'view_asc':
        youtube_results = sorted(youtube_results, key=lambda x: x.view_count_numeric)
    elif sort_by == 'view_desc':
        youtube_results = sorted(youtube_results, key=lambda x: x.view_count_numeric, reverse=True)
    elif sort_by == 'date_asc':
        youtube_results = sorted(youtube_results, key=lambda x: x.upload_timestamp or datetime.min)
    elif sort_by == 'date_desc':
        youtube_results = sorted(youtube_results, key=lambda x: x.upload_timestamp or datetime.min, reverse=True)
    
    return jsonify({
        'keyword': search.keyword,
        'search_date': search.search_date.strftime('%Y-%m-%d %H:%M:%S'),
        'google_results': [r.to_dict() for r in google_results],
        'youtube_results': [r.to_dict() for r in youtube_results]
    })


@app.route('/history')
def history():
    """검색 기록 페이지"""
    searches = SearchHistory.query.order_by(SearchHistory.search_date.desc()).all()
    return render_template('history.html', searches=searches)


@app.route('/api/history')
def api_history():
    """검색 기록 API"""
    searches = SearchHistory.query.order_by(SearchHistory.search_date.desc()).all()
    return jsonify([s.to_dict() for s in searches])


@app.route('/api/history/<int:search_id>', methods=['DELETE'])
def delete_history(search_id):
    """검색 기록 삭제"""
    search = SearchHistory.query.get_or_404(search_id)
    db.session.delete(search)
    db.session.commit()
    return jsonify({'message': '삭제되었습니다.'})


@app.route('/api/history/<int:search_id>', methods=['PUT'])
def update_history(search_id):
    """검색 기록 수정 (키워드 변경)"""
    search = SearchHistory.query.get_or_404(search_id)
    data = request.get_json()
    
    new_keyword = data.get('keyword', '').strip()
    if new_keyword:
        search.keyword = new_keyword
        db.session.commit()
        return jsonify({'message': '수정되었습니다.'})
    
    return jsonify({'error': '키워드를 입력해주세요.'}), 400


# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    import webbrowser
    import threading
    
    def open_browser():
        """서버 시작 후 브라우저 자동 열기"""
        import time
        time.sleep(1.5)  # 서버가 완전히 시작될 때까지 대기
        webbrowser.open('http://localhost:5000')
    
    print("=" * 50)
    print("구글/유튜브 모바일 검색 크롤러 시작")
    print("브라우저가 자동으로 열립니다...")
    print("=" * 50)
    
    # 브라우저를 별도 스레드에서 열기
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)


