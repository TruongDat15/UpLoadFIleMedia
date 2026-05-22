# 📑 Bắt đầu ở đây!

Chào mừng đến nền tảng **Video Upload & HLS Streaming**!

## 🚀 Bắt đầu nhanh (5 phút)

1. **Đọc**: [`QUICKSTART.md`](./QUICKSTART.md) - Hướng dẫn khởi động trong 5 phút
2. **Chạy**: `python -m uvicorn UploadMultiPart:app --reload --port 8888`
3. **Mở**: Trình duyệt → `Client.html` hoặc `http://127.0.0.1:8888/`
4. **Upload**: Kéo file video vào giao diện

## 📚 Tài liệu

| File | Nội dung |
|------|---------|
| **[QUICKSTART.md](./QUICKSTART.md)** | ⚡ Khởi động nhanh, setup server, test |
| **[README.md](./README.md)** | 📖 Hướng dẫn chi tiết, cấu hình, troubleshooting |
| **[FEATURES.md](./FEATURES.md)** | ✨ Danh sách tính năng, API endpoints, tech stack |
| **[INDEX.md](./INDEX.md)** | 📑 File này |

## 🎯 Thứ tự đọc (theo mức độ)

### Mức 1: Muốn chạy ngay (5-10 phút)
```
1. QUICKSTART.md
2. Mở Client.html
3. Upload video test
```

### Mức 2: Muốn hiểu toàn bộ (30 phút)
```
1. README.md (Architecture + API endpoints)
2. FEATURES.md (Tính năng chi tiết)
3. UploadMultiPart.py (Code backend)
4. Client.html (Code frontend)
```

### Mức 3: Muốn customize/deploy (1+ giờ)
```
1. README.md (Production setup)
2. UploadMultiPart.py (Thử sửa config)
3. Client.html (Thử sửa giao diện)
4. test_api.py (Thử test API)
```

## 📁 Cấu trúc thư mục

```
MuliPart/
├── Client.html              # Giao diện web
├── UploadMultiPart.py       # Backend FastAPI
├── test_api.py              # Script test API
├── README.md                # Hướng dẫn đầy đủ
├── QUICKSTART.md            # Khởi động nhanh
├── FEATURES.md              # Danh sách tính năng
└── INDEX.md                 # File này

../temp_uploads/            # Chunks upload
../final_uploads/           # Video hoàn chỉnh
../thumbnails/              # Ảnh thumbnail
../hls_videos/              # HLS segments
```

## ⚙️ Yêu cầu hệ thống

- **Python**: 3.8+
- **FFmpeg**: Latest version
- **Database**: MySQL hoặc SQLite
- **Browser**: Modern (Chrome, Firefox, Safari)
- **Network**: Upload/download stable

## 🔍 Quick Reference

### Chỉnh sửa cấu hình

**File**: `UploadMultiPart.py` (dòng 15-29)

```python
DATABASE_URL = "sqlite:///./upload_demo.db"  # Dev
CHUNK_SIZE = 5 * 1024 * 1024                # 5 MB
```

### Đổi port

**Lệnh**: Sửa `--port 8888` thành port khác

```powershell
python -m uvicorn UploadMultiPart:app --port 9000
```

### Debug mode

**Thêm**: Logging verbose

```python
# UploadMultiPart.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🐛 Gặp vấn đề?

1. **Server không chạy**: Kiểm tra port 8888 đang bị chiếm?
2. **Lỗi ffmpeg**: Kiểm tra ffmpeg trong PATH
3. **Database error**: Chuyển sang SQLite hoặc check MySQL
4. **HLS không play**: Kiểm tra browser hỗ trợ HLS.js

**Chi tiết**: Xem phần Troubleshooting trong [`README.md`](./README.md)

## 💡 Mẹo

### Test nhanh API

```powershell
python test_api.py
```

### Xem logs realtime

```powershell
# Terminal 1: Server
python -m uvicorn UploadMultiPart:app --log-level debug

# Terminal 2: Browser console (F12)
```

### Reset database

```powershell
# SQLite
rm upload_demo.db  # Tự động tạo lại khi run

# MySQL
DROP DATABASE chunk_upload_demo;
CREATE DATABASE chunk_upload_demo;
```

## 🎓 Mở rộng

### Thêm feature mới

1. Thêm endpoint trong `UploadMultiPart.py`
2. Test với `test_api.py`
3. Thêm UI trong `Client.html`

### Ví dụ: Thêm DELETE video API

```python
@app.delete("/video/{video_id}")
def delete_video(video_id: str):
    # Implementation
    pass
```

## 📞 Hỗ trợ

- 📖 Xem tài liệu chi tiết trong README.md
- 🧪 Chạy test_api.py để kiểm tra
- 💻 Kiểm tra console browser (F12 > Console)
- 🔍 Kiểm tra terminal server logs

## ✅ Checklist khởi động

- [ ] Cài Python 3.8+
- [ ] Cài FFmpeg
- [ ] Cài dependencies: `pip install -r requirements.txt`
- [ ] Cấu hình database (SQLite hoặc MySQL)
- [ ] Chạy server: `uvicorn UploadMultiPart:app --port 8888`
- [ ] Mở Client.html
- [ ] Upload file video test
- [ ] Phát video từ tab "My Videos"

## 🎉 Thành công!

Bây giờ bạn có thể:
- ✅ Upload video lớn với resume
- ✅ Streaming video bằng HLS
- ✅ Quản lý danh sách video
- ✅ Tùy chỉnh theo nhu cầu

Happy coding! 🚀

---

**Phiên bản**: 1.0.0  
**Cập nhật**: May 2026  
**Trạng thái**: Production Ready ✅

