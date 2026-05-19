from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.common import save_upload_file, status_label
from api.deps import get_db
from models.media_model import FileType, Media, Status
from models.user_model import User

router = APIRouter(prefix="/upload-video", tags=["upload-video"])


def _build_media_response(media: Media) -> dict:
    return {
        "id": media.id,
        "user_id": media.user_id,
        "title": media.title,
        "file_type": media.file_type,
        "original_path": media.original_path,
        "thumb_path": media.thumb_path,
        "file_size": media.file_size,
        "status": status_label(media.status),
        "created_at": media.created_at,
    }


@router.post("")
def upload_video(
    user_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a video")

    saved_path = save_upload_file(file, "videos")
    file_size = saved_path.stat().st_size

    media = Media(
        user_id=user_id,
        title=title,
        file_type=FileType.VIDEO.value,
        original_path=str(saved_path),
        thumb_path=None,
        file_size=file_size,
        status=Status.PENDING.value,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return _build_media_response(media)

