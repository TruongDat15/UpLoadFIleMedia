# Quick Start Guide

## 🚀 Khởi động nhanh (Windows PowerShell)

### Bước 1: Kích hoạt virtualenv

```powershell
cd D:\test_gemini\upLoadFileChunk
.\.venv\Scripts\Activate.ps1
```

### Bước 2: Thêm ffmpeg vào PATH

```powershell
$env:PATH = "$env:PATH;D:\test_gemini\upLoadFileChunk\CronJobDo\ffmpeg-8.1.1-essentials_build\bin"
ffmpeg -version  # Kiểm tra
```

### Bước 3: Khởi động server

```powershell
cd D:\test_gemini\upLoadFileChunk\CronJobDo\MuliPart
python -m uvicorn UploadMultiPart:app --reload --host 127.0.0.1 --port 8888 --log-level info
```

Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8888
INFO:     Application startup complete
```

### Bước 4: Mở giao diện

```powershell
# Cách 1: cmd hoặc PowerShell mới
start http://127.0.0.1:8888/

# Cách 2: Mở trực tiếp file Client.html
start D:\test_gemini\upLoadFileChunk\CronJobDo\MuliPart\Client.html
```

## ✅ Kiểm tra hoạt động

### Test Upload

1. Tìm file video test (hoặc dùng file trong `D:\test_gemini\upLoadFileChunk\data\upload\`)
2. Tab "📤 Upload":
   - Kéo file vào hoặc nhấp "Chọn file"
   - Nhấp "Upload"
   - Chờ hoàn tất (tự động convert sang HLS)

### Test Video Playback

1. Tab "🎬 My Videos":
   - Chờ tải danh sách
   - Nhấp "▶ Phát" để phát video
   - Nhấp ESC hoặc nút X để đóng

## 🛠️ Database Options

### Tùy chọn 1: SQLite (dev/test - dễ nhất)

Sửa `UploadMultiPart.py` dòng 15:
```python
DATABASE_URL = "sqlite:///./upload_demo.db"
```

Sau đó restart server - tự động tạo database.

### Tùy chọn 2: MySQL (production)

Kiểm tra MySQL chạy:
```powershell
# Test kết nối
mysql -u root -p -h 127.0.0.1
```

Tạo database:
```sql
CREATE DATABASE IF NOT EXISTS chunk_upload_demo CHARACTER SET utf8mb4;
```

Kiểm tra trong `UploadMultiPart.py`:
```python
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/chunk_upload_demo"
```

## 🐛 Troubleshooting

| Lỗi | Giải pháp |
|-----|---------|
| `ffmpeg not found` | Chạy lệnh PATH trong Bước 2 |
| `Port 8888 already in use` | Đổi port: `--port 9000` |
| `Database connection failed` | Dùng SQLite hoặc check MySQL |
| `HLS conversion failed` | Check ffmpeg, disk space, video valid |
| Video file quá lớn | Sẽ thấy progress upload, bình thường |

## 📊 Thử nghiệm với file đã có

```powershell
# Copy file test từ repo
Copy-Item "D:\test_gemini\upLoadFileChunk\data\upload\video3.mp4" -Destination "C:\Users\$env:USERNAME\Downloads\test.mp4"

# Sau đó upload file test.mp4 từ giao diện
```

## 🎯 Endpoints thử nhanh (curl)

```powershell
# Check server sống
curl http://127.0.0.1:8888/video/list

# Response:
# {"videos":[],"total":0}
```

## 📝 Logs

Kiểm tra logs:
```powershell
# Terminal uvicorn sẽ in logs
# Hoặc check:
# ../logs/app.log (nếu có)
```

## 🎉 Done!

Bây giờ bạn có thể:
- ✅ Upload video với resume
- ✅ Convert sang HLS tự động
- ✅ Phát video trực tiếp
- ✅ Quản lý danh sách video

Happy streaming! 🎬

