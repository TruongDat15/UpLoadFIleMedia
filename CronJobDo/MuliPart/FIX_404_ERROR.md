# 🔧 FIX LỖI 404 - KHÔNG HIỂN THỊ ĐƯỢC VIDEO

## 📋 Tóm tắt vấn đề
Server trả lỗi 404 khi cố gắng xem video đã upload vì 3 lý do chính:

### ❌ **Vấn đề 1: Đường dẫn tương đối không đáng tin cậy**
```python
# ❌ CŨ - Sai
TEMP_DIR = Path("../temp_uploads")
HLS_DIR = Path("../hls_videos")
```
- Đường dẫn tương đối phụ thuộc vào **working directory** của server
- Khi chạy từ directory khác => không tìm thấy file

### ❌ **Vấn đề 2: Không verify HLS conversion thành công**
- FFmpeg có thể chạy nhưng không tạo ra segments
- Server tưởng video sẵn sàng nhưng file không tồn tại

### ❌ **Vấn đề 3: Endpoint segment không hỗ trợ tất cả format request**
- HLS player request segment theo nhiều cách khác nhau
- Endpoint chỉ hỗ trợ một format duy nhất

---

## ✅ Các sửa chữa đã áp dụng

### 1️⃣ **Dùng đường dẫn tuyệt đối**
```python
# ✅ MỚI - Đúng
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent.parent  # Thư mục upLoadFileChunk

TEMP_DIR = BASE_DIR / "temp_uploads"
FINAL_DIR = BASE_DIR / "final_uploads"
THUMB_DIR = BASE_DIR / "thumbnails"
HLS_DIR = BASE_DIR / "hls_videos"
```
✓ Luôn resolve đúng path bất kể ở đâu chạy

### 2️⃣ **Verify HLS conversion**
```python
# ✅ Kiểm tra playlist + segments được tạo
def convert_to_hls(video_path: str, output_dir: Path, video_id: str) -> bool:
    # ... FFmpeg conversion ...
    
    # ✅ Verify playlist được tạo
    if not playlist_path.exists():
        print(f"ERROR: Playlist not created at {playlist_path}")
        return False
    
    # ✅ Verify segments được tạo
    segments = list(output_dir.glob("segment_*.ts"))
    if not segments:
        print(f"ERROR: No segments created in {output_dir}")
        return False
```
✓ Tránh lưu video "READY" khi chưa have segments

### 3️⃣ **Hỗ trợ nhiều format request**
```python
@app.get("/video/{video_id}/segment/{segment}")
@app.get("/video/{video_id}/{segment}")  # ✅ Thêm fallback route
def get_hls_segment(video_id: str, segment: str):
    # ...
```
✓ HLS player có thể request `/segment/xxx` hoặc `/xxx`

### 4️⃣ **Thêm static files serving cho HLS**
```python
# ✅ Mount HLS directory
if HLS_DIR.exists():
    app.mount("/hls", StaticFiles(directory=str(HLS_DIR)), name="hls")
```
✓ Cho phép direct access đến HLS files

### 5️⃣ **Thêm debug logging**
```python
print(f"[DEBUG] Looking for playlist: {playlist_path}")
print(f"[DEBUG] Playlist exists: {playlist_path.exists()}")
print(f"[DEBUG] Available files in HLS dir: {[f.name for f in available]}")
```
✓ Giúp dễ debug khi có vấn đề

---

## 🔍 CÁCH DEBUG VẤN ĐỀ

### 1. Kiểm tra trạng thái hệ thống
```bash
curl http://localhost:8888/debug/system-info
```

**Response mẫu:**
```json
{
  "script_dir": "D:\\test_gemini\\upLoadFileChunk\\CronJobDo\\MuliPart",
  "base_dir": "D:\\test_gemini\\upLoadFileChunk",
  "hls_dir": "D:\\test_gemini\\upLoadFileChunk\\hls_videos",
  "hls_dir_exists": true,
  "temp_dir_exists": true,
  "final_dir_exists": true
}
```

✓ Đảm bảo `hls_dir_exists: true`

### 2. Liệt kê tất cả videos
```bash
curl http://localhost:8888/debug/videos
```

**Response mẫu:**
```json
{
  "videos": [
    {
      "video_id": "16ea83c9-d610-4c94-b718-731f36275efd",
      "filename": "video.mp4",
      "status": "READY",
      "hls_path_exists": true,
      "playlist_exists": true,
      "segment_count": 2,
      "duration": 30
    }
  ],
  "total": 1
}
```

✓ Kiểm tra:
- `status` = "READY"
- `hls_path_exists` = true
- `playlist_exists` = true
- `segment_count` > 0

### 3. Xem logs trong server console
```
[DEBUG] Looking for playlist: D:\test_gemini\upLoadFileChunk\hls_videos\16ea83c9-d610-4c94-b718-731f36275efd\playlist.m3u8
[DEBUG] Playlist exists: True
[OK] Serving segment: D:\test_gemini\upLoadFileChunk\hls_videos\16ea83c9-d610-4c94-b718-731f36275efd\segment_000.ts
```

---

## 🚀 QUY TRÌNH HOÀN CHỈNH

### Để xem được video, làm theo đúng thứ tự này:

```
1. Upload video (tạo upload_id)
   POST /upload/init → upload_id

2. Upload chunks
   POST /upload/{upload_id}/chunk/{part_number}

3. Hoàn tất upload
   POST /upload/{upload_id}/complete

4. Convert sang HLS
   POST /video/{upload_id}/convert-hls → video_id

5. Xem danh sách video
   GET /video/list

6. Xem video
   GET /video/{video_id}/playlist.m3u8
   (Các segment tự động load)
```

---

## 📝 TEST CLIENT

Tạo file `test_video_streaming.py`:

```python
import requests
import time

BASE_URL = "http://localhost:8888"

# 1. Check system info
print("=== System Info ===")
response = requests.get(f"{BASE_URL}/debug/system-info")
print(response.json())

# 2. List debug videos
print("\n=== Debug Videos ===")
response = requests.get(f"{BASE_URL}/debug/videos")
print(response.json())

# 3. List ready videos
print("\n=== Ready Videos ===")
response = requests.get(f"{BASE_URL}/video/list")
videos = response.json()
print(f"Found {videos['total']} videos")

for video in videos['videos']:
    print(f"\nVideo: {video['filename']}")
    print(f"  ID: {video['video_id']}")
    print(f"  Playlist URL: {video['playlist_url']}")
    print(f"  Thumbnail URL: {video['thumbnail_url']}")
```

Chạy:
```bash
python test_video_streaming.py
```

---

## ✨ Các endpoint cải tiến

| Endpoint | Mục đích |
|----------|---------|
| `GET /debug/system-info` | Kiểm tra cấu hình đường dẫn ✅ |
| `GET /debug/videos` | Xem tất cả videos + tình trạng file ✅ |
| `GET /video/list` | Xem videos sẵn sàng |
| `GET /video/{video_id}/playlist.m3u8` | Lấy HLS playlist |
| `GET /video/{video_id}/{segment}` | Lấy segment (fallback) ✅ |
| `GET /video/{video_id}/info` | Thông tin video |
| `GET /video/{video_id}/thumbnail` | Thumbnail video |

---

## ⚠️ Nếu vẫn lỗi 404

1. **Kiểm tra `/debug/system-info`**
   - Tất cả `_exists` phải `true`
   - Nếu không → xem quyền file

2. **Kiểm tra `/debug/videos`**
   - `segment_count > 0` ?
   - `playlist_exists: true` ?
   - Nếu không → HLS conversion fail → check logs

3. **Xem server console**
   - Có error message nào không?
   - FFmpeg có fail không?

4. **Xem filesystem**
   - File có trong `hls_videos/{video_id}/` không?
   - Có `playlist.m3u8` không?
   - Có `segment_*.ts` không?

---

## 📚 Tham khảo

- HLS (HTTP Live Streaming): Chuẩn Apple để stream video
- Segments: Các file `.ts` nhỏ thay vì một file lớn
- Playlist: File `.m3u8` liệt kê thứ tự segments
- StaticFiles: FastAPI mounting thư mục để serve static files

