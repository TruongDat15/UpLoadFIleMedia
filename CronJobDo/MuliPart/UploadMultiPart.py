import math
import uuid
import hashlib
import subprocess
import os
from pathlib import Path
from datetime import datetime

import ffmpeg
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import (
    create_engine, Column, BigInteger, Integer,
    String, TIMESTAMP, func
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/chunk_upload_demo"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ✅ Sử dụng đường dẫn tuyệt đối thay vì tương đối
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent.parent  # Thư mục upLoadFileChunk

TEMP_DIR = BASE_DIR / "temp_uploads"
FINAL_DIR = BASE_DIR / "final_uploads"
THUMB_DIR = BASE_DIR / "thumbnails"
HLS_DIR = BASE_DIR / "hls_videos"

TEMP_DIR.mkdir(exist_ok=True)
FINAL_DIR.mkdir(exist_ok=True)
THUMB_DIR.mkdir(exist_ok=True)
HLS_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 5 * 1024 * 1024


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_id = Column(String(100), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100))
    chunk_size = Column(BigInteger, nullable=False)
    total_parts = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    final_path = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class UploadPart(Base):
    __tablename__ = "upload_parts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_id = Column(String(100), nullable=False)
    part_number = Column(Integer, nullable=False)
    size = Column(BigInteger, nullable=False)
    hash = Column(String(100), nullable=False)
    path = Column(String(500), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class HLSVideo(Base):
    __tablename__ = "hls_videos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(String(100), unique=True, nullable=False)
    upload_id = Column(String(100), nullable=False)
    original_filename = Column(String(255), nullable=False)
    hls_path = Column(String(500), nullable=False)
    playlist_path = Column(String(500), nullable=False)
    status = Column(String(30), nullable=False)  # PROCESSING, READY, FAILED
    duration = Column(Integer)  # in seconds
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Thêm static files serving cho HLS videos
if HLS_DIR.exists():
    app.mount("/hls", StaticFiles(directory=str(HLS_DIR)), name="hls")


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def get_session_or_404(db, upload_id: str):
    session = db.query(UploadSession).filter_by(upload_id=upload_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    return session


def get_part_path(upload_id: str, part_number: int) -> Path:
    folder = TEMP_DIR / upload_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"part_{part_number:05d}.chunk"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while data := f.read(1024 * 1024):
            h.update(data)

    return h.hexdigest()


@app.post("/upload/init")
def init_upload(
    filename: str = Form(...),
    file_size: int = Form(...),
    content_type: str = Form("application/octet-stream")
):
    db = get_db()

    upload_id = str(uuid.uuid4())
    total_parts = math.ceil(file_size / CHUNK_SIZE)

    session = UploadSession(
        upload_id=upload_id,
        filename=filename,
        file_size=file_size,
        content_type=content_type,
        chunk_size=CHUNK_SIZE,
        total_parts=total_parts,
        status="UPLOADING"
    )

    db.add(session)
    db.commit()
    db.close()

    return {
        "upload_id": upload_id,
        "chunk_size": CHUNK_SIZE,
        "total_parts": total_parts,
        "status": "UPLOADING"
    }


@app.post("/upload/{upload_id}/chunk/{part_number}")
async def upload_chunk(
    upload_id: str,
    part_number: int,
    chunk: UploadFile = File(...)
):
    db = get_db()
    session = get_session_or_404(db, upload_id)

    if session.status != "UPLOADING":
        db.close()
        raise HTTPException(status_code=400, detail="Upload is not active")

    if part_number < 1 or part_number > session.total_parts:
        db.close()
        raise HTTPException(status_code=400, detail="Invalid part number")

    path = get_part_path(upload_id, part_number)

    with open(path, "wb") as f:
        while data := await chunk.read(1024 * 1024):
            f.write(data)

    size = path.stat().st_size
    hash_value = sha256_file(path)

    old_part = db.query(UploadPart).filter_by(
        upload_id=upload_id,
        part_number=part_number
    ).first()

    if old_part:
        old_part.size = size
        old_part.hash = hash_value
        old_part.path = str(path)
    else:
        part = UploadPart(
            upload_id=upload_id,
            part_number=part_number,
            size=size,
            hash=hash_value,
            path=str(path)
        )
        db.add(part)

    db.commit()
    db.close()

    return {
        "part_number": part_number,
        "size": size,
        "hash": hash_value,
        "status": "UPLOADED"
    }


@app.get("/upload/{upload_id}/status")
def upload_status(upload_id: str):
    db = get_db()
    session = get_session_or_404(db, upload_id)

    parts = db.query(UploadPart).filter_by(upload_id=upload_id).all()
    uploaded_parts = sorted([p.part_number for p in parts])

    missing_parts = [
        i for i in range(1, session.total_parts + 1)
        if i not in uploaded_parts
    ]

    result = {
        "upload_id": upload_id,
        "filename": session.filename,
        "file_size": session.file_size,
        "chunk_size": session.chunk_size,
        "total_parts": session.total_parts,
        "status": session.status,
        "uploaded_parts": uploaded_parts,
        "missing_parts": missing_parts
    }

    db.close()
    return result


@app.post("/upload/{upload_id}/complete")
def complete_upload(upload_id: str):
    db = get_db()
    session = get_session_or_404(db, upload_id)

    if session.status != "UPLOADING":
        db.close()
        raise HTTPException(status_code=400, detail="Upload is not active")

    parts = db.query(UploadPart).filter_by(upload_id=upload_id).order_by(
        UploadPart.part_number.asc()
    ).all()

    if len(parts) != session.total_parts:
        db.close()
        raise HTTPException(status_code=400, detail="Missing chunks")

    for i in range(1, session.total_parts + 1):
        if parts[i - 1].part_number != i:
            db.close()
            raise HTTPException(status_code=400, detail=f"Missing part {i}")

    final_path = FINAL_DIR / f"{upload_id}_{session.filename}"

    with open(final_path, "wb") as output:
        for part in parts:
            part_file = Path(part.path)

            if not part_file.exists():
                db.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Part file not found: {part.part_number}"
                )

            current_hash = sha256_file(part_file)
            if current_hash != part.hash:
                db.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Hash mismatch at part {part.part_number}"
                )

            with open(part_file, "rb") as pf:
                while data := pf.read(1024 * 1024):
                    output.write(data)

    if final_path.stat().st_size != session.file_size:
        db.close()
        raise HTTPException(status_code=400, detail="Final file size mismatch")

    session.status = "COMPLETED"
    session.final_path = str(final_path)
    db.commit()

    db.close()

    return {
        "upload_id": upload_id,
        "status": "COMPLETED",
        "final_path": str(final_path)
    }


@app.post("/upload/{upload_id}/ffmpeg/check")
def ffmpeg_check(upload_id: str):
    db = get_db()
    session = get_session_or_404(db, upload_id)

    if session.status != "COMPLETED":
        db.close()
        raise HTTPException(status_code=400, detail="Upload not completed")

    try:
        (
            ffmpeg
            .input(session.final_path)
            .output("null", f="null")
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        db.close()
        return {
            "valid": False,
            "error": e.stderr.decode("utf-8", errors="ignore")
        }

    db.close()

    return {
        "valid": True,
        "message": "Video is valid"
    }


@app.post("/upload/{upload_id}/ffmpeg/thumbnail")
def create_thumbnail(upload_id: str):
    db = get_db()
    session = get_session_or_404(db, upload_id)

    if session.status != "COMPLETED":
        db.close()
        raise HTTPException(status_code=400, detail="Upload not completed")

    thumb_path = THUMB_DIR / f"{upload_id}.jpg"

    try:
        (
            ffmpeg
            .input(session.final_path, ss=1)
            .output(str(thumb_path), vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        db.close()
        raise HTTPException(
            status_code=500,
            detail=e.stderr.decode("utf-8", errors="ignore")
        )

    db.close()

    return {
        "thumbnail_path": str(thumb_path)
    }


# ==================== HLS VIDEO STREAMING ====================

def get_video_duration(video_path: str) -> int:
    """Lấy độ dài video theo giây"""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return int(duration)
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0


def convert_to_hls(video_path: str, output_dir: Path, video_id: str) -> bool:
    """Convert video sang HLS format"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # HLS playlist path
        playlist_path = output_dir / "playlist.m3u8"

        # FFmpeg command để convert sang HLS
        (
            ffmpeg
            .input(video_path)
            .output(
                str(playlist_path),
                codec='copy',  # Copy codec không re-encode
                f='hls',
                hls_time=10,  # 10 seconds per segment
                hls_list_size=0,  # Keep all segments in playlist
                hls_segment_filename=str(output_dir / "segment_%03d.ts")
            )
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
    except Exception as e:
        print(f"Error converting to HLS: {e}")
        return False


@app.post("/video/{upload_id}/convert-hls")
def convert_video_to_hls(upload_id: str):
    """Convert uploaded video sang HLS"""
    db = get_db()
    session = get_session_or_404(db, upload_id)

    if session.status != "COMPLETED":
        db.close()
        raise HTTPException(status_code=400, detail="Upload not completed")

    try:
        video_id = str(uuid.uuid4())
        hls_output_dir = HLS_DIR / video_id

        # Create HLS video record with PROCESSING status
        # ✅ Convert to ABSOLUTE paths khi lưu DB
        hls_video = HLSVideo(
            video_id=video_id,
            upload_id=upload_id,
            original_filename=session.filename,
            hls_path=str(hls_output_dir.resolve()),
            playlist_path=str((hls_output_dir / "playlist.m3u8").resolve()),
            status="PROCESSING"
        )

        db.add(hls_video)
        db.commit()

        # Get video duration
        duration = get_video_duration(session.final_path)

        # Convert to HLS
        success = convert_to_hls(session.final_path, hls_output_dir, video_id)

        if success:
            hls_video.status = "READY"
            hls_video.duration = duration
            db.commit()
            db.close()

            return {
                "video_id": video_id,
                "status": "READY",
                "playlist_url": f"/video/{video_id}/playlist.m3u8",
                "duration": duration
            }
        else:
            hls_video.status = "FAILED"
            db.commit()
            db.close()
            raise HTTPException(status_code=500, detail="HLS conversion failed")

    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/debug/videos")
def debug_videos():
    """Debug: Kiểm tra tất cả videos trong DB"""
    db = SessionLocal()
    try:
        # Lấy tất cả videos
        videos = db.query(HLSVideo).all()

        result = []
        for v in videos:
            hls_path = Path(v.hls_path)
            segments = list(hls_path.glob("segment_*.ts")) if hls_path.exists() else []
            playlist_exists = (hls_path / "playlist.m3u8").exists() if hls_path.exists() else False

            result.append({
                "video_id": v.video_id,
                "upload_id": v.upload_id,
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


@app.get("/video/list")
def list_videos():
    """Liệt kê tất cả video HLS"""
    db = SessionLocal()
    try:
        videos = db.query(HLSVideo).filter_by(status="READY").all()

        result = []
        for v in videos:
            result.append({
                "video_id": v.video_id,
                "filename": v.original_filename,
                "duration": v.duration,
                "playlist_url": f"/video/{v.video_id}/playlist.m3u8",
                "thumbnail_url": f"/video/{v.video_id}/thumbnail",
                "created_at": v.created_at.isoformat() if v.created_at else None
            })

        return {"videos": result, "total": len(result)}
    finally:
        db.close()


# ✅ SPECIFIC ENDPOINTS FIRST (trước fallback)

@app.get("/video/{video_id}/playlist.m3u8")
def get_hls_playlist(video_id: str):
    """Phục vụ HLS playlist"""
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(video_id=video_id, status="READY").first()

        if not hls_video:
            print(f"[404] Video not found in DB: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")

        playlist_path = Path(hls_video.playlist_path)

        print(f"[DEBUG] Looking for playlist: {playlist_path}")
        print(f"[DEBUG] Playlist exists: {playlist_path.exists()}")

        if not playlist_path.exists():
            raise HTTPException(status_code=404, detail=f"Playlist not found: {playlist_path}")

        return FileResponse(
            playlist_path,
            media_type="application/vnd.apple.mpegurl",
            headers={"Content-Disposition": "inline"}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Playlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/video/{video_id}/info")
def get_video_info(video_id: str):
    """Lấy thông tin video"""
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(video_id=video_id).first()

        if not hls_video:
            raise HTTPException(status_code=404, detail="Video not found")

        return {
            "video_id": video_id,
            "filename": hls_video.original_filename,
            "duration": hls_video.duration,
            "status": hls_video.status,
            "playlist_url": f"/video/{video_id}/playlist.m3u8",
            "thumbnail_url": f"/video/{video_id}/thumbnail",
            "created_at": hls_video.created_at.isoformat() if hls_video.created_at else None
        }
    finally:
        db.close()


@app.get("/video/{video_id}/thumbnail")
def get_video_thumbnail(video_id: str):
    """Lấy thumbnail video"""
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(video_id=video_id).first()

        if not hls_video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Tìm upload session gốc
        upload_session = db.query(UploadSession).filter_by(
            upload_id=hls_video.upload_id
        ).first()

        if not upload_session:
            raise HTTPException(status_code=404, detail="Upload session not found")

        thumb_path = THUMB_DIR / f"{hls_video.upload_id}.jpg"

        if not thumb_path.exists():
            # Tạo thumbnail nếu chưa có
            try:
                (
                    ffmpeg
                    .input(upload_session.final_path, ss=1)
                    .output(str(thumb_path), vframes=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            except Exception as e:
                print(f"Thumbnail generation error: {e}")
                raise HTTPException(status_code=500, detail="Thumbnail generation failed")

        return FileResponse(
            thumb_path,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline"}
        )
    finally:
         db.close()


# ✅ FALLBACK ROUTES (phải ở cuối sau các specific endpoints)

@app.get("/video/{video_id}/segment/{segment}")
@app.get("/video/{video_id}/{segment}")
def get_hls_segment(video_id: str, segment: str):
    """Phục vụ HLS segment"""
    db = SessionLocal()
    try:
        hls_video = db.query(HLSVideo).filter_by(video_id=video_id, status="READY").first()

        if not hls_video:
            print(f"[404] Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")

        hls_path = Path(hls_video.hls_path)
        segment_path = hls_path / segment

        print(f"[DEBUG] HLS Path: {hls_path}")
        print(f"[DEBUG] Requesting segment: {segment}")
        print(f"[DEBUG] Full segment path: {segment_path}")
        print(f"[DEBUG] Path exists: {segment_path.exists()}")

        # ✅ Debug: List available segments
        if hls_path.exists():
            available = list(hls_path.glob("*"))
            print(f"[DEBUG] Available files in HLS dir: {[f.name for f in available]}")

        if not segment_path.exists():
            print(f"[404] Segment not found: {segment_path}")
            raise HTTPException(status_code=404, detail=f"Segment not found: {segment}")

        print(f"[OK] Serving segment: {segment_path}")
        return FileResponse(
            segment_path,
            media_type="video/mp2t",
            headers={"Content-Disposition": "inline"}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Segment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



if __name__ == "__main__":
    import uvicorn

    # Chạy server ở port 8888 như bạn cấu hình
    uvicorn.run(app, host="127.0.0.1", port=8888)