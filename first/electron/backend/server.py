# -*- coding: utf-8 -*-
import sys
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 부모 디렉토리 경로 설정
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

logger.info(f'부모 디렉토리: {parent_dir}')
logger.info(f'현재 디렉토리: {os.getcwd()}')

# app.py 임포트
try:
    from app import app
    logger.info('✓ app.py 임포트 성공')
except ImportError as e:
    logger.error(f'✗ app.py 임포트 실패: {e}')
    # 임포트 실패시 Flask 앱 직접 생성
    from flask import Flask
    app = Flask(__name__, 
                template_folder=os.path.join(parent_dir, 'templates'),
                static_folder=os.path.join(parent_dir, 'static'))
    logger.info('✓ Flask 앱 직접 생성')

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=3001, help='서버 포트')
    parser.add_argument('--dev', action='store_true', help='개발 모드')
    args = parser.parse_args()
    
    print(f'\n{"="*80}')
    print(f'Electron 백엔드 서버 시작')
    print(f'URL: http://localhost:{args.port}')
    print(f'{"="*80}\n')
    
    try:
        app.run(host='0.0.0.0', port=args.port, debug=args.dev, use_reloader=False)
    except Exception as e:
        logger.error(f'서버 시작 오류: {e}')
