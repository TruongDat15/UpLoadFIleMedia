# FFmpeg Pipeline

## FFmpeg lam gi trong he thong upload video

Sau khi video duoc upload xong, backend thuong khong nen tra ngay la video da san sang. File goc can duoc xu ly bat dong bo:

- Lay metadata bang `ffprobe`.
- Tao thumbnail.
- Chuyen ma video sang dinh dang phu hop.
- Kiem tra file co doc duoc khong.
- Cap nhat record `Media` sang `COMPLETE` hoac `FAIL`.

Trong model hien tai, cac trang thai nam o `Server/models/media_model.py`:

```python
class Status(IntEnum):
    PENDING = 0
    CONVERTING = 1
    COMPLETE = 2
    FAIL = 3
```

Day la nen tang de tach upload ra khoi xu ly FFmpeg.

## FFmpeg va ffprobe khac nhau the nao

| Cong cu | Muc dich |
| --- | --- |
| `ffprobe` | Doc metadata: duration, stream, codec, width, height, bitrate |
| `ffmpeg` | Xu ly media: cat, resize, transcode, tao thumbnail, copy stream |

Nen dung `ffprobe` truoc khi xu ly nang. Neu `ffprobe` khong doc duoc file, kha nang cao file hong hoac sai dinh dang.

## Quy trinh xu ly khuyen nghi

```text
Lay media status=PENDING
  -> doi status=CONVERTING
  -> download object tu MinIO ve file tam
  -> ffprobe de validate va lay metadata
  -> ffmpeg tao thumbnail/transcode neu can
  -> upload ket qua len MinIO
  -> cap nhat thumb_path/status=COMPLETE
  -> neu loi: status=FAIL va log ly do
```

## Tao thumbnail bang FFmpeg

Lenh pho bien:

```bash
ffmpeg -ss 00:00:01 -i input.mp4 -frames:v 1 -q:v 2 thumbnail.jpg
```

Y nghia:

- `-ss 00:00:01`: lay frame o giay thu 1.
- `-i input.mp4`: file dau vao.
- `-frames:v 1`: chi lay mot frame video.
- `-q:v 2`: chat luong anh tot, so cang nho chat luong cang cao.

Neu video rat ngan, co the lay tai `00:00:00` hoac tinh vi tri theo duration.

## Stream copy va transcode

Stream copy:

```bash
ffmpeg -i input.mkv -c copy output.mp4
```

FFmpeg chi doi container neu codec phu hop. Cach nay nhanh vi khong decode/encode.

Transcode:

```bash
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac output.mp4
```

Transcode ton CPU hon nhung tao file dau ra on dinh hon cho web/mobile.

## Cac tham so hay dung

| Tham so | Y nghia |
| --- | --- |
| `-i` | Input file |
| `-ss` | Seek den thoi diem can xu ly |
| `-frames:v 1` | Lay mot frame video |
| `-vf scale=...` | Filter resize video/anh |
| `-c copy` | Copy stream, khong transcode |
| `-c:v libx264` | Encode video H.264 |
| `-c:a aac` | Encode audio AAC |
| `-crf` | Chat luong video khi encode x264/x265 |
| `-preset` | Toc do encode va kha nang nen |

## Goi tu Python

Project da co dependency `ffmpeg-python`. Co the dung:

```python
import ffmpeg

probe_data = ffmpeg.probe("input.mp4")

(
    ffmpeg
    .input("input.mp4", ss=1)
    .output("thumbnail.jpg", vframes=1, **{"q:v": 2})
    .overwrite_output()
    .run()
)
```

Khi chay trong worker, nen bat loi:

```python
try:
    ffmpeg.probe("input.mp4")
except ffmpeg.Error as exc:
    error_text = exc.stderr.decode("utf-8", errors="replace")
```

## Luu y ve tai nguyen

FFmpeg la process rieng va dung CPU/RAM/disk I/O kha nang. Khong nen xu ly qua nhieu video cung luc tren mot may nho.

De an toan:

- Gioi han so job `CONVERTING` song song.
- Dung timeout cho moi lenh FFmpeg.
- Luu file tam vao thu muc rieng va don sau khi xu ly.
- Log stderr cua FFmpeg khi fail.
- Khong chay command bang string ghep tay neu co input tu user; dung argument list hoac API thu vien.
