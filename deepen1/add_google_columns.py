"""구글 검색 결과에 source, result_type 컬럼 추가"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # source 컬럼 추가
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE google_results ADD COLUMN source VARCHAR(200)"))
                conn.commit()
                print("✓ source 컬럼 추가 완료")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ source 컬럼이 이미 존재합니다")
                else:
                    raise
        
        # result_type 컬럼 추가
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE google_results ADD COLUMN result_type VARCHAR(20) DEFAULT '일반'"))
                conn.commit()
                print("✓ result_type 컬럼 추가 완료")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ result_type 컬럼이 이미 존재합니다")
                else:
                    raise
        
        # 기존 데이터의 result_type을 '일반'으로 설정
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE google_results SET result_type = '일반' WHERE result_type IS NULL"))
            conn.commit()
            print("✓ 기존 데이터 업데이트 완료")
        
        print("\n✅ 데이터베이스 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

