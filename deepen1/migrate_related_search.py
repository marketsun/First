"""
관련검색어 기능을 위한 DB 마이그레이션 스크립트
"""
import sqlite3
import os

def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 데이터베이스 마이그레이션 시작...")
        
        # 1. search_history 테이블에 컬럼 추가
        print("\n[1/2] search_history 테이블에 관련검색어 컬럼 추가 중...")
        
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(search_history)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # related_search_enabled 컬럼 추가
        if 'related_search_enabled' not in existing_columns:
            cursor.execute("""
                ALTER TABLE search_history 
                ADD COLUMN related_search_enabled BOOLEAN DEFAULT 0
            """)
            print("  ✅ related_search_enabled 컬럼 추가 완료")
        else:
            print("  ⏭️  related_search_enabled 컬럼이 이미 존재합니다")
        
        # google_related_searches 컬럼 추가
        if 'google_related_searches' not in existing_columns:
            cursor.execute("""
                ALTER TABLE search_history 
                ADD COLUMN google_related_searches TEXT
            """)
            print("  ✅ google_related_searches 컬럼 추가 완료")
        else:
            print("  ⏭️  google_related_searches 컬럼이 이미 존재합니다")
        
        # youtube_related_searches 컬럼 추가
        if 'youtube_related_searches' not in existing_columns:
            cursor.execute("""
                ALTER TABLE search_history 
                ADD COLUMN youtube_related_searches TEXT
            """)
            print("  ✅ youtube_related_searches 컬럼 추가 완료")
        else:
            print("  ⏭️  youtube_related_searches 컬럼이 이미 존재합니다")
        
        # 2. related_search_results 테이블 생성
        print("\n[2/2] related_search_results 테이블 생성 중...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS related_search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_search_id INTEGER NOT NULL,
                keyword VARCHAR(200) NOT NULL,
                source VARCHAR(50) NOT NULL,
                results TEXT NOT NULL,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_search_id) REFERENCES search_history (id) ON DELETE CASCADE
            )
        """)
        print("  ✅ related_search_results 테이블 생성 완료")
        
        # 변경사항 저장
        conn.commit()
        print("\n✅ 마이그레이션이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

