# Media Processing Worker

## Vi sao can worker

Upload va xu ly video nen la hai viec tach rieng.

Upload can nhanh va on dinh. FFmpeg lai cham, ton CPU, de fail voi file loi. Neu xu ly FFmpeg ngay trong request upload, user phai cho lau va request de timeout.

Kien truc phu hop voi project:

```text
FastAPI upload API
  -> luu object len MinIO
  -> tao Media(status=PENDING)

Worker/Cronjob
  -> lay Media PENDING
  -> doi sang CONVERTING
  -> chay ffprobe/ffmpeg
  -> cap nhat COMPLETE hoac FAIL
```

## State machine

Trang thai hien co:

| Status | Gia tri | Y nghia |
| --- | ---: | --- |
| `PENDING` | 0 | Upload xong, cho xu ly |
| `CONVERTING` | 1 | Worker dang xu ly |
| `COMPLETE` | 2 | Xu ly xong |
| `FAIL` | 3 | Xu ly loi |

Luong chuan:

```text
PENDING -> CONVERTING -> COMPLETE
                     \-> FAIL
```

## Race condition

Neu co nhieu worker chay cung luc, hai worker co the lay cung mot media `PENDING`. Khi do ca hai cung xu ly mot file.

Can co buoc claim job:

1. Bat transaction.
2. Lay record `PENDING`.
3. Doi status sang `CONVERTING`.
4. Commit.
5. Chi worker claim thanh cong moi xu ly.

Voi MySQL, co the dung row lock:

```sql
SELECT *
FROM media
WHERE status = 0 AND file_type = 'video'
ORDER BY id
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

Neu chua dung lock phuc tap, cach don gian la xu ly mot worker duy nhat trong giai do hoc/demo.

## Idempotency

Worker nen duoc thiet ke de chay lai an toan. Vi du:

- Neu thumbnail da ton tai, co the ghi de hoac tao key theo media id.
- Neu job fail giua chung, lan sau co the xu ly lai tu file goc.
- Khong xoa file goc khi chua chac ket qua da upload thanh cong.

## Stuck job recovery

Neu worker crash sau khi doi status sang `CONVERTING`, record se bi ket mai. Nen them cac cot nhu:

- `processing_started_at`
- `error_message`
- `retry_count`

Sau do co rule:

```text
Neu status=CONVERTING qua 30 phut
  -> coi la stale
  -> dua ve PENDING hoac FAIL tuy retry_count
```

## Pipeline worker goi y

```python
def process_one_media(media_id: int) -> None:
    media = claim_pending_media(media_id)
    if not media:
        return

    try:
        local_input = download_from_minio(media.original_path)
        metadata = probe(local_input)
        thumb_file = create_thumbnail(local_input)
        thumb_url = upload_thumbnail(thumb_file)
        mark_complete(media.id, thumb_url)
    except Exception as exc:
        mark_fail(media.id, str(exc))
    finally:
        cleanup_temp_files()
```

## Nen luu them metadata nao

Bang `media` hien co co `file_size`, `original_path`, `thumb_path`. Khi phat trien tiep, nen them:

| Cot | Ly do |
| --- | --- |
| `duration` | Hien thi thoi luong video |
| `width`, `height` | Biet resolution va tao UI dung ti le |
| `codec_video`, `codec_audio` | Debug kha nang phat |
| `bitrate` | Uoc luong chat luong/dung luong |
| `error_message` | Biet FFmpeg fail vi sao |
| `retry_count` | Gioi han so lan retry |

## Checklist van hanh

- Worker chi lay media `PENDING`.
- Doi status sang `CONVERTING` truoc khi chay FFmpeg.
- Gioi han concurrency.
- Ghi log stderr cua FFmpeg.
- Cap nhat `FAIL` khi loi.
- Don file tam sau moi job.
- Co recovery cho job ket o `CONVERTING`.
