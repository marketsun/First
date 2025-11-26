from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class SearchHistory(db.Model):
    """검색 기록 모델"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 스크린샷 경로 추가
    google_screenshot = db.Column(db.Text, nullable=True)  # 구글 검색 스크린샷 경로
    youtube_screenshot = db.Column(db.Text, nullable=True)  # 유튜브 검색 스크린샷 경로
    
    # 관련검색어 기능
    related_search_enabled = db.Column(db.Boolean, default=False)  # 관련검색어 토글 상태
    google_related_searches = db.Column(db.Text, nullable=True)  # JSON: 구글 관련검색어 목록
    youtube_related_searches = db.Column(db.Text, nullable=True)  # JSON: 유튜브 관련검색어 목록
    
    # 관계 설정
    google_results = db.relationship('GoogleResult', backref='search', lazy=True, cascade='all, delete-orphan')
    youtube_results = db.relationship('YouTubeResult', backref='search', lazy=True, cascade='all, delete-orphan')
    related_results = db.relationship('RelatedSearchResult', backref='search', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'search_date': self.search_date.strftime('%Y-%m-%d %H:%M:%S'),
            'google_count': len(self.google_results),
            'youtube_count': len(self.youtube_results),
            'google_screenshot': self.google_screenshot,
            'youtube_screenshot': self.youtube_screenshot
        }


class GoogleResult(db.Model):
    """구글 검색 결과 모델"""
    __tablename__ = 'google_results'
    
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('search_history.id'), nullable=False)
    
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    snippet = db.Column(db.Text)
    source = db.Column(db.String(200))  # 출처
    thumbnail = db.Column(db.Text)
    position = db.Column(db.Integer)  # 검색 순위
    result_type = db.Column(db.String(20), default='일반')  # 타입: 일반/이미지
    published_date = db.Column(db.String(100))  # 게시일 (있는 경우)
    is_ad = db.Column(db.Boolean, default=False)  # 광고 여부
    media_type = db.Column(db.String(20), default='earned')  # 미디어 타입: owned/earned
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'thumbnail': self.thumbnail,
            'position': self.position,
            'result_type': self.result_type,
            'published_date': self.published_date,
            'is_ad': self.is_ad,
            'media_type': self.media_type
        }


class YouTubeResult(db.Model):
    """유튜브 검색 결과 모델"""
    __tablename__ = 'youtube_results'
    
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('search_history.id'), nullable=False)
    
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    video_id = db.Column(db.String(50))
    thumbnail = db.Column(db.Text)
    channel_name = db.Column(db.String(200))
    view_count = db.Column(db.String(50))  # "1.2만 회" 형태로 저장
    view_count_numeric = db.Column(db.Integer)  # 정렬용 숫자 값
    upload_date = db.Column(db.String(100))  # "1일 전", "2023.11.10" 등
    upload_timestamp = db.Column(db.DateTime)  # 정렬용 날짜
    like_count = db.Column(db.String(50))
    duration = db.Column(db.String(20))  # 영상 길이
    position = db.Column(db.Integer)  # 검색 순위 (전체 순서)
    is_short = db.Column(db.Boolean, default=False)  # Shorts 여부
    short_shelf_index = db.Column(db.Integer, nullable=True)  # Shorts 구간 번호 (1, 2, ...)
    position_in_shelf = db.Column(db.Integer, nullable=True)  # 구간 내 순서 (1~5)
    media_type = db.Column(db.String(20), default='earned')  # 미디어 타입: owned/earned
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'video_id': self.video_id,
            'thumbnail': self.thumbnail,
            'channel_name': self.channel_name,
            'view_count': self.view_count,
            'view_count_numeric': self.view_count_numeric,
            'upload_date': self.upload_date,
            'upload_timestamp': self.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.upload_timestamp else None,
            'like_count': self.like_count,
            'duration': self.duration,
            'position': self.position,
            'is_short': self.is_short,
            'short_shelf_index': self.short_shelf_index,
            'position_in_shelf': self.position_in_shelf,
            'media_type': self.media_type
        }


class RelatedSearchResult(db.Model):
    """관련검색어별 검색 결과 모델"""
    __tablename__ = 'related_search_results'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_search_id = db.Column(db.Integer, db.ForeignKey('search_history.id'), nullable=False)
    keyword = db.Column(db.String(200), nullable=False)  # 관련검색어
    source = db.Column(db.String(50), nullable=False)  # 'google' 또는 'youtube'
    results = db.Column(db.Text, nullable=False)  # JSON: 검색 결과 리스트
    screenshot_path = db.Column(db.Text, nullable=True)  # 스크린샷 경로
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'source': self.source,
            'results': json.loads(self.results) if self.results else [],
            'screenshot_path': self.screenshot_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


