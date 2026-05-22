# 📝 CHI TIẾT CÁC THAY ĐỔI - BEFORE & AFTER

## 1️⃣ Import + Đường dẫn (Dòng 1-40)

### ❌ TRƯỚC
```python
import math
import uuid
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# ... imports ...

TEMP_DIR = Path("../temp_uploads")           # ❌ Tương đối
FINAL_DIR = Path("../final_uploads")         # ❌ Tương đối
THUMB_DIR = Path("../thumbnails")           # ❌ Tương đối
HLS_DIR = Path("../hls_videos")              # ❌ Tương đối
```

**Vấn đề:**
- Nếu chạy từ directory khác → Path không resolve đúng
- Ví dụ: Nếu chạy từ `upLoadFileChunk/` → `../hls_videos/` = `hls_videos/`
- Nếu chạy từ `upLoadFileChunk/CronJobDo/` → `../hls_videos/` = `CronJobDo/../hls_videos/`
- Kết quả: File không tìm thấy → 404

### ✅ SAU
```python
import math
import uuid
import hashlib
import subprocess
import os                                      # ✅ Thêm
from pathlib import Path
from datetime import datetime

# ...

from fastapi.staticfiles import StaticFiles  # ✅ Thêm

# ✅ Sử dụng đường dẫn tuyệt đối
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent.parent           # = upLoadFileChunk

TEMP_DIR = BASE_DIR / "temp_uploads"
FINAL_DIR = BASE_DIR / "final_uploads"
THUMB_DIR = BASE_DIR / "thumbnails"
HLS_DIR = BASE_DIR / "hls_videos"
```

**Lợi ích:**
- ✅ `Path(__file__)` = File hiện tại
- ✅ `.parent.parent` = Thư mục `upLoadFileChunk` (không phụ thuộc vào nơi chạy)
- ✅ Tất cả paths luôn chính xác

**Ví dụ:**
- Script tại: `D:\test_gemini\upLoadFileChunk\CronJobDo\MuliPart\UploadMultiPart.py`
- SCRIPT_DIR = `D:\test_gemini\upLoadFileChunk\CronJobDo\MuliPart\`
- BASE_DIR = `D:\test_gemini\upLoadFileChunk\`
- HLS_DIR = `D:\test_gemini\upLoadFileChunk\hls_videos\`

---

## 2️⃣ Mount Static Files (Dòng ~100)

### ❌ TRƯỚC
```python
app = FastAPI()
app.add_middleware(CORSMiddleware, ...)
# Không có static file serving
```

### ✅ SAU
```python
app = FastAPI()
app.add_middleware(CORSMiddleware, ...)

# ✅ Thêm static files serving
if HLS_DIR.exists():
    app.mount("/hls", StaticFiles(directory=str(HLS_DIR)), name="hls")
```

**Lợi ích:**
- ✅ Cho phép direct access: `http://localhost:8888/hls/{video_id}/segment_000.ts`
- ✅ Hiệu suất tốt hơn (FastAPI optimize static files)
- ✅ Fallback route nếu endpoint fail

---

## 3️⃣ HLS Conversion - Verify (Dòng 382-412)

### ❌ TRƯỚC
```python
def convert_to_hls(video_path: str, output_dir: Path, video_id: str) -> bool:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        playlist_path = output_dir / "playlist.m3u8"
        
        (ffmpeg
         .input(video_path)
         .output(str(playlist_path), ...)
         .overwrite_output()
         .run(capture_stdout=True, capture_stderr=True, quiet=False)
        )
        
        return True  # ❌ Giả sử thành công mà không check
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
```

**Vấn đề:**
- FFmpeg chạy xong không có nghĩa là tạo được playlist & segments
- Nếu video dài 1 giờ → segments có thể chưa tạo xong
- Code return `True` nhưng file vẫn không tồn tại → 404

### ✅ SAU
```python
def convert_to_hls(video_path: str, output_dir: Path, video_id: str) -> bool:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        playlist_path = output_dir / "playlist.m3u8"
        
        (ffmpeg
         .input(video_path)
         .output(str(playlist_path), ...)
         .overwrite_output()
         .run(capture_stdout=True, capture_stderr=True, quiet=False)
        )
        
        # ✅ Verify playlist được tạo
        if not playlist_path.exists():
            print(f"ERROR: Playlist not created at {playlist_path}")
            return False
        
        # ✅ Verify segments được tạo
        segments = list(output_dir.glob("segment_*.ts"))
        if not segments:
            print(f"ERROR: No segments created in {output_dir}")
            return False
        
        print(f"✓ Playlist created: {playlist_path}")
        print(f"✓ Segments created: {len(segments)}")
        
        return True
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
```

**Lợi ích:**
- ✅ Check xem playlist có được tạo không
- ✅ Check xem có segments không (phải > 0)
- ✅ In log chi tiết để debug

---

## 4️⃣ Playlist Endpoint (Dòng 494-515)

### ❌ TRƯỚC
```python
@app.get("/video/{video_id}/playlist.m3u8")
def get_hls_playlist(video_id: str):
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(
            video_id=video_id, 
            status="READY"
        ).first()
        
        if not hls_video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        playlist_path = Path(hls_video.playlist_path)
        
        if not playlist_path.exists():
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        return FileResponse(...)
    finally:
        db.close()
```

**Vấn đề:**
- Lỗi 404 nhưng không biết là DB không có hay file không tồn tại
- Khó debug

### ✅ SAU
```python
@app.get("/video/{video_id}/playlist.m3u8")
def get_hls_playlist(video_id: str):
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(
            video_id=video_id, 
            status="READY"
        ).first()
        
        if not hls_video:
            print(f"[404] Video not found in DB: {video_id}")  # ✅ Log
            raise HTTPException(status_code=404, detail="Video not found")
        
        playlist_path = Path(hls_video.playlist_path)
        
        print(f"[DEBUG] Looking for playlist: {playlist_path}")  # ✅ Log
        print(f"[DEBUG] Playlist exists: {playlist_path.exists()}")  # ✅ Log
        
        if not playlist_path.exists():
            raise HTTPException(status_code=404, detail=f"Playlist not found: {playlist_path}")
        
        return FileResponse(...)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Playlist error: {e}")  # ✅ Log exception
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

**Lợi ích:**
- ✅ Log chi tiết để biết lỗi ở đâu
- ✅ Xử lý exception (nếu file access fail)
- ✅ Trả về thông tin path trong error (giúp debug)

---

## 5️⃣ Segment Endpoint (Dòng 600-641)

### ❌ TRƯỚC
```python
@app.get("/video/{video_id}/segment/{segment}")
def get_hls_segment(video_id: str, segment: str):
    # Chỉ support 1 format: /video/{video_id}/segment/{segment}
    # HLS player có thể request: /video/{video_id}/{segment}
    # → 404 endpoint not found
```

**Vấn đề:**
- HLS player request segment theo nhiều format:
  - `/video/{video_id}/segment/segment_000.ts` ✓
  - `/video/{video_id}/segment_000.ts` ✗
  - `/video/{video_id}/segment_000.ts` (relative from m3u8) ✗

### ✅ SAU
```python
@app.get("/video/{video_id}/segment/{segment}")
@app.get("/video/{video_id}/{segment}")  # ✅ Thêm fallback
def get_hls_segment(video_id: str, segment: str):
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(
            video_id=video_id, 
            status="READY"
        ).first()
        
        if not hls_video:
            print(f"[404] Video not found: {video_id}")  # ✅ Log
            raise HTTPException(status_code=404, detail="Video not found")
        
        hls_path = Path(hls_video.hls_path)
        segment_path = hls_path / segment
        
        print(f"[DEBUG] HLS Path: {hls_path}")              # ✅ Log
        print(f"[DEBUG] Requesting segment: {segment}")    # ✅ Log
        print(f"[DEBUG] Full segment path: {segment_path}") # ✅ Log
        print(f"[DEBUG] Path exists: {segment_path.exists()}")  # ✅ Log
        
        # ✅ List available segments khi segfault
        if hls_path.exists():
            available = list(hls_path.glob("*"))
            print(f"[DEBUG] Available files: {[f.name for f in available]}")
        
        if not segment_path.exists():
            print(f"[404] Segment not found: {segment_path}")  # ✅ Log
            raise HTTPException(status_code=404, detail=f"Segment not found: {segment}")
        
        print(f"[OK] Serving segment: {segment_path}")  # ✅ Log success
        return FileResponse(segment_path, ...)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Segment error: {e}")  # ✅ Log exception
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

**Lợi ích:**
- ✅ Support 2 route patterns → tức linh hoạt hơn
- ✅ Log chi tiết khi request segment
- ✅ List available files khi file không tìm thấy
- ✅ Dễ debug

---

## 6️⃣ Debug Endpoints (Dòng 495-541) - ✅ THÊM MỚI

### ✅ Endpoint mới: `/debug/system-info`
```python
@app.get("/debug/system-info")
def debug_system_info():
    """Debug: Kiểm tra trạng thái hệ thống"""
    return {
        "script_dir": str(SCRIPT_DIR),
        "base_dir": str(BASE_DIR),
        "temp_dir": str(TEMP_DIR),
        "temp_dir_exists": TEMP_DIR.exists(),
        "final_dir": str(FINAL_DIR),
        "final_dir_exists": FINAL_DIR.exists(),
        "hls_dir": str(HLS_DIR),
        "hls_dir_exists": HLS_DIR.exists(),
        "thumb_dir": str(THUMB_DIR),
        "thumb_dir_exists": THUMB_DIR.exists(),
    }
```

**Dùng để:**
- Kiểm tra tất cả paths được resolve đúng không
- Kiểm tra tất cả thư mục tồn tại không

---

### ✅ Endpoint mới: `/debug/videos`
```python
@app.get("/debug/videos")
def debug_videos():
    """Debug: Kiểm tra tất cả videos trong DB"""
    db = SessionLocal()
    try:
        videos = db.query(HLSVideo).all()
        result = []
        
        for v in videos:
            hls_path = Path(v.hls_path)
            segments = list(hls_path.glob("segment_*.ts")) if hls_path.exists() else []
            playlist_exists = (hls_path / "playlist.m3u8").exists() if hls_path.exists() else False
            
            result.append({
                "video_id": v.video_id,
                "filename": v.original_filename,
                "status": v.status,
                "hls_path": v.hls_path,
                "hls_path_exists": hls_path.exists(),
                "playlist_exists": playlist_exists,
                "segment_count": len(segments),
                "duration": v.duration,
                "created_at": v.created_at.isoformat() if v.created_at else None
            })
        
        return {"videos": result, "total": len(result)}
    finally:
        db.close()
```

**Dùng để:**
- Xem tất cả videos trong DB
- Kiểm tra status từng video
- Kiểm tra file từng video có tồn tại không
- Kiểm tra có bao nhiêu segments

---

## 📊 TÓMERARY COMPARISON

| Aspect | Trước ❌ | Sau ✅ |
|--------|---------|--------|
| Paths | Tương đối | Tuyệt đối |
| HLS verify | Không có | Có (playlist + segments) |
| Segment routes | 1 pattern | 2 patterns (fallback) |
| Static files | Không mount | Mount /hls |
| Logging | Cơ bản | Chi tiết (DEBUG, ERROR, OK) |
| Debug endpoints | Không có | 2 endpoints (/debug/system-info, /debug/videos) |
| Error handling | Cơ bản | Toàn diện (try-except-finally) |

---

## 🧪 Kiểm tra thay đổi

Trước khi và sau khi cập nhật, chạy:

```bash
# Kiểm tra syntax
python -m py_compile UploadMultiPart.py

# Chạy test
python test_video_streaming.py

# Hoặc test endpoints
curl http://localhost:8888/debug/system-info
curl http://localhost:8888/debug/videos
```

---

## ✨ Tóm lại

| Thay đổi | Vấn đề giải quyết |
|----------|------------------|
| Đường dẫn tuyệt đối | Path not found 404 |
| HLS verify | Lưu video chưa có segments |
| Segment routes x2 | HLS player không tìm được segments |
| Static files mounting | Direct file serving không hoạt động |
| Detailed logging | Khó debug lỗi |
| Debug endpoints | Không biết status chi tiết |

**Kết quả:** Lỗi 404 được khắc phục! 🎉

