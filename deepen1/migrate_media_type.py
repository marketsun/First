"""
미디어 타입 컬럼 추가 마이그레이션
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일을 찾을 수 없습니다.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # GoogleResult 테이블에 media_type 컬럼 추가
        print("📝 GoogleResult 테이블에 media_type 컬럼 추가 중...")
        cursor.execute("""
            ALTER TABLE google_results 
            ADD COLUMN media_type VARCHAR(20) DEFAULT 'earned'
        """)
        print("✅ GoogleResult 테이블 업데이트 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  GoogleResult.media_type 컬럼이 이미 존재합니다.")
        else:
            print(f"⚠️  GoogleResult 테이블 오류: {e}")
    
    try:
        # YouTubeResult 테이블에 media_type 컬럼 추가
        print("📝 YouTubeResult 테이블에 media_type 컬럼 추가 중...")
        cursor.execute("""
            ALTER TABLE youtube_results 
            ADD COLUMN media_type VARCHAR(20) DEFAULT 'earned'
        """)
        print("✅ YouTubeResult 테이블 업데이트 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  YouTubeResult.media_type 컬럼이 이미 존재합니다.")
        else:
            print(f"⚠️  YouTubeResult 테이블 오류: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 마이그레이션 완료!")

if __name__ == '__main__':
    migrate()

