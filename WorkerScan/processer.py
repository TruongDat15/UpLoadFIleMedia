from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import ffmpeg
from sqlalchemy.orm import Session
from core.settings import get_settings
from logging_config import setup_logging
from models.media_model import Media, Status
from service.s3_service import S3Client

setup_logging()
log = logging.getLogger("cronjob")

settings = get_settings()


def _resolve_ffmpeg_bin() -> str:
    """Resolve ffmpeg executable path from env, PATH, or bundled binary."""
    env_bin = os.getenv("FFMPEG_BIN")
    if env_bin and Path(env_bin).exists():
        return str(Path(env_bin))

    path_env = os.environ.get("PATH", "")
    for path_item in path_env.split(os.pathsep):
        if not path_item:
            continue
        candidate = Path(path_item) / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
        candidate_no_ext = Path(path_item) / "ffmpeg"
        if candidate_no_ext.exists():
            return str(candidate_no_ext)

    project_root = Path(__file__).resolve().parents[1]
    bundled_bin = project_root / "CronJobDo" / "ffmpeg-8.1.1-essentials_build" / "bin" / "ffmpeg.exe"
    if bundled_bin.exists():
        return str(bundled_bin)

    raise RuntimeError("Khong tim thay ffmpeg. Dat FFMPEG_BIN hoac them ffmpeg vao PATH.")


# ------------------------------------------------------------------ #
#  Lấy frame đầu tiên từ video trên MinIO bằng FFmpeg                #
# ------------------------------------------------------------------ #

def extract_first_frame(media: Media) -> str:
    """
    Tải video từ MinIO về /tmp, dùng FFmpeg lấy frame đầu tiên,
    upload thumbnail lên MinIO, trả về URL thumbnail.
    """
    s3_client = S3Client()

    # Lấy key từ original_path (vd: http://minio:9000/bucket/abc.mp4 → abc.mp4)
    parsed = urlparse(media.original_path)
    object_key = parsed.path.lstrip("/").split("/", 1)[-1]  # bỏ phần bucket

    video_suffix = Path(object_key).suffix or ".mp4"
    thumb_key = f"thumbnails/{Path(object_key).stem}_thumb.jpg"

    # Create a persistent tmp folder next to this module: WorkerScan/tmp/<mediaid>_<timestamp>/
    base_tmp = Path(__file__).resolve().parent / "tmp"
    base_tmp.mkdir(parents=True, exist_ok=True)
    subdir_name = f"{media.id}_{int(datetime.now().timestamp())}"
    tmpdir = base_tmp / subdir_name
    tmpdir.mkdir(parents=True, exist_ok=True)

    video_path = str(tmpdir / f"video{video_suffix}")
    thumb_path = str(tmpdir / "thumb.jpg")

    # 1. Download video từ MinIO về thư mục tmp dự án
    log.info("⬇️   Tải video từ MinIO: %s  → %s", object_key, video_path)
    s3_client.download_file(
        Bucket=settings.bucket,
        Key=object_key,
        Filename=video_path,
    )

    # 2. FFmpeg: lấy đúng frame đầu tiên (vframes 1, seek 0)
    log.info("🎞️   FFmpeg đang trích frame đầu tiên (lưu tmp ở %s)...", tmpdir)
    ffmpeg_bin = _resolve_ffmpeg_bin()
    log.info("🛠️   Su dung ffmpeg: %s", ffmpeg_bin)
    try:
        (
            ffmpeg
            .input(video_path, ss=0)
            .output(thumb_path, vframes=1, **{"q:v": 2}, f="image2")
            .overwrite_output()
            .run(cmd=ffmpeg_bin, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as exc:
        stderr_text = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else str(exc)
        raise RuntimeError(f"FFmpeg lỗi: {stderr_text}") from exc

    if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
        raise RuntimeError("FFmpeg không tạo được thumbnail.")

    log.info("📦  Upload thumbnail lên MinIO: %s", thumb_key)

    # 3. Upload thumbnail lên MinIO
    s3_client.upload_file(
        Filename=thumb_path,
        Bucket=settings.bucket,
        Key=thumb_key,
    )

    thumb_url = f"{s3_client.endpoint_url}/{settings.bucket}/{thumb_key}"
    log.info("🖼️   Thumbnail URL: %s", thumb_url)
    return thumb_url


# ------------------------------------------------------------------ #
#  Xử lý từng media                                                   #
# ------------------------------------------------------------------ #

def process_media(media: Media, db: Session) -> None:
    """Xử lý 1 bản ghi media đang PENDING."""
    log.info("⚙️   Đang xử lý media id=%s  file=%s", media.id, media.original_path)

    try:
        thumb_url = extract_first_frame(media)

        media.thumb_path = thumb_url
        media.status = Status.COMPLETE.value
        db.commit()

        log.info("✅  media id=%s  → DONE  thumb=%s", media.id, thumb_url)

    except Exception as exc:
        db.rollback()
        media.status = Status.FAIL.value
        db.commit()
        log.error("❌  media id=%s  thất bại: %s", media.id, exc)
