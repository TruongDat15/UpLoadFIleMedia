#!/usr/bin/env python3
"""
Script xóa các bản ghi HLS video cũ có path tương đối
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/chunk_upload_demo"

def reset_database():
    """Xóa tất cả HLS videos và upload sessions để reset"""
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            # Xóa HLS videos
            result1 = conn.execute(text("SELECT COUNT(*) as cnt FROM hls_videos"))
            count1 = result1.fetchone()[0]
            print(f"Tìm thấy {count1} HLS videos")

            conn.execute(text("DELETE FROM hls_videos"))
            conn.commit()
            print(f"✅ Đã xóa {count1} HLS videos")

            # Xóa upload parts
            result2 = conn.execute(text("SELECT COUNT(*) as cnt FROM upload_parts"))
            count2 = result2.fetchone()[0]
            print(f"\nTìm thấy {count2} upload parts")

            conn.execute(text("DELETE FROM upload_parts"))
            conn.commit()
            print(f"✅ Đã xóa {count2} upload parts")

            # Xóa upload sessions
            result3 = conn.execute(text("SELECT COUNT(*) as cnt FROM upload_sessions"))
            count3 = result3.fetchone()[0]
            print(f"\nTìm thấy {count3} upload sessions")

            conn.execute(text("DELETE FROM upload_sessions"))
            conn.commit()
            print(f"✅ Đã xóa {count3} upload sessions")

            print("\n" + "=" * 50)
            print("✅ ĐÃ RESET DATABASE THÀNH CÔNG!")
            print("=" * 50)
            print("\nBây giờ bạn có thể:")
            print("1. Upload video mới")
            print("2. Chạy test lại: python test_video_streaming.py")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("  RESET DATABASE - XÓA CÁC BẢN GHI CŨ")
    print("=" * 60)

    reset_database()

