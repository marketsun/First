"""
테스트용 Flask 앱
포트 5001에서 실행되며, 구글 크롤링 개선 버전을 테스트합니다.
기존 app.py (포트 5000)는 건드리지 않습니다.
"""

from flask import Flask, render_template, request, jsonify
from models import db, SearchHistory, GoogleResult, YouTubeResult
from datetime import datetime
import os
import sys
import threading
import io

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)

# 데이터베이스 설정 (기존과 동일)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database_test.db')  # 별도 DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-secret-key'

# 데이터베이스 초기화
db.init_app(app)

# 크롤링 상태 및 로그 저장
crawling_status = {}
crawling_logs = {}


@app.route('/')
def index():
    """테스트 메인 페이지"""
    return render_template('index_test.html')


@app.route('/search', methods=['POST'])
def search():
    """검색 실행 (구글만 테스트)"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': '키워드를 입력해주세요.'}), 400
    
    try:
        crawl_id = f"{keyword}_{datetime.now().timestamp()}"
        crawling_status[crawl_id] = {'status': 'running', 'progress': 0}
        
        # 백그라운드에서 크롤링 실행
        thread = threading.Thread(target=perform_crawling_test, args=(keyword, crawl_id))
        thread.start()
        
        return jsonify({
            'message': '테스트 크롤링을 시작했습니다.',
            'crawl_id': crawl_id
        })
        
    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500


def perform_crawling_test(keyword, crawl_id):
    """실제 크롤링 수행 (테스트 버전 - 구글만)"""
    crawling_logs[crawl_id] = []
    
    def add_log(message):
        crawling_logs[crawl_id].append(message)
        print(message)
    
    try:
        add_log(f"=" * 50)
        add_log(f"[테스트] 키워드 '{keyword}' 크롤링 시작")
        add_log(f"=" * 50)
        
        crawling_status[crawl_id]['progress'] = 10
        
        # 구글 크롤링만 실행 (개선된 버전)
        from crawler_test import GoogleCrawlerTest
        
        add_log(f"[1/2] 구글 검색 시작 (개선 버전)...")
        
        crawler = GoogleCrawlerTest()
        google_results = crawler.crawl(keyword)
        
        add_log(f"[완료] 구글 크롤링 완료: {len(google_results)}개 결과")
        
        crawling_status[crawl_id]['progress'] = 60
        
        add_log(f"[2/2] 데이터베이스에 저장 중...")
        
        # 데이터베이스에 저장
        with app.app_context():
            search_history = SearchHistory(keyword=keyword)
            db.session.add(search_history)
            db.session.flush()
            
            # 구글 결과 저장
            for result in google_results:
                google_result = GoogleResult(
                    search_id=search_history.id,
                    title=result['title'],
                    url=result['url'],
                    snippet=result.get('snippet', ''),
                    source=result.get('source', ''),
                    thumbnail=result.get('thumbnail', ''),
                    position=result.get('position', 0),
                    result_type=result.get('result_type', '일반'),
                    published_date=result.get('published_date', ''),
                    is_ad=result.get('is_ad', False)
                )
                db.session.add(google_result)
            
            db.session.commit()
            
            add_log(f"[완료] 데이터베이스 저장 완료!")
            add_log(f"  - 검색 ID: {search_history.id}")
            add_log(f"  - 구글 결과: {len(google_results)}개")
            
            crawling_status[crawl_id]['progress'] = 100
            crawling_status[crawl_id]['status'] = 'completed'
            crawling_status[crawl_id]['search_id'] = search_history.id
            
            add_log(f"=" * 50)
            add_log(f"[성공] 테스트 크롤링 완료!")
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
    return jsonify(status)


@app.route('/api/logs/<crawl_id>')
def get_logs(crawl_id):
    """크롤링 로그 조회"""
    logs = crawling_logs.get(crawl_id, [])
    return jsonify({'logs': logs})


@app.route('/api/results/<int:search_id>')
def api_results(search_id):
    """검색 결과 API"""
    search = SearchHistory.query.get_or_404(search_id)
    
    return jsonify({
        'keyword': search.keyword,
        'search_date': search.search_date.strftime('%Y-%m-%d %H:%M:%S'),
        'google_results': [r.to_dict() for r in search.google_results],
        'youtube_results': []  # 테스트에서는 유튜브 제외
    })


@app.route('/history')
def history():
    """검색 기록 페이지"""
    searches = SearchHistory.query.order_by(SearchHistory.search_date.desc()).all()
    return render_template('history_test.html', searches=searches)


# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    print("=" * 50)
    print("🧪 테스트 서버 시작 (포트 5001)")
    print("브라우저에서 http://localhost:5001 으로 접속하세요")
    print("메인 서버 (5000)는 그대로 유지됩니다")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)

