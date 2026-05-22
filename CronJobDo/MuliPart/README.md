# Video Upload & HLS Streaming Platform

Nền tảng upload video song song với hỗ trợ HLS streaming.

## ✨ Tính năng

- **Upload song song**: Upload video theo chunks với nhiều worker đồng thời (4 parallel)
- **Resume upload**: Tiếp tục upload nếu gián đoạn
- **HLS Streaming**: Chuyển đổi video sang HLS format cho phát trực tiếp
- **Giao diện đẹp**: UI responsive với Tailwind-like styling
- **Quản lý video**: Xem danh sách video, thumbnail, thông tin
- **Video Player**: Phát HLS video in-browser

## 🚀 Cách chạy

### 1. Chuẩn bị môi trường

```powershell
# Cài dependencies (nếu chưa)
pip install -r ../../requirements.txt

# Thêm ffmpeg vào PATH (Windows)
$env:PATH = "$env:PATH;D:\test_gemini\upLoadFileChunk\CronJobDo\ffmpeg-8.1.1-essentials_build\bin"
ffmpeg -version  # kiểm tra
```

### 2. Chuẩn bị Database

Sử dụng MySQL hoặc SQLite:

**Option A: MySQL** (mặc định)
```sql
CREATE DATABASE IF NOT EXISTS chunk_upload_demo CHARACTER SET utf8mb4;
USE chunk_upload_demo;
```

**Option B: SQLite** (dev/test)
Sửa file `UploadMultiPart.py`:
```python
DATABASE_URL = "sqlite:///./upload_demo.db"
```

### 3. Chạy server

```powershell
# Từ thư mục CronJobDo/MuliPart
cd D:\test_gemini\upLoadFileChunk\CronJobDo\MuliPart

# Chạy server
python -m uvicorn UploadMultiPart:app --reload --host 127.0.0.1 --port 8888 --log-level info
```

Server sẽ chạy tại: **http://127.0.0.1:8888**

### 4. Mở giao diện

```powershell
# Mở Client.html in browser
start Client.html
```

Hoặc dùng Live Server (VSCode) để tự động reload.

## 📋 Cách sử dụng

### 📤 Upload Video

1. Nhấp tab **"📤 Upload"**
2. Kéo file vào hoặc nhấp để chọn
3. Nhấp **"Upload"**
4. Chờ hoàn tất + chuyển đổi HLS

Lưu ý:
- Hỗ trợ video format: MP4, MKV, WebM, v.v...
- Nếu upload gián đoạn, nhấp **"Resume"** để tiếp tục
- **"Xóa Session"** để khởi động lại upload

### 🎬 Phát Video

1. Nhấp tab **"🎬 My Videos"**
2. Xem danh sách video đã upload
3. Nhấp **"▶ Phát"** để phát
4. Nhấp vào video hoặc nhấn **ESC** để đóng

## 🛠️ API Endpoints

### Upload APIs

```
POST /upload/init
- body: filename, file_size, content_type
- response: upload_id, chunk_size, total_parts

POST /upload/{upload_id}/chunk/{part_number}
- body: chunk file
- response: part_number, size, hash, status

GET /upload/{upload_id}/status
- response: uploaded_parts, missing_parts, file_size, ...

POST /upload/{upload_id}/complete
- response: upload_id, status, final_path

POST /upload/{upload_id}/ffmpeg/check
- response: valid, error/message

POST /upload/{upload_id}/ffmpeg/thumbnail
- response: thumbnail_path
```

### HLS APIs

```
POST /video/{upload_id}/convert-hls
- Chuyển đổi video sang HLS
- response: video_id, status, playlist_url, duration

GET /video/list
- Liệt kê tất cả video HLS
- response: { videos: [...], total: N }

GET /video/{video_id}/playlist.m3u8
- Phục vụ HLS playlist

GET /video/{video_id}/segment/{segment}
- Phục vụ HLS segment (.ts file)

GET /video/{video_id}/info
- Lấy thông tin video

GET /video/{video_id}/thumbnail
- Lấy thumbnail video
```

## 📁 Cấu trúc thư mục

```
MuliPart/
├── Client.html                 # Giao diện web
├── UploadMultiPart.py          # Backend API
├── README.md                   # File này
│
../temp_uploads/               # Chunks tạm thời
../final_uploads/              # Video hoàn chỉnh
../thumbnails/                 # Ảnh thumbnail
../hls_videos/                 # HLS segments
```

## ⚙️ Cấu hình

File `UploadMultiPart.py`:

```python
CHUNK_SIZE = 5 * 1024 * 1024       # 5 MB per chunk
CONCURRENCY = 4                     # 4 workers song song (trong Client.html)
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/chunk_upload_demo"
```

## 🔧 Khắc phục sự cố

### Lỗi: "ffmpeg not found"
```powershell
# Thêm ffmpeg vào PATH
$env:PATH = "$env:PATH;D:\path\to\ffmpeg\bin"
ffmpeg -version
```

### Lỗi: "Database connection failed"
- Kiểm tra MySQL đang chạy
- Kiểm tra credentials trong DATABASE_URL
- Hoặc chuyển sang SQLite: `sqlite:///./upload_demo.db`

### Lỗi: "HLS conversion failed"
- Kiểm tra file video hợp lệ
- Kiểm tra disk space
- Kiểm tra quyền ghi vào `../hls_videos/`

### Video không phát
- Kiểm tra HLS playlist tồn tại: `../hls_videos/{video_id}/playlist.m3u8`
- Kiểm tra segments tồn tại: `../hls_videos/{video_id}/segment_*.ts`
- Dùng browser console (F12) để xem lỗi

## 📊 Hiệu suất

- **Upload**: 4 chunks song song × 5 MB/chunk = 20 MB mỗi lần gửi
- **HLS**: Chia video thành segments ~10 giây mỗi segment
- **Player**: Hỗ trợ adaptive streaming (tùy bandwidth)

## 🎓 Thông tin kỹ thuật

- **Frontend**: HTML5 + Vanilla JavaScript (không dependencies)
- **Backend**: FastAPI + SQLAlchemy + FFmpeg
- **Streaming**: HLS (HTTP Live Streaming)
- **Protocol**: HTTP/CORS enabled

## 📝 License

MIT

## 📧 Support

Nếu gặp vấn đề, kiểm tra:
- Console browser (F12) để xem error
- Server logs (terminal)
- Database logs (MySQL/SQLite)

