"""
스크린샷 필드 추가를 위한 데이터베이스 마이그레이션 스크립트
"""
import sqlite3
import os

def migrate_database():
    """데이터베이스에 스크린샷 필드 추가"""
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일이 없습니다. 먼저 앱을 실행하여 데이터베이스를 생성하세요.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # search_history 테이블에 google_screenshot 컬럼 추가
        print("1. google_screenshot 컬럼 추가 중...")
        try:
            cursor.execute("ALTER TABLE search_history ADD COLUMN google_screenshot TEXT")
            print("   ✅ google_screenshot 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️ google_screenshot 컬럼이 이미 존재합니다.")
            else:
                raise
        
        # search_history 테이블에 youtube_screenshot 컬럼 추가
        print("2. youtube_screenshot 컬럼 추가 중...")
        try:
            cursor.execute("ALTER TABLE search_history ADD COLUMN youtube_screenshot TEXT")
            print("   ✅ youtube_screenshot 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ⚠️ youtube_screenshot 컬럼이 이미 존재합니다.")
            else:
                raise
        
        conn.commit()
        print("\n✅ 마이그레이션이 완료되었습니다!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("스크린샷 필드 추가 마이그레이션 시작")
    print("=" * 50)
    print()
    
    migrate_database()
    
    print()
    print("=" * 50)
    print("마이그레이션 완료!")
    print("=" * 50)

