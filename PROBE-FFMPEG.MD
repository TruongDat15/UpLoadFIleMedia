## `ffmpeg.probe()` trong ffmpeg-python

`ffmpeg.probe(file_path)` là hàm dùng để **đọc metadata** của file media (video/audio/image) mà không cần decode toàn bộ nội dung.

---

### Cơ chế hoạt động

Bên dưới, hàm này chạy lệnh `ffprobe` (công cụ đi kèm FFmpeg):

```bash
ffprobe -v quiet -print_format json -show_streams -show_format <file_path>
```

Kết quả được parse thành **Python dict**.

---

### Cấu trúc `probe_data`

```python
probe_data = {
    "streams": [...],   # Danh sách các luồng (video, audio, subtitle...)
    "format":  {...}    # Thông tin tổng quan về container/file
}
```

#### `"format"` – Thông tin file tổng quan

```python
probe_data["format"] = {
    "filename":         "video.mp4",
    "nb_streams":       2,           # Số luồng (1 video + 1 audio)
    "format_name":      "mov,mp4,m4a,3gp,3g2,mj2",
    "duration":         "120.5",     # Giây (dạng string!)
    "size":             "15204352",  # Bytes
    "bit_rate":         "1008000",   # bps
    "tags": {
        "title": "My Video",
        "encoder": "Lavf58.76.100"
    }
}
```

#### `"streams"` – Danh sách luồng

Mỗi phần tử là một stream, có thể là **video** hoặc **audio**:

```python
# Stream VIDEO
{
    "index":          0,
    "codec_type":     "video",
    "codec_name":     "h264",
    "width":          1920,
    "height":         1080,
    "r_frame_rate":   "30/1",      # FPS dạng phân số
    "duration":       "120.5",
    "bit_rate":       "800000",
    "pix_fmt":        "yuv420p",
    "nb_frames":      "3615"
}

# Stream AUDIO
{
    "index":          1,
    "codec_type":     "audio",
    "codec_name":     "aac",
    "sample_rate":    "44100",
    "channels":       2,
    "duration":       "120.5",
    "bit_rate":       "128000"
}
```

---

### Cách truy xuất thông tin thực tế

```python
import ffmpeg

probe_data = ffmpeg.probe("video.mp4")

# --- Lấy thông tin format ---
fmt      = probe_data["format"]
duration = float(fmt["duration"])          # → 120.5 (float)
size_mb  = int(fmt["size"]) / 1024**2      # → MB

# --- Lấy stream video đầu tiên ---
video_stream = next(
    s for s in probe_data["streams"]
    if s["codec_type"] == "video"
)
width    = video_stream["width"]           # → 1920
height   = video_stream["height"]          # → 1080

# Tính FPS từ "30/1"
num, den = map(int, video_stream["r_frame_rate"].split("/"))
fps = num / den                            # → 30.0

# --- Lấy stream audio đầu tiên ---
audio_stream = next(
    s for s in probe_data["streams"]
    if s["codec_type"] == "audio"
)
sample_rate = int(audio_stream["sample_rate"])  # → 44100
channels    = audio_stream["channels"]           # → 2
```

---

### Xử lý lỗi

```python
try:
    probe_data = ffmpeg.probe("file.mp4")
except ffmpeg.Error as e:
    # e.stderr chứa output lỗi từ ffprobe
    print("Lỗi:", e.stderr.decode())
```

Lỗi thường gặp:
| Nguyên nhân | Thông báo |
|---|---|
| File không tồn tại | `No such file or directory` |
| File bị hỏng | `Invalid data found when processing input` |
| FFmpeg chưa cài | `FileNotFoundError` |

---

### Lưu ý quan trọng

> ⚠️ Hầu hết các giá trị số (`duration`, `bit_rate`, `size`, `sample_rate`) trả về dạng **string**, phải ép kiểu thủ công sang `int` hoặc `float` trước khi tính toán.